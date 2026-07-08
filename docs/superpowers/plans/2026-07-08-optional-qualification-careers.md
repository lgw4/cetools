# Optional Qualification for Careers (Batch 0) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a `Career` declare "no qualification requirement" (via `None`) so always-open careers like Drifter fit the data model, mirroring how `commission`/`advancement` already express "not applicable".

**Architecture:** Make `Career.qualification_stat`/`qualification_target` nullable in the frozen dataclass (`base.py`), with a both-or-neither construction guard. Then teach the two generator sites that read qualification — the enlistment `_check` in `generate_character` and the reroll loop in `roll_until_qualified` — to short-circuit when qualification is `None`. No new career ships in this batch; a synthetic `None`-qualification career (built with `dataclasses.replace(NAVY_CAREER, ...)`) proves the capability.

**Tech Stack:** Python 3.10+, frozen `@dataclass`, pytest (with coverage gate ≥85% on `src/cetools`), Black, flake8, isort.

## Global Constraints

- Package source under `src/cetools/`; tests mirror it under `tests/` (`test_careers.py`, `test_generator.py`).
- Run `uv run black . && uv run flake8 src tests && uv run pytest` before committing; the suite enforces ≥85% coverage on `src/cetools`.
- Conventional Commits for every commit (`feat:`, `test:`, `refactor:`, etc.).
- `str | None` union syntax is already used in `base.py` (`commission_stat: str | None`) — follow it; do not add `Optional`/`typing` imports.
- Do NOT touch: the CLI, the formatter, the draft table, or any existing career's data. Existing careers keep concrete qualification values and must behave exactly as before.

---

### Task 1: Make `Career` qualification optional

**Files:**
- Modify: `src/cetools/engine/careers/base.py:16-17` (field types) and `src/cetools/engine/careers/base.py:33-50` (`__post_init__` validation)
- Test: `tests/test_careers.py` (append to the `Career.__post_init__ validation` section at the end)

**Interfaces:**
- Consumes: nothing new.
- Produces: `Career.qualification_stat: str | None` and `Career.qualification_target: int | None`. Construction raises `ValueError` (message containing `both be set or both be None`) if exactly one of the two is `None`. When `qualification_stat` is a non-`None` value, it must still be a valid stat name (unchanged behavior).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_careers.py`:

```python
def test_career_allows_none_qualification() -> None:
    career = _make_valid_career(
        name="NoQual", qualification_stat=None, qualification_target=None
    )
    assert career.qualification_stat is None
    assert career.qualification_target is None


def test_career_rejects_qualification_stat_none_with_target_set() -> None:
    import pytest

    with pytest.raises(ValueError, match="both be set or both be None"):
        _make_valid_career(name="Bad", qualification_stat=None)


def test_career_rejects_qualification_target_none_with_stat_set() -> None:
    import pytest

    with pytest.raises(ValueError, match="both be set or both be None"):
        _make_valid_career(name="Bad", qualification_target=None)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_careers.py::test_career_allows_none_qualification tests/test_careers.py::test_career_rejects_qualification_stat_none_with_target_set tests/test_careers.py::test_career_rejects_qualification_target_none_with_stat_set -v --no-cov`

Expected: FAIL. `test_career_allows_none_qualification` fails because the current mandatory-stat loop rejects `None` (`ValueError: qualification_stat 'None' is not a valid stat`); the two rejection tests fail because no both-or-neither guard exists yet (they raise the wrong message or none at all).

- [ ] **Step 3: Change the field types**

In `src/cetools/engine/careers/base.py`, change the two qualification fields (currently lines 16-17):

```python
    qualification_stat: str | None
    qualification_target: int | None
```

- [ ] **Step 4: Update `__post_init__` validation**

In `src/cetools/engine/careers/base.py`, replace the two stat-validation loops at the top of `__post_init__` (currently lines 34-50 — the `valid_stats` assignment, the mandatory `("qualification_stat", ...), ("survival_stat", ...)` loop, and the optional `("commission_stat", ...), ("advancement_stat", ...)` loop) with:

```python
        valid_stats = set(STAT_NAMES)
        if (self.qualification_stat is None) != (self.qualification_target is None):
            raise ValueError(
                f"Career '{self.name}': qualification_stat and qualification_target"
                " must both be set or both be None"
            )
        if self.survival_stat not in valid_stats:
            raise ValueError(
                f"Career '{self.name}': survival_stat"
                f" '{self.survival_stat}' is not a valid stat"
            )
        for field_name, stat in (
            ("qualification_stat", self.qualification_stat),
            ("commission_stat", self.commission_stat),
            ("advancement_stat", self.advancement_stat),
        ):
            if stat is not None and stat not in valid_stats:
                raise ValueError(
                    f"Career '{self.name}': {field_name} '{stat}' is not a valid stat"
                )
```

Leave the skill-table loop and the ranks validation (below this block) unchanged.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_careers.py -v --no-cov`

Expected: PASS. The three new tests pass, and the existing validation tests still pass — in particular `test_career_rejects_invalid_qualification_stat` (which passes `qualification_stat="Luck"` with the target still set) now raises from the moved optional-group loop with the same `qualification_stat` message.

