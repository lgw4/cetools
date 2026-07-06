# Benefit List Refinements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse repeated material benefits into a single "Name x N" entry in the
formatted character output, and prevent a character from ever being granted the
"Explorers' Society" material benefit more than once.

**Architecture:** Two independent, small changes to existing modules — no new files,
no new data model fields. `src/cetools/formatter.py` gets a private grouping helper
consumed by `format_character`. `src/cetools/engine/generator.py` gets a private
material-benefit-picking helper (with a reroll loop) consumed by `_muster_out`.

**Tech Stack:** Python 3.13, pytest (with coverage), Black, flake8, uv. No new
dependencies.

## Global Constraints

- Spec: `specs/008-benefit-list-refinements/spec.md` (read this first if anything
  below is ambiguous).
- FR-003 / Clarifications: repeated benefit count text is exactly `"<Name> x <count>"`
  — lowercase `x`, one space on each side (e.g. `Weapon x 3`).
- FR-004: single-occurrence names keep their first-occurrence order; names with a
  count are appended after all singles, themselves ordered by first occurrence.
- FR-007: the uniqueness/reroll rule applies to the exact string `"Explorers' Society"`
  only — do not generalize to other benefit names.
- FR-008: the reroll must not change the total number of mustering-out rolls a
  character receives.
- Black line length / flake8 max-line-length: 99 chars (`pyproject.toml`, `.flake8`).
- Run `uv run black . && uv run flake8 src tests && uv run pytest` before treating any
  task as finished (per `AGENTS.md`); `pytest` alone enforces an 85% coverage floor on
  `src/cetools`. Use `--no-cov` when running a single test file/test during
  development (per-task steps below do this).
- Commit messages use Conventional Commits (`feat: ...`, `fix: ...`, `docs: ...`,
  `test: ...`).

## File Map

- `src/cetools/formatter.py` — add `_combine_material_benefits`; wire into
  `format_character`. (Task 1)
- `tests/test_formatter.py` — add coverage for combined/repeated material benefits.
  (Task 1)
- `specs/006-universal-character-format/contracts/ucf-output.md` — update the
  `equipment_list` grammar row, now stale. (Task 2)
- `src/cetools/engine/generator.py` — add `_UNIQUE_MATERIAL_BENEFIT` constant and
  `_roll_material_benefit`; wire into `_muster_out`. (Tasks 3–4)
- `tests/test_generator.py` — add unit tests for `_roll_material_benefit`, rewrite one
  existing test that would otherwise hang, add an integration-level dedup test.
  (Tasks 3–4)

---

### Task 1: Combine repeated material benefits in formatted output

**Files:**
- Modify: `src/cetools/formatter.py`
- Test: `tests/test_formatter.py`

**Interfaces:**
- Consumes: `Benefit`, `Character` from `cetools.engine.models` (existing, no changes).
- Produces: `_combine_material_benefits(benefits: list[Benefit]) -> list[str]` in
  `src/cetools/formatter.py`. `format_character`'s public signature is unchanged.

- [ ] **Step 1: Write failing tests**

Open `tests/test_formatter.py`. Immediately after the existing
`test_us3_material_benefits_listed_by_name_in_order` test (it ends with the line
`assert lines[-1] == "Weapon, Travellers' Aid Society, Ship Share"`), add:

```python
def test_material_benefits_combine_repeated_names_with_count() -> None:
    """Matches spec 008's worked example: singles keep their order, then any
    repeated name is appended once as "Name x N", in first-occurrence order."""
    character = _make_empty_character()
    character.benefits = [
        Benefit(kind="material", material_name="Weapon"),
        Benefit(kind="material", material_name="+1 Edu"),
        Benefit(kind="material", material_name="High Passage"),
        Benefit(kind="material", material_name="Weapon"),
        Benefit(kind="material", material_name="+1 Soc"),
        Benefit(kind="material", material_name="Weapon"),
    ]
    output = format_character(character)
    lines = output.split("\n")
    assert lines[-1] == "+1 Edu, High Passage, +1 Soc, Weapon x 3"


def test_material_benefits_multiple_repeated_names_ordered_by_first_occurrence() -> None:
    character = _make_empty_character()
    character.benefits = [
        Benefit(kind="material", material_name="High Passage"),
        Benefit(kind="material", material_name="Weapon"),
        Benefit(kind="material", material_name="High Passage"),
        Benefit(kind="material", material_name="Weapon"),
    ]
    output = format_character(character)
    lines = output.split("\n")
    assert lines[-1] == "High Passage x 2, Weapon x 2"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_formatter.py -v --no-cov -k combine_repeated_names_with_count or multiple_repeated_names`

