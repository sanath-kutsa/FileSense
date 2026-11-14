"""Read-only filesystem scanning."""

import os
from collections.abc import Iterator
from pathlib import Path

from .models import FileRecord


def iter_files(root: Path, errors: list[str] | None = None) -> Iterator[Path]:
    """Yield files beneath root without following directory symlinks.

    When an errors list is supplied, inaccessible directories are reported
    there while the scan continues.
    """
    if not root.exists():
        raise FileNotFoundError(f"Directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root}")

    def on_walk_error(error: OSError) -> None:
        if errors is not None:
            location = error.filename or str(root)
            errors.append(f"{location}: {error}")

    for current, directories, filenames in os.walk(
        root, onerror=on_walk_error, followlinks=False
    ):
        current_path = Path(current)
        directories[:] = [
            name for name in directories
            if not (current_path / name).is_symlink()
        ]
        for filename in filenames:
            path = current_path / filename
            if path.is_symlink():
                continue
            yield path


def scan_directory(root: str | Path) -> tuple[list[FileRecord], list[str]]:
    """Collect metadata for accessible files under a directory.

    Returns a tuple of file records and non-fatal error messages.
    """
    root_path = Path(root).expanduser()
    records: list[FileRecord] = []
    errors: list[str] = []

    for path in iter_files(root_path, errors):
        try:
            records.append(FileRecord.from_path(path))
        except OSError as error:
            errors.append(f"{path}: {error}")

    return records, errors
