# Background Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the placeholder background-skill logic in `generate_character` with rules-accurate Cepheus SRD background skills: `3 + Education DM` distinct level-0 skills, the first two drawn from a homeworld pool and the rest from the education pool.

**Architecture:** Two new module-level skill pools and two pure helpers (`_draw_distinct`, `_grant_background_skills`) in `src/cetools/engine/generator.py`. The grant helper is called at character-creation start (before the qualification check), faithful to the SRD ordering. Background skills seed the `skills` dict at level 0; career service skills, rank bonuses, and skill rolls stack on top exactly as today.

**Tech Stack:** Python ≥3.13, `uv`, pytest (+coverage), Black, flake8, isort.

## Global Constraints

- Python ≥3.13; format with Black (line-length 99); lint clean with flake8 (max-line-length 99); imports sorted with isort (black profile).
- Full suite must pass with `src/cetools` coverage ≥85%: `uv run black . && uv run flake8 src tests && uv run pytest`.
- Per-test timeout is 30s (configured); all tests here run in well under that.
- Conventional Commits for every commit (e.g. `feat: ...`).
- Dice randomness is always threaded through the injected `DiceRoller`; never use `random` directly. Tests use the `ConstantRoller`, `SmartRoller`, and `SequenceRoller` fakes from `tests/conftest.py`.

## Reference: the two skill pools

Homeworld pool (deduplicated union of the SRD homeworld tables, 10 skills):

```
Animals, Broker, Carousing, Computer, Gun Combat, Melee Combat, Streetwise, Survival, Watercraft, Zero-G
```

Education pool (the existing 15 Primary Education Skills, currently the `_BACKGROUND_SKILLS` tuple):

```
Admin, Advocate, Animals, Carousing, Comms, Computer, Electronics, Engineering, Life Sciences, Linguistics, Mechanics, Medicine, Physical Sciences, Social Sciences, Space Sciences
```

`Animals`, `Carousing`, and `Computer` appear in both pools; the education draw excludes any skill already taken from the homeworld pool so the whole background set stays distinct.

## Count formula (worked)

`count = max(0, 3 + characteristic_modifier(Education))`, using the project's existing `characteristic_modifier`:

| Education | modifier | count |
|-----------|----------|-------|
| 2         | -2       | 1     |
| 4         | -1       | 2     |
| 7         | 0        | 3     |
| 10        | +1       | 4     |
| 12        | +2       | 5     |
| 15        | +3       | 6     |

`homeworld_count = min(2, count)`; `education_count = count - homeworld_count`.

---

## Task 1: Homeworld pool and `_draw_distinct` helper

Purely additive. Adds the homeworld pool constant and a draw-without-replacement helper, with unit tests. Nothing else changes, so the existing suite stays green.

**Files:**
- Modify: `src/cetools/engine/generator.py` (add `_HOMEWORLD_SKILLS` after the existing `_BACKGROUND_SKILLS` tuple near line 38; add `_draw_distinct` after `_dm` near line 50)
- Test: `tests/test_generator.py` (append new tests)

**Interfaces:**
- Consumes: `DiceRoller` (already imported in `generator.py`).
- Produces: `_HOMEWORLD_SKILLS: tuple[str, ...]`; `_draw_distinct(pool: tuple[str, ...], count: int, roller: DiceRoller, exclude: tuple[str, ...] = ()) -> list[str]` — returns up to `count` distinct items from `pool` (skipping any in `exclude`), drawn without replacement using `(roller.roll(len(remaining)) - 1) % len(remaining)` indexing into a shrinking list (the die is sized to the remaining pool so pools larger than six stay fully reachable).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_generator.py` (the `_draw_distinct` import is added in the same edit):

```python
# --- Background skills: _draw_distinct ---


def test_draw_distinct_returns_requested_count_of_distinct_items() -> None:
    # ConstantRoller(1): idx = (1-1) % len = 0 every time → pops the head repeatedly.
    result = _draw_distinct(("A", "B", "C", "D"), 3, ConstantRoller(1))
    assert result == ["A", "B", "C"]
    assert len(set(result)) == 3


def test_draw_distinct_respects_exclude() -> None:
    result = _draw_distinct(("A", "B", "C"), 2, ConstantRoller(1), exclude=("A",))
    assert result == ["B", "C"]
    assert "A" not in result


