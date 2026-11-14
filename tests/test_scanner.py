from pathlib import Path

import pytest

from filesense.scanner import scan_directory


def test_scan_directory_collects_file_metadata(tmp_path: Path):
    sample = tmp_path / "notes.txt"
    sample.write_text("hello", encoding="utf-8")

    records, errors = scan_directory(tmp_path)

    assert errors == []
    assert len(records) == 1
    assert records[0].name == "notes.txt"
    assert records[0].size_bytes == 5
    assert records[0].extension == ".txt"
    assert records[0].category == "Documents"


def test_scan_directory_recurses_into_subdirectories(tmp_path: Path):
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "image.png").write_bytes(b"image")

    records, errors = scan_directory(tmp_path)

    assert errors == []
    assert [record.name for record in records] == ["image.png"]


def test_scan_missing_directory_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        scan_directory(tmp_path / "missing")


def test_scan_file_path_raises_not_a_directory(tmp_path: Path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("data", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        scan_directory(file_path)
