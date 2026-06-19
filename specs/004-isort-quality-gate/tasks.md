---

description: "Task list for isort Quality Gate and Pre-Commit Support"
---

# Tasks: isort Quality Gate and Pre-Commit Support

**Input**: Design documents from `/specs/004-isort-quality-gate/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Not applicable — this feature introduces no new Python modules. Principle IV variance
is justified in plan.md. Acceptance is verified by manual scenarios from quickstart.md and SC-005.

**Organization**: Tasks are grouped by user story to enable independent implementation and
verification of each story. Three user stories: US1 (isort hook), US2 (full quality gate),
US3 (onboarding docs).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in all descriptions

---

## Phase 1: Setup

**Purpose**: Add new dev dependencies and configure isort in `pyproject.toml`; install them.
All user story work depends on this phase.

- [X] T001 Add `isort = ">=5.13"` and `pre-commit = ">=3"` to `[dependency-groups].dev` in `pyproject.toml`
- [X] T002 Add `[tool.isort]` section to `pyproject.toml` with `profile = "black"`, `line_length = 99`, `src_paths = ["src", "tests"]`
- [X] T003 Run `uv sync` from the repo root to install `isort` and `pre-commit` into `.venv`; verify `uv run isort --version` and `uv run pre-commit --version` both succeed

---

## Phase 2: Foundational (Blocking Prerequisite)

**Purpose**: Apply the initial import sort to the existing codebase so the first push does not
fail immediately. Must be complete before any hook verification begins.

**⚠️ CRITICAL**: US1 hook verification cannot begin until SC-005 is satisfied here.

- [X] T004 Run `uv run isort .` from the repo root to sort all existing imports; then run `uv run isort --check-only --diff src tests` and confirm it exits 0 (SC-005); stage and commit any changes produced

**Checkpoint**: `uv run isort --check-only --diff src tests` exits 0 — hook will not reject existing code.

---

## Phase 3: User Story 1 - Import Sorting Enforced on Every Push (Priority: P1) 🎯 MVP

**Goal**: A `git push` is blocked whenever any Python file has unsorted imports; a clear diff
is shown so the developer knows exactly what to fix. A clean push proceeds without interruption.

**Independent Test**: Stage a file with unsorted imports, run `git push`, confirm rejection with
an isort diff. Fix with `uv run isort .`, re-push, confirm success. (quickstart.md Scenario 1–3)

### Implementation for User Story 1

- [X] T005 [US1] Create `.pre-commit-config.yaml` at repo root with isort as a `repo: local` hook using `entry: uv run isort --check-only --diff`, `stages: [pre-push]`
- [X] T006 [US1] Install the pre-push hook: run `uv run pre-commit install --hook-type pre-push` from the repo root; confirm `.git/hooks/pre-push` now exists
- [X] T007 [US1] Verify US1 acceptance: follow quickstart.md Scenario 1 (push blocked by unsorted imports) and Scenario 3 (push succeeds after `uv run isort .` fix)

**Checkpoint**: US1 is fully functional — push rejected on unsorted imports, accepted after fix.

---

## Phase 4: User Story 2 - Full Quality Gate Runs Before Push (Priority: P2)

**Goal**: A `git push` is also blocked by Black formatting violations, flake8 lint errors, or
failing tests. All four hooks (isort, Black, flake8, pytest) run automatically at push time.

**Independent Test**: Stage a file with a deliberate flake8 violation (`unused_var = 1`), run
`git push`, confirm the push is blocked and the lint error is reported. (quickstart.md Scenario 4)

### Implementation for User Story 2

- [X] T008 [US2] Add Black hook to `.pre-commit-config.yaml`: `repo: https://github.com/psf/black`, `rev: 24.10.0`, `hooks: [{id: black, stages: [pre-push]}]`
- [X] T009 [US2] Add flake8 hook to `.pre-commit-config.yaml`: `repo: https://github.com/PyCQA/flake8`, `rev: 7.1.0`, `hooks: [{id: flake8, stages: [pre-push]}]`
- [X] T010 [US2] Add local pytest hook to `.pre-commit-config.yaml`: `repo: local`, `hooks: [{id: pytest, name: pytest, entry: uv run pytest, language: system, pass_filenames: false, stages: [pre-push]}]`
- [X] T011 [US2] Verify US2 acceptance: follow quickstart.md Scenario 4 (push blocked by flake8 violation); confirm all four hooks run and pass via `pre-commit run --hook-stage push --all-files`

