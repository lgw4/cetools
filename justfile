# justfile for common tasks

# Run tests

test:
 # run pytest inside uv environment
 uv run pytest -q

# Run linters

lint:
 uv run ruff src tests

# Format code

fmt:
 uv run black src tests

# Start a development shell

dev:
 uv shell

# This file contains GitHub Copilot generated content
