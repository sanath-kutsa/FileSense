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
- Export scan results as JSON or CSV
- Handle inaccessible files without stopping the entire scan

## Requirements

- Python 3.10 or newer
- No third-party runtime dependencies
- pytest for development and tests

## Getting started

Clone the repository and enter the project directory:

```bash
git clone https://github.com/sanath-kutsa/FileSense.git
cd FileSense
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation scripts, you can temporarily allow activation for the current terminal session with:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

## Usage

Scan and summarize a directory:

```bash
python main.py scan .
```

Scan another directory:

```bash
python main.py scan "C:/Users/YourName/Downloads"
```

List the 10 largest files:

```bash
python main.py largest . --limit 10
```

Find duplicate files:

```bash
python main.py duplicates .
```

Scan a specific directory for duplicates:

```bash
python main.py duplicates "C:/Users/YourName/Downloads"
```

Change the hashing read size (default is 1 MiB):

```bash
python main.py duplicates . --chunk-size 65536
```

Export scan results:

```bash
python main.py scan . --json reports/scan.json --csv reports/scan.csv
```

## How duplicate detection works

1. FileSense groups scanned files by their recorded size. Files with different sizes cannot have identical contents.
2. Only files sharing a size are read and hashed.
3. Each candidate is processed in fixed-size chunks with SHA-256 from Python's standard-library `hashlib` module.
4. Files with matching SHA-256 digests are reported together as a duplicate group.

Chunked reading keeps memory use bounded even when files are large. SHA-256 is used as a practical content fingerprint; a matching digest is treated as a strong indication that file contents match.

## Safety principles

- Scanning and duplicate detection are read-only.
- FileSense never deletes, renames, or moves files during these operations.
- Inaccessible files are reported as warnings and skipped.
- No file operation is performed automatically.

Future organization features will use a preview-first workflow and require explicit confirmation before changing files.

## Development and tests

Run the test suite:

```bash
python -m pytest -v
```

## Project structure

```text
FileSense/
├── filesense/
│   ├── __init__.py
│   ├── analyzer.py
│   ├── categorizer.py
│   ├── duplicates.py
│   ├── models.py
│   ├── reports.py
│   └── scanner.py
├── tests/
│   ├── test_analyzer.py
│   ├── test_categorizer.py
│   ├── test_duplicates.py
│   └── test_scanner.py
├── reports/
├── .gitignore
├── main.py
├── README.md
└── requirements-dev.txt
```

## Roadmap

- [x] Read-only recursive scanner
- [x] File type categorization
- [x] Storage summaries and largest-file analysis
- [x] JSON and CSV reports
- [x] SHA-256 duplicate detection
- [ ] Search and filtering
- [ ] SQLite scan and operation history
- [ ] Preview-first file organization with reversible operation history
- [ ] Expanded test coverage and performance profiling

## Learning goals

FileSense is a practical Python engineering project covering filesystem APIs, modular design, data modeling, hashing, algorithmic complexity, error handling, command-line interfaces, serialization, and automated testing.

## License

A license has not yet been selected.