def test_draw_distinct_truncates_when_over_requested() -> None:
    # Only 2 items available but 5 requested → returns just the 2.
    result = _draw_distinct(("A", "B"), 5, ConstantRoller(1))
    assert result == ["A", "B"]


def test_draw_distinct_uses_roller_to_index() -> None:
    # ConstantRoller(3): idx = (3-1) % len = 2 % len.
    # remaining=[A,B,C,D] → idx 2 → C; remaining=[A,B,D] → idx 2 → D.
    result = _draw_distinct(("A", "B", "C", "D"), 2, ConstantRoller(3))
    assert result == ["C", "D"]
```

Update the import block at the top of `tests/test_generator.py` to include `_draw_distinct`:

```python
from cetools.engine.generator import (
    _apply_material_benefit,
    _apply_skill_entry,
    _apply_stat_boost,
    _check,
    _draw_distinct,
    _muster_out,
    _roll_material_benefit,
    draft_character,
    generate_career_character,
    generate_character,
    roll_until_qualified,
)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_generator.py -k draw_distinct --no-cov -v`
Expected: FAIL — `ImportError: cannot import name '_draw_distinct'`.

- [ ] **Step 3: Add the pool constant and helper**

In `src/cetools/engine/generator.py`, add `_HOMEWORLD_SKILLS` immediately after the closing `)` of the existing `_BACKGROUND_SKILLS` tuple (leave `_BACKGROUND_SKILLS` unchanged in this task):

```python
_HOMEWORLD_SKILLS = (
    "Animals",
    "Broker",
    "Carousing",
    "Computer",
    "Gun Combat",
    "Melee Combat",
    "Streetwise",
    "Survival",
    "Watercraft",
    "Zero-G",
)
```

Add the helper immediately after the `_dm` function:

```python
def _draw_distinct(
    pool: tuple[str, ...],
    count: int,
    roller: DiceRoller,
    exclude: tuple[str, ...] = (),
) -> list[str]:
    remaining = [skill for skill in pool if skill not in exclude]
    chosen: list[str] = []
    for _ in range(min(count, len(remaining))):
        idx = (roller.roll(len(remaining)) - 1) % len(remaining)
        chosen.append(remaining.pop(idx))
    return chosen
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_generator.py -k draw_distinct --no-cov -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/generator.py tests/test_generator.py
git commit -m "feat: add homeworld skill pool and distinct-draw helper"
```

---

## Task 2: `_grant_background_skills` helper

Purely additive. Adds the grant helper and isolated unit tests that call it directly (no `generate_character` involvement, so no roller-sequence coupling). The helper is defined but not yet called by `generate_character`, so the existing suite stays green.

**Files:**
- Modify: `src/cetools/engine/generator.py` (add `_grant_background_skills` after `_draw_distinct`)
- Test: `tests/test_generator.py` (append new tests)

**Interfaces:**
- Consumes: `_HOMEWORLD_SKILLS`, `_BACKGROUND_SKILLS` (the education pool), `_draw_distinct`, `characteristic_modifier` (already imported).
- Produces: `_grant_background_skills(characteristics: dict[str, int], skills: dict[str, int], roller: DiceRoller) -> None` — mutates `skills` in place, seeding `count` distinct background skills at level 0. `count = max(0, 3 + characteristic_modifier(characteristics.get("Education", 0)))`; first `min(2, count)` from the homeworld pool, remainder from the education pool excluding the homeworld picks.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_generator.py`:

