# CONTEXT.md

The domain language of cetools. Use these terms exactly—in code, in tests, in
commit messages, and in conversation. When a new concept earns a name, it gets
an entry here.

cetools generates characters for the [Cepheus Engine SRD](https://evolvedexperiment.github.io/cepheus-srd/).
Where cetools departs from the SRD, the entry says so.

## Domain

**Career**—one of the 24 services a character can enter (Navy, Scout, Rogue,
…). A career is pure data: the targets a character must roll against, its four
skill tables, its ranks, and its benefit tables. Careers never contain logic.

A career has **one** identity: its name. There is no slug: the lookup key is
`name.lower()`, derived and never authored. `engine/careers` is the only module
that knows what a career is called—it exposes `CAREERS` (all of them, in name
order), `DRAFT_TABLE`, `is_military(career)`, and `resolve(spec)`, which turns
whatever a user typed into a **Career** or an `UnknownCareer` carrying the nearest
suggestion. Callers hold `Career` objects, never names: a **Character** carries
its `Career`, so nothing ever has to turn a name back into a career.

**Assignment**—how a character came to be in a career: a **Career** (chosen by
name), `DRAFT`, or `RANDOM`. It is the first argument to `generate()`, and it is
the only thing that decides whether a character is `drafted`—so a "drafted
random" character cannot be asked for.

**Rules**—which rules a character is generated under. cetools departs from the
SRD in exactly two places, both settled in
`specs/002-scout-career-character/spec.md`, and they travel together as a policy
rather than as loose flags:

| | `HOUSE` (the default) | `SRD` |
| --- | --- | --- |
| qualification | reroll characteristics until the career's target is met as a raw number; enlistment **cannot** fail | roll once, then a `2D6 + DM ≥ target` check that **can** fail |
| natural 12 at the 7-term cap | ignored: seven terms is the end | honoured: the character serves an eighth term |

`HOUSE` is what cetools has always done. Two consequences worth knowing: under
`HOUSE`, `generate()` **cannot fail at all**, so a **GenerationFailure** is an
`SRD`-only outcome; and the worst rung of the ageing ladder is unreachable,
because it needs the eighth term that only `SRD` allows.

`HOUSE`'s re-roll gives up after `MAX_ROLL_ATTEMPTS` attempts and raises, through
`bounded_retry` (see Architecture). Real dice never reach that: the highest target
any career sets is 8, which `2D6` clears about 42% of the time. The guard is there
so that a **ScriptedRolls** pinned below a career's target fails loudly instead of
hanging for ever.

**Draft table**—the six careers a drafted character can land in. It holds
`Career` objects, so a draft can never land on a career that does not exist. It
is also the single source of truth for which careers are **military**; there is
no separate list.

**Term**—four years of service. A term is survived or not; it may bring a
**commission**, an **advancement**, skills, and ageing. A character serves up to
seven terms. Under `SRD` **rules** a natural 12 on re-enlistment forces an eighth;
under `HOUSE`, the default, the cap is hard and the 12 is ignored.

**Check**—the engine's one universal rule: `2D6 + DM ≥ target`. Qualification,
survival, commission, advancement, the psionics gate and psionic training are
all checks. Nothing else in the rules has this shape, and everything with this
shape is a check.

**DM**—a dice modifier, usually derived from a characteristic via
`characteristic_modifier`. The caller computes its own DM; a **check** only
knows the number.

**Skill level**—a skill first gained from a Skills and Training roll is taken at
level **1**; one the character already has goes up a level. Level **0** means the
character has the skill but has never rolled it: basic training grants every
service skill at 0, and background skills come in at 0.

**Skills and Training rolls**—a **term** is worth **one** roll, plus an *extra*
for a **commission** and *another* for an **advancement**. So a Navy term is worth
1 quiet, 2 commissioned, 3 commissioned-and-promoted.

The exception is the seven careers with neither check (Athlete, Barbarian, Belter,
Drifter, Entertainer, Hunter, Scout): they take **two** rolls every term. That is
a property of the *career*, not of what happened this term. A character who merely
failed their commission gets the base one roll, not two—the two are not the same
thing, and conflating them was a real bug (`training.rolls_this_term`).

**Mishap**—what happens when a **term** is not survived: a discharge (honorable,
dishonorable, medical, or none), possibly imprisonment, possibly injury, possibly
debt. A mishap ends the career.

**Injury crisis**—an injury that would reduce a characteristic to zero. The
characteristic is restored to 1 and the character takes debt instead.

**Muster-out**—the benefits drawn on leaving a career: **cash benefits** (at
most three draws) and **material benefits**. A dishonorable discharge forfeits
both.

**Benefit**—one thing drawn at muster-out. It is one of exactly four:

| | |
| --- | --- |
| `Cash(amount)` | money |
| `StatBoost(label)` | a `"+1 X"` entry, by the abbreviation it is written with ("Edu"). Always one level—no table says `"+2 X"`—so two boosts of a stat are two of these, and summing them for display is the formatter's job |
| `Item(name)` | a thing: a Weapon, a High Passage, a ship |
| `Shares(quantity)` | ship shares, whose count is rolled when granted |

Each variant carries exactly what it is, so a benefit that means nothing cannot
be built. Some **items** are **once-only** (Explorers' Society, Research Vessel,
Courier Vessel): a career can grant them at most once.

**The `"+1 X"` notation**—used by both career skill tables and material benefit
tables. It is parsed in exactly one place (`models.parse_stat_boost`) and applied
in exactly one place (`models.apply_stat_boost`). `training` asks "boost or
skill?", `benefits` asks "boost or item?", and the formatter never asks: benefits
arrive already knowing what they are.

**UPP**—the six characteristics encoded in pseudo-hex. A psionic character's
Psi strength is appended after a hyphen.

**Ship design**—the Cepheus Engine SRD "Ship Design and Construction" rules, digested in
`specs/010-starship-generator/research.md`. Where the SRD defers a step to referee discretion—crew
role assignment beyond the stated minimums, mission-specific fittings—cetools invents nothing: those
steps are out of automated scope and documented here as omitted (FR-002). The same discipline
applies to catalog entries the SRD names but never prices: a beam laser is named in the Turret
Weapons prose (FR-010) alongside pulse laser, sandcaster, and particle beam, but the source page
lists no cost for it, so `TURRET_WEAPONS` omits it rather than guessing a figure. Small-craft drive
codes sX–sY–sZ are the same case: they fall inside the energy-weapon cap bands but the source page
tabulates no small-craft performance for them, so `SMALL_CRAFT_DRIVE_PERFORMANCE` carries no row and
the builder rejects them. One further rule is deliberately unenforced because the SRD states none:
a cockpit's "1-man"/"2-man" seating never constrains the derived minimum crew. Component tech
levels (`ArmorRow.tl`, `ComputerRow.tl`, and the `tl` column on every other row the SRD tabulates
one for) *are* read: `build_ship` takes the highest among the fitted components as `Ship.tech_level`,
which the ship description prints in its heading. They still constrain nothing—a design may fit a
component above the tech level it claims, which FR-028b treats as a statement about the yard that
built the ship rather than an error.

**Fuel-limited drive selection**—`generate_ship`'s rule for picking a jump drive: the drawn letter is
a ceiling, not a guarantee. The generator downgrades it to the highest rating the hull's tonnage,
after every mandatory system, can fuel for one complete jump—falling back to the lowest legal rating
on a hull too small to fuel even that—and among drives of the chosen rating always installs the
lightest one, so a downgrade's freed tonnage flows on to fuel and fittings rather than sitting
unused. This is generation *policy*, not an SRD rule (the SRD does not say how a referee picks a
drive for a random ship), so `build_ship` deliberately does not apply it: a hand-authored short-legged
design—one whose `jump_distance` is below its drive's rating—builds exactly as written.

**`ShipDesign`**—the input record: hull, configuration, drives, power plant, bridge or cockpit,
computer, software, electronics, armor, quarters, fittings, turrets, bays, screens, and the
standard-design discount flag. Its own validation is **shape only**—types, ranges, enum
membership—never an SRD rule, so a well-formed but rules-illegal design still constructs and still
loads; only `build_ship` rejects it.

**`build_ship`**—the sole SRD-rule authority for ships, the way `engine/careers` is for careers. It
walks the SRD build order (hull and configuration, armor, drives and power plant, bridge or cockpit,
computer and software, electronics, quarters, fittings, turrets, bays, screens, cargo), costing and
validating each step in turn as a `LineItem`, so a design with two violations is rejected on
whichever comes first in *build order*, not in argument order. `generate_ship` and `cetools ship`
both route every design through `build_ship` rather than duplicating a check, so a generated ship can
never be rules-illegal.

**`Ship`**—the output record `build_ship` returns: every `LineItem`, the derived `Crew`,
hull/structure points, fuel, cost, and build time. It carries its own `design`, so
`build_ship(loads_design(dump_design(ship.design))) == ship`—a ship round-trips through TOML
losslessly, including one produced by `generate_ship`.

**Ship description**—the SRD's Universal Ship Description Format, and the only rendering cetools
does for a ship: `render_description(ship)` returns a `TL<n> <name>` heading, a blank line, and one
unwrapped paragraph whose sentences run in the order and wording the rules use. It is *presentation
only*—it reads `Ship`, `ShipDesign` and the static tables, computes nothing, and reads no clock,
seed or locale, so equal ships render byte-identically. A sentence for equipment the ship does not
carry is dropped whole rather than emitted empty. Component wording lives in the tables' `name` and
`plural` columns, never in the renderer, so an SRD row added to a table reaches the paragraph with
no change to `description.py`.

**Small craft**—a 10–95-ton hull built under a second, smaller ruleset in the same builder and
generator: a cockpit instead of a bridge, no jump drive, a one-week power-plant fuel floor, exactly
one hardpoint, and a power-plant energy-weapon cap. `HullClass` distinguishes it from a standard
starship hull.

**Crew**—derived, never authored: pilot, navigator (unless Jump-Control software), engineers,
gunners (turrets plus bays), `screen_operators` (one per screen), stewards, and a **medic** that is
`0` unless the ship carries high or middle passengers. `⌈(crew + passengers) ÷ 120⌉` alone would put
a medic on every ship, which the SRD does not.

## Architecture

The architecture vocabulary (module, interface, depth, seam, adapter, leverage,
locality) is defined by the `/codebase-design` skill and used as written there.

**The engine's steps**—each named step of character creation is its own module,
with a deep interface: give it the state and the **Rolls**, get back what changed.
None of them mutates its arguments.

| module | interface | the SRD step |
| --- | --- | --- |
| `background.py` | `background_skills(characteristics, rolls)` | the skills a character brings to their first career |
| `ranks.py` | `progress(career, rank, characteristics, skills, rolls)` | Commission and Advancement |
| `training.py` | `roll_skill(career, characteristics, skills, rolls)`, `rolls_this_term(career, commissioned, promoted)` | Skills and Training |
| `aging.py` | `apply_aging(characteristics, terms_served, rolls)` | Ageing |
| `benefits.py` | `muster_out(career, …, rolls)` | Benefits (**muster-out**) |
| `mishaps.py` | `resolve_survival_mishap(rolls, characteristics)` | Survival Mishaps |
| `psionics.py` | `roll_psionics(terms_served, rolls)` | Psionics |

A check *against a characteristic* (qualification, survival, commission,
advancement) is made in one place: `models.characteristic_check`, the module that
owns the DM rule. The two psionics checks are not among them: the eligibility gate
takes no DM at all, and a talent check's DM comes from Psi strength, which is not
one of the six characteristics. Those two call the seam directly.

`generator.py` is the **coordinator**: it owns qualification, survival,
re-enlistment, and the **term** loop, and calls the steps above. It holds no rules
content that belongs to a named step.

**There is no Term module, deliberately.** See `docs/adr/0001-no-term-module.md`:
it would have exactly one caller, so it would relocate the loop rather than deepen
anything. Reopen only if a second caller appears.

**Rolls**—the engine's single seam for chance. Everything the rules leave to
chance passes through it, and nothing else in the engine touches `random`.

Its interface is four verbs, because the rules only ever do four things:

| verb | meaning |
| --- | --- |
| `check(dm, target, name)` | the **check** rule: `2D6 + dm ≥ target` |
| `two_d6(name)` | a raw `2D6` value the rules do arithmetic on (characteristics, ageing, re-enlistment, Psi strength) |
| `d6(name)` | a `1D6` table index or quantity |
| `choose(items, name)` | a uniform pick from a list—not a die roll at all |

**Roll name**—every roll site is named with a `RollName`. The enum is the index
of every random decision the rules make: read it and you know what the engine
leaves to chance. Names exist so that tests can address a roll by intent
("survival fails in term 2") instead of by position in a die sequence.

Two adapters satisfy the seam: `RandomRolls` in production, `ScriptedRolls` in
tests. A test scripts rolls by name; anything it does not name takes a per-verb
default.

**`bounded_retry`**—the one guard for a draw that filters its result. Some draws
reject what they drew and draw again: characteristics below a career's target, a
world name already used in the subsector, a once-only benefit already granted.
`bounded_retry` caps that at `MAX_ROLL_ATTEMPTS` and returns nothing on exhaustion,
so a `ScriptedRolls` pinned to a rejected value fails loudly instead of hanging;
real dice never reach the cap. It lives beside the seam because it exists for the
seam's one degenerate case—a pinned adapter—and each caller decides what
exhaustion means: raise, or fall back to a deterministic scan.
