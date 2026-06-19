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

### Hooks

After `uv sync`, install the pre-push quality gate hooks (one-time per clone):

```bash
uv run pre-commit install --hook-type pre-push
```

This installs hooks that run isort, Black, flake8, and pytest automatically before every `git push`.

If a push is rejected because of unsorted imports, fix them with:

```bash
uv run isort .
```

To deliberately update pinned hook revisions:

```bash
uv run pre-commit autoupdate
```

## Running tests

```bash
uv run pytest
```

Coverage is measured automatically. The suite fails if `src/cetools` coverage drops below 85%.

Run a single file or test (no coverage enforcement on partial runs):

```bash
uv run pytest tests/test_foo.py --no-cov
uv run pytest tests/test_foo.py::test_bar -v --no-cov
```

All new code should have corresponding tests in `tests/`. Run the full suite before considering a task complete.

## Code style

- Format with Black: `uv run black .`
- Lint with flake8: `uv run flake8 src tests`
- Both should be run (and pass) before finishing a change.

## PR instructions

- Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for all commit messages and PR titles (e.g., `feat: add X`, `fix: correct Y`, `docs: update Z`).
- Run `uv run black . && uv run flake8 src tests && uv run pytest` before committing. The `pytest` step includes coverage; the suite fails if coverage falls below 85%.
