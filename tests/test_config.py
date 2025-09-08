"""Tests for the config module."""

import os
import pathlib
import tempfile
from unittest import mock

import pytest
import tomli
import tomli_w

from cetools.core.config import (
    DEFAULT_CONFIG,
    get_config_value,
    load_config,
    save_config,
    set_config_value,
)


class TestConfig:
    """Tests for the configuration management functions."""

    @pytest.fixture
    def mock_config_path(self):
        """Create a temporary directory for config testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            config_dir = temp_path / "cetools"
            config_file = config_dir / "config.toml"

            with (
                mock.patch("cetools.core.config.CONFIG_DIR", config_dir),
                mock.patch("cetools.core.config.CONFIG_FILE", config_file),
            ):
                yield config_file

    def test_load_config_default(self, mock_config_path):
        """Test loading the configuration when the file doesn't exist."""
        config = load_config()
        assert config == DEFAULT_CONFIG

    def test_save_and_load_config(self, mock_config_path):
        """Test saving and loading a configuration."""
        test_config = {
            "general": {
                "export_format": "yaml",
                "output_format": "json",
            },
            "character": {
                "default_template": "custom",
            },
        }

        save_config(test_config)
        loaded_config = load_config()

        assert loaded_config == test_config
        assert mock_config_path.exists()

    def test_get_config_value(self, mock_config_path):
        """Test getting a specific configuration value."""
        save_config(DEFAULT_CONFIG)

        assert get_config_value("general", "export_format") == "json"
        assert get_config_value("character", "default_template") == "traveller"
        assert get_config_value("nonexistent", "key") is None
        assert get_config_value("nonexistent", "key", "default") == "default"

    def test_set_config_value(self, mock_config_path):
        """Test setting a specific configuration value."""
        save_config(DEFAULT_CONFIG)

        set_config_value("general", "export_format", "yaml")
        assert get_config_value("general", "export_format") == "yaml"

        # Test creating a new section
        set_config_value("new_section", "new_key", "new_value")
        assert get_config_value("new_section", "new_key") == "new_value"


# This file contains GitHub Copilot generated content.
