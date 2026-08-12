# Contract: `cetools/data/tasks.toml`

**Feature**: `001-dice-task-engine`

The shipped rules data. Per Principle V, none of these values may appear in engine
code. Editing this file changes the engine's arithmetic with no code change
(SC-010).

## File content

```toml
# Open Game Content per OGL 1.0a; see LICENSE-OGL.txt
#
# Core task resolution parameters.

[task]
roll = "2d6"
target = 8
unskilled-dm = -3

[difficulty-dms]
"Simple" = 6
"Easy" = 4
"Routine" = 2
"Average" = 0
"Difficult" = -2
"Very Difficult" = -4
"Formidable" = -6

[characteristic-dms]
"0-2" = -2
"3-5" = -1
"6-8" = 0
"9-11" = 1
"12-14" = 2
"15-17" = 3
"18-20" = 4
"21-23" = 5
"24-26" = 6
"27-29" = 7
"30-32" = 8
"33+" = 9
```

## Notes on each part

**`task.roll`** is dice notation parsed by the same grammar `cetools roll` uses.
The check's own dice therefore come from data rather than being hard-coded as
`2d6` in the engine, so a referee can house-rule the core throw.

**`task.target`** is the flat target. Success is `total >= target`. Difficulty is a
modifier to the roll, never a shift in this number (FR-014).

**`task.unskilled-dm`** applies when no skill level is supplied. A skill at level 0
applies nothing instead, which is a different case.

**`[difficulty-dms]`** is the full seven-rung ladder. The prototype sketch in the
project's decision notes omits `Simple`; that is corrected here. Order in the file
is preserved on load and is the order used when an error message lists valid names.

The entry whose value is `0` is the default difficulty when the referee names none
(FR-014). It is found by its value, not by its name or its position, so a
house-ruled ladder of a different length or with renamed rungs still has a
well-defined default. Exactly one rung may be `0`; a file with none or with several
is rejected, because the default would otherwise be undefined or arbitrary.

**`[characteristic-dms]`** is a range table rather than the equivalent
`floor(score / 3) - 2` formula. A formula in code would foreclose exactly the
substitution Principle V exists to enable: a referee house-ruling a flatter or
steeper curve. Twelve bands, ending in an unbounded `33+`. The prototype truncates
at `15+`; that is corrected here.

## Key grammar for band keys

```
BAND := digits "-" digits     inclusive range
      | digits "+"            unbounded upper end
```

## Validation performed on load

Deliberately minimal. Feature 2 (`rules-data-loading`) owns schema validation and
will **replace** this, not extend it.

| Check | Failure |
|---|---|
| `[task]`, `[difficulty-dms]`, `[characteristic-dms]` all present | `RulesDataError` |
| `task.roll` is a string that parses as dice notation | `RulesDataError` |
| `task.target` and `task.unskilled-dm` are integers | `RulesDataError` |
| Every difficulty value is an integer | `RulesDataError` |
| Exactly one difficulty value is zero (this rung is the default, per FR-014) | `RulesDataError` |
| Every band key matches the grammar above | `RulesDataError` |
| Every band value is an integer | `RulesDataError` |
| Exactly one band is unbounded | `RulesDataError` |
| File missing or not valid TOML | `RulesDataError` |

There is no fallback to built-in defaults for any failure (FR-024). Gap and overlap
detection across bands is **not** performed here; a score falling in a gap raises
`RulesDataError` at lookup time instead. Full coverage checking belongs to feature 2.

## Licensing

The file opens with its Open Game Content designation, per the constitution's
Licensing and Distribution Constraints. The Product Identity strings "Cepheus
Engine" and "Samardan Press" must not appear in it. Bundling the full OGL 1.0a
text, the Section 15 chain, and the compatibility statement is the
`packaging-release` feature's job; only the per-file designation is in scope here.

## Packaging

Shipped inside the wheel at `cetools/data/tasks.toml` and read through
`importlib.resources.files("cetools.data")`, so it resolves correctly from a wheel,
a zipapp, or a source checkout. `cetools/data/__init__.py` exists so the directory
is an importable package.
