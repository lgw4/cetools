# AGENTS.md

## Project layout

- Package source: `src/cetools/`
- Tests: `tests/`, mirroring the package structure (e.g. `src/cetools/foo.py` -> `tests/test_foo.py`)
- Dependencies and project metadata: `pyproject.toml`, managed with `uv`

## Setup

```bash
uv sync
```

Installs the project and all dependencies (including dev dependencies) into `.venv`.

## Running tests

```bash
uv run pytest
```

Run a single file or test:

```bash
uv run pytest tests/test_foo.py
uv run pytest tests/test_foo.py::test_bar -v
```

All new code should have corresponding tests in `tests/`. Run the full suite before considering a task complete.

## Code style

- Format with Black: `uv run black .`
- Lint with flake8: `uv run flake8 src tests`
- Both should be run (and pass) before finishing a change.

## PR instructions

- Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for all commit messages and PR titles (e.g., `feat: add X`, `fix: correct Y`, `docs: update Z`).
- Run `uv run black . && uv run flake8 src tests && uv run pytest` before committing.
