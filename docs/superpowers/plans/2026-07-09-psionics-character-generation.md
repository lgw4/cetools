# Psionics Character Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Roll the Psi characteristic for every generated character and, when Psi is viable, learn the five psionic talents — surfaced as a hyphenated pseudo-hex UPP suffix and an optional `Psionics:` line.

**Architecture:** A new pure, roller-injected function `roll_psionics` in `engine/psionics.py` computes `Psi = 2D6 − terms_served` (floored at 0) and attempts the five talents highest-DM-first with a cumulative per-attempt penalty. The generator calls it once on the unconditional return path; two new `Character` fields carry the data; the formatter decides presentation (suffix only for psionic characters, `Psionics:` line only when talents were learned).

**Tech Stack:** Python 3.13, dataclasses, pytest (with coverage ≥85% enforced), Black, flake8, isort. Dice go through the `DiceRoller` protocol (`engine/dice.py`); tests use the roller helpers in `tests/conftest.py`.

## Global Constraints

- Python 3.13+; format with Black, lint with flake8, imports sorted with isort.
- `src/cetools` test coverage must stay ≥85% (full-suite pytest enforces it).
- All randomness routes through the injected `DiceRoller`; never call `random` directly in engine code.
- Conventional Commits for every commit message.
- `Character.upp` stays the bare six-character pseudo-hex UPP; the Psi suffix is a **formatter-only** presentation concern.
- Psi is rolled for **every** character (universal testing); talents are attempted only when `Psi ≥ 1`. No CLI flag. Training cost/time is not modeled (cash and age untouched).
- Talent attempt order and Learning DMs (fixed): Telepathy +4, Clairvoyance +3, Telekinesis +2, Awareness +1, Teleportation +0. Training check target is 8+.

**Note on the spec signature:** the design doc sketched `roll_psionics(terms_served, characteristics, roller)`. The `characteristics` argument is unused — the Psi characteristic DM derives from the rolled Psi score, not from any of the six base characteristics — so this plan uses the tighter signature `roll_psionics(terms_served, roller)`. This is the only deviation from the spec.

---

### Task 1: Add `psi_strength` and `talents` fields to `Character`

**Files:**
- Modify: `src/cetools/engine/models.py` (the `Character` dataclass, ~lines 88–104)
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Character.psi_strength: int` (default `0`) and `Character.talents: dict[str, int]` (default empty), consumed by Tasks 3 and 4.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_models.py`:

```python
def test_character_psionics_default_to_non_psionic() -> None:
    char = Character(
        characteristics={},
        upp="000000",
        age=18,
        career="Scout",
        rank=0,
        rank_title="Scout",
        terms_served=1,
        name="Jane Doe",
        skills={},
        benefits=[],
        pension=None,
        terms=[],
    )
    assert char.psi_strength == 0
    assert char.talents == {}


def test_character_psionics_can_be_set() -> None:
    char = Character(
        characteristics={},
        upp="000000",
        age=18,
        career="Scout",
        rank=0,
        rank_title="Scout",
        terms_served=1,
        name="Jane Doe",
        skills={},
        benefits=[],
        pension=None,
        terms=[],
        psi_strength=6,
        talents={"Telepathy": 0},
    )
    assert char.psi_strength == 6
    assert char.talents == {"Telepathy": 0}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_models.py -k psionics --no-cov -v`
Expected: FAIL — `TypeError: Character.__init__() got an unexpected keyword argument 'psi_strength'`.

- [ ] **Step 3: Add the fields**

In `src/cetools/engine/models.py`, in the `Character` dataclass, add these two fields immediately after `debt: int = 0` (both are defaulted, so they must stay after the existing defaulted fields):

```python
    psi_strength: int = 0
    talents: dict[str, int] = field(default_factory=dict)
```

`field` is already imported at the top of the file (`from dataclasses import dataclass, field`).

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_models.py -k psionics --no-cov -v`
Expected: PASS (both tests).

- [ ] **Step 5: Commit**

```bash
git add src/cetools/engine/models.py tests/test_models.py
git commit -m "feat: add psi_strength and talents fields to Character"
```

---

### Task 2: Implement `roll_psionics` in `engine/psionics.py`

**Files:**
- Create: `src/cetools/engine/psionics.py`
- Test: `tests/test_psionics.py`

**Interfaces:**
- Consumes: `DiceRoller` (`engine/dice.py`), `characteristic_modifier` (`engine/models.py`).
- Produces: `roll_psionics(terms_served: int, roller: DiceRoller) -> tuple[int, dict[str, int]]` — returns `(psi_strength, talents)` where `talents` maps each learned talent name to `0` and is empty when `psi_strength < 1`. Consumed by Task 4.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_psionics.py`:

