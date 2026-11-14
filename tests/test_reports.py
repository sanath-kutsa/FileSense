import csv
import json

from filesense.models import FileRecord
from filesense.reports import export_csv, export_json


def make_record(name: str = "notes.txt", size: int = 5) -> FileRecord:
    return FileRecord(
        name=name,
        path=f"/tmp/{name}",
        extension=".txt",
        size_bytes=size,
        modified_at="2026-01-01T00:00:00+00:00",
        category="Documents",
    )


def test_export_json_writes_summary_files_and_errors(tmp_path):
    destination = tmp_path / "nested" / "report.json"

    result = export_json([make_record()], destination, ["permission warning"])

    payload = json.loads(result.read_text(encoding="utf-8"))
    assert result == destination
    assert payload["summary"]["total_files"] == 1
    assert payload["files"][0]["name"] == "notes.txt"
    assert payload["errors"] == ["permission warning"]


def test_export_json_handles_empty_records_and_default_errors(tmp_path):
    destination = tmp_path / "empty.json"

    export_json([], destination)

    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["summary"]["total_files"] == 0
    assert payload["files"] == []
    assert payload["errors"] == []


def test_export_csv_writes_header_and_file_metadata(tmp_path):
    destination = tmp_path / "nested" / "report.csv"

    result = export_csv([make_record()], destination)

    with result.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert result == destination
    assert rows == [{
        "name": "notes.txt",
        "path": "/tmp/notes.txt",
        "extension": ".txt",
        "size_bytes": "5",
        "modified_at": "2026-01-01T00:00:00+00:00",
        "category": "Documents",
    }]


def test_export_csv_handles_empty_records(tmp_path):
    destination = tmp_path / "empty.csv"

    export_csv([], destination)

    with destination.open(newline="", encoding="utf-8") as csv_file:
        assert list(csv.reader(csv_file)) == [
            ["name", "path", "extension", "size_bytes", "modified_at", "category"]
        ]
