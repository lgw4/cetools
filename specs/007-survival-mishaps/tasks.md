---

description: "Task list for Survival Mishaps Instead of Character Death"
---

# Tasks: Survival Mishaps Instead of Character Death

**Input**: Design documents from `/specs/007-survival-mishaps/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/mishaps-engine-api.md,
contracts/mishap-output.md, quickstart.md

**Tests**: Included and REQUIRED — Constitution Principle IV (Test-First) is non-negotiable for
this project; every task below that touches behavior is preceded by a failing-test task.

**Organization**: Tasks are grouped by user story. Unlike some prior features on this project,
there is **no hard cross-story prerequisite** here: User Story 2 (formatter output) only needs the
`MishapOutcome`/`Character.mishap`/`Character.debt` shapes added in Foundational — it can be built
and tested entirely against hand-constructed fixtures, independent of User Story 1's
`generator.py` integration. User Story 3 (benefit/pension/debt matrix) *does* depend on User
Story 1's term-loop change, since its tests drive real `generate_character` runs. See
Dependencies & Execution Order below.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Setup/Foundational/Polish tasks carry no `[Story]` label

## Path Conventions

Single project: `src/cetools/`, `tests/` at repository root (existing layout, unchanged — see
plan.md Project Structure).

## Implementation note carried into the tasks below (read before starting US1)

`resolve_survival_mishap` returns `tuple[MishapOutcome, int]` — the `MishapOutcome` exactly as
`data-model.md` specifies (no `debt` field on it), plus a second `int` for this mishap's debt
(`0`, the fixed `10_000`, or the random `1D6 * 10_000` crisis amount), since `MishapOutcome` itself
excludes `debt` (it lands only on `Character.debt`, never on the outcome record) and a tuple is the
only way for the *random* crisis-debt amount to travel from the resolver to the caller. This is now
reflected consistently in `contracts/mishaps-engine-api.md` and `data-model.md`'s behavioral
contract (step 2) — tasks T005/T006/T008/T010 below implement it as specified there.

---

## Phase 1: Setup

**Purpose**: Establish a known-green baseline before touching any code.

- [X] T001 Run `uv sync && uv run pytest` on the current branch tip and confirm the full suite is
      green with ≥85% coverage on `src/cetools`. No code changes in this task — it is the
      baseline every later regression is measured against. No new dependencies are required for
      this feature (plan.md Technical Context).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the shared data shapes (`MishapOutcome`, `Character.mishap`, `Character.debt`)
that every user story reads or writes. No table content and no resolution logic lives here —
just the record shapes, mirroring how `specs/006-universal-character-format` isolated
`Character.name` as the one shared field addition in its own Foundational phase.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Add failing tests to `tests/test_models.py`: (a) construct
      `MishapOutcome(roll=1, discharge_type="none", imprisoned=False, injury_reductions={"Strength": 3}, injury_crisis=False)`
      and assert each of the five fields is stored as given; (b) construct a `Character(...)` using
      the existing full-argument pattern already in this file (see
      `test_character_drafted_defaults_to_false`) *without* passing `mishap` or `debt` and assert
      `char.mishap is None` and `char.debt == 0`; (c) construct the same `Character(...)` passing
      `mishap=<a MishapOutcome instance>, debt=15000` and assert both are stored as given. Confirm
      these fail (RED) — `MishapOutcome` does not exist yet and `Character` has no `mishap`/`debt`
      fields.
- [X] T003 Implement in `src/cetools/engine/models.py`: add a `MishapOutcome` dataclass (plain,
      mutable — not frozen, consistent with `Benefit`/`Term`) with fields `roll: int`,
      `discharge_type: Literal["honorable", "dishonorable", "medical", "none"]`,
      `imprisoned: bool`, `injury_reductions: dict[str, int]`, `injury_crisis: bool`, exactly per
      `data-model.md` (no `__post_init__` invariant — see data-model.md's rationale: it is only
      ever constructed internally by `mishaps.resolve_survival_mishap`). Add two new fields to
      `Character`, placed after the existing `drafted: bool = False` field (order among
      already-defaulted fields doesn't matter for dataclass validity): `mishap: MishapOutcome |
      None = None` and `debt: int = 0`. Confirm T002 passes (GREEN).

**Checkpoint**: `MishapOutcome` exists; `Character` carries `mishap`/`debt`, both defaulted so
every existing `Character(...)` call site in the codebase and test suite keeps compiling
unchanged.

---

## Phase 3: User Story 1 - Always receive a usable character (Priority: P1) 🎯 MVP

**Goal**: A failed term survival roll resolves via the SRD Survival Mishaps table (new
`src/cetools/engine/mishaps.py`) instead of ending generation in an unrecoverable
`GenerationFailure`; the term loop ends immediately with correct age/terms-served bookkeeping.

**Independent Test**: Force a failed survival roll via a scripted roller and confirm
`generate_character` (and, transitively, `generate_career_character`/`draft_character`) returns a
complete `Character` with `.mishap is not None`, never a `GenerationFailure`.

### Tests for User Story 1 ⚠️

> Write these first, confirm they FAIL before implementing.

- [X] T004 [US1] Create `tests/test_mishaps.py` (new file) with table-shape tests: import
      `SURVIVAL_MISHAPS_TABLE`, `INJURY_TABLE`, `MishapEntry`, `InjuryEntry` from
      `cetools.engine.mishaps`; assert each table has exactly 6 entries; assert
      `SURVIVAL_MISHAPS_TABLE[roll - 1]` matches data-model.md's row-by-row values for every
      `roll` 1–6 (`discharge_type`/`imprisoned`/`debt`/`injury_rolls` — e.g. roll 1:
      `("none", False, 0, 2)`, roll 5: `("dishonorable", True, 0, 0)`); assert `INJURY_TABLE[roll -
      1]` matches data-model.md's row-by-row values for every roll 1–6
      (`candidate_stats`/`primary_dice`/`primary_fixed`/`secondary_amount` — e.g. roll 1:
      `(("Strength", "Dexterity", "Endurance"), 1, 0, 2)`, roll 3: `(("Strength", "Dexterity"), 0,
      2, 0)`, roll 6: `((), 0, 0, 0)`). Confirm these fail (RED) — `cetools.engine.mishaps` does
      not exist yet.
- [X] T005 [US1] Add to `tests/test_mishaps.py`: behavioral tests for
      `resolve_survival_mishap(roller, characteristics) -> tuple[MishapOutcome, int]` (see the
      Implementation Note above for the tuple-return decision) covering the four non-injury
      outcomes: roll=2 → `discharge_type="honorable"`, `imprisoned=False`, `injury_reductions=={}`,
      `injury_crisis=False`, debt `== 0`, `characteristics` dict unchanged (use e.g.
      `SequenceRoller([2], default=6)` so the single consumed roll is the mishap-table roll); roll=3
      → same but debt `== 10_000`; roll=4 → `discharge_type="dishonorable"`, `imprisoned=False`,
      debt `== 0`; roll=5 → `discharge_type="dishonorable"`, `imprisoned=True`, debt `== 0`. Then
      cover candidate-stat dice selection and secondary reduction for the injury outcomes: roll=6
      (single injury roll) with a controlled injury-table roll of e.g. 2 (all-3-candidates,
      `primary_dice=1`) — assert exactly one of Strength/Dexterity/Endurance was reduced by the
      1D6 amount rolled, chosen via an additional `roller.roll(len(candidate_stats))` call (mirror
      the existing `roller.roll(len(FIRST_NAMES)) - 1` indexing convention in
      `src/cetools/engine/names.py`), and the other two physical stats are unchanged
      (`secondary_amount == 0` for row 2); a second case with injury-table roll 1
      (`secondary_amount == 2`) confirming the two non-primary physical stats are each reduced by
      2; a third case with injury-table roll 3 (`candidate_stats == ("Strength", "Dexterity")`,
      `primary_fixed=2`) confirming the extra candidate-pick roll only ranges over those two
      stats, never Endurance. Confirm all fail (RED).
- [X] T006 [US1] Add to `tests/test_mishaps.py`: (a) the outcome-1 "roll twice, take the lower
      (more severe) result" rule (research.md D1) — drive two different injury-table rolls (e.g. 5
      then 2) via a `SequenceRoller` and assert the **row-2** reduction (the lower/more severe of
      the two) was applied, not row 5's; (b) injury-crisis tests (FR-009/research.md D8): a
      characteristic already near zero (e.g. `Strength: 2`) hit by a reduction that would take it
      to zero or below is instead left at `1`, the returned debt is `roller.roll(6) * 10_000` (a
      multiple of 10,000 between 10,000 and 60,000 — use a `SequenceRoller` to pin the crisis roll
      and assert the exact resulting amount), and the outcome's `injury_crisis` is `True`; (c) a
      case where a single mishap's reduction drives *two* physical characteristics to zero at once
      (e.g. row 1's dual reduction against two already-low stats) and assert only **one** crisis
      debt charge is returned (not two) while both zeroed stats are restored to `1`; (d) confirm
      `resolve_survival_mishap` mutates the passed-in `characteristics` dict in place (same
      convention as the existing `_apply_aging` helper in `generator.py`) rather than returning a
      new dict. Confirm all fail (RED).
- [X] T007 [US1] Add to `tests/test_mishaps.py`: the SC-004 statistical distribution test — call
      `resolve_survival_mishap` 10,000 times with a fresh `RandomDiceRoller()` and characteristics
      high enough that no injury-crisis interferes with counting outcomes (e.g. all physical stats
      at 10), tally `Counter(outcome.roll for outcome, _debt in results)`, and assert every count
      for roll 1–6 falls within `1500`–`1834` (±10% of the expected 1,667 per quickstart.md
      scenario 5 / spec.md SC-004's clarified tolerance). This test will be slower than the rest of
      the suite; that is expected and acceptable (plan.md's Testing section calls out exactly this
      one statistical test as the exception to the otherwise fully-deterministic suite). Confirm
      it fails (RED) — `resolve_survival_mishap` does not exist yet.

### Implementation for User Story 1

- [X] T008 [US1] Create `src/cetools/engine/mishaps.py`: `InjuryEntry` and `MishapEntry` frozen
      dataclasses per data-model.md's field tables; `SURVIVAL_MISHAPS_TABLE: tuple[MishapEntry,
      ...]` and `INJURY_TABLE: tuple[InjuryEntry, ...]` populated with the exact 6 rows each from
      data-model.md (also reproduced in T004 above); add a module-level length check for each table
      (e.g. `assert len(SURVIVAL_MISHAPS_TABLE) == 6` / `assert len(INJURY_TABLE) == 6`, or an
      explicit `raise ValueError(...)` if you prefer over a bare `assert`) mirroring the spirit of
      `Career.__post_init__`'s 6-entry validation in `careers/base.py`, adapted to plain tuples
      which have no `__post_init__` of their own. Confirm T004 passes (GREEN).
- [X] T009 [US1] Implement `resolve_survival_mishap(roller: DiceRoller, characteristics: dict[str,
      int]) -> tuple[MishapOutcome, int]` in `src/cetools/engine/mishaps.py` per
      `contracts/mishaps-engine-api.md`'s Behavior section (steps 1–5), returning the debt amount
      as the second tuple element per this file's Implementation Note: (1) roll `roller.roll(6)`
      to index `SURVIVAL_MISHAPS_TABLE`; (2) if `entry.injury_rolls > 0`, roll the injury table
      that many times, and for 2 rolls apply only the row for `min(roll_a, roll_b)`; applying a row
      means picking a primary stat from `candidate_stats` (via `roller.roll(len(candidate_stats))`
      when there's more than one candidate, else the sole candidate with no roll), reducing it by
      `roller.roll(6, count=primary_dice)` or by `primary_fixed`, then reducing every other
      physical stat by `secondary_amount` if nonzero — every reduction floored via `max(0, current
      - amount)`; (3) if any physical characteristic was driven to 0, charge exactly one crisis
      debt of `roller.roll(6) * 10_000` and restore every zeroed characteristic to `1`; (4) if
      `entry.debt > 0` (outcome 3), that fixed amount is this mishap's debt instead (mutually
      exclusive with step 3 in practice, per data-model.md); (5) return
      `(MishapOutcome(roll=..., discharge_type=entry.discharge_type, imprisoned=entry.imprisoned,
      injury_reductions=..., injury_crisis=...), debt_amount)`. Confirm T005, T006, and T007 all
      pass (GREEN).
- [X] T010 [US1] Add failing tests to `tests/test_generator.py`: replace
      `test_survival_fail_returns_generation_failure` (currently asserts `GenerationFailure`) with
      an equivalent test asserting `isinstance(result, Character)`, `result.mishap is not None`,
      and that the last entry in `result.terms` still has `survived=False` (the `Term` record is
      still appended, per data-model.md D6). Add six new integration tests — one per
      `SURVIVAL_MISHAPS_TABLE` roll — each using a `SequenceRoller` that first passes enlistment
      and the first term's checks, then fails the survival check, then supplies the exact mishap
      (and, where relevant, injury/candidate) rolls needed to hit that outcome; assert
      `result.mishap.roll`, `.discharge_type`, `.imprisoned`, `.injury_reductions`,
      `.injury_crisis`, and `result.debt` all match data-model.md's table for that row, and that
      `result.age == 20` (18 + 2) for every roll except 5, where `result.age == 24` (18 + 2 + 4 —
      research.md D9) — this is quickstart.md scenario 1. Also add an assertion that
      `draft_character()` (not just `generate_character`) returns a `Character` — never
      `GenerationFailure` — when its underlying survival check is rigged to fail, proving FR-011's
      uniform-application requirement (quickstart.md scenario 7) now that both functions funnel
      through the same `generate_character`. Finally, update
      `test_bypass_qualification_skips_enlistment`: it currently tolerates a `GenerationFailure`
      result via an `if isinstance(result, GenerationFailure): assert "enlist" not in
      result.reason.lower()` branch — since a survival-roll failure can no longer produce
      `GenerationFailure`, change this to an unconditional `assert isinstance(result, Character)`.
      Confirm all of the above fail (RED) against the current `generator.py`, which still returns
      `GenerationFailure` on survival failure.
- [X] T011 [US1] Update the term loop in `src/cetools/engine/generator.py`: introduce a local
      `debt = 0` accumulator before the loop; in the survival-check failure branch (currently
      `generator.py:220-233`), after appending the existing `Term(..., survived=False, ...)`
      record, call `mishap, mishap_debt = mishaps.resolve_survival_mishap(roller,
      characteristics)`, add `debt += mishap_debt`, increment `age` by `2` (not the usual `4`), and
      by an additional `4` if `mishap.imprisoned` (research.md D9); do **not** increment
      `terms_served`; then unconditionally end the term loop (`break` — no reenlistment roll, no
      further terms, no aging-table check for this term). Remove the `return
      GenerationFailure(reason=f"Character died...")` branch entirely. Pass `mishap=mishap,
      debt=debt` into the `Character(...)` constructed at the end of the function (`mishap=None,
      debt=0` implicitly on every path that never enters this branch — no other change needed
      there, since both fields already default correctly). Import `mishaps` at the top of the
      file. Confirm T010 passes and no other pre-existing `test_generator.py` test regresses.
- [X] T012 [P] [US1] Update `tests/test_marine_career.py`'s
      `test_generate_career_character_marine_100_runs_no_unhandled_exceptions`: since
      `generate_career_character` already bypasses enlistment (`roll_until_qualified` +
      `bypass_qualification=True`) and a survival-roll failure can no longer produce
      `GenerationFailure`, remove the `else: assert "survival check" in result.reason` branch and
      assert `isinstance(result, Character)` unconditionally for all 100 `RandomDiceRoller` runs.
      Confirm green against T011's `generator.py`.
- [X] T013 [P] [US1] Update `tests/test_cli.py`: repurpose the three stale "survival failure"
      tests (`test_survival_failure_exit_code_1`, `test_survival_failure_stdout_empty`,
      `test_survival_failure_stderr_nonempty`) — their mocked
      `GenerationFailure(reason="Character died during term 2 survival check")` describes a
      scenario that can no longer occur in production. Change the mocked `reason` string in all
      three to a different, still-plausible enlistment-failure wording (e.g. `"Marine enlistment
      failed"`) so these tests keep exercising the CLI's generic `GenerationFailure` → exit-1 /
      empty-stdout / non-empty-stderr handling (`cli/character.py:49-53`, which needs **no** code
      change per plan.md) without depending on an impossible scenario. Confirm still green — this
      is a test-only rewording, not a behavior change.

