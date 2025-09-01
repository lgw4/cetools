# Cetools — Implementation Plan

This implementation plan maps the project specification into a sequence of concrete, bounded work items suitable for a single engineer with an LLM assistant. Each task is scoped to be completable within at most forty hours of focused work and includes acceptance criteria, estimated effort, and test/quality gates.

## High-level plan

1. Bootstrap repository and developer environment (4–8h)
2. Core library skeleton and types (24–40h)
3. Dice module implementation and tests (8–16h)
4. Character module skeleton and basic generator (24–40h)
5. CLI wrappers using `typer` (12–24h)
6. Tests, CI, and formatting (12–24h)
7. Optional: FastAPI adapter and small demo (16–40h)

Each task below includes steps, deliverables, acceptance criteria, and risk/mitigation notes.

## 1 — Bootstrap repository and developer environment (4–8h)

What

- Modernize `pyproject.toml` for packaging and dev tools (Black, ruff, isort, pytest). Add `console_scripts` entry points placeholder.
- Add a small `justfile` with common tasks: `dev`, `test`, `lint`.
- Add instructions to README for using `uv` environment (per project conventions).

Deliverables

- Updated `pyproject.toml` with dev dependencies and entry points.
- `justfile` with dev commands.
- README additions describing setup.

Acceptance criteria

- `pip install -e .[dev]` or `uv` equivalent installs dev deps.
- `just test` runs pytest and passes (no tests yet is OK).

Risks

- Dependency version conflicts — mitigate by pinning minimal versions and using `uv.lock`.

## 2 — Core library skeleton and types (24–40h)

What

- Create `src/cetools/__init__.py` (if missing) and module directories: `dice`, `characters`, `npc`, `equipment`, `encounters`, `utils`.
- Define data models using `pydantic` (prefer Pydantic v2 for performance and serialization). Include `model_dump()`/`model_validate()` usage and helper methods for JSON serialization.
- Add custom exception types: `InvalidInputError`, `NotFoundError`, `CetoolsError`.

Deliverables

- Package layout under `src/cetools/` with `__init__.py` and empty module stubs.
- `models.py` or package-level models using `pydantic.BaseModel` (Pydantic v2) for `Character`, `NPC`, `RollResult`.
- Unit tests that import modules and validate model serialization and `model_dump()` output.

Acceptance criteria

- Imports succeed; simple model creation and JSON serialization round-trip tests pass.

Risks

- Choice of dataclass vs pydantic affects UX; pick pydantic unless performance or extra deps are critical.

## 3 — Dice module implementation and tests (8–16h)

What

- Implement `cetools.dice` with a `roll` function that parses expressions like `2d6+3`, supports multiple expressions, and deterministic seeding.
- Return a `RollResult` Pydantic model with breakdown and total and ensure `model_dump()` produces JSON-friendly output.

Deliverables

- `src/cetools/dice.py` with `roll(expression: str, seed: int|None) -> RollResult`.
- Unit tests covering edge cases (invalid expressions, large dice counts, seed deterministic behavior).

Acceptance criteria

- Tests validate expression parsing, deterministic results with seed, and JSON serializable result.

Risks

- Parsing complexity for advanced expressions — start with common subset (NdM+K, with optional negative K).

## 4 — Character module skeleton and basic generator (24–40h)

What

- Implement core `characters` module with a `generate` function that can create a character using simple rules: attribute rolls (using `dice`), career selection, and a minimal set of derived stats.
- Support passing a `seed` and optional `template` dict to override fields.

Deliverables

- `src/cetools/characters.py` with `generate()` and `Character` model.
- Example templates under `tests/fixtures/`.
- Unit tests validating generation with seeds and template overrides.

Acceptance criteria

- Generated character JSON conforms to `Character` model and respects seed/template inputs.

Risks

- The original project may have complex legacy rules; start with a minimal generator and add features iteratively.

## 5 — CLI wrappers using Typer (8–20h)

What

- Add a `cli` package and entry points via `pyproject.toml` console_scripts (e.g., `cetools=cetools.cli:app`).
- Implement subcommands for `character create`, `dice roll`, `npc generate`, `equipment find`, and `encounter random` using `typer` (built on Click).
- Support `--json` flag and `--seed` for reproducibility.

Deliverables

- `src/cetools/cli.py` or `src/cetools/cli/__init__.py` with `app: typer.Typer` and command functions.
- Tests for CLI using Typer's testing helpers (which build on Click's test client).

Acceptance criteria

- Running `cetools --help` shows subcommands.
- `cetools dice roll '2d6+3' --json` outputs valid JSON matching `RollResult`.

Risks

- Typer adds a small dependency but provides excellent ergonomics and auto-generated help, plus easier parameter parsing and testing. If minimal-deps constraint is strict, we can revert to `argparse`.

## 6 — Tests, CI, and formatting (12–24h)

What

- Add pytest tests for modules implemented.
- Add GitHub Actions workflow to run tests, ruff, and mypy/typing checks.
- Configure pre-commit and run formatting.

Deliverables

- `.github/workflows/ci.yaml` that runs tests and linters on PRs.
- Passing local tests and static checks.

Acceptance criteria

- CI config runs and passes for the repo on a feature branch.

Risks

- CI flakiness; keep tests deterministic and small.

## 7 — Optional: FastAPI adapter and small demo (16–40h)

What

- Create a minimal FastAPI app exposing `POST /roll`, `POST /character`, and `GET /equipment/{name}` endpoints that call into the library.
- Add a small example UI or curl examples.

Deliverables

- `src/cetools/api.py` with FastAPI app exposing a few endpoints.
- `tests/test_api.py` with small integration tests using `TestClient`.

Acceptance criteria

- Example API endpoints return JSON matching library models.

Risks

- Extra dependency and surface area; keep adapter thin and focus on core library correctness first.

## Quality gates and verification

- Build: ensure `pip install -e .[dev]` succeeds.
- Lint: ruff and isort configured; no new errors.
- Tests: pytest runs, unit tests passing.
- Type: add mypy or pyright checks if desired.

## Next steps (first sprint)

1. Bootstrap repo (task 1).
2. Implement `dice` module (task 3) and tests — provides immediate user-visible utility.
3. Create core package layout and basic models (task 2).

Each step should be followed by a PR with CI and tests.

<!-- This file contains GitHub Copilot generated content. -->
