# ruff: noqa: S101, PLR2004, S104
"""Tests for the configuration manager."""

from pathlib import Path

import pytest

from src.config import ConfigurationManager


def test_config_loads_valid_yaml(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test that configuration loads correctly from a valid YAML file."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  host: 0.0.0.0\n  port: 9000\n")

    monkeypatch.setenv("CONFIG_PATH", str(config_file))

    manager = ConfigurationManager()
    config = manager.get_config()

    assert config.server.host == "0.0.0.0"
    assert config.server.port == 9000


def test_config_fallback_to_defaults(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test that configuration falls back to defaults when values are missing."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("server:\n  host: 127.0.0.1\n")  # missing port

    monkeypatch.setenv("CONFIG_PATH", str(config_file))

    manager = ConfigurationManager()
    config = manager.get_config()

    assert config.server.host == "127.0.0.1"
    assert config.server.port == 8000  # default value


def test_config_missing_file_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a missing config file raises a FileNotFoundError."""
    monkeypatch.setenv("CONFIG_PATH", "/path/to/nowhere/config.yaml")

    with pytest.raises(FileNotFoundError):
        ConfigurationManager()
