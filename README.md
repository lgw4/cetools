# cetools

Cepheus Engine character and world generation tools. Generates playable characters and worlds following the [Cepheus Engine SRD](https://evolvedexperiment.github.io/cepheus-srd/) rules.

Supported careers: **Aerospace System Defense**, **Agent**, **Athlete**, **Barbarian**, **Belter**, **Bureaucrat**, **Colonist**, **Diplomat**, **Drifter**, **Entertainer**, **Hunter**, **Marine**, **Maritime System Defense**, **Mercenary**, **Merchant**, **Navy**, **Noble**, **Physician**, **Pirate**, **Rogue**, **Scientist**, **Scout**, **Surface System Defense**, **Technician**. Omit `--career` to have one of the six services (Aerospace System Defense, Marine, Maritime System Defense, Navy, Scout, Surface System Defense) drafted at random; the other careers are selectable with `--career` only.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)

## Installation

```bash
git clone <repo>
cd cetools
uv sync
```

## Usage

### CLI

Generate a character for a specific career:

```bash
uv run cetools character generate --career navy
uv run cetools character generate --career scout
uv run cetools character generate --career marine
uv run cetools character generate --career "aerospace system defense"
```

Career names are case-insensitive. An unknown career suggests the closest match and exits `1`:

```console
$ uv run cetools character generate --career navvy
Unknown career 'navvy'. Did you mean: Navy?
```

Omit `--career` to let the draft table assign one randomly:

```bash
uv run cetools character generate
```

Use `--random` to draw uniformly from all 24 careers instead of the draft table's six services:

```bash
uv run cetools character generate --random
```

Generate several characters at once with `--count`/`-n` (blocks are separated by a blank line):

```bash
uv run cetools character generate --career scout -n 3
```

`--career` and `--random` are mutually exclusive; passing both exits `1`.

#### Output format

Each character prints as a compact block:

