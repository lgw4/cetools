# Maritime System Defense (Planetary Navy) Career Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the Maritime System Defense (Planetary Navy) career to the cetools character generator as a data-only addition.

**Architecture:** The career system is fully data-driven — a career is a frozen `Career` dataclass instance consumed generically by the generator, CLI, and validation. This work adds one new data module (`MARITIME_CAREER`), registers it, makes it draftable, and adds tests. No engine, CLI, or `base.py` changes.

**Tech Stack:** Python 3, `uv` for dependency/venv management, Black + isort + flake8 for formatting/lint, pytest (with coverage gate) for tests.

## Global Constraints

- Coverage: `src/cetools` line coverage must stay at or above 85% (`uv run pytest` enforces this).
- Formatting/lint: `uv run black .`, `uv run isort .`, and `uv run flake8 src tests` must all pass before every commit.
- Commits: Conventional Commits (e.g. `feat: ...`, `test: ...`).
- Punctuation: em/en/hyphen dashes are tight (no surrounding spaces); prefer commas/colons/parentheses over em-dashes.
- `Career` dataclass rules (enforced in `base.py:__post_init__`): each of the four skill tables must have **exactly 6 entries**; `ranks` must have 1–7 entries with `ranks[i].rank == i`; stat fields must be valid `STAT_NAMES` (`Strength`, `Dexterity`, `Endurance`, `Intelligence`, `Education`, `Social Standing`); personal-development stat boosts use abbreviations (`+1 Str`, `+1 Dex`, `+1 End`, `+1 Int`, `+1 Edu`, `+1 Soc`).
- Career `name` drops the parenthetical subtitle, matching the sibling `"Aerospace System Defense"` (not `"...(Planetary Air Force)"`).

---

### Task 1: Career data module `MARITIME_CAREER` + tests

**Files:**
- Create: `src/cetools/engine/careers/maritime.py`
- Create: `tests/test_maritime_career.py`

**Interfaces:**
- Consumes: `Career`, `RankEntry` from `cetools.engine.careers.base`; `generate_character` from `cetools.engine.generator`; `Character` from `cetools.engine.models`; `ConstantRoller`, `SequenceRoller` from `conftest`.
- Produces: module-level constant `MARITIME_CAREER: Career` importable as `from cetools.engine.careers.maritime import MARITIME_CAREER`. `MARITIME_CAREER.name == "Maritime System Defense"`.

- [ ] **Step 1: Write the failing test file**

Create `tests/test_maritime_career.py` with the full data and behavioral suite:

