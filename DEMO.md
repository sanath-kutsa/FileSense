# FileSense Demo Guide

This guide provides a repeatable demonstration using a dedicated sample directory. It is intended for a project presentation, portfolio walkthrough, or screen recording.

## Demo goals

Show that FileSense can scan a directory, identify duplicate contents, search by metadata, preview an organization plan, apply moves only after confirmation, roll back a recorded operation, and preserve scan history and reports.

## 1. Prepare a clean demo workspace

Run these commands in Windows PowerShell from the FileSense project root. They create sample files inside `demo_workspace` and do not touch your personal folders.

```powershell
$demo = Join-Path $PWD "demo_workspace"
New-Item -ItemType Directory -Force -Path $demo | Out-Null

$sharedText = "FileSense duplicate-detection demonstration sample."
Set-Content -Path (Join-Path $demo "project-brief.txt") -Value $sharedText
Set-Content -Path (Join-Path $demo "project-brief-copy.txt") -Value $sharedText
Set-Content -Path (Join-Path $demo "meeting-notes.txt") -Value "Meeting notes: review the project architecture and testing plan."
Set-Content -Path (Join-Path $demo "analysis.py") -Value "def summarize(values):`n    return sum(values) / len(values)"
Set-Content -Path (Join-Path $demo "budget.csv") -Value "item,cost`nprinting,250`ntravel,500"

Write-Host "Demo workspace created at: $demo"
Get-ChildItem $demo
```

The two project brief files have identical contents, so the duplicate detector should group them. The remaining files provide different categories for the organization preview.

If you want to reset the demo later, first make sure you no longer need anything in this dedicated sample directory, then remove only that directory:

```powershell
Remove-Item -Recurse -Force .\demo_workspace
```

## 2. Run the demo

Run each command separately so you can pause and explain the output.

### A. Scan and export

```powershell
python main.py scan .\demo_workspace --json reports\demo-scan.json --csv reports\demo-scan.csv
```

Show the file count, storage summary, warning count, and generated report paths.

### B. Find duplicate contents

```powershell
python main.py duplicates .\demo_workspace
```

Point out that the two project brief files are grouped because their contents match, even though their names differ. This command is read-only.

### C. Search for a file type

```powershell
python main.py search .\demo_workspace --extension txt
```

This should return the text files and save another scan-history entry.

### D. Review scan history

```powershell
python main.py history --limit 10
```

Explain that scan metadata is stored locally in SQLite and does not require a separate database server.

### E. Preview organization

```powershell
python main.py organize .\demo_workspace --destination .\demo_workspace_organized
```

Pause on the preview. Explain that no files have moved yet. The plan groups files into category folders and displays their proposed destinations.

### F. Apply the plan with confirmation

```powershell
python main.py organize .\demo_workspace --destination .\demo_workspace_organized --apply
```

Review the displayed plan, then type `yes` only when prompted. Point out the operation ID and JSON journal path printed after the moves complete.

### G. Inspect the organized files

```powershell
Get-ChildItem .\demo_workspace_organized -Recurse
```

### H. Roll back the operation

```powershell
python main.py rollback .\demo_workspace_organized
```

Confirm that the original files have been restored:

```powershell
Get-ChildItem .\demo_workspace
```

Explain that rollback uses the operation journal and refuses to overwrite an occupied original path.

## 3. Recommended screenshots

Capture screenshots from your own terminal after running the commands. Keep the terminal font readable and crop out unrelated desktop content.

| Screenshot | What it should show | Suggested filename |
|---|---|---|
| Scan summary | File count, storage summary, and report export paths | `01-scan-summary.png` |
| Duplicate detection | Matching duplicate group and SHA-256 output | `02-duplicate-detection.png` |
| Search | Extension-filtered results | `03-search-results.png` |
| Organization preview | Proposed moves and preview-only safety message | `04-organization-preview.png` |
| Confirmed organization | Confirmation prompt and operation ID | `05-organization-applied.png` |
| Rollback | Successful rollback and restored file count | `06-rollback.png` |
| Repository overview | GitHub README title, feature list, and license badge | `07-github-repository.png` |
| Architecture | Diagram in ARCHITECTURE.md | `08-architecture.png` |

Do not fabricate terminal output or edit screenshots to imply a command succeeded when it did not. If output differs, investigate it and capture what actually happened.

## 4. Suggested short presentation narration

> FileSense is a Python-based file intelligence and organization tool. It scans directories and analyzes storage without changing the user's files. It detects duplicate contents using chunked SHA-256 hashing, searches files using combined metadata filters, and preserves scan history in SQLite. Its organizer is preview-first: users review proposed moves, explicitly confirm the operation, and can roll it back using a JSON journal. The project also includes automated tests, linting, structured logging, and JSON and CSV exports.

## 5. Before recording or publishing

- Run the test suite: `python -m pytest -v`.
- Run lint checks: `python -m ruff check .`.
- Check formatting: `python -m ruff format --check .`.
- Use only the dedicated demo workspace.
- Make sure no personal file paths, usernames, private files, or API keys appear in screenshots.
- Verify every screenshot reflects output you actually observed.
- Do not include the generated SQLite database or personal files in the repository.

The demo workspace, organized output, and generated reports are demonstration artifacts. Keep them out of Git unless you deliberately choose to publish sanitized sample artifacts.
