import pytest

from filesense.analyzer import build_summary, format_bytes, largest_files
from filesense.models import FileRecord


def make_record(name: str, size: int, category: str = "Documents") -> FileRecord:
    return FileRecord(
        name=name,
        path=f"/tmp/{name}",
        extension=".txt",
        size_bytes=size,
        modified_at="2026-01-01T00:00:00+00:00",
        category=category,
    )


def test_summary_totals_and_categories():
    records = [make_record("a.txt", 100), make_record("b.txt", 300, "Other")]
    summary = build_summary(records)
    assert summary["total_files"] == 2
    assert summary["total_bytes"] == 400
    assert summary["category_sizes"] == {"Documents": 100, "Other": 300}


def test_largest_files_are_sorted_descending():
    records = [make_record("small.txt", 10), make_record("large.txt", 500)]
    assert largest_files(records, 1)[0].name == "large.txt"


def test_largest_files_rejects_invalid_limit():
    with pytest.raises(ValueError):
        largest_files([], 0)


def test_format_bytes():
    assert format_bytes(512) == "512 B"
    assert format_bytes(1024) == "1.00 KB"
