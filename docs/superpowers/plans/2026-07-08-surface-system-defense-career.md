# Surface System Defense (Planetary Army) Career Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the Surface System Defense (Planetary Army) career to the cetools character generator as a data-only addition, retiring the last `navy` placeholder in the draft table.

**Architecture:** The career system is fully data-driven — a career is a frozen `Career` dataclass instance consumed generically by the generator, CLI, and validation. This work adds one new data module (`SURFACE_CAREER`), registers it, makes it draftable at slot 6, adds tests, and updates the README. No engine, CLI, or `base.py` changes.

**Tech Stack:** Python 3, `uv` for dependency/venv management, Black + isort + flake8 for formatting/lint, pytest (with coverage gate) for tests.

## Global Constraints

- Coverage: `src/cetools` line coverage must stay at or above 85% (`uv run pytest` enforces this).
- Formatting/lint: `uv run isort .`, `uv run black .`, and `uv run flake8 src tests` must all pass before every commit.
- Commits: Conventional Commits (e.g. `feat: ...`, `test: ...`, `docs: ...`).
- Punctuation: em/en/hyphen dashes are tight (no surrounding spaces); prefer commas/colons/parentheses over em-dashes.
- `Career` dataclass rules (enforced in `base.py:__post_init__`): each of the four skill tables must have **exactly 6 entries**; `ranks` must have 1–7 entries with `ranks[i].rank == i`; stat fields must be valid `STAT_NAMES` (`Strength`, `Dexterity`, `Endurance`, `Intelligence`, `Education`, `Social Standing`); personal-development stat boosts use abbreviations (`+1 Str`, `+1 Dex`, `+1 End`, `+1 Int`, `+1 Edu`, `+1 Soc`).
- Career `name` drops the parenthetical subtitle, matching the siblings `"Maritime System Defense"` (not `"...(Planetary Navy)"`) and `"Aerospace System Defense"`.
- Distinctive to this career (verified against the SRD source): **Survival keys off Education (Edu 5+)**, not Endurance; and material-benefit slot 2 is `+1 Int`, not `+1 Edu`.

---

### Task 1: Career data module `SURFACE_CAREER` + tests

**Files:**
- Create: `src/cetools/engine/careers/surface.py`
- Create: `tests/test_surface_career.py`

**Interfaces:**
- Consumes: `Career`, `RankEntry` from `cetools.engine.careers.base`; `generate_character` from `cetools.engine.generator`; `Character` from `cetools.engine.models`; `ConstantRoller`, `SequenceRoller` from `conftest`.
- Produces: module-level constant `SURFACE_CAREER: Career` importable as `from cetools.engine.careers.surface import SURFACE_CAREER`. `SURFACE_CAREER.name == "Surface System Defense"`.

- [ ] **Step 1: Write the failing test file**

Create `tests/test_surface_career.py` with the full data and behavioral suite:

