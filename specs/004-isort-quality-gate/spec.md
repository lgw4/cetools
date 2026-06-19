# Feature Specification: isort Quality Gate and Pre-Commit Support

**Feature Branch**: `004-isort-quality-gate`

**Created**: 2026-06-18

**Status**: Draft

**Input**: User description: "We need to add isort as a quality gate and pre-commit (https://pre-commit.com) support to make sure tests and quality gates are run before pushing to GitHub."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Import Sorting Enforced on Every Push (Priority: P1)

A developer working on cetools edits a file and pushes to GitHub. Before the push completes, the pre-commit hooks run automatically and reject any commits where Python imports are not sorted according to the project standard. The developer sees a clear error message, re-runs the sort, and the push succeeds.

**Why this priority**: Import ordering is the new quality gate being introduced; without it running consistently, the enforcement has no effect. This is the core ask.

**Independent Test**: Can be fully tested by staging a Python file with unsorted imports, attempting a `git push`, and confirming the push is blocked with an actionable error message.

**Acceptance Scenarios**:

1. **Given** a Python file with imports in non-standard order is staged and committed, **When** the developer runs `git push`, **Then** the push is rejected and the developer is shown which file(s) have unsorted imports.
2. **Given** a Python file with correctly sorted imports is staged and committed, **When** the developer runs `git push`, **Then** the push proceeds without error.
3. **Given** a developer runs the import sorter manually to fix the issue, **When** they re-stage and push, **Then** the push succeeds.

---

### User Story 2 - Full Quality Gate Runs Before Push (Priority: P2)

A developer pushes code that passes import sorting but has a flake8 lint error or a failing test. The pre-push hook catches the failure before the code reaches GitHub, and the developer fixes it locally.

**Why this priority**: The feature request explicitly names tests and all quality gates as required checks. Blocking only on import ordering without also enforcing existing gates (Black formatting, flake8, pytest) would leave gaps in the guard.

**Independent Test**: Can be fully tested by staging code with a deliberate flake8 violation, running `git push`, and confirming the push is blocked with a lint error — without touching the import-sorting feature.

**Acceptance Scenarios**:

1. **Given** a commit with a Black formatting violation, **When** the developer runs `git push`, **Then** the push is blocked and the formatting error is reported.
2. **Given** a commit with a flake8 lint warning, **When** the developer runs `git push`, **Then** the push is blocked and the lint issue is reported.
3. **Given** a commit that causes a test to fail, **When** the developer runs `git push`, **Then** the push is blocked and the failing test(s) are reported.
4. **Given** all checks pass (imports sorted, Black clean, flake8 clean, all tests green), **When** the developer runs `git push`, **Then** the push proceeds.

---

### User Story 3 - New Contributor Onboarding (Priority: P3)

A developer who is new to the project clones the repository, follows the setup instructions, and the pre-commit tooling is automatically installed and ready to use. They do not need to read extra documentation or take manual configuration steps beyond the standard `uv sync`.

**Why this priority**: Automation that only works for existing contributors has limited value. New contributors should get the same protection without friction.

**Independent Test**: Can be fully tested by cloning into a clean environment, running the documented setup command, and verifying that a deliberate import-sort violation is caught on the next push.

**Acceptance Scenarios**:

1. **Given** a fresh clone of the repository, **When** the developer runs the standard setup command, **Then** the pre-commit hooks are installed and active.
2. **Given** hooks are installed, **When** the developer stages a file with unsorted imports and pushes, **Then** the push is blocked identically to the experience of an existing contributor.

---

### Edge Cases

