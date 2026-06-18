# cetools

Cepheus Engine character generation tools. Generates playable Navy characters following the [Cepheus Engine SRD](https://evolvedexperiment.github.io/cepheus-srd/) rules.

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

Generate a Navy character and print a formatted record to stdout:

```bash
uv run cetools character generate
```

Example output:

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

**Exit codes**: `0` on success, `1` if the character died or failed enlistment (reason written to stderr).

Characteristic values above 9 are shown in [pseudo-hex notation](https://evolvedexperiment.github.io/cepheus-srd/introduction.html#pseudo-hexadecimal-notation) — `A`=10, `B`=11, … skipping `I` and `O`.

### Library

The generation engine is usable directly without the CLI:

```python
from cetools.engine.generator import generate_character
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.models import Character, GenerationFailure

result = generate_character(NAVY_CAREER)

if isinstance(result, Character):
    print(f"UPP: {result.upp}  Rank: {result.rank_title}  Terms: {result.terms_served}")
else:
    print(f"Generation failed: {result.reason}")
```

`generate_character` is a pure function with no I/O side effects. Inject a custom `DiceRoller` for deterministic results:

```python
from cetools.engine.dice import DiceRoller
from typing import Protocol

class FixedRoller:
    def roll(self, sides: int, count: int = 1) -> int:
        return count * 4  # always rolls 4 per die

result = generate_character(NAVY_CAREER, roller=FixedRoller())
```
