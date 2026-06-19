# Implementation Plan: isort Quality Gate and Pre-Commit Support

**Branch**: `004-isort-quality-gate` | **Date**: 2026-06-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-isort-quality-gate/spec.md`

## Summary

Add `isort` (Black-compatible profile) and `pre-commit` as dev dependencies, configure a
`.pre-commit-config.yaml` with `pre-push` hooks covering isort, Black, flake8, and pytest, and
update `AGENTS.md` with the one-time hook-installation step. No new engine or CLI code is
introduced — this is pure tooling configuration.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**:
- `isort>=5.13` (new dev dep — import sorter)
- `pre-commit>=3` (new dev dep — hook runner)
- `black>=24`, `flake8>=7`, `pytest>=8` (existing dev deps, also run as hooks)

**Storage**: N/A

**Testing**: pytest (existing); no new test modules — feature is tooling configuration

**Target Platform**: Developer workstation (macOS/Linux with standard `git` CLI)

**Project Type**: CLI library — this feature adds developer-tooling configuration only

**Performance Goals**: All pre-push checks complete in under 2 minutes on a standard developer machine

**Constraints**:
- isort profile MUST be `black` to avoid conflicts with Black formatting
- `line_length` in isort config MUST match Black's `line-length = 99`
- Each pre-commit hook revision MUST be pinned to a specific release tag
- Hooks fire at `pre-push` (not `pre-commit`) to keep the commit cycle fast

**Scale/Scope**: Single-developer project; hooks protect the remote branch from quality regressions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. SRD-Fidelity | NOT APPLICABLE | No SRD game-rule content introduced |
| II. Library-First | NOT APPLICABLE | No engine code introduced or modified |
| III. CLI Interface | NOT APPLICABLE | No CLI code introduced or modified |
| IV. Test-First | VARIANCE JUSTIFIED | Feature introduces no new Python modules — only configuration files. No Red-Green-Refactor cycle applies. SC-004 (zero new failing tests) and SC-005 (zero isort violations after initial sort) serve as the functional acceptance criteria. Existing test suite must remain green. |
| V. Data-Driven Extensibility | NOT APPLICABLE | No game content introduced |

**Gate result**: PASS — all applicable principles satisfied; variance on Principle IV is justified
by the configuration-only nature of this feature.

**Post-design re-check**: Confirmed after Phase 1 — no source files under `src/cetools/` are
changed; the existing test suite is unaffected; the isort initial sort applies the Black profile
uniformly.

## Project Structure

### Documentation (this feature)

```text
specs/004-isort-quality-gate/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks command — NOT created here)
```

No `contracts/` directory — this feature exposes no public API or external interface.

### Files Changed (repository root)

```text
.pre-commit-config.yaml          # NEW — hook runner configuration (pre-push stage)

pyproject.toml                   # MODIFIED:
                                 #   [dependency-groups] dev += isort>=5.13, pre-commit>=3
                                 #   [tool.isort] section added (profile = "black", line_length = 99)

AGENTS.md                        # MODIFIED:
                                 #   New "Hooks" subsection in "Setup" section
                                 #   Command: pre-commit install --hook-type pre-push
```

No files under `src/cetools/` or `tests/` are created or modified by this feature (other than
reformatting existing imports via the initial `isort .` run if any are out of order).

**Structure Decision**: Single-project layout; only config-layer files change.

## Complexity Tracking

No constitution violations requiring justification.
