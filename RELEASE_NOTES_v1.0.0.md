# FileSense v1.0.0

**Safe File Intelligence and Organization Engine built with Python.**

FileSense is a command-line application for understanding and organizing files with a safety-first workflow. Scanning, analysis, duplicate detection, searching, and reporting are read-only. File moves are previewed first, require explicit confirmation, and can be rolled back using the operation journal.

## Highlights

- **Filesystem scanning:** Recursively scans directories and collects file metadata, categories, and storage information.
- **Storage analysis:** Summarizes storage usage by category and extension, and identifies large files.
- **Duplicate detection:** Uses chunked SHA-256 hashing to identify files with identical content.
- **File search:** Filters by name, extension, category, size, and modification date, with sorting options.
- **Scan history:** Persists scan summaries and file records in SQLite.
- **Reports:** Exports scan information to JSON and CSV.
- **Safe organization:** Builds a preview plan before moving files, supports custom extension rules, and requires explicit confirmation to apply changes.
- **Rollback:** Records organization operations in a JSON journal and supports restoring moved files.
- **Configuration and logging:** Supports environment-based configuration and console/file logging.

## Safety principles

- Scanning and analysis do not modify source files.
- Organization is preview-first.
- Applying a plan requires explicit confirmation.
- FileSense does not automatically delete files.
- Organization operations are journaled and can be rolled back when the original paths are available.

## Verification recorded for this release

The project was locally verified during Milestone 7 with:

- 52 passing tests using `py -m pytest -v`
- Ruff lint checks passing using `py -m ruff check .`
- Ruff formatting check passing using `py -m ruff format --check .`

These are the results recorded from the development verification. Run the commands again against the exact checkout you intend to use.

## Getting started

See the [README](README.md) for installation and CLI usage, [ARCHITECTURE.md](ARCHITECTURE.md) for the design, and [DEMO.md](DEMO.md) for a safe walkthrough.

## License

Released under the [MIT License](LICENSE).

---

**Version:** 1.0.0  
**Release type:** Initial stable release