```python
# --- Background skills: _grant_background_skills ---


def test_background_skill_count_matches_three_plus_education_dm() -> None:
    # count = 3 + characteristic_modifier(Education).
    cases = {2: 1, 4: 2, 7: 3, 10: 4, 12: 5, 15: 6}
    for education, expected in cases.items():
        skills: dict[str, int] = {}
        _grant_background_skills({"Education": education}, skills, ConstantRoller(1))
        assert len(skills) == expected, f"Education {education} should grant {expected} skills"


def test_background_skills_are_all_level_zero() -> None:
    skills: dict[str, int] = {}
    _grant_background_skills({"Education": 12}, skills, ConstantRoller(1))
    assert all(level == 0 for level in skills.values())


def test_background_low_education_draws_only_homeworld_skills() -> None:
    # count 1 (Edu 2) and count 2 (Edu 4) → every skill comes from the homeworld pool.
    for education in (2, 4):
        skills: dict[str, int] = {}
        _grant_background_skills({"Education": education}, skills, ConstantRoller(1))
        assert set(skills) <= set(_HOMEWORLD_SKILLS)


def test_background_full_draw_is_deterministic_and_distinct() -> None:
    # Edu 12 → count 5. ConstantRoller(1) always pops index 0.
    # Homeworld: Animals, Broker. Education (excluding those): Admin, Advocate, Carousing.
    skills: dict[str, int] = {}
    _grant_background_skills({"Education": 12}, skills, ConstantRoller(1))
    assert set(skills) == {"Animals", "Broker", "Admin", "Advocate", "Carousing"}


def test_background_skills_reproducible_across_identical_rollers() -> None:
    first: dict[str, int] = {}
    second: dict[str, int] = {}
    _grant_background_skills({"Education": 10}, first, SequenceRoller([2, 4, 1, 3]))
    _grant_background_skills({"Education": 10}, second, SequenceRoller([2, 4, 1, 3]))
    assert first == second
```

Update the import block at the top of `tests/test_generator.py` to add `_grant_background_skills` and `_HOMEWORLD_SKILLS` (alongside `_draw_distinct` from Task 1):

```python
from cetools.engine.generator import (
    _HOMEWORLD_SKILLS,
    _apply_material_benefit,
    _apply_skill_entry,
    _apply_stat_boost,
    _check,
    _draw_distinct,
    _grant_background_skills,
    _muster_out,
    _roll_material_benefit,
    draft_character,
    generate_career_character,
    generate_character,
    roll_until_qualified,
)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_generator.py -k background --no-cov -v`
Expected: FAIL — `ImportError: cannot import name '_grant_background_skills'`.

- [ ] **Step 3: Add the helper**

In `src/cetools/engine/generator.py`, add immediately after `_draw_distinct`:

```python
def _grant_background_skills(
    characteristics: dict[str, int], skills: dict[str, int], roller: DiceRoller
) -> None:
    count = max(0, 3 + characteristic_modifier(characteristics.get("Education", 0)))
    homeworld_count = min(2, count)
    education_count = count - homeworld_count
    homeworld = _draw_distinct(_HOMEWORLD_SKILLS, homeworld_count, roller)
    education = _draw_distinct(
        _BACKGROUND_SKILLS, education_count, roller, exclude=tuple(homeworld)
    )
    for name in homeworld + education:
        skills[name] = 0
```

