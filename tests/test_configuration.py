import pytest

from filesense.config import FileSenseConfig
from filesense.logging_config import configure_logging


def test_configuration_reads_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("FILESENSE_DATABASE", str(tmp_path / "custom.db"))
    monkeypatch.setenv("FILESENSE_LOG", str(tmp_path / "logs" / "app.log"))
    monkeypatch.setenv("FILESENSE_LOG_LEVEL", "DEBUG")

    config = FileSenseConfig.from_environment()

    assert config.database_path == tmp_path / "custom.db"
    assert config.log_path == tmp_path / "logs" / "app.log"
    assert config.log_level == "DEBUG"


def test_configuration_rejects_invalid_log_level(monkeypatch):
    monkeypatch.setenv("FILESENSE_LOG_LEVEL", "LOUD")
    with pytest.raises(ValueError):
        FileSenseConfig.from_environment()


def test_logging_writes_to_file(tmp_path):
    logger = configure_logging(tmp_path / "filesense.log", "INFO")
    logger.info("test message")
    for handler in logger.handlers:
        handler.flush()
    assert "test message" in (tmp_path / "filesense.log").read_text(encoding="utf-8")
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def test_logging_rejects_invalid_level(tmp_path):
    with pytest.raises(ValueError):
        configure_logging(tmp_path / "filesense.log", "LOUD")
