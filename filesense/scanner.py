"""Read-only filesystem scanning."""

from collections.abc import Iterator
from pathlib import Path

from .models import FileRecord


def iter_files(root: Path) -> Iterator[Path]:
    """Yield files beneath root without following directory symlinks."""
    if not root.exists():
        raise FileNotFoundError(f"Directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root}")

    def on_walk_error(error: OSError) -> None:
        # os.walk calls this for directories that cannot be traversed.
        # The scan continues; inaccessible locations are simply skipped.
        return None

    import os

    for current, directories, filenames in os.walk(root, onerror=on_walk_error, followlinks=False):
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

    for path in iter_files(root_path):
        try:
            records.append(FileRecord.from_path(path))
        except (OSError, PermissionError) as error:
            errors.append(f"{path}: {error}")

    return records, errors
