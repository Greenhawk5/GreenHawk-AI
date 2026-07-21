"""Feature Similarity Index (FSIM).

Implemented through :func:`piq.fsim`.  FSIM computes similarity based on
phase congruency and gradient magnitude, two complementary low-level
features that correlate well with human perception of image quality.
"""

from __future__ import annotations

import numpy as np
import torch
from piq import fsim

from utils.image_loader import to_tensor
from utils.logger import get_logger

logger = get_logger(__name__)

#: Value range for tensors normalised to ``[0, 1]``.
_DATA_RANGE: float = 1.0


def calculate_fsim(reference: np.ndarray, target: np.ndarray) -> float:
    """Compute FSIM between two RGB images.

    FSIM is computed by combining phase congruency and gradient magnitude
    similarity.  The output is in ``[0, 1]`` where 1 means the two images
    are structurally identical.

    Parameters
    ----------
    reference:
        Ground-truth image, shape ``(H, W, 3)``, ``uint8``.
    target:
        Generated image, same shape and dtype.

    Returns
    -------
    float
        FSIM value in ``[0, 1]`` (higher is better).
    """
    if reference.shape != target.shape:
        raise ValueError(
            f"Shape mismatch: {reference.shape} vs {target.shape}"
        )
    if reference.dtype != np.uint8 or target.dtype != np.uint8:
        raise ValueError("Both images must be uint8 RGB arrays.")

    # FSIM uses luminance information only; piq handles RGB inputs internally
    # by converting to YIQ and using the Y channel for phase congruency.
    ref_t = to_tensor(reference, normalize_range=(0.0, 1.0))
    tgt_t = to_tensor(target, normalize_range=(0.0, 1.0))

    with torch.no_grad():
        value = fsim(ref_t, tgt_t, data_range=_DATA_RANGE, reduction="mean")
    return float(value.item())
