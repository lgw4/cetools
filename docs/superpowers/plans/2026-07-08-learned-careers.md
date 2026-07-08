# Learned Careers (Batch 4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the final three non-draft SRD careers — Physician, Scientist, Technician — completing all 24 careers, and generalize the muster-out once-only-benefit dedup to cover Research Vessel and Courier Vessel.

**Architecture:** Careers are data-driven frozen `Career` instances in `src/cetools/engine/careers/<name>.py`, registered in `registry.py`, each with a per-career test file. One small engine change generalizes `generator.py`'s hard-coded single once-only benefit into a frozenset. No model or formatter changes.

**Tech Stack:** Python 3, `uv`, pytest (with coverage gate), Black, flake8, isort, Typer (CLI).

## Global Constraints

- **Commits:** Conventional Commits (`feat:`, `docs:`, `test:`, etc.).
- **Formatting/lint:** `uv run black .`, `uv run isort .`, and `uv run flake8 src tests` must pass.
- **Coverage:** `uv run pytest` enforces ≥85% coverage on `src/cetools`.
- **Career.name:** drops any parenthetical SRD subtitle. Registry keys are the lowercased name (`"physician"`, `"scientist"`, `"technician"`).
- **Data fidelity:** stat strings are full names (`"Education"`, `"Intelligence"`, `"Dexterity"`); skill strings match existing conventions verbatim (`"Sciences"`, `"Jack o' Trades"`, `"Gun Combat"`, etc.).
- **Rank-title normalization:** the two abbreviated Physician titles are expanded — `Attending Phys.` → `Attending Physician`, `Hospital Admin.` → `Hospital Administrator`.
- **Skill tables** have exactly 6 entries; **cash/material tables** exactly 7 entries here (all three careers have full tables); **ranks** are consecutive from 0.
- Work happens on branch `feat/learned-careers` (already created and checked out).

---

### Task 1: Physician career

**Files:**
- Create: `src/cetools/engine/careers/physician.py`
- Test: `tests/test_physician_career.py`

**Interfaces:**
- Consumes: `Career`, `RankEntry` from `cetools.engine.careers.base`.
- Produces: `PHYSICIAN_CAREER: Career` in `cetools.engine.careers.physician`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_physician_career.py`:

```python
from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.physician import PHYSICIAN_CAREER


def test_physician_scalar_fields() -> None:
    assert PHYSICIAN_CAREER.name == "Physician"
    assert PHYSICIAN_CAREER.qualification_stat == "Education"
    assert PHYSICIAN_CAREER.qualification_target == 6
    assert PHYSICIAN_CAREER.survival_stat == "Intelligence"
    assert PHYSICIAN_CAREER.survival_target == 4
    assert PHYSICIAN_CAREER.commission_stat == "Intelligence"
    assert PHYSICIAN_CAREER.commission_target == 5
    assert PHYSICIAN_CAREER.advancement_stat == "Education"
    assert PHYSICIAN_CAREER.advancement_target == 8
    assert PHYSICIAN_CAREER.reenlistment_target == 5


def test_physician_skill_tables() -> None:
    assert PHYSICIAN_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "+1 Int",
        "+1 Edu",
        "Gun Combat",
    )
    assert PHYSICIAN_CAREER.service_skills == (
        "Admin",
        "Computer",
        "Mechanics",
        "Medicine",
        "Leadership",
        "Sciences",
    )
    assert PHYSICIAN_CAREER.specialist_skills == (
        "Computer",
        "Carousing",
        "Electronics",
        "Medicine",
        "Medicine",
        "Sciences",
    )
    assert PHYSICIAN_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Jack o' Trades",
        "Linguistics",
        "Medicine",
        "Sciences",
    )


def test_physician_ranks() -> None:
    assert PHYSICIAN_CAREER.ranks == (
        RankEntry(0, "Intern", ("Medicine",)),
        RankEntry(1, "Resident", ()),
        RankEntry(2, "Senior Resident", ()),
        RankEntry(3, "Chief Resident", ()),
        RankEntry(4, "Attending Physician", ("Admin",)),
        RankEntry(5, "Service Chief", ()),
        RankEntry(6, "Hospital Administrator", ()),
    )


