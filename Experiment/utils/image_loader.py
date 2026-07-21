"""Image loading and conversion utilities.

This module centralises everything related to reading image files from disk,
converting them to a canonical ``RGB uint8`` NumPy representation, resizing
them when their resolution does not match the ground truth, and producing the
normalised ``[0, 1]`` tensors expected by the deep-learning based metrics
(LPIPS, MS-SSIM, FSIM).
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple, Union

import cv2
import numpy as np
import torch

from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Image file extensions accepted by the pipeline.
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".webp"})

#: Default OpenCV interpolation used when downscaling.
_INTERPOLATION_DOWNSCALE: int = cv2.INTER_AREA
#: Default OpenCV interpolation used when upscaling or same-size operations.
_INTERPOLATION_UPSCALE: int = cv2.INTER_LINEAR


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

#: Type alias for anything that can be interpreted as a filesystem path.
PathLike = Union[str, Path]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_image(path: PathLike) -> np.ndarray:
    """Load an image from disk and return it as an ``RGB uint8`` array.

    The function transparently handles every supported format (``jpg``,
    ``jpeg``, ``png``, ``webp``), discards any alpha channel, and converts
    grayscale images to 3-channel RGB so that all downstream metrics can
    operate on a uniform representation.

    Parameters
    ----------
    path:
        Path to the image file.

    Returns
    -------
    np.ndarray
        Image of shape ``(H, W, 3)`` with ``dtype=uint8`` in RGB channel
        order.

    Raises
    ------
    FileNotFoundError
        If ``path`` does not exist.
    ValueError
        If the file exists but cannot be decoded as an image, or if it has an
        unsupported extension.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Image not found: {p}")

    if p.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported extension '{p.suffix}'. "
            f"Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    # ``cv2.imread`` does not natively read WEBP on every platform / build,
    # so we read the raw bytes and let OpenCV decode them.  Using ``IMREAD_COLOR``
    # forces a 3-channel BGR output, automatically dropping any alpha channel.
    raw_bytes = np.fromfile(p, dtype=np.uint8)
    bgr = cv2.imdecode(raw_bytes, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError(f"Failed to decode image (corrupted or unsupported): {p}")

    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return rgb


def resize_if_needed(
    image: np.ndarray,
    reference: np.ndarray,
) -> np.ndarray:
    """Resize ``image`` so it matches the resolution of ``reference``.

    The aspect ratio of ``image`` is **preserved** by first letterboxing /
    cropping to the reference aspect ratio and then resizing to the exact
    target resolution.  This guarantees that pixel-wise metrics (PSNR, SSIM,
    FSIM, Delta-E) and structural metrics (LPIPS, MS-SSIM) all operate on
    aligned arrays.

    Parameters
    ----------
    image:
        The image to resize, shape ``(H, W, 3)``, ``uint8``.
    reference:
        The ground-truth image whose resolution will be matched,
        shape ``(H_ref, W_ref, 3)``.

    Returns
    -------
    np.ndarray
        ``image`` resized to exactly ``(H_ref, W_ref, 3)``.
    """
    target_h, target_w = reference.shape[:2]
    src_h, src_w = image.shape[:2]

    if (src_h, src_w) == (target_h, target_w):
        return image

    # Preserve aspect ratio by cropping the source centred to the target AR.
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        # Source is wider than target: crop horizontally.
        new_w = int(round(src_h * target_ratio))
        x0 = (src_w - new_w) // 2
        cropped = image[:, x0:x0 + new_w, :]
    elif src_ratio < target_ratio:
        # Source is taller than target: crop vertically.
        new_h = int(round(src_w / target_ratio))
        y0 = (src_h - new_h) // 2
        cropped = image[y0:y0 + new_h, :, :]
    else:
        cropped = image

    interp = (
        _INTERPOLATION_DOWNSCALE
        if (cropped.shape[0] > target_h or cropped.shape[1] > target_w)
        else _INTERPOLATION_UPSCALE
    )
    resized = cv2.resize(cropped, (target_w, target_h), interpolation=interp)
    return resized


def resize_to_match(
    image: np.ndarray,
    target_size: Tuple[int, int],
) -> np.ndarray:
    """Resize ``image`` to ``target_size = (H, W)`` preserving aspect ratio.

    Thin wrapper around :func:`resize_if_needed` that builds a synthetic
    reference of the requested size.
    """
    h, w = target_size
    reference = np.zeros((h, w, 3), dtype=np.uint8)
    return resize_if_needed(image, reference)


def to_tensor(
    image: np.ndarray,
    normalize_range: Tuple[float, float] = (0.0, 1.0),
) -> torch.Tensor:
    """Convert an ``HWC uint8`` NumPy image into a normalised ``NCHW`` tensor.

    The output is suitable for the PyTorch-based metrics (LPIPS, MS-SSIM,
    FSIM).  Two ranges are supported:

    * ``(0.0, 1.0)`` – the standard range used by ``pytorch_msssim`` and
      ``piq``.
    * ``(-1.0, 1.0)`` – the range required by ``lpips``.

    Parameters
    ----------
    image:
        Array of shape ``(H, W, 3)`` with ``dtype=uint8`` or float.
    normalize_range:
        Output value range.  Must be one of ``(0.0, 1.0)`` or ``(-1.0, 1.0)``.

    Returns
    -------
    torch.Tensor
        Float tensor of shape ``(1, 3, H, W)`` normalised to the requested
        range.
    """
    if normalize_range not in ((0.0, 1.0), (-1.0, 1.0)):
        raise ValueError(
            f"normalize_range must be (0.0, 1.0) or (-1.0, 1.0); got {normalize_range}"
        )

    arr = np.asarray(image)
    if arr.dtype != np.uint8:
        arr = np.clip(arr, 0, 255).astype(np.uint8)

    # HWC -> CHW, add batch dim.
    chw = arr.transpose(2, 0, 1).astype(np.float32) / 255.0
    tensor = torch.from_numpy(chw).unsqueeze(0)

    if normalize_range == (-1.0, 1.0):
        tensor = tensor * 2.0 - 1.0
    return tensor
