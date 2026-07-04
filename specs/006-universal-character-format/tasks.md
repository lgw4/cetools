---

description: "Task list for Universal Character Format Output"
---

# Tasks: Universal Character Format Output

**Input**: Design documents from `/specs/006-universal-character-format/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ucf-output.md, quickstart.md

**Tests**: Included and REQUIRED — Constitution Principle IV (Test-First) is non-negotiable for
this project; every task below that touches behavior is preceded by a failing-test task.

**Organization**: Tasks are grouped by user story. **Execution order deviates from strict
P1→P2→P3 priority order**: spec.md's own "Why this priority" note for User Story 2 states it is
"a prerequisite for User Story 1 to be fully satisfied" (line 1 of UCF cannot exist without a
name), so User Story 2 (P2) is implemented before User Story 1 (P1) below. Priority labels
(`[US1]`, `[US2]`, `[US3]`) are kept for traceability; see Dependencies & Execution Order.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Setup/Foundational/Polish tasks carry no `[Story]` label

## Path Conventions

Single project: `src/cetools/`, `tests/` at repository root (existing layout, unchanged — see
plan.md Project Structure).

---

## Phase 1: Setup

**Purpose**: Establish a known-green baseline before touching any code.

- [X] T001 Run `uv sync && uv run pytest` on the current branch tip and confirm the full suite is
      green with ≥85% coverage on `src/cetools`. No code changes in this task — it is the
      baseline SC-004 ("zero regressions") will be measured against. No new dependencies are
      required for this feature (plan.md Technical Context).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the one new `Character` field both stories build on, and repair every existing
fixture that directly constructs a `Character(...)` (unrelated to the format itself) so the suite
compiles against the new required field.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. Note: after this
phase, `tests/test_generator.py` will be RED (the production `Character(...)` call inside
`generate_character` does not yet supply `name=`) — that breakage is intentionally resolved by
User Story 2 (T009), not here, since fixing it requires `generate_name` to exist first.

- [X] T002 [P] Add a failing test `test_character_name_field_is_stored` in
      `tests/test_models.py`: construct a `Character(..., name="Jane Doe")` and assert
      `char.name == "Jane Doe"`. Confirm it fails (RED) — `name` is not yet a field.
- [X] T003 Add a `name: str` field (no default, per data-model.md — every other identity field on
      `Character` is required) to the `Character` dataclass in `src/cetools/engine/models.py`.
      **Position matters**: `drafted: bool = False` is the dataclass's only field with a default
      and is declared last; Python requires non-default fields precede default fields, so `name`
      MUST be declared somewhere *before* `drafted` (e.g. grouped with the other identity fields,
      immediately after `age` or `rank_title`) — appending it after `drafted` raises `TypeError:
      non-default argument 'name' follows default argument`. Confirm T002 passes (GREEN).
- [X] T004 [P] Update the two existing `Character(...)` fixtures in `tests/test_models.py`
      (`test_character_drafted_defaults_to_false`, `test_character_drafted_can_be_set_true`) to
      pass `name=` so they compile against the new required field.
- [X] T005 [P] Update the four existing `Character(...)` fixtures in `tests/test_cli.py`
      (`_make_character`, `_SCOUT_CHARACTER`, `_make_aerospace_character`,
      `_make_marine_character`) to pass `name=` so they compile against the new required field.

**Checkpoint**: `Character` has a `name` field; every fixture that builds one directly compiles.
`tests/test_generator.py` is expected to be RED until User Story 2 completes — this is normal and
tracked, not a regression to chase down here.

---

## Phase 3: User Story 2 - Every character has a name (Priority: P2, implemented first — see note above) 🎯 prerequisite for US1

**Goal**: Every generated character gets a randomly assigned, independently-drawn two-word name,
sourced from new data tables, using the existing `DiceRoller` seam (no new randomness mechanism).

**Independent Test**: Generate several characters and verify each one's output (or, at this
implementation stage, each `Character.name` value) is a two-or-more-word string; generating two
characters may produce the same name (acceptable, not an error).

### Tests for User Story 2 ⚠️

> Write these first, confirm they FAIL before implementing.

- [X] T006 [P] [US2] Create `tests/test_names.py` (new file) with tests asserting: `FIRST_NAMES`
      and `LAST_NAMES` are each `tuple[str, ...]` with at least 10 entries; `generate_name(roller)`
      returns a string of exactly two space-separated, non-empty words; `generate_name` makes
      exactly two independent `roller.roll(...)` calls — one sized to `len(FIRST_NAMES)`, one to
      `len(LAST_NAMES)` — never a single shared roll or list index (use the existing
      `ConstantRoller`/`SequenceRoller` doubles from `conftest.py`, e.g. a `SequenceRoller` whose
      two consumed values map to known first/last entries, to prove two distinct draws happened).
      Confirm these fail (RED) — `cetools.engine.names` does not exist yet.

### Implementation for User Story 2

- [X] T007 [US2] Create `src/cetools/engine/names.py` (new file, mirroring the
      `careers/*.py` data-table convention): `FIRST_NAMES: tuple[str, ...]` (≥10 unisex,
      proper-cased entries — no gendered split, per FR-001/Assumptions), `LAST_NAMES:
      tuple[str, ...]` (≥10 entries), and `generate_name(roller: DiceRoller) -> str` that calls
      `roller.roll(len(FIRST_NAMES))` and `roller.roll(len(LAST_NAMES))` independently and returns
      `f"{first} {last}"`. Confirm T006 passes (GREEN).
- [X] T008 [P] [US2] Add failing tests in `tests/test_generator.py`: a successfully generated
      character (e.g. `generate_character(NAVY_CAREER, roller=SmartRoller(10, 1))`) has a
      non-empty `.name` containing two-or-more words; confirm every pre-existing
      `SequenceRoller`-based test in this file still asserts the same roll-sequence-derived
      values it did before (i.e., name generation must not be inserted before any existing roll in
      the sequence — it only runs after `_muster_out`, right before `Character(...)` is built).
      These new assertions will fail (RED) until T009 lands, alongside the pre-existing
      now-broken tests from Phase 2's checkpoint note.
- [X] T009 [US2] Update `src/cetools/engine/generator.py`: import `generate_name` from
      `cetools.engine.names`; call it exactly once near the end of `generate_character`, after
      `_muster_out` and immediately before constructing the returned `Character`; pass the result
      as `name=`. Confirm T008 passes and every previously-passing test in `tests/test_generator.py`
      is GREEN again (this also resolves the Phase 2 checkpoint breakage).

**Checkpoint**: Every successfully generated character (career-selected, drafted, or via
`generate_career_character`) carries a real, independently-drawn name. `tests/test_generator.py`
is fully green.

---

## Phase 4: User Story 1 - Read a character in the standard format (Priority: P1) 🎯 MVP

**Goal**: `format_character` emits exactly the Universal Character Format line set — nothing
more, nothing less — per `contracts/ucf-output.md`.

**Independent Test**: Generate a character for any implemented career and verify the printed
output contains only the UCF lines (name/rank/UPP/age; career/terms/funds; skills;
equipment-if-any), with no characteristic breakdown, benefit-type headers, pension line, or
`(Drafted)` annotation.

### Tests for User Story 1 ⚠️

> Write these first, confirm they FAIL before implementing.

- [X] T010 [P] [US1] Rewrite `tests/test_formatter.py` to assert the exact grammar from
      `contracts/ucf-output.md` in place of the old multi-section assertions: line 1 is
      `"{rank_title }name\tupp\tAge {age}"` (rank-title segment, with its trailing space, omitted
      when `rank_title` is empty); line 2 is `"{career} ({terms_served} terms)\tCr{funds}"` with
      `funds` = sum of cash benefit amounts, thousands-separated, `"Cr0"` when there are none;
      line 3 is the skill list sorted alphabetically as `"Name-Level"` joined by `", "` (present
      even when empty); line 4 lists each material benefit's name joined by `", "`, present only
      when at least one exists (omitted as a whole line, not blank, otherwise); no blank lines
      appear anywhere between lines; none of `"UPP:"`, `"Characteristics:"`,
      `"Mustering-Out Benefits:"`, `"Retirement Pension:"`, `"(Drafted)"` appear anywhere in the
      output; the output is never more than 4 lines total, i.e. no species-traits line ever
      appears (this is the concrete test coverage for FR-008 — the requirement holds vacuously
      since no code path ever produces such a line, but the exact-line-count assertion is what
      pins that down as a regression check). Include both worked examples from
      `contracts/ucf-output.md` (fully-populated character; zero-cash/zero-material/zero-skills
      character) as concrete fixture-driven cases. Confirm these fail (RED) against the current
      `formatter.py`.
- [X] T011 [P] [US1] Update `tests/test_cli.py` assertions for the new output shape: remove or
      rewrite `test_cli_no_career_generates_drafted_character` and
      `test_cli_no_career_career_line_contains_drafted` (the `(Drafted)` annotation no longer
      appears anywhere, per FR-009 — a drafted character's output is indistinguishable in shape
      from a `--career`-selected one). Leave the rank-title assertions
      (`_AEROSPACE_RANK_TITLES`/`_MARINE_RANK_TITLES` membership checks) in place and re-verify
      they still hold against the new line-1 format. (Fixture `name=` values were already added in
      T005.)

### Implementation for User Story 1

- [X] T012 [US1] Rewrite `format_character` in `src/cetools/formatter.py` per
      `contracts/ucf-output.md`/data-model.md: drop the per-characteristic breakdown, the
      cash/material header split, the pension line, and the drafted annotation entirely; emit
      exactly `line1\nline2\nline3[\nline4]` with tab-separated segments within lines 1–2 as
      specified. Confirm T010 and T011 both pass (GREEN).
- [X] T013 [US1] Manually validate quickstart.md Scenario 1 (`uv run cetools generate --career
      navy`) and Scenario 4 (`uv run cetools generate`, draft path): confirm real stdout is 3–4
      lines, matches the UCF shape, and contains no legacy headers or `(Drafted)` marker. Smoke
      test only — no new automated assertions.

**Checkpoint**: MVP complete — every generated character, however it was created, prints exactly
the UCF line set with a real name.

---

## Phase 5: User Story 3 - Funds and equipment at a glance (Priority: P3)

**Goal**: Confirm the funds-summing and equipment-listing behavior already delivered by T012
satisfies US3's specific acceptance scenarios (multi-benefit summing, zero-benefit defaults,
comma-separated equipment naming) — this story shares its implementation with US1 (both are
governed by the same `contracts/ucf-output.md` grammar for lines 2 and 4), so no new production
code is expected; if a gap is found, fix `format_character` in place here.

**Independent Test**: Generate a character with multiple cash and material mustering-out benefits
and verify the funds line shows one combined `Cr<amount>` total and the equipment line lists each
material benefit by name.

### Tests for User Story 3 ⚠️

- [X] T014 [US3] Add targeted tests to `tests/test_formatter.py` covering US3's acceptance
      scenarios precisely: multiple cash benefits (e.g. `Cr50,000 + Cr20,000 + Cr10,000`) sum to a
      single `"Cr80,000"` figure; a character with zero cash benefits shows `"Cr0"` (not omitted);
      a character with one or more material benefits lists each by name, comma-separated, in
      benefit-list order. Confirm these pass against the existing T012 implementation; if any
      fails, fix `format_character` in `src/cetools/formatter.py` until green.

**Checkpoint**: All three user stories are independently verified against their own acceptance
scenarios.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final quality gate, matching AGENTS.md's required pre-commit sequence.

- [X] T015 Run `uv run black .` then `uv run flake8 src tests`; fix any formatting/lint violations
      across all files touched by this feature.
- [X] T016 Run `uv run pytest` (full suite, coverage enforced) and confirm ≥85% coverage on
      `src/cetools` with zero regressions outside display-format/name-related tests (SC-004).
- [X] T017 Re-run all four quickstart.md scenarios end-to-end (including the Regression Check) as
      final sign-off on SC-001, SC-002, and SC-003.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup. BLOCKS both user stories below.
- **User Story 2 (Phase 3)**: Depends on Foundational. Must complete before User Story 1, because
  spec.md identifies it as a hard prerequisite (UCF line 1 requires a name to exist).
- **User Story 1 (Phase 4)**: Depends on Foundational **and** User Story 2 (T013's quickstart
  smoke test needs real generated names; T010/T012 could technically be written against
  hand-built fixtures alone, but the story isn't fully satisfiable end-to-end without US2).
- **User Story 3 (Phase 5)**: Depends on User Story 1 (T012) being complete — it shares the same
  implementation and only adds targeted test coverage.
- **Polish (Phase 6)**: Depends on all three user stories being complete.

### Within Each Phase

- Tests MUST be written and confirmed to FAIL before the corresponding implementation task
  (Constitution Principle IV, non-negotiable).
- Implementation task depends on its paired test task in the same phase.

### Parallel Opportunities

- T004 and T005 (Foundational): different files (`tests/test_models.py`, `tests/test_cli.py`), no
  dependency between them — run in parallel.
- T006 and T008 (User Story 2): different files (`tests/test_names.py`, `tests/test_generator.py`),
  no dependency between them — run in parallel.
- T010 and T011 (User Story 1): different files (`tests/test_formatter.py`, `tests/test_cli.py`),
  no dependency between them — run in parallel.

---

## Parallel Example: Foundational Fixture Repair

```bash
# After T003 lands (Character.name field exists), run together:
Task: "Update Character(...) fixtures in tests/test_models.py to pass name="
Task: "Update Character(...) fixtures in tests/test_cli.py to pass name="
```

## Parallel Example: User Story 2 Tests

```bash
# Before any implementation, run together:
Task: "Write tests/test_names.py for FIRST_NAMES/LAST_NAMES/generate_name"
Task: "Write failing name-assignment tests in tests/test_generator.py"
```

---

## Implementation Strategy

### MVP Scope

The MVP for this feature is **Foundational + User Story 2 + User Story 1** (T001–T013) —
not "User Story 1 alone" — because spec.md explicitly calls out User Story 2 as a prerequisite
for User Story 1's full satisfaction (UCF line 1 cannot render without a name). Stopping after
Foundational + User Story 1 only would leave `Character.name` populated by nothing real.

### Incremental Delivery

1. Setup + Foundational → baseline confirmed, model field in place (test_generator.py
   intentionally red).
2. User Story 2 → real names generated; test_generator.py green again. Not yet independently
   shippable (format still shows the old multi-section layout).
3. User Story 1 → MVP reached: full UCF output, real names, quickstart Scenarios 1 & 4 pass.
4. User Story 3 → additional targeted coverage confirming funds/equipment content details;
   no new shippable behavior, closes out spec.md's acceptance criteria explicitly.
5. Polish → quality gate (black, flake8, full coverage-enforced pytest run, full quickstart
   re-validation).

---

## Notes

- [P] tasks = different files, no dependencies.
- [Story] label maps task to specific user story for traceability; execution order above departs
  from strict P1→P2→P3 sequencing for the reason stated at the top of this document.
- Every test task must be confirmed RED before its paired implementation task begins (Constitution
  Principle IV).
- Commit after each task or logical group; run `uv run black . && uv run flake8 src tests && uv
  run pytest` before any push (AGENTS.md, pre-push hook).