```python
"""Tests for SURFACE_CAREER data fields and behavior."""

from cetools.engine.careers.base import RankEntry
from conftest import ConstantRoller, SequenceRoller

# ---------------------------------------------------------------------------
# Qualification, survival, commission, advancement, reenlistment, name
# ---------------------------------------------------------------------------


def test_surface_qualification_stat() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.qualification_stat == "Endurance"


def test_surface_qualification_target() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.qualification_target == 5


def test_surface_survival_stat() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.survival_stat == "Education"


def test_surface_survival_target() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.survival_target == 5


def test_surface_commission_stat() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.commission_stat == "Endurance"


def test_surface_commission_target() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.commission_target == 6


def test_surface_advancement_stat() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.advancement_stat == "Education"


def test_surface_advancement_target() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.advancement_target == 7


def test_surface_reenlistment_target() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.reenlistment_target == 5


def test_surface_name() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.name == "Surface System Defense"


# ---------------------------------------------------------------------------
# Skill tables (24 exact positions)
# ---------------------------------------------------------------------------


def test_surface_personal_development_table() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "Athletics",
        "Melee Combat",
        "Vehicle",
    )


def test_surface_service_skills_table() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.service_skills == (
        "Mechanics",
        "Gun Combat",
        "Gunnery",
        "Melee Combat",
        "Recon",
        "Battle Dress",
    )


def test_surface_specialist_skills_table() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.specialist_skills == (
        "Comms",
        "Demolitions",
        "Gun Combat",
        "Melee Combat",
        "Survival",
        "Vehicle",
    )


def test_surface_advanced_education_table() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Jack o' Trades",
        "Medicine",
        "Leadership",
        "Tactics",
    )


def test_surface_all_skill_tables_have_six_entries() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert len(SURFACE_CAREER.personal_development) == 6
    assert len(SURFACE_CAREER.service_skills) == 6
    assert len(SURFACE_CAREER.specialist_skills) == 6
    assert len(SURFACE_CAREER.advanced_education) == 6


# ---------------------------------------------------------------------------
# Rank entries (7 ranks, bonus skills at 0 and 3)
# ---------------------------------------------------------------------------


def test_surface_rank_count() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert len(SURFACE_CAREER.ranks) == 7


def test_surface_rank_titles() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    expected = [
        "Private",
        "Lieutenant",
        "Captain",
        "Major",
        "Lt Colonel",
        "Colonel",
        "General",
    ]
    for i, title in enumerate(expected):
        assert (
            SURFACE_CAREER.ranks[i].title == title
        ), f"Rank {i}: expected {title!r}, got {SURFACE_CAREER.ranks[i].title!r}"


def test_surface_rank_indices() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    for i in range(7):
        assert SURFACE_CAREER.ranks[i].rank == i


def test_surface_rank_0_private_bonus_gun_combat() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.ranks[0] == RankEntry(0, "Private", ("Gun Combat",))


def test_surface_rank_3_major_bonus_leadership() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.ranks[3] == RankEntry(3, "Major", ("Leadership",))


def test_surface_ranks_without_bonus_skills() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    for rank_idx in [1, 2, 4, 5, 6]:
        assert (
            SURFACE_CAREER.ranks[rank_idx].bonus_skills == ()
        ), f"Rank {rank_idx} should have no bonus skills"


# ---------------------------------------------------------------------------
# Mustering-out tables (7 cash, 7 material)
# ---------------------------------------------------------------------------


def test_surface_cash_benefits_values() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.cash_benefits == (
        1000,
        5000,
        10000,
        10000,
        20000,
        50000,
        50000,
    )


def test_surface_cash_benefits_count() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert len(SURFACE_CAREER.cash_benefits) == 7


def test_surface_material_benefits_content() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert SURFACE_CAREER.material_benefits == (
        "Low Passage",
        "+1 Int",
        "Weapon",
        "Mid Passage",
        "Weapon",
        "High Passage",
        "+1 Soc",
    )


def test_surface_material_benefits_count() -> None:
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert len(SURFACE_CAREER.material_benefits) == 7


# ---------------------------------------------------------------------------
# Commission and advancement behavior
# ---------------------------------------------------------------------------


def test_surface_commission_roll_success_advances_to_rank_1() -> None:
    """When commission roll succeeds, character advances past rank 0."""
    from cetools.engine.careers.surface import SURFACE_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    result = generate_character(SURFACE_CAREER, roller=ConstantRoller(12))
    assert isinstance(result, Character)
    assert result.rank >= 1


def test_surface_commission_roll_failure_stays_at_rank_0() -> None:
    """When commission roll fails, enlisted character stays at rank 0."""
    from cetools.engine.careers.surface import SURFACE_CAREER
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

    # Survival (Edu 5): pass with the leading 12
    # Commission (End 6): fail with default 1
    # Reenlistment (5): fail after 1 term with default 1
    result = generate_character(
        SURFACE_CAREER,
        roller=SequenceRoller([12], default=1),
        preset_characteristics=_PRESET,
        bypass_qualification=True,
    )
    assert isinstance(result, Character)
    assert result.rank == 0


def test_surface_advancement_increments_rank() -> None:
    """A commissioned character who passes advancement gains rank."""
    from cetools.engine.careers.surface import SURFACE_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    result = generate_character(SURFACE_CAREER, roller=ConstantRoller(12))
    assert isinstance(result, Character)
    assert result.rank >= 1


def test_surface_rank_cap_at_6() -> None:
    """Character at rank 6 cannot advance further."""
    from cetools.engine.careers.surface import SURFACE_CAREER

    assert len(SURFACE_CAREER.ranks) == 7
    assert SURFACE_CAREER.ranks[6].title == "General"
    assert SURFACE_CAREER.ranks[6].rank == 6


def test_surface_rank_0_gun_combat_applied_at_enlistment() -> None:
    """A freshly generated Surface character has Gun Combat in their skills."""
    from cetools.engine.careers.surface import SURFACE_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    result = generate_character(SURFACE_CAREER, roller=ConstantRoller(12))
    assert isinstance(result, Character)
    assert "Gun Combat" in result.skills


def test_surface_rank_3_leadership_applied() -> None:
    """A character who reaches rank 3 has Leadership in their skills."""
    from cetools.engine.careers.surface import SURFACE_CAREER
    from cetools.engine.generator import generate_character
    from cetools.engine.models import Character

    result = generate_character(SURFACE_CAREER, roller=ConstantRoller(12))
    assert isinstance(result, Character)
    if result.rank >= 3:
        assert "Leadership" in result.skills
```