**Checkpoint**: Every survival-roll failure — through `generate_character`,
`generate_career_character`, and `draft_character` alike — now produces a complete `Character`
carrying a populated `mishap` and correct `debt`, never a `GenerationFailure`. MVP reached.

---

## Phase 4: User Story 2 - Understand why a career ended early (Priority: P2)

**Goal**: `format_character` prints a trailing `Mishap: ...` line (per
`contracts/mishap-output.md`) whenever `character.mishap is not None`, so a user can tell what
happened without inspecting fields directly.

**Independent Test**: Construct `Character` fixtures (directly, no `generate_character` needed)
covering each of the six mishap outcomes plus the no-mishap case, and confirm the printed output
correctly reflects discharge type, injury, imprisonment, crisis, and debt per outcome.

### Tests for User Story 2 ⚠️

- [X] T014 [P] [US2] Add failing tests to `tests/test_formatter.py` per
      `contracts/mishap-output.md`'s grammar, using directly-constructed `Character` fixtures
      (mirroring the existing `_make_full_character`/`_make_empty_character` pattern, extended with
      a `mishap=` argument): no `Mishap:` line at all when `character.mishap is None` (line count
      unchanged from today, not a blank line); `"Mishap: Honorably discharged"` for
      `discharge_type="honorable"` with no debt/injury; `"Mishap: Honorably discharged; Debt
      Cr10,000"` when `character.debt == 10_000`; `"Mishap: Dishonorably discharged"` for
      `discharge_type="dishonorable", imprisoned=False`; `"Mishap: Dishonorably discharged
      (imprisoned)"` when `imprisoned=True`; `"Mishap: Medically discharged"` for
      `discharge_type="medical"`; `"Mishap: Injured in action"` for `discharge_type="none"`; the
      injury clause `", injured (Endurance -2, Strength -1)"` appended (stats sorted
      alphabetically) when `injury_reductions` is non-empty; the crisis clause `", survived an
      injury crisis"` appended after the injury clause when `injury_crisis=True`; and the four
      worked examples from `contracts/mishap-output.md` reproduced verbatim as concrete
      fixture-driven cases (including the combined "Medically discharged, injured (Dexterity -6),
      survived an injury crisis; Debt Cr40,000" example). Also update the pre-existing
      `test_output_never_more_than_4_lines` (line count assumption predates this feature): split it
      so non-mishap characters are still asserted at ≤4 lines, while a new assertion covers a
      mishap-affected character at exactly 5 lines (4 UCF lines + 1 mishap line) when all four
      lines are otherwise present, or fewer when equipment/skills lines are empty. Confirm all new
      assertions fail (RED) against the current `formatter.py`, which has no mishap awareness.
- [X] T015 [US2] Update `format_character` in `src/cetools/formatter.py`: after the existing
      conditional equipment line, append a conditional `Mishap: ...` line built exactly per
      `contracts/mishap-output.md`'s grammar (`outcome_desc` by `discharge_type`/`imprisoned`,
      optional `, injured (...)` clause sorted alphabetically by stat, optional `, survived an
      injury crisis` clause, optional `; Debt Cr{amount:,}` clause when `character.debt != 0`),
      present only when `character.mishap is not None` — omitted as a whole line (not blank)
      otherwise. Confirm T014 passes (GREEN) and no earlier `test_formatter.py` assertion (US1/US3
      lines from `specs/006-universal-character-format`) regresses.

