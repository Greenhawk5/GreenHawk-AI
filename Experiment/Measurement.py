"""Colorization Evaluation Pipeline – Bachelor Thesis Project.

Compares three AI image-colorization models (Zhang CNN, DeOldify, FLUX)
against ground-truth colour images using six image-quality metrics:

* PSNR       – peak signal-to-noise ratio            (scikit-image)
* SSIM       – structural similarity index            (scikit-image)
* MS-SSIM    – multi-scale SSIM                       (pytorch-msssim)
* LPIPS      – learned perceptual image patch sim.    (lpips, AlexNet)
* FSIM       – feature similarity index               (piq)
* Delta E    – CIEDE2000 colour difference            (colour-science)

Run with::

    python Measurement.py

The script:

1. Discovers every test folder under ``Test Results/``.
2. For each folder, identifies the five images (original / grayscale /
   zhang / deoldify / flux) by filename keyword.
3. Computes the six metrics for every model output against the original.
4. Saves ``results.{csv,xlsx}``, ``summary.{csv,xlsx}`` and the plots in
   ``results/plots/``.

Author: Bachelor Thesis – Image Colorization Evaluation
Python: 3.11+
"""

from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path to import utils package
# The script is in Report/Test Results/, so we need to go up 3 levels
utils_path = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, utils_path)
print(f"Added to sys.path: {utils_path}", file=sys.stderr)

import pandas as pd
import torch

from utils.logger import get_logger
from utils.file_detector import (
    EVALUATED_ROLES,
    ImageRole,
    ImageSet,
    detect_files,
)
from utils.image_loader import load_image, resize_if_needed
from utils.exporter import export_results, export_summary, generate_plots

