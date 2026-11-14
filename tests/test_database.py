from filesense.database import list_scans, save_scan
from filesense.models import FileRecord


def make_record(name="notes.txt", size=12):
    return FileRecord(
        name=name,
        path=f"/tmp/{name}",
        extension=".txt",
        size_bytes=size,
        modified_at="2026-01-01T00:00:00+00:00",
        category="Documents",
    )


def test_save_scan_persists_scan_and_file_records(tmp_path):
    database = tmp_path / "history" / "filesense.db"
    scan_id = save_scan(tmp_path, [make_record()], [], database)

    history = list_scans(database_path=database)

    assert scan_id == 1
    assert len(history) == 1
    assert history[0]["total_files"] == 1
    assert history[0]["total_bytes"] == 12
    assert history[0]["summary"]["category_counts"] == {"Documents": 1}


def test_save_scan_records_errors_and_multiple_files(tmp_path):
    database = tmp_path / "filesense.db"
    save_scan(
        tmp_path,
        [make_record(), make_record("second.txt", 20)],
        ["permission denied"],
        database,
    )

    history = list_scans(database_path=database)

    assert history[0]["total_files"] == 2
    assert history[0]["total_bytes"] == 32
    assert history[0]["error_count"] == 1


def test_history_is_newest_first_and_obeys_limit(tmp_path):
    database = tmp_path / "filesense.db"
    save_scan(tmp_path, [make_record("first.txt")], database_path=database)
    save_scan(tmp_path, [make_record("second.txt")], database_path=database)

    history = list_scans(limit=1, database_path=database)

    assert len(history) == 1
    assert history[0]["id"] == 2


def test_missing_database_returns_empty_history(tmp_path):
    assert list_scans(database_path=tmp_path / "missing.db") == []


def test_history_rejects_invalid_limit(tmp_path):
    try:
        list_scans(limit=0, database_path=tmp_path / "filesense.db")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for an invalid history limit.")
