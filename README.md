# FileSense

**Safe File Intelligence and Organization Engine built with Python.**

FileSense is a command-line tool that scans directories, turns filesystem contents into useful information, and helps users understand how their storage is being used. It is being developed with a safety-first approach: scanning and analysis are read-only and do not move or delete files.

## Current capabilities

- Recursively scan a directory and collect file metadata
- Categorize common file formats
- Summarize storage usage by category and extension
- Find the largest files
- Detect identical file contents using SHA-256 hashing
- Group duplicate files even when their names differ
- Search by partial filename, extension, category, file size, and modification date
- Combine multiple search filters and sort matching files
- Save scan summaries and file metadata in a local SQLite database
- Review previous scans through persistent scan history
- Export scan results as JSON or CSV
- Handle inaccessible files without stopping the entire scan

## Requirements

- Python 3.10 or newer
- No third-party runtime dependencies
- pytest for development and tests

## Getting started

Clone the repository and enter the project directory:

    git clone https://github.com/sanath-kutsa/FileSense.git
    cd FileSense

Create a virtual environment:

    python -m venv .venv

Activate it in Windows PowerShell:

    .\.venv\Scripts\Activate.ps1

If PowerShell blocks activation scripts, you can temporarily allow activation for the current terminal session with:

    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\.venv\Scripts\Activate.ps1

Install development dependencies:

    python -m pip install -r requirements-dev.txt

## Usage

Scan and summarize a directory. Every scan is saved to the local SQLite history database at `instance/filesense.db` by default:

    python main.py scan .

Scan another directory:

    python main.py scan "C:/Users/YourName/Downloads"

List the 10 largest files:

    python main.py largest . --limit 10

Find duplicate files:

    python main.py duplicates .

Export scan results:

    python main.py scan . --json reports/scan.json --csv reports/scan.csv

### Intelligent search

Search by a partial filename:

    python main.py search . --name report

Filter by extension and category:

    python main.py search . --extension pdf --category Documents

Use a size range in bytes:

    python main.py search . --min-size 1024 --max-size 10485760

Filter by modification date. Dates and times use ISO format:

    python main.py search . --modified-after 2026-01-01 --modified-before 2026-12-31

Combine filters and sort largest first:

    python main.py search . --name project --extension pdf --extension docx --sort-by size --descending

Supported sort keys are `name`, `size`, and `modified`. Repeat `--extension` to match more than one extension. Search scans the selected directory and saves that scan to history.

### Scan history

Show the 10 most recent scans:

    python main.py history

Show more entries:

    python main.py history --limit 25

Choose a different SQLite database location:

    python main.py scan . --database reports/custom-history.db
    python main.py history --database reports/custom-history.db

## How duplicate detection works

1. FileSense groups scanned files by their recorded size. Files with different sizes cannot have identical contents.
2. Only files sharing a size are read and hashed.
3. Each candidate is processed in fixed-size chunks with SHA-256 from Python's standard-library `hashlib` module.
4. Files with matching SHA-256 digests are reported together as a duplicate group.

Chunked reading keeps memory use bounded even when files are large. SHA-256 is used as a practical content fingerprint; a matching digest is treated as a strong indication that file contents match.

## How search works

The search module receives the file records collected by the scanner and applies the requested filters in memory. Filters can be combined, and the final results can be sorted by filename, file size, or modification time. Search never changes the underlying files.

## How scan history works

FileSense uses Python's built-in `sqlite3` module, so no database server or additional runtime package is required. Each saved scan has a timestamp, scanned directory, file count, total storage, summary data, and warning count. The associated file metadata is stored as a per-scan snapshot, allowing historical records to remain available even after later scans.

The default database is stored locally at `instance/filesense.db`. It is generated at runtime and is not intended to be committed to Git.

## Safety principles

- Scanning, searching, and duplicate detection are read-only.
- FileSense never deletes, renames, or moves files during these operations.
- Inaccessible files are reported as warnings and skipped.
- Scan history stores metadata snapshots, not copies of the scanned files.
- No file operation is performed automatically.

Future organization features will use a preview-first workflow and require explicit confirmation before changing files.

## Development and tests

Run the test suite:

    python -m pytest -v

## Project structure

    FileSense/
    ├── filesense/
    │   ├── __init__.py
    │   ├── analyzer.py
    │   ├── categorizer.py
    │   ├── database.py
    │   ├── duplicates.py
    │   ├── models.py
    │   ├── reports.py
    │   ├── scanner.py
    │   └── search.py
    ├── tests/
    │   ├── test_analyzer.py
    │   ├── test_categorizer.py
    │   ├── test_database.py
    │   ├── test_duplicates.py
    │   ├── test_scanner.py
    │   └── test_search.py
    ├── reports/
    ├── .gitignore
    ├── main.py
    ├── README.md
    └── requirements-dev.txt

## Roadmap

- [x] Read-only recursive scanner
- [x] File type categorization
- [x] Storage summaries and largest-file analysis
- [x] JSON and CSV reports
- [x] SHA-256 duplicate detection
- [x] Search and filtering
- [x] SQLite scan history
- [ ] Preview-first file organization with reversible operation history
- [ ] Expanded test coverage and performance profiling
- [ ] Final release and documentation polish

## Learning goals

FileSense is a practical Python engineering project covering filesystem APIs, modular design, data modeling, hashing, search and filtering, SQLite persistence, algorithmic complexity, error handling, command-line interfaces, serialization, and automated testing.

## License

A license has not yet been selected.