from metrics import (
    calculate_psnr,
    calculate_ssim,
    calculate_msssim,
    calculate_lpips,
    calculate_fsim,
    calculate_deltaE,
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Directory containing one sub-folder per test image.
TEST_RESULTS_DIR: Path = Path(__file__).resolve().parent
#: Directory where every output artefact is written.
RESULTS_DIR: Path = Path(__file__).resolve().parent / "results"
#: Sub-directory containing the plots.
PLOTS_DIR: Path = RESULTS_DIR / "plots"
#: Human-readable labels for each evaluated role, used in the DataFrame.
MODEL_LABELS: Dict[ImageRole, str] = {
    ImageRole.ZHANG: "Zhang",
    ImageRole.DEOLDIFY: "DeOldify",
    ImageRole.FLUX: "FLUX",
}
#: Column names of the per-image results DataFrame.
RESULT_COLUMNS: List[str] = [
    "Image Name", "Model",
    "PSNR", "SSIM", "MS-SSIM", "LPIPS", "FSIM", "DeltaE",
]


# ---------------------------------------------------------------------------
# Per-image evaluation
# ---------------------------------------------------------------------------

def _compute_all_metrics(reference: "np.ndarray", target: "np.ndarray") -> Dict[str, float]:
    """Run every metric on a single (reference, target) pair.

    Each metric is wrapped in its own try/except so a failure in one of them
    (e.g. a CUDA OOM in LPIPS) does not invalidate the whole evaluation.
    Missing values are stored as ``NaN`` so pandas handles them gracefully
    when computing averages.
    """
    # ``np`` is imported lazily inside the function body to keep the import
    # section of the module clean.
    import numpy as np  # noqa: WPS433 – intentional local import.

    results: Dict[str, float] = {}

    # --- PSNR -------------------------------------------------------------
    try:
        results["PSNR"] = calculate_psnr(reference, target)
    except Exception as exc:  # pragma: no cover
        logger.error("PSNR failed: %s", exc, exc_info=True)
        results["PSNR"] = float("nan")

    # --- SSIM -------------------------------------------------------------
    try:
        results["SSIM"] = calculate_ssim(reference, target)
    except Exception as exc:  # pragma: no cover
        logger.error("SSIM failed: %s", exc, exc_info=True)
        results["SSIM"] = float("nan")

    # --- MS-SSIM ----------------------------------------------------------
    try:
        results["MS-SSIM"] = calculate_msssim(reference, target)
    except Exception as exc:  # pragma: no cover
        logger.error("MS-SSIM failed: %s", exc, exc_info=True)
        results["MS-SSIM"] = float("nan")

    # --- LPIPS ------------------------------------------------------------
    try:
        results["LPIPS"] = calculate_lpips(reference, target)
    except Exception as exc:  # pragma: no cover
        logger.error("LPIPS failed: %s", exc, exc_info=True)
        results["LPIPS"] = float("nan")

    # --- FSIM -------------------------------------------------------------
    try:
        results["FSIM"] = calculate_fsim(reference, target)
    except Exception as exc:  # pragma: no cover
        logger.error("FSIM failed: %s", exc, exc_info=True)
        results["FSIM"] = float("nan")

    # --- Delta E ----------------------------------------------------------
    try:
        results["DeltaE"] = calculate_deltaE(reference, target)
    except Exception as exc:  # pragma: no cover
        logger.error("DeltaE failed: %s", exc, exc_info=True)
        results["DeltaE"] = float("nan")

    return results


def evaluate_model(
    reference,
    generated_path: Path,
    model_label: str,
    image_name: str,
) -> Optional[Dict[str, object]]:
    """Evaluate a single model output against the reference image.

    Parameters
    ----------
    reference:
        Pre-loaded ground-truth image (HWC uint8 RGB).
    generated_path:
        Path to the generated image file.
    model_label:
        Label that will appear in the ``Model`` column.
    image_name:
        Label that will appear in the ``Image Name`` column.

    Returns
    -------
    dict or None
        One-row dict ready to be appended to the results DataFrame, or
        ``None`` if evaluation failed and the sample should be skipped.
    """
    try:
        generated = load_image(generated_path)
    except Exception as exc:
        logger.error(
            "Failed to load generated image '%s' (%s): %s",
            generated_path, model_label, exc, exc_info=True,
        )
        return None

    try:
        generated = resize_if_needed(generated, reference)
    except Exception as exc:
        logger.error(
            "Failed to resize generated image '%s' (%s): %s",
            generated_path, model_label, exc, exc_info=True,
        )
        return None

    metrics = _compute_all_metrics(reference, generated)
    row: Dict[str, object] = {
        "Image Name": image_name,
        "Model": model_label,
    }
    row.update(metrics)
    return row


# ---------------------------------------------------------------------------
# Per-folder evaluation
# ---------------------------------------------------------------------------

def evaluate_folder(folder: Path) -> List[Dict[str, object]]:
    """Evaluate every model output inside a single test folder.

    Parameters
    ----------
    folder:
        Directory containing ``image-original.*`` plus the three model
        outputs (``image-zhang.*``, ``image-deoldify.*``, ``image-flux.*``).

    Returns
    -------
    list of dict
        One dict per successfully evaluated model output.  May be empty if
        the folder is missing the original image or all model outputs.
    """
    image_set: ImageSet = detect_files(folder)
    rows: List[Dict[str, object]] = []

    if image_set.original is None:
        logger.error(
            "Folder '%s' skipped: no original/ground-truth image detected.",
            folder.name,
        )
        return rows

    try:
        reference = load_image(image_set.original)
    except Exception as exc:
        logger.error(
            "Failed to load original image '%s': %s",
            image_set.original, exc, exc_info=True,
        )
        return rows

    for role in EVALUATED_ROLES:
        path = image_set.as_dict().get(role)
        label = MODEL_LABELS[role]
        if path is None:
            logger.warning(
                "Folder '%s': model '%s' output is missing – skipping.",
                folder.name, label,
            )
            continue

        logger.info("    Evaluating %s ...", label)
        row = evaluate_model(
            reference=reference,
            generated_path=path,
            model_label=label,
            image_name=image_set.name,
        )
        if row is not None:
            rows.append(row)

    return rows


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_test_folders(base_dir: Path) -> List[Path]:
    """Return every sub-directory of ``base_dir`` that looks like a test case.

    A folder qualifies if it contains at least one image file.  Folders that
    contain only non-image files (e.g. ``.DS_Store``) are silently skipped.
    """
    if not base_dir.exists():
        logger.error("Test Results directory does not exist: %s", base_dir)
        return []

    from utils.image_loader import SUPPORTED_EXTENSIONS

    folders: List[Path] = []
    for entry in sorted(base_dir.iterdir()):
        if not entry.is_dir():
            continue
        has_image = any(
            child.suffix.lower() in SUPPORTED_EXTENSIONS for child in entry.iterdir()
        )
        if has_image:
            folders.append(entry)
    return folders


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """Entry point of the evaluation pipeline.

    Returns
    -------
    int
        Process exit code (0 = success).
    """
    start_time = time.perf_counter()
    logger.info("=" * 72)
    logger.info("Colorization Evaluation Pipeline")
    logger.info("=" * 72)
    logger.info("Device: %s",
                "CUDA" if torch.cuda.is_available() else "CPU")
    logger.info("Test results directory: %s", TEST_RESULTS_DIR)
    logger.info("Output directory:       %s", RESULTS_DIR)
    logger.info("-" * 72)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    folders = discover_test_folders(TEST_RESULTS_DIR)
    if not folders:
        logger.error(
            "No test folders detected under '%s'. "
            "Place folders like 'Test Results/Mosque/image-original.jpg ...' "
            "next to Measurement.py and re-run.",
            TEST_RESULTS_DIR,
        )
        return 1

    total = len(folders)
    logger.info("Discovered %d test folder(s).", total)
    logger.info("-" * 72)

    all_rows: List[Dict[str, object]] = []
    for idx, folder in enumerate(folders, start=1):
        logger.info("Processing folder %d/%d: %s", idx, total, folder.name)
        try:
            rows = evaluate_folder(folder)
        except Exception as exc:
            logger.error(
                "Unexpected error while processing folder '%s': %s",
                folder.name, exc, exc_info=True,
            )
            rows = []
        all_rows.extend(rows)

    if not all_rows:
        logger.error("No metric rows were produced – nothing to export.")
        return 2

    df = pd.DataFrame(all_rows, columns=RESULT_COLUMNS)
    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    export_results(df, RESULTS_DIR)
    summary_df = export_summary(df, RESULTS_DIR)

    try:
        generate_plots(df, PLOTS_DIR)
    except Exception as exc:
        logger.error("Plot generation failed: %s", exc, exc_info=True)

    # ------------------------------------------------------------------
    # Final report
    # ------------------------------------------------------------------
    elapsed = time.perf_counter() - start_time
    n_images = df["Image Name"].nunique()
    n_evaluations = len(df)

    logger.info("-" * 72)
    logger.info("Finished.")
    logger.info("Number of images:           %d", n_images)
    logger.info("Number of evaluated models: %d", n_evaluations)
    logger.info("Execution time:             %.2f seconds", elapsed)
    logger.info("Output folder:              %s", RESULTS_DIR)
    logger.info("-" * 72)
    logger.info("Per-model summary:")
    for _, row in summary_df.iterrows():
        logger.info(
            "  %-9s  PSNR=%6.2f  SSIM=%.4f  MS-SSIM=%.4f  "
            "LPIPS=%.4f  FSIM=%.4f  ΔE=%6.2f",
            row["Model"],
            row.get("Mean PSNR", float("nan")),
            row.get("Mean SSIM", float("nan")),
            row.get("Mean MS-SSIM", float("nan")),
            row.get("Mean LPIPS", float("nan")),
            row.get("Mean FSIM", float("nan")),
            row.get("Mean DeltaE", float("nan")),
        )
    logger.info("=" * 72)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.warning("Interrupted by user.")
        sys.exit(130)
    except Exception as exc:  # pragma: no cover
        logger.critical("Fatal error: %s", exc)
        logger.critical("%s", traceback.format_exc())
        sys.exit(1)
