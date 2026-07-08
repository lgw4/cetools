# Frontier Careers (Batch 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the five Frontier careers (Athlete, Barbarian, Colonist, Hunter, Drifter) as data modules, exercising the already-built optional-qualification (Drifter) and ship-shares (Hunter) mechanics.

**Architecture:** Pure data. Each career is a frozen `Career` literal in its own module with a mirrored per-career test file, following the existing pattern. Three targeted generator tests prove the reused mechanics (Drifter no-qualification end-to-end, a zero-value cash benefit, Hunter ship shares). A final task registers all five (registry-only, not draftable) and updates the README and CLI tests. No engine, model, or formatter changes.

**Tech Stack:** Python 3.10+, frozen `@dataclass`, pytest (coverage gate ≥85% on `src/cetools`), Black, flake8, isort.

## Global Constraints

- Package source under `src/cetools/`; tests mirror it under `tests/`.
- Run `uv run black . && uv run flake8 src tests && uv run pytest` before committing; the suite enforces ≥85% coverage on `src/cetools`. Single-file runs use `--no-cov`.
- Conventional Commits for every commit.
- Frozen-dataclass style with `str | None` / `int | None` unions — no `typing.Optional`.
- All skill names, benefit strings, rank titles, and numbers are transcribed **verbatim** from `docs/superpowers/specs/2026-07-08-frontier-careers-design.md`. `Explorers' Society` uses that exact plural-possessive spelling.
- The five new careers are added to `CAREER_REGISTRY` **only** — never `DRAFT_TABLE`. Selectable via `--career`, not draftable.
- `Career` field order follows the existing files: name, qualification, survival, commission, advancement, reenlistment, `service_skills`, `personal_development`, `specialist_skills`, `advanced_education`, `ranks`, `cash_benefits`, `material_benefits`.
- No-commission/advancement careers set all four `commission_*`/`advancement_*` to `None`. No-rank careers use a single `RankEntry(0, "<CareerName>", (bonus...))`. Careers with a blank SRD 7th material slot get exactly 6 material entries.
- Drifter alone has `qualification_stat=None, qualification_target=None` (both-or-neither, per the model guard added in Batch 0).

---

### Task 1: Athlete career

**Files:**
- Create: `src/cetools/engine/careers/athlete.py`
- Test: `tests/test_athlete_career.py`

**Interfaces:**
- Produces: `ATHLETE_CAREER` importable from `cetools.engine.careers.athlete`. No commission/advancement; single rank; 6 material entries.

- [ ] **Step 1: Write the failing test**

Create `tests/test_athlete_career.py`:

```python
from cetools.engine.careers.athlete import ATHLETE_CAREER
from cetools.engine.careers.base import RankEntry


def test_athlete_scalar_fields() -> None:
    assert ATHLETE_CAREER.name == "Athlete"
    assert ATHLETE_CAREER.qualification_stat == "Endurance"
    assert ATHLETE_CAREER.qualification_target == 8
    assert ATHLETE_CAREER.survival_stat == "Dexterity"
    assert ATHLETE_CAREER.survival_target == 5
    assert ATHLETE_CAREER.commission_stat is None
    assert ATHLETE_CAREER.commission_target is None
    assert ATHLETE_CAREER.advancement_stat is None
    assert ATHLETE_CAREER.advancement_target is None
    assert ATHLETE_CAREER.reenlistment_target == 6


def test_athlete_skill_tables() -> None:
    assert ATHLETE_CAREER.personal_development == (
        "+1 Dex", "+1 Int", "+1 Edu", "+1 Soc", "Carousing", "Melee Combat",
    )
    assert ATHLETE_CAREER.service_skills == (
        "Athletics", "Admin", "Carousing", "Computer", "Gambling", "Vehicle",
    )
    assert ATHLETE_CAREER.specialist_skills == (
        "Zero-G", "Athletics", "Athletics", "Computer", "Leadership", "Gambling",
    )
    assert ATHLETE_CAREER.advanced_education == (
        "Advocate", "Computer", "Liaison", "Linguistics", "Medicine", "Sciences",
    )


def test_athlete_ranks() -> None:
    assert ATHLETE_CAREER.ranks == (RankEntry(0, "Athlete", ("Athletics",)),)


def test_athlete_benefits() -> None:
    assert ATHLETE_CAREER.cash_benefits == (2000, 10000, 20000, 20000, 50000, 100000, 100000)
    assert ATHLETE_CAREER.material_benefits == (
        "Low Passage", "+1 Int", "Weapon", "High Passage", "Explorers' Society",
        "High Passage",
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_athlete_career.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'cetools.engine.careers.athlete'`.

