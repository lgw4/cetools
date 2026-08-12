# cetools

A dice and task-check engine for Cepheus Engine SRD-based games: seeded,
reproducible dice throws and 2D6 task resolution, available as a Python
library and as the `cetools` command-line tool.

## Installation

Requires Python 3.13 or newer.

```sh
uv add cetools
```

Or, from a source checkout:

```sh
uv sync
```

## Usage

```sh
$ cetools roll 2d6+1 --seed session-alpha
2d6+1 = 7
  Dice:     1, 5 (sum 6)
  Modifier: +1
  Seed:     14333185781139156525

$ cetools roll d66 --seed session-alpha
d66 = 15
  Dice: 1, 5
  Seed: 14333185781139156525

$ cetools check --difficulty Difficult --characteristic 9 --skill 2 \
    --dm "cover=-2" --seed session-alpha
Check: FAILURE
  Dice:  1, 5 (sum 6)
  Modifiers:
    Difficulty (Difficult) -2
    Characteristic 9       +1
    Skill 2                +2
    cover                  -2
  Total: 5 vs target 8
  Seed:  14333185781139156525
```

Both commands accept `--json` for machine-readable output, and either
prints the seed it used (fresh, if none was given), so any result is
reproducible from `--seed <that seed> --json` given the same package
version.

## Development

```sh
uv sync
uv run pytest
```

See `CONTRIBUTING.md` for the workflow, the testing rules, and the
licensing constraints on new files, and `CHANGELOG.md` for release history.

## Licensing

This repository carries two licenses. `src/cetools/data/tasks.toml` is Open
Game Content under the Open Game License v1.0a (see `LICENSE-OGL.txt`).
Everything else — the library and CLI source, tests, and packaging — is
licensed under the GNU General Public License v3.0 (see `LICENSE`).
