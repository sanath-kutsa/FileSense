"""Preview-first file organization with an operation journal and rollback."""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import shutil
from typing import Iterable, Mapping
from uuid import uuid4

from .models import FileRecord

LOGGER = logging.getLogger("filesense")
HISTORY_FILENAME = ".filesense-history.json"

@dataclass(frozen=True, slots=True)
class MoveOperation:
    """A proposed move from an existing file to a destination path."""

    source: Path
    destination: Path

@dataclass(frozen=True, slots=True)
class AppliedOperation:
    """A completed move recorded for possible rollback."""

    operation_id: str
    moved_files: tuple[MoveOperation, ...]

def _safe_folder_name(value: str) -> str:
    name = value.strip()
    if not name or name in {".", ".."} or Path(name).name != name:
        raise ValueError(f"Organization folder must be a single safe name: {value!r}")
    if any(char in name for char in '<>:"/\\|?*'):
        raise ValueError(f"Organization folder contains invalid characters: {value!r}")
    return name

def build_organization_plan(
    records: Iterable[FileRecord],
    destination: str | Path,
    rules: Mapping[str, str] | None = None,
) -> list[MoveOperation]:
    """Create a deterministic move plan without changing any files.

    Rules map extensions (for example, '.pdf') to destination folder names.
    Unmatched files use their scanner category.
    """
    destination_root = Path(destination).expanduser().resolve()
    normalized_rules = {
        (key.lower() if key.startswith(".") else f".{key.lower()}"): _safe_folder_name(value)
        for key, value in (rules or {}).items()
    }
    plan: list[MoveOperation] = []
    destinations: set[Path] = set()

    for record in records:
        source = Path(record.path).expanduser().resolve()
        if not source.is_file():
            LOGGER.warning("Skipping missing or non-file source: %s", source)
            continue
        try:
            source.relative_to(destination_root)
        except ValueError:
            pass
        else:
            # Never attempt to organize files already inside the target tree.
            continue

        folder = normalized_rules.get(record.extension.lower(), _safe_folder_name(record.category))
        target = (destination_root / folder / source.name).resolve()
        if target == source:
            continue
        try:
            target.relative_to(destination_root)
        except ValueError as error:
            raise ValueError("Planned destination escaped the organization directory.") from error
        if target.exists() or target in destinations:
            raise FileExistsError(
                f"Destination already exists or is duplicated: {target}. "
                "Resolve the name conflict before applying the plan."
            )
        destinations.add(target)
        plan.append(MoveOperation(source=source, destination=target))
    return plan

def _history_path(destination: str | Path) -> Path:
    return Path(destination).expanduser().resolve() / HISTORY_FILENAME

def _read_history(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read FileSense operation history: {error}") from error
    if not isinstance(data, list):
        raise ValueError("FileSense operation history has an invalid format.")
    return data

def _write_history(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(entries, indent=2), encoding="utf-8")
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()

def apply_organization_plan(
    plan: Iterable[MoveOperation],
    destination: str | Path,
    *,
    confirmed: bool = False,
) -> AppliedOperation:
    """Apply a plan only when explicitly confirmed; revert partial moves on error."""
    if not confirmed:
        raise PermissionError("Applying moves requires explicit confirmation.")
    operations = tuple(plan)
    if not operations:
        raise ValueError("There are no file moves to apply.")

    destination_root = Path(destination).expanduser().resolve()
    for operation in operations:
        source = operation.source.expanduser().resolve()
        target = operation.destination.expanduser().resolve()
        try:
            target.relative_to(destination_root)
        except ValueError as error:
            raise ValueError("A planned destination is outside the organization directory.") from error
        try:
            source.relative_to(destination_root)
        except ValueError:
            pass
        else:
            raise ValueError("A source file cannot already be inside the organization directory.")
        if source == target:
            raise ValueError("Source and destination paths must be different.")
        if not source.is_file():
            raise FileNotFoundError(f"Source file no longer exists: {source}")
        if target.exists():
            raise FileExistsError(f"Destination already exists: {target}")

    operation_id = uuid4().hex
    completed: list[MoveOperation] = []
    try:
        for operation in operations:
            operation.destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(operation.source), str(operation.destination))
            completed.append(operation)
            LOGGER.info("Moved %s -> %s", operation.source, operation.destination)
    except OSError:
        for operation in reversed(completed):
            operation.source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(operation.destination), str(operation.source))
        raise

    entry = {
        "operation_id": operation_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "rolled_back": False,
        "moves": [
            {"source": str(item.source), "destination": str(item.destination)}
            for item in completed
        ],
    }
    history_path = _history_path(destination)
    entries = _read_history(history_path)
    entries.append(entry)
    try:
        _write_history(history_path, entries)
    except OSError:
        # Do not leave moved files without a recoverable operation record.
        for operation in reversed(completed):
            operation.source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(operation.destination), str(operation.source))
        raise
    LOGGER.info("Organization operation %s completed (%d files)", operation_id, len(completed))
    return AppliedOperation(operation_id=operation_id, moved_files=tuple(completed))

def rollback_organization(
    destination: str | Path,
    operation_id: str = "latest",
) -> AppliedOperation:
    """Reverse a recorded operation, refusing to overwrite any existing source."""
    history_path = _history_path(destination)
    entries = _read_history(history_path)
    candidates = [
        item for item in entries
        if not item.get("rolled_back") and (operation_id == "latest" or item.get("operation_id") == operation_id)
    ]
    if not candidates:
        raise ValueError(f"No active organization operation found for: {operation_id}")
    entry = candidates[-1]
    operations = tuple(
        MoveOperation(Path(item["source"]), Path(item["destination"]))
        for item in entry["moves"]
    )
    destination_root = Path(destination).expanduser().resolve()
    for operation in operations:
        try:
            operation.destination.resolve().relative_to(destination_root)
        except ValueError as error:
            raise ValueError("Operation journal contains a destination outside its organization directory.") from error
        if not operation.source.is_absolute():
            raise ValueError("Operation journal contains a non-absolute original path.")
    for operation in operations:
        if not operation.destination.is_file():
            raise FileNotFoundError(f"Moved file is missing: {operation.destination}")
        if operation.source.exists():
            raise FileExistsError(
                f"Cannot roll back because the original path is occupied: {operation.source}"
            )

    restored: list[MoveOperation] = []
    try:
        for operation in reversed(operations):
            operation.source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(operation.destination), str(operation.source))
            restored.append(operation)
            LOGGER.info("Restored %s -> %s", operation.destination, operation.source)
    except OSError:
        for operation in reversed(restored):
            operation.destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(operation.source), str(operation.destination))
        raise

    entry["rolled_back"] = True
    entry["rolled_back_at"] = datetime.now(timezone.utc).isoformat()
    _write_history(history_path, entries)
    LOGGER.info("Organization operation %s rolled back", entry["operation_id"])
    return AppliedOperation(operation_id=entry["operation_id"], moved_files=operations)
