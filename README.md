# cetools

Cepheus Engine character generation tools. Generates playable characters following the [Cepheus Engine SRD](https://evolvedexperiment.github.io/cepheus-srd/) rules.

Supported careers: **Navy**, **Scout**.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)

## Installation

```bash
git clone <repo>
cd cetools
uv sync
```

## Usage

### CLI

Generate a character for a specific career:

```bash
uv run cetools character generate --career navy
uv run cetools character generate --career scout
```

Omit `--career` to let the draft table assign one randomly:

```bash
uv run cetools character generate
```

Example output (Navy):

```
UPP: 95AB75

Navy (Commander, Rank 4) — 5 terms, age 38

Characteristics:
  Strength: 9
  Dexterity: 5
  Endurance: 10 (A)
  Intelligence: 11 (B)
  Education: 7
  Social Standing: 5

Skills:
  Admin-0, Advocate-0, Animals-0, Comms-0, Engineering-3, Gun Combat-0, Gunnery-1, Melee Combat-1, Tactics-1, Vehicle-0, Zero-G-1

Mustering-Out Benefits:
  Cash:     Cr20,000, Cr10,000, Cr10,000
  Material: High Passage, Low Passage, Weapon

Retirement Pension: Cr10,000/year
```

Example output (Scout, drafted):

```
UPP: 7A8965

Scout (Drafted) (Scout, Rank 0) — 3 terms, age 30

Characteristics:
  Strength: 7
  Dexterity: 10 (A)
  Endurance: 8
  Intelligence: 9
  Education: 6
  Social Standing: 5

Skills:
  Advocate-0, Animals-0, Comms-1, Electronics-0, Gun Combat-0, Gunnery-0, Navigation-1, Piloting-1, Recon-0

Mustering-Out Benefits:
  Cash:     Cr5,000, Cr1,000, Cr10,000
  Material: Weapon
```

**Exit codes**: `0` on success, `1` if the character died, generation failed, or an unknown `--career` value was given (reason written to stderr).

Characteristic values above 9 are shown in [pseudo-hex notation](https://evolvedexperiment.github.io/cepheus-srd/introduction.html#pseudo-hexadecimal-notation) — `A`=10, `B`=11, … skipping `I` and `O`.

### Library

The generation engine is usable directly without the CLI.

Generate a character for a specific career (re-rolls characteristics until the career qualifies, enforces a hard 7-term cap):

```python
from cetools.engine.generator import generate_career_character
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER
from cetools.engine.models import Character, GenerationFailure

result = generate_career_character(NAVY_CAREER)

if isinstance(result, Character):
    print(f"UPP: {result.upp}  Career: {result.career}  Terms: {result.terms_served}")
else:
    print(f"Generation failed: {result.reason}")
```

Generate a draft character (career assigned by 1D6 roll against the draft table):

```python
from cetools.engine.generator import draft_character

result = draft_character()
if isinstance(result, Character):
    print(f"Career: {result.career}  Drafted: {result.drafted}")
```

Use the career registry to look up a career by name:

```python
from cetools.engine.careers import CAREER_REGISTRY

career = CAREER_REGISTRY["scout"]  # or "navy"
```

Inject a custom `DiceRoller` for deterministic results:

```python
from cetools.engine.generator import generate_career_character
from cetools.engine.careers.scout import SCOUT_CAREER

class FixedRoller:
    def roll(self, sides: int, count: int = 1) -> int:
        return count * 4  # always rolls 4 per die

result = generate_career_character(SCOUT_CAREER, roller=FixedRoller())
```