- [ ] **Step 6: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/base.py tests/test_careers.py
git commit -m "feat: allow Career qualification to be optional"
```

---

### Task 2: Teach the generator to skip `None` qualification

**Files:**
- Modify: `src/cetools/engine/generator.py:251-255` (enlistment check in `generate_character`) and `src/cetools/engine/generator.py:394-400` (`roll_until_qualified`)
- Test: `tests/test_generator.py` (add imports at top; append new tests)

**Interfaces:**
- Consumes: `Career.qualification_stat: str | None` / `qualification_target: int | None` from Task 1.
- Produces: `generate_character(career, roller=...)` with a `None`-qualification career auto-passes enlistment (never returns an enlistment `GenerationFailure`). `roll_until_qualified(career, roller=...)` returns the first characteristics dict immediately when qualification is `None`, without indexing on `None` and without looping.

- [ ] **Step 1: Add test imports**

At the top of `tests/test_generator.py`, add a `dataclasses` import and pull `STAT_NAMES` into the existing `from cetools.engine.models import ...` line so it reads:

```python
import dataclasses

import pytest
```

and

```python
from cetools.engine.models import STAT_NAMES, Character, GenerationFailure
```

(`NAVY_CAREER`, `generate_character`, `roll_until_qualified`, and `ConstantRoller` are already imported.)

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_generator.py`:

```python
def test_generate_character_none_qualification_skips_enlistment_failure() -> None:
    no_qual = dataclasses.replace(
        NAVY_CAREER, name="Drifter", qualification_stat=None, qualification_target=None
    )
    # ConstantRoller(1) would fail Navy's Int 6+ qualification; with no
    # qualification the career must not return an enlistment failure.
    result = generate_character(no_qual, roller=ConstantRoller(1))
    assert isinstance(result, Character)


def test_generate_character_concrete_qualification_still_gates() -> None:
    result = generate_character(NAVY_CAREER, roller=ConstantRoller(1))
    assert isinstance(result, GenerationFailure)
    assert "enlistment failed" in result.reason


def test_roll_until_qualified_none_qualification_returns_immediately() -> None:
    no_qual = dataclasses.replace(
        NAVY_CAREER, name="Drifter", qualification_stat=None, qualification_target=None
    )
    # All stats roll to 1 — Navy would loop forever; no-qual returns at once.
    result = roll_until_qualified(no_qual, roller=ConstantRoller(1))
    assert set(result.keys()) == set(STAT_NAMES)
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_generator.py::test_generate_character_none_qualification_skips_enlistment_failure tests/test_generator.py::test_roll_until_qualified_none_qualification_returns_immediately tests/test_generator.py::test_generate_character_concrete_qualification_still_gates -v --no-cov`

Expected: The two `none_qualification` tests FAIL with `KeyError: None` (the current code calls `_check(..., None, None)` → `_dm(characteristics, None)` → `characteristics[None]`, and `roll_until_qualified` indexes `characteristics[None]`). `test_generate_character_concrete_qualification_still_gates` already PASSES (it documents the unchanged gate).

- [ ] **Step 4: Guard the enlistment check in `generate_character`**

In `src/cetools/engine/generator.py`, replace the enlistment check (currently lines 251-255):

```python
    if (
        not bypass_qualification
        and career.qualification_stat is not None
        and career.qualification_target is not None
    ):
        if not _check(
            roller, characteristics, career.qualification_stat, career.qualification_target
        ):
            return GenerationFailure(reason=f"{career.name} enlistment failed")
```

- [ ] **Step 5: Short-circuit `roll_until_qualified`**

In `src/cetools/engine/generator.py`, update the loop body of `roll_until_qualified` (currently lines 397-400):

```python
    while True:
        characteristics = {stat: roller.roll(6, count=2) for stat in STAT_NAMES}
        if career.qualification_stat is None or career.qualification_target is None:
            return characteristics
        if characteristics[career.qualification_stat] >= career.qualification_target:
            return characteristics
```

- [ ] **Step 6: Run the new tests to verify they pass**

Run: `uv run pytest tests/test_generator.py::test_generate_character_none_qualification_skips_enlistment_failure tests/test_generator.py::test_roll_until_qualified_none_qualification_returns_immediately tests/test_generator.py::test_generate_character_concrete_qualification_still_gates -v --no-cov`

Expected: PASS (all three).

- [ ] **Step 7: Run the full suite with coverage**

Run: `uv run pytest`

Expected: PASS, coverage on `src/cetools` ≥85%. This confirms no existing career or generator behavior regressed.

- [ ] **Step 8: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/generator.py tests/test_generator.py
git commit -m "feat: skip qualification when a career has none"
```

---

## Self-Review

**Spec coverage:**
- Model field types `str | None`/`int | None` → Task 1, Step 3. ✓
- Move `qualification_stat` into the optional validation group → Task 1, Step 4. ✓
- Both-or-neither consistency guard raising `ValueError` → Task 1, Steps 1 & 4. ✓
- `generate_character` enlistment guard on `None` → Task 2, Step 4. ✓
- `roll_until_qualified` `None` short-circuit → Task 2, Step 5. ✓
- Not touched (CLI, formatter, draft table, existing careers) → Global Constraints; regression covered by Task 2 Steps 6-7 and the existing `test_careers.py`/`test_generator.py` suites. ✓
- Synthetic no-qualification fixture, no career shipped → Task 2 uses `dataclasses.replace(NAVY_CAREER, ...)`; no registry or README change. ✓

**Placeholder scan:** No TBD/TODO/"handle edge cases"/"similar to Task N". Every code step shows complete code. ✓

**Type consistency:** `qualification_stat`/`qualification_target` names and `str | None`/`int | None` types are identical across the model change (Task 1) and both generator sites and tests (Task 2). The both-or-neither `ValueError` message substring `both be set or both be None` is asserted in Task 1 tests and produced verbatim in Task 1 Step 4. ✓