### Manual validation for User Story 2

- [X] T016 [US2] Manually validate quickstart.md scenario 2 (print `format_character(result)` for a
      mishap-affected character built via a rigged roller) and scenario 6 (`uv run cetools
      character generate`, run repeatedly — or with a seeded/deterministic roller patched in —
      until a mishap occurs; confirm exit code `0` and that stdout includes the `Mishap:` line).
      Smoke test only, no new automated assertions.

**Checkpoint**: A mishap-affected character's printed record fully explains what happened, with no
change required to `cli/character.py`.

---

## Phase 5: User Story 3 - Accurate financial and physical consequences (Priority: P3)

**Goal**: Benefits, pension, and debt for a mishap-affected character match the specific outcome's
severity — dishonorable discharge forfeits both mustering-out benefits and pension outright, every
other outcome preserves benefits/pension earned from prior, fully-completed terms while excluding
the mishap term's own roll.

**Independent Test**: For each of the six mishap outcomes, generate a character that already
completed 5+ terms before the mishap and confirm `benefits`/`pension`/`debt` match
quickstart.md's expected-outcome table (preserved, reduced, or forfeited).

### Tests for User Story 3 ⚠️

- [X] T017 [US3] Add tests to `tests/test_generator.py` driving a roller through 5+ fully-completed
      terms (so `_pension` would normally return non-`None` and `_muster_out` would normally grant
      multiple benefit rolls) before forcing a survival failure on a later term, for all six
      mishap outcomes, asserting per quickstart.md's expected-outcome table: outcomes 1, 2, 3, and
      6 — `len(result.benefits)` equals the mustering-out roll count for `terms_served` *excluding*
      the mishap term (i.e. unchanged from what those prior terms alone would have earned) and
      `result.pension is not None`; outcome 3 specifically — `result.debt == 10_000`; outcomes 1
      and 6 — `result.debt == 0` when no injury-crisis fired, or a multiple of `10_000` between
      `10_000` and `60_000` when one did; outcomes 4 and 5 — `result.benefits == []` and
      `result.pension is None`, **regardless** of the 5+ prior completed terms. Confirm the
      outcome-4/5 assertions fail (RED) against the current `generator.py` (no forfeiture override
      exists yet — it would otherwise incorrectly grant benefits/pension from the prior terms),
      while the outcome-1/2/3/6 assertions already pass (these already fall out of T011's
      `terms_served`-based bookkeeping with no new code, per research.md D6).

