"""CLI integration tests for organization and rollback workflows."""

import sys

import main as cli


def test_history_parser_uses_centralized_database_default():
    args = cli.create_parser().parse_args(["history"])
    assert args.database == cli.CONFIG.database_path


def test_organize_preview_apply_and_rollback_cli_workflow(
    tmp_path, monkeypatch
):
    source = tmp_path / "source"
    source.mkdir()
    samples = {
        "notes.txt": "notes",
        "report.pdf": "report",
        "photo.jpg": "photo",
    }
    for name, contents in samples.items():
        (source / name).write_text(contents, encoding="utf-8")

    destination = tmp_path / "organized"
    monkeypatch.setattr(cli, "configure_logging", lambda *_args: None)

    # Preview must not create the destination or move any source files.
    monkeypatch.setattr(
        sys,
        "argv",
        ["filesense", "organize", str(source), "--destination", str(destination)],
    )
    assert cli.main() == 0
    assert not destination.exists()
    assert all((source / name).is_file() for name in samples)

    # Applying requires the exact confirmation and then moves every file.
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "filesense",
            "organize",
            str(source),
            "--destination",
            str(destination),
            "--apply",
        ],
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: "yes")
    assert cli.main() == 0
    assert not any((source / name).exists() for name in samples)
    assert (destination / "Documents" / "notes.txt").read_text(encoding="utf-8") == "notes"
    assert (destination / "Documents" / "report.pdf").read_text(encoding="utf-8") == "report"
    assert (destination / "Images" / "photo.jpg").read_text(encoding="utf-8") == "photo"
    assert (destination / ".filesense-history.json").is_file()

    # The CLI rollback command must restore the original files and contents.
    monkeypatch.setattr(
        sys,
        "argv",
        ["filesense", "rollback", str(destination)],
    )
    assert cli.main() == 0
    for name, contents in samples.items():
        assert (source / name).read_text(encoding="utf-8") == contents