- [ ] **Step 3: Create the career module**

Create `src/cetools/engine/careers/athlete.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

ATHLETE_CAREER = Career(
    name="Athlete",
    qualification_stat="Endurance",
    qualification_target=8,
    survival_stat="Dexterity",
    survival_target=5,
    commission_stat=None,
    commission_target=None,
    advancement_stat=None,
    advancement_target=None,
    reenlistment_target=6,
    service_skills=("Athletics", "Admin", "Carousing", "Computer", "Gambling", "Vehicle"),
    personal_development=("+1 Dex", "+1 Int", "+1 Edu", "+1 Soc", "Carousing", "Melee Combat"),
    specialist_skills=("Zero-G", "Athletics", "Athletics", "Computer", "Leadership", "Gambling"),
    advanced_education=("Advocate", "Computer", "Liaison", "Linguistics", "Medicine", "Sciences"),
    ranks=(RankEntry(0, "Athlete", ("Athletics",)),),
    cash_benefits=(2000, 10000, 20000, 20000, 50000, 100000, 100000),
    material_benefits=(
        "Low Passage",
        "+1 Int",
        "Weapon",
        "High Passage",
        "Explorers' Society",
        "High Passage",
    ),
)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_athlete_career.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/athlete.py tests/test_athlete_career.py
git commit -m "feat: add Athlete career"
```

---

### Task 2: Barbarian career (+ zero-cash-benefit test)

**Files:**
- Create: `src/cetools/engine/careers/barbarian.py`
- Test: `tests/test_barbarian_career.py`, and append one test to `tests/test_generator.py`

**Interfaces:**
- Produces: `BARBARIAN_CAREER` importable from `cetools.engine.careers.barbarian`. No commission/advancement; single rank; 6 material entries; cash table begins with `0`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_barbarian_career.py`:

```python
from cetools.engine.careers.barbarian import BARBARIAN_CAREER
from cetools.engine.careers.base import RankEntry


def test_barbarian_scalar_fields() -> None:
    assert BARBARIAN_CAREER.name == "Barbarian"
    assert BARBARIAN_CAREER.qualification_stat == "Endurance"
    assert BARBARIAN_CAREER.qualification_target == 5
    assert BARBARIAN_CAREER.survival_stat == "Strength"
    assert BARBARIAN_CAREER.survival_target == 6
    assert BARBARIAN_CAREER.commission_stat is None
    assert BARBARIAN_CAREER.commission_target is None
    assert BARBARIAN_CAREER.advancement_stat is None
    assert BARBARIAN_CAREER.advancement_target is None
    assert BARBARIAN_CAREER.reenlistment_target == 5


def test_barbarian_skill_tables() -> None:
    assert BARBARIAN_CAREER.personal_development == (
        "+1 Str", "+1 Dex", "+1 End", "+1 Int", "Athletics", "Gun Combat",
    )
    assert BARBARIAN_CAREER.service_skills == (
        "Gun Combat", "Melee Combat", "Recon", "Survival", "Animals", "Gun Combat",
    )
    assert BARBARIAN_CAREER.specialist_skills == (
        "Gun Combat", "Jack o' Trades", "Melee Combat", "Recon", "Animals", "Tactics",
    )
    assert BARBARIAN_CAREER.advanced_education == (
        "Advocate", "Linguistics", "Medicine", "Leadership", "Broker", "Tactics",
    )


def test_barbarian_ranks() -> None:
    assert BARBARIAN_CAREER.ranks == (RankEntry(0, "Barbarian", ("Melee Combat",)),)


def test_barbarian_benefits() -> None:
    assert BARBARIAN_CAREER.cash_benefits == (0, 1000, 2000, 5000, 5000, 10000, 10000)
    assert BARBARIAN_CAREER.material_benefits == (
        "Low Passage", "+1 Int", "Weapon", "Weapon", "+1 End", "Mid Passage",
    )
