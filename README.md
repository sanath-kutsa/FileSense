# FileSense

**A safe file intelligence and organization engine built with Python.**

FileSense is a command-line application that helps you understand, search, and organize files on your computer. It scans directories, analyzes storage usage, detects duplicate file contents, keeps a history of scans, and creates organization plans that you can review before applying.

The project is designed around one rule: **your files should never be changed without your explicit permission.** Scanning and analysis are read-only. Organization starts with a preview, requires confirmation before moving files, and keeps a journal so supported moves can be rolled back.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Features

### Filesystem scanning and storage analysis
- Recursively scan directories and collect file metadata.
- Categorize common file formats.
- Summarize storage usage by category and extension.
- Identify the largest files.
- Report inaccessible files and directories as warnings without stopping the entire scan.

### Duplicate detection
- Detect duplicate file contents using SHA-256.
- Group identical files even when their names or paths differ.
- Group candidates by file size before hashing to avoid unnecessary reads.
- Read files in chunks to keep memory use bounded.

### Search and filtering
- Search by partial filename.
- Filter by one or more extensions and by category.
- Filter using minimum and maximum file sizes.
- Filter by modification date.
- Combine filters and sort results by name, size, or modification time.

### Persistent scan history
- Store scan summaries and file metadata snapshots in SQLite.
- Review previous scans from the command line.
- Use a local database powered by Python's built-in `sqlite3` module. No database server is required.

### Safe file organization
- Preview proposed moves before making changes.
- Organize files by detected category or custom extension-to-folder rules.
- Require explicit confirmation before applying a plan.
- Record successful moves in a JSON operation journal.
- Roll back recorded moves when the original paths are available.
- Refuse destination collisions instead of overwriting existing files.

### Developer-focused foundations
- Configurable database and log paths through environment variables.
- Structured console and file logging.
- JSON and CSV report exports.
- Typed data models and modular Python packages.
- Automated tests, linting, and formatting checks.

## Documentation

- [Demo Guide](DEMO.md): sample workspace setup, repeatable CLI walkthrough, screenshot checklist, and presentation narration.
- [Architecture Guide](ARCHITECTURE.md): module responsibilities, data flow, database design, organization workflow, safety boundaries, and design decisions.
- [v1.0.0 Release Notes](RELEASE_NOTES_v1.0.0.md): initial stable release highlights, safety principles, and recorded verification.
- [Version](VERSION): current project version.

## Requirements

- Python 3.10 or newer
- No third-party runtime dependencies
- Development tools are listed in `requirements-dev.txt`

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/sanath-kutsa/FileSense.git
cd FileSense
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation scripts, allow activation for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

### 3. Install development dependencies

```bash
python -m pip install -r requirements-dev.txt
```

## Command-line usage

Run commands from the project root.

### Scan a directory

Scan the current directory:

```bash
python main.py scan .
```

Scan a specific directory:

```bash
python main.py scan "C:/Users/YourName/Downloads"
```

Scans are saved to the local SQLite history database at `instance/filesense.db` by default.

### Analyze large files

List the 10 largest files:

```bash
python main.py largest . --limit 10
```

### Find duplicate files

```bash
python main.py duplicates .
```

FileSense first groups files by size, then hashes same-size candidates in chunks using SHA-256.

### Export scan reports

Export JSON and CSV reports:

```bash
python main.py scan . --json reports/scan.json --csv reports/scan.csv
```

### Search files

Search by a partial filename:

```bash
python main.py search . --name report
```

Filter by extension and category:

```bash
python main.py search . --extension pdf --category Documents
```

Filter by a size range in bytes:

```bash
python main.py search . --min-size 1024 --max-size 10485760
```

Filter by modification date using ISO date format:

```bash
python main.py search . --modified-after 2026-01-01 --modified-before 2026-12-31
```

Combine filters and sort largest first:

```bash
python main.py search . --name project --extension pdf --extension docx --sort-by size --descending
```

Supported sort keys are `name`, `size`, and `modified`. Repeat `--extension` to include multiple extensions. Search scans the selected directory and saves that scan to history.

### Organize files safely

First, preview the proposed moves. This does not move any files:

```bash
python main.py organize "C:/Users/YourName/Downloads"
```

Choose a separate destination:

```bash
python main.py organize "C:/Users/YourName/Downloads" --destination "D:/OrganizedFiles"
```

You can also define custom extension-to-folder rules. For example, create a `rules.json` file containing:

```json
{
  ".pdf": "PDF Files",
  ".jpg": "Photos",
  ".png": "Photos"
}
```

Preview the custom plan:

```bash
python main.py organize "C:/Users/YourName/Downloads" --rules rules.json
```

After reviewing the preview, request the apply prompt:

```bash
python main.py organize "C:/Users/YourName/Downloads" --rules rules.json --apply
```

FileSense asks you to type the exact word `yes` before moving files. Successful operations are recorded in `.filesense-history.json` inside the destination directory.

Roll back the latest organization operation:

