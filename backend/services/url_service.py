from pathlib import Path

from config import STORAGE_DIR


def convert_path_to_url(path):
    """Convert a stored file path into an API-relative, browser-safe URL."""
    try:
        relative_path = Path(path).resolve().relative_to(STORAGE_DIR)
    except ValueError as error:
        raise ValueError("File path is outside the configured storage directory") from error

    return f"/files/{relative_path.as_posix()}"


def convert_input_path_to_url(path):
    return convert_path_to_url(path)