### Implementation for User Story 3

- [X] T018 [US3] Add the dishonorable-discharge forfeiture override to
      `src/cetools/engine/generator.py`: after the term loop and after computing `mishap`, if
      `mishap is not None and mishap.discharge_type == "dishonorable"`, skip the
      `_muster_out`/`_pension` calls entirely and use `benefits = []` and `pension = None` instead
      of their results, per data-model.md's behavioral contract step 5 (FR-005). Every other path
      (`mishap is None`, or `mishap.discharge_type != "dishonorable"`) continues to call
      `_muster_out`/`_pension` exactly as it does today. Confirm T017's outcome-4/5 assertions turn
      GREEN, with zero regression to outcomes 1/2/3/6 or any pre-existing non-mishap test.
- [X] T019 [US3] Add a targeted edge-case test to `tests/test_generator.py` (spec.md Edge Cases,
      "mishap during a character's very first term"): for each of the six outcomes, a character
      whose *first* term ends in a mishap has `terms_served == 0`, `result.benefits == []`, and
      `result.pension is None` — since no benefits/pension were earned yet regardless of discharge
      type, not only for the two dishonorable outcomes. Confirm this already passes as a natural
      consequence of `terms_served`-keyed `_muster_out`/`_pension` (no new code expected); if any
      outcome fails, treat it as a real gap and fix `generator.py` until green.