```bash
python main.py rollback "D:/OrganizedFiles"
```

Or specify an operation ID:

```bash
python main.py rollback "D:/OrganizedFiles" --operation-id YOUR_OPERATION_ID
```

Rollback refuses to overwrite an occupied original path. FileSense does not automatically delete files.

### View scan history

Show the 10 most recent scans:

```bash
python main.py history
```

Show more entries:

```bash
python main.py history --limit 25
```

Use a custom SQLite database path:

```bash
python main.py scan . --database reports/custom-history.db
python main.py history --database reports/custom-history.db
```

## Configuration and logging

The following environment variables can override default paths and logging settings:

| Variable | Purpose |
|---|---|
| `FILESENSE_DATABASE` | SQLite database path |
| `FILESENSE_LOG` | Log file path |
| `FILESENSE_LOG_LEVEL` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` |

Example in PowerShell:

```powershell
$env:FILESENSE_LOG_LEVEL = "DEBUG"
$env:FILESENSE_LOG = "logs/debug.log"
```

Logs are written to the console and configured log file.

## How it works

### Duplicate detection

1. Scanned files are grouped by recorded file size. Files with different sizes cannot have identical contents.
2. Only files in the same-size groups are read and hashed.
3. Each candidate is processed in fixed-size chunks using SHA-256 from Python's standard-library `hashlib` module.
4. Files with matching digests are reported together as a duplicate group.

Chunked reading keeps memory use bounded when processing large files. A matching SHA-256 digest is treated as a strong indication that file contents are identical.

### Search

The scanner collects file records, and the search module applies the requested filters to those records. Filters can be combined, and results can be sorted by filename, file size, or modification time. Search does not change the underlying files.

### Scan history

FileSense uses Python's built-in `sqlite3` module. Each scan record stores information such as its timestamp, scanned directory, file count, total storage, summary data, and warning count. Associated file metadata is stored as a per-scan snapshot, so earlier scan records remain available after later scans.

The default database is created locally at `instance/filesense.db`. It is generated at runtime and is not intended to be committed to Git.

### Organization and rollback

Organization is a two-stage workflow. FileSense first builds a plan and displays the proposed moves. Only after the user explicitly confirms can the plan be applied. Applied moves are written to a JSON journal, which rollback uses to restore files when it is safe to do so.

## Safety principles

- Scanning, searching, analysis, and duplicate detection are read-only.
- FileSense does not delete files.
- No organization move happens during preview.
- Applying an organization plan requires explicit confirmation.
- Destination collisions are rejected rather than overwritten.
- Rollback refuses to overwrite an existing file at the original path.
- Inaccessible files and directories are reported as warnings and skipped.
- Scan history stores metadata snapshots, not copies of scanned files.

Always review an organization preview before confirming the operation.

## Development and testing

Run the full test suite:

```bash
python -m pytest -v
```

Run Ruff lint checks:

```bash
python -m ruff check .
```

Check code formatting:

```bash
python -m ruff format --check .
```

Generate a coverage report:

```bash
python -m pytest --cov=filesense --cov-report=term-missing
```

At the Milestone 7 verification point, the project had **52 passing tests**, clean Ruff lint checks, and all 24 Python files passing the Ruff formatting check.

## Project structure

```text
FileSense/
├── filesense/
│   ├── __init__.py
│   ├── analyzer.py
│   ├── categorizer.py
│   ├── config.py
│   ├── database.py
│   ├── duplicates.py
│   ├── logging_config.py
│   ├── models.py
│   ├── organizer.py
│   ├── reports.py
│   ├── scanner.py
│   └── search.py
├── tests/
│   ├── test_analyzer.py
│   ├── test_categorizer.py
│   ├── test_cli_organization.py
│   ├── test_configuration.py
│   ├── test_database.py
│   ├── test_duplicates.py
│   ├── test_organizer.py
│   ├── test_reports.py
│   ├── test_scanner.py
│   └── test_search.py
├── reports/
├── .gitignore
├── LICENSE
├── ARCHITECTURE.md
├── DEMO.md
├── RELEASE_NOTES_v1.0.0.md
├── VERSION
├── main.py
├── README.md
└── requirements-dev.txt
```

## Roadmap

- [x] Read-only recursive filesystem scanner
- [x] File categorization and storage analysis
- [x] JSON and CSV report exports
- [x] SHA-256 duplicate detection
- [x] Search and filtering
- [x] SQLite scan history
- [x] Preview-first organization with operation journal and rollback
- [x] Configurable runtime settings and structured logging
- [x] Expanded automated tests and code-quality checks
- [x] MIT License
- [x] Core project documentation
- [ ] Create a tagged GitHub release
- [ ] Optional performance profiling and optimization

## Learning goals

FileSense is a practical Python engineering project covering filesystem APIs, modular design, data modeling, hashing, search and filtering, SQLite persistence, algorithmic complexity, error handling, command-line interfaces, serialization, logging, and automated testing.

## License

FileSense is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for the full license text.

Copyright (c) 2026 sanath-kutsa.
