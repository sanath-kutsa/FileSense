"""Map common file extensions to human-readable categories."""

from pathlib import Path

CATEGORY_EXTENSIONS: dict[str, set[str]] = {
    "Documents": {".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md"},
    "Images": {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".svg",
        ".webp",
        ".tif",
        ".tiff",
    },
    "Videos": {".mp4", ".mkv", ".mov", ".avi", ".webm", ".wmv"},
    "Audio": {".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"},
    "Archives": {".zip", ".tar", ".gz", ".bz2", ".7z", ".rar"},
    "Code": {
        ".py",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".go",
        ".rs",
        ".php",
        ".sql",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
    },
    "Spreadsheets": {".csv", ".xls", ".xlsx", ".ods"},
    "Presentations": {".ppt", ".pptx", ".odp"},
}


def categorize_extension(extension: str) -> str:
    """Return the category for an extension, or 'Other' if unknown."""
    normalized = extension.lower()
    for category, extensions in CATEGORY_EXTENSIONS.items():
        if normalized in extensions:
            return category
    return "Other"


def categorize_path(path: Path) -> str:
    """Categorize a path based on its suffix."""
    return categorize_extension(path.suffix.lower() or "[no extension]")
