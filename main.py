"""Command-line interface for FileSense."""

import argparse
from pathlib import Path

from filesense.analyzer import build_summary, format_bytes, largest_files
from filesense.database import DEFAULT_DB_PATH, list_scans, save_scan
from filesense.duplicates import find_duplicates
from filesense.models import FileRecord
from filesense.reports import export_csv, export_json
from filesense.scanner import scan_directory
from filesense.search import SearchCriteria, search_files


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="filesense",
        description="Read-only filesystem intelligence and storage analysis.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan a directory and summarize its files.")
    scan_parser.add_argument("directory", type=Path, help="Directory to scan.")
    scan_parser.add_argument("--json", dest="json_path", help="Write a JSON report to this path.")
    scan_parser.add_argument("--csv", dest="csv_path", help="Write a CSV report to this path.")
    scan_parser.add_argument("--database", type=Path, default=DEFAULT_DB_PATH, help="SQLite history database path.")

    largest_parser = subparsers.add_parser("largest", help="List the largest files in a directory.")
    largest_parser.add_argument("directory", type=Path, help="Directory to scan.")
    largest_parser.add_argument("--limit", type=int, default=10, help="Number of files to show.")

    duplicate_parser = subparsers.add_parser(
        "duplicates",
        help="Find files with identical contents using SHA-256.",
    )
    duplicate_parser.add_argument("directory", type=Path, help="Directory to scan for duplicates.")
    duplicate_parser.add_argument(
        "--chunk-size",
        type=int,
        default=1024 * 1024,
        help="Bytes read per hashing operation (default: 1048576).",
    )

    search_parser = subparsers.add_parser("search", help="Search and filter files in a directory.")
    search_parser.add_argument("directory", type=Path, help="Directory to search.")
    search_parser.add_argument("--name", help="Case-insensitive partial filename match.")
    search_parser.add_argument("--extension", action="append", dest="extensions", help="Extension filter; repeat to allow multiple extensions.")
    search_parser.add_argument("--category", help="File category, such as Documents or Images.")
    search_parser.add_argument("--min-size", type=int, help="Minimum file size in bytes.")
    search_parser.add_argument("--max-size", type=int, help="Maximum file size in bytes.")
    search_parser.add_argument("--modified-after", help="Include files modified on or after this ISO date/time.")
    search_parser.add_argument("--modified-before", help="Include files modified on or before this ISO date/time.")
    search_parser.add_argument("--sort-by", choices=("name", "size", "modified"), default="name")
    search_parser.add_argument("--descending", action="store_true", help="Reverse the selected sort order.")
    search_parser.add_argument("--database", type=Path, default=DEFAULT_DB_PATH, help="SQLite history database path.")

    history_parser = subparsers.add_parser("history", help="Show recent saved scan history.")
    history_parser.add_argument("--limit", type=int, default=10, help="Number of previous scans to display.")
    history_parser.add_argument("--database", type=Path, default=DEFAULT_DB_PATH, help="SQLite history database path.")

    return parser


def persist_scan(
    directory: Path,
    records: list[FileRecord],
    errors: list[str],
    database_path: Path,
) -> int:
    return save_scan(directory, records, errors, database_path)


def run_scan(
    directory: Path,
    json_path: str | None,
    csv_path: str | None,
    database_path: Path = DEFAULT_DB_PATH,
) -> int:
    records, errors = scan_directory(directory)
    summary = build_summary(records)
    scan_id = persist_scan(directory, records, errors, database_path)

    print(f"\nFileSense scan: {directory.expanduser().resolve()}")
    print(f"Files scanned : {summary['total_files']}")
    print(f"Total storage : {summary['total_size']}")
    print(f"Saved to history as scan #{scan_id}")

    print("\nStorage by category:")
    if summary["category_sizes"]:
        for category, size in summary["category_sizes"].items():
            print(f"  {category:<16} {format_bytes(size)}")
    else:
        print("  No accessible files found.")

    if errors:
        print(f"\nWarnings: {len(errors)} file(s) could not be read.")
        for error in errors[:5]:
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more.")

    if json_path:
        print(f"\nJSON report: {export_json(records, json_path, errors)}")
    if csv_path:
        print(f"CSV report:  {export_csv(records, csv_path)}")
    return 0