```

Append to `tests/test_generator.py` (a direct `_muster_out` test proving a `0` cash slot yields a valid benefit):

```python
def test_muster_out_zero_cash_benefit() -> None:
    from cetools.engine.careers.barbarian import BARBARIAN_CAREER
    from cetools.engine.models import STAT_NAMES

    characteristics = {stat: 7 for stat in STAT_NAMES}
    # rank 0, terms=1 -> 1 total roll (cash). ConstantRoller(1) with no Gambling
    # -> cash_dm=0 -> idx 0 -> cash_benefits[0] == 0.
    benefits = _muster_out(BARBARIAN_CAREER, 1, 0, {}, characteristics, ConstantRoller(1))
    cash = [b for b in benefits if b.kind == "cash"]
    assert len(cash) == 1
    assert cash[0].cash_amount == 0
```

(`_muster_out`, `ConstantRoller` are already imported in `tests/test_generator.py`.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_barbarian_career.py tests/test_generator.py::test_muster_out_zero_cash_benefit -v --no-cov`
Expected: FAIL — `ModuleNotFoundError` for `barbarian` (both the career test and the generator test import it).

- [ ] **Step 3: Create the career module**

Create `src/cetools/engine/careers/barbarian.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

BARBARIAN_CAREER = Career(
    name="Barbarian",
    qualification_stat="Endurance",
    qualification_target=5,
    survival_stat="Strength",
    survival_target=6,
    commission_stat=None,
    commission_target=None,
    advancement_stat=None,
    advancement_target=None,
    reenlistment_target=5,
    service_skills=("Gun Combat", "Melee Combat", "Recon", "Survival", "Animals", "Gun Combat"),
    personal_development=("+1 Str", "+1 Dex", "+1 End", "+1 Int", "Athletics", "Gun Combat"),
    specialist_skills=("Gun Combat", "Jack o' Trades", "Melee Combat", "Recon", "Animals", "Tactics"),
    advanced_education=("Advocate", "Linguistics", "Medicine", "Leadership", "Broker", "Tactics"),
    ranks=(RankEntry(0, "Barbarian", ("Melee Combat",)),),
    cash_benefits=(0, 1000, 2000, 5000, 5000, 10000, 10000),
    material_benefits=(
        "Low Passage",
        "+1 Int",
        "Weapon",
        "Weapon",
        "+1 End",
        "Mid Passage",
    ),
)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_barbarian_career.py tests/test_generator.py::test_muster_out_zero_cash_benefit -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/barbarian.py tests/test_barbarian_career.py tests/test_generator.py
git commit -m "feat: add Barbarian career"
```

---

### Task 3: Colonist career

**Files:**
- Create: `src/cetools/engine/careers/colonist.py`
- Test: `tests/test_colonist_career.py`

**Interfaces:**
- Produces: `COLONIST_CAREER` importable from `cetools.engine.careers.colonist`. Full ranks 0–6, commission Intelligence 7, advancement Education 6, 7 material entries.

- [ ] **Step 1: Write the failing test**

Create `tests/test_colonist_career.py`:

```python
from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.colonist import COLONIST_CAREER


def test_colonist_scalar_fields() -> None:
    assert COLONIST_CAREER.name == "Colonist"
    assert COLONIST_CAREER.qualification_stat == "Endurance"
    assert COLONIST_CAREER.qualification_target == 5
    assert COLONIST_CAREER.survival_stat == "Endurance"
    assert COLONIST_CAREER.survival_target == 6
    assert COLONIST_CAREER.commission_stat == "Intelligence"
    assert COLONIST_CAREER.commission_target == 7
    assert COLONIST_CAREER.advancement_stat == "Education"
    assert COLONIST_CAREER.advancement_target == 6
    assert COLONIST_CAREER.reenlistment_target == 5


def test_colonist_skill_tables() -> None:
    assert COLONIST_CAREER.personal_development == (
        "+1 Str", "+1 Dex", "+1 End", "+1 Int", "Athletics", "Gun Combat",
    )
    assert COLONIST_CAREER.service_skills == (
        "Mechanics", "Gun Combat", "Animals", "Electronics", "Survival", "Vehicle",
    )
    assert COLONIST_CAREER.specialist_skills == (
        "Athletics", "Carousing", "Jack o' Trades", "Engineering", "Animals", "Vehicle",
    )
    assert COLONIST_CAREER.advanced_education == (
        "Advocate", "Linguistics", "Medicine", "Liaison", "Admin", "Animals",
    )


def test_colonist_ranks() -> None:
    assert COLONIST_CAREER.ranks == (
        RankEntry(0, "Citizen", ("Survival",)),
        RankEntry(1, "District Leader", ()),
        RankEntry(2, "District Delegate", ()),
        RankEntry(3, "Council Advisor", ("Liaison",)),
        RankEntry(4, "Councilor", ()),
        RankEntry(5, "Lieutenant Governor", ()),
        RankEntry(6, "Governor", ()),
    )


def test_colonist_benefits() -> None:
    assert COLONIST_CAREER.cash_benefits == (1000, 5000, 5000, 5000, 10000, 20000, 50000)
    assert COLONIST_CAREER.material_benefits == (
        "Low Passage", "+1 Int", "Weapon", "Mid Passage", "Mid Passage",
        "High Passage", "+1 Soc",
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_colonist_career.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Create the career module**

Create `src/cetools/engine/careers/colonist.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

