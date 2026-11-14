"""Command-line interface for FileSense."""

import argparse
from pathlib import Path

from filesense.analyzer import build_summary, format_bytes, largest_files
from filesense.duplicates import find_duplicates
from filesense.reports import export_csv, export_json
from filesense.scanner import scan_directory


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

    return parser


def run_scan(directory: Path, json_path: str | None, csv_path: str | None) -> int:
    records, errors = scan_directory(directory)
    summary = build_summary(records)

    print(f"\nFileSense scan: {directory.expanduser().resolve()}")
    print(f"Files scanned : {summary['total_files']}")
    print(f"Total storage : {summary['total_size']}")

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


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    try:
        if args.command == "scan":
            return run_scan(args.directory, args.json_path, args.csv_path)
        if args.command == "largest":
            return run_largest(args.directory, args.limit)
        if args.command == "duplicates":
            if args.chunk_size < 1:
                parser.error("--chunk-size must be at least 1")
            return run_duplicates(args.directory, args.chunk_size)
    except (FileNotFoundError, NotADirectoryError, PermissionError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
