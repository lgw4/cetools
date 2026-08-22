# cetools

A dice and task-check engine for SRD-derived 2D6 roleplaying rules: seeded,
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
  Rules: packaged (cetools 2026.8.1)
```

`roll`, `check`, and `validate` all accept `--json` for machine-readable
output, and `roll` and `check` each print the seed used (fresh, if none was
given), so any result is reproducible from `--seed <that seed> --json` given
the same package version. `cetools --version` prints the installed package
version.

`check` resolves against the rules data packaged with `cetools`: a task
definition, three registries of names, the universal chargen tables, and
eight careers. `cetools validate` checks that data set, or a house rule
composed over it, and reports every problem it finds in one run:

```sh
$ cetools validate
Rules data is valid.
  Files: 18
  Rules: packaged (cetools 2026.8.1)
```

A house rule is a directory or a single file, named on the command line and
composed over the packaged data by filename; nothing else changes:

```sh
$ cetools check --seed session-alpha --rules-data ./house-rules
...
  Rules: overridden (cetools 2026.8.1)
    navy.toml   replaced  sha256:3b1f...c0
```

`cetools validate ./house-rules` checks a house rule to the same standard as
the packaged data before it ever reaches a result, and reports which file
took effect and its fingerprint, so a result can always be traced back to
what produced it.

## Development

```sh
uv sync
uv run pytest
```

See `CONTRIBUTING.md` for the workflow, the testing rules, and the
licensing constraints on new files, and `CHANGELOG.md` for release history.

## Licensing

This repository carries two licenses. Every `.toml` file under
`src/cetools/data/registries/`, `src/cetools/data/chargen/`, and
`src/cetools/data/careers/`, plus `src/cetools/data/tasks.toml` itself — the
rules data, which ships as `cetools/data/` in an installed package — is Open
Game Content under the Open Game License v1.0a (see `LICENSE-OGL.txt`).
Every `.toml` file under `src/cetools/data/names/` is this project's own
content, not Open Game Content, and is licensed GPL-3.0-only along with
everything else — the library and CLI source, the `__init__.py` that makes
the data directory importable, tests, and packaging — under the GNU General
Public License v3.0 (see `LICENSE`).

A house rule supplied through `--rules-data` or `cetools validate PATH`
carries no such obligation: it is your own content, not something this
project distributes.
