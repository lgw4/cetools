# Contract: CLI (`cetools ship`)

A Typer sub-app in `src/cetools/cli/ship.py`, registered in `cli/main.py` as `ship`. Pure I/O
routing: parse args / read TOML → call `cetools.engine.ships` → write stdout. No game logic
(Principle III).

## `cetools ship build`—build a ship from a TOML design file

| Argument / Option | Type | Default | Meaning |
|-------------------|------|---------|---------|
| `FILE` | path (positional) | (required) | TOML design file to build (FR-021) |
| `--toml` | flag | off | Emit the built ship as a TOML design file to stdout instead of a sheet |
| `--out` | path | none | Write the emitted TOML to a file (with `--toml`) |

**Behavior**: reads the design, calls `build_ship`, and prints the human-readable ship sheet to
stdout (default) or the round-trippable TOML design (`--toml`) (FR-022). Exit 0.

Example:

```text
$ uv run cetools ship build specs/010-starship-generator/examples/free-trader.toml
Ship: Beowulf (standard)
Hull: 200 tons, standard (hull 2)
Drives: Jump-1 (A)  Maneuver-1 (A)  Power-1 (A), 4t power plant
Fuel: 20t jump (assumes range 1), 2t power plant (2 weeks)
Bridge: 10t
Computer: Model/1
Crew: pilot 1, navigator 1, engineers 1, gunners 0, screen operators 0, medic 1, stewards 1 (total 5)
Quarters: 4 staterooms, 0 low berths, 0 emergency low berths
Fittings: fuel_processor x1
Tonnage: 65 used, 135 cargo, hardpoints 0/2
Hull points: 4, Structure points: 4
Cost: MCr29.772, Build time: 44 weeks
```

The same block appears in the README, where `check_docs.py` runs the command and asserts the
output matches, so it cannot drift from the sheet `render_sheet` actually produces.

## `cetools ship generate`—randomly generate a ship

| Option | Type | Default | Meaning |
|--------|------|---------|---------|
| `--hull` | `int` | none | Constrain to a tabulated hull size (100–5,000, or 10–95 with `--small-craft`) (FR-018) |
| `--small-craft` | flag | off | Generate under the small-craft ruleset (FR-019) |
| `--toml` | flag | off | Emit the generated ship as a TOML design file instead of a sheet (FR-023) |
| `--out` | path | none | Write the emitted TOML to a file (with `--toml`) |
| `--seed` | `int` | none | Seed for reproducible output (FR-017) |

**Behavior**: builds a random rules-legal ship through the engine and prints its sheet (default) or
its round-trippable TOML (`--toml`). When `--seed` is omitted, the chosen seed is reported **on
stderr** so the run can be reproduced; stdout carries only the sheet, which `render_sheet` derives
from the `Ship` alone and which therefore never contains the seed. Exit 0.

Example (sheets abridged to their first lines; the full sheet has the same sections as `build`):

```text
$ uv run cetools ship generate --seed 42
Ship: Unnamed Ship (custom)
Hull: 400 tons, distributed (hull 4)
...

$ uv run cetools ship generate     # seed chosen for you, reported on stderr
seed: 8613427                      # stderr
Ship: Unnamed Ship (custom)        # stdout
...
```

## Error handling

| Condition | Exit | stderr |
|-----------|------|--------|
| Design file not found / unreadable | 1 | `"cannot read design file: <path>"` |
| Malformed TOML or schema-invalid design | 1 | The `ValueError` message from `load_design` (shape errors only) |
| Rules-illegal design (e.g. over-allocation) | 1 | The `ValueError` message from `build_ship` (names the violated rule) |
| Invalid `--hull` value | 1 | Typer validation / `ValueError` listing valid sizes |
| `--out` without `--toml` | 1 | `"--out requires --toml"` |

Success always exits 0; any user-facing failure (bad input or a rules-illegal design) exits 1—
analogous to the character generator's enlistment-failure exit (Principle III).

## Registration

`cli/main.py` gains `from cetools.cli import ship` and `app.add_typer(ship.app, name="ship")`,
alongside the existing `character` and `world` sub-apps. The root callback help text is updated to
mention ship design.
