# Quickstart Validation Guide: Navy Character Generator

**Phase**: 1 | **Date**: 2026-06-17 | **Spec**: [spec.md](spec.md)

---

## Prerequisites

- Python 3.13+
- `uv` installed
- Repository cloned

## Setup

```bash
uv sync
```

---

## Scenario 1: Successful Character Generation (P1 — core path)

**What it proves**: A complete Navy character is generated with a valid UPP, career history, and mustering-out benefits.

```bash
uv run cetools character generate
```

**Expected**:
- Exit code 0
- stdout contains a 6-character UPP (e.g., `7A6B85`) using only pseudo-hex chars (no `I` or `O`)
- stdout contains "Navy" career name, a rank title from the Navy rank table, terms served, and age
- stdout lists at least one skill
- stdout lists mustering-out benefits
- stderr is empty

---

## Scenario 2: Enlistment Failure (P1 — failure path)

**What it proves**: When the qualification roll fails, the CLI exits with code 1, writes to stderr only, and produces no character output.

Since enlistment is probabilistic, inject a failing roller via the library API:

```python
# validate_enlistment_failure.py
from cetools.engine.generator import generate_character
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.models import GenerationFailure

class AlwaysFailRoller:
    def roll(self, sides: int, count: int = 1) -> int:
        return count  # always rolls minimum

result = generate_character(NAVY_CAREER, roller=AlwaysFailRoller())
assert isinstance(result, GenerationFailure)
assert "enlistment" in result.reason.lower()
print("PASS: enlistment failure handled correctly")
```

```bash
uv run python validate_enlistment_failure.py
```

---

## Scenario 3: Pseudo-Hex Encoding Correctness (SC-002)

**What it proves**: Values above 9 encode to the correct letters; `I` and `O` are never produced.

```bash
uv run pytest tests/test_pseudohex.py -v
```

Expected: all tests pass, covering values 0–33 including boundary cases (9→`9`, 10→`A`, 17→`H`, 18→`J`, 22→`N`, 23→`P`, 33→`Z`).

---

## Scenario 4: Library Independence (SC-005)

**What it proves**: The engine can be called directly without invoking the CLI.

```python
# validate_library_interface.py
from cetools.engine.generator import generate_character
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.models import Character, GenerationFailure

result = generate_character(NAVY_CAREER)
if isinstance(result, Character):
    print(f"Character generated: UPP={result.upp}, Rank={result.rank_title}")
else:
    print(f"Generation failed: {result.reason}")
```

```bash
uv run python validate_library_interface.py
```

Expected: runs without error; prints either a UPP string or a failure reason. No CLI subprocess invoked.

---

## Scenario 5: Extensibility — Adding a Second Career (SC-004)

**What it proves**: A new career can be added with zero changes to the engine.

```python
# validate_extensibility.py
from dataclasses import replace
from cetools.engine.generator import generate_character
from cetools.engine.careers.navy import NAVY_CAREER

# Define a minimal Scout career using the same Career dataclass
from cetools.engine.careers.base import Career, RankEntry
scout_career = replace(
    NAVY_CAREER,
    name="Scout",
    qualification_stat="Intelligence",
    qualification_target=5,
    # ... minimal overrides
)

result = generate_character(scout_career)
print(f"Scout generation result: {result}")
```

```bash
uv run python validate_extensibility.py
```

Expected: the engine processes the Scout career without modification to generator.py.

---

## Automated Test Suite

Run the full suite to validate all rules:

```bash
uv run pytest -v
```

Key test files and what they cover:

| File | Covers |
|------|--------|
| `tests/test_pseudohex.py` | All 34 pseudo-hex mappings, invalid inputs |
| `tests/test_generator.py` | Full generation lifecycle, aging, mustering-out, pension |
| `tests/test_careers.py` | Navy career data structure integrity |
| `tests/test_models.py` | UPP encoding, characteristic modifiers |
| `tests/test_cli.py` | CLI exit codes, stdout/stderr routing |
| `tests/test_formatter.py` | Output contains all required fields |

---

## Linting and Formatting

```bash
uv run black . && uv run flake8 src tests
```

Both must pass before a change is considered complete (per AGENTS.md).