(Note: this references `_BACKGROUND_SKILLS` for the education pool; the rename to `_EDUCATION_SKILLS` happens in Task 3.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_generator.py -k background --no-cov -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/generator.py tests/test_generator.py
git commit -m "feat: add background skill granting helper"
```

---

## Task 3: Wire into generation, rename the pool, migrate desynced tests

This is the "activate and reconcile" task. It replaces the placeholder with a call to `_grant_background_skills` at chargen start, renames `_BACKGROUND_SKILLS` → `_EDUCATION_SKILLS` for clarity, adds one integration test, and migrates the 26 existing `SequenceRoller` tests that desync because background skills now consume roller draws before the rest of generation. All of these must land together to keep the suite green, so they are one commit.

**Background draw accounting (why the migration is needed):** With faithful start-ordering, `_grant_background_skills` makes exactly `count` single-die `roller.roll(...)` calls (each die sized to the remaining pool, not a fixed d6), right after characteristics are set and before the qualification check. For `SequenceRoller` tests this shifts every later value by `count` positions. The fix for each test is to insert `count` filler values (use `6`) at the point where the background draws occur — the value is irrelevant because it only selects which background skills are picked, which none of these tests assert on. `count` is derived from each test's Education (see the count table above).

**Files:**
- Modify: `src/cetools/engine/generator.py` (rename constant; replace placeholder at lines 207–210 with the helper call)
- Test: `tests/test_generator.py` (migrate desynced tests; add one integration test; fix a stale comment)
- Test: `tests/test_marine_career.py` (migrate three desynced tests)

**Interfaces:**
- Consumes: `_grant_background_skills` (Task 2).
- Produces: no new public interface; `generate_character` now grants background skills.

- [ ] **Step 1: Rename the education pool constant**

In `src/cetools/engine/generator.py`, rename the `_BACKGROUND_SKILLS` tuple to `_EDUCATION_SKILLS` (the 15-skill tuple near line 22), and update the reference inside `_grant_background_skills` from `_BACKGROUND_SKILLS` to `_EDUCATION_SKILLS`. The placeholder loop at lines 208–210 still references `_BACKGROUND_SKILLS` and will be removed in Step 2 — do not run the suite between Step 1 and Step 2.

- [ ] **Step 2: Replace the placeholder with the helper call**

In `generate_character`, replace:

```python
    skills: dict[str, int] = {}
    for i in range(3):
        bg_skill = _BACKGROUND_SKILLS[i % len(_BACKGROUND_SKILLS)]
        skills[bg_skill] = skills.get(bg_skill, -1) + 1
```

with:

```python
    skills: dict[str, int] = {}
    _grant_background_skills(characteristics, skills, roller)
```

This sits immediately after the characteristics are established and before the qualification check, so background skills are granted at chargen start.

- [ ] **Step 3: Add an integration test proving the wiring**

Append to `tests/test_generator.py`:

```python
def test_generate_character_grants_background_skills() -> None:
    # Preset Education 10 → 4 background skills. SmartRoller single-die value 1 →
    # idx 0 every draw → homeworld Animals, Broker; education Admin, Advocate.
    # Broker/Admin/Advocate are not Scout service, rank, or skill-roll outputs
    # under this roller, so they can only come from background granting.
    preset = {
        "Strength": 10,
        "Dexterity": 10,
        "Endurance": 10,
        "Intelligence": 10,
        "Education": 10,
        "Social Standing": 10,
    }
    result = generate_character(
        SCOUT_CAREER,
        roller=SmartRoller(10, 1),
        preset_characteristics=preset,
        bypass_qualification=True,
    )
    assert isinstance(result, Character)
    for skill in ("Animals", "Broker", "Admin", "Advocate"):
        assert skill in result.skills
```

`SCOUT_CAREER` is already imported at the top of `tests/test_generator.py`.

- [ ] **Step 4: Migrate the desynced Navy tests with the `[10]×7` pattern (Education 10 → insert 4 fillers)**

These call `generate_character(NAVY_CAREER, ...)` with no preset, so the 6 characteristic rolls come first (positions 0–5); the background draws consume positions 6–9; qualification and the rest follow. Insert `[6, 6, 6, 6]` after the six characteristic values. In `tests/test_generator.py`:

`test_survival_fail_returns_character_with_mishap`:
```python
    roller = SequenceRoller([10] * 6 + [6] * 4 + [10, 1], default=1)
```

`test_mishap_roll_1_injury_no_discharge`:
```python
    roller = SequenceRoller([10] * 6 + [6] * 4 + [10, 2, 1, 6, 6], default=6)
```

`test_mishap_roll_2_honorable_discharge`:
```python
    roller = SequenceRoller([10] * 6 + [6] * 4 + [10, 2, 2], default=6)
```

`test_mishap_roll_3_honorable_discharge_with_legal_debt`:
```python
    roller = SequenceRoller([10] * 6 + [6] * 4 + [10, 2, 3], default=6)
```

`test_mishap_roll_4_dishonorable_discharge_not_imprisoned`:
```python
    roller = SequenceRoller([10] * 6 + [6] * 4 + [10, 2, 4], default=6)
```

`test_mishap_roll_5_dishonorable_discharge_imprisoned`:
```python
    roller = SequenceRoller([10] * 6 + [6] * 4 + [10, 2, 5], default=6)
```

`test_mishap_roll_6_medical_discharge_with_injury`:
```python
    roller = SequenceRoller([10] * 6 + [6] * 4 + [10, 2, 6, 6], default=6)
```

- [ ] **Step 5: Migrate the desynced Navy tests with the `[8]×8` pattern (Education 8 → insert 3 fillers)**

No preset; insert `[6, 6, 6]` after the six characteristic values. In `tests/test_generator.py`, both `test_failed_commission_grants_two_skill_rolls` and `test_per_term_skill_rolls_recorded_in_term_history` use the same roller — change both:

```python
    roller = SequenceRoller([8] * 6 + [6, 6, 6] + [8, 8, 4, 2, 1, 2], default=1)
```

- [ ] **Step 6: Migrate the draft and career-path Scout tests**

`test_single_term_scout_muster_out` goes through `generate_career_character` (Scout): `roll_until_qualified` consumes the six `8`s and qualifies immediately, then `generate_character` runs the background draws (Education 8 → 3 fillers) before survival. Insert `[6, 6, 6]` after the six characteristic values:

```python
    roller = SequenceRoller([8] * 6 + [6, 6, 6] + [8, 1, 1, 1, 1, 4, 1], default=1)
```

`test_draft_character_survival_failure_returns_character_not_failure` goes through `draft_character` → `generate_career_character` (Scout): 1 draft roll, then 6 qualification rolls, then 4 background draws (Education 10). Insert `[6, 6, 6, 6]` after the seven leading values:

```python
    roller = SequenceRoller([5, 10, 10, 10, 10, 10, 10] + [6] * 4 + [2, 2], default=6)
```

- [ ] **Step 7: Migrate the preset Scout mishap helper functions**

Both helpers call `generate_character` with `_SCOUT_PRESET` (Education 10 → 4 background draws) and `bypass_qualification=True`, so the background draws consume the first 4 values of the sequence. Prepend `[6, 6, 6, 6]`. In `tests/test_generator.py`:

`_generate_scout_mishap_after_five_terms`:
```python
    values = [6] * 4 + _five_completed_scout_terms() + [1] + mishap_extra
```

`_generate_scout_first_term_mishap`:
```python
    values = [6] * 4 + [1] + mishap_extra
```

These two edits fix all six `test_mishap_outcome_*_..._after_five_terms` tests and all six `test_first_term_mishap_yields_no_benefits_or_pension` parametrizations.

- [ ] **Step 8: Migrate the desynced Marine tests (Education 7 → insert 3 fillers)**

All three call `generate_character(MARINE_CAREER, ..., preset_characteristics=_PRESET, bypass_qualification=True)` (Education 7 → 3 background draws consuming the first 3 sequence values). Prepend `[6, 6, 6]`. In `tests/test_marine_career.py`:

`test_marine_commission_success_advances_rank_0_to_1`:
```python
    roller = SequenceRoller([6, 6, 6] + [8, 6, 2, 1, 1, 2], default=1)
```

`test_marine_advancement_increments_commissioned_officer_rank`:
```python
    roller = SequenceRoller([6, 6, 6] + [8, 6, 2, 1, 1, 8, 8, 8, 1, 1, 2], default=1)
```

`test_marine_commissioned_officer_retains_rank_0_zero_g_bonus`:
```python
    roller = SequenceRoller([6, 6, 6] + [8, 6, 2, 1, 1, 2], default=1)
```

- [ ] **Step 9: Fix the now-stale comment**

In `tests/test_generator.py`, `test_education_below_8_excludes_advanced_education_skills` has a comment claiming background skills are "always granted" (a fixed `Advocate`). That is no longer true. Replace the stale comment line:

```python
    # "Advocate" is excluded: it also appears in background skills (always granted)
```

with:

```python
    # Background skills are random now; probe only advanced-education-exclusive skills.
```

The assertions in that test (absence of `Navigation`/`Tactics`) are unaffected — background skills never include those.

- [ ] **Step 10: Run the full suite**

Run: `uv run pytest`
Expected: PASS — every test green, `src/cetools` coverage ≥85%. If any `SequenceRoller` test still fails, its filler count is wrong: recompute `count = 3 + characteristic_modifier(Education)` for that test's Education and confirm the fillers were inserted at the point the background draws occur (after characteristic/qualification rolls, before survival).

- [ ] **Step 11: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/generator.py tests/test_generator.py tests/test_marine_career.py
git commit -m "feat: grant background skills during character generation"
```

---

## Self-review notes

- **Spec coverage:** count formula (Task 2 tests + count table), homeworld-then-education draw with distinctness (Task 2), level 0 (Task 2), merge-silently / no model change (Tasks 2–3, no `models.py` edits), start-ordering (Task 3 Step 2), pool rename (Task 3 Step 1). All covered.
- **Roller accounting:** every migrated test's filler count equals `3 + characteristic_modifier(Education)` for that test's Education (10→4, 8→3, 7→3), inserted at the position the background draws execute.
- **No placeholders:** every code and test block is complete and literal.