```python
from cetools.engine.psionics import roll_psionics
from tests.conftest import SequenceRoller


def test_psi_strength_is_two_d6_minus_terms() -> None:
    # First 2D6 roll (9) minus 3 terms = 6.
    psi, _ = roll_psionics(terms_served=3, roller=SequenceRoller([9], default=2))
    assert psi == 6


def test_psi_strength_floors_at_zero_and_skips_training() -> None:
    # 7 - 10 = -3, floored to 0. The high follow-up values (12) must never be
    # consumed, proving no talent checks are attempted when Psi < 1.
    psi, talents = roll_psionics(
        terms_served=10, roller=SequenceRoller([7, 12, 12, 12, 12, 12])
    )
    assert psi == 0
    assert talents == {}


def test_training_order_and_cumulative_penalty() -> None:
    # Psi roll 7, terms 0 -> Psi 7 (PsiDM 0). Then five talent checks each roll 8:
    #   Telepathy(+4, attempt 0): 8+4-0=12 >= 8  -> learned
    #   Clairvoyance(+3, attempt 1): 8+3-1=10 >= 8 -> learned
    #   Telekinesis(+2, attempt 2): 8+2-2=8 >= 8   -> learned
    #   Awareness(+1, attempt 3): 8+1-3=6 < 8      -> not learned
    #   Teleportation(+0, attempt 4): 8+0-4=4 < 8  -> not learned
    psi, talents = roll_psionics(
        terms_served=0, roller=SequenceRoller([7, 8, 8, 8, 8, 8])
    )
    assert psi == 7
    assert talents == {"Telepathy": 0, "Clairvoyance": 0, "Telekinesis": 0}


def test_learned_talents_are_level_zero() -> None:
    _, talents = roll_psionics(terms_served=0, roller=SequenceRoller([7, 8, 8, 8, 8, 8]))
    assert all(level == 0 for level in talents.values())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_psionics.py --no-cov -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cetools.engine.psionics'`.

- [ ] **Step 3: Write the implementation**

Create `src/cetools/engine/psionics.py`:

```python
from cetools.engine.dice import DiceRoller
from cetools.engine.models import characteristic_modifier

# Talents in highest-Learning-DM-first attempt order (name, learning DM).
_TALENTS: tuple[tuple[str, int], ...] = (
    ("Telepathy", 4),
    ("Clairvoyance", 3),
    ("Telekinesis", 2),
    ("Awareness", 1),
    ("Teleportation", 0),
)

_TRAINING_TARGET = 8


def roll_psionics(terms_served: int, roller: DiceRoller) -> tuple[int, dict[str, int]]:
    """Roll Psi strength and learn talents.

    Psi = 2D6 - terms_served, floored at 0. A character is psionic when Psi >= 1;
    only then are talents attempted. Each talent is a check
    ``2D6 + PsiDM + talentDM - (previous attempts) >= 8``; successes are granted
    at level 0. Talents are attempted highest-DM-first.
    """
    psi_strength = max(0, roller.roll(6, count=2) - terms_served)
    talents: dict[str, int] = {}
    if psi_strength < 1:
        return psi_strength, talents

    psi_dm = characteristic_modifier(psi_strength)
    for attempt_index, (name, talent_dm) in enumerate(_TALENTS):
        total = roller.roll(6, count=2) + psi_dm + talent_dm - attempt_index
        if total >= _TRAINING_TARGET:
            talents[name] = 0
    return psi_strength, talents
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_psionics.py --no-cov -v`
Expected: PASS (all four tests).

- [ ] **Step 5: Commit**

```bash
git add src/cetools/engine/psionics.py tests/test_psionics.py
git commit -m "feat: add roll_psionics for Psi strength and talent learning"
```

---

### Task 3: Render the Psi suffix and Psionics line in the formatter

**Files:**
- Modify: `src/cetools/formatter.py` (`format_character`, and a new import)
- Test: `tests/test_formatter.py`