Expected: both new tests FAIL. The first fails with something like
`AssertionError: assert 'Weapon, +1 Edu, High Passage, Weapon, +1 Soc, Weapon' == '+1 Edu, High Passage, +1 Soc, Weapon x 3'`
— today's formatter lists every occurrence uncombined.

- [ ] **Step 3: Implement the combining helper**

In `src/cetools/formatter.py`, change the import line and add the new function above
`_mishap_line`:

```python
from cetools.engine.models import Benefit, Character

_DISCHARGE_TEXT = {
    "honorable": "Honorably discharged",
    "medical": "Medically discharged",
    "none": "Injured in action",
}


def _combine_material_benefits(benefits: list[Benefit]) -> list[str]:
    names = [b.material_name for b in benefits if b.kind == "material"]

    counts: dict[str, int] = {}
    first_index: dict[str, int] = {}
    for i, name in enumerate(names):
        counts[name] = counts.get(name, 0) + 1
        first_index.setdefault(name, i)

    singles = sorted(
        (name for name, count in counts.items() if count == 1),
        key=lambda name: first_index[name],
    )
    repeats = sorted(
        (name for name, count in counts.items() if count > 1),
        key=lambda name: first_index[name],
    )

    return singles + [f"{name} x {counts[name]}" for name in repeats]
```

Then, inside `format_character`, replace:

```python
    material_parts = [b.material_name for b in character.benefits if b.kind == "material"]
    if material_parts:
        lines.append(", ".join(material_parts))
```

with:

```python
    material_parts = _combine_material_benefits(character.benefits)
    if material_parts:
        lines.append(", ".join(material_parts))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_formatter.py -v --no-cov`

Expected: all tests in the file PASS, including the two new ones and the
pre-existing `test_us3_material_benefits_listed_by_name_in_order` (unaffected, since
it has no repeated names).

- [ ] **Step 5: Commit**

```bash
git add src/cetools/formatter.py tests/test_formatter.py
git commit -m "feat: combine repeated material benefits in formatted output"
```

---

### Task 2: Update the stale UCF output contract

**Files:**
- Modify: `specs/006-universal-character-format/contracts/ucf-output.md`

**Interfaces:**
- None (documentation only). No automated test covers this file; verify by reading
  the edited table row.

- [ ] **Step 1: Update the `equipment_list` grammar row**

In the `## Grammar` table, replace this row:

```markdown
| `equipment_list` | `character.benefits` where `kind == "material"` | `material_name` per entry, joined `", "`, in benefit-list order |
```

with:

```markdown
| `equipment_list` | `character.benefits` where `kind == "material"` | Distinct `material_name` values: names occurring once first, in original first-occurrence order; then any name occurring 2+ times, rendered once as `"<Name> x <count>"`, also ordered by first occurrence; joined `", "` (see spec 008) |
```

- [ ] **Step 2: Commit**

```bash
git add specs/006-universal-character-format/contracts/ucf-output.md
git commit -m "docs: update UCF equipment_list contract for combined benefits"
```

---

### Task 3: Add the Explorers' Society reroll helper

**Files:**
- Modify: `src/cetools/engine/generator.py`
- Test: `tests/test_generator.py`

**Interfaces:**
- Consumes: `Career` from `cetools.engine.careers.base`, `DiceRoller` from
  `cetools.engine.dice` (both already imported in `generator.py`).
- Produces: `_UNIQUE_MATERIAL_BENEFIT: str` constant and
  `_roll_material_benefit(career: Career, material_dm: int, roller: DiceRoller, granted_names: set[str]) -> str`
  in `src/cetools/engine/generator.py`. Task 4 wires this into `_muster_out`.

- [ ] **Step 1: Add the new imports**

In `tests/test_generator.py`, the top of the file currently reads:

```python
import pytest

from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER
from cetools.engine.generator import (
    _apply_material_benefit,
    _apply_skill_entry,
    _apply_stat_boost,
    _check,
    _muster_out,
    draft_character,
    generate_career_character,
    generate_character,
    roll_until_qualified,
)
```

