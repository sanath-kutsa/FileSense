# FileSense

**Safe File Intelligence and Organization Engine built with Python.**

FileSense is a command-line tool that scans directories, turns filesystem contents into useful information, and helps users understand how their storage is being used. It is being developed with a safety-first approach: the initial release is read-only and does not move or delete files.

## Current capabilities

- Recursively scan a directory using Python's `pathlib`
- Collect file names, extensions, sizes, paths, and modification timestamps
- Categorize common file formats
- Summarize storage usage by category and extension
- Find the largest files
- Export scan results as JSON or CSV
- Handle inaccessible files without crashing the entire scan

## Requirements

- Python 3.10 or newer
- No third-party runtime dependencies

## Getting started

Clone the repository and enter the project directory:

```bash
git clone https://github.com/sanath-kutsa/FileSense.git
cd FileSense
```

Run a scan:

```bash
python main.py scan .
```

Scan a different directory:

```bash
python main.py scan "C:/Users/YourName/Downloads"
```

Show the largest 10 files:

```bash
python main.py largest "C:/Users/YourName/Downloads" --limit 10
```

Export results:

```bash
python main.py scan . --json reports/scan.json
python main.py scan . --csv reports/scan.csv
```

On Windows, use forward slashes in paths or wrap paths containing spaces in quotes.

## Development setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Install development dependencies and run tests:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

## Project structure

```text
FileSense/
├── filesense/
│   ├── __init__.py
│   ├── analyzer.py
│   ├── categorizer.py
│   ├── models.py
│   ├── reports.py
│   └── scanner.py
├── tests/
│   ├── test_analyzer.py
│   ├── test_categorizer.py
│   └── test_scanner.py
├── .gitignore
├── main.py
├── README.md
└── requirements-dev.txt
```

## Safety principles

1. Scanning is read-only.
2. File operations that could change user data are not part of the initial release.
3. File access errors are reported and skipped rather than causing an uncontrolled failure.
4. Reports are written only to the output paths explicitly supplied by the user.

Future organization features will use a preview-first workflow and will require explicit confirmation before changing files.

## Roadmap

- [x] Read-only recursive scanner
- [x] File type categorization
- [x] Storage summaries and largest-file analysis
- [x] JSON and CSV reports
- [ ] SHA-256 duplicate detection
- [ ] Search and filtering
- [ ] SQLite scan history
- [ ] Preview-first file organization with reversible operation history
- [ ] Expanded test coverage and performance profiling

## Learning goals

FileSense is also a practical Python engineering project. It explores filesystem APIs, modular design, data modeling, error handling, command-line interfaces, serialization, and automated testing.

## License

A license has not yet been selected.