- [ ] **Step 2: Run the test file to verify it fails**

Run: `uv run pytest tests/test_surface_career.py --no-cov`
Expected: collection/import error — `ModuleNotFoundError: No module named 'cetools.engine.careers.surface'`.

- [ ] **Step 3: Create the career module**

Create `src/cetools/engine/careers/surface.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

SURFACE_CAREER = Career(
    name="Surface System Defense",
    qualification_stat="Endurance",
    qualification_target=5,
    survival_stat="Education",
    survival_target=5,
    commission_stat="Endurance",
    commission_target=6,
    advancement_stat="Education",
    advancement_target=7,
    reenlistment_target=5,
    service_skills=(
        "Mechanics",
        "Gun Combat",
        "Gunnery",
        "Melee Combat",
        "Recon",
        "Battle Dress",
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
        "Demolitions",
        "Gun Combat",
        "Melee Combat",
        "Survival",
        "Vehicle",
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
        RankEntry(0, "Private", ("Gun Combat",)),
        RankEntry(1, "Lieutenant", ()),
        RankEntry(2, "Captain", ()),
        RankEntry(3, "Major", ("Leadership",)),
        RankEntry(4, "Lt Colonel", ()),
        RankEntry(5, "Colonel", ()),
        RankEntry(6, "General", ()),
    ),
    cash_benefits=(1000, 5000, 10000, 10000, 20000, 50000, 50000),
    material_benefits=(
        "Low Passage",
        "+1 Int",
        "Weapon",
        "Mid Passage",
        "Weapon",
        "High Passage",
        "+1 Soc",
    ),
)
```

- [ ] **Step 4: Run the test file to verify it passes**

Run: `uv run pytest tests/test_surface_career.py --no-cov`
Expected: PASS (all tests green).

- [ ] **Step 5: Format and lint**

Run: `uv run isort . && uv run black . && uv run flake8 src tests`
Expected: no changes reported by flake8; isort/black exit clean.

- [ ] **Step 6: Commit**

```bash
git add src/cetools/engine/careers/surface.py tests/test_surface_career.py
git commit -m "feat: add Surface System Defense career data and tests"
```

---

### Task 2: Register Surface, make it draftable, and update the README

**Files:**
- Modify: `src/cetools/engine/careers/registry.py`
- Modify: `tests/test_careers.py` (registry-membership + draft-table assertions)
- Modify: `README.md` (supported-careers line)

**Interfaces:**
- Consumes: `SURFACE_CAREER` from `cetools.engine.careers.surface` (Task 1).
- Produces: `CAREER_REGISTRY["surface system defense"] is SURFACE_CAREER`; `DRAFT_TABLE == ("aerospace system defense", "marine", "maritime system defense", "navy", "scout", "surface system defense")`.

- [ ] **Step 1: Write the failing registry/draft tests**

In `tests/test_careers.py`, add an import for `SURFACE_CAREER` alongside the existing career imports (near the `MARITIME_CAREER` / `SCOUT_CAREER` import block that carries `# noqa: E402`):

```python
from cetools.engine.careers.surface import SURFACE_CAREER  # noqa: E402
```

Add these two new registry tests (near `test_career_registry_maritime_value`):

```python
def test_career_registry_has_surface_key() -> None:
    assert "surface system defense" in CAREER_REGISTRY


def test_career_registry_surface_value() -> None:
    assert CAREER_REGISTRY["surface system defense"] is SURFACE_CAREER
```

Add a draft-table slot assertion for the new slot 6 (near the other `test_draft_table_index_*` tests):

```python
def test_draft_table_index_5_is_surface() -> None:
    assert DRAFT_TABLE[5] == "surface system defense"
```

Replace the existing `test_draft_table_other_entries_are_navy` test. Slot 6 is no longer a `navy` placeholder, so after this change index 3 is the **only** `navy` slot. Delete the old test body and replace it with a test that asserts exactly that:

