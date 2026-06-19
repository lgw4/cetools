# Research: isort Quality Gate and Pre-Commit Support

## Decision: isort version to pin

- **Decision**: Use `isort>=5.13` as a floor-pinned PyPI dev dep; all hooks run via `uv run` against the resolved version in `uv.lock` (8.0.1 as of 2026-06-18), eliminating separate `.pre-commit-config.yaml` rev pins.
- **Rationale**: Switching all hooks to `repo: local` with `entry: uv run ...` ensures developers always run the same tool version whether they invoke `uv run isort .` manually or push and trigger the hook. A separate `rev:` pin would create version skew between `uv.lock` and the hook environment.
- **Alternatives considered**: exact-pin `isort==5.13.2` for both PyPI dep and hook rev — rejected; this causes confusing failures when `uv run isort .` (using `uv.lock`) fixes imports that the hook (pinned to an older version) still rejects.

## Decision: pre-commit version to pin

- **Decision**: `pre-commit>=3` as PyPI dev dep; no rev pin needed for the runner itself (only hooks are pinned).
- **Rationale**: pre-commit 3.x is the current stable major; pinning the runner to a floor (not exact) is conventional practice since the runner version does not affect hook reproducibility.
- **Alternatives considered**: exact-pin the runner — rejected as unnecessary overhead.

## Decision: isort Black-compatible profile configuration

- **Decision**: Add `[tool.isort]` to `pyproject.toml`:
  ```toml
  [tool.isort]
  profile = "black"
  line_length = 99
  src_paths = ["src", "tests"]
  ```
- **Rationale**: The `black` profile sets `multi_line_output = 3`, `include_trailing_comma = True`, `force_grid_wrap = 0`, `use_parentheses = True`, and `ensure_newline_before_comments = True` — all values Black expects. `line_length` must match Black's value (99, per `[tool.black]`). `src_paths` ensures first-party imports in `src/` and `tests/` are classified correctly.
- **Alternatives considered**: Separate `.isort.cfg` — rejected; `pyproject.toml` is the single config source per the constitution.

## Decision: hook runner strategy for Black and flake8

- **Decision**: Use the canonical upstream pre-commit hook repositories:
  - `https://github.com/psf/black` (rev: `24.10.0`) — runs `black --check`
  - `https://github.com/PyCQA/flake8` (rev: `7.1.0`) — runs flake8
  - `https://github.com/PyCQA/isort` (rev: `5.13.2`) — runs `isort --check-only --diff`
- **Rationale**: These repos vendor their own hook environments; pre-commit installs them independently of the project's `.venv`, which is correct — hooks should not depend on the dev environment being activated.
- **Alternatives considered**: Local hooks for Black/flake8 — rejected; remote hooks are more reproducible and are the idiomatic pre-commit approach for these well-maintained tools.

## Decision: hook runner strategy for pytest

- **Decision**: Use a `repo: local` hook that runs `uv run pytest`:
  ```yaml
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: uv run pytest
        language: system
        pass_filenames: false
        stages: [pre-push]
  ```
- **Rationale**: pytest requires the project's own virtual environment (to access test modules, fixtures, and `src/cetools`). `language: system` delegates environment management to the system shell, where `uv run` resolves the `.venv` correctly. There is no maintained upstream pre-commit mirror for pytest that would satisfy our project-specific setup.
- **Alternatives considered**: `language: python` with `additional_dependencies` — rejected; this creates a second isolated env that cannot import `src/cetools`. A pre-commit mirror for pytest — rejected for the same reason.

## Decision: hook stage (pre-push vs pre-commit)

- **Decision**: All four hooks (isort, black, flake8, pytest) run at the `pre-push` stage.
- **Rationale**: Per the spec assumptions and FR-003, pre-push keeps the commit cycle fast. Only the push to the remote is gated.
- **How to configure**: Each hook entry includes `stages: [pre-push]`, and the developer installs with `uv run pre-commit install --hook-type pre-push`.
- **Alternatives considered**: `pre-commit` stage for lint-only hooks — rejected; the spec explicitly requires a single gate at push time; splitting stages adds cognitive overhead.

## Decision: initial isort sort of existing codebase

- **Decision**: Run `uv run isort .` on the existing codebase as a one-time step in the implementation task, then verify `uv run isort --check-only .` reports zero violations (SC-005).
- **Rationale**: If existing imports are already Black-compatible, isort will make no changes. If any are out of order, the fix must land before the hook is installed so that the first push after setup doesn't fail.
- **Alternatives considered**: Skip the initial sort and let the hook catch issues on first push — rejected; this would block the developer immediately and is confusing UX.

## Resolved NEEDS CLARIFICATION items

All Technical Context fields were known from the existing project. No external research blockers remain.