def test_physician_benefits() -> None:
    assert PHYSICIAN_CAREER.cash_benefits == (2000, 10000, 20000, 20000, 50000, 100000, 100000)
    assert PHYSICIAN_CAREER.material_benefits == (
        "Low Passage",
        "+1 Edu",
        "+1 Int",
        "High Passage",
        "Explorers' Society",
        "High Passage",
        "+1 Soc",
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_physician_career.py --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'cetools.engine.careers.physician'`

- [ ] **Step 3: Write minimal implementation**

Create `src/cetools/engine/careers/physician.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

PHYSICIAN_CAREER = Career(
    name="Physician",
    qualification_stat="Education",
    qualification_target=6,
    survival_stat="Intelligence",
    survival_target=4,
    commission_stat="Intelligence",
    commission_target=5,
    advancement_stat="Education",
    advancement_target=8,
    reenlistment_target=5,
    service_skills=("Admin", "Computer", "Mechanics", "Medicine", "Leadership", "Sciences"),
    personal_development=("+1 Str", "+1 Dex", "+1 End", "+1 Int", "+1 Edu", "Gun Combat"),
    specialist_skills=(
        "Computer",
        "Carousing",
        "Electronics",
        "Medicine",
        "Medicine",
        "Sciences",
    ),
    advanced_education=(
        "Advocate",
        "Computer",
        "Jack o' Trades",
        "Linguistics",
        "Medicine",
        "Sciences",
    ),
    ranks=(
        RankEntry(0, "Intern", ("Medicine",)),
        RankEntry(1, "Resident", ()),
        RankEntry(2, "Senior Resident", ()),
        RankEntry(3, "Chief Resident", ()),
        RankEntry(4, "Attending Physician", ("Admin",)),
        RankEntry(5, "Service Chief", ()),
        RankEntry(6, "Hospital Administrator", ()),
    ),
    cash_benefits=(2000, 10000, 20000, 20000, 50000, 100000, 100000),
    material_benefits=(
        "Low Passage",
        "+1 Edu",
        "+1 Int",
        "High Passage",
        "Explorers' Society",
        "High Passage",
        "+1 Soc",
    ),
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_physician_career.py --no-cov`
Expected: PASS (4 passed)

- [ ] **Step 5: Format and commit**

```bash
uv run black src/cetools/engine/careers/physician.py tests/test_physician_career.py
git add src/cetools/engine/careers/physician.py tests/test_physician_career.py
git commit -m "feat: add Physician career"
```

---

### Task 2: Scientist career

**Files:**
- Create: `src/cetools/engine/careers/scientist.py`
- Test: `tests/test_scientist_career.py`

**Interfaces:**
- Consumes: `Career`, `RankEntry` from `cetools.engine.careers.base`.
- Produces: `SCIENTIST_CAREER: Career` in `cetools.engine.careers.scientist`. Its `material_benefits[6]` is `"Research Vessel"` (relied on by Task 5's regression test).

- [ ] **Step 1: Write the failing test**

Create `tests/test_scientist_career.py`:

```python
from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.scientist import SCIENTIST_CAREER


def test_scientist_scalar_fields() -> None:
    assert SCIENTIST_CAREER.name == "Scientist"
    assert SCIENTIST_CAREER.qualification_stat == "Education"
    assert SCIENTIST_CAREER.qualification_target == 6
    assert SCIENTIST_CAREER.survival_stat == "Education"
    assert SCIENTIST_CAREER.survival_target == 5
    assert SCIENTIST_CAREER.commission_stat == "Intelligence"
    assert SCIENTIST_CAREER.commission_target == 7
    assert SCIENTIST_CAREER.advancement_stat == "Intelligence"
    assert SCIENTIST_CAREER.advancement_target == 6
    assert SCIENTIST_CAREER.reenlistment_target == 5


def test_scientist_skill_tables() -> None:
    assert SCIENTIST_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "+1 Int",
        "+1 Edu",
        "Gun Combat",
    )
    assert SCIENTIST_CAREER.service_skills == (
        "Admin",
        "Computer",
        "Electronics",
        "Medicine",
        "Bribery",
        "Sciences",
    )
    assert SCIENTIST_CAREER.specialist_skills == (
        "Navigation",
        "Admin",
        "Sciences",
        "Sciences",
        "Animals",
        "Vehicle",
    )
    assert SCIENTIST_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Jack o' Trades",
        "Linguistics",
        "Medicine",
        "Sciences",
    )