```python
"""Tests for MARITIME_CAREER data fields and behavior."""

from cetools.engine.careers.base import RankEntry
from conftest import ConstantRoller, SequenceRoller

# ---------------------------------------------------------------------------
# Qualification, survival, commission, advancement, reenlistment, name
# ---------------------------------------------------------------------------


def test_maritime_qualification_stat() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.qualification_stat == "Endurance"


def test_maritime_qualification_target() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.qualification_target == 5


def test_maritime_survival_stat() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.survival_stat == "Endurance"


def test_maritime_survival_target() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.survival_target == 5


def test_maritime_commission_stat() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.commission_stat == "Intelligence"


def test_maritime_commission_target() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.commission_target == 6


def test_maritime_advancement_stat() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.advancement_stat == "Education"


def test_maritime_advancement_target() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.advancement_target == 7


def test_maritime_reenlistment_target() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.reenlistment_target == 5


def test_maritime_name() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.name == "Maritime System Defense"


# ---------------------------------------------------------------------------
# Skill tables (24 exact positions)
# ---------------------------------------------------------------------------


def test_maritime_personal_development_table() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "Athletics",
        "Melee Combat",
        "Vehicle",
    )


def test_maritime_service_skills_table() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.service_skills == (
        "Mechanics",
        "Gun Combat",
        "Gunnery",
        "Melee Combat",
        "Survival",
        "Watercraft",
    )


def test_maritime_specialist_skills_table() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.specialist_skills == (
        "Comms",
        "Electronics",
        "Gun Combat",
        "Demolitions",
        "Recon",
        "Watercraft",
    )


def test_maritime_advanced_education_table() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Jack o' Trades",
        "Medicine",
        "Leadership",
        "Tactics",
    )


def test_maritime_all_skill_tables_have_six_entries() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert len(MARITIME_CAREER.personal_development) == 6
    assert len(MARITIME_CAREER.service_skills) == 6
    assert len(MARITIME_CAREER.specialist_skills) == 6
    assert len(MARITIME_CAREER.advanced_education) == 6


# ---------------------------------------------------------------------------
# Rank entries (7 ranks, bonus skills at 0 and 3)
# ---------------------------------------------------------------------------


def test_maritime_rank_count() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert len(MARITIME_CAREER.ranks) == 7


def test_maritime_rank_titles() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    expected = [
        "Seaman",
        "Ensign",
        "Lieutenant",
        "Lt Commander",
        "Commander",
        "Captain",
        "Admiral",
    ]
    for i, title in enumerate(expected):
        assert (
            MARITIME_CAREER.ranks[i].title == title
        ), f"Rank {i}: expected {title!r}, got {MARITIME_CAREER.ranks[i].title!r}"


def test_maritime_rank_indices() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    for i in range(7):
        assert MARITIME_CAREER.ranks[i].rank == i


def test_maritime_rank_0_seaman_bonus_watercraft() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.ranks[0] == RankEntry(0, "Seaman", ("Watercraft",))


def test_maritime_rank_3_lt_commander_bonus_leadership() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.ranks[3] == RankEntry(3, "Lt Commander", ("Leadership",))


def test_maritime_ranks_without_bonus_skills() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    for rank_idx in [1, 2, 4, 5, 6]:
        assert (
            MARITIME_CAREER.ranks[rank_idx].bonus_skills == ()
        ), f"Rank {rank_idx} should have no bonus skills"


# ---------------------------------------------------------------------------
# Mustering-out tables (7 cash, 7 material)
# ---------------------------------------------------------------------------


def test_maritime_cash_benefits_values() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.cash_benefits == (
        1000,
        5000,
        10000,
        10000,
        20000,
        50000,
        50000,
    )


def test_maritime_cash_benefits_count() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert len(MARITIME_CAREER.cash_benefits) == 7


def test_maritime_material_benefits_content() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert MARITIME_CAREER.material_benefits == (
        "Low Passage",
        "+1 Edu",
        "Weapon",
        "Mid Passage",
        "Weapon",
        "High Passage",
        "+1 Soc",
    )


def test_maritime_material_benefits_count() -> None:
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert len(MARITIME_CAREER.material_benefits) == 7


# ---------------------------------------------------------------------------
# Commission and advancement behavior
# ---------------------------------------------------------------------------


def test_maritime_commission_roll_success_advances_to_rank_1() -> None:
    """When commission roll succeeds, character advances past rank 0."""
    from cetools.engine.careers.maritime import MARITIME_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    result = generate_character(MARITIME_CAREER, roller=ConstantRoller(12))
    if isinstance(result, Character):
        assert result.rank >= 1


def test_maritime_commission_roll_failure_stays_at_rank_0() -> None:
    """When commission roll fails, enlisted character stays at rank 0."""
    from cetools.engine.careers.maritime import MARITIME_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    _PRESET = {
        "Strength": 7,
        "Dexterity": 7,
        "Endurance": 7,
        "Intelligence": 7,
        "Education": 7,
        "Social Standing": 7,
    }

    # Survival (End 5): pass with 12
    # Commission (Int 6): fail with 1
    # Reenlistment (5): fail after 1 term with 1
    result = generate_character(
        MARITIME_CAREER,
        roller=SequenceRoller([12], default=1),
        preset_characteristics=_PRESET,
        bypass_qualification=True,
    )
    assert isinstance(result, Character)
    assert result.rank == 0


def test_maritime_advancement_increments_rank() -> None:
    """A commissioned character who passes advancement gains rank."""
    from cetools.engine.careers.maritime import MARITIME_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    result = generate_character(MARITIME_CAREER, roller=ConstantRoller(12))
    if isinstance(result, Character):
        assert result.rank >= 1


def test_maritime_rank_cap_at_6() -> None:
    """Character at rank 6 cannot advance further."""
    from cetools.engine.careers.maritime import MARITIME_CAREER

    assert len(MARITIME_CAREER.ranks) == 7
    assert MARITIME_CAREER.ranks[6].title == "Admiral"
    assert MARITIME_CAREER.ranks[6].rank == 6


def test_maritime_rank_0_watercraft_applied_at_enlistment() -> None:
    """A freshly generated Maritime character has Watercraft in their skills."""
    from cetools.engine.careers.maritime import MARITIME_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    result = generate_character(MARITIME_CAREER, roller=ConstantRoller(12))
    if isinstance(result, Character):
        assert "Watercraft" in result.skills


def test_maritime_rank_3_leadership_applied() -> None:
    """A character who reaches rank 3 has Leadership in their skills."""
    from cetools.engine.careers.maritime import MARITIME_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    result = generate_character(MARITIME_CAREER, roller=ConstantRoller(12))
    if isinstance(result, Character):
        if result.rank >= 3:
            assert "Leadership" in result.skills
```