**Checkpoint**: US1 and US2 both work — all four hooks fire at push time, each blocks on its class of violation.

---

## Phase 5: User Story 3 - New Contributor Onboarding (Priority: P3)

**Goal**: A developer who follows only `AGENTS.md` gets hooks installed and knows how to fix
isort violations, without consulting external documentation.

**Independent Test**: Read the updated AGENTS.md Setup section and confirm it contains both
`pre-commit install --hook-type pre-push` and `uv run isort .`; then follow quickstart.md
Scenario 5 in a fresh clone to confirm hooks are active after setup.

### Implementation for User Story 3

- [X] T012 [US3] Add a "Hooks" subsection inside the existing "Setup" section in `AGENTS.md` containing: (a) `pre-commit install --hook-type pre-push` as the one-time hook-installation command, (b) `uv run isort .` as the command to fix isort violations flagged at push time (FR-006), and (c) `uv run pre-commit autoupdate` as the command to deliberately update pinned hook revisions (FR-005)

**Checkpoint**: A new contributor can follow AGENTS.md alone to install and use the pre-push hooks.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification that all acceptance criteria and the full quality gate pass.

- [X] T013 [P] Run the full quality gate and confirm all commands exit 0: `uv run isort --check-only --diff src tests && uv run black --check src tests && uv run flake8 src tests && uv run pytest`
- [X] T014 [P] Run `pre-commit run --hook-stage push --all-files` with hooks installed; confirm all four hooks pass on the current codebase

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — `uv sync` must complete before `uv run isort .`
- **User Story 1 (Phase 3)**: Depends on Phase 2 — initial sort must be clean before hook verification
- **User Story 2 (Phase 4)**: Depends on Phase 3 (`.pre-commit-config.yaml` must exist from T005)
- **User Story 3 (Phase 5)**: Depends only on Phase 1 completion (no hook dependencies); can overlap with US2 if desired
- **Polish (Phase 6)**: Depends on all preceding phases

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational — no dependencies on US2 or US3
- **US2 (P2)**: Depends on US1 (`.pre-commit-config.yaml` created in T005) — sequential additions to same file
- **US3 (P3)**: Depends only on Phase 1 — `AGENTS.md` edit is independent of hook config

### Within Each User Story

- T005 (create config) → T006 (install) → T007 (verify): strictly sequential
- T008 → T009 → T010 (all modify same file): strictly sequential
- T011 depends on T008–T010 all complete
- T012 is independent of T005–T011

### Parallel Opportunities

- T013 and T014 (Polish phase) can run in parallel
- US3 (T012) can be worked in parallel with US2 (T008–T011) — different files

---

## Parallel Example: US2 + US3

```bash
# These two can be done in parallel (different files):
Task T012: "Add Hooks subsection to AGENTS.md"
Task T008: "Add Black hook to .pre-commit-config.yaml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (`pyproject.toml` deps + isort config)
2. Complete Phase 2: Foundational (initial sort + SC-005 verification)
3. Complete Phase 3: US1 (create `.pre-commit-config.yaml` with isort hook, install, verify)
4. **STOP and VALIDATE**: Push a file with unsorted imports — confirm rejection
5. The isort gate is live and protecting the remote branch

### Incremental Delivery

1. Setup + Foundational → isort available, existing code clean
2. US1 → isort hook active at push time (MVP)
3. US2 → full quality gate (Black + flake8 + pytest) added to same hook runner
4. US3 → AGENTS.md updated; new contributors have full setup instructions
5. Polish → confirm clean state across all checks

---

## Notes

- `[P]` tasks can be done in parallel (different files, no incomplete prerequisites)
- `[Story]` label maps task to its user story for traceability
- No new test files are created — Principle IV variance is justified in plan.md
- SC-005 (`isort --check-only` exits 0) is verified in T004; re-verified in T013
- Commit after each task or logical group; run `uv run black . && uv run flake8 src tests && uv run pytest` before each commit per AGENTS.md
