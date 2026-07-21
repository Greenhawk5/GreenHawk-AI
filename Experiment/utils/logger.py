"""Centralised logging configuration for the evaluation pipeline.

A single call to :func:`get_logger` returns a configured logger that writes
simultaneously to the console (``stdout``) and to a rotating log file located
at ``logs/pipeline.log`` (relative to the project root).  Every other module
should simply call ``get_logger(__name__)`` instead of using ``print``.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Maximum size of a single log file before rotation (5 MB).
_MAX_LOG_BYTES: int = 5 * 1024 * 1024
#: Number of backup log files to keep.
_MAX_LOG_BACKUPS: int = 3
#: Format used for both console and file handlers.
_LOG_FORMAT: str = (
    "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
)
#: Date format used inside the log prefix.
_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------

#: Tracks whether the root logger has already been configured.
_logger_configured: bool = False
#: Directory where the log file is written.
_LOG_DIR: Path = Path(__file__).resolve().parent.parent / "logs"
#: Full path to the log file.
_LOG_FILE: Path = _LOG_DIR / "pipeline.log"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a configured :class:`logging.Logger`.

    The first call sets up the root logger (console + rotating file handler).
    Subsequent calls simply return ``logging.getLogger(name)`` so every module
    shares the same handlers and formatting.

    Parameters
    ----------
    name:
        Hierarchical name of the logger, typically ``__name__`` of the calling
        module.  If ``None``, the root logger is returned.

    Returns
    -------
    logging.Logger
        A ready-to-use logger instance.
    """
    global _logger_configured
    root = logging.getLogger()

    if not _logger_configured:
        # Make sure the log directory exists.
        _LOG_DIR.mkdir(parents=True, exist_ok=True)

        root.setLevel(logging.INFO)

        formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

        # --- Console handler -------------------------------------------------
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)

        # --- Rotating file handler ------------------------------------------
        file_handler = RotatingFileHandler(
            _LOG_FILE,
            maxBytes=_MAX_LOG_BYTES,
            backupCount=_MAX_LOG_BACKUPS,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

        # Reduce verbosity of noisy third-party loggers.
        logging.getLogger("PIL").setLevel(logging.WARNING)
        logging.getLogger("matplotlib").setLevel(logging.WARNING)

        _logger_configured = True

    return logging.getLogger(name if name else "colorization_eval")
