# Contract: CLI (`cetools world`)

A Typer sub-app in `src/cetools/cli/world.py`, registered in `cli/main.py` as `world`. Pure I/O
routing: parse args → call `cetools.engine.worlds` → write stdout. No game logic (Principle III).

## `cetools world generate`—one or more fully-described systems

| Option | Type | Default | Meaning |
|--------|------|---------|---------|
| `--name` | `str` | none | Override the generated world name (only meaningful with `--count 1`) |
| `--count`, `-n` | `int ≥ 1` | 1 | Number of systems to generate |
| `--allegiance` | `str` | `Na` | Allegiance stamped on each system |
| `--seed` | `int` | none | Seed for reproducible output |

**Behavior**: prints one full world-data line per system to stdout. Exit 0.

Example:

```text
$ cetools world generate --seed 42
Veltura       A867A9C-F  N  Ag Ni  A  234  Na
```

## `cetools world subsector`—an 8×10 region

| Option | Type | Default | Meaning |
|--------|------|---------|---------|
| `--density` | choice: `rift\|sparse\|standard\|dense` | `standard` | World-presence density |
| `--seed` | `int` | none | Seed for reproducible output |

**Behavior**: prints one world-data line per occupied hex (ordered by hex coordinate), each prefixed
by its `CCRR` hex. Exit 0.

Example:

```text
$ cetools world subsector --density sparse --seed 7
0102  Karnas     C7A5410-8     S  Ni  A  102  Na
0105  Dramio     X431220-6         Lo Po     101  Na
...
```

## Error handling

| Condition | Exit | stderr |
|-----------|------|--------|
| Invalid `--density` value | 1 | Typer usage error listing valid choices |
| `--count < 1` | 1 | Typer validation error |
| `--name` with `--count > 1` | 1 | "`--name` applies only to a single world (use --count 1)." |

Success always exits 0 (world generation has no in-domain failure like character death).

## Registration

`cli/main.py` gains `app.add_typer(world.app, name="world")`, alongside the existing `character`
sub-app. The root callback help text is updated to mention world generation.
