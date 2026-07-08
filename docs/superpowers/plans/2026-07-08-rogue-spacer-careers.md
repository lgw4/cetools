# Rogue & Spacer Careers (Batch 3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the five Rogue/spacer careers (Belter, Mercenary, Pirate, Rogue, Merchant) as data modules, reusing the existing ship-shares and Explorers'-Society mechanics.

**Architecture:** Pure data plus one test-only change. Each career is a frozen `Career` literal in its own module with a mirrored per-career test file. One targeted generator test proves Belter's ship-shares slot rolls a quantity. A final task registers all five (registry-only, not draftable), updates the README, swaps the now-real `merchant` unknown-career sentinel in `tests/test_cli.py` to `smuggler`, and updates the two `Valid careers:` lists to 21 entries. No engine, model, or formatter changes.

**Tech Stack:** Python 3.10+, frozen `@dataclass`, pytest (coverage gate ≥85% on `src/cetools`), Black, flake8, isort.

## Global Constraints

- Package source under `src/cetools/`; tests mirror it under `tests/`.
- Run `uv run black . && uv run flake8 src tests && uv run pytest` before committing; the suite enforces ≥85% coverage on `src/cetools`. Single-file runs use `--no-cov`.
- Conventional Commits for every commit.
- Frozen-dataclass style with `str | None` / `int | None` unions — no `typing.Optional`.
- All skill names, benefit strings, rank titles, and numbers are transcribed **verbatim** from `docs/superpowers/specs/2026-07-08-rogue-spacer-careers-design.md`. `Explorers' Society` uses that exact plural-possessive spelling. The pilot rank bonus is recorded as `Piloting` (not the SRD rank-table abbreviation `Pilot`).
- The five new careers are added to `CAREER_REGISTRY` **only** — never `DRAFT_TABLE`. Selectable via `--career`, not draftable.
- `Career` field order follows the existing files: name, qualification, survival, commission, advancement, reenlistment, `service_skills`, `personal_development`, `specialist_skills`, `advanced_education`, `ranks`, `cash_benefits`, `material_benefits`.
- Belter has no commission/advancement (all four `None`) and a single `RankEntry(0, "Belter", ())` with an empty bonus tuple. Its blank SRD 7th material slot is dropped (6 entries). The other four keep 7 material entries.

---

### Task 1: Belter career (+ ship-shares test)

**Files:**
- Create: `src/cetools/engine/careers/belter.py`
- Test: `tests/test_belter_career.py`, and append one test to `tests/test_generator.py`

**Interfaces:**
- Produces: `BELTER_CAREER` importable from `cetools.engine.careers.belter`. No commission/advancement; single rank titled `Belter` with empty bonus; 6 material entries with the `"1D6 Ship Shares"` sentinel at index 4.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_belter_career.py`:

```python
from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.belter import BELTER_CAREER


def test_belter_scalar_fields() -> None:
    assert BELTER_CAREER.name == "Belter"
    assert BELTER_CAREER.qualification_stat == "Intelligence"
    assert BELTER_CAREER.qualification_target == 4
    assert BELTER_CAREER.survival_stat == "Dexterity"
    assert BELTER_CAREER.survival_target == 7
    assert BELTER_CAREER.commission_stat is None
    assert BELTER_CAREER.commission_target is None
    assert BELTER_CAREER.advancement_stat is None
    assert BELTER_CAREER.advancement_target is None
    assert BELTER_CAREER.reenlistment_target == 5


def test_belter_skill_tables() -> None:
    assert BELTER_CAREER.personal_development == (
        "+1 Str", "+1 Dex", "+1 End", "Zero-G", "Melee Combat", "Gambling",
    )
    assert BELTER_CAREER.service_skills == (
        "Comms", "Demolitions", "Gun Combat", "Gunnery", "Prospecting", "Piloting",
    )
    assert BELTER_CAREER.specialist_skills == (
        "Zero-G", "Electronics", "Prospecting", "Sciences", "Vehicle", "Vehicle",
    )
    assert BELTER_CAREER.advanced_education == (
        "Advocate", "Engineering", "Medicine", "Navigation", "Comms", "Tactics",
    )


def test_belter_ranks() -> None:
    assert BELTER_CAREER.ranks == (RankEntry(0, "Belter", ()),)


def test_belter_benefits() -> None:
    assert BELTER_CAREER.cash_benefits == (1000, 5000, 5000, 5000, 10000, 20000, 50000)
    assert BELTER_CAREER.material_benefits == (
        "Low Passage", "+1 Int", "Mid Passage", "Mid Passage", "1D6 Ship Shares",
        "High Passage",
    )
