# Social Careers (Batch 1) + Ship Shares Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the five Soc-based Social careers (Agent, Bureaucrat, Diplomat, Entertainer, Noble) and a ship-shares mustering-out mechanic that rolls and records a real quantity.

**Architecture:** Ship shares first: add a nullable `material_quantity` to the `Benefit` dataclass, roll 1D6 in `_muster_out` when the ship-shares slot is drawn, and sum quantities in the formatter. Then each career is a frozen `Career` data literal in its own module with a mirrored test file, following the existing pattern. A final task registers all five (registry-only, not draftable) and updates the README and CLI tests.

**Tech Stack:** Python 3.10+, frozen `@dataclass`, pytest (coverage gate ≥85% on `src/cetools`), Black, flake8, isort.

## Global Constraints

- Package source under `src/cetools/`; tests mirror it under `tests/`.
- Run `uv run black . && uv run flake8 src tests && uv run pytest` before committing; the suite enforces ≥85% coverage on `src/cetools`. Single-file runs use `--no-cov`.
- Conventional Commits for every commit.
- Frozen-dataclass style with `str | None` / `int | None` unions — no `typing.Optional`.
- All skill names, benefit strings, rank titles, and numbers are transcribed **verbatim** from `docs/superpowers/specs/2026-07-08-social-careers-design.md`. `Explorers' Society` uses that exact plural-possessive spelling.
- The five new careers are added to `CAREER_REGISTRY` **only** — never to `DRAFT_TABLE`. They are selectable via `--career` but not draftable.
- Ship shares: the career table sentinel is the literal string `"1D6 Ship Shares"`; the recorded/displayed benefit name is `"Ship Shares"`; the quantity lives in `Benefit.material_quantity`. No pluralization (`"1 Ship Shares"` is correct output).
- Career field order in each `Career(...)` literal follows the existing files (`src/cetools/engine/careers/surface.py`): name, qualification, survival, commission, advancement, reenlistment, `service_skills`, `personal_development`, `specialist_skills`, `advanced_education`, `ranks`, `cash_benefits`, `material_benefits`.

---

### Task 1: Ship-shares mechanic — model field + generator roll

**Files:**
- Modify: `src/cetools/engine/models.py:51-55` (`Benefit` dataclass)
- Modify: `src/cetools/engine/generator.py:59` (add constant) and `src/cetools/engine/generator.py:184-195` (`_muster_out` loop body)
- Test: `tests/test_models.py`, `tests/test_generator.py`

**Interfaces:**
- Produces: `Benefit.material_quantity: int | None = None` (defaults `None` for all existing benefits). `_muster_out` records a ship-shares draw as `Benefit(kind="material", material_name="Ship Shares", material_quantity=<1d6>)`; the module constant `_SHIP_SHARES_BENEFIT = "1D6 Ship Shares"` names the career-table sentinel. Ship shares mutate neither characteristics nor skills.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_models.py`:

```python
def test_benefit_material_quantity_defaults_none() -> None:
    b = Benefit(kind="material", material_name="Weapon")
    assert b.material_quantity is None


def test_benefit_carries_material_quantity() -> None:
    b = Benefit(kind="material", material_name="Ship Shares", material_quantity=4)
    assert b.material_quantity == 4
```

(Confirm `Benefit` is imported at the top of `tests/test_models.py`; add `from cetools.engine.models import Benefit` if it is not already present.)

Append to `tests/test_generator.py`:

```python
def test_muster_out_ship_shares_rolls_quantity() -> None:
    import dataclasses

    from cetools.engine.models import STAT_NAMES

    ship_career = dataclasses.replace(
        NAVY_CAREER,
        material_benefits=(
            "Low Passage",
            "+1 Int",
            "Weapon",
            "Mid Passage",
            "+1 Soc",
            "High Passage",
            "1D6 Ship Shares",
        ),
    )
    characteristics = {stat: 7 for stat in STAT_NAMES}
    # rank 5 -> material_dm=1 and +2 bonus muster rolls; terms=2 -> 4 total rolls
    # (3 cash cap, then 1 material). Cash rolls 1,1,1; material-select roll 6 ->
    # idx 6 -> "1D6 Ship Shares"; quantity roll 3.
    roller = SequenceRoller([1, 1, 1, 6, 3])
    benefits = _muster_out(ship_career, 2, 5, {}, characteristics, roller)
    material = [b for b in benefits if b.kind == "material"]
    assert len(material) == 1
    assert material[0].material_name == "Ship Shares"
    assert material[0].material_quantity == 3
    # ship shares do not touch characteristics
    assert all(value == 7 for value in characteristics.values())
```

(`NAVY_CAREER`, `_muster_out`, and `SequenceRoller` are already imported in `tests/test_generator.py`.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_models.py::test_benefit_carries_material_quantity tests/test_generator.py::test_muster_out_ship_shares_rolls_quantity -v --no-cov`

Expected: FAIL. The model test raises `TypeError` (unexpected keyword `material_quantity`). The generator test fails because the current code records `material_name="1D6 Ship Shares"` with no quantity attribute.

