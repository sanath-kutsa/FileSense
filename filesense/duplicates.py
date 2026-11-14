"""Content-based duplicate detection using SHA-256."""

import hashlib
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .models import FileRecord


@dataclass(frozen=True, slots=True)
class DuplicateGroup:
    """Files that have the same size and SHA-256 content digest."""

    sha256: str
    size_bytes: int
    files: tuple[FileRecord, ...]


def calculate_sha256(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Calculate a file's SHA-256 digest without loading it all into memory."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be at least 1")

    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def find_duplicates(
    records: Iterable[FileRecord],
    chunk_size: int = 1024 * 1024,
) -> tuple[list[DuplicateGroup], list[str]]:
    """Find identical files, returning duplicate groups and access errors.

    Files are grouped by size first. Only files sharing a size are hashed,
    which avoids reading files that cannot possibly be duplicates.
    """
    if chunk_size < 1:
        raise ValueError("chunk_size must be at least 1")

    candidates: dict[int, list[FileRecord]] = defaultdict(list)
    for record in records:
        candidates[record.size_bytes].append(record)

    duplicate_groups: list[DuplicateGroup] = []
    errors: list[str] = []

    for size_bytes, same_size_records in candidates.items():
        if len(same_size_records) < 2:
            continue

        digest_groups: dict[str, list[FileRecord]] = defaultdict(list)
        for record in same_size_records:
            try:
                digest = calculate_sha256(record.path, chunk_size)
            except OSError as error:
                errors.append(f"{record.path}: {error}")
                continue
            digest_groups[digest].append(record)

        for digest, matching_records in digest_groups.items():
            if len(matching_records) > 1:
                duplicate_groups.append(
                    DuplicateGroup(
                        sha256=digest,
                        size_bytes=size_bytes,
                        files=tuple(
                            sorted(matching_records, key=lambda item: item.path)
                        ),
                    )
                )

    duplicate_groups.sort(key=lambda group: (-group.size_bytes, group.sha256))
    return duplicate_groups, errors
