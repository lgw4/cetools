# cetools

Cepheus Engine character generation tools. Generates playable characters following the [Cepheus Engine SRD](https://evolvedexperiment.github.io/cepheus-srd/) rules.

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

- **Line 1** — `Rank Name`, the [UPP](https://evolvedexperiment.github.io/cepheus-srd/introduction.html#universal-personality-profile), and age, tab-separated.
- **Line 2** — career and terms served, then total mustering-out cash, tab-separated.
- **Line 3** — skills, alphabetical.
- **Optional** — a `Psionics:` line of learned talents, alphabetical, when the character is psionic.
- **Optional** — a line of material benefits (repeats collapsed as `Name x N`).
- **Optional** — a final `Mishap:` line when a survival mishap ended the career.

Skills are shown with their level. A skill first gained from a Skills and Training roll starts at level 1; level 0 means the character has the skill but has never rolled it — it came from basic training or from their background.

Example output (Navy, full career):

```text
Commodore Sam Voss	7796D5	Age 46
Navy (7 terms)	Cr61,000
Advocate-0, Comms-1, Computer-0, Engineering-0, Gravitics-1, Gun Combat-1, Gunnery-1, Leadership-2, Linguistics-0, Melee Combat-0, Navigation-2, Streetwise-0, Tactics-1, Vehicle-1, Zero-G-1
+2 Edu, Explorers' Society, Weapon, High Passage, Mid Passage (x2)
```

Example output (drafted; note repeated benefits collapsed to `(x2)`, and stat boosts summed):

```text
General Drew Kade	798979	Age 46
Surface System Defense (7 terms)	Cr50,000
Animals-0, Battle Dress-0, Carousing-0, Gun Combat-2, Gunnery-0, Leadership-1, Mechanics-1, Melee Combat-4, Recon-2, Vehicle-1
+3 Soc, Weapon, High Passage, Mid Passage (x2)
```

Example output (Marine, career cut short by a mishap):

```text
Trooper Taylor Voss	216668	Age 20
Marine (0 terms)	Cr0
Battle Dress-0, Comms-0, Demolitions-0, Engineering-0, Gun Combat-0, Gunnery-0, Melee Combat-0, Watercraft-0, Zero-G-1
Mishap: Medically discharged, injured (Dexterity -6, Endurance -2, Strength -2), survived an injury crisis; Debt Cr10,000
```

Example output (Navy, psionic):

```text
Captain Drew Solis	69575C-2	Age 42
Navy (6 terms)	Cr21,000
Comms-0, Engineering-2, Gravitics-1, Gun Combat-0, Gunnery-2, Melee Combat-0, Streetwise-0, Survival-0, Tactics-1, Vehicle-0, Zero-G-1
Psionics: Telekinesis-0
+1 Soc, Mid Passage, High Passage, Weapon (x2)
```

Characters no longer die during generation. A failed survival roll resolves on the [Survival Mishaps table](https://evolvedexperiment.github.io/cepheus-srd/) and always yields a usable character: an injury, a discharge (honorable, dishonorable, or medical), and sometimes debt. The mishap is summarized on the `Mishap:` line.

Characters are tested for psionics under a cetools house rule layered on the optional [SRD psionics rule](https://evolvedexperiment.github.io/cepheus-srd/): a character must first pass a flat `2D6 ≥ 11` eligibility check to be tested at all (roughly 8% do), which keeps psionic characters a genuine minority. Characters who fail the check, or who roll `Psi` 0, show the bare UPP as before; psionic characters (`Psi ≥ 1`) append it as a hyphenated pseudo-hex suffix, e.g. `5A3B93-6`. Any talents learned during training appear on an optional `Psionics:` line, alphabetical, each at level 0. Psionic training's cash cost and time are abstracted away — mustering-out cash and age are unaffected.

Output above is illustrative; generation is random, so your results will differ.

**Exit codes**: `0` on success; `1` if generation failed or an unknown `--career` value was given (reason written to stderr).

Characteristic values above 9 are shown in [pseudo-hex notation](https://evolvedexperiment.github.io/cepheus-srd/introduction.html#pseudo-hexadecimal-notation) — `A`=10, `B`=11, … skipping `I` and `O`.

### Library

The generation engine is usable directly without the CLI. There is one entry point:

```python
from cetools.engine.generator import DRAFT, RANDOM, generate
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.models import Character

result = generate(NAVY_CAREER)   # or generate(DRAFT), or generate(RANDOM)

if isinstance(result, Character):
    print(f"UPP: {result.upp}  Career: {result.career}  Terms: {result.terms_served}")
else:
    print(f"Generation failed: {result.reason}")
```

The first argument is the **assignment**: a career, `DRAFT` (a 1D6 against the draft table), or `RANDOM` (any career, uniformly). It is also the only thing that decides whether the character is `drafted`.

`generate` returns `Character | GenerationFailure`. A `Character` carries the fields surfaced in output — `name`, `rank_title`, `upp`, `age`, `skills`, `benefits`, and (when a survival mishap ended the career) `mishap` and `debt`.

Look a career up by name with the registry:

```python
from cetools.engine.careers import CAREER_REGISTRY

career = CAREER_REGISTRY["scout"]  # keys are lowercase, e.g. "aerospace system defense"
```

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
| natural 12 at the 7-term cap | ignored — seven terms is the end | honoured — the character serves an eighth term |

Under `HOUSE`, a `GenerationFailure` can only mean that the draft landed on a career cetools has not implemented.

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