- [ ] **Step 3: Add the model field**

In `src/cetools/engine/models.py`, add the field to `Benefit` (after `material_name`):

```python
@dataclass
class Benefit:
    kind: Literal["cash", "material"]
    cash_amount: int | None = None
    material_name: str | None = None
    material_quantity: int | None = None

    def __post_init__(self) -> None:
        if self.kind == "cash" and self.cash_amount is None:
            raise ValueError("Benefit: kind 'cash' requires cash_amount")
        if self.kind == "material" and self.material_name is None:
            raise ValueError("Benefit: kind 'material' requires material_name")
```

- [ ] **Step 4: Add the generator constant**

In `src/cetools/engine/generator.py`, immediately after the `_UNIQUE_MATERIAL_BENEFIT` line (currently line 59), add:

```python
_SHIP_SHARES_BENEFIT = "1D6 Ship Shares"
```

- [ ] **Step 5: Handle ship shares in `_muster_out`**

In `src/cetools/engine/generator.py`, replace the `else` branch of the muster-out loop (currently lines 191-195):

```python
        else:
            name = _roll_material_benefit(career, material_dm, roller, granted_material_names)
            if name == _SHIP_SHARES_BENEFIT:
                quantity = roller.roll(6)
                benefits.append(
                    Benefit(
                        kind="material",
                        material_name="Ship Shares",
                        material_quantity=quantity,
                    )
                )
                granted_material_names.add(name)
            else:
                _apply_material_benefit(name, characteristics, skills)
                granted_material_names.add(name)
                benefits.append(Benefit(kind="material", material_name=name))
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_models.py tests/test_generator.py -v --no-cov`

Expected: PASS (the two new tests plus all existing model/generator tests).

- [ ] **Step 7: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/models.py src/cetools/engine/generator.py tests/test_models.py tests/test_generator.py
git commit -m "feat: roll and record ship-shares benefit quantity"
```

---

### Task 2: Ship-shares formatter rendering

**Files:**
- Modify: `src/cetools/formatter.py:10-38` (`_combine_material_benefits`)
- Test: `tests/test_formatter.py`

**Interfaces:**
- Consumes: `Benefit.material_quantity` from Task 1.
- Produces: `_combine_material_benefits` renders quantity-bearing benefits as `"<summed-quantity> <name>"` (e.g. `"7 Ship Shares"`), appended after boosts, singles, and repeats; quantity benefits never render as `(xN)`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_formatter.py`:

```python
def test_ship_shares_quantities_summed() -> None:
    from cetools.formatter import _combine_material_benefits

    benefits = [
        Benefit(kind="material", material_name="Ship Shares", material_quantity=3),
        Benefit(kind="material", material_name="Ship Shares", material_quantity=4),
    ]
    assert _combine_material_benefits(benefits) == ["7 Ship Shares"]


def test_single_ship_share_renders_without_pluralization() -> None:
    from cetools.formatter import _combine_material_benefits

    benefits = [Benefit(kind="material", material_name="Ship Shares", material_quantity=1)]
    assert _combine_material_benefits(benefits) == ["1 Ship Shares"]


def test_ship_shares_coexist_with_boosts_and_items() -> None:
    from cetools.formatter import _combine_material_benefits

    benefits = [
        Benefit(kind="material", material_name="+1 Edu"),
        Benefit(kind="material", material_name="High Passage"),
        Benefit(kind="material", material_name="Ship Shares", material_quantity=2),
    ]
    assert _combine_material_benefits(benefits) == [
        "+1 Edu",
        "High Passage",
        "2 Ship Shares",
    ]
```

