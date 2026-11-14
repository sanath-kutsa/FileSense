"""Search and filtering helpers for scanned file records."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from .models import FileRecord


@dataclass(frozen=True, slots=True)
class SearchCriteria:
    """Optional filters used to search a collection of file records."""

    name: str | None = None
    extensions: tuple[str, ...] = ()
    category: str | None = None
    min_size: int | None = None
    max_size: int | None = None
    modified_after: str | None = None
    modified_before: str | None = None
    sort_by: str = "name"
    descending: bool = False


def _parse_datetime(value: str | None, field_name: str) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field_name} must be a valid ISO date or datetime.") from error
    if field_name == "modified_before" and len(value) == 10:
        parsed = parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed.astimezone(timezone.utc)


def _record_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed.astimezone(timezone.utc)


def _normalize_extension(extension: str) -> str:
    value = extension.strip().lower()
    if value in {"no extension", "[no extension]"}:
        return "[no extension]"
    return value if value.startswith(".") else f".{value}"


def search_files(
    records: Iterable[FileRecord],
    criteria: SearchCriteria | None = None,
    **filters,
) -> list[FileRecord]:
    """Filter and sort file records without changing the filesystem.

    Pass either a SearchCriteria object or keyword filters, not both.
    Supported keyword filters match SearchCriteria field names.
    """
    if criteria is not None and filters:
        raise ValueError("Pass SearchCriteria or keyword filters, not both.")
    if criteria is None:
        criteria = SearchCriteria(**filters)

    if criteria.min_size is not None and criteria.min_size < 0:
        raise ValueError("min_size cannot be negative.")
    if criteria.max_size is not None and criteria.max_size < 0:
        raise ValueError("max_size cannot be negative.")
    if (
        criteria.min_size is not None
        and criteria.max_size is not None
        and criteria.min_size > criteria.max_size
    ):
        raise ValueError("min_size cannot be greater than max_size.")

    sort_keys = {
        "name": lambda item: (item.name.casefold(), item.path.casefold()),
        "size": lambda item: (item.size_bytes, item.name.casefold()),
        "modified": lambda item: (_record_datetime(item.modified_at), item.name.casefold()),
    }
    if criteria.sort_by not in sort_keys:
        raise ValueError("sort_by must be one of: name, size, modified.")

    after = _parse_datetime(criteria.modified_after, "modified_after")
    before = _parse_datetime(criteria.modified_before, "modified_before")
    if after and before and after > before:
        raise ValueError("modified_after cannot be later than modified_before.")

    extensions = {_normalize_extension(item) for item in criteria.extensions}
    name_query = criteria.name.casefold() if criteria.name else None
    category_query = criteria.category.casefold() if criteria.category else None

    matches: list[FileRecord] = []
    for record in records:
        if name_query and name_query not in record.name.casefold():
            continue
        if extensions and record.extension.lower() not in extensions:
            continue
        if category_query and record.category.casefold() != category_query:
            continue
        if criteria.min_size is not None and record.size_bytes < criteria.min_size:
            continue
        if criteria.max_size is not None and record.size_bytes > criteria.max_size:
            continue
        modified = _record_datetime(record.modified_at)
        if after and modified < after:
            continue
        if before and modified > before:
            continue
        matches.append(record)

    return sorted(matches, key=sort_keys[criteria.sort_by], reverse=criteria.descending)