- [ ] **Step 2: Run the test file to verify it fails**

Run: `uv run pytest tests/test_maritime_career.py --no-cov`
Expected: collection/import errors — `ModuleNotFoundError: No module named 'cetools.engine.careers.maritime'`.

- [ ] **Step 3: Create the career module**

Create `src/cetools/engine/careers/maritime.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

MARITIME_CAREER = Career(
    name="Maritime System Defense",
    qualification_stat="Endurance",
    qualification_target=5,
    survival_stat="Endurance",
    survival_target=5,
    commission_stat="Intelligence",
    commission_target=6,
    advancement_stat="Education",
    advancement_target=7,
    reenlistment_target=5,
    service_skills=(
        "Mechanics",
        "Gun Combat",
        "Gunnery",
        "Melee Combat",
        "Survival",
        "Watercraft",
    ),
    personal_development=(
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "Athletics",
        "Melee Combat",
        "Vehicle",
    ),
    specialist_skills=(
        "Comms",
        "Electronics",
        "Gun Combat",
        "Demolitions",
        "Recon",
        "Watercraft",
    ),
    advanced_education=(
        "Advocate",
        "Computer",
        "Jack o' Trades",
        "Medicine",
        "Leadership",
        "Tactics",
    ),
    ranks=(
        RankEntry(0, "Seaman", ("Watercraft",)),
        RankEntry(1, "Ensign", ()),
        RankEntry(2, "Lieutenant", ()),
        RankEntry(3, "Lt Commander", ("Leadership",)),
        RankEntry(4, "Commander", ()),
        RankEntry(5, "Captain", ()),
        RankEntry(6, "Admiral", ()),
    ),
    cash_benefits=(1000, 5000, 10000, 10000, 20000, 50000, 50000),
    material_benefits=(
        "Low Passage",
        "+1 Edu",
        "Weapon",
        "Mid Passage",
        "Weapon",
        "High Passage",
        "+1 Soc",
    ),
)
```

- [ ] **Step 4: Run the test file to verify it passes**

Run: `uv run pytest tests/test_maritime_career.py --no-cov`
Expected: PASS (all tests green).

- [ ] **Step 5: Format and lint**

Run: `uv run isort . && uv run black . && uv run flake8 src tests`
Expected: no changes reported by flake8; isort/black exit clean.

- [ ] **Step 6: Commit**

```bash
git add src/cetools/engine/careers/maritime.py tests/test_maritime_career.py
git commit -m "feat: add Maritime System Defense career data and tests"
```

---

### Task 2: Register and make Maritime draftable

**Files:**
- Modify: `src/cetools/engine/careers/registry.py`
- Modify: `tests/test_careers.py` (registry-membership + draft-table assertions)

**Interfaces:**
- Consumes: `MARITIME_CAREER` from `cetools.engine.careers.maritime` (Task 1).
- Produces: `CAREER_REGISTRY["maritime system defense"] is MARITIME_CAREER`; `DRAFT_TABLE == ("aerospace system defense", "marine", "maritime system defense", "navy", "scout", "navy")`.

- [ ] **Step 1: Write the failing registry/draft tests**

In `tests/test_careers.py`, add an import for `MARITIME_CAREER` alongside the existing career imports near the top of the file (the block that imports `NAVY_CAREER`, `SCOUT_CAREER`, etc.):

```python
from cetools.engine.careers.maritime import MARITIME_CAREER  # noqa: E402
```

Add these two new tests in the registry section (near `test_career_registry_navy_value`):

