"""Structural Similarity Index Measure (SSIM).

Implemented through :func:`skimage.metrics.structural_similarity` with
``channel_axis=2`` so the metric is computed per channel and averaged.
"""

from __future__ import annotations

import numpy as np
from skimage.metrics import structural_similarity

from utils.logger import get_logger

logger = get_logger(__name__)

#: Maximum value for an 8-bit image.
_DATA_RANGE: int = 255
#: Window size (default skimage value, kept here for documentation purposes).
_WIN_SIZE: int = 7
#: Standard deviation of the Gaussian window used by SSIM.
_SIGMA: float = 1.5


def calculate_ssim(reference: np.ndarray, target: np.ndarray) -> float:
    """Compute the multi-channel SSIM between two RGB images.

    SSIM compares local patterns of pixel intensities that have been
    normalised for luminance and contrast.  The result lies in ``[-1, 1]``
    where 1 means perfect structural similarity.

    Parameters
    ----------
    reference:
        Ground-truth image, shape ``(H, W, 3)``, ``uint8``.
    target:
        Generated image, same shape and dtype.

    Returns
    -------
    float
        Mean SSIM over the three channels, in ``[-1, 1]``.

    Raises
    ------
    ValueError
        If the inputs have mismatched shapes or dtypes other than uint8.
    """
    if reference.shape != target.shape:
        raise ValueError(
            f"Shape mismatch: {reference.shape} vs {target.shape}"
        )
    if reference.dtype != np.uint8 or target.dtype != np.uint8:
        raise ValueError("Both images must be uint8 RGB arrays.")

    # ``gaussian_weights=True`` reproduces the original Wang et al. (2004)
    # implementation and yields deterministic, comparable results.
    value = float(
        structural_similarity(
            reference,
            target,
            channel_axis=2,
            data_range=_DATA_RANGE,
            gaussian_weights=True,
            sigma=_SIGMA,
            use_sample_covariance=False,
        )
    )
    return value
