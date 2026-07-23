# Contract: CLI (`cetools ship`)

A Typer sub-app in `src/cetools/cli/ship.py`, registered in `cli/main.py` as `ship`. Pure I/O
routing: parse args / read TOML → call `cetools.engine.ships` → write stdout. No game logic
(Principle III).

## `cetools ship build`—build a ship from a TOML design file

| Argument / Option | Type | Default | Meaning |
|-------------------|------|---------|---------|
| `FILE` | path (positional) | — | TOML design file to build (FR-021) |
| `--toml` | flag | off | Emit the built ship as a TOML design file to stdout instead of a sheet |
| `--out` | path | none | Write the emitted TOML to a file (with `--toml`) |

**Behavior**: reads the design, calls `build_ship`, and prints the human-readable ship sheet to
stdout (default) or the round-trippable TOML design (`--toml`) (FR-022). Exit 0.

Example:

```text
$ cetools ship build free-trader.toml
Ship: Beowulf (custom)
Hull: 200 tons, streamlined (hull 2)   Hull/Structure: 4/4
Drives: Jump-1 (A)  Maneuver-1 (A)  Power-1 (A)
...
Tonnage: 191 used / 9 cargo            Cost: MCr 61.06        Build: 44 weeks
```

## `cetools ship generate`—randomly generate a ship

| Option | Type | Default | Meaning |
|--------|------|---------|---------|
| `--hull` | `int` | none | Constrain to a hull size (100–5,000, or 10–95 with `--small-craft`) (FR-018) |
| `--small-craft` | flag | off | Generate under the small-craft ruleset (FR-019) |
| `--toml` | flag | off | Emit the generated ship as a TOML design file instead of a sheet (FR-023) |
| `--out` | path | none | Write the emitted TOML to a file (with `--toml`) |
| `--seed` | `int` | none | Seed for reproducible output (FR-017) |

**Behavior**: builds a random rules-legal ship through the engine and prints its sheet (default) or
its round-trippable TOML (`--toml`). When `--seed` is omitted, the chosen seed is reported (to stderr)
so the run can be reproduced. Exit 0.

Example:

```text
$ cetools ship generate --seed 42
Ship: (generated, seed 42)
Hull: 400 tons, standard (hull 4)  ...
```

## Error handling

| Condition | Exit | stderr |
|-----------|------|--------|
| Design file not found / unreadable | 1 | `"cannot read design file: <path>"` |
| Malformed TOML or schema-invalid design | 1 | The `ValueError` message from `load_design` |
| Rules-illegal design (e.g. over-allocation) | 1 | The `ValueError` message from `build_ship` (names the violated rule) |
| Invalid `--hull` value | 1 | Typer validation / `ValueError` listing valid sizes |
| `--out` without `--toml` | 1 | `"--out requires --toml"` |

Success always exits 0; any user-facing failure (bad input or a rules-illegal design) exits 1—
analogous to the character generator's enlistment-failure exit (Principle III).

## Registration

`cli/main.py` gains `from cetools.cli import ship` and `app.add_typer(ship.app, name="ship")`,
alongside the existing `character` and `world` sub-apps. The root callback help text is updated to
mention ship design.
