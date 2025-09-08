"""Configuration management for CETools."""

import os
import pathlib
from typing import Any, Dict, Optional

import tomli
import tomli_w

# Constants for configuration paths
CONFIG_DIR = (
    pathlib.Path(os.environ.get("XDG_CONFIG_HOME", pathlib.Path.home() / ".config")) / "cetools"
)
CONFIG_FILE = CONFIG_DIR / "config.toml"
DEFAULT_CONFIG = {
    "general": {
        "export_format": "json",
        "output_format": "text",
    },
    "character": {
        "default_template": "traveller",
    },
    "dice": {
        "d66_unordered": False,
    },
}


def ensure_config_dir() -> None:
    """Ensure the configuration directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """Load the configuration file."""
    ensure_config_dir()

    if not CONFIG_FILE.exists():
        # If the config file doesn't exist, create it with default values
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "rb") as f:
            return tomli.load(f)
    except (tomli.TOMLDecodeError, OSError) as e:
        # If there's an error loading the config, return the default
        print(f"Error loading configuration: {e}")
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> None:
    """Save the configuration to the config file."""
    ensure_config_dir()

    try:
        with open(CONFIG_FILE, "wb") as f:
            tomli_w.dump(config, f)
    except OSError as e:
        print(f"Error saving configuration: {e}")


def get_config_value(section: str, key: str, default: Optional[Any] = None) -> Any:
    """Get a specific configuration value."""
    config = load_config()
    return config.get(section, {}).get(key, default)


def set_config_value(section: str, key: str, value: Any) -> None:
    """Set a specific configuration value."""
    config = load_config()

    if section not in config:
        config[section] = {}

    config[section][key] = value
    save_config(config)


# This file contains GitHub Copilot generated content.