COLONIST_CAREER = Career(
    name="Colonist",
    qualification_stat="Endurance",
    qualification_target=5,
    survival_stat="Endurance",
    survival_target=6,
    commission_stat="Intelligence",
    commission_target=7,
    advancement_stat="Education",
    advancement_target=6,
    reenlistment_target=5,
    service_skills=("Mechanics", "Gun Combat", "Animals", "Electronics", "Survival", "Vehicle"),
    personal_development=("+1 Str", "+1 Dex", "+1 End", "+1 Int", "Athletics", "Gun Combat"),
    specialist_skills=("Athletics", "Carousing", "Jack o' Trades", "Engineering", "Animals", "Vehicle"),
    advanced_education=("Advocate", "Linguistics", "Medicine", "Liaison", "Admin", "Animals"),
    ranks=(
        RankEntry(0, "Citizen", ("Survival",)),
        RankEntry(1, "District Leader", ()),
        RankEntry(2, "District Delegate", ()),
        RankEntry(3, "Council Advisor", ("Liaison",)),
        RankEntry(4, "Councilor", ()),
        RankEntry(5, "Lieutenant Governor", ()),
        RankEntry(6, "Governor", ()),
    ),
    cash_benefits=(1000, 5000, 5000, 5000, 10000, 20000, 50000),
    material_benefits=(
        "Low Passage",
        "+1 Int",
        "Weapon",
        "Mid Passage",
        "Mid Passage",
        "High Passage",
        "+1 Soc",
    ),
)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_colonist_career.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/colonist.py tests/test_colonist_career.py
git commit -m "feat: add Colonist career"
```

---

### Task 4: Hunter career (+ ship-shares test)

**Files:**
- Create: `src/cetools/engine/careers/hunter.py`
- Test: `tests/test_hunter_career.py`, and append one test to `tests/test_generator.py`

**Interfaces:**
- Produces: `HUNTER_CAREER` importable from `cetools.engine.careers.hunter`. No commission/advancement; single rank; 6 material entries with the `"1D6 Ship Shares"` sentinel at index 4.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_hunter_career.py`:

```python
from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.hunter import HUNTER_CAREER


def test_hunter_scalar_fields() -> None:
    assert HUNTER_CAREER.name == "Hunter"
    assert HUNTER_CAREER.qualification_stat == "Endurance"
    assert HUNTER_CAREER.qualification_target == 5
    assert HUNTER_CAREER.survival_stat == "Strength"
    assert HUNTER_CAREER.survival_target == 8
    assert HUNTER_CAREER.commission_stat is None
    assert HUNTER_CAREER.commission_target is None
    assert HUNTER_CAREER.advancement_stat is None
    assert HUNTER_CAREER.advancement_target is None
    assert HUNTER_CAREER.reenlistment_target == 6


def test_hunter_skill_tables() -> None:
    assert HUNTER_CAREER.personal_development == (
        "+1 Str", "+1 Dex", "+1 End", "+1 Int", "Athletics", "Gun Combat",
    )
    assert HUNTER_CAREER.service_skills == (
        "Mechanics", "Gun Combat", "Melee Combat", "Recon", "Survival", "Vehicle",
    )
    assert HUNTER_CAREER.specialist_skills == (
        "Admin", "Comms", "Electronics", "Recon", "Animals", "Vehicle",
    )
    assert HUNTER_CAREER.advanced_education == (
        "Advocate", "Linguistics", "Medicine", "Liaison", "Animals", "Animals",
    )


def test_hunter_ranks() -> None:
    assert HUNTER_CAREER.ranks == (RankEntry(0, "Hunter", ("Survival",)),)


def test_hunter_benefits() -> None:
    assert HUNTER_CAREER.cash_benefits == (1000, 5000, 10000, 20000, 20000, 50000, 100000)
    assert HUNTER_CAREER.material_benefits == (
        "Low Passage", "+1 Int", "Weapon", "High Passage", "1D6 Ship Shares",
        "High Passage",
    )
```

