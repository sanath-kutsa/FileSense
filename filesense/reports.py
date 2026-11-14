"""Export scan results to JSON and CSV."""

import csv
import json
from collections.abc import Iterable
from pathlib import Path

from .analyzer import build_summary
from .models import FileRecord


def export_json(
    records: Iterable[FileRecord],
    destination: str | Path,
    errors: list[str] | None = None,
) -> Path:
    """Write a JSON report and return its path."""
    record_list = list(records)
    output = Path(destination).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": build_summary(record_list),
        "files": [record.to_dict() for record in record_list],
        "errors": errors or [],
    }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output


def export_csv(records: Iterable[FileRecord], destination: str | Path) -> Path:
    """Write file metadata as CSV and return its path."""
    output = Path(destination).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["name", "path", "extension", "size_bytes", "modified_at", "category"]
    with output.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_dict())
    return output
