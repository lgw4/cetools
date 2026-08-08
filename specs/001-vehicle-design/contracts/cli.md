# Contract: the `cetools vehicle` command group

**Feature**: `001-vehicle-design` | **Date**: 2026-08-07

Registered in `src/cetools/cli/main.py` alongside `character`, `world` and `ship`, singular to match
them (FR-024). Implemented in `src/cetools/cli/vehicle.py`, which contains no rules logic: it parses
arguments, calls the engine, formats output and picks an exit code.

## `cetools vehicle build`

Build a vehicle from a TOML design file or from the installed catalog, and print its description.

| Argument or option | Type | Default | Meaning |
|---|---|---|---|
| `FILE` | path, positional, optional | n/a | Path to a TOML vehicle design file. |
| `--catalog NAME` | str | none | Build an installed catalog vehicle by name instead of a file. |
| `--table` | flag | off | Print the component table beneath the description. |
| `--toml` | flag | off | Emit round-trippable TOML instead of a description. |
| `--out PATH` | path | none | Write output to a file instead of stdout. |

Argument rules, all checked at the top of the command body before any engine call:

- Exactly one of `FILE` and `--catalog` is required. Neither, or both, exits 1 with a message
  naming the two ways in.
- `--out` requires `--toml`, reusing the existing message verbatim: `--out requires --toml`.
- `--table` with `--toml` exits 1: they are different representations of the same vehicle (FR-025a).

## `cetools vehicle generate`

Generate a rules-legal vehicle from a seed and print its description. Non-interactive: there is no
`--interactive` flag and no wizard (FR-027).

| Option | Type | Default | Meaning |
|---|---|---|---|
| `--seed N` | int | drawn | Seed for reproducible output. |
| `--tech-level N` | int | none | Constrain to a tech level. |
| `--chassis CODE` | str | none | Constrain to a chassis code. |
| `--locomotion NAME` | str | none | Constrain to a propulsion table name or a coarse alias. |
| `--table` | flag | off | As `build`. |
| `--toml` | flag | off | As `build`. |
| `--out PATH` | path | none | As `build`. |

The same `--out`/`--toml` and `--table`/`--toml` rules apply.

## `cetools vehicle catalog`

List the fifteen installed catalog vehicles by name, one per line, on stdout. No options. This is
what makes `--catalog` usable by a referee who knows no file paths (FR-024a).

## Output contract

**stdout carries the artifact and nothing else.** One of: the Universal Vehicle Description Format
paragraph; that paragraph followed by the component table when `--table` is given; round-trippable
TOML when `--toml` is given; the catalog listing. When `--out` is given, stdout stays empty.

**stderr carries everything else.** Diagnostics, the auto-chosen seed, and the unmet-constraint
report. This is the existing stream discipline and `tests/test_cli.py` already asserts it as a rule
in its own right.

## Exit codes

| Code | When |
|---|---|
| 0 | A vehicle was produced, including when constraints could not all be honored. |
| 1 | Argument rules violated; the design file cannot be read; the engine raised `ValueError`. |

Engine errors are `ValueError` and are printed as `str(exc)` verbatim on stderr, unwrapped: the
builder's messages already name the rule and the offending numbers, so the CLI adds nothing. A file
that cannot be read is reported as `cannot read design file: {path}`, matching `cetools ship build`.

## Unmet constraints

When generation could not honor a constraint, the report goes to **stderr** and the exit code stays
**0**, because a vehicle really was produced and must still pipe (FR-032). The shape mirrors
`cetools ship generate`:

```text
could not honor 1 constraint(s):
  locomotion: asked grav, got wheeled (no grav propulsion at TL5)
```

## Seeding

An omitted `--seed` is drawn and echoed to stderr as `seed: {seed}`, so an unseeded run stays
reproducible after the fact. The same seed and the same constraints produce byte-identical stdout
(FR-031), with the documented caveat inherited from ships: a pinned constraint consumes no dice, so
two runs on one seed diverge below the first pin, and only the unconstrained sequence is byte-stable
across changes.

## What this group does not have

No `--interactive`, no wizard, no name generation, no watercraft, no vehicles over 20 tons. Those
last two are rejected at build with **separate messages**, each naming only the limit it hit: an
oversized design is told that vehicles over 20 tons are not yet supported, and is told nothing about
watercraft support it never asked for; a design naming a watercraft-only component is told that
watercraft are not supported, and which component gave it away (FR-013, SC-005).