```python
def test_career_registry_has_maritime_key() -> None:
    assert "maritime system defense" in CAREER_REGISTRY


def test_career_registry_maritime_value() -> None:
    assert CAREER_REGISTRY["maritime system defense"] is MARITIME_CAREER
```

Add a draft-table slot assertion (near the other `test_draft_table_index_*` tests):

```python
def test_draft_table_index_2_is_maritime() -> None:
    assert DRAFT_TABLE[2] == "maritime system defense"


def test_draft_table_index_3_is_navy() -> None:
    assert DRAFT_TABLE[3] == "navy"
```

Update the existing `test_draft_table_other_entries_are_navy` to exclude the new maritime slot at index 2 (indices 0=aerospace, 1=marine, 2=maritime, 4=scout are the non-navy slots):

```python
def test_draft_table_other_entries_are_navy() -> None:
    for i, entry in enumerate(DRAFT_TABLE):
        if i not in (0, 1, 2, 4):
            assert entry == "navy", f"DRAFT_TABLE[{i}] expected 'navy', got {entry!r}"
```

- [ ] **Step 2: Run to verify the new/updated tests fail**

Run: `uv run pytest tests/test_careers.py -k "maritime or draft_table" --no-cov`
Expected: FAIL — `test_career_registry_has_maritime_key` / `test_career_registry_maritime_value` fail (key absent), `test_draft_table_index_2_is_maritime` fails (index 2 is currently `"navy"`), and `test_draft_table_other_entries_are_navy` fails once index 2 changes.

- [ ] **Step 3: Update the registry**

Edit `src/cetools/engine/careers/registry.py`. Add the import (keep imports alphabetically grouped with the existing ones):

```python
from cetools.engine.careers.maritime import MARITIME_CAREER
```

Add the registry key (keep dict keys alphabetical):

```python
CAREER_REGISTRY: dict[str, Career] = {
    "aerospace system defense": AEROSPACE_CAREER,
    "marine": MARINE_CAREER,
    "maritime system defense": MARITIME_CAREER,
    "navy": NAVY_CAREER,
    "scout": SCOUT_CAREER,
}
```

Update `DRAFT_TABLE` to the SRD-accurate 1D6 ordering (slot 6 stays `navy` as a placeholder until Surface System Defense exists):

```python
DRAFT_TABLE: tuple[str, ...] = (
    "aerospace system defense",  # 1
    "marine",  # 2
    "maritime system defense",  # 3
    "navy",  # 4
    "scout",  # 5
    "navy",  # 6: placeholder for Surface System Defense (not yet implemented)
)
```

- [ ] **Step 4: Run the full suite to verify green**

Run: `uv run pytest`
Expected: PASS, coverage at or above 85%.

- [ ] **Step 5: Format and lint**

Run: `uv run isort . && uv run black . && uv run flake8 src tests`
Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add src/cetools/engine/careers/registry.py tests/test_careers.py
git commit -m "feat: register Maritime System Defense and make it draftable"
```

---

## Self-Review

**Spec coverage:**
- New data module with all SRD fields → Task 1 (module + full data tests). ✓
- Skill tables, ranks with bonus skills, cash/material benefits → Task 1. ✓
- Education 8+ advanced-education gate → already generic in `generator.py`; verified by design, no task needed. ✓
- Registry key + CLI reachability (CLI reads `CAREER_REGISTRY` generically) → Task 2. ✓
- SRD-accurate `DRAFT_TABLE` with documented slot-6 placeholder → Task 2. ✓
- Tests mirroring `test_aerospace_career.py` + registry/draft assertions in `test_careers.py` → Tasks 1 and 2. ✓

**Placeholder scan:** No TBD/TODO/"handle edge cases"/"similar to Task N" — every code and test block is complete and literal. The one `navy` placeholder in `DRAFT_TABLE` slot 6 is an intentional, documented data value (Surface System Defense career does not yet exist), not a plan placeholder. ✓

**Type consistency:** `MARITIME_CAREER` name and import path identical across Task 1 (definition) and Task 2 (registry import + test). `RankEntry(0, "Seaman", ("Watercraft",))` and `RankEntry(3, "Lt Commander", ("Leadership",))` match between the module and the tests. Draft-table tuple in Task 2 Step 3 matches the assertions in Task 2 Step 1. ✓
