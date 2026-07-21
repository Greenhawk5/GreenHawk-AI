"""Metric implementations package.

Each metric lives in its own module and exposes a single public
``calculate_*`` function with a uniform signature::

    calculate_*(reference: np.ndarray, target: np.ndarray) -> float

The two arrays are always ``HWC uint8 RGB`` and have identical resolution.
This keeps the call site (``Measurement.py``) clean and makes it trivial to
add new metrics later.
"""

from metrics.psnr import calculate_psnr
from metrics.ssim import calculate_ssim
from metrics.msssim import calculate_msssim
from metrics.lpips_metric import calculate_lpips, get_lpips_model
from metrics.fsim import calculate_fsim
from metrics.deltaE import calculate_deltaE

__all__ = [
    "calculate_psnr",
    "calculate_ssim",
    "calculate_msssim",
    "calculate_lpips",
    "get_lpips_model",
    "calculate_fsim",
    "calculate_deltaE",
]