- What happens when a developer bypasses hooks with `--no-verify`? The bypass remains available (standard git behavior), but the CI/CD pipeline (if added later) would still catch violations. This spec does not prohibit `--no-verify`; it only installs the hooks.
- What happens when isort and Black have conflicting opinions on import formatting? isort must be configured to produce output compatible with Black (the `black` profile for isort).
- What happens if the test suite takes a long time and the developer is blocked at push time? The full test suite runs on push (not commit); developers retain the option to bypass with `--no-verify` if they understand the trade-off.
- What happens on a system without `pre-commit` installed? The setup step must surface a clear error or install `pre-commit` as part of the developer environment setup.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST enforce sorted Python imports (via isort) as a mandatory quality check before any push to GitHub reaches the remote.
- **FR-002**: The project MUST enforce Black formatting, flake8 linting, and full pytest suite passage as mandatory checks before any push reaches GitHub.
- **FR-003**: All pre-push checks MUST run automatically via pre-commit hooks without requiring the developer to invoke them manually.
- **FR-004**: isort MUST be configured to use the Black-compatible profile (`profile = "black"`) and MUST use the same `line_length` as Black (99) so its output never conflicts with Black's formatting.
- **FR-009**: The isort pre-push hook MUST run in check-only mode: it reports which files have unsorted imports and exits non-zero, but does not modify any files. Developers are responsible for running isort manually to fix violations before re-pushing.
- **FR-005**: The pre-commit configuration MUST be version-controlled in the repository so every contributor gets the same hooks. Each hook sourced from an upstream repository MUST be pinned to a specific release tag; updates are made deliberately via `pre-commit autoupdate`. The local pytest hook (`repo: local`) is exempt from release-tag pinning because it has no upstream repository; its version is implicitly pinned by the project's own `pyproject.toml` dev dependencies.
- **FR-006**: AGENTS.md MUST be updated with a new "Hooks" subsection inside the existing "Setup" section containing: (a) the hook-installation command `pre-commit install --hook-type pre-push`, so new contributors run it alongside `uv sync`; and (b) the command to manually sort imports (`uv run isort .`) so a developer who receives an isort failure can resolve it without consulting external documentation.
- **FR-007**: isort MUST be added as a project dependency (dev dependency) in `pyproject.toml` so it is installed by `uv sync`.
- **FR-008**: pre-commit MUST be added as a project dependency (dev dependency) in `pyproject.toml`.

### Key Entities

- **Pre-commit hook configuration**: The `.pre-commit-config.yaml` file at the project root; defines which hooks run and at which git event (pre-push).
- **isort configuration**: Settings (Black profile, source paths) expressed in `pyproject.toml` under `[tool.isort]`; no separate config file needed.
- **Developer setup step**: The command a developer runs once after cloning to activate the hooks (`pre-commit install --hook-type pre-push`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A push containing Python files with unsorted imports is blocked 100% of the time when hooks are installed.
- **SC-002**: A push where all quality gates pass (imports sorted, Black clean, flake8 clean, all tests green) completes within 2 minutes of the `git push` command being issued on a standard developer machine with `.venv` already present.
- **SC-003**: A developer following only the documented setup steps in AGENTS.md has hooks installed and active in under 2 minutes on a machine where `uv sync` has already completed.
- **SC-004**: Zero new failing tests are introduced in the existing test suite as a result of this change.
- **SC-005**: Running `uv run isort --check-only .` exits with code 0 on the current codebase after the initial sort is applied.

## Clarifications

### Session 2026-06-18

- Q: What command/location should the AGENTS.md hook-installation step use? → A: `pre-commit install --hook-type pre-push` added as a new "Hooks" subsection inside the existing Setup section in AGENTS.md, alongside `uv sync`.
- Q: How should hook versions be pinned in `.pre-commit-config.yaml`? → A: Pin each hook to a specific release tag (e.g., `rev: v5.13.0`); update deliberately via `pre-commit autoupdate`.

## Assumptions

- All developers use `uv sync` for environment setup; the new `pre-commit` and `isort` dependencies will be picked up by that existing command without additional steps.
- The hooks are enforced at `pre-push` (not `pre-commit`) to keep the commit cycle fast while still guarding the remote branch.
- The existing AGENTS.md is the canonical developer setup document and is the right place to document the hook-installation step.
- The target platform is macOS and Linux developer workstations; Windows is out of scope. Mobile or non-standard git clients are also out of scope; the hooks target the standard `git` CLI.
- No CI/CD pipeline exists yet; this feature focuses solely on local pre-push enforcement.
- Manual invocation of the full quality gate suite (`pre-commit run --all-files`) is out of scope for this feature's requirements; `quickstart.md` is the appropriate location for such usage guidance.
