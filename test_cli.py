#!/usr/bin/env python3
"""Test script for CLI functionality."""

import sys
import subprocess


def test_cli():
    """Test the CLI by running it in a subprocess."""
    print("Testing CLI functionality...")

    try:
        # Test version command
        result = subprocess.run(
            [sys.executable, "-m", "cetools.cli.__main__", "version"],
            capture_output=True,
            text=True,
            cwd="/Users/lgw4/Developer/python/cetools",
        )

        print(f"Version command return code: {result.returncode}")
        print(f"Version command stdout: {result.stdout}")
        print(f"Version command stderr: {result.stderr}")

        # Test help command
        result = subprocess.run(
            [sys.executable, "-m", "cetools.cli.__main__", "--help"],
            capture_output=True,
            text=True,
            cwd="/Users/lgw4/Developer/python/cetools",
        )

        print(f"Help command return code: {result.returncode}")
        print(f"Help command stdout: {result.stdout}")
        print(f"Help command stderr: {result.stderr}")

    except Exception as e:
        print(f"Error testing CLI: {e}")


if __name__ == "__main__":
    test_cli()