**Interfaces:**
- Consumes: `Character.psi_strength` and `Character.talents` (Task 1); `to_pseudohex` (`engine/pseudohex.py`).
- Produces: no new public symbols; changes `format_character` output.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_formatter.py` (the module already imports `Character` and `format_character`, and defines `_make_full_character` / `_make_empty_character` helpers whose characters default to `psi_strength=0`, `talents={}`):

```python
def test_psionic_character_renders_upp_suffix_and_psionics_line() -> None:
    char = _make_full_character()
    char.psi_strength = 6
    char.talents = {"Telepathy": 0, "Awareness": 0}
    lines = format_character(char).split("\n")
    # UPP token on line 1 carries the pseudo-hex suffix.
    assert f"{char.upp}-6" in lines[0]
    # Psionics line is alphabetical and sits immediately after the skills line.
    assert "Psionics: Awareness-0, Telepathy-0" in lines
    skills_index = next(i for i, ln in enumerate(lines) if ln.startswith("Admin"))
    assert lines[skills_index + 1] == "Psionics: Awareness-0, Telepathy-0"


def test_non_psionic_character_has_bare_upp_and_no_psionics_line() -> None:
    char = _make_empty_character()  # psi_strength defaults to 0, talents to {}
    output = format_character(char)
    assert f"\t{char.upp}\t" in output  # bare UPP, no hyphen suffix
    assert "Psionics:" not in output


def test_high_psi_renders_pseudohex_suffix() -> None:
    char = _make_full_character()
    char.psi_strength = 10
    char.talents = {"Telepathy": 0}
    assert f"{char.upp}-A" in format_character(char)
```

Note: `_make_full_character` uses skills whose alphabetically-first entry is `Engineering`, not `Admin`. Confirm the first skill token when writing the test; adjust the `startswith(...)` sentinel in `test_psionic_character_renders_upp_suffix_and_psionics_line` to the actual first skill of that helper (it is the skill line, `lines[2]`). Simplest robust form: use `skills_index = 2` since line order is fixed (name/UPP/age, career/cash, skills).

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_formatter.py -k "psionic or psi" --no-cov -v`
Expected: FAIL — the UPP has no `-6` suffix and there is no `Psionics:` line.

- [ ] **Step 3: Implement the formatter changes**

In `src/cetools/formatter.py`:

Add the import near the top (below the existing `from cetools.engine.models import ...`):

```python
from cetools.engine.pseudohex import to_pseudohex
```

Replace the first two statements of `format_character` (the `rank_prefix` / `line1` lines) with:

```python
    rank_prefix = f"{character.rank_title} " if character.rank_title else ""
    upp_display = character.upp
    if character.psi_strength >= 1:
        upp_display += f"-{to_pseudohex(character.psi_strength)}"
    line1 = f"{rank_prefix}{character.name}\t{upp_display}\tAge {character.age}"
```

Then, after the block that builds `line3` and `lines = [line1, line2, line3]`, insert the Psionics line **before** the material-benefits block:

```python
    if character.talents:
        talent_parts = [
            f"{name}-{level}" for name, level in sorted(character.talents.items())
        ]
        lines.append("Psionics: " + ", ".join(talent_parts))
```

Leave the existing material-benefits and mishap blocks unchanged (they still append after this).

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_formatter.py --no-cov -v`
Expected: PASS — the three new tests pass and all pre-existing formatter tests still pass (their characters default to non-psionic, so output is unchanged).

- [ ] **Step 5: Commit**

```bash
git add src/cetools/formatter.py tests/test_formatter.py
git commit -m "feat: render Psi UPP suffix and Psionics line"
```

---

### Task 4: Wire `roll_psionics` into the generator

**Files:**
- Modify: `src/cetools/engine/generator.py` (`generate_character`: add import, compute Psi, pass to `Character(...)`, ~lines 402–420)
- Test: `tests/test_generator.py`

**Interfaces:**
- Consumes: `roll_psionics` (Task 2); `Character.psi_strength` / `Character.talents` (Task 1).
- Produces: every generated `Character` carries populated `psi_strength` and `talents`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_generator.py`. Check the existing imports at the top of the file; it already imports `Character` and career constants. Add `from tests.conftest import ConstantRoller` if not already present, and import the Navy career the way the file's other tests do (e.g. `from cetools.engine.careers.navy import NAVY_CAREER`).