- **Line 1**—`Rank Name`, the [UPP](https://evolvedexperiment.github.io/cepheus-srd/introduction.html#universal-personality-profile), and age, tab-separated.
- **Line 2**—career and terms served, then total mustering-out cash, tab-separated.
- **Line 3**—skills, alphabetical.
- **Optional**—a `Psionics:` line of learned talents, alphabetical, when the character is psionic.
- **Optional**—a line of material benefits (repeats collapsed as `Name x N`).
- **Optional**—a final `Mishap:` line when a survival mishap ended the career.

Skills are shown with their level. A skill first gained from a Skills and Training roll starts at level 1; level 0 means the character has the skill but has never rolled it: it came from basic training or from their background.

A term is worth one Skills and Training roll, plus an extra for a commission and another for an advancement. The seven careers with neither check (Athlete, Barbarian, Belter, Drifter, Entertainer, Hunter, Scout) take two rolls every term instead of one.

Example output (Navy, full career; note stat boosts summed as `+2 Edu`):

```text
Captain Taylor Nakamura	364889	Age 46
Navy (7 terms)	Cr25,000
Comms-1, Engineering-1, Gravitics-1, Gun Combat-1, Gunnery-2, Melee Combat-1, Navigation-1, Piloting-1, Streetwise-0, Tactics-1, Vehicle-0, Watercraft-0, Zero-G-1
+1 Soc, +2 Edu, High Passage, Explorers' Society, Weapon
```

Example output (drafted; note repeated benefits collapsed to `(x2)`):

```text
Scout Sam Voss	56B878	Age 46
Scout (7 terms)	Cr70,000
Comms-0, Demolitions-1, Electronics-1, Gun Combat-1, Gunnery-2, Jack o' Trades-1, Medicine-1, Melee Combat-1, Navigation-1, Piloting-1, Recon-0, Survival-0
Courier Vessel, Explorers' Society, Mid Passage (x2)
```

Example output (Marine, career cut short by a mishap):

```text
Trooper Sam Brennan	68185A	Age 20
Marine (0 terms)	Cr0
Battle Dress-0, Comms-0, Demolitions-0, Gun Combat-0, Gunnery-0, Melee Combat-0, Survival-0, Watercraft-0, Zero-G-1
Mishap: Medically discharged, injured (Dexterity -2, Endurance -4, Strength -2), survived an injury crisis; Debt Cr60,000
```

Example output (Navy, psionic):

```text
Commander Taylor Reyes	43AAA6-5	Age 46
Navy (7 terms)	Cr12,000
Advocate-1, Comms-1, Computer-0, Engineering-0, Gun Combat-1, Gunnery-0, Melee Combat-2, Piloting-2, Space Sciences-0, Tactics-1, Vehicle-0, Watercraft-0, Zero-G-1
Psionics: Clairvoyance-0, Telekinesis-0
+1 Edu, +2 Soc, Mid Passage (x2)
```

Characters no longer die during generation. A failed survival roll resolves on the [Survival Mishaps table](https://evolvedexperiment.github.io/cepheus-srd/) and always yields a usable character: an injury, a discharge (honorable, dishonorable, or medical), and sometimes debt. The mishap is summarized on the `Mishap:` line.

Characters are tested for psionics under a cetools house rule layered on the optional [SRD psionics rule](https://evolvedexperiment.github.io/cepheus-srd/): a character must first pass a flat `2D6 ≥ 11` eligibility check to be tested at all (roughly 8% do), which keeps psionic characters a genuine minority. Characters who fail the check, or who roll `Psi` 0, show the bare UPP as before; psionic characters (`Psi ≥ 1`) append it as a hyphenated pseudo-hex suffix, e.g. `5A3B93-6`. Any talents learned during training appear on an optional `Psionics:` line, alphabetical, each at level 0. Psionic training's cash cost and time are abstracted away—mustering-out cash and age are unaffected.

Output above is illustrative; generation is random, so your results will differ.

**Exit codes**: `0` on success; `1` on a usage error (an unknown `--career` value, or `--career` and `--random` together), with the reason on stderr. The CLI generates under the house rules, where generation itself cannot fail.

Characteristic values above 9 are shown in [pseudo-hex notation](https://evolvedexperiment.github.io/cepheus-srd/introduction.html#pseudo-hexadecimal-notation)—`A`=10, `B`=11, … skipping `I` and `O`.

### Library

The generation engine is usable directly without the CLI. There is one entry point:

```python
from cetools.engine.generator import DRAFT, RANDOM, generate
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.models import Character

result = generate(NAVY_CAREER)   # or generate(DRAFT), or generate(RANDOM)

if isinstance(result, Character):
    print(f"UPP: {result.upp}  Career: {result.career.name}  Terms: {result.terms_served}")
else:
    print(f"Generation failed: {result.reason}")
```

The first argument is the **assignment**: a career, `DRAFT` (a 1D6 against the draft table), or `RANDOM` (any career, uniformly). It is also the only thing that decides whether the character is `drafted`.

`generate` returns `Character | GenerationFailure`. A `Character` carries the fields surfaced in output—`name`, `upp`, `age`, `skills`, `benefits`, and (when a survival mishap ended the career) `mishap` and `debt`. It also carries its `Career`, so `character.career.name` and `character.rank_title` come from the career rather than from copies.

Look a career up by whatever a user typed—case, surrounding space, and hyphens-for-spaces all work:

```python
from cetools.engine.careers import CAREERS, UnknownCareer, resolve

career = resolve("Aerospace-System-Defense")

match resolve("nvy"):
    case UnknownCareer(spec, suggestion):
        print(f"No career {spec!r}. Did you mean {suggestion.name}?")   # Navy
    case found:
        print(found.name)
```

`CAREERS` is all 24, in name order. A career has one identity—its name; the lookup key is derived from it.

#### Rules

cetools departs from the SRD in two places, and they travel together as a policy:

```python
from cetools.engine.rules import HOUSE, SRD

generate(NAVY_CAREER)                    # HOUSE, the default
generate(NAVY_CAREER, rules=SRD)
```

| | `HOUSE` (default) | `SRD` |
| --- | --- | --- |
| qualification | characteristics are re-rolled until the career's target is met as a raw number; enlistment cannot fail | rolled once, then a `2D6 + DM ≥ target` check that can fail |
| natural 12 at the 7-term cap | ignored—seven terms is the end | honoured—the character serves an eighth term |

Under `HOUSE`, `generate()` **cannot fail**: characteristics are re-rolled until the career accepts them, and the draft table holds careers rather than names, so there is nothing left to fail at. `GenerationFailure` is an `SRD`-only outcome.

#### Deterministic results

Everything the rules leave to chance goes through one seam. Script rolls by name for reproducible characters:

```python
from cetools.engine.rolls import RollName, ScriptedRolls

rolls = ScriptedRolls(
    checks={RollName.SURVIVAL: [True, False]},   # survive term 1, fail term 2
    two_d6={RollName.CHARACTERISTIC: 10},
    d6={RollName.MISHAP: 4},
)
result = generate(NAVY_CAREER, rolls)
```

Anything left unscripted takes a per-verb default. `RandomRolls` is the production adapter, and `RollName` is the index of every random decision the rules make.

## World generation

Generates worlds, systems, and subsectors following SRD Chapter 12: a single [Universal World Profile](https://evolvedexperiment.github.io/cepheus-srd/introduction.html#universal-personality-profile) (UWP), a fully-described system, or an 8x10 subsector.

### CLI

Generate a fully-described system:

```bash
uv run cetools world generate --seed 42
```

```console
$ uv run cetools world generate --seed 42
Dehi    X553338-2     Lo Lt Po     321  Na
```

Name a single world explicitly, or generate several at once with `--count`/`-n`:

```bash
uv run cetools world generate --name Terra --seed 1
uv run cetools world generate --seed 5 -n 2
```

`--name` applies only to a single world; passing it together with `--count` greater than 1 exits `1`.

Generate an 8x10 subsector—one line per occupied hex, ordered by coordinate, each carrying its four-digit hex code:

```bash
uv run cetools world subsector --seed 7
```

```console
$ uv run cetools world subsector --seed 7
Citifa  0103  D542440-5     Lt Ni Po  A  133  Na
Tici  0106  E546659-5     Ag Lt Ni  A  912  Na
Rino  0109  E120443-9     De Ni Po     311  Na
...
```

Control occupied-hex density with `--density` (rift, sparse, standard, or dense; default standard, roughly 50% occupied):

```bash
uv run cetools world subsector --density dense --seed 7
```

An unknown `--density` value exits `1` with the valid choices on stderr.

Output above is illustrative; generation is random unless `--seed` is given, so unseeded results will differ.

**Exit codes**: `0` on success; `1` on a usage error (an unknown `--density` value, or `--name` together with `--count` greater than 1), with the reason on stderr. World generation has no in-domain failure analogous to character death.

#### Output format

Each printed line is the full SRD world-data line: name, hex (subsector listings only), UWP profile, base code, trade codes, travel-zone code, PBG triple, and allegiance.

### Library

The generation engine is usable directly without the CLI:

```python
from cetools.engine.worlds import generate_system, generate_subsector

system = generate_system()
print(system.world.profile)   # e.g. A867A9C-F
print(system.data_line)       # the full world-data line

subsector = generate_subsector()
print(len(subsector.systems), "occupied hexes")
```

`generate_system` returns a `System` wrapping a `World`; `system.world.profile` is the classic UWP string and `system.data_line` is the full rendered line. `generate_subsector` walks the 8x10 grid and returns a `Subsector` of `System`s, each with its `hex` set to its own coordinate.

World generation reuses the same `Rolls` seam as character generation, so it is deterministic given a seed:

```python
import random
from cetools.engine.rolls import RandomRolls
from cetools.engine.worlds import generate_world

world = generate_world(RandomRolls(random.Random(42)))
assert world == generate_world(RandomRolls(random.Random(42)))
```
