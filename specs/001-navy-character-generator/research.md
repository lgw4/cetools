# Research: Navy Character Generator

**Phase**: 0 | **Date**: 2026-06-17 | **Spec**: [spec.md](spec.md)
**Rules Sources**:
- Career tables: https://evolvedexperiment.github.io/cepheus-srd/character-creation.html#career-tables
- Pseudo-hex notation (canonical): https://evolvedexperiment.github.io/cepheus-srd/introduction.html#pseudo-hexadecimal-notation
- Canonical terminology: https://evolvedexperiment.github.io/cepheus-srd/introduction.html#important-terms

---

## Canonical Cepheus Engine Terminology

The following terms are defined by the SRD at the Introduction page and MUST be used consistently in all code identifiers, docstrings, and documentation. Using non-canonical synonyms is incorrect and will create confusion when referencing rules.

| SRD Term | Abbreviation | Use Instead Of |
|----------|-------------|---------------|
| Characteristic score | Str/Dex/End/Int/Edu/Soc | "stat", "attribute", "ability score" |
| Characteristic modifier | (none) | "modifier" alone, "bonus" |
| Dice modifier | DM | "modifier", "bonus/penalty" when applied to a check |
| Check (or Throw) | (none) | "roll" when used as a noun for an action resolution |
| 2D6 | (none) | "2d6", "two dice", "d6+d6" |
| Credit | Cr | "gold", "money", "currency" |
| Referee | (none) | "Game Master", "GM", "DM", "dungeon master" |
| Skill | (none) | Skills are always expressed as Name-Level (e.g., Navigation-1) |
| Universal Personality Profile | UPP | "character string", "stat block" |
| Homeworld | (none) | "home planet", "birth world" |
| Explorer's Society | (none) | Note: "Explorer's Society" not "Explorer's Society" |

**Pseudo-hexadecimal notation** (SRD canonical description): "The Cepheus Engine uses a form of pseudo-hexadecimal notation as a type of shorthand in noting specific values of characteristic scores, world statistics, drive type designations and similar design elements. The pseudohexadecimal notation proceeds as normal for values from 0 to 15, but extends beyond F for 15, with G for 16, etc. The Cepheus Engine skips the use of the letters I and O, because they might be mistaken for the numbers 1 and 0."

