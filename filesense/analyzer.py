"""Analysis helpers for scanned file records."""

from collections import defaultdict
from collections.abc import Iterable

from .models import FileRecord


def format_bytes(size: int) -> str:
    """Format a byte count using binary units."""
    value = float(size)
    units = ("B", "KB", "MB", "GB", "TB")
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.2f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


def build_summary(records: Iterable[FileRecord]) -> dict:
    """Calculate file counts and storage totals by category and extension."""
    category_sizes: dict[str, int] = defaultdict(int)
    extension_sizes: dict[str, int] = defaultdict(int)
    category_counts: dict[str, int] = defaultdict(int)
    total_bytes = 0
    total_files = 0

    for record in records:
        total_files += 1
        total_bytes += record.size_bytes
        category_sizes[record.category] += record.size_bytes
        extension_sizes[record.extension] += record.size_bytes
        category_counts[record.category] += 1

    return {
        "total_files": total_files,
        "total_bytes": total_bytes,
        "total_size": format_bytes(total_bytes),
        "category_sizes": dict(sorted(category_sizes.items())),
        "extension_sizes": dict(sorted(extension_sizes.items())),
        "category_counts": dict(sorted(category_counts.items())),
    }


def largest_files(records: Iterable[FileRecord], limit: int = 10) -> list[FileRecord]:
    """Return up to limit records ordered by descending file size."""
    if limit < 1:
        raise ValueError("limit must be at least 1")
    return sorted(records, key=lambda record: record.size_bytes, reverse=True)[:limit]
