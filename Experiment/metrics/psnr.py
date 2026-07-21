"""Peak Signal-to-Noise Ratio (PSNR).

Implemented through :func:`skimage.metrics.peak_signal_noise_ratio` to
guarantee a well-tested, scientifically accepted implementation.
"""

from __future__ import annotations

import numpy as np
from skimage.metrics import peak_signal_noise_ratio

from utils.logger import get_logger

logger = get_logger(__name__)

#: Maximum value for an 8-bit image.  Used as the ``data_range`` argument.
_DATA_RANGE: int = 255


def calculate_psnr(reference: np.ndarray, target: np.ndarray) -> float:
    """Compute the PSNR between two RGB images.

    PSNR is defined as::

        PSNR = 10 * log10( MAX^2 / MSE )

    where ``MAX`` is the maximum possible pixel value (255 for 8-bit images).
    Higher values indicate better fidelity.  A PSNR of ``inf`` means the two
    images are identical.

    Parameters
    ----------
    reference:
        Ground-truth image, shape ``(H, W, 3)``, ``uint8``.
    target:
        Generated image, same shape and dtype.

    Returns
    -------
    float
        PSNR value in decibels (dB).  ``inf`` if the images are identical.

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

    value = float(
        peak_signal_noise_ratio(reference, target, data_range=_DATA_RANGE)
    )
    return value
