"""Keyword-based detection of the five image roles inside a test folder.

Each test folder produced by the user's pipeline contains exactly five
images with names following the convention:

* ``image-original.*``   – ground-truth colour image.
* ``image-grayscale.*``  – grayscale version (NOT evaluated, but used to
                            detect that the folder is a valid test case).
* ``image-zhang.*``      – Zhang CNN output.
* ``image-deoldify.*``   – DeOldify output.
* ``image-flux.*``       – FLUX output.

The detector never hardcodes file names: it only inspects lower-cased
filename stems and matches them against the keyword tables defined below.
This way the script keeps working if the user later renames files to
``mosque_original.jpg``, ``zhang_out.webp``, etc.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from utils.image_loader import SUPPORTED_EXTENSIONS
from utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

class ImageRole(str, Enum):
    """Enumeration of the five possible roles a file can take."""

    ORIGINAL = "original"
    GRAYSCALE = "grayscale"
    ZHANG = "zhang"
    DEOLDIFY = "deoldify"
    FLUX = "flux"


# ---------------------------------------------------------------------------
# Keyword tables
# ---------------------------------------------------------------------------

#: Keywords that identify each role.  Order matters only for tie-breaking
#: (the first matching role wins) but in practice the keywords are disjoint.
ROLE_KEYWORDS: Dict[ImageRole, List[str]] = {
    ImageRole.ORIGINAL: ["original", "ground_truth", "groundtruth", "gt", "ref", "reference"],
    ImageRole.GRAYSCALE: ["grayscale", "grey", "gray", "bw", "blackwhite"],
    ImageRole.ZHANG: ["zhang"],
    ImageRole.DEOLDIFY: ["deoldify"],
    ImageRole.FLUX: ["flux"],
}

#: Roles that will be actively compared against the original image.
EVALUATED_ROLES: tuple[ImageRole, ...] = (
    ImageRole.ZHANG,
    ImageRole.DEOLDIFY,
    ImageRole.FLUX,
)


# ---------------------------------------------------------------------------
# Data container
# ---------------------------------------------------------------------------

@dataclass
class ImageSet:
    """Container holding the resolved paths for a single test folder.

    ``grayscale`` may be ``None`` if the folder does not contain one (the
    pipeline still works without it).  Any of the evaluated roles may also be
    ``None`` – they will be skipped at evaluation time and logged as missing.
    """

    folder: Path
    name: str
    original: Optional[Path] = None
    grayscale: Optional[Path] = None
    zhang: Optional[Path] = None
    deoldify: Optional[Path] = None
    flux: Optional[Path] = None

    def as_dict(self) -> Dict[ImageRole, Optional[Path]]:
        """Return a role → path mapping (excluding ``folder`` / ``name``)."""
        return {
            ImageRole.ORIGINAL: self.original,
            ImageRole.GRAYSCALE: self.grayscale,
            ImageRole.ZHANG: self.zhang,
            ImageRole.DEOLDIFY: self.deoldify,
            ImageRole.FLUX: self.flux,
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _classify_filename(filename: str) -> Optional[ImageRole]:
    """Return the :class:`ImageRole` matching ``filename`` or ``None``.

    The check is case-insensitive and inspects only the stem (no extension).
    The first matching role in declaration order wins, which guarantees that
    e.g. ``image-grayscale.jpg`` is never misclassified as the original even
    if the original keywords list happens to contain a substring match.
    """
    stem = Path(filename).stem.lower()
    for role, keywords in ROLE_KEYWORDS.items():
        for kw in keywords:
            if kw in stem:
                return role
    return None


def detect_files(folder: Path) -> ImageSet:
    """Inspect ``folder`` and return an :class:`ImageSet` of detected files.

    Parameters
    ----------
    folder:
        Directory that should contain the five image variants.

    Returns
    -------
    ImageSet
        Populated dataclass.  Fields for missing roles will be ``None``.

    Raises
    ------
    NotADirectoryError
        If ``folder`` is not a directory.
    """
    if not folder.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder}")

    image_set = ImageSet(folder=folder, name=folder.name)

    for entry in sorted(folder.iterdir()):
        if not entry.is_file():
            continue
        if entry.suffix.lower() not in SUPPORTED_EXTENSIONS:
            logger.debug("Skipping unsupported file: %s", entry)
            continue

        role = _classify_filename(entry.name)
        if role is None:
            logger.debug("Skipping unrecognised file: %s", entry)
            continue

        # The first match wins; if a duplicate is found we keep the first
        # occurrence and warn about the second.
        current = image_set.as_dict().get(role)
        if current is not None:
            logger.warning(
                "Duplicate role '%s' in folder '%s': keeping '%s', ignoring '%s'",
                role.value,
                folder.name,
                current.name,
                entry.name,
            )
            continue

        if role is ImageRole.ORIGINAL:
            image_set.original = entry
        elif role is ImageRole.GRAYSCALE:
            image_set.grayscale = entry
        elif role is ImageRole.ZHANG:
            image_set.zhang = entry
        elif role is ImageRole.DEOLDIFY:
            image_set.deoldify = entry
        elif role is ImageRole.FLUX:
            image_set.flux = entry

    return image_set
