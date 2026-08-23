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

`roll`, `check`, `validate`, and `npc` all accept `--json` for
machine-readable output, and `roll`, `check`, and `npc` each print the seed
used (fresh, if none was given), so any result is reproducible from
`--seed <that seed> --json` given the same package version. `cetools
--version` prints the installed package version.

`cetools npc` walks the source material's lifepath end to end and prints
the Universal Character Format — the source material's own sheet, tab
separated — to standard output, with the seed and provenance on standard
error so a redirected sheet is exactly a sheet and nothing else:

```sh
$ cetools npc --seed session-alpha
Lieutenant Darrell Soyinka	687A68	Age 30
Aerospace Defense (2 terms), Surface Defense (1 term)	Cr5,000
Animals-0, Electronics-0, Flyer-1, Gun Combat (Archery)-1, Gun Combat (Energy Pistol)-0, Gunnery (Screens)-0, Jack-of-All-Trades-0, Mechanic-0, Melee Combat (Bludgeoning Weapons)-1, Navigation-0, Vehicle (Aircraft)-0, Vehicle (Watercraft)-1
Mid Passage, Weapon
```

The character is always alive, always named, and always internally
consistent; nothing is discarded and re-rolled. `--full` adds the
outstanding debt, the pension, and the generation history — one line per
step, composed from the step's own kind, career, term, throw, and effects
— so a surprising sheet is diagnosed from output rather than a debugger.
`--json` emits the same character as a machine-readable document instead,
with the seed and provenance in the document rather than on standard
error; the two options combine without conflict. `--count N` generates
`N` characters from the same seed, one blank line between consecutive
sheets:

```sh
$ cetools npc --seed table-of-twelve --count 3
Scout Bennette Kalama	5887BA	Age 22
Scout (1 term)	Cr20,000
Advocate-0, Electronics-1, Gambler-0, Gun Combat (Archery)-0, Gunnery (Turret Weapons)-0, Mechanic-0, Medicine-0, Navigation-0, Piloting-0, Survival-1, Vehicle (Tracked Vehicle)-0

Flight Lieutenant Quinn Yoon	68A868	Age 22
Aerospace Defense (1 term)	Cr0
Admin-0, Electronics-0, Flyer-1, Gun Combat (Energy Rifle)-0, Gunnery (Spinal Mounts)-0, Gunnery (Turret Weapons)-1, Mechanic-0, Vehicle (Tracked Vehicle)-0, Vehicle (Wheeled Vehicle)-0
Personal Vehicle

Captain Kim Davis	9A6636	Age 26
Marine (2 terms)	Cr15,000
Athletics-0, Gun Combat (Energy Rifle)-0, Gun Combat (Slug Pistol)-0, Gun Combat (Slug Rifle)-1, Melee Combat (Piercing Weapons)-1, Melee Combat (Slashing Weapons)-0, Recon-1, Vehicle (Tracked Vehicle)-0, Zero-G-0
```

A batch of one is byte-identical to the single character of that seed, and
the same seed reproduces the whole batch: quoting a batch member's own
seed (printed with `--json`) back to `--seed` regenerates that one person
alone. `--name` supplies a name verbatim instead of rolling one, and
changes nothing else about the character the seed produces; it cannot be
combined with `--count` above 1, since a personal name names one
character.

`check` resolves against the rules data packaged with `cetools`: a task
definition, three registries of names, the universal chargen tables, eight
careers, and the name tables the NPC generator draws from. `cetools
validate` checks that data set, or a house rule composed over it, and
reports every problem it finds in one run:

```sh
$ cetools validate
Rules data is valid.
  Files: 26
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