```

Append to `tests/test_generator.py`:

```python
def test_muster_out_belter_ship_shares() -> None:
    from cetools.engine.careers.belter import BELTER_CAREER
    from cetools.engine.models import STAT_NAMES

    characteristics = {stat: 7 for stat in STAT_NAMES}
    # rank 0 -> material_dm=0; terms=4 -> 4 total rolls (3 cash cap, 1 material).
    # Cash rolls 1,1,1; material-select roll 5 -> idx 4 -> "1D6 Ship Shares";
    # quantity roll 3.
    roller = SequenceRoller([1, 1, 1, 5, 3])
    benefits = _muster_out(BELTER_CAREER, 4, 0, {}, characteristics, roller)
    material = [b for b in benefits if b.kind == "material"]
    assert len(material) == 1
    assert material[0].material_name == "Ship Shares"
    assert material[0].material_quantity == 3
```

(`_muster_out`, `SequenceRoller` are already imported in `tests/test_generator.py`.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_belter_career.py tests/test_generator.py::test_muster_out_belter_ship_shares -v --no-cov`
Expected: FAIL — `ModuleNotFoundError` for `belter`.

- [ ] **Step 3: Create the career module**

Create `src/cetools/engine/careers/belter.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

BELTER_CAREER = Career(
    name="Belter",
    qualification_stat="Intelligence",
    qualification_target=4,
    survival_stat="Dexterity",
    survival_target=7,
    commission_stat=None,
    commission_target=None,
    advancement_stat=None,
    advancement_target=None,
    reenlistment_target=5,
    service_skills=("Comms", "Demolitions", "Gun Combat", "Gunnery", "Prospecting", "Piloting"),
    personal_development=("+1 Str", "+1 Dex", "+1 End", "Zero-G", "Melee Combat", "Gambling"),
    specialist_skills=("Zero-G", "Electronics", "Prospecting", "Sciences", "Vehicle", "Vehicle"),
    advanced_education=("Advocate", "Engineering", "Medicine", "Navigation", "Comms", "Tactics"),
    ranks=(RankEntry(0, "Belter", ()),),
    cash_benefits=(1000, 5000, 5000, 5000, 10000, 20000, 50000),
    material_benefits=(
        "Low Passage",
        "+1 Int",
        "Mid Passage",
        "Mid Passage",
        "1D6 Ship Shares",
        "High Passage",
    ),
)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_belter_career.py tests/test_generator.py::test_muster_out_belter_ship_shares -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/belter.py tests/test_belter_career.py tests/test_generator.py
git commit -m "feat: add Belter career"
```

---

### Task 2: Mercenary career

**Files:**
- Create: `src/cetools/engine/careers/mercenary.py`
- Test: `tests/test_mercenary_career.py`

**Interfaces:**
- Produces: `MERCENARY_CAREER` importable from `cetools.engine.careers.mercenary`. Full ranks 0–6; commission Intelligence 7, advancement Intelligence 6; 7 material entries with ship shares at index 6.

- [ ] **Step 1: Write the failing test**

Create `tests/test_mercenary_career.py`:

```python
from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.mercenary import MERCENARY_CAREER


def test_mercenary_scalar_fields() -> None:
    assert MERCENARY_CAREER.name == "Mercenary"
    assert MERCENARY_CAREER.qualification_stat == "Intelligence"
    assert MERCENARY_CAREER.qualification_target == 4
    assert MERCENARY_CAREER.survival_stat == "Endurance"
    assert MERCENARY_CAREER.survival_target == 6
    assert MERCENARY_CAREER.commission_stat == "Intelligence"
    assert MERCENARY_CAREER.commission_target == 7
    assert MERCENARY_CAREER.advancement_stat == "Intelligence"
    assert MERCENARY_CAREER.advancement_target == 6
    assert MERCENARY_CAREER.reenlistment_target == 5


def test_mercenary_skill_tables() -> None:
    assert MERCENARY_CAREER.personal_development == (
        "+1 Str", "+1 Dex", "+1 End", "Zero-G", "Melee Combat", "Gambling",
    )
    assert MERCENARY_CAREER.service_skills == (
        "Comms", "Mechanics", "Gun Combat", "Melee Combat", "Gambling", "Battle Dress",
    )
    assert MERCENARY_CAREER.specialist_skills == (
        "Gravitics", "Gun Combat", "Gunnery", "Melee Combat", "Recon", "Vehicle",
    )
    assert MERCENARY_CAREER.advanced_education == (
        "Advocate", "Engineering", "Medicine", "Navigation", "Sciences", "Tactics",
    )


def test_mercenary_ranks() -> None:
    assert MERCENARY_CAREER.ranks == (
        RankEntry(0, "Private", ("Gun Combat",)),
        RankEntry(1, "Lieutenant", ()),
        RankEntry(2, "Captain", ()),
        RankEntry(3, "Major", ("Tactics",)),
        RankEntry(4, "Lt Colonel", ()),
        RankEntry(5, "Colonel", ()),
        RankEntry(6, "Brigadier", ()),
    )


def test_mercenary_benefits() -> None:
    assert MERCENARY_CAREER.cash_benefits == (1000, 5000, 10000, 20000, 20000, 50000, 100000)
    assert MERCENARY_CAREER.material_benefits == (
        "Low Passage", "+1 Int", "Weapon", "High Passage", "+1 Soc",
        "High Passage", "1D6 Ship Shares",
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_mercenary_career.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Create the career module**

Create `src/cetools/engine/careers/mercenary.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

