"""Tests for the CLI character creation command."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


def _run_cetools(args, cwd=None):
    # Run the CLI using the project's runner (uv) and explicit python3
    cmd = ["uv", "run", "python3", "-m", "cetools.cli.__main__"] + args
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return proc


def test_character_create_export_json(tmp_path):
    """Creating a character with export should write a JSON file."""
    # Use a temporary working directory so files are written there
    proc = _run_cetools(
        ["character", "create", "--template", "traveller", "--export", "json"], cwd=str(tmp_path)
    )
    assert proc.returncode == 0

    # Look for any .json file in tmp_path
    json_files = list(Path(tmp_path).glob("*.json"))
    assert json_files, "Expected a JSON file to be created"

    # Load and verify basic structure
    content = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert "name" in content
    assert "attributes" in content


def test_character_create_stdout_no_export(tmp_path):
    """Creating a character with no export should print JSON to stdout."""
    proc = _run_cetools(["character", "create", "--template", "soldier"], cwd=str(tmp_path))
    assert proc.returncode == 0
    # Expect JSON-like output
    assert "Unnamed" in proc.stdout or "name" in proc.stdout


# This file contains GitHub Copilot generated content.
