from pathlib import Path

import pytest

from filesense.duplicates import calculate_sha256, find_duplicates
from filesense.models import FileRecord


def make_record(path: Path) -> FileRecord:
    stat = path.stat()
    return FileRecord(
        name=path.name,
        path=str(path),
        extension=path.suffix.lower() or "[no extension]",
        size_bytes=stat.st_size,
        modified_at="2026-01-01T00:00:00+00:00",
        category="Other",
    )


def test_finds_same_content_with_different_names(tmp_path: Path):
    first = tmp_path / "report.txt"
    second = tmp_path / "report_backup.txt"
    first.write_bytes(b"same content")
    second.write_bytes(b"same content")

    groups, errors = find_duplicates([make_record(first), make_record(second)])

    assert errors == []
    assert len(groups) == 1
    assert groups[0].size_bytes == len(b"same content")
    assert {record.name for record in groups[0].files} == {
        "report.txt",
        "report_backup.txt",
    }


def test_same_size_but_different_content_is_not_duplicate(tmp_path: Path):
    first = tmp_path / "first.txt"
    second = tmp_path / "other.txt"
    first.write_bytes(b"alpha")
    second.write_bytes(b"bravo")

    groups, errors = find_duplicates([make_record(first), make_record(second)])

    assert groups == []
    assert errors == []


def test_empty_files_are_detected_as_duplicates(tmp_path: Path):
    first = tmp_path / "empty-one"
    second = tmp_path / "empty-two"
    first.write_bytes(b"")
    second.write_bytes(b"")

    groups, errors = find_duplicates([make_record(first), make_record(second)])

    assert errors == []
    assert len(groups) == 1
    assert groups[0].size_bytes == 0


def test_unique_file_is_not_hashed_as_a_duplicate_candidate(tmp_path: Path):
    only_file = tmp_path / "unique.bin"
    only_file.write_bytes(b"unique")
    missing = FileRecord(
        name="missing.bin",
        path=str(tmp_path / "missing.bin"),
        extension=".bin",
        size_bytes=100,
        modified_at="2026-01-01T00:00:00+00:00",
        category="Other",
    )

    groups, errors = find_duplicates([make_record(only_file), missing])

    assert groups == []
    assert errors == []


def test_hashing_uses_chunks_and_validates_chunk_size(tmp_path: Path):
    sample = tmp_path / "large-ish.bin"
    sample.write_bytes(b"abcdefgh" * 100)

    assert calculate_sha256(sample, chunk_size=7) == calculate_sha256(sample)
    with pytest.raises(ValueError):
        calculate_sha256(sample, chunk_size=0)


def test_unreadable_candidate_is_reported(tmp_path: Path):
    readable = tmp_path / "readable.txt"
    missing = tmp_path / "missing.txt"
    readable.write_bytes(b"same")
    missing_record = FileRecord(
        name=missing.name,
        path=str(missing),
        extension=".txt",
        size_bytes=4,
        modified_at="2026-01-01T00:00:00+00:00",
        category="Documents",
    )

    groups, errors = find_duplicates([make_record(readable), missing_record])

    assert groups == []
    assert len(errors) == 1
    assert str(missing) in errors[0]