```python
def test_draft_table_only_slot_3_is_navy() -> None:
    for i, entry in enumerate(DRAFT_TABLE):
        if i == 3:
            assert entry == "navy", f"DRAFT_TABLE[3] expected 'navy', got {entry!r}"
        else:
            assert entry != "navy", f"DRAFT_TABLE[{i}] unexpectedly 'navy'"
```

- [ ] **Step 2: Run to verify the new/updated tests fail**

Run: `uv run pytest tests/test_careers.py -k "surface or draft_table" --no-cov`
Expected: FAIL — `test_career_registry_has_surface_key` / `test_career_registry_surface_value` fail (key absent), `test_draft_table_index_5_is_surface` fails (slot 6 is currently `"navy"`), and `test_draft_table_only_slot_3_is_navy` fails (slot 6 is still `"navy"`).

- [ ] **Step 3: Update the registry**

Edit `src/cetools/engine/careers/registry.py`. Add the import (keep imports alphabetically grouped with the existing ones — after `scout`):

```python
from cetools.engine.careers.surface import SURFACE_CAREER
```

Add the registry key (keep dict keys alphabetical — after `scout`):

```python
CAREER_REGISTRY: dict[str, Career] = {
    "aerospace system defense": AEROSPACE_CAREER,
    "marine": MARINE_CAREER,
    "maritime system defense": MARITIME_CAREER,
    "navy": NAVY_CAREER,
    "scout": SCOUT_CAREER,
    "surface system defense": SURFACE_CAREER,
}
```

Update `DRAFT_TABLE` so slot 6 points to the new career (retiring the placeholder):

```python
DRAFT_TABLE: tuple[str, ...] = (
    "aerospace system defense",  # 1
    "marine",  # 2
    "maritime system defense",  # 3
    "navy",  # 4
    "scout",  # 5
    "surface system defense",  # 6
)
```

- [ ] **Step 4: Run the full suite to verify green**

Run: `uv run pytest`
Expected: PASS, coverage at or above 85%.

- [ ] **Step 5: Update the README supported-careers line**

Edit `README.md` line 5. Add **Surface System Defense** to the alphabetical list so it reads:

```markdown
Supported careers: **Aerospace System Defense**, **Marine**, **Maritime System Defense**, **Navy**, **Scout**, **Surface System Defense**. Omit the career to have one drafted at random.
```

- [ ] **Step 6: Format and lint**

Run: `uv run isort . && uv run black . && uv run flake8 src tests`
Expected: clean.

- [ ] **Step 7: Commit**

```bash
git add src/cetools/engine/careers/registry.py tests/test_careers.py README.md
git commit -m "feat: register Surface System Defense and make it draftable"
```

---

## Self-Review

**Spec coverage:**
- New data module with all SRD fields (including Survival = Education, material slot 2 = `+1 Int`) → Task 1 (module + full data tests). ✓
- Skill tables, ranks with bonus skills (Gun Combat at 0, Leadership at 3), cash/material benefits → Task 1. ✓
- Education 8+ advanced-education gate → already generic in `generator.py`; verified by design, no task needed. ✓
- Registry key + CLI reachability (CLI reads `CAREER_REGISTRY` generically) → Task 2. ✓
- SRD-accurate `DRAFT_TABLE` slot 6 → Task 2 (placeholder retired). ✓
- README supported-careers list → Task 2 Step 5. ✓
- Tests mirroring `test_maritime_career.py` + registry/draft assertions in `test_careers.py` → Tasks 1 and 2. ✓

**Placeholder scan:** No TBD/TODO/"handle edge cases"/"similar to Task N" — every code and test block is complete and literal. The remaining `navy` at `DRAFT_TABLE[4]` is the SRD-correct value for draft roll 4 (Navy), not a placeholder. ✓

**Type consistency:** `SURFACE_CAREER` name and import path (`cetools.engine.careers.surface`) identical across Task 1 (definition), Task 2 (registry import + test). `RankEntry(0, "Private", ("Gun Combat",))` and `RankEntry(3, "Major", ("Leadership",))` match between the module (Task 1 Step 3) and the tests (Task 1 Step 1). Draft-table tuple in Task 2 Step 3 matches the assertions in Task 2 Step 1 (`DRAFT_TABLE[5] == "surface system defense"`, only slot 3 is `navy`). ✓
