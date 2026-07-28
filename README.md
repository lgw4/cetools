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

Pass `--seed` for reproducible output; the same seed and options always produce the same character(s), and a seed works with `--career`, `--random`, or the draft. With `-n`, the seed fixes the whole sequence, not one repeated character:

```bash
uv run cetools character generate --career scout --seed 42
```

Generation is otherwise random, so unseeded results differ from run to run.

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

Generates worlds, systems, and subsectors following SRD Chapter 12: a single [Universal World Profile](https://evolvedexperiment.github.io/cepheus-srd/worlds.html#universal-world-profile) (UWP), a fully-described system, or an 8x10 subsector.

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

## Starship generation

Designs and generates starships following the Cepheus Engine SRD [Ship Design and Construction](https://evolvedexperiment.github.io/cepheus-srd/ship-design-and-construction.html) rules: a deterministic **builder** that costs and validates a hull, drives, armor, computer, crew and armaments, and a seed-driven **random generator** layered on top of it.

### CLI

Build a ship from a TOML design file:

```bash
uv run cetools ship build tests/data/ships/free-trader.toml
```

```console
$ uv run cetools ship build tests/data/ships/free-trader.toml
TL8 Beowulf

Using a 200-ton hull (4 Hull, 4 Structure), the Beowulf is a starship. It mounts jump drive A, maneuver drive A and power plant A, giving a performance of Jump-1 and 1-G acceleration. Fuel tankage of 22 tons supports the power plant for two weeks and one Jump-1 jump. Adjacent to the bridge is a computer Model 1. The ship is equipped with Standard sensors (DM-4). There are four staterooms. The ship has two hardpoints and two tons allocated to fire control, but has no weapons installed. Cargo capacity is 135 tons. The hull is standard, and no additional armor has been installed. Special features include one ton of fuel processors (processes 20 tons of unrefined fuel into refined fuel per day). The ship requires a crew of five: one pilot, one navigator, one engineer, one medic and one steward. The ship cannot carry any additional passengers. The ship costs MCr29.772 (including discounts and fees) and takes 44 weeks to build.
```

The output is the SRD's Universal Ship Description Format: a `TL<n> <name>` heading, a blank line, and one unwrapped paragraph whose sentences run in the order the rules use.

Randomly generate a ship from a seed, or constrain it to a hull size or the small-craft ruleset:

```bash
uv run cetools ship generate --seed 42
uv run cetools ship generate --hull 10 --small-craft --seed 7
uv run cetools ship generate --interactive --seed 42
```

`--interactive` (`-i`) asks what to pin and rolls the rest. Every question shows its default and pressing Enter takes it, so answering nothing produces exactly the ship the same seed produces without the flag. Typing `none` at an optional component's question pins its *absence*, which is a different answer from pressing Enter: `none` at the armour question guarantees an unarmoured ship, where Enter rolls for one. An answer the tables do not recognise is rejected and asked again with the reason, so a typo costs a line rather than the session. `--hull` and `--small-craft` pre-answer their questions, which are then not asked. Questions and their answers go to stderr, so `--interactive` composes with `--toml` and `--out`.

Drives are answered as *ratings* (Jump-2, 2-G) rather than as drive code letters, because the letter that delivers a rating depends on the hull and a referee does not think in letters. A pinned rating installs the lightest code delivering it on the chosen hull, so the tonnage a lighter drive saves flows on to fuel and fittings. The power plant is asked for too rather than derived, since a referee may want surplus power for energy weapons; its prompt states the floor the drives *it was given* set, and rejects an answer below it. A drive left to the dice needs no such floor, because the dice are capped at the pinned plant instead: a pin is a promise and a roll only a preference, so the roll gives way. When the hull was left to the dice a rating can only be checked against the ratings some hull of that class can deliver, so one this particular hull cannot reach surfaces when the ship is assembled.

The wizard asks for the hull class first, because it governs everything after it: which hull tonnages are tabulated, and which questions are worth asking at all. It then walks the design in SRD build order: hull tonnage, configuration, the drives, armour, computer, electronics, staterooms, fitting, turrets, weapon bay, screen, name and purpose. A small craft is never asked about a jump drive or a weapon bay, because its ruleset forbids both, and its power plant is offered only the ratings that fit beside the manoeuvre drive already chosen. Its screen prompt defaults to none rather than to a roll, because the rules permit a small craft a screen but generation never draws one. `purpose` is the exception to every rule here, because cetools never invents one: its prompt defaults to none rather than to a roll, and leaving it unanswered yields a ship without a purpose rather than a random one. At the staterooms prompt `none` means a deliberate zero, which is a different answer from letting the dice choose the count.

Turrets are the one repeating question. Answering a count opens a mount and a weapon question for each turret in turn, both defaulting to random, so pinning the count and pressing Enter through the rest gives a ship with that many turrets and nothing else decided. A count above the hull's hardpoints is refused at the prompt, since hardpoints follow from a hull tonnage settled earlier in the session; with the hull left to the dice the count is taken on trust and ruled on by the hull it lands on.

Armour is answered as a type and a percent of the hull, like `crystaliron 10`. Any type in the SRD table may be pinned, including ones generation would never roll for itself. Rules that live in `build_ship`, such as armour arriving in 5% increments, are not duplicated into the prompts: an answer that breaks one is accepted where it is typed and reported when the ship is assembled.

A randomly generated ship arrives already named, drawn from `generate_ship_name`'s curated catalogue of mythology and folklore, written science fiction, and screen science fiction sources; a hand-authored design's own `name` is never overwritten.

Add `--toml` to emit a round-trippable design file instead of the description, and `--out` to write it to a file. Omit `--seed` to have one chosen for you and reported on stderr, so the run can be reproduced.

A referee can ask for more than a hull can hold. Generation never fails on tonnage: the ship still comes back, and the answers it could not honour are listed on stderr with what was asked, what was got, and why. That is a degraded ship rather than a failure, so the command still exits `0` and stdout still carries a design a pipe can read. A rolled value that would not fit is dropped in silence, because it was a preference rather than a promise.

Interactively that report is a question rather than a verdict. The session lists what it could not honour and asks whether to accept the ship or revise, with accept as the default:

```text
could not honour 2 constraint(s):
  staterooms: asked 8, got 7 (needs 32t, 30t free)
  turrets: asked turret 1 (triple pulse_laser), got none (needs 1t, 0t free)
Accept this ship or revise [accept]:
```

Answering `revise` re-asks only the questions the report names and keeps every other answer, so one bad fit does not cost a session's worth of answers. The same loop catches a design the builder rejects outright: that yields no ship, so interactively it goes back to the answers the refusal points at rather than aborting. Non-interactively it still exits `1`. A session that keeps producing the same conflict stops revising after a few rounds and hands back the ship it has.

To keep tonight's ship, save it and rebuild it: no replay format is needed, because the TOML round-trip is already lossless.

```bash
uv run cetools ship generate --interactive --toml --out tonight.toml
uv run cetools ship build tonight.toml
```

**Exit codes**: `0` on success, including a ship that missed some of its constraints; `1` on a missing or malformed design file, an unknown hull size, or a rules-illegal design (e.g. a power plant rated below its drives), with the violated rule on stderr. Only tonnage shortfalls degrade; a design the builder rejects yields no ship at all, though an interactive session is offered the chance to fix it first.

Output above is illustrative; generation is random unless `--seed` is given, so unseeded results will differ.

### Library

```python
from cetools.engine.ships import build_ship, load_design

ship = build_ship(load_design("tests/data/ships/free-trader.toml"))
print(ship.total_cost, ship.cargo_tons, ship.crew.total)   # 29.772 135.0 5
```

`build_ship` is the sole validation authority: it allocates every component in SRD build order and rejects a rules-illegal design with a message naming the violated rule. `load_design`/`loads_design` and `dump_design` round-trip a `ShipDesign` through TOML losslessly, including a ship's own `design`, so `build_ship(loads_design(dump_design(ship.design))) == ship`.

`generate_ship` reuses the same `Rolls` seam as character and world generation, so it is deterministic given a seed, and it always routes through `build_ship`, so a generated ship can never be rules-illegal:

```python
from cetools.engine.rolls import RandomRolls
from cetools.engine.ships import generate_ship

result = generate_ship(RandomRolls.seeded(42))
assert result == generate_ship(RandomRolls.seeded(42))
print(result.ship.hull_tons, result.unmet)   # 400 ()
```

`generate_ship` returns a `GenerationResult`, not a bare `Ship`: `result.ship` is the ship, and `result.unmet` reports any constraint the tonnage budget could not honour. Unconstrained generation has nothing to report, so `unmet` is empty.

What a referee pins at the prompts, a library caller passes as a `DesignConstraints` value; the wizard is a thin layer over the same seam. Anything left unset is rolled, and a pinned value consumes no dice. What that buys is that generation with no constraints draws exactly the sequence it always drew, so a seed keeps meaning what it meant. What it costs is that a pin resolving without a draw shifts every draw behind it: two runs on one seed differing in a single pin diverge completely downstream of that pin, so seed 42 below yields a different configuration and a different name once the hull is pinned.

```python
from cetools.engine.ships import DesignConstraints, HullClass, generate_ship

pinned = generate_ship(RandomRolls.seeded(42), constraints=DesignConstraints(hull_tons=200))
print(pinned.ship.hull_tons)   # 200

launch = generate_ship(
    RandomRolls.seeded(7), constraints=DesignConstraints(hull_class=HullClass.SMALL_CRAFT)
)
print(launch.ship.design.hull_class is HullClass.SMALL_CRAFT)   # True
```

Every optional-component field is three-state, because *roll for armour* and *no armour* are different instructions and the second has to be honoured. Leaving a field unset rolls it, a value pins it, and `ABSENT` pins its absence:

```python
from cetools.engine.ships import ABSENT, ArmorFit, ArmorType

armored = generate_ship(
    RandomRolls.seeded(7),
    constraints=DesignConstraints(armor=ArmorFit(type=ArmorType.BONDED_SUPERDENSE, percent=5)),
)
bare = generate_ship(RandomRolls.seeded(0), constraints=DesignConstraints(armor=ABSENT))

print(armored.ship.design.armor[0].type.value, bare.ship.design.armor)   # bonded_superdense ()
```

A pinned value is validated against the full SRD tables, not the curated lists that keep rolled output plausible, so bonded superdense can be pinned even though no seed would ever produce it.

When the hull cannot hold everything asked of it, the shortfalls come back on the result as records rather than as text to parse:

```python
from cetools.engine.ships import ArmorFit, ArmorType, DesignConstraints, generate_ship

crowded = generate_ship(
    RandomRolls.seeded(11),
    constraints=DesignConstraints(
        hull_tons=200,
        jump_rating=2,
        armor=ArmorFit(type=ArmorType.CRYSTALIRON, percent=30),
        staterooms=8,
    ),
)

for unmet in crowded.unmet:
    print(unmet.field, unmet.asked, unmet.got)   # staterooms 8 7
```

Each record carries the `field` a caller can match against `DesignConstraints`, what was `asked`, what it `got`, and the `reason` it fell short.

Drives are pinned the same way, as ratings: `jump_rating`, `maneuver_rating` and `power_rating` each resolve to the lightest code delivering that rating on the chosen hull. `available_ratings` reports what a hull can deliver, and `validate_rating` raises the same message a referee would see at the prompt. A pinned jump rating is a ceiling rather than a guarantee: if the hull cannot carry fuel for a complete jump at it, the rating degrades exactly as a drawn one would and the shortfall is recorded.

A randomly generated starship always carries fuel for at least one complete jump at its installed rating—the drive drawn is a ceiling, not a guarantee, and the generator downgrades it to whatever rating the hull's remaining tonnage can fuel for a full jump. Among drives of that rating, the lightest one is always the one installed, so the tonnage a downgrade frees flows on to fuel and fittings rather than sitting unused. This is generation policy, not an SRD rule: a hand-authored design loaded through `build_ship` is never second-guessed this way, so a short-legged design—one whose `jump_distance` is deliberately below its drive's rating—still builds exactly as written.
