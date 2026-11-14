"""Data models used by FileSense."""

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class FileRecord:
    """Metadata collected for one file during a scan."""

    name: str
    path: str
    extension: str
    size_bytes: int
    modified_at: str
    category: str

    @classmethod
    def from_path(cls, path: Path) -> "FileRecord":
        """Build a record from a file path and its current metadata."""
        stat = path.stat()
        modified_at = datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat()
        extension = path.suffix.lower() or "[no extension]"
        from .categorizer import categorize_extension

        return cls(
            name=path.name,
            path=str(path.resolve()),
            extension=extension,
            size_bytes=stat.st_size,
            modified_at=modified_at,
            category=categorize_extension(extension),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return asdict(self)
