# AGENTS.md

## Principles

The project constitution, `.specify/memory/constitution.md`, is the authority on engineering
principles: SRD fidelity, library-first with a thin CLI, red-green TDD, determinism through the
`Rolls` seam, and simplicity. Read it before your first substantive change. Where this file
disagrees with it, the constitution governs.

## Setup

```shell
uv sync
```

Installs the project and all dependencies (including dev dependencies) into `.venv`.

### Hooks

After `uv sync`, install the pre-push quality gate hooks (one-time per clone):

```shell
uv run pre-commit install --hook-type pre-push
```

This installs hooks that run isort, Black, flake8, pytest, and the docs check automatically before every `git push`.

If a push is rejected because of unsorted imports, fix them with:

```shell
uv run isort .
```

To deliberately update pinned hook revisions:

```shell
uv run pre-commit autoupdate
```

## Running tests

```shell
uv run pytest
```

Coverage is measured automatically. The suite fails if `src/cetools` coverage drops below 85%.

Run a single file or test (no coverage enforcement on partial runs):

```shell
uv run pytest tests/test_foo.py --no-cov
uv run pytest tests/test_foo.py::test_bar -v --no-cov
```

All new code should have corresponding tests in `tests/`. Run the full suite before considering a task complete.

## Code style

- Sort imports with isort: `uv run isort .`
- Format with Black: `uv run black .`
- Lint with flake8: `uv run flake8 src tests`
- Run the suite: `uv run pytest`
- Check the docs against the code: `uv run python scripts/check_docs.py`
- All five are the quality gate, and all five must pass before finishing a change.

The docs check fails if a backticked symbol in `README.md`, `CONTRIBUTING.md`
or `AGENTS.md` no longer exists, if a README Python
example stops running, if the module map misses an engine module, or if a dash is
spaced. Rename a symbol and the docs that name it must move with it.

## PR instructions

- Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for all commit messages and PR titles (e.g., `feat: add X`, `fix: correct Y`, `docs: update Z`).
- Run `uv run isort . && uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py` before committing. The `pytest` step includes coverage; the suite fails if coverage falls below 85%. The pre-push hooks run the same five.
