# CLI Contract: cetools character generate

**Version**: MVP | **Date**: 2026-06-17 | **Spec**: [spec.md](../spec.md)
**Rules Source**: https://evolvedexperiment.github.io/cepheus-srd/

---

## Command

```
cetools character generate
```

No subcommands, no options, no arguments for MVP. The complete invocation is the bare command above.

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Character generated successfully |
| 1 | Generation failed (enlistment rejected or character died) |

---

## Standard Streams

### On success (exit 0)

**stdout**: A plain-text formatted character record. **stderr**: Empty.

Example output:

```
UPP: 7A6B85

Navy (Commodore, Rank 6) — 7 terms, age 46

Characteristics:
  Strength:        7
  Dexterity:      10 (A)
  Endurance:       6
  Intelligence:   11 (B)
  Education:       8
  Social Standing: 5

Skills:
  Engineering-2, Gunnery-1, Navigation-2, Tactics-1, Zero-G-1

Mustering-Out Benefits:
  Cash:     Cr50,000, Cr20,000, Cr10,000
  Material: High Passage, +1 Edu, Explorer's Society, Mid Passage

Retirement Pension: Cr14,000/year
```

The exact formatting is not contractually fixed for MVP; the above illustrates required content. The content contract is:
- UPP string (6 pseudo-hex characters) on first line or clearly labeled
- Career name, final rank title, total terms served, and final age
- All six characteristics by name and value (with pseudo-hex encoding if value > 9)
- All skills with their levels
- All mustering-out benefits (cash amounts in Credits, material benefit names)
- Retirement pension if applicable

### On failure (exit 1)

**stdout**: Empty (no character record).

**stderr**: One line describing the failure cause.

| Failure scenario | stderr message |
|-----------------|----------------|
| Enlistment failed | `Navy enlistment failed.` |
| Survival roll failed in term N | `Character died during term N survival check.` |

---

## Library Contract

The CLI is a thin wrapper over the generation library. The library is the primary interface for testing and future delivery layers.

```python
# Public API: src/cetools/engine/generator.py

from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.generator import generate_character
from cetools.engine.dice import DiceRoller

result: Character | GenerationFailure = generate_character(
    career=NAVY_CAREER,
    roller=DiceRoller(),       # inject a deterministic mock for tests
)
```

`generate_character` is a pure function: given a `Career` and a `DiceRoller`, it returns either a fully-formed `Character` or a `GenerationFailure`. It has no I/O side effects, no global state.

The `DiceRoller` protocol:
```python
class DiceRoller(Protocol):
    def roll(self, sides: int, count: int = 1) -> int:
        """Return the sum of `count` dice, each with `sides` faces."""
```

The default `DiceRoller` uses `random.randint`. Tests inject a deterministic implementation.