**Code naming implications**:
- Module: `pseudohex` (one word, matching SRD's "pseudohexadecimal")
- Function: `to_pseudohex(value: int) -> str` and `from_pseudohex(char: str) -> int`
- UPP string type: named `upp` in all models and contracts
- Dice: `roll_2d6()` and `roll_1d6()` — note capital D in documentation/comments, lowercase in code identifiers per Python convention
- Characteristic score fields: use full names as keys (`"Strength"`, `"Dexterity"`, etc.) and SRD abbreviations in display (`Str`, `Dex`, `End`, `Int`, `Edu`, `Soc`)
- Dice modifier variable: `dm` (not `modifier` or `bonus`)
- Check resolution: method name `check(target: int, dm: int) -> bool`

---

## Technology Stack

### Decision: Python 3.13 + Typer + frozen dataclasses

**Rationale**: Python 3.13 is the current stable release (released Oct 2024, support through Oct 2029). Typer provides a clean nested-command model with no boilerplate. Frozen dataclasses with `slots=True` are the right fit for read-only career config data — no extra dependencies, IDE-navigable, immutable at runtime.

**Alternatives considered**:
- Pydantic `BaseModel` — overkill for static config the codebase controls; adds runtime validation overhead. Worthwhile only if careers are loaded from user-editable YAML files (deferred to future phase).
- `TypedDict` — no attribute access (`.name` vs `["name"]`), no frozen enforcement, no methods.
- Named tuples — positional access becomes brittle as the Career struct grows.

### Decision: Hardcode career data as Python frozen dataclasses (not YAML/JSON)

**Rationale**: Career data is immutable rules, not user configuration. Encoding it in Python gives type-checking, IDE navigation, and zero parsing overhead. YAML/JSON loading is deferred until there is a reason to allow user-defined careers outside source control.

**Alternatives considered**: YAML config files with Pydantic parsing — valid future path if community career packs are desired, but premature for MVP.

---

## CLI Structure

### Decision: `cetools character generate` via Typer `add_typer`

```python
# src/cetools/cli/main.py
import typer
from cetools.cli import character

app = typer.Typer()
app.add_typer(character.app, name="character")
```

```python
# src/cetools/cli/character.py
import typer
from cetools.engine.generator import generate_character

app = typer.Typer(help="Character generation commands")

@app.command()
def generate() -> None:
    """Generate a new Navy character."""
    ...
```

**pyproject.toml entry point**:
```toml
[project.scripts]
cetools = "cetools.cli.main:app"
```

**Rationale**: `add_typer` is the canonical Typer pattern for command groups. The generate command takes no arguments (per spec clarification); the bare `cetools character generate` invocation is the complete MVP CLI interface.

---

## Cepheus Engine SRD Rules

Source: https://evolvedexperiment.github.io/cepheus-srd/character-creation.html#career-tables

### Characteristic Modifier Table

| Score | Modifier |
|-------|----------|
| 0–2 | -2 |
| 3–5 | -1 |
| 6–8 | +0 |
| 9–11 | +1 |
| 12–14 | +2 |
| 15–17 | +3 |
| 18–20 | +4 |
| 21–23 | +5 |
| 24–26 | +6 |
| 27–29 | +7 |
| 30–32 | +8 |
| 33+ | +9 |

Floor modifier is -2 (not -3). Table extends to +9 to support pseudo-hex values up to 33.

### Pseudo-Hexadecimal Notation (canonical table)

Source: https://evolvedexperiment.github.io/cepheus-srd/introduction.html#pseudo-hexadecimal-notation

SRD description: "The pseudohexadecimal notation proceeds as normal for values from 0 to 15, but extends beyond F for 15, with G for 16, etc. The Cepheus Engine skips the use of the letters I and O, because they might be mistaken for the numbers 1 and 0."

**Table: Pseudo-Hexadecimal Notation** (verbatim from SRD)

| Actual Value | PseudoHex | Actual Value | PseudoHex | Actual Value | PseudoHex |
|---|---|---|---|---|---|
| 0 | 0 | 12 | C | 24 | Q |
| 1 | 1 | 13 | D | 25 | R |
| 2 | 2 | 14 | E | 26 | S |
| 3 | 3 | 15 | F | 27 | T |
| 4 | 4 | 16 | G | 28 | U |
| 5 | 5 | 17 | H | 29 | V |
| 6 | 6 | 18 | J | 30 | W |
| 7 | 7 | 19 | K | 31 | X |
| 8 | 8 | 20 | L | 32 | Y |
| 9 | 9 | 21 | M | 33 | Z |
| 10 | A | 22 | N | | |
| 11 | B | 23 | P | | |

`I` (between H and J) and `O` (between N and P) omitted. Total: 34 values (0–33). Confirmed by SRD UPP example `687B9C-4` (scores 6,8,7,11,9,12 → 11=B, 12=C).

### Navy Career Rolls

| Roll | Characteristic | Target |
|------|---------------|--------|
| Qualification | Intelligence | 6+ |
| Survival | Intelligence | 5+ |
| Commission | Social Standing | 7+ |
| Advancement | Education | 6+ |
| Re-enlistment | — | 5+ |

### Navy Rank Table

| Rank | Title | Bonus Skill |
|------|-------|-------------|
| 0 | Starman | Zero-G-1 |
| 1 | Midshipman | — |
| 2 | Lieutenant | — |
| 3 | Lt Commander | Tactics-1 |
| 4 | Commander | — |
| 5 | Captain | — |
| 6 | Commodore | — |

Rank 0 (Starman) bonus Zero-G-1 is granted at enlistment. Rank 3 (Lt Commander) grants Tactics-1 on promotion.

### Navy Skill Tables (roll 1D6; result maps to row index: roll 1 → index 0)

**Personal Development**

| Roll | Result |
|------|--------|
| 1 | +1 Str |
| 2 | +1 Dex |
| 3 | +1 End |
| 4 | +1 Int |
| 5 | +1 Edu |
| 6 | Melee Combat |

**Service Skills**

| Roll | Result |
|------|--------|
| 1 | Comms |
| 2 | Engineering |
| 3 | Gun Combat |
| 4 | Gunnery |
| 5 | Melee Combat |
| 6 | Vehicle |

**Specialist Skills**

| Roll | Result |
|------|--------|
| 1 | Gravitics |
| 2 | Jack o' Trades |
| 3 | Melee Combat |
| 4 | Navigation |
| 5 | Leadership |
| 6 | Piloting |

**Advanced Education (requires Education 8+)**

| Roll | Result |
|------|--------|
| 1 | Advocate |
| 2 | Computer |
| 3 | Engineering |
| 4 | Medicine |
| 5 | Navigation |
| 6 | Tactics |

### Navy Mustering-Out Tables

Both tables have 7 rows. Row 7 is reachable via high rank or Gambling skill DM.

**Cash Benefits**

| Roll | Credits |
|------|---------|
| 1 | Cr1,000 |
| 2 | Cr5,000 |
| 3 | Cr10,000 |
| 4 | Cr10,000 |
| 5 | Cr20,000 |
| 6 | Cr50,000 |
| 7 | Cr50,000 |

**Material Benefits**

| Roll | Benefit |
|------|---------|
| 1 | Low Passage |
| 2 | +1 Edu |
| 3 | Weapon |
| 4 | Mid Passage |
| 5 | +1 Soc |
| 6 | High Passage |
| 7 | Explorer's Society |

### Aging Table

Aging check triggers at the end of each term starting at term 4 (age 34+). Roll 2D6 and apply a negative DM equal to total terms served.

| Modified 2D6 | Effect |
|--------------|--------|
| -6 or less | Reduce three physical stats by 2; reduce one mental stat by 1 |
| -5 | Reduce three physical stats by 2 |
| -4 | Reduce two physical stats by 2; reduce one physical stat by 1 |
| -3 | Reduce one physical stat by 2; reduce two physical stats by 1 |
| -2 | Reduce three physical stats by 1 |
| -1 | Reduce two physical stats by 1 |
| 0 | Reduce one physical stat by 1 |
| 1+ | No effect |

Physical stats: Strength, Dexterity, Endurance. Player distributes reductions. If any stat reaches 0: aging crisis (pay 1D6×Cr10,000 for medical care or die; restored to 1 if paid). In MVP (no player input mid-generation), apply reductions in order: Strength, then Dexterity, then Endurance.

### Background Skills

Count: 3 + Education DM. MVP simplification: fixed 3 skills at Level 0 from the primary education list; full homeworld generation (first two picks from homeworld/trade code tables) is deferred.

Primary education list: Admin, Advocate, Animals, Carousing, Comms, Computer, Electronics, Engineering, Life Sciences, Linguistics, Mechanics, Medicine, Physical Sciences, Social Sciences, Space Sciences (all at Level 0).

### Retirement Pension

5+ terms in a single career:

| Terms | Annual Pension |
|-------|----------------|
| 5 | Cr10,000 |
| 6 | Cr12,000 |
| 7 | Cr14,000 |
| 8 | Cr16,000 |
| 9+ | +Cr2,000 per additional term beyond 8 |

### Mustering-Out Benefit Count

- Base: 1 roll per completed term
- Maximum 3 rolls on Cash table; excess must be Material
- Rank bonuses: O4 (Commander, Rank 4) +1, O5 (Captain, Rank 5) +2, O6 (Commodore, Rank 6) +3

---

## Discrepancies: Spec vs. SRD

The following spec FRs contain values that conflict with the SRD. **SRD is authoritative** (per Assumption in spec). Implementation MUST follow SRD values.

| FR | Spec (incorrect) | SRD (correct) |
|----|-----------------|---------------|
| FR-004 | Enlistment: Endurance 5+ | Qualification: Intelligence 6+ |
| FR-005 | Commission: Education 6+ | Commission: Social Standing 7+ |
| FR-005 | Advancement: Education 7+ | Advancement: Education 6+ |
| FR-006 | Ranks "Ensign through Fleet Admiral" | Ranks Starman (0) through Commodore (6) |
| FR-006 | Leadership-1 at "Rank 3/Captain" | Tactics-1 at Rank 3 (Lt Commander); no bonus at Captain (Rank 5) |

These corrections do not change the feature's scope or acceptance criteria — only the rules values.

---

## RNG Injection Pattern

Per spec clarification: "deterministic testing is achieved via RNG injection at the library layer." The generation engine accepts a `DiceRoller` protocol instance, defaulting to `random.randint`. Tests inject a controlled implementation.

```python
from typing import Protocol

class DiceRoller(Protocol):
    def roll(self, sides: int, count: int = 1) -> int:
        """Return the sum of `count` dice, each with `sides` faces."""
```