**Checkpoint**: All three user stories are independently verified against their own acceptance
scenarios; benefits, pension, and debt are correct for every one of the six mishap outcomes in
every eligibility state (pre-pension and post-pension-qualified).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final quality gate, matching AGENTS.md's required pre-push sequence.

- [X] T020 Run `uv run black .` then `uv run flake8 src tests`; fix any formatting/lint violations
      across `src/cetools/engine/mishaps.py`, `src/cetools/engine/models.py`,
      `src/cetools/engine/generator.py`, `src/cetools/formatter.py`, and every test file touched by
      this feature.
- [X] T021 Run `uv run pytest` (full suite, coverage enforced) and confirm ≥85% coverage on
      `src/cetools` with zero regressions outside mishap/formatter/generator-related tests.
- [X] T022 Re-run all seven quickstart.md scenarios end-to-end as final sign-off on SC-001 through
      SC-004: (1) failed-survival-roll-produces-character across all six outcomes; (2) mishap
      details visible in printed output; (3) benefits/pension/debt matrix per outcome; (4) injury
      crisis never kills; (5) SC-004 statistical distribution; (6) CLI end-to-end exit code 0; (7)
      uniform application across `draft_character` and `generate_career_character`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup. BLOCKS all three user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational only.
- **User Story 2 (Phase 4)**: Depends on Foundational only — **independent of User Story 1**; its
  tests use hand-built `Character`/`MishapOutcome` fixtures, not `generate_character`. Could be
  implemented before or in parallel with User Story 1 if staffed separately.