Append to `tests/test_generator.py`:

```python
def test_muster_out_hunter_ship_shares() -> None:
    from cetools.engine.careers.hunter import HUNTER_CAREER
    from cetools.engine.models import STAT_NAMES

    characteristics = {stat: 7 for stat in STAT_NAMES}
    # rank 0 -> material_dm=0; terms=4 -> 4 total rolls (3 cash cap, 1 material).
    # Cash rolls 1,1,1; material-select roll 5 -> idx 4 -> "1D6 Ship Shares";
    # quantity roll 3.
    roller = SequenceRoller([1, 1, 1, 5, 3])
    benefits = _muster_out(HUNTER_CAREER, 4, 0, {}, characteristics, roller)
    material = [b for b in benefits if b.kind == "material"]
    assert len(material) == 1
    assert material[0].material_name == "Ship Shares"
    assert material[0].material_quantity == 3
```

(`_muster_out`, `SequenceRoller` are already imported in `tests/test_generator.py`.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_hunter_career.py tests/test_generator.py::test_muster_out_hunter_ship_shares -v --no-cov`
Expected: FAIL — `ModuleNotFoundError` for `hunter`.

- [ ] **Step 3: Create the career module**

Create `src/cetools/engine/careers/hunter.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

HUNTER_CAREER = Career(
    name="Hunter",
    qualification_stat="Endurance",
    qualification_target=5,
    survival_stat="Strength",
    survival_target=8,
    commission_stat=None,
    commission_target=None,
    advancement_stat=None,
    advancement_target=None,
    reenlistment_target=6,
    service_skills=("Mechanics", "Gun Combat", "Melee Combat", "Recon", "Survival", "Vehicle"),
    personal_development=("+1 Str", "+1 Dex", "+1 End", "+1 Int", "Athletics", "Gun Combat"),
    specialist_skills=("Admin", "Comms", "Electronics", "Recon", "Animals", "Vehicle"),
    advanced_education=("Advocate", "Linguistics", "Medicine", "Liaison", "Animals", "Animals"),
    ranks=(RankEntry(0, "Hunter", ("Survival",)),),
    cash_benefits=(1000, 5000, 10000, 20000, 20000, 50000, 100000),
    material_benefits=(
        "Low Passage",
        "+1 Int",
        "Weapon",
        "High Passage",
        "1D6 Ship Shares",
        "High Passage",
    ),
)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_hunter_career.py tests/test_generator.py::test_muster_out_hunter_ship_shares -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/hunter.py tests/test_hunter_career.py tests/test_generator.py
git commit -m "feat: add Hunter career"
```

---

### Task 5: Drifter career (+ no-qualification end-to-end test)

**Files:**
- Create: `src/cetools/engine/careers/drifter.py`
- Test: `tests/test_drifter_career.py`, and append one test to `tests/test_generator.py`

**Interfaces:**
- Produces: `DRIFTER_CAREER` importable from `cetools.engine.careers.drifter`. `qualification_stat`/`qualification_target` are `None`; no commission/advancement; single rank titled `Drifter` with no bonus skill; 6 material entries; cash begins with `0`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_drifter_career.py`:

```python
from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.drifter import DRIFTER_CAREER


def test_drifter_scalar_fields() -> None:
    assert DRIFTER_CAREER.name == "Drifter"
    assert DRIFTER_CAREER.qualification_stat is None
    assert DRIFTER_CAREER.qualification_target is None
    assert DRIFTER_CAREER.survival_stat == "Endurance"
    assert DRIFTER_CAREER.survival_target == 5
    assert DRIFTER_CAREER.commission_stat is None
    assert DRIFTER_CAREER.commission_target is None
    assert DRIFTER_CAREER.advancement_stat is None
    assert DRIFTER_CAREER.advancement_target is None
    assert DRIFTER_CAREER.reenlistment_target == 5


def test_drifter_skill_tables() -> None:
    assert DRIFTER_CAREER.personal_development == (
        "+1 Str", "+1 Dex", "+1 End", "Melee Combat", "Bribery", "Gambling",
    )
    assert DRIFTER_CAREER.service_skills == (
        "Streetwise", "Mechanics", "Gun Combat", "Melee Combat", "Recon", "Vehicle",
    )
    assert DRIFTER_CAREER.specialist_skills == (
        "Electronics", "Melee Combat", "Bribery", "Streetwise", "Gambling", "Recon",
    )
    assert DRIFTER_CAREER.advanced_education == (
        "Computer", "Engineering", "Jack o' Trades", "Medicine", "Liaison", "Tactics",
    )


def test_drifter_ranks() -> None:
    assert DRIFTER_CAREER.ranks == (RankEntry(0, "Drifter", ()),)


def test_drifter_benefits() -> None:
    assert DRIFTER_CAREER.cash_benefits == (0, 1000, 2000, 5000, 5000, 10000, 10000)
    assert DRIFTER_CAREER.material_benefits == (
        "Low Passage", "+1 Int", "Weapon", "Weapon", "Mid Passage", "Mid Passage",
    )
```

Append to `tests/test_generator.py` (the Batch 0 deferred end-to-end: a no-qualification career generates via the `--career` path without looping or raising):

```python
def test_generate_career_character_drifter_no_qualification() -> None:
    from cetools.engine.careers.drifter import DRIFTER_CAREER

    result = generate_career_character(DRIFTER_CAREER, roller=SmartRoller(10, 1))
    assert isinstance(result, Character)
    assert result.career == "Drifter"
```

(`generate_career_character`, `Character`, `SmartRoller` are already imported in `tests/test_generator.py`.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_drifter_career.py tests/test_generator.py::test_generate_career_character_drifter_no_qualification -v --no-cov`
Expected: FAIL — `ModuleNotFoundError` for `drifter`.

- [ ] **Step 3: Create the career module**

Create `src/cetools/engine/careers/drifter.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

DRIFTER_CAREER = Career(
    name="Drifter",
    qualification_stat=None,
    qualification_target=None,
    survival_stat="Endurance",
    survival_target=5,
    commission_stat=None,
    commission_target=None,
    advancement_stat=None,
    advancement_target=None,
    reenlistment_target=5,
    service_skills=("Streetwise", "Mechanics", "Gun Combat", "Melee Combat", "Recon", "Vehicle"),
    personal_development=("+1 Str", "+1 Dex", "+1 End", "Melee Combat", "Bribery", "Gambling"),
    specialist_skills=("Electronics", "Melee Combat", "Bribery", "Streetwise", "Gambling", "Recon"),
    advanced_education=("Computer", "Engineering", "Jack o' Trades", "Medicine", "Liaison", "Tactics"),
    ranks=(RankEntry(0, "Drifter", ()),),
    cash_benefits=(0, 1000, 2000, 5000, 5000, 10000, 10000),
    material_benefits=(
        "Low Passage",
        "+1 Int",
        "Weapon",
        "Weapon",
        "Mid Passage",
        "Mid Passage",
    ),
)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_drifter_career.py tests/test_generator.py::test_generate_career_character_drifter_no_qualification -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/drifter.py tests/test_drifter_career.py tests/test_generator.py
git commit -m "feat: add Drifter career"
```

---

### Task 6: Register the five careers + update README and CLI tests

**Files:**
- Modify: `src/cetools/engine/careers/registry.py` (imports + `CAREER_REGISTRY`, NOT `DRAFT_TABLE`)
- Modify: `README.md:5` (supported-careers line)
- Test: `tests/test_careers.py` (registry assertions), `tests/test_cli.py` (the two hard-coded "Valid careers:" strings)

**Interfaces:**
- Consumes: `ATHLETE_CAREER`, `BARBARIAN_CAREER`, `COLONIST_CAREER`, `HUNTER_CAREER`, `DRIFTER_CAREER` from Tasks 1–5.
- Produces: registry keys `"athlete"`, `"barbarian"`, `"colonist"`, `"hunter"`, `"drifter"` resolving to those careers; none added to `DRAFT_TABLE`.

- [ ] **Step 1: Write the failing registry tests**

Append to `tests/test_careers.py`:

```python
from cetools.engine.careers.athlete import ATHLETE_CAREER  # noqa: E402
from cetools.engine.careers.barbarian import BARBARIAN_CAREER  # noqa: E402
from cetools.engine.careers.colonist import COLONIST_CAREER  # noqa: E402
from cetools.engine.careers.drifter import DRIFTER_CAREER  # noqa: E402
from cetools.engine.careers.hunter import HUNTER_CAREER  # noqa: E402


def test_registry_has_frontier_career_keys() -> None:
    for key in ("athlete", "barbarian", "colonist", "hunter", "drifter"):
        assert key in CAREER_REGISTRY


def test_registry_frontier_career_values() -> None:
    assert CAREER_REGISTRY["athlete"] is ATHLETE_CAREER
    assert CAREER_REGISTRY["barbarian"] is BARBARIAN_CAREER
    assert CAREER_REGISTRY["colonist"] is COLONIST_CAREER
    assert CAREER_REGISTRY["hunter"] is HUNTER_CAREER
    assert CAREER_REGISTRY["drifter"] is DRIFTER_CAREER


def test_frontier_careers_not_draftable() -> None:
    for key in ("athlete", "barbarian", "colonist", "hunter", "drifter"):
        assert key not in DRAFT_TABLE
    assert len(DRAFT_TABLE) == 6
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_careers.py -k "frontier" -v --no-cov`
Expected: FAIL — imports resolve (Tasks 1–5 created the modules) but the registry keys are absent.

- [ ] **Step 3: Register the careers**

Replace the contents of `src/cetools/engine/careers/registry.py` with:

```python
from cetools.engine.careers.aerospace import AEROSPACE_CAREER
from cetools.engine.careers.agent import AGENT_CAREER
from cetools.engine.careers.athlete import ATHLETE_CAREER
from cetools.engine.careers.barbarian import BARBARIAN_CAREER
from cetools.engine.careers.base import Career
from cetools.engine.careers.bureaucrat import BUREAUCRAT_CAREER
from cetools.engine.careers.colonist import COLONIST_CAREER
from cetools.engine.careers.diplomat import DIPLOMAT_CAREER
from cetools.engine.careers.drifter import DRIFTER_CAREER
from cetools.engine.careers.entertainer import ENTERTAINER_CAREER
from cetools.engine.careers.hunter import HUNTER_CAREER
from cetools.engine.careers.marine import MARINE_CAREER
from cetools.engine.careers.maritime import MARITIME_CAREER
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.noble import NOBLE_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER
from cetools.engine.careers.surface import SURFACE_CAREER

CAREER_REGISTRY: dict[str, Career] = {
    "aerospace system defense": AEROSPACE_CAREER,
    "agent": AGENT_CAREER,
    "athlete": ATHLETE_CAREER,
    "barbarian": BARBARIAN_CAREER,
    "bureaucrat": BUREAUCRAT_CAREER,
    "colonist": COLONIST_CAREER,
    "diplomat": DIPLOMAT_CAREER,
    "drifter": DRIFTER_CAREER,
    "entertainer": ENTERTAINER_CAREER,
    "hunter": HUNTER_CAREER,
    "marine": MARINE_CAREER,
    "maritime system defense": MARITIME_CAREER,
    "navy": NAVY_CAREER,
    "noble": NOBLE_CAREER,
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

- [ ] **Step 4: Update the two CLI "Valid careers:" assertions**

In `tests/test_cli.py`, the sorted careers list now has sixteen entries:
`Aerospace System Defense, Agent, Athlete, Barbarian, Bureaucrat, Colonist, Diplomat, Drifter, Entertainer, Hunter, Marine, Maritime System Defense, Navy, Noble, Scout, Surface System Defense`.

Replace the first expectation (currently lines 199-201, the `'merchant'` case):

```python
        "Unknown career 'merchant'. Valid careers: Aerospace System Defense, "
        "Agent, Athlete, Barbarian, Bureaucrat, Colonist, Diplomat, Drifter, "
        "Entertainer, Hunter, Marine, Maritime System Defense, Navy, Noble, "
        "Scout, Surface System Defense"
```

Replace the second expectation (currently lines 402-404, the `'xyzzy'` case) the same way:

```python
        "Unknown career 'xyzzy'. Valid careers: Aerospace System Defense, "
        "Agent, Athlete, Barbarian, Bureaucrat, Colonist, Diplomat, Drifter, "
        "Entertainer, Hunter, Marine, Maritime System Defense, Navy, Noble, "
        "Scout, Surface System Defense"
```

(These are implicitly-concatenated string literals that must reproduce the CLI output exactly. If either `'merchant'` or `'xyzzy'` now yields a `difflib` "Did you mean" suggestion instead of the list — verify in Step 6 — STOP and report it; do not rewrite the test to expect a suggestion.)

- [ ] **Step 5: Update the README supported-careers line**

In `README.md`, replace line 5 (the current 11-career "Supported careers:" line, which ends `... **Surface System Defense**. Omit \`--career\` to have one of the six services (Aerospace System Defense, Marine, Maritime System Defense, Navy, Scout, Surface System Defense) drafted at random; the other careers are selectable with \`--career\` only.`) with the same sentence but listing all sixteen careers alphabetically:

```markdown
Supported careers: **Aerospace System Defense**, **Agent**, **Athlete**, **Barbarian**, **Bureaucrat**, **Colonist**, **Diplomat**, **Drifter**, **Entertainer**, **Hunter**, **Marine**, **Maritime System Defense**, **Navy**, **Noble**, **Scout**, **Surface System Defense**. Omit `--career` to have one of the six services (Aerospace System Defense, Marine, Maritime System Defense, Navy, Scout, Surface System Defense) drafted at random; the other careers are selectable with `--career` only.
```

- [ ] **Step 6: Run the full suite with coverage**

Run: `uv run pytest`
Expected: PASS, coverage ≥85%. Confirms the registry, both updated CLI assertions, and the `merchant`/`xyzzy` list-path behavior all agree. If a CLI test reports a "Did you mean" suggestion for `merchant` or `xyzzy`, stop and report it (see Step 4 note).

- [ ] **Step 7: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/registry.py README.md tests/test_careers.py tests/test_cli.py
git commit -m "feat: register Frontier careers and document them"
```

---

## Self-Review

**Spec coverage:**
- Athlete / Barbarian / Colonist / Hunter / Drifter data (all fields verbatim) → Tasks 1-5. ✓
- No-commission/advancement careers (Athlete, Barbarian, Hunter, Drifter) `None` pattern; Colonist full ranks → Tasks 1, 2, 4, 5 / Task 3. ✓
- No-rank single `RankEntry(0, "<name>", ...)`; Drifter title `Drifter`, empty bonus → Tasks 1, 2, 4, 5. ✓
- 6 material entries where SRD 7th slot is blank; Colonist 7 entries → per-task benefit assertions. ✓
- Drifter `None` qualification + end-to-end `generate_career_character` → Task 5. ✓
- Zero cash benefit valid → Task 2 generator test. ✓
- Hunter `1D6 Ship Shares` rolls a quantity → Task 4 generator test. ✓
- Registry-only (not draftable) → Task 6 + `test_frontier_careers_not_draftable`. ✓
- README + CLI 16-entry list → Task 6, Steps 4-5. ✓

**Placeholder scan:** No TBD/TODO/"handle edge cases". Every code and test step contains complete content. The Step-4/6 difflib note is a verification instruction, not deferred work.

**Type consistency:** Career constant names (`ATHLETE_CAREER`, `BARBARIAN_CAREER`, `COLONIST_CAREER`, `HUNTER_CAREER`, `DRIFTER_CAREER`) are produced in Tasks 1-5 and consumed verbatim in Task 6 imports/registry and in the generator tests. Registry keys (`"athlete"`, `"barbarian"`, `"colonist"`, `"hunter"`, `"drifter"`) match between Task 6's literal and its tests. Ship-shares assertions reuse the Batch 1 field `material_quantity` and display name `"Ship Shares"`. Drifter's `None`/`None` qualification matches the Batch 0 both-or-neither guard.