(`Benefit` is already imported at the top of `tests/test_formatter.py`.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_formatter.py -k ship_share -v --no-cov`

Expected: FAIL. The current formatter treats `"Ship Shares"` as a plain item, so two rolls render `["Ship Shares (x2)"]` and a single renders `["Ship Shares"]` — neither matches.

- [ ] **Step 3: Rewrite `_combine_material_benefits`**

In `src/cetools/formatter.py`, replace the whole `_combine_material_benefits` function with:

```python
def _combine_material_benefits(benefits: list[Benefit]) -> list[str]:
    boost_totals: dict[str, int] = {}
    boost_first_index: dict[str, int] = {}
    item_counts: dict[str, int] = {}
    item_first_index: dict[str, int] = {}
    quantity_totals: dict[str, int] = {}
    quantity_first_index: dict[str, int] = {}

    index = 0
    for benefit in benefits:
        if benefit.kind != "material":
            continue
        name = benefit.material_name
        if benefit.material_quantity is not None:
            quantity_totals[name] = quantity_totals.get(name, 0) + benefit.material_quantity
            quantity_first_index.setdefault(name, index)
        elif name.startswith("+1 "):
            label = name[3:]
            boost_totals[label] = boost_totals.get(label, 0) + 1
            boost_first_index.setdefault(label, index)
        else:
            item_counts[name] = item_counts.get(name, 0) + 1
            item_first_index.setdefault(name, index)
        index += 1

    boosts = [
        f"+{boost_totals[label]} {label}"
        for label in sorted(boost_totals, key=lambda label: boost_first_index[label])
    ]
    singles = sorted(
        (name for name, count in item_counts.items() if count == 1),
        key=lambda name: item_first_index[name],
    )
    repeats = sorted(
        (name for name, count in item_counts.items() if count > 1),
        key=lambda name: item_first_index[name],
    )
    quantities = [
        f"{quantity_totals[name]} {name}"
        for name in sorted(quantity_totals, key=lambda name: quantity_first_index[name])
    ]

    return (
        boosts
        + singles
        + [f"{name} (x{item_counts[name]})" for name in repeats]
        + quantities
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_formatter.py -v --no-cov`

Expected: PASS (the three new tests plus all existing formatter tests — the existing flat `"Ship Share"` benefit carries no quantity, so it still renders as a plain item).

- [ ] **Step 5: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/formatter.py tests/test_formatter.py
git commit -m "feat: render ship-shares benefit quantity in output"
```

---

### Task 3: Agent career

**Files:**
- Create: `src/cetools/engine/careers/agent.py`
- Test: `tests/test_agent_career.py`

**Interfaces:**
- Produces: `AGENT_CAREER` (a `Career`) importable from `cetools.engine.careers.agent`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_agent_career.py`:

```python
from cetools.engine.careers.agent import AGENT_CAREER
from cetools.engine.careers.base import RankEntry


def test_agent_scalar_fields() -> None:
    assert AGENT_CAREER.name == "Agent"
    assert AGENT_CAREER.qualification_stat == "Social Standing"
    assert AGENT_CAREER.qualification_target == 6
    assert AGENT_CAREER.survival_stat == "Intelligence"
    assert AGENT_CAREER.survival_target == 6
    assert AGENT_CAREER.commission_stat == "Education"
    assert AGENT_CAREER.commission_target == 7
    assert AGENT_CAREER.advancement_stat == "Education"
    assert AGENT_CAREER.advancement_target == 6
    assert AGENT_CAREER.reenlistment_target == 6


def test_agent_skill_tables() -> None:
    assert AGENT_CAREER.personal_development == (
        "+1 Dex", "+1 End", "+1 Int", "+1 Edu", "Athletics", "Carousing",
    )
    assert AGENT_CAREER.service_skills == (
        "Admin", "Computer", "Streetwise", "Bribery", "Leadership", "Vehicle",
    )
    assert AGENT_CAREER.specialist_skills == (
        "Gun Combat", "Melee Combat", "Bribery", "Leadership", "Recon", "Survival",
    )
    assert AGENT_CAREER.advanced_education == (
        "Advocate", "Computer", "Liaison", "Linguistics", "Medicine", "Leadership",
    )


def test_agent_ranks() -> None:
    assert AGENT_CAREER.ranks == (
        RankEntry(0, "Agent", ("Streetwise",)),
        RankEntry(1, "Special Agent", ()),
        RankEntry(2, "Sp Agent in Charge", ()),
        RankEntry(3, "Unit Chief", ()),
        RankEntry(4, "Section Chief", ("Admin",)),
        RankEntry(5, "Assistant Director", ()),
        RankEntry(6, "Director", ()),
    )


def test_agent_benefits() -> None:
    assert AGENT_CAREER.cash_benefits == (1000, 5000, 10000, 10000, 20000, 50000, 50000)
    assert AGENT_CAREER.material_benefits == (
        "Low Passage", "+1 Int", "Weapon", "Mid Passage", "+1 Soc",
        "High Passage", "Explorers' Society",
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_agent_career.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'cetools.engine.careers.agent'`.

- [ ] **Step 3: Create the career module**

Create `src/cetools/engine/careers/agent.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

AGENT_CAREER = Career(
    name="Agent",
    qualification_stat="Social Standing",
    qualification_target=6,
    survival_stat="Intelligence",
    survival_target=6,
    commission_stat="Education",
    commission_target=7,
    advancement_stat="Education",
    advancement_target=6,
    reenlistment_target=6,
    service_skills=("Admin", "Computer", "Streetwise", "Bribery", "Leadership", "Vehicle"),
    personal_development=("+1 Dex", "+1 End", "+1 Int", "+1 Edu", "Athletics", "Carousing"),
    specialist_skills=("Gun Combat", "Melee Combat", "Bribery", "Leadership", "Recon", "Survival"),
    advanced_education=("Advocate", "Computer", "Liaison", "Linguistics", "Medicine", "Leadership"),
    ranks=(
        RankEntry(0, "Agent", ("Streetwise",)),
        RankEntry(1, "Special Agent", ()),
        RankEntry(2, "Sp Agent in Charge", ()),
        RankEntry(3, "Unit Chief", ()),
        RankEntry(4, "Section Chief", ("Admin",)),
        RankEntry(5, "Assistant Director", ()),
        RankEntry(6, "Director", ()),
    ),
    cash_benefits=(1000, 5000, 10000, 10000, 20000, 50000, 50000),
    material_benefits=(
        "Low Passage",
        "+1 Int",
        "Weapon",
        "Mid Passage",
        "+1 Soc",
        "High Passage",
        "Explorers' Society",
    ),
)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_agent_career.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/agent.py tests/test_agent_career.py
git commit -m "feat: add Agent career"
```

---

### Task 4: Bureaucrat career

**Files:**
- Create: `src/cetools/engine/careers/bureaucrat.py`
- Test: `tests/test_bureaucrat_career.py`

**Interfaces:**
- Produces: `BUREAUCRAT_CAREER` importable from `cetools.engine.careers.bureaucrat`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_bureaucrat_career.py`:

```python
from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.bureaucrat import BUREAUCRAT_CAREER


def test_bureaucrat_scalar_fields() -> None:
    assert BUREAUCRAT_CAREER.name == "Bureaucrat"
    assert BUREAUCRAT_CAREER.qualification_stat == "Social Standing"
    assert BUREAUCRAT_CAREER.qualification_target == 6
    assert BUREAUCRAT_CAREER.survival_stat == "Education"
    assert BUREAUCRAT_CAREER.survival_target == 4
    assert BUREAUCRAT_CAREER.commission_stat == "Social Standing"
    assert BUREAUCRAT_CAREER.commission_target == 5
    assert BUREAUCRAT_CAREER.advancement_stat == "Intelligence"
    assert BUREAUCRAT_CAREER.advancement_target == 8
    assert BUREAUCRAT_CAREER.reenlistment_target == 5


def test_bureaucrat_skill_tables() -> None:
    assert BUREAUCRAT_CAREER.personal_development == (
        "+1 Dex", "+1 End", "+1 Int", "+1 Edu", "Athletics", "Carousing",
    )
    assert BUREAUCRAT_CAREER.service_skills == (
        "Admin", "Computer", "Carousing", "Bribery", "Leadership", "Vehicle",
    )
    assert BUREAUCRAT_CAREER.specialist_skills == (
        "Admin", "Computer", "Perception", "Leadership", "Steward", "Vehicle",
    )
    assert BUREAUCRAT_CAREER.advanced_education == (
        "Advocate", "Computer", "Liaison", "Linguistics", "Medicine", "Admin",
    )


def test_bureaucrat_ranks() -> None:
    assert BUREAUCRAT_CAREER.ranks == (
        RankEntry(0, "Assistant", ("Admin",)),
        RankEntry(1, "Clerk", ()),
        RankEntry(2, "Supervisor", ()),
        RankEntry(3, "Manager", ()),
        RankEntry(4, "Chief", ("Advocate",)),
        RankEntry(5, "Director", ()),
        RankEntry(6, "Minister", ()),
    )


def test_bureaucrat_benefits() -> None:
    assert BUREAUCRAT_CAREER.cash_benefits == (1000, 5000, 10000, 10000, 20000, 50000, 50000)
    assert BUREAUCRAT_CAREER.material_benefits == (
        "Low Passage", "+1 Edu", "+1 Int", "Mid Passage", "Mid Passage",
        "High Passage", "+1 Soc",
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_bureaucrat_career.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Create the career module**

Create `src/cetools/engine/careers/bureaucrat.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

BUREAUCRAT_CAREER = Career(
    name="Bureaucrat",
    qualification_stat="Social Standing",
    qualification_target=6,
    survival_stat="Education",
    survival_target=4,
    commission_stat="Social Standing",
    commission_target=5,
    advancement_stat="Intelligence",
    advancement_target=8,
    reenlistment_target=5,
    service_skills=("Admin", "Computer", "Carousing", "Bribery", "Leadership", "Vehicle"),
    personal_development=("+1 Dex", "+1 End", "+1 Int", "+1 Edu", "Athletics", "Carousing"),
    specialist_skills=("Admin", "Computer", "Perception", "Leadership", "Steward", "Vehicle"),
    advanced_education=("Advocate", "Computer", "Liaison", "Linguistics", "Medicine", "Admin"),
    ranks=(
        RankEntry(0, "Assistant", ("Admin",)),
        RankEntry(1, "Clerk", ()),
        RankEntry(2, "Supervisor", ()),
        RankEntry(3, "Manager", ()),
        RankEntry(4, "Chief", ("Advocate",)),
        RankEntry(5, "Director", ()),
        RankEntry(6, "Minister", ()),
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

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_bureaucrat_career.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/bureaucrat.py tests/test_bureaucrat_career.py
git commit -m "feat: add Bureaucrat career"
```

---

### Task 5: Diplomat career

**Files:**
- Create: `src/cetools/engine/careers/diplomat.py`
- Test: `tests/test_diplomat_career.py`

**Interfaces:**
- Produces: `DIPLOMAT_CAREER` importable from `cetools.engine.careers.diplomat`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_diplomat_career.py`:

```python
from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.diplomat import DIPLOMAT_CAREER


def test_diplomat_scalar_fields() -> None:
    assert DIPLOMAT_CAREER.name == "Diplomat"
    assert DIPLOMAT_CAREER.qualification_stat == "Social Standing"
    assert DIPLOMAT_CAREER.qualification_target == 6
    assert DIPLOMAT_CAREER.survival_stat == "Education"
    assert DIPLOMAT_CAREER.survival_target == 5
    assert DIPLOMAT_CAREER.commission_stat == "Intelligence"
    assert DIPLOMAT_CAREER.commission_target == 7
    assert DIPLOMAT_CAREER.advancement_stat == "Social Standing"
    assert DIPLOMAT_CAREER.advancement_target == 7
    assert DIPLOMAT_CAREER.reenlistment_target == 5


def test_diplomat_skill_tables() -> None:
    assert DIPLOMAT_CAREER.personal_development == (
        "+1 Dex", "+1 End", "+1 Int", "+1 Edu", "Athletics", "Carousing",
    )
    assert DIPLOMAT_CAREER.service_skills == (
        "Admin", "Computer", "Carousing", "Bribery", "Liaison", "Vehicle",
    )
    assert DIPLOMAT_CAREER.specialist_skills == (
        "Carousing", "Linguistics", "Bribery", "Liaison", "Steward", "Vehicle",
    )
    assert DIPLOMAT_CAREER.advanced_education == (
        "Advocate", "Computer", "Liaison", "Linguistics", "Medicine", "Leadership",
    )


def test_diplomat_ranks() -> None:
    assert DIPLOMAT_CAREER.ranks == (
        RankEntry(0, "Attaché", ("Liaison",)),
        RankEntry(1, "Third Secretary", ()),
        RankEntry(2, "Second Secretary", ()),
        RankEntry(3, "First Secretary", ("Admin",)),
        RankEntry(4, "Counselor", ()),
        RankEntry(5, "Minister", ()),
        RankEntry(6, "Ambassador", ()),
    )


def test_diplomat_benefits() -> None:
    assert DIPLOMAT_CAREER.cash_benefits == (1000, 5000, 10000, 20000, 20000, 50000, 100000)
    assert DIPLOMAT_CAREER.material_benefits == (
        "Low Passage", "+1 Edu", "Mid Passage", "High Passage", "+1 Soc",
        "High Passage", "Explorers' Society",
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_diplomat_career.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Create the career module**

Create `src/cetools/engine/careers/diplomat.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

DIPLOMAT_CAREER = Career(
    name="Diplomat",
    qualification_stat="Social Standing",
    qualification_target=6,
    survival_stat="Education",
    survival_target=5,
    commission_stat="Intelligence",
    commission_target=7,
    advancement_stat="Social Standing",
    advancement_target=7,
    reenlistment_target=5,
    service_skills=("Admin", "Computer", "Carousing", "Bribery", "Liaison", "Vehicle"),
    personal_development=("+1 Dex", "+1 End", "+1 Int", "+1 Edu", "Athletics", "Carousing"),
    specialist_skills=("Carousing", "Linguistics", "Bribery", "Liaison", "Steward", "Vehicle"),
    advanced_education=("Advocate", "Computer", "Liaison", "Linguistics", "Medicine", "Leadership"),
    ranks=(
        RankEntry(0, "Attaché", ("Liaison",)),
        RankEntry(1, "Third Secretary", ()),
        RankEntry(2, "Second Secretary", ()),
        RankEntry(3, "First Secretary", ("Admin",)),
        RankEntry(4, "Counselor", ()),
        RankEntry(5, "Minister", ()),
        RankEntry(6, "Ambassador", ()),
    ),
    cash_benefits=(1000, 5000, 10000, 20000, 20000, 50000, 100000),
    material_benefits=(
        "Low Passage",
        "+1 Edu",
        "Mid Passage",
        "High Passage",
        "+1 Soc",
        "High Passage",
        "Explorers' Society",
    ),
)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_diplomat_career.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/diplomat.py tests/test_diplomat_career.py
git commit -m "feat: add Diplomat career"
```

---

### Task 6: Entertainer career

**Files:**
- Create: `src/cetools/engine/careers/entertainer.py`
- Test: `tests/test_entertainer_career.py`

**Interfaces:**
- Produces: `ENTERTAINER_CAREER` importable from `cetools.engine.careers.entertainer`. No commission/advancement (`None`); a single rank-0 entry; six material benefits.

- [ ] **Step 1: Write the failing test**

Create `tests/test_entertainer_career.py`:

```python
from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.entertainer import ENTERTAINER_CAREER


def test_entertainer_scalar_fields() -> None:
    assert ENTERTAINER_CAREER.name == "Entertainer"
    assert ENTERTAINER_CAREER.qualification_stat == "Social Standing"
    assert ENTERTAINER_CAREER.qualification_target == 8
    assert ENTERTAINER_CAREER.survival_stat == "Intelligence"
    assert ENTERTAINER_CAREER.survival_target == 4
    assert ENTERTAINER_CAREER.commission_stat is None
    assert ENTERTAINER_CAREER.commission_target is None
    assert ENTERTAINER_CAREER.advancement_stat is None
    assert ENTERTAINER_CAREER.advancement_target is None
    assert ENTERTAINER_CAREER.reenlistment_target == 6


def test_entertainer_skill_tables() -> None:
    assert ENTERTAINER_CAREER.personal_development == (
        "+1 Dex", "+1 Int", "+1 Edu", "+1 Soc", "Carousing", "Melee Combat",
    )
    assert ENTERTAINER_CAREER.service_skills == (
        "Athletics", "Admin", "Carousing", "Bribery", "Gambling", "Vehicle",
    )
    assert ENTERTAINER_CAREER.specialist_skills == (
        "Computer", "Carousing", "Bribery", "Liaison", "Gambling", "Recon",
    )
    assert ENTERTAINER_CAREER.advanced_education == (
        "Advocate", "Computer", "Carousing", "Linguistics", "Medicine", "Sciences",
    )


def test_entertainer_ranks() -> None:
    assert ENTERTAINER_CAREER.ranks == (RankEntry(0, "Entertainer", ("Carousing",)),)


def test_entertainer_benefits() -> None:
    assert ENTERTAINER_CAREER.cash_benefits == (2000, 10000, 20000, 20000, 50000, 100000, 100000)
    assert ENTERTAINER_CAREER.material_benefits == (
        "Low Passage", "+1 Edu", "+1 Soc", "High Passage", "Explorers' Society",
        "High Passage",
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_entertainer_career.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Create the career module**

Create `src/cetools/engine/careers/entertainer.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

ENTERTAINER_CAREER = Career(
    name="Entertainer",
    qualification_stat="Social Standing",
    qualification_target=8,
    survival_stat="Intelligence",
    survival_target=4,
    commission_stat=None,
    commission_target=None,
    advancement_stat=None,
    advancement_target=None,
    reenlistment_target=6,
    service_skills=("Athletics", "Admin", "Carousing", "Bribery", "Gambling", "Vehicle"),
    personal_development=("+1 Dex", "+1 Int", "+1 Edu", "+1 Soc", "Carousing", "Melee Combat"),
    specialist_skills=("Computer", "Carousing", "Bribery", "Liaison", "Gambling", "Recon"),
    advanced_education=("Advocate", "Computer", "Carousing", "Linguistics", "Medicine", "Sciences"),
    ranks=(RankEntry(0, "Entertainer", ("Carousing",)),),
    cash_benefits=(2000, 10000, 20000, 20000, 50000, 100000, 100000),
    material_benefits=(
        "Low Passage",
        "+1 Edu",
        "+1 Soc",
        "High Passage",
        "Explorers' Society",
        "High Passage",
    ),
)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_entertainer_career.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/entertainer.py tests/test_entertainer_career.py
git commit -m "feat: add Entertainer career"
```

---

### Task 7: Noble career

**Files:**
- Create: `src/cetools/engine/careers/noble.py`
- Test: `tests/test_noble_career.py`

**Interfaces:**
- Produces: `NOBLE_CAREER` importable from `cetools.engine.careers.noble`. Material slot 1 is `High Passage` and slot 7 is the `1D6 Ship Shares` sentinel (consumed by the Task 1 mechanic).

- [ ] **Step 1: Write the failing test**

Create `tests/test_noble_career.py`:

```python
from cetools.engine.careers.base import RankEntry
from cetools.engine.careers.noble import NOBLE_CAREER


def test_noble_scalar_fields() -> None:
    assert NOBLE_CAREER.name == "Noble"
    assert NOBLE_CAREER.qualification_stat == "Social Standing"
    assert NOBLE_CAREER.qualification_target == 8
    assert NOBLE_CAREER.survival_stat == "Social Standing"
    assert NOBLE_CAREER.survival_target == 4
    assert NOBLE_CAREER.commission_stat == "Education"
    assert NOBLE_CAREER.commission_target == 5
    assert NOBLE_CAREER.advancement_stat == "Intelligence"
    assert NOBLE_CAREER.advancement_target == 8
    assert NOBLE_CAREER.reenlistment_target == 6


def test_noble_skill_tables() -> None:
    assert NOBLE_CAREER.personal_development == (
        "+1 Dex", "+1 Int", "+1 Edu", "+1 Soc", "Carousing", "Melee Combat",
    )
    assert NOBLE_CAREER.service_skills == (
        "Athletics", "Admin", "Carousing", "Leadership", "Gambling", "Vehicle",
    )
    assert NOBLE_CAREER.specialist_skills == (
        "Computer", "Carousing", "Gun Combat", "Melee Combat", "Liaison", "Animals",
    )
    assert NOBLE_CAREER.advanced_education == (
        "Advocate", "Computer", "Liaison", "Linguistics", "Medicine", "Sciences",
    )


def test_noble_ranks() -> None:
    assert NOBLE_CAREER.ranks == (
        RankEntry(0, "Courtier", ("Carousing",)),
        RankEntry(1, "Knight", ()),
        RankEntry(2, "Baron", ()),
        RankEntry(3, "Marquis", ()),
        RankEntry(4, "Count", ("Advocate",)),
        RankEntry(5, "Duke", ()),
        RankEntry(6, "Archduke", ()),
    )


def test_noble_benefits() -> None:
    assert NOBLE_CAREER.cash_benefits == (2000, 10000, 20000, 20000, 50000, 100000, 100000)
    assert NOBLE_CAREER.material_benefits == (
        "High Passage", "+1 Edu", "+1 Int", "High Passage", "Explorers' Society",
        "High Passage", "1D6 Ship Shares",
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_noble_career.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Create the career module**

Create `src/cetools/engine/careers/noble.py`:

```python
from cetools.engine.careers.base import Career, RankEntry

NOBLE_CAREER = Career(
    name="Noble",
    qualification_stat="Social Standing",
    qualification_target=8,
    survival_stat="Social Standing",
    survival_target=4,
    commission_stat="Education",
    commission_target=5,
    advancement_stat="Intelligence",
    advancement_target=8,
    reenlistment_target=6,
    service_skills=("Athletics", "Admin", "Carousing", "Leadership", "Gambling", "Vehicle"),
    personal_development=("+1 Dex", "+1 Int", "+1 Edu", "+1 Soc", "Carousing", "Melee Combat"),
    specialist_skills=("Computer", "Carousing", "Gun Combat", "Melee Combat", "Liaison", "Animals"),
    advanced_education=("Advocate", "Computer", "Liaison", "Linguistics", "Medicine", "Sciences"),
    ranks=(
        RankEntry(0, "Courtier", ("Carousing",)),
        RankEntry(1, "Knight", ()),
        RankEntry(2, "Baron", ()),
        RankEntry(3, "Marquis", ()),
        RankEntry(4, "Count", ("Advocate",)),
        RankEntry(5, "Duke", ()),
        RankEntry(6, "Archduke", ()),
    ),
    cash_benefits=(2000, 10000, 20000, 20000, 50000, 100000, 100000),
    material_benefits=(
        "High Passage",
        "+1 Edu",
        "+1 Int",
        "High Passage",
        "Explorers' Society",
        "High Passage",
        "1D6 Ship Shares",
    ),
)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_noble_career.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/noble.py tests/test_noble_career.py
git commit -m "feat: add Noble career"
```

---

### Task 8: Register the five careers + update README and CLI tests

**Files:**
- Modify: `src/cetools/engine/careers/registry.py` (imports + `CAREER_REGISTRY`, NOT `DRAFT_TABLE`)
- Modify: `README.md:5` (supported-careers line)
- Test: `tests/test_careers.py` (registry assertions), `tests/test_cli.py` (the two hard-coded "Valid careers:" strings)

**Interfaces:**
- Consumes: `AGENT_CAREER`, `BUREAUCRAT_CAREER`, `DIPLOMAT_CAREER`, `ENTERTAINER_CAREER`, `NOBLE_CAREER` from Tasks 3–7.
- Produces: registry keys `"agent"`, `"bureaucrat"`, `"diplomat"`, `"entertainer"`, `"noble"` resolving to those careers; none added to `DRAFT_TABLE`.

- [ ] **Step 1: Write the failing registry tests**

Append to `tests/test_careers.py`:

```python
from cetools.engine.careers.agent import AGENT_CAREER  # noqa: E402
from cetools.engine.careers.bureaucrat import BUREAUCRAT_CAREER  # noqa: E402
from cetools.engine.careers.diplomat import DIPLOMAT_CAREER  # noqa: E402
from cetools.engine.careers.entertainer import ENTERTAINER_CAREER  # noqa: E402
from cetools.engine.careers.noble import NOBLE_CAREER  # noqa: E402


def test_registry_has_social_career_keys() -> None:
    for key in ("agent", "bureaucrat", "diplomat", "entertainer", "noble"):
        assert key in CAREER_REGISTRY


def test_registry_social_career_values() -> None:
    assert CAREER_REGISTRY["agent"] is AGENT_CAREER
    assert CAREER_REGISTRY["bureaucrat"] is BUREAUCRAT_CAREER
    assert CAREER_REGISTRY["diplomat"] is DIPLOMAT_CAREER
    assert CAREER_REGISTRY["entertainer"] is ENTERTAINER_CAREER
    assert CAREER_REGISTRY["noble"] is NOBLE_CAREER


def test_social_careers_not_draftable() -> None:
    for key in ("agent", "bureaucrat", "diplomat", "entertainer", "noble"):
        assert key not in DRAFT_TABLE
    assert len(DRAFT_TABLE) == 6
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_careers.py -k "social" -v --no-cov`
Expected: FAIL — the imports resolve (Tasks 3–7 created the modules) but the registry keys are absent, so `test_registry_has_social_career_keys` fails.

- [ ] **Step 3: Register the careers**

Replace the contents of `src/cetools/engine/careers/registry.py` with:

```python
from cetools.engine.careers.aerospace import AEROSPACE_CAREER
from cetools.engine.careers.agent import AGENT_CAREER
from cetools.engine.careers.base import Career
from cetools.engine.careers.bureaucrat import BUREAUCRAT_CAREER
from cetools.engine.careers.diplomat import DIPLOMAT_CAREER
from cetools.engine.careers.entertainer import ENTERTAINER_CAREER
from cetools.engine.careers.marine import MARINE_CAREER
from cetools.engine.careers.maritime import MARITIME_CAREER
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.noble import NOBLE_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER
from cetools.engine.careers.surface import SURFACE_CAREER

CAREER_REGISTRY: dict[str, Career] = {
    "aerospace system defense": AEROSPACE_CAREER,
    "agent": AGENT_CAREER,
    "bureaucrat": BUREAUCRAT_CAREER,
    "diplomat": DIPLOMAT_CAREER,
    "entertainer": ENTERTAINER_CAREER,
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

In `tests/test_cli.py`, the sorted careers list now has eleven entries:
`Aerospace System Defense, Agent, Bureaucrat, Diplomat, Entertainer, Marine, Maritime System Defense, Navy, Noble, Scout, Surface System Defense`.

Update the first hard-coded expectation (currently around lines 199-200, the `'merchant'` case):

```python
        "Unknown career 'merchant'. Valid careers: Aerospace System Defense, "
        "Agent, Bureaucrat, Diplomat, Entertainer, Marine, "
        "Maritime System Defense, Navy, Noble, Scout, Surface System Defense"
```

Update the second hard-coded expectation (currently around lines 401-402, the `'xyzzy'` case) the same way:

```python
        "Unknown career 'xyzzy'. Valid careers: Aerospace System Defense, "
        "Agent, Bureaucrat, Diplomat, Entertainer, Marine, "
        "Maritime System Defense, Navy, Noble, Scout, Surface System Defense"
```

(These are adjacent implicitly-concatenated string literals; keep them as a single concatenated string matching the CLI output exactly. If either `'merchant'` or `'xyzzy'` now yields a `difflib` "Did you mean" suggestion instead of the list — verify in Step 6 — that is a real behavior change to surface, not to paper over.)

- [ ] **Step 5: Update the README supported-careers line**

In `README.md`, replace line 5:

```markdown
Supported careers: **Aerospace System Defense**, **Marine**, **Maritime System Defense**, **Navy**, **Scout**, **Surface System Defense**. Omit the career to have one drafted at random.
```

with:

```markdown
Supported careers: **Aerospace System Defense**, **Agent**, **Bureaucrat**, **Diplomat**, **Entertainer**, **Marine**, **Maritime System Defense**, **Navy**, **Noble**, **Scout**, **Surface System Defense**. Omit `--career` to have one of the six services (Aerospace System Defense, Marine, Maritime System Defense, Navy, Scout, Surface System Defense) drafted at random; the other careers are selectable with `--career` only.
```

- [ ] **Step 6: Run the full suite with coverage**

Run: `uv run pytest`
Expected: PASS, coverage ≥85%. Confirms the registry, README-independent CLI behavior, and the two updated CLI assertions all agree with the actual sorted careers list. If a CLI test instead reports a "Did you mean" suggestion for `merchant` or `xyzzy`, stop and report it (see Step 4 note).

- [ ] **Step 7: Format, lint, commit**

```bash
uv run black . && uv run flake8 src tests
git add src/cetools/engine/careers/registry.py README.md tests/test_careers.py tests/test_cli.py
git commit -m "feat: register Social careers and document them"
```

---

## Self-Review

**Spec coverage:**
- Ship-shares model field → Task 1, Step 3. ✓
- Ship-shares generator roll + `_SHIP_SHARES_BENEFIT` constant → Task 1, Steps 4-5. ✓
- Ship-shares formatter aggregation (`"7 Ship Shares"`, `"1 Ship Shares"`, coexists with boosts/items, no `(xN)`) → Task 2. ✓
- Agent / Bureaucrat / Diplomat / Entertainer / Noble data (all fields verbatim) → Tasks 3-7. ✓
- Entertainer `None` commission/advancement, single rank, 6 material entries → Task 6. ✓
- Noble slot-1 `High Passage`, slot-7 `1D6 Ship Shares` → Task 7. ✓
- Registry-only (not draftable) → Task 8, Step 3 + `test_social_careers_not_draftable`. ✓
- README + CLI list updates → Task 8, Steps 4-5. ✓
- Per-career test files mirroring the pattern; model/generator/formatter mechanic tests → each task. ✓

**Placeholder scan:** No TBD/TODO/"handle edge cases". Every code and test step contains complete content. The Step-4/Step-6 note about a possible `difflib` suggestion is a verification instruction, not deferred work.

**Type consistency:** `material_quantity: int | None` is defined in Task 1 and consumed by name in Task 2 and the generator. Career constant names (`AGENT_CAREER`, etc.) are produced in Tasks 3-7 and consumed verbatim in Task 8's imports and registry. Registry keys (`"agent"`, `"bureaucrat"`, `"diplomat"`, `"entertainer"`, `"noble"`) match between Task 8's registry literal and its tests. `"Ship Shares"` (display) vs `"1D6 Ship Shares"` (sentinel) are used consistently.