- **User Story 3 (Phase 5)**: Depends on Foundational **and** User Story 1 (T011's term-loop
  change) — its tests drive real `generate_character` runs through a completed mishap resolution
  path before adding the forfeiture override on top.
- **Polish (Phase 6)**: Depends on all three user stories being complete.

### Within Each Phase

- Tests MUST be written and confirmed to FAIL before the corresponding implementation task
  (Constitution Principle IV, non-negotiable).
- Implementation task depends on its paired test task(s) in the same phase.

### Parallel Opportunities

- T012 and T013 (User Story 1): different files (`tests/test_marine_career.py`,
  `tests/test_cli.py`), both depend only on T011 having landed, no dependency on each other — run
  in parallel.
- User Story 2 (Phase 4) as a whole can be staffed in parallel with User Story 1 (Phase 3) once
  Foundational is complete, per the Phase Dependencies note above.

---

## Parallel Example: Post-Integration Regression Repairs (User Story 1)

```bash
# After T011 lands, run together:
Task: "Update tests/test_marine_career.py's 100-run stability test to expect only Character"
Task: "Repurpose tests/test_cli.py's three stale survival-failure tests to enlistment wording"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories).
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: run quickstart.md scenarios 1 and 7 against the branch.
5. Deploy/demo if ready — every generation attempt already produces a usable character at this
   point, satisfying the feature's core value (SC-001).

### Incremental Delivery

1. Setup + Foundational → shared record shapes in place.
2. User Story 1 → MVP reached: no more `GenerationFailure` from survival rolls, anywhere.
3. User Story 2 → mishap details legible in the printed record (independent of US1; can be done
   in either order or in parallel).
4. User Story 3 → benefits/pension/debt correctness closes out the remaining acceptance criteria
   (SC-003).
5. Polish → quality gate (black, flake8, full coverage-enforced pytest run, full quickstart
   re-validation).

### Parallel Team Strategy

With two developers: one takes User Story 1 (Phase 3) while the other takes User Story 2
(Phase 4) immediately after Foundational lands, since Phase 4 has no dependency on Phase 3. User
Story 3 (Phase 5) must wait for whichever developer finishes User Story 1.

---

## Notes

- [P] tasks = different files, no dependencies.
- [Story] label maps task to specific user story for traceability.
- Every test task must be confirmed RED before its paired implementation task begins (Constitution
  Principle IV).
- `resolve_survival_mishap` returns `tuple[MishapOutcome, int]`, per
  `contracts/mishaps-engine-api.md` and `data-model.md`'s behavioral contract (step 2) — see the
  Implementation Note near the top of this file. It does not change `MishapOutcome`'s shape or
  either static table.
- Commit after each task or logical group; run `uv run black . && uv run flake8 src tests && uv
  run pytest` before any push (AGENTS.md, pre-push hook).
