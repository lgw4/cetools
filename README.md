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

#### Output format

Each character prints as a compact block:

- **Line 1** — `Rank Name`, the [UPP](https://evolvedexperiment.github.io/cepheus-srd/introduction.html#universal-personality-profile), and age, tab-separated.
- **Line 2** — career and terms served, then total mustering-out cash, tab-separated.
- **Line 3** — skills, alphabetical.
- **Optional** — a line of material benefits (repeats collapsed as `Name x N`).
- **Optional** — a final `Mishap:` line when a survival mishap ended the career.

Example output (Navy, full career):

```text
Starman Sam Voss	5A3B93	Age 38
Navy (5 terms)	Cr52,000
Admin-0, Advocate-1, Animals-0, Comms-0, Engineering-1, Gun Combat-0, Gunnery-0, Melee Combat-2, Tactics-1, Vehicle-2, Zero-G-1
+1 Edu, High Passage
```

Example output (drafted; note repeated benefits collapsed to `x 2`):

```text
Captain Morgan Voss	7937A5	Age 42
Navy (6 terms)	Cr61,000
Admin-0, Advocate-0, Animals-0, Comms-0, Engineering-0, Gun Combat-0, Gunnery-0, Jack o' Trades-0, Leadership-0, Melee Combat-0, Piloting-0, Tactics-2, Vehicle-1, Zero-G-1
+1 Soc, +1 Edu x 2, Weapon x 2
```

Example output (Marine, career cut short by a mishap):

```text
Trooper Casey Voss	481749	Age 20
Marine (0 terms)	Cr0
Admin-0, Advocate-0, Animals-0, Battle Dress-0, Comms-0, Demolitions-0, Gun Combat-0, Gunnery-0, Melee Combat-0, Zero-G-1
Mishap: Injured in action, injured (Endurance -6), survived an injury crisis; Debt Cr40,000
```

Characters no longer die during generation. A failed survival roll resolves on the [Survival Mishaps table](https://evolvedexperiment.github.io/cepheus-srd/) and always yields a usable character: an injury, a discharge (honorable, dishonorable, or medical), and sometimes debt. The mishap is summarized on the `Mishap:` line.

Output above is illustrative; generation is random, so your results will differ.

**Exit codes**: `0` on success; `1` if generation failed or an unknown `--career` value was given (reason written to stderr).

Characteristic values above 9 are shown in [pseudo-hex notation](https://evolvedexperiment.github.io/cepheus-srd/introduction.html#pseudo-hexadecimal-notation) — `A`=10, `B`=11, … skipping `I` and `O`.

### Library

The generation engine is usable directly without the CLI.

Generate a character for a specific career (re-rolls characteristics until the career qualifies, enforces a hard 7-term cap):

```python
from cetools.engine.generator import generate_career_character
from cetools.engine.careers.aerospace import AEROSPACE_CAREER
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER
from cetools.engine.models import Character, GenerationFailure

result = generate_career_character(NAVY_CAREER)

if isinstance(result, Character):
    print(f"UPP: {result.upp}  Career: {result.career}  Terms: {result.terms_served}")
else:
    print(f"Generation failed: {result.reason}")
```

Both `generate_career_character` and `draft_character` return `Character | GenerationFailure`. A `Character` carries the fields surfaced in output — `name`, `rank_title`, `upp`, `age`, `skills`, `benefits`, and (when a survival mishap ended the career) `mishap` and `debt`.

Generate a draft character (career assigned by 1D6 roll against the draft table):

```python
from cetools.engine.generator import draft_character

result = draft_character()
if isinstance(result, Character):
    print(f"Career: {result.career}  Drafted: {result.drafted}")
```

Use the career registry to look up a career by name:

```python
from cetools.engine.careers import CAREER_REGISTRY

career = CAREER_REGISTRY["scout"]  # or "navy", "marine", "maritime system defense", "aerospace system defense"
```

Inject a custom `DiceRoller` for deterministic results:

```python
from cetools.engine.generator import generate_career_character
from cetools.engine.careers.scout import SCOUT_CAREER

class FixedRoller:
    def roll(self, sides: int, count: int = 1) -> int:
        return count * 4  # always rolls 4 per die

result = generate_career_character(SCOUT_CAREER, roller=FixedRoller())
```
