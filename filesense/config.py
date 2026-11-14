"""Centralized runtime configuration for FileSense."""

from dataclasses import dataclass
from pathlib import Path
import os

@dataclass(frozen=True, slots=True)
class FileSenseConfig:
    """Application paths and logging settings."""

    database_path: Path = Path("instance") / "filesense.db"
    log_path: Path = Path("logs") / "filesense.log"
    log_level: str = "INFO"

    @classmethod
    def from_environment(cls) -> "FileSenseConfig":
        """Build configuration from environment variables with safe defaults."""
        level = os.getenv("FILESENSE_LOG_LEVEL", "INFO").upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("FILESENSE_LOG_LEVEL must be a valid logging level.")
        return cls(
            database_path=Path(os.getenv("FILESENSE_DATABASE", "instance/filesense.db")),
            log_path=Path(os.getenv("FILESENSE_LOG", "logs/filesense.log")),
            log_level=level,
        )

CONFIG = FileSenseConfig.from_environment()
