"""Consistent application logging configuration."""

import logging
from pathlib import Path

def configure_logging(log_path: str | Path, level: str = "INFO") -> logging.Logger:
    """Configure a named logger with console and rotating-free file output."""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Unsupported logging level: {level}")

    logger = logging.getLogger("filesense")
    logger.setLevel(numeric_level)
    logger.propagate = False
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console = logging.StreamHandler()
    console.setLevel(numeric_level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    path = Path(log_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(path, encoding="utf-8")
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger
