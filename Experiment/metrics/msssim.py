"""Multi-Scale Structural Similarity (MS-SSIM).

Implemented through :func:`pytorch_msssim.ms_ssim`, the most widely used
PyTorch implementation of the Wang et al. (2003) multi-scale extension of
SSIM.
"""

from __future__ import annotations

import numpy as np
import torch
from pytorch_msssim import ms_ssim

from utils.image_loader import to_tensor
from utils.logger import get_logger

logger = get_logger(__name__)

#: Value range for tensors normalised to ``[0, 1]``.
_DATA_RANGE: float = 1.0
#: MS-SSIM requires the image to be at least this many times downsample-able.
_MIN_SIDE: int = 161  # 5-level MS-SSIM with 11x11 windows needs >=161 px.


def calculate_msssim(reference: np.ndarray, target: np.ndarray) -> float:
    """Compute MS-SSIM between two RGB images.

    MS-SSIM evaluates SSIM at five successive scales and combines the
    results with weights originally proposed by Wang et al. (2003).  The
    output is in ``[0, 1]`` (1 = perfect similarity).

    Parameters
    ----------
    reference:
        Ground-truth image, shape ``(H, W, 3)``, ``uint8``.
    target:
        Generated image, same shape and dtype.

    Returns
    -------
    float
        MS-SSIM value in ``[0, 1]``.

    Raises
    ------
    ValueError
        If the inputs have mismatched shapes or dtypes other than uint8.
    RuntimeError
        If the GPU/CPU forward pass fails.
    """
    if reference.shape != target.shape:
        raise ValueError(
            f"Shape mismatch: {reference.shape} vs {target.shape}"
        )
    if reference.dtype != np.uint8 or target.dtype != np.uint8:
        raise ValueError("Both images must be uint8 RGB arrays.")

    h, w = reference.shape[:2]
    if min(h, w) < _MIN_SIDE:
        logger.warning(
            "Image is smaller than %dpx on the shortest side (%dx%d); "
            "MS-SSIM may be inaccurate.",
            _MIN_SIDE, w, h,
        )

    ref_t = to_tensor(reference, normalize_range=(0.0, 1.0))
    tgt_t = to_tensor(target, normalize_range=(0.0, 1.0))

    with torch.no_grad():
        value = ms_ssim(
            ref_t, tgt_t,
            data_range=_DATA_RANGE,
            win_size=11,
            size_average=True,
        )
    return float(value.item())