Change it to add `AEROSPACE_CAREER` (alphabetically before the `navy` import) and
`_roll_material_benefit` (alphabetically among the generator imports):

```python
import pytest

from cetools.engine.careers.aerospace import AEROSPACE_CAREER
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER
from cetools.engine.generator import (
    _apply_material_benefit,
    _apply_skill_entry,
    _apply_stat_boost,
    _check,
    _muster_out,
    _roll_material_benefit,
    draft_character,
    generate_career_character,
    generate_character,
    roll_until_qualified,
)
```

- [ ] **Step 2: Write failing tests**

Find the existing `test_gambling_skill_grants_cash_dm_on_muster_out` test (it ends
with `assert with_dm[0].cash_amount == 50000`) and the `# --- Benefits non-empty ---`
comment that follows it. Insert a new section between them:

```python
# --- Explorers' Society: reroll on repeat ---


def test_roll_material_benefit_grants_explorers_society_when_not_yet_granted() -> None:
    # NAVY_CAREER.material_benefits[6] = "Explorers' Society". material_dm=1, so
    # idx = clamp(roll + 1 - 1) = roll; ConstantRoller(6) -> idx 6.
    name = _roll_material_benefit(NAVY_CAREER, 1, ConstantRoller(6), set())
    assert name == "Explorers' Society"


def test_roll_material_benefit_rerolls_once_when_already_granted() -> None:
    # First die = 6 -> "Explorers' Society", but it's already granted, so it
    # rerolls: second die = 3 -> idx 3 -> "Mid Passage".
    roller = SequenceRoller([6, 3], default=6)
    name = _roll_material_benefit(
        NAVY_CAREER, 1, roller, {"Explorers' Society"}
    )
    assert name == "Mid Passage"


def test_roll_material_benefit_rerolls_repeatedly_until_non_duplicate() -> None:
    # Three more 6s in a row (each still "Explorers' Society", already granted)
    # before a 2 finally lands on idx 2 -> "Weapon".
    roller = SequenceRoller([6, 6, 6, 2], default=6)
    name = _roll_material_benefit(
        NAVY_CAREER, 1, roller, {"Explorers' Society"}
    )
    assert name == "Weapon"


def test_roll_material_benefit_unaffected_for_career_without_explorers_society() -> None:
    # AEROSPACE_CAREER.material_benefits[6] = "+1 Soc" (no "Explorers' Society" entry
    # exists in this table at all), so the uniqueness check can never match —
    # behavior is identical to before this feature, even when `granted_names`
    # already contains that string. material_dm=1, so idx = clamp(6 + 1 - 1) = 6.
    name = _roll_material_benefit(
        AEROSPACE_CAREER, 1, ConstantRoller(6), {"Explorers' Society"}
    )
    assert name == "+1 Soc"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_generator.py -v --no-cov -k roll_material_benefit`

