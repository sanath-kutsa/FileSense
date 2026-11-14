from datetime import datetime, timezone

import pytest

from filesense.models import FileRecord
from filesense.search import SearchCriteria, search_files


def make_record(name, extension, size, category, modified):
    return FileRecord(
        name=name,
        path=f"/tmp/{name}",
        extension=extension,
        size_bytes=size,
        modified_at=modified,
        category=category,
    )


@pytest.fixture
def records():
    return [
        make_record("Project Notes.txt", ".txt", 100, "Documents", "2026-01-01T10:00:00+00:00"),
        make_record("holiday.png", ".png", 500, "Images", "2026-02-01T10:00:00+00:00"),
        make_record("project-plan.PDF", ".pdf", 300, "Documents", "2026-03-01T10:00:00+00:00"),
        make_record("archive", "[no extension]", 50, "Other", "2025-12-01T10:00:00+00:00"),
    ]


def test_search_by_partial_name_is_case_insensitive(records):
    found = search_files(records, name="PROJECT")
    assert {item.name for item in found} == {"Project Notes.txt", "project-plan.PDF"}


def test_search_by_extension_accepts_dot_or_no_dot(records):
    found = search_files(records, extensions=("PDF",))
    assert [item.name for item in found] == ["project-plan.PDF"]


def test_search_by_category_and_size(records):
    found = search_files(records, category="documents", min_size=100, max_size=200)
    assert [item.name for item in found] == ["Project Notes.txt"]


def test_search_combines_extension_and_name_filters(records):
    found = search_files(records, name="project", extensions=(".pdf", ".txt"))
    assert len(found) == 2


def test_search_by_modified_date_is_inclusive(records):
    found = search_files(records, modified_after="2026-02-01", modified_before="2026-02-01T10:00:00+00:00")
    assert [item.name for item in found] == ["holiday.png"]


def test_search_sorts_by_size_descending(records):
    found = search_files(records, sort_by="size", descending=True)
    assert [item.size_bytes for item in found] == [500, 300, 100, 50]


def test_search_supports_no_extension(records):
    found = search_files(records, extensions=("no extension",))
    assert [item.name for item in found] == ["archive"]


def test_search_rejects_invalid_ranges_and_sort_keys(records):
    with pytest.raises(ValueError):
        search_files(records, min_size=500, max_size=100)
    with pytest.raises(ValueError):
        search_files(records, sort_by="unknown")
    with pytest.raises(ValueError):
        search_files(records, modified_after="not-a-date")
