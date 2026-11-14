from pathlib import Path

import pytest

from filesense.models import FileRecord
from filesense.organizer import (
    apply_organization_plan,
    build_organization_plan,
    rollback_organization,
)

def record(path: Path, category: str = "Documents") -> FileRecord:
    stat = path.stat()
    return FileRecord(
        name=path.name,
        path=str(path.resolve()),
        extension=path.suffix.lower() or "[no extension]",
        size_bytes=stat.st_size,
        modified_at="2026-01-01T00:00:00+00:00",
        category=category,
    )

def test_plan_uses_category_and_does_not_move_files(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    sample = source / "notes.txt"
    sample.write_text("hello", encoding="utf-8")
    destination = tmp_path / "organized"

    plan = build_organization_plan([record(sample)], destination)

    assert len(plan) == 1
    assert plan[0].destination == destination / "Documents" / "notes.txt"
    assert sample.exists()
    assert not destination.exists()

def test_custom_extension_rule_overrides_category(tmp_path):
    sample = tmp_path / "report.pdf"
    sample.write_text("pdf", encoding="utf-8")
    plan = build_organization_plan([record(sample)], tmp_path / "out", {".pdf": "PDF Files"})
    assert plan[0].destination.parent.name == "PDF Files"

def test_plan_rejects_existing_destination(tmp_path):
    sample = tmp_path / "report.txt"
    sample.write_text("data", encoding="utf-8")
    target = tmp_path / "out" / "Documents"
    target.mkdir(parents=True)
    (target / sample.name).write_text("existing", encoding="utf-8")
    with pytest.raises(FileExistsError):
        build_organization_plan([record(sample)], tmp_path / "out")

def test_plan_rejects_unsafe_rule_folder(tmp_path):
    sample = tmp_path / "report.txt"
    sample.write_text("data", encoding="utf-8")
    with pytest.raises(ValueError):
        build_organization_plan([record(sample)], tmp_path / "out", {".txt": "../outside"})

def test_apply_requires_explicit_confirmation(tmp_path):
    sample = tmp_path / "notes.txt"
    sample.write_text("hello", encoding="utf-8")
    plan = build_organization_plan([record(sample)], tmp_path / "out")
    with pytest.raises(PermissionError):
        apply_organization_plan(plan, tmp_path / "out")
    assert sample.exists()

def test_apply_and_rollback_restore_original_file(tmp_path):
    sample = tmp_path / "notes.txt"
    sample.write_text("hello", encoding="utf-8")
    destination = tmp_path / "out"
    plan = build_organization_plan([record(sample)], destination)
    applied = apply_organization_plan(plan, destination, confirmed=True)
    moved = destination / "Documents" / "notes.txt"

    assert not sample.exists()
    assert moved.read_text(encoding="utf-8") == "hello"

    rolled_back = rollback_organization(destination, applied.operation_id)

    assert rolled_back.operation_id == applied.operation_id
    assert sample.read_text(encoding="utf-8") == "hello"
    assert not moved.exists()

def test_rollback_refuses_to_overwrite_original_path(tmp_path):
    sample = tmp_path / "notes.txt"
    sample.write_text("hello", encoding="utf-8")
    destination = tmp_path / "out"
    applied = apply_organization_plan(
        build_organization_plan([record(sample)], destination),
        destination,
        confirmed=True,
    )
    sample.write_text("new content", encoding="utf-8")
    with pytest.raises(FileExistsError):
        rollback_organization(destination, applied.operation_id)