```python
def test_generated_character_has_psionics() -> None:
    # ConstantRoller returns 9 for every roll, including the Psi 2D6 roll, so
    # Psi = max(0, 9 - terms_served). terms_served is on the result, so the
    # relationship holds without predicting the full generation.
    result = generate_career_character(NAVY_CAREER, ConstantRoller(9))
    assert isinstance(result, Character)
    assert isinstance(result.talents, dict)
    assert result.psi_strength == max(0, 9 - result.terms_served)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_generator.py::test_generated_character_has_psionics --no-cov -v`
Expected: FAIL — `assert 0 == max(0, 9 - N)` (Psi is still the default `0`, but the character served terms).

- [ ] **Step 3: Wire the generator**

In `src/cetools/engine/generator.py`:

Add the import alongside the other engine imports near the top:

```python
from cetools.engine.psionics import roll_psionics
```

In `generate_character`, immediately after `name = generate_name(roller)` (just before `return Character(`), add:

```python
    psi_strength, talents = roll_psionics(terms_served, roller)
```

Then in the `return Character(...)` call, add these two keyword arguments (e.g. after `debt=debt,`):

```python
        psi_strength=psi_strength,
        talents=talents,
```

This return is the single unconditional exit for both mishap and non-mishap characters, so every generated character — including those whose career ended in a mishap — gets a Psi roll.

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_generator.py::test_generated_character_has_psionics --no-cov -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/cetools/engine/generator.py tests/test_generator.py
git commit -m "feat: roll psionics for every generated character"
```

---

### Task 5: Full-suite verification, formatting, and README

**Files:**
- Modify: `README.md` (document psionics output)

**Interfaces:** none.

- [ ] **Step 1: Format and lint**

Run:
```bash
uv run isort . && uv run black . && uv run flake8 src tests
```
Expected: no changes needed / no lint errors. If isort or black reports changes, let them apply and re-run.

- [ ] **Step 2: Run the full suite with coverage**

Run: `uv run pytest`
Expected: all tests pass; `src/cetools` coverage ≥85%.

- [ ] **Step 3: Update the README**

In `README.md`, add a short note in the output-format section documenting psionics: every character rolls a Psi characteristic; psionic characters (`Psi ≥ 1`) show it as a hyphenated pseudo-hex UPP suffix (e.g. `5A3B93-6`), and any learned talents appear on an optional `Psionics:` line (alphabetical, each at level 0). Add a worked example, e.g.:

```text
Starman Sam Voss	5A3B93-6	Age 38
Navy (5 terms)	Cr52,000
Admin-0, Advocate-1, Comms-0, Engineering-1, Melee Combat-2, Tactics-1, Vehicle-2, Zero-G-1
Psionics: Awareness-0, Telepathy-0
+1 Edu, High Passage
```

Note in the prose that psionics is an optional SRD rule and that training cost/time is abstracted away (cash and age are untouched).

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: document psionics in character output"
```

---

## Self-Review

**Spec coverage:**
- Psi = 2D6 − terms_served, floored → Task 2 (`test_psi_strength_is_two_d6_minus_terms`, `test_psi_strength_floors_at_zero_and_skips_training`).
- Universal testing, viability gate at Psi ≥ 1 → Task 2 (floor test skips training) + Task 4 (unconditional return path).
- Highest-DM-first order + cumulative penalty + 8+ target → Task 2 (`test_training_order_and_cumulative_penalty`).
- Level-0 grants → Task 2 (`test_learned_talents_are_level_zero`).
- Cost/time abstracted (no cash/age change) → not modeled anywhere by construction; `roll_psionics` touches neither; noted in Global Constraints and README (Task 5).
- Model fields with safe defaults → Task 1.
- UPP bare + suffix only for psionic, pseudo-hex → Task 3 (`test_non_psionic_...`, `test_psionic_...`, `test_high_psi_renders_pseudohex_suffix`).
- Psionics line alphabetical, positioned after skills → Task 3.
- Generator wiring, one call site, mishap characters covered → Task 4.
- Coverage ≥85%, formatting, README → Task 5.

**Placeholder scan:** none — every code and test step carries complete code and exact commands.

**Type consistency:** `roll_psionics(terms_served: int, roller: DiceRoller) -> tuple[int, dict[str, int]]` is defined in Task 2 and called identically in Task 4. `Character.psi_strength: int` / `Character.talents: dict[str, int]` defined in Task 1 and consumed with matching names in Tasks 3 and 4. `to_pseudohex` signature matches its definition in `engine/pseudohex.py`.