Expected: FAIL with `ImportError: cannot import name '_roll_material_benefit' from 'cetools.engine.generator'` (collection error — the function doesn't exist yet).

- [ ] **Step 4: Implement the helper**

In `src/cetools/engine/generator.py`, the constants block currently reads:

```python
_MAX_TERMS = 7
_MAX_CASH_ROLLS = 3
```

Add a new constant after it:

```python
_MAX_TERMS = 7
_MAX_CASH_ROLLS = 3
_UNIQUE_MATERIAL_BENEFIT = "Explorers' Society"
```

Then add the new function directly after `_muster_out` (before `_apply_material_benefit`):

```python
def _roll_material_benefit(
    career: Career,
    material_dm: int,
    roller: DiceRoller,
    granted_names: set[str],
) -> str:
    mat_max = len(career.material_benefits) - 1
    while True:
        idx = max(0, min(mat_max, roller.roll(6) + material_dm - 1))
        name = career.material_benefits[idx]
        if name == _UNIQUE_MATERIAL_BENEFIT and name in granted_names:
            continue
        return name
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_generator.py -v --no-cov -k roll_material_benefit`

Expected: all 3 tests PASS. (`_muster_out` itself isn't wired up yet — that's Task 4
— so run the full file too and confirm nothing else broke: `uv run pytest tests/test_generator.py --no-cov`, expected: all PASS.)

- [ ] **Step 6: Commit**

```bash
git add src/cetools/engine/generator.py tests/test_generator.py
git commit -m "feat: add reroll-on-repeat helper for Explorers' Society benefit"
```

---

### Task 4: Wire the reroll helper into mustering-out

**Files:**
- Modify: `src/cetools/engine/generator.py`
- Test: `tests/test_generator.py`

**Interfaces:**
- Consumes: `_roll_material_benefit` (Task 3).
- Produces: updated `_muster_out` behavior. Return type (`list[Benefit]`) and
  signature are unchanged.

- [ ] **Step 1: Rewrite the row-7 test to call `_muster_out` directly**

`test_material_benefit_row_7_reachable_at_rank_5_plus` currently drives a *full*
`generate_character` run with `SmartRoller(10, 6)` — a roller that returns a fixed
`6` for every single-die roll, forever. Once Task 4's reroll logic is wired in, that
fixed-value roller would spin forever the moment a reroll is triggered (it can never
return anything but 6). Rewrite the test now, before wiring anything up, to call
`_muster_out` directly with a bounded number of rolls instead:

Replace:

```python
def test_material_benefit_row_7_reachable_at_rank_5_plus() -> None:
    # SmartRoller(10, 6): all 2D6 checks pass → rank 6 (Commodore), 7 terms served;
    # material_dm = 1 (rank >= 5). Each material benefit roll: 6 + 1 - 1 = 6 → index 6
    # → material_benefits[6] = "Explorers' Society". Without the DM it would be index 5
    # (High Passage), so this confirms row 7 is reachable.
    result = generate_character(NAVY_CAREER, roller=SmartRoller(10, 6))
    assert isinstance(result, Character)
    assert result.rank >= 5
    material_benefits = [b for b in result.benefits if b.kind == "material"]
    assert any(
        b.material_name == "Explorers' Society" for b in material_benefits
    ), "rank 5+ DM should make material benefit row 7 (Explorers' Society) reachable"
```

with:

```python
def test_material_benefit_row_7_reachable_at_rank_5_plus() -> None:
    # Direct unit test of _muster_out (a full generate_character run with a
    # fixed-value roller would hang once reroll-on-repeat is wired in below, since
    # a fixed roller can never produce a "different" result). rank=5 -> material_dm=1,
    # so idx = clamp(roll + 1 - 1) = roll. terms_served=2 + rank-5 bonus_rolls (2) = 4
    # total rolls: 3 cash (cap) + 1 material. ConstantRoller(6): material die=6 ->
    # idx=6 -> material_benefits[6] = "Explorers' Society". Without the rank-5+ DM,
    # idx would clamp to 5 (High Passage), so this confirms row 7 is reachable.
    result = _muster_out(
        career=NAVY_CAREER,
        terms_served=2,
        rank=5,
        skills={},
        characteristics={},
        roller=ConstantRoller(6),
    )
    assert len(result) == 4
    material_benefits = [b for b in result if b.kind == "material"]
    assert any(
        b.material_name == "Explorers' Society" for b in material_benefits
    ), "rank 5+ DM should make material benefit row 7 (Explorers' Society) reachable"
```

Run: `uv run pytest tests/test_generator.py -v --no-cov -k row_7_reachable`

Expected: PASS. (This is a refactor of an already-passing test, not a red step —
`_muster_out` isn't wired to reroll yet, so this just confirms the direct-call
rewrite is faithful to the original before we change any production code.)

- [ ] **Step 2: Write a new failing integration test**

Immediately after the test from Step 1, add:

```python
def test_muster_out_grants_explorers_society_once_and_rerolls_repeat() -> None:
    # NAVY_CAREER.material_benefits[6] = "Explorers' Society". rank=5 -> material_dm=1,
    # so idx = clamp(roll + 1 - 1) = roll. terms_served=3 + rank-5 bonus_rolls (2) = 5
    # total rolls: 3 cash (any values) + 2 material.
    # Material roll 1: die=6 -> idx 6 -> "Explorers' Society" (granted).
    # Material roll 2: die=6 -> idx 6 -> "Explorers' Society" again, but it's already
    # granted, so it rerolls: die=2 -> idx 2 -> "Weapon" (accepted).
    roller = SequenceRoller([1, 1, 1, 6, 6, 2], default=6)
    result = _muster_out(
        career=NAVY_CAREER,
        terms_served=3,
        rank=5,
        skills={},
        characteristics={},
        roller=roller,
    )
    assert len(result) == 5  # reroll must not add an extra roll (FR-008)
    material = [b.material_name for b in result if b.kind == "material"]
    assert material == ["Explorers' Society", "Weapon"]
```

Run: `uv run pytest tests/test_generator.py -v --no-cov -k grants_explorers_society_once`

Expected: FAIL — `_muster_out` doesn't dedupe yet, so `material` comes back as
`["Explorers' Society", "Explorers' Society"]`, not `["Explorers' Society", "Weapon"]`.

- [ ] **Step 3: Wire the helper into `_muster_out`**

In `src/cetools/engine/generator.py`, `_muster_out` currently reads:

```python
def _muster_out(
    career: Career,
    terms_served: int,
    rank: int,
    skills: dict[str, int],
    characteristics: dict[str, int],
    roller: DiceRoller,
) -> list[Benefit]:
    bonus_rolls = _RANK_BONUS_ROLLS.get(rank, 0)
    total_rolls = terms_served + bonus_rolls
    cash_rolls_used = 0
    benefits: list[Benefit] = []

    cash_dm = 1 if skills.get("Gambling", -1) >= 0 else 0
    material_dm = 1 if rank >= 5 else 0

    for _ in range(total_rolls):
        use_cash = cash_rolls_used < _MAX_CASH_ROLLS
        if use_cash:
            idx = max(0, min(6, roller.roll(6) + cash_dm - 1))
            amount = career.cash_benefits[idx]
            benefits.append(Benefit(kind="cash", cash_amount=amount))
            cash_rolls_used += 1
        else:
            mat_max = len(career.material_benefits) - 1
            idx = max(0, min(mat_max, roller.roll(6) + material_dm - 1))
            name = career.material_benefits[idx]
            _apply_material_benefit(name, characteristics, skills)
            benefits.append(Benefit(kind="material", material_name=name))

    return benefits
```

Replace it with:

```python
def _muster_out(
    career: Career,
    terms_served: int,
    rank: int,
    skills: dict[str, int],
    characteristics: dict[str, int],
    roller: DiceRoller,
) -> list[Benefit]:
    bonus_rolls = _RANK_BONUS_ROLLS.get(rank, 0)
    total_rolls = terms_served + bonus_rolls
    cash_rolls_used = 0
    benefits: list[Benefit] = []
    granted_material_names: set[str] = set()

    cash_dm = 1 if skills.get("Gambling", -1) >= 0 else 0
    material_dm = 1 if rank >= 5 else 0

    for _ in range(total_rolls):
        use_cash = cash_rolls_used < _MAX_CASH_ROLLS
        if use_cash:
            idx = max(0, min(6, roller.roll(6) + cash_dm - 1))
            amount = career.cash_benefits[idx]
            benefits.append(Benefit(kind="cash", cash_amount=amount))
            cash_rolls_used += 1
        else:
            name = _roll_material_benefit(
                career, material_dm, roller, granted_material_names
            )
            _apply_material_benefit(name, characteristics, skills)
            granted_material_names.add(name)
            benefits.append(Benefit(kind="material", material_name=name))

    return benefits
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_generator.py -v --no-cov`

Expected: every test in the file PASSes, including both tests touched in Steps 1–2
and all pre-existing tests.

- [ ] **Step 5: Commit**

```bash
git add src/cetools/engine/generator.py tests/test_generator.py
git commit -m "fix: grant Explorers' Society material benefit at most once"
```

---

### Task 5: Full verification

**Files:** none (verification only).

**Interfaces:** none.

- [ ] **Step 1: Format**

Run: `uv run black .`

Expected: `All done!`. If Black reports any files reformatted, stage and commit them
separately before continuing:

```bash
git add -A
git commit -m "style: apply black formatting"
```

If it reports `0 files reformatted`, skip the commit.

- [ ] **Step 2: Lint**

Run: `uv run flake8 src tests`

Expected: no output, exit code 0.

- [ ] **Step 3: Full test suite with coverage**

Run: `uv run pytest`

Expected: all tests PASS, and the coverage report shows `src/cetools` coverage at or
above 85% (the suite fails the build itself if it drops below that, so a green exit
code confirms this).

- [ ] **Step 4: Confirm no leftover changes**

Run: `git status`

Expected: working tree clean (everything from Tasks 1–5 already committed).
