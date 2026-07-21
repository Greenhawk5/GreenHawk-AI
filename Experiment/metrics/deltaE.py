"""Delta E (CIEDE2000) colour difference.

Implemented through :mod:`colour` (colour-science).  Each pixel is converted
from sRGB to CIE Lab via XYZ, then the CIEDE2000 formula is applied.  The
final scalar is the **mean** Delta E over all pixels.
"""

from __future__ import annotations

import numpy as np
import colour

from utils.logger import get_logger

logger = get_logger(__name__)

#: sRGB transfer function constants – handled by ``colour.models.sRGB_to_XYZ``
#: but documented here for reference.


def _to_lab(rgb: np.ndarray) -> np.ndarray:
    """Convert an ``HWC uint8 sRGB`` image to ``HWC float Lab``.

    The colour-science library expects float sRGB in ``[0, 1]`` and returns
    Lab values where ``L`` is in ``[0, 100]`` and ``a, b`` are roughly in
    ``[-128, 128]``.
    """
    rgb_f = rgb.astype(np.float64) / 255.0
    xyz = colour.models.sRGB_to_XYZ(rgb_f)
    lab = colour.XYZ_to_Lab(xyz)
    return lab


def calculate_deltaE(reference: np.ndarray, target: np.ndarray) -> float:
    """Compute the mean CIEDE2000 Delta E between two RGB images.

    CIEDE2000 is the current ISO/CIE standard colour-difference formula
    (ISO/CIE 11664-6:2014).  It was designed to be perceptually uniform for
    small to moderate colour differences, which is exactly the regime of
    interest for AI-colorization evaluation.  Lower values indicate higher
    colour fidelity.

    Parameters
    ----------
    reference:
        Ground-truth image, shape ``(H, W, 3)``, ``uint8``.
    target:
        Generated image, same shape and dtype.

    Returns
    -------
    float
        Mean Delta E (CIEDE2000) across all pixels (lower is better).
    """
    if reference.shape != target.shape:
        raise ValueError(
            f"Shape mismatch: {reference.shape} vs {target.shape}"
        )
    if reference.dtype != np.uint8 or target.dtype != np.uint8:
        raise ValueError("Both images must be uint8 RGB arrays.")

    lab_ref = _to_lab(reference)
    lab_tgt = _to_lab(target)

    # ``colour.delta_E`` returns an array the same HxW shape as the inputs.
    delta = colour.delta_E(lab_ref, lab_tgt, method="CIE 2000")
    return float(np.mean(delta))