def test_scientist_ranks() -> None:
    assert SCIENTIST_CAREER.ranks == (
        RankEntry(0, "Instructor", ("Sciences",)),
        RankEntry(1, "Adjunct Professor", ()),
        RankEntry(2, "Research Professor", ()),
        RankEntry(3, "Assistant Professor", ("Computer",)),
        RankEntry(4, "Associate Professor", ()),
        RankEntry(5, "Professor", ()),
        RankEntry(6, "Distinguished Professor", ()),
    )


def test_scientist_benefits() -> None:
    assert SCIENTIST_CAREER.cash_benefits == (1000, 5000, 10000, 10000, 20000, 50000, 50000)
    assert SCIENTIST_CAREER.material_benefits == (
        "Low Passage",
        "+1 Edu",
        "+1 Int",
        "Mid Passage",
        "+1 Soc",
        "High Passage",
        "Research Vessel",
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_scientist_career.py --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'cetools.engine.careers.scientist'`

- [ ] **Step 3: Write minimal implementation**

Create `src/cetools/engine/careers/scientist.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

SCIENTIST_CAREER = Career(
    name="Scientist",
    qualification_stat="Education",
    qualification_target=6,
    survival_stat="Education",
    survival_target=5,
    commission_stat="Intelligence",
    commission_target=7,
    advancement_stat="Intelligence",
    advancement_target=6,
    reenlistment_target=5,
    service_skills=("Admin", "Computer", "Electronics", "Medicine", "Bribery", "Sciences"),
    personal_development=("+1 Str", "+1 Dex", "+1 End", "+1 Int", "+1 Edu", "Gun Combat"),
    specialist_skills=("Navigation", "Admin", "Sciences", "Sciences", "Animals", "Vehicle"),
    advanced_education=(
        "Advocate",
        "Computer",
        "Jack o' Trades",
        "Linguistics",
        "Medicine",
        "Sciences",
    ),
    ranks=(
        RankEntry(0, "Instructor", ("Sciences",)),
        RankEntry(1, "Adjunct Professor", ()),
        RankEntry(2, "Research Professor", ()),
        RankEntry(3, "Assistant Professor", ("Computer",)),
        RankEntry(4, "Associate Professor", ()),
        RankEntry(5, "Professor", ()),
        RankEntry(6, "Distinguished Professor", ()),
    ),
    cash_benefits=(1000, 5000, 10000, 10000, 20000, 50000, 50000),
    material_benefits=(
        "Low Passage",
        "+1 Edu",
        "+1 Int",
        "Mid Passage",
        "+1 Soc",
        "High Passage",
        "Research Vessel",
    ),
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_scientist_career.py --no-cov`
Expected: PASS (4 passed)

- [ ] **Step 5: Format and commit**

```bash
uv run black src/cetools/engine/careers/scientist.py tests/test_scientist_career.py
git add src/cetools/engine/careers/scientist.py tests/test_scientist_career.py
git commit -m "feat: add Scientist career"
```

---

### Task 3: Technician career

**Files:**
- Create: `src/cetools/engine/careers/technician.py`
- Test: `tests/test_technician_career.py`

**Interfaces:**
- Consumes: `Career`, `RankEntry` from `cetools.engine.careers.base`.
- Produces: `TECHNICIAN_CAREER: Career` in `cetools.engine.careers.technician`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_technician_career.py`:

```python
from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.technician import TECHNICIAN_CAREER


def test_technician_scalar_fields() -> None:
    assert TECHNICIAN_CAREER.name == "Technician"
    assert TECHNICIAN_CAREER.qualification_stat == "Education"
    assert TECHNICIAN_CAREER.qualification_target == 6
    assert TECHNICIAN_CAREER.survival_stat == "Dexterity"
    assert TECHNICIAN_CAREER.survival_target == 4
    assert TECHNICIAN_CAREER.commission_stat == "Education"
    assert TECHNICIAN_CAREER.commission_target == 5
    assert TECHNICIAN_CAREER.advancement_stat == "Intelligence"
    assert TECHNICIAN_CAREER.advancement_target == 8
    assert TECHNICIAN_CAREER.reenlistment_target == 5


def test_technician_skill_tables() -> None:
    assert TECHNICIAN_CAREER.personal_development == (
        "+1 Str",
        "+1 Dex",
        "+1 End",
        "+1 Int",
        "+1 Edu",
        "Gun Combat",
    )
    assert TECHNICIAN_CAREER.service_skills == (
        "Admin",
        "Computer",
        "Mechanics",
        "Medicine",
        "Electronics",
        "Sciences",
    )
    assert TECHNICIAN_CAREER.specialist_skills == (
        "Computer",
        "Electronics",
        "Gravitics",
        "Linguistics",
        "Engineering",
        "Animals",
    )
    assert TECHNICIAN_CAREER.advanced_education == (
        "Advocate",
        "Computer",
        "Jack o' Trades",
        "Linguistics",
        "Medicine",
        "Sciences",
    )


def test_technician_ranks() -> None:
    assert TECHNICIAN_CAREER.ranks == (
        RankEntry(0, "Technician", ("Computer",)),
        RankEntry(1, "Team Lead", ()),
        RankEntry(2, "Supervisor", ()),
        RankEntry(3, "Manager", ()),
        RankEntry(4, "Director", ("Admin",)),
        RankEntry(5, "Vice-President", ()),
        RankEntry(6, "Executive Officer", ()),
    )


def test_technician_benefits() -> None:
    assert TECHNICIAN_CAREER.cash_benefits == (1000, 5000, 10000, 10000, 20000, 50000, 50000)
    assert TECHNICIAN_CAREER.material_benefits == (
        "Low Passage",
        "+1 Edu",
        "+1 Int",
        "Mid Passage",
        "Mid Passage",
        "High Passage",
        "+1 Soc",
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_technician_career.py --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'cetools.engine.careers.technician'`

- [ ] **Step 3: Write minimal implementation**

Create `src/cetools/engine/careers/technician.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

TECHNICIAN_CAREER = Career(
    name="Technician",
    qualification_stat="Education",
    qualification_target=6,
    survival_stat="Dexterity",
    survival_target=4,
    commission_stat="Education",
    commission_target=5,
    advancement_stat="Intelligence",
    advancement_target=8,
    reenlistment_target=5,
    service_skills=("Admin", "Computer", "Mechanics", "Medicine", "Electronics", "Sciences"),
    personal_development=("+1 Str", "+1 Dex", "+1 End", "+1 Int", "+1 Edu", "Gun Combat"),
    specialist_skills=(
        "Computer",
        "Electronics",
        "Gravitics",
        "Linguistics",
        "Engineering",
        "Animals",
    ),
    advanced_education=(
        "Advocate",
        "Computer",
        "Jack o' Trades",
        "Linguistics",
        "Medicine",
        "Sciences",
    ),
    ranks=(
        RankEntry(0, "Technician", ("Computer",)),
        RankEntry(1, "Team Lead", ()),
        RankEntry(2, "Supervisor", ()),
        RankEntry(3, "Manager", ()),
        RankEntry(4, "Director", ("Admin",)),
        RankEntry(5, "Vice-President", ()),
        RankEntry(6, "Executive Officer", ()),
    ),
    cash_benefits=(1000, 5000, 10000, 10000, 20000, 50000, 50000),
    material_benefits=(
        "Low Passage",
        "+1 Edu",
        "+1 Int",
        "Mid Passage",
        "Mid Passage",
        "High Passage",
        "+1 Soc",
    ),
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_technician_career.py --no-cov`
Expected: PASS (4 passed)

- [ ] **Step 5: Format and commit**

```bash
uv run black src/cetools/engine/careers/technician.py tests/test_technician_career.py
git add src/cetools/engine/careers/technician.py tests/test_technician_career.py
git commit -m "feat: add Technician career"
```

---

### Task 4: Register the three careers and fix the CLI valid-careers list

Registering the careers immediately changes the CLI's auto-generated `_CANONICAL_CAREERS` string (it sorts `CAREER_REGISTRY.values()` by `.name`), so the two exact-string assertions in `tests/test_cli.py` must move to the new 24-entry list in the SAME task to keep the suite green.

**Files:**
- Modify: `src/cetools/engine/careers/registry.py`
- Test: `tests/test_careers.py` (add registry tests)
- Test: `tests/test_cli.py:198-205, 403-409` (update expected strings)

**Interfaces:**
- Consumes: `PHYSICIAN_CAREER`, `SCIENTIST_CAREER`, `TECHNICIAN_CAREER` (Tasks 1–3).
- Produces: registry keys `"physician"`, `"scientist"`, `"technician"` in `CAREER_REGISTRY`; `DRAFT_TABLE` unchanged (length 6).

- [ ] **Step 1: Write the failing registry test**

Append to `tests/test_careers.py`:

```python
from cetools.engine.careers.physician import PHYSICIAN_CAREER  # noqa: E402
from cetools.engine.careers.scientist import SCIENTIST_CAREER  # noqa: E402
from cetools.engine.careers.technician import TECHNICIAN_CAREER  # noqa: E402


def test_registry_has_learned_career_keys() -> None:
    for key in ("physician", "scientist", "technician"):
        assert key in CAREER_REGISTRY


def test_registry_learned_career_values() -> None:
    assert CAREER_REGISTRY["physician"] is PHYSICIAN_CAREER
    assert CAREER_REGISTRY["scientist"] is SCIENTIST_CAREER
    assert CAREER_REGISTRY["technician"] is TECHNICIAN_CAREER


def test_learned_careers_not_draftable() -> None:
    for key in ("physician", "scientist", "technician"):
        assert key not in DRAFT_TABLE
    assert len(DRAFT_TABLE) == 6


def test_registry_has_all_24_careers() -> None:
    assert len(CAREER_REGISTRY) == 24
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_careers.py::test_registry_has_learned_career_keys tests/test_careers.py::test_registry_has_all_24_careers --no-cov`
Expected: FAIL — `KeyError`/`AssertionError` (keys absent; registry has 21, not 24).

- [ ] **Step 3: Register the careers**

In `src/cetools/engine/careers/registry.py`, add three imports (alphabetical among the existing import block):

```python
from cetools.engine.careers.physician import PHYSICIAN_CAREER
```
```python
from cetools.engine.careers.scientist import SCIENTIST_CAREER
```
```python
from cetools.engine.careers.technician import TECHNICIAN_CAREER
```

Then add three entries to the `CAREER_REGISTRY` dict, in alphabetical key order:

```python
    "physician": PHYSICIAN_CAREER,
```
(place between `"noble"` and `"pirate"`)
```python
    "scientist": SCIENTIST_CAREER,
```
(place between `"rogue"` and `"scout"`)
```python
    "technician": TECHNICIAN_CAREER,
```
(place after `"surface system defense"`, at the end of the dict)

Leave `DRAFT_TABLE` untouched.

- [ ] **Step 4: Run registry tests to verify they pass**

Run: `uv run pytest tests/test_careers.py --no-cov`
Expected: PASS (all registry tests, including the new four).

- [ ] **Step 5: Update the CLI valid-careers expected strings**

Two assertions in `tests/test_cli.py` (`test_career_unknown_stderr_message_exact` near line 198, and `test_career_no_match_valid_careers_format` near line 403) hard-code the sorted career list. Replace **both** expected-string literals with the new 24-entry list. For the `smuggler` one:

```python
    expected = (
        "Unknown career 'smuggler'. Valid careers: Aerospace System Defense, "
        "Agent, Athlete, Barbarian, Belter, Bureaucrat, Colonist, Diplomat, "
        "Drifter, Entertainer, Hunter, Marine, Maritime System Defense, "
        "Mercenary, Merchant, Navy, Noble, Physician, Pirate, Rogue, "
        "Scientist, Scout, Surface System Defense, Technician"
    )
```

For the `xyzzy` one, use the identical list with the `'xyzzy'` prefix:

```python
    expected = (
        "Unknown career 'xyzzy'. Valid careers: Aerospace System Defense, "
        "Agent, Athlete, Barbarian, Belter, Bureaucrat, Colonist, Diplomat, "
        "Drifter, Entertainer, Hunter, Marine, Maritime System Defense, "
        "Mercenary, Merchant, Navy, Noble, Physician, Pirate, Rogue, "
        "Scientist, Scout, Surface System Defense, Technician"
    )
```

(New names slot in by `.name` sort: **Physician** after Noble, **Scientist** after Rogue, **Technician** last. `smuggler` remains an unknown-career value — none of the three careers is named `smuggler` — so both tests still exercise the "no close match → full list" path.)

- [ ] **Step 6: Run the CLI tests to verify they pass**

Run: `uv run pytest tests/test_cli.py --no-cov`
Expected: PASS (both updated exact-string tests pass; `smuggler`/`xyzzy` still hit the list path, not a "Did you mean" suggestion).

- [ ] **Step 7: Format and commit**

```bash
uv run isort src/cetools/engine/careers/registry.py
uv run black src/cetools/engine/careers/registry.py tests/test_careers.py tests/test_cli.py
git add src/cetools/engine/careers/registry.py tests/test_careers.py tests/test_cli.py
git commit -m "feat: register Physician, Scientist, and Technician careers"
```

---

### Task 5: Generalize the once-only-benefit dedup

Replace the single hard-coded once-only benefit with a frozenset covering all three ship/society grants, so Scientist's Research Vessel and Scout's Courier Vessel are each capped at one per muster-out (the latter is an intentional behavior change to the already-shipped Scout career).

**Files:**
- Modify: `src/cetools/engine/generator.py:59` and `src/cetools/engine/generator.py:222`
- Test: `tests/test_generator.py` (add four regression tests)

**Interfaces:**
- Consumes: `SCIENTIST_CAREER` (Task 2; `material_benefits[6] == "Research Vessel"`), `SCOUT_CAREER` (existing; `material_benefits[5] == "Courier Vessel"`, 6-entry table), `_roll_material_benefit`, `ConstantRoller`, `SequenceRoller` (all already imported in `tests/test_generator.py`).
- Produces: `_UNIQUE_MATERIAL_BENEFITS: frozenset[str]` replacing `_UNIQUE_MATERIAL_BENEFIT: str` in `generator.py`.

- [ ] **Step 1: Write the failing regression tests**

Add near the existing "Explorers' Society: reroll on repeat" block in `tests/test_generator.py`. First add the Scientist import with the other career imports at the top of the file:

```python
from cetools.engine.careers.scientist import SCIENTIST_CAREER
```

Then append the tests:

```python
# --- Research Vessel (Scientist) and Courier Vessel (Scout): once-only ---


def test_roll_material_benefit_grants_research_vessel_when_not_yet_granted() -> None:
    # SCIENTIST_CAREER.material_benefits[6] = "Research Vessel". material_dm=1, so
    # idx = clamp(6 + 1 - 1) = 6.
    name = _roll_material_benefit(SCIENTIST_CAREER, 1, ConstantRoller(6), set())
    assert name == "Research Vessel"


def test_roll_material_benefit_rerolls_research_vessel_when_already_granted() -> None:
    # First die = 6 -> "Research Vessel", already granted, so it rerolls:
    # second die = 4 -> idx 4 -> "+1 Soc".
    roller = SequenceRoller([6, 4], default=6)
    name = _roll_material_benefit(SCIENTIST_CAREER, 1, roller, {"Research Vessel"})
    assert name == "+1 Soc"


def test_roll_material_benefit_grants_courier_vessel_when_not_yet_granted() -> None:
    # SCOUT_CAREER.material_benefits has 6 entries; [5] = "Courier Vessel".
    # material_dm=1, roll 6 -> idx = clamp(6, 0, 5) = 5.
    name = _roll_material_benefit(SCOUT_CAREER, 1, ConstantRoller(6), set())
    assert name == "Courier Vessel"


def test_roll_material_benefit_rerolls_courier_vessel_when_already_granted() -> None:
    # First die = 6 -> idx 5 -> "Courier Vessel", already granted, so it rerolls:
    # second die = 3 -> idx 3 -> "Mid Passage".
    roller = SequenceRoller([6, 3], default=6)
    name = _roll_material_benefit(SCOUT_CAREER, 1, roller, {"Courier Vessel"})
    assert name == "Mid Passage"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_generator.py -k "research_vessel or courier_vessel" -v --no-cov`
Expected: FAIL — the two `rerolls_*_when_already_granted` tests fail because the current code only dedups `"Explorers' Society"`, so Research Vessel / Courier Vessel are returned again instead of rerolled. (The two `grants_*` tests may already pass.)

- [ ] **Step 3: Generalize the dedup constant and check**

In `src/cetools/engine/generator.py`, replace the constant definition (line 59):

```python
_UNIQUE_MATERIAL_BENEFIT = "Explorers' Society"
```

with:

```python
_UNIQUE_MATERIAL_BENEFITS = frozenset(
    {"Explorers' Society", "Research Vessel", "Courier Vessel"}
)
```

Then update the check inside `_roll_material_benefit` (line 222) from:

```python
        if name == _UNIQUE_MATERIAL_BENEFIT and name in granted_names:
```

to:

```python
        if name in _UNIQUE_MATERIAL_BENEFITS and name in granted_names:
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_generator.py -k "research_vessel or courier_vessel or explorers" -v --no-cov`
Expected: PASS — the four new tests pass AND the existing Explorers' Society dedup tests still pass (the frozenset still contains it). Confirm no other reference to the old name remains:

Run: `rg -n "_UNIQUE_MATERIAL_BENEFIT\b" src tests`
Expected: no matches (the old singular name is fully replaced; no test imported it by name).

- [ ] **Step 5: Format and commit**

```bash
uv run black src/cetools/engine/generator.py tests/test_generator.py
git add src/cetools/engine/generator.py tests/test_generator.py
git commit -m "feat: treat Research Vessel and Courier Vessel as once-only benefits"
```

---

### Task 6: README update and full verification

**Files:**
- Modify: `README.md:5` (supported-careers list)

**Interfaces:**
- Consumes: nothing new. Final gate for the whole batch.

- [ ] **Step 1: Update the README supported-careers list**

In `README.md`, the "Supported careers:" sentence (line 5) lists careers in bold, alphabetically. Insert the three new names in `.name` sort order:

- `**Physician**` between `**Noble**` and `**Pirate**`
- `**Scientist**` between `**Rogue**` and `**Scout**`
- `**Technician**` after `**Surface System Defense**` (end of the list)

The parenthetical clause after the list ("the other careers are selectable with `--career` only") already covers these — leave it unchanged. Do not add any of the three to the six drafted services listed in that same sentence.

- [ ] **Step 2: Run Black and flake8**

Run: `uv run black . && uv run flake8 src tests`
Expected: Black reports "All done" / files unchanged; flake8 exits 0 with no output.

- [ ] **Step 3: Run isort check**

Run: `uv run isort --check-only .`
Expected: exit 0 (no files would be reordered). If it fails, run `uv run isort .` and re-stage.

- [ ] **Step 4: Run the full test suite with coverage**

Run: `uv run pytest`
Expected: PASS — all tests green and `src/cetools` coverage ≥85% (the run fails if coverage drops below the gate).

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: list Physician, Scientist, and Technician as supported careers"
```

---

## Self-Review

**1. Spec coverage:**
- Three career modules + per-career tests → Tasks 1, 2, 3. ✓
- No engine change beyond dedup generalization → only Task 5 touches `generator.py`. ✓
- Once-only generalization (`_UNIQUE_MATERIAL_BENEFITS` frozenset with Explorers' Society + Research Vessel + Courier Vessel) → Task 5. ✓
- Scientist Research Vessel once-only test + Scout Courier Vessel regression test → Task 5. ✓
- Rank-title expansion (Attending Physician, Hospital Administrator) → Task 1 data + test. ✓
- Registry: three keys, 24 total, DRAFT_TABLE still length 6, none draftable → Task 4. ✓
- CLI "Valid careers" strings updated to 24-entry list; `smuggler` sentinel stays valid → Task 4. ✓
- README supported-careers update → Task 6. ✓
- Coverage ≥85% → Task 6 full run. ✓

**2. Placeholder scan:** No TBD/TODO/"handle edge cases"/"similar to Task N"; every code step shows complete code. ✓

**3. Type consistency:** `PHYSICIAN_CAREER`/`SCIENTIST_CAREER`/`TECHNICIAN_CAREER` names consistent across Tasks 1–4; `_UNIQUE_MATERIAL_BENEFITS` (frozenset) referenced consistently in Task 5 definition and check; `_roll_material_benefit(career, material_dm, roller, granted_names)` signature matches existing usage; Scout material index 5 / Scientist material index 6 confirmed against the career data. ✓
