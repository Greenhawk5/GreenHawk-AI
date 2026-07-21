"""Learned Perceptual Image Patch Similarity (LPIPS).

Implemented through the official :mod:`lpips` package (Zhang et al., 2018).
The AlexNet backbone is used by default because it offers the best
speed/perception trade-off and is the most common choice in the literature.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

import numpy as np
import torch

from utils.image_loader import to_tensor
from utils.logger import get_logger

logger = get_logger(__name__)

#: Backend network used by LPIPS.  ``alex`` is fast and accurate enough for
#: academic benchmarks.  ``vgg`` is the original paper default.
NetworkName = Literal["alex", "vgg", "squeeze"]
_DEFAULT_NETWORK: NetworkName = "alex"


# ---------------------------------------------------------------------------
# Model singleton
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_lpips_model(network: NetworkName = _DEFAULT_NETWORK) -> "torch.nn.Module":
    """Return a cached LPIPS model ready for inference.

    The model is created once and reused across all evaluations to avoid the
    non-trivial overhead of downloading/loading the pretrained weights for
    every image.

    Parameters
    ----------
    network:
        One of ``"alex"``, ``"vgg"`` or ``"squeeze"``.

    Returns
    -------
    torch.nn.Module
        LPIPS model in eval mode on the most appropriate device available.
    """
    import lpips  # Imported lazily so the rest of the pipeline still works
                  # if the user only wants the non-DL metrics.

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = lpips.LPIPS(net=network, verbose=False).to(device).eval()
    logger.info("LPIPS model loaded (net=%s, device=%s)", network, device)
    return model


# ---------------------------------------------------------------------------
# Public metric
# ---------------------------------------------------------------------------

def calculate_lpips(
    reference: np.ndarray,
    target: np.ndarray,
    network: NetworkName = _DEFAULT_NETWORK,
) -> float:
    """Compute LPIPS between two RGB images.

    LPIPS measures the perceptual distance between two images by comparing
    their deep features extracted from a pretrained network.  The output is
    in ``[0, +inf)`` where 0 means perceptually identical and larger values
    indicate larger perceptual differences.

    Parameters
    ----------
    reference:
        Ground-truth image, shape ``(H, W, 3)``, ``uint8``.
    target:
        Generated image, same shape and dtype.
    network:
        Backbone network name (default ``"alex"``).

    Returns
    -------
    float
        LPIPS distance (lower is better).
    """
    if reference.shape != target.shape:
        raise ValueError(
            f"Shape mismatch: {reference.shape} vs {target.shape}"
        )
    if reference.dtype != np.uint8 or target.dtype != np.uint8:
        raise ValueError("Both images must be uint8 RGB arrays.")

    model = get_lpips_model(network)
    device = next(model.parameters()).device

    # LPIPS expects tensors normalised to [-1, 1].
    ref_t = to_tensor(reference, normalize_range=(-1.0, 1.0)).to(device)
    tgt_t = to_tensor(target, normalize_range=(-1.0, 1.0)).to(device)

    with torch.no_grad():
        distance = model(ref_t, tgt_t)
    return float(distance.item())