def run_largest(directory: Path, limit: int) -> int:
    records, errors = scan_directory(directory)
    for record in largest_files(records, limit):
        print(f"{format_bytes(record.size_bytes):>12}  {record.path}")
    if not records:
        print("No accessible files found.")
    if errors:
        print(f"\nSkipped {len(errors)} inaccessible file(s).")
    return 0


def run_duplicates(directory: Path, chunk_size: int) -> int:
    records, scan_errors = scan_directory(directory)
    groups, hash_errors = find_duplicates(records, chunk_size=chunk_size)
    errors = scan_errors + hash_errors

    print(f"\nFileSense duplicate scan: {directory.expanduser().resolve()}")
    if not groups:
        print("No duplicate files found.")
    else:
        print(f"Duplicate groups found: {len(groups)}")
        total_redundant_bytes = 0
        for index, group in enumerate(groups, start=1):
            duplicate_copies = len(group.files) - 1
            total_redundant_bytes += group.size_bytes * duplicate_copies
            print(f"\nGroup {index} | {format_bytes(group.size_bytes)} each")
            print(f"SHA-256: {group.sha256}")
            for record in group.files:
                print(f"  - {record.path}")
        print(
            "\nPotential duplicate storage: "
            f"{format_bytes(total_redundant_bytes)} "
            "(excluding the first copy in each group)"
        )

    if errors:
        print(f"\nWarnings: {len(errors)} file(s) could not be accessed or hashed.")
        for error in errors[:5]:
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more.")
    print("\nNo files were changed or deleted.")
    return 0


def run_search(args: argparse.Namespace) -> int:
    criteria = SearchCriteria(
        name=args.name,
        extensions=tuple(args.extensions or ()),
        category=args.category,
        min_size=args.min_size,
        max_size=args.max_size,
        modified_after=args.modified_after,
        modified_before=args.modified_before,
        sort_by=args.sort_by,
        descending=args.descending,
    )
    # Validate filters before creating a scan-history entry.
    search_files([], criteria)
    records, errors = scan_directory(args.directory)
    scan_id = persist_scan(args.directory, records, errors, args.database)
    matches = search_files(records, criteria)

    print(f"\nFileSense search: {args.directory.expanduser().resolve()}")
    print(f"Matching files: {len(matches)}")
    print(f"Scan saved as history entry #{scan_id}")
    for record in matches:
        print(f"{format_bytes(record.size_bytes):>12}  {record.name}  [{record.category}]")
        print(f"              {record.path}")
    if not matches:
        print("No files matched the supplied filters.")
    if errors:
        print(f"\nSkipped {len(errors)} inaccessible file(s).")
    print("\nSearch is read-only. No files were changed or deleted.")
    return 0


def run_history(limit: int, database_path: Path) -> int:
    history = list_scans(limit=limit, database_path=database_path)
    print("\nFileSense scan history")
    if not history:
        print("No saved scans yet. Run 'python main.py scan <directory>' first.")
        return 0

    for scan in history:
        print(
            f"\nScan #{scan['id']} | {scan['scanned_at']}\n"
            f"  Directory : {scan['root_path']}\n"
            f"  Files     : {scan['total_files']}\n"
            f"  Storage   : {format_bytes(scan['total_bytes'])}\n"
            f"  Warnings  : {scan['error_count']}"
        )
    return 0


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    try:
        if args.command == "scan":
            return run_scan(args.directory, args.json_path, args.csv_path, args.database)
        if args.command == "largest":
            return run_largest(args.directory, args.limit)
        if args.command == "duplicates":
            if args.chunk_size < 1:
                parser.error("--chunk-size must be at least 1")
            return run_duplicates(args.directory, args.chunk_size)
        if args.command == "search":
            return run_search(args)
        if args.command == "history":
            return run_history(args.limit, args.database)
    except (FileNotFoundError, NotADirectoryError, PermissionError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