MERCENARY_CAREER = Career(
    name="Mercenary",
    qualification_stat="Intelligence",
    qualification_target=4,
    survival_stat="Endurance",
    survival_target=6,
    commission_stat="Intelligence",
    commission_target=7,
    advancement_stat="Intelligence",
    advancement_target=6,
    reenlistment_target=5,
    service_skills=("Comms", "Mechanics", "Gun Combat", "Melee Combat", "Gambling", "Battle Dress"),
    personal_development=("+1 Str", "+1 Dex", "+1 End", "Zero-G", "Melee Combat", "Gambling"),
    specialist_skills=("Gravitics", "Gun Combat", "Gunnery", "Melee Combat", "Recon", "Vehicle"),
    advanced_education=("Advocate", "Engineering", "Medicine", "Navigation", "Sciences", "Tactics"),
    ranks=(
        RankEntry(0, "Private", ("Gun Combat",)),
        RankEntry(1, "Lieutenant", ()),
        RankEntry(2, "Captain", ()),
        RankEntry(3, "Major", ("Tactics",)),
        RankEntry(4, "Lt Colonel", ()),
        RankEntry(5, "Colonel", ()),
        RankEntry(6, "Brigadier", ()),
    ),
    cash_benefits=(1000, 5000, 10000, 20000, 20000, 50000, 100000),
    material_benefits=(
        "Low Passage",
        "+1 Int",
        "Weapon",
        "High Passage",
        "+1 Soc",
        "High Passage",
        "1D6 Ship Shares",
    ),
)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_mercenary_career.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/mercenary.py tests/test_mercenary_career.py
git commit -m "feat: add Mercenary career"
```

---

### Task 3: Pirate career

**Files:**
- Create: `src/cetools/engine/careers/pirate.py`
- Test: `tests/test_pirate_career.py`

**Interfaces:**
- Produces: `PIRATE_CAREER` importable from `cetools.engine.careers.pirate`. Full ranks 0–6; commission Strength 7, advancement Intelligence 6; rank 2 bonus `Piloting`; 7 material entries with ship shares at index 6.

- [ ] **Step 1: Write the failing test**

Create `tests/test_pirate_career.py`:

```python
from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.pirate import PIRATE_CAREER


def test_pirate_scalar_fields() -> None:
    assert PIRATE_CAREER.name == "Pirate"
    assert PIRATE_CAREER.qualification_stat == "Dexterity"
    assert PIRATE_CAREER.qualification_target == 5
    assert PIRATE_CAREER.survival_stat == "Dexterity"
    assert PIRATE_CAREER.survival_target == 6
    assert PIRATE_CAREER.commission_stat == "Strength"
    assert PIRATE_CAREER.commission_target == 7
    assert PIRATE_CAREER.advancement_stat == "Intelligence"
    assert PIRATE_CAREER.advancement_target == 6
    assert PIRATE_CAREER.reenlistment_target == 5


def test_pirate_skill_tables() -> None:
    assert PIRATE_CAREER.personal_development == (
        "+1 Str", "+1 Dex", "+1 End", "Melee Combat", "Bribery", "Gambling",
    )
    assert PIRATE_CAREER.service_skills == (
        "Streetwise", "Electronics", "Gun Combat", "Melee Combat", "Recon", "Vehicle",
    )
    assert PIRATE_CAREER.specialist_skills == (
        "Zero-G", "Comms", "Engineering", "Gunnery", "Navigation", "Piloting",
    )
    assert PIRATE_CAREER.advanced_education == (
        "Computer", "Gravitics", "Jack o' Trades", "Medicine", "Advocate", "Tactics",
    )


def test_pirate_ranks() -> None:
    assert PIRATE_CAREER.ranks == (
        RankEntry(0, "Crewman", ("Gunnery",)),
        RankEntry(1, "Corporal", ()),
        RankEntry(2, "Lieutenant", ("Piloting",)),
        RankEntry(3, "Lt Commander", ()),
        RankEntry(4, "Commander", ()),
        RankEntry(5, "Captain", ()),
        RankEntry(6, "Commodore", ()),
    )


def test_pirate_benefits() -> None:
    assert PIRATE_CAREER.cash_benefits == (1000, 5000, 10000, 20000, 20000, 50000, 100000)
    assert PIRATE_CAREER.material_benefits == (
        "Low Passage", "+1 Int", "Weapon", "High Passage", "+1 Soc",
        "High Passage", "1D6 Ship Shares",
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_pirate_career.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Create the career module**

Create `src/cetools/engine/careers/pirate.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

PIRATE_CAREER = Career(
    name="Pirate",
    qualification_stat="Dexterity",
    qualification_target=5,
    survival_stat="Dexterity",
    survival_target=6,
    commission_stat="Strength",
    commission_target=7,
    advancement_stat="Intelligence",
    advancement_target=6,
    reenlistment_target=5,
    service_skills=("Streetwise", "Electronics", "Gun Combat", "Melee Combat", "Recon", "Vehicle"),
    personal_development=("+1 Str", "+1 Dex", "+1 End", "Melee Combat", "Bribery", "Gambling"),
    specialist_skills=("Zero-G", "Comms", "Engineering", "Gunnery", "Navigation", "Piloting"),
    advanced_education=("Computer", "Gravitics", "Jack o' Trades", "Medicine", "Advocate", "Tactics"),
    ranks=(
        RankEntry(0, "Crewman", ("Gunnery",)),
        RankEntry(1, "Corporal", ()),
        RankEntry(2, "Lieutenant", ("Piloting",)),
        RankEntry(3, "Lt Commander", ()),
        RankEntry(4, "Commander", ()),
        RankEntry(5, "Captain", ()),
        RankEntry(6, "Commodore", ()),
    ),
    cash_benefits=(1000, 5000, 10000, 20000, 20000, 50000, 100000),
    material_benefits=(
        "Low Passage",
        "+1 Int",
        "Weapon",
        "High Passage",
        "+1 Soc",
        "High Passage",
        "1D6 Ship Shares",
    ),
)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_pirate_career.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/pirate.py tests/test_pirate_career.py
git commit -m "feat: add Pirate career"
```

---

### Task 4: Rogue career

**Files:**
- Create: `src/cetools/engine/careers/rogue.py`
- Test: `tests/test_rogue_career.py`

**Interfaces:**
- Produces: `ROGUE_CAREER` importable from `cetools.engine.careers.rogue`. Full ranks 0–6; commission Strength 6, advancement Intelligence 7; rank 2 bonus `Gun Combat`; 7 material entries, no ship shares, `Weapon` at slots 3 and 5.

- [ ] **Step 1: Write the failing test**

Create `tests/test_rogue_career.py`:

```python
from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.rogue import ROGUE_CAREER


def test_rogue_scalar_fields() -> None:
    assert ROGUE_CAREER.name == "Rogue"
    assert ROGUE_CAREER.qualification_stat == "Dexterity"
    assert ROGUE_CAREER.qualification_target == 5
    assert ROGUE_CAREER.survival_stat == "Dexterity"
    assert ROGUE_CAREER.survival_target == 4
    assert ROGUE_CAREER.commission_stat == "Strength"
    assert ROGUE_CAREER.commission_target == 6
    assert ROGUE_CAREER.advancement_stat == "Intelligence"
    assert ROGUE_CAREER.advancement_target == 7
    assert ROGUE_CAREER.reenlistment_target == 4


def test_rogue_skill_tables() -> None:
    assert ROGUE_CAREER.personal_development == (
        "+1 Str", "+1 Dex", "+1 End", "Melee Combat", "Bribery", "Gambling",
    )
    assert ROGUE_CAREER.service_skills == (
        "Streetwise", "Mechanics", "Gun Combat", "Melee Combat", "Recon", "Vehicle",
    )
    assert ROGUE_CAREER.specialist_skills == (
        "Computer", "Electronics", "Bribery", "Broker", "Recon", "Vehicle",
    )
    assert ROGUE_CAREER.advanced_education == (
        "Computer", "Gravitics", "Jack o' Trades", "Medicine", "Advocate", "Tactics",
    )


def test_rogue_ranks() -> None:
    assert ROGUE_CAREER.ranks == (
        RankEntry(0, "Independent", ("Streetwise",)),
        RankEntry(1, "Associate", ()),
        RankEntry(2, "Soldier", ("Gun Combat",)),
        RankEntry(3, "Lieutenant", ()),
        RankEntry(4, "Underboss", ()),
        RankEntry(5, "Consigliere", ()),
        RankEntry(6, "Boss", ()),
    )


def test_rogue_benefits() -> None:
    assert ROGUE_CAREER.cash_benefits == (1000, 5000, 5000, 5000, 10000, 20000, 50000)
    assert ROGUE_CAREER.material_benefits == (
        "Low Passage", "+1 Int", "Weapon", "Mid Passage", "Weapon",
        "High Passage", "+1 Soc",
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_rogue_career.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Create the career module**

Create `src/cetools/engine/careers/rogue.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

ROGUE_CAREER = Career(
    name="Rogue",
    qualification_stat="Dexterity",
    qualification_target=5,
    survival_stat="Dexterity",
    survival_target=4,
    commission_stat="Strength",
    commission_target=6,
    advancement_stat="Intelligence",
    advancement_target=7,
    reenlistment_target=4,
    service_skills=("Streetwise", "Mechanics", "Gun Combat", "Melee Combat", "Recon", "Vehicle"),
    personal_development=("+1 Str", "+1 Dex", "+1 End", "Melee Combat", "Bribery", "Gambling"),
    specialist_skills=("Computer", "Electronics", "Bribery", "Broker", "Recon", "Vehicle"),
    advanced_education=("Computer", "Gravitics", "Jack o' Trades", "Medicine", "Advocate", "Tactics"),
    ranks=(
        RankEntry(0, "Independent", ("Streetwise",)),
        RankEntry(1, "Associate", ()),
        RankEntry(2, "Soldier", ("Gun Combat",)),
        RankEntry(3, "Lieutenant", ()),
        RankEntry(4, "Underboss", ()),
        RankEntry(5, "Consigliere", ()),
        RankEntry(6, "Boss", ()),
    ),
    cash_benefits=(1000, 5000, 5000, 5000, 10000, 20000, 50000),
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

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_rogue_career.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/rogue.py tests/test_rogue_career.py
git commit -m "feat: add Rogue career"
```

---

### Task 5: Merchant career

**Files:**
- Create: `src/cetools/engine/careers/merchant.py`
- Test: `tests/test_merchant_career.py`

**Interfaces:**
- Produces: `MERCHANT_CAREER` importable from `cetools.engine.careers.merchant`. Full ranks 0–6; commission Intelligence 5, advancement Education 8; rank 3 bonus `Piloting`; 7 material entries with ship shares at index 4 and `Explorers' Society` at index 6; material slot 2 is `+1 Edu`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_merchant_career.py`:

```python
from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.merchant import MERCHANT_CAREER


def test_merchant_scalar_fields() -> None:
    assert MERCHANT_CAREER.name == "Merchant"
    assert MERCHANT_CAREER.qualification_stat == "Intelligence"
    assert MERCHANT_CAREER.qualification_target == 4
    assert MERCHANT_CAREER.survival_stat == "Intelligence"
    assert MERCHANT_CAREER.survival_target == 5
    assert MERCHANT_CAREER.commission_stat == "Intelligence"
    assert MERCHANT_CAREER.commission_target == 5
    assert MERCHANT_CAREER.advancement_stat == "Education"
    assert MERCHANT_CAREER.advancement_target == 8
    assert MERCHANT_CAREER.reenlistment_target == 4


def test_merchant_skill_tables() -> None:
    assert MERCHANT_CAREER.personal_development == (
        "+1 Str", "+1 Dex", "+1 End", "Melee Combat", "Steward", "Gambling",
    )
    assert MERCHANT_CAREER.service_skills == (
        "Comms", "Engineering", "Gun Combat", "Melee Combat", "Broker", "Vehicle",
    )
    assert MERCHANT_CAREER.specialist_skills == (
        "Carousing", "Gunnery", "Jack o' Trades", "Medicine", "Navigation", "Piloting",
    )
    assert MERCHANT_CAREER.advanced_education == (
        "Advocate", "Engineering", "Medicine", "Navigation", "Sciences", "Tactics",
    )


def test_merchant_ranks() -> None:
    assert MERCHANT_CAREER.ranks == (
        RankEntry(0, "Crewman", ("Steward",)),
        RankEntry(1, "Deck Cadet", ()),
        RankEntry(2, "Fourth Officer", ()),
        RankEntry(3, "Third Officer", ("Piloting",)),
        RankEntry(4, "Second Officer", ()),
        RankEntry(5, "First Officer", ()),
        RankEntry(6, "Captain", ()),
    )


def test_merchant_benefits() -> None:
    assert MERCHANT_CAREER.cash_benefits == (1000, 5000, 10000, 20000, 20000, 50000, 100000)
    assert MERCHANT_CAREER.material_benefits == (
        "Low Passage", "+1 Edu", "Weapon", "High Passage", "1D6 Ship Shares",
        "High Passage", "Explorers' Society",
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_merchant_career.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Create the career module**

Create `src/cetools/engine/careers/merchant.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

MERCHANT_CAREER = Career(
    name="Merchant",
    qualification_stat="Intelligence",
    qualification_target=4,
    survival_stat="Intelligence",
    survival_target=5,
    commission_stat="Intelligence",
    commission_target=5,
    advancement_stat="Education",
    advancement_target=8,
    reenlistment_target=4,
    service_skills=("Comms", "Engineering", "Gun Combat", "Melee Combat", "Broker", "Vehicle"),
    personal_development=("+1 Str", "+1 Dex", "+1 End", "Melee Combat", "Steward", "Gambling"),
    specialist_skills=("Carousing", "Gunnery", "Jack o' Trades", "Medicine", "Navigation", "Piloting"),
    advanced_education=("Advocate", "Engineering", "Medicine", "Navigation", "Sciences", "Tactics"),
    ranks=(
        RankEntry(0, "Crewman", ("Steward",)),
        RankEntry(1, "Deck Cadet", ()),
        RankEntry(2, "Fourth Officer", ()),
        RankEntry(3, "Third Officer", ("Piloting",)),
        RankEntry(4, "Second Officer", ()),
        RankEntry(5, "First Officer", ()),
        RankEntry(6, "Captain", ()),
    ),
    cash_benefits=(1000, 5000, 10000, 20000, 20000, 50000, 100000),
    material_benefits=(
        "Low Passage",
        "+1 Edu",
        "Weapon",
        "High Passage",
        "1D6 Ship Shares",
        "High Passage",
        "Explorers' Society",
    ),
)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_merchant_career.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/merchant.py tests/test_merchant_career.py
git commit -m "feat: add Merchant career"
```

---

### Task 6: Register the five careers + update README and CLI tests

**Files:**
- Modify: `src/cetools/engine/careers/registry.py` (imports + `CAREER_REGISTRY`, NOT `DRAFT_TABLE`)
- Modify: `README.md:5` (supported-careers line)
- Test: `tests/test_careers.py` (registry assertions), `tests/test_cli.py` (merchant→smuggler sentinel + both "Valid careers:" lists)

**Interfaces:**
- Consumes: `BELTER_CAREER`, `MERCENARY_CAREER`, `PIRATE_CAREER`, `ROGUE_CAREER`, `MERCHANT_CAREER` from Tasks 1–5.
- Produces: registry keys `"belter"`, `"mercenary"`, `"pirate"`, `"rogue"`, `"merchant"` resolving to those careers; none added to `DRAFT_TABLE`.

- [ ] **Step 1: Write the failing registry tests**

Append to `tests/test_careers.py`:

```python
from cetools.engine.careers.belter import BELTER_CAREER  # noqa: E402
from cetools.engine.careers.mercenary import MERCENARY_CAREER  # noqa: E402
from cetools.engine.careers.merchant import MERCHANT_CAREER  # noqa: E402
from cetools.engine.careers.pirate import PIRATE_CAREER  # noqa: E402
from cetools.engine.careers.rogue import ROGUE_CAREER  # noqa: E402


def test_registry_has_rogue_spacer_career_keys() -> None:
    for key in ("belter", "mercenary", "pirate", "rogue", "merchant"):
        assert key in CAREER_REGISTRY


def test_registry_rogue_spacer_career_values() -> None:
    assert CAREER_REGISTRY["belter"] is BELTER_CAREER
    assert CAREER_REGISTRY["mercenary"] is MERCENARY_CAREER
    assert CAREER_REGISTRY["pirate"] is PIRATE_CAREER
    assert CAREER_REGISTRY["rogue"] is ROGUE_CAREER
    assert CAREER_REGISTRY["merchant"] is MERCHANT_CAREER


def test_rogue_spacer_careers_not_draftable() -> None:
    for key in ("belter", "mercenary", "pirate", "rogue", "merchant"):
        assert key not in DRAFT_TABLE
    assert len(DRAFT_TABLE) == 6
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_careers.py -k "rogue_spacer" -v --no-cov`
Expected: FAIL — imports resolve (Tasks 1–5 created the modules) but the registry keys are absent.

- [ ] **Step 3: Register the careers**

Replace the contents of `src/cetools/engine/careers/registry.py` with:

```python
from cetools.engine.careers.aerospace import AEROSPACE_CAREER
from cetools.engine.careers.agent import AGENT_CAREER
from cetools.engine.careers.athlete import ATHLETE_CAREER
from cetools.engine.careers.barbarian import BARBARIAN_CAREER
from cetools.engine.careers.base import Career
from cetools.engine.careers.belter import BELTER_CAREER
from cetools.engine.careers.bureaucrat import BUREAUCRAT_CAREER
from cetools.engine.careers.colonist import COLONIST_CAREER
from cetools.engine.careers.diplomat import DIPLOMAT_CAREER
from cetools.engine.careers.drifter import DRIFTER_CAREER
from cetools.engine.careers.entertainer import ENTERTAINER_CAREER
from cetools.engine.careers.hunter import HUNTER_CAREER
from cetools.engine.careers.marine import MARINE_CAREER
from cetools.engine.careers.maritime import MARITIME_CAREER
from cetools.engine.careers.mercenary import MERCENARY_CAREER
from cetools.engine.careers.merchant import MERCHANT_CAREER
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.noble import NOBLE_CAREER
from cetools.engine.careers.pirate import PIRATE_CAREER
from cetools.engine.careers.rogue import ROGUE_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER
from cetools.engine.careers.surface import SURFACE_CAREER

CAREER_REGISTRY: dict[str, Career] = {
    "aerospace system defense": AEROSPACE_CAREER,
    "agent": AGENT_CAREER,
    "athlete": ATHLETE_CAREER,
    "barbarian": BARBARIAN_CAREER,
    "belter": BELTER_CAREER,
    "bureaucrat": BUREAUCRAT_CAREER,
    "colonist": COLONIST_CAREER,
    "diplomat": DIPLOMAT_CAREER,
    "drifter": DRIFTER_CAREER,
    "entertainer": ENTERTAINER_CAREER,
    "hunter": HUNTER_CAREER,
    "marine": MARINE_CAREER,
    "maritime system defense": MARITIME_CAREER,
    "mercenary": MERCENARY_CAREER,
    "merchant": MERCHANT_CAREER,
    "navy": NAVY_CAREER,
    "noble": NOBLE_CAREER,
    "pirate": PIRATE_CAREER,
    "rogue": ROGUE_CAREER,
    "scout": SCOUT_CAREER,
    "surface system defense": SURFACE_CAREER,
}

DRAFT_TABLE: tuple[str, ...] = (
    "aerospace system defense",  # 1
    "marine",  # 2
    "maritime system defense",  # 3
    "navy",  # 4
    "scout",  # 5
    "surface system defense",  # 6
)
```

- [ ] **Step 4: Swap the `merchant` sentinel to `smuggler` and update both CLI lists**

`merchant` is now a real career, so all three `merchant`/`Merchant` uses in `tests/test_cli.py` must change to `smuggler`/`Smuggler`, and both "Valid careers:" expectations grow to 21 entries. Make these four edits:

1. In `test_career_unknown_exits_1` (currently line 191): change `"--career", "merchant"` to `"--career", "smuggler"`.

2. In `test_career_unknown_stderr_message_exact` (currently lines 197-204): change `"--career", "merchant"` to `"--career", "smuggler"`, and replace the `expected` string with:

```python
    expected = (
        "Unknown career 'smuggler'. Valid careers: Aerospace System Defense, "
        "Agent, Athlete, Barbarian, Belter, Bureaucrat, Colonist, Diplomat, "
        "Drifter, Entertainer, Hunter, Marine, Maritime System Defense, "
        "Mercenary, Merchant, Navy, Noble, Pirate, Rogue, Scout, "
        "Surface System Defense"
    )
```

3. In `test_career_unknown_original_value_in_message` (currently lines 207-209): change `"--career", "Merchant"` to `"--career", "Smuggler"` and the assertion to `assert "Smuggler" in result.stderr`.

4. In `test_career_no_match_valid_careers_format` (currently lines 400-408, the `xyzzy` case): replace the `expected` string with:

```python
    expected = (
        "Unknown career 'xyzzy'. Valid careers: Aerospace System Defense, "
        "Agent, Athlete, Barbarian, Belter, Bureaucrat, Colonist, Diplomat, "
        "Drifter, Entertainer, Hunter, Marine, Maritime System Defense, "
        "Mercenary, Merchant, Navy, Noble, Pirate, Rogue, Scout, "
        "Surface System Defense"
    )
```

Both `smuggler` and `xyzzy` must remain unknown careers with no `difflib` close match (verified in Step 6). If either now yields a "Did you mean" suggestion, STOP and report it — do not rewrite the test to expect a suggestion.

- [ ] **Step 5: Update the README supported-careers line**

In `README.md`, replace line 5 (the current 16-career "Supported careers:" line ending with the `... selectable with \`--career\` only.` clarification) with the same sentence listing all twenty-one careers alphabetically:

```markdown
Supported careers: **Aerospace System Defense**, **Agent**, **Athlete**, **Barbarian**, **Belter**, **Bureaucrat**, **Colonist**, **Diplomat**, **Drifter**, **Entertainer**, **Hunter**, **Marine**, **Maritime System Defense**, **Mercenary**, **Merchant**, **Navy**, **Noble**, **Pirate**, **Rogue**, **Scout**, **Surface System Defense**. Omit `--career` to have one of the six services (Aerospace System Defense, Marine, Maritime System Defense, Navy, Scout, Surface System Defense) drafted at random; the other careers are selectable with `--career` only.
```

- [ ] **Step 6: Run the full suite with coverage**

Run: `uv run pytest`
Expected: PASS, coverage ≥85%. Confirms the registry, both updated CLI assertions, and that `smuggler`/`xyzzy` still hit the "Valid careers:" list path (no `difflib` "Did you mean" suggestion). If a CLI test reports a suggestion for `smuggler` or `xyzzy`, stop and report it (see Step 4 note).

- [ ] **Step 7: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/registry.py README.md tests/test_careers.py tests/test_cli.py
git commit -m "feat: register Rogue & spacer careers and document them"
```

---

## Self-Review

**Spec coverage:**
- Belter / Mercenary / Pirate / Rogue / Merchant data (all fields verbatim) → Tasks 1-5. ✓
- Belter no-commission/advancement + single empty-bonus rank + 6 material entries → Task 1. ✓
- Full ranks 0–6 for the other four; `Pilot`→`Piloting` rank bonuses (Pirate rank 2, Merchant rank 3) → Tasks 3, 5. ✓
- Ship-shares sentinels (Belter idx4, Mercenary/Pirate idx6, Merchant idx4) + Merchant `Explorers' Society` idx6 + Merchant slot-2 `+1 Edu` → Tasks 1-3, 5 benefit assertions. ✓
- Belter ship-shares generator test → Task 1. ✓
- Registry-only (not draftable) → Task 6 + `test_rogue_spacer_careers_not_draftable`. ✓
- `merchant`→`smuggler` sentinel swap (all three uses) + both 21-entry CLI lists + README → Task 6, Steps 4-5. ✓

**Placeholder scan:** No TBD/TODO/"handle edge cases". Every code and test step contains complete content. The Step-4/6 difflib note is a verification instruction, not deferred work.

**Type consistency:** Career constant names (`BELTER_CAREER`, `MERCENARY_CAREER`, `PIRATE_CAREER`, `ROGUE_CAREER`, `MERCHANT_CAREER`) are produced in Tasks 1-5 and consumed verbatim in Task 6 imports/registry and the Belter generator test. Registry keys (`"belter"`, `"mercenary"`, `"pirate"`, `"rogue"`, `"merchant"`) match between Task 6's literal and its tests. Ship-shares assertions reuse the Batch 1 field `material_quantity` and display name `"Ship Shares"`. `Piloting` (not `Pilot`) is used consistently in the rank literals and tests.
