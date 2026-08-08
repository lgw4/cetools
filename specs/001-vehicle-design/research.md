# Phase 0 Research: Vehicle Design System

**Feature**: `001-vehicle-design` | **Date**: 2026-08-07 | **Spec**: [spec.md](./spec.md)

Sources: the Cepheus Engine SRD at `evolvedexperiment.github.io/cepheus-srd`, fetched as raw HTML
and read from disk (WebFetch hallucinates the tables on that site); the existing `ships` domain; the
constitution; `scripts/check_docs.py`.

## Corrections to the specification

Three factual errors in the spec surfaced while verifying it against the SRD. None changes the
feature's shape, and all three are recorded here rather than silently edited into `spec.md`.

### C-001: the published vehicles are not in Chapter 1

The spec says "Fifteen vehicles published in Chapter 1" (User Story 2, FR-021). Chapter 1
(`vehicle-design.html`) is the construction chapter and contains **zero** worked examples. It closes
by saying so: "Examples can be found in Chapter 2: Common Aircraft through Chapter 6: Uncommon
Vehicles." The fifteen the spec wants are spread across four chapters:

| Chapter | Vehicles |
|---|---|
| 2, Common Aircraft | TL5 Biplane, TL7 Helicopter, TL7 Twin Engine Jet |
| 3, Common Grav Vehicles | TL9 Air/Raft, TL15 G/Carrier, TL12 Grav Bike, TL11 Grav Floater, TL9 Grav Tank, TL9 Speeder |
| 4, Common Ground Vehicles | TL12 AFV (Tracked), TL12 ATV (Tracked), TL5 Ground Car, TL3 Stagecoach, TL5 Van |
| 6, Uncommon Vehicles | TL8 Tunnel Boring Machine |

The count and the breakdown are exactly right; only the chapter attribution is wrong. Chapter 5
(Common Watercraft) holds five more (Destroyer, Hovercraft, Motor Boat, Steamship, Submersible),
and the spec is correct to exclude them: four of the five need the over-20-ton rules.

**Decision**: read every "Chapter 1" in the spec as "the Vehicle Design System construction rules"
where it means the rules, and as "Chapters 2, 3, 4 and 6" where it means the examples. Suggest a
one-line spec amendment; nothing in the plan depends on the wrong attribution.

### C-002: the discount does not cover fuel or ammunition

FR-007 says the discount is "applied to the summed component price." The construction rules say
otherwise: **fuel and weapon ammunition are not covered by the Standard Design Discount.** The
ships domain already models exactly this with `LineItem.discountable`, and `_total_cost` splits the
discountable lines from the exempt ones before applying the multiplier.

**Decision**: implement the SRD rule. Fuel and ammunition line items are built with
`discountable=False`. Read FR-007's "summed component price" as "the summed price of the
discountable components," which is what the rule it cites actually says.

**Consequence**: this puts cetools at odds with the published examples, which appear to apply
0.9 to the whole total (the Helicopter and the Twin Engine Jet both show it). That is a divergence
under FR-017, and it goes on `DIVERGENCES.md`.

### C-003: the Air/Raft's four figures, verified

All four figures the spec quotes in User Story 2, acceptance scenario 3 are quoted correctly. What
the spec does not say is where each comes from:

| Figure | Status |
|---|---|
| Cr104,614.5 | As printed in the TOTALS row. The twelve priced rows actually sum to Cr104,614.51; the printed total is rounded down by one centicredit. |
| Cr94,153.05 | Arithmetically exact (104,614.5 × 0.9). The book never prints it. |
| Cr94,160 | The design table's own footnote. Recovered by 0.9 rounded **up to the nearest Cr10**, a convention that reproduces 18 of the 20 published footnotes. |
| KCr94.340 | The prose figure, repeated in Appendix A. Cr180 above the table's own footnote and not derivable by any reading. The Air/Raft is the only one of the twenty published designs whose prose price disagrees with its own footnote. |

A fifth Air/Raft defect the spec does not mention: **its Spaces column does not balance.** The
component rows leave 5.11 spaces unaccounted for, cargo is printed as 24.57 where the arithmetic
gives 29.68, and the prose repeats the wrong number. It is the only design of the twenty whose
spaces fail to sum to the chassis. Under FR-006 cargo is the remainder, so cetools will print 29.68
and the difference is a divergence.

## Decisions

### R-001: table inventory and how `tables.py` is organized

Chapter 1 holds **40 tables**. Grouped as the build order needs them:

| Group | Tables |
|---|---|
| Chassis and configuration | Chassis by Displacement (24 rows), Configuration (2), Submersible Dive Depth (6, out of scope) |
| Armor and structure | Armor by Type (7), Hull and Structure (8) |
| Drives and fuel | Power Plant Types (10), Propulsion Types (16), Drive Costs (24), Drive Performance smaller chassis (24×12), Drive Performance larger chassis (24×12), Base Speed by Drive Performance (15), Power Plant Fuel Requirements (24), Fuel Consumption by Power Plant Type (10), Agility Modifiers (24) |
| Controls and electronics | Control Systems (5), Drone Controllers (5), Robot Brains (3), Communication Systems (4), Alternative Communicators (3), Standard Sensors (5), Computer Models (6) |
| Crew and components | Accommodations (12), Life Support (2), Cargo Trailer (6), Manipulator Arm Maximums (4), Additional Components (34) |
| Armaments | Gun Port Weapons (24), Weapon Mounts (6), Turrets (3), Vehicular Turret Weapons (76), Weapon Ammunition (11), Ordinance Bay Weapons (12), Vehicular Missiles (10), Anti-Missile Systems (9) |
| Special rules | Lift Envelope Size (4), Missile Time to Impact (out), Missile To-Hit (out), Animal Gait (4), Sample Animals (5), Sailing Speeds (3) |

**Decision**: one `tables.py`, mirroring `ships/tables.py` exactly in idiom: a `<Thing>Row` frozen
dataclass per table shape, then module-level annotated `SCREAMING_SNAKE` constants built with
keyword arguments, each followed by a bare docstring naming its SRD table and its key columns. No
functions in the file, no in-package imports. The two Drive Performance tables merge into one
`DRIVE_PERFORMANCE: dict[str, dict[str, int | None]]` keyed drive code → chassis code, because
their split is a page-width artifact.

**Size estimate**: the two drive-performance matrices are 576 cells and the turret weapons table is
76 rows of ten columns, so `tables.py` lands around 2,000 to 2,500 lines. That is the single
largest file in the change and it is data.

**Alternative rejected**: splitting into `tables/` submodules by group. `ships/tables.py` is 1,179
lines in one file and the flat form is what the docs check and the import discipline expect.

### R-002: tech level is a gate, not a dimension

Only three Chapter 1 tables carry values that **vary** with tech level: Submersible Dive Depth (out
of scope), Manipulator Arm Maximums, and Vehicular Turret Weapons, where TL is baked into the row
identity ("Howitzer-TL 12") so fourteen weapon families reappear at several TLs. Everywhere else TL
is a scalar availability gate on the row.

**Decision**: carry `tl: int | None` as a column on the row types that have one, exactly as ships
does, and derive nothing from it beyond FR-012's availability check. Turret weapons are keyed by
their printed weapon-at-TL name, so the 76 rows stay one flat table.

Note this makes FR-001's stated rationale slightly off ("vehicle armor varies by type and tech
level"): vehicle armor varies by **type**, and TL gates it. The conclusion FR-001 draws is still
right for a stronger reason: the vehicle tables are keyed by chassis code and spaces where the ship
tables are keyed by tonnage, so no row type is shareable.

### R-003: SRD defects inside Chapter 1 itself

The spec anticipates divergences between the worked examples and the rules. Research turned up
defects in the **rules tables**, which FR-017 does not cover because it names Chapter 1 as the
single source of truth and here Chapter 1 contradicts itself:

1. **Drive Code D**: `Vehicle Drive Costs` gives row D values identical to row C (0.4 spaces,
   Cr450), but `Power Plant Fuel Requirements` lists D as **0.75** spaces. Two tables, same
   quantity, different answers. The fuel table's 0.75 fits the progression C 0.4 → D 0.75 → E 1.0;
   the drive-cost row looks like a copy-paste of C.
2. **Primitive controls**: the table says TL1, the prose definition says TL2.
3. **Wet Bar**: the row is column-shifted, reading Spaces `1`, Price `5 Cr2,000`. The prose gives
   1.5 spaces at Cr2,000.
4. **Standard sensors**: max range printed "Very Long (500 km)" where the comms table and the
   underwater-sensor note both make Very Long 500 **m**.
5. **Chassis code H** (13 t) is priced Cr23,350, breaking the progression F 20,150 → G 22,650 →
   H → J 28,150.
6. **Folding Wings/Rotors (TL3)** has a prose entry and no row in Additional Components.
7. **Ordinance bay, Torpedo Nuclear Heavy**: truncated in the source HTML.

**Decision**: transcribe what the table prints, except where the table contradicts prose in the
same chapter, in which case take the prose and record a divergence. That gives: Drive Code D takes
the fuel table's 0.75; Primitive controls take TL2; Wet Bar takes 1.5 spaces at Cr2,000; Folding
Wings gets a row from its prose entry. Sensors max range and chassis H price are transcribed as
printed, because nothing in the chapter contradicts them and "looks like a typo" is not a source.
Every one of these seven goes on `DIVERGENCES.md`, which therefore has a rules section as well as a
worked-examples section.

**Alternative rejected**: transcribing every printed value verbatim and letting the contradictions
stand. A table that cannot produce a number is not transcription, and FR-003 requires the tables
ship complete.

### R-004: the scope boundary is enforceable from the tables

**Over-20-ton** is detectable without ship tables: the chassis table stops at 20 tons / chassis code
Q, and the Hull and Structure and Drive Performance tables stop with it. Anything larger has no row,
so FR-013's rejection is "no chassis row for this displacement" rather than a special case.

**Watercraft** is detectable as a fixed set of names: the Submersible, Hydrofoils and Wave-Piercing
Hull configuration options; the Screw Propeller and Sails propulsion types; the underwater sensor
package; the six torpedo rows in Ordinance Bay Weapons; the Floats/Pontoons component; and the
Sailing Speeds table's water row.

**Decision**: transcribe every one of these rows (FR-003 says the tables ship complete), and gate
them at build time with a single `_WATERCRAFT_ONLY` frozenset per category that FR-013's error
message reads from. The Agility Modifiers rows "Huge (20+ tons)" and "Gargantuan (100+ tons)"
transcribe too and are simply unreachable.

**Play rules confirmed separable**: Missile Time to Impact, Missile To-Hit, Off-Road Movement and
Atmospheres and Aircraft never feed back into component selection. Two options that look like play
rules are construction items and stay in: Off-Road Capability and Extended Operational Environment
Range, both of which are bought to cancel a play penalty.

### R-005: module layout mirrors ships

```text
src/cetools/engine/vehicles/
├── __init__.py        # public surface, explicit __all__, no logic
├── tables.py          # the 40 Chapter 1 tables as data; no functions
├── models.py          # VehicleDesign, Vehicle, component fits, enums
├── design.py          # TOML load/dump, shape validation only
├── builder.py         # build_vehicle: the single authority on the rules
├── prose.py           # number, list and article primitives for vehicle prose
├── description.py     # the UVDF paragraph and the component table
├── generator.py       # roles, constraints, seeded generation
├── catalog.py         # the fifteen installed designs, by name
├── published.py       # the fifteen published stat blocks, transcribed
└── catalog/*.toml     # the fifteen authored design files
```

Ten modules against ships' nine, in the same dependency direction: `tables` and `prose` import
nothing in-package; `models` imports `tables`; `design`, `builder` and `description` import
`models`; `generator` imports `builder`; `catalog` imports `design`; `__init__` imports everything.

**Decision on `prose.py`**: vehicles gets its own rather than importing `ships/prose.py` or
promoting it to `engine/prose.py`. FR-001 forbids the import outright, and promotion would put a
second module outside the vehicles domain into a change whose Dependencies section claims exactly
one. The overlap is real but partial: `count`, `join`, `article` and `plural` recur, while vehicles
need spaces, kph, agility and performance-code spellings that ships has no use for, and ships'
`tons` helper encodes a displacement-ton rule vehicles does not share. Roughly 60% overlap on 136
lines is under the threshold where the constitution's Principle V favors an abstraction.

**Decision on the module map**: `check_module_map` makes only top-level `engine/*.py` mandatory, so
a `vehicles/` subpackage is not forced into CONTRIBUTING.md's tree. `ships/` is listed there by
convention and `vehicles/` will be too.

### R-006: shipping the catalog as package data

There is **no precedent** in the repo. Every piece of game data today is a Python literal in a
module, and nothing under `src/` uses `importlib.resources`, `pkgutil.get_data`, or a
`__file__`-relative path. The build backend is hatchling with
`packages = ["src/cetools"]` and no package-data configuration, which means non-Python files under
`src/cetools` are included in the wheel already; no `pyproject.toml` change is needed.

**Decision**: the fifteen designs ship as TOML under `src/cetools/engine/vehicles/catalog/`, read
through `importlib.resources.files("cetools.engine.vehicles") / "catalog"`. `catalog.py` exposes
`catalog_names() -> tuple[str, ...]` and `load_catalog(name) -> VehicleDesign`, with names as
stable kebab-case slugs (`air-raft`, `grav-tank`, `tunnel-boring-machine`).

**Alternative rejected**: transcribing the designs as Python literals to match the existing
convention. FR-021 and FR-022 require *authored design files* going through the same loader a
referee's file uses; a Python literal would skip `loads_design` and stop being the round-trip
evidence User Story 4 depends on.

**Alternative rejected**: keeping them in `tests/data/vehicles/` as ships does. The clarification
session settled this: a catalog only the test suite can read delivers none of User Story 2's
referee-facing value.

### R-007: how SC-002 is actually enforced

Two mechanisms, deliberately different, because they fail in different directions.

`published.py` carries the transcription: `PUBLISHED: dict[str, dict[str, object]]`, catalog name →
figure name → published value, verified against the SRD text. It lives in the package rather than in
`tests/` because it is transcribed SRD data and Principle I says that belongs in data separate from
the code that consults it, and because `scripts/check_docs.py` must be able to import it without
reaching into the test tree.

1. **The comparison test** (`tests/test_vehicle_catalog.py`) builds all fifteen and compares every
   transcribed figure. A mismatch fails unless that vehicle and figure appear on `DIVERGENCES.md`
   with the same published and produced values. This catches a divergence nobody noticed.
2. **The docs check** (a new function in `scripts/check_docs.py`) parses `DIVERGENCES.md`, rebuilds
   each named vehicle, and confirms the "cetools" column still matches what the builder produces.
   This catches a divergence whose prose has gone stale.

Both read the same markdown table, so the page has one machine-readable shape: a table per section
with columns Vehicle, Figure, Published, cetools, Why.

**`DIVERGENCES.md` joins `DOCS`**, which imposes exactly two new obligations on its prose:
every backticked identifier must resolve to a public name in the package or be added to `NOT_CODE`,
and no dash may be spaced. The American-spelling check already covers every non-hidden markdown
file at the repo root, so that applies either way. `check_readme_examples`,
`check_readme_ship_console_examples` and `check_module_map` are hard-coded to their own files and
will ignore the new page, which is why the rebuild check has to be written rather than inherited.

### R-008: generation, roles, and the position ships took

`ships/generator.py` has no archetype concept, and its absence is a documented refusal: roll
plurality was considered and rejected because it "would make random ships busier rather than more
coherent, and would put the generator in the position of judging whether a library, a laboratory
and luxuries belong together on a hundred-ton hull."

FR-026b requires the opposite for vehicles, and the clarification session confirmed it. The two
positions are compatible for a reason worth stating in the code: a ship's tonnage budget is large
enough that an independently drawn component is merely *surprising*, while a vehicle's is small
enough that one is often *absurd* (a turret on an ambulance, a wet bar on a grav bike), and Chapter
1's component list is far wider relative to the chassis than Chapter 8's is relative to a hull.

**Decision**: a `Role` enum with a loadout profile per role, living in `generator.py`, never
imported by `builder.py`, and documented on `DIVERGENCES.md`'s generation-policy section as a
cetools choice rather than a rule. The profile constrains which categories are filled and from what
pool; every draw still goes through the `Rolls` seam.

**Reused verbatim from ships**: the `TonnageLedger` shape (renamed to a spaces ledger), the
three-state `Absent`/`ABSENT` sentinel for optional components, `_pin_all_or_draw_one`, and the
distinction that **a pin is a promise and a roll is only a preference**—a pinned value that will
not fit is declined and recorded, a drawn one is dropped in silence.

**Reused verbatim for constraint failure**: refuse up front with `ValueError` anything decidable
from the tables alone (an unknown chassis size, a locomotion alias matching no row); degrade and
record an `UnmetConstraint` for anything that depends on the running budget. `UnmetConstraint.field`
must be spelled exactly as a `GenerationConstraints` field name.

### R-009: roll names

`RollName` is a flat `StrEnum` in `engine/rolls.py` grouped by verb, with `WORLD_*` and `SHIP_*`
prefixes for the newer domains. Vehicles add `VEHICLE_*` members: `VEHICLE_ROLE`,
`VEHICLE_TECH_LEVEL`, `VEHICLE_CHASSIS`, `VEHICLE_CONFIGURATION`, `VEHICLE_ARMOR`,
`VEHICLE_PROPULSION`, `VEHICLE_POWER_PLANT`, `VEHICLE_DRIVE_CODE`, `VEHICLE_CONTROLS`,
`VEHICLE_COMMUNICATIONS`, `VEHICLE_SENSORS`, `VEHICLE_COMPUTER`, `VEHICLE_ACCOMMODATION`,
`VEHICLE_COMPONENT`, `VEHICLE_MOUNT`, `VEHICLE_WEAPON`, `VEHICLE_AMMUNITION`.

`RandomRolls` wraps one `random.Random` stream, so **draw order is load-bearing** and the role draw
must come first (it decides every later pool). Ships pins its name draw last for the same reason;
vehicles have no name draw, so the ordering constraint is only at the front.

### R-010: determinism baseline

Ships pins `tests/data/baseline/designs.json` as `{"path:seed": dump_design(...)}` for 100 seeds
and compares serialized TOML rather than objects so a failure diffs readably. Vehicles follow that
exactly with `tests/data/baseline/vehicle_designs.json`.

The documented caveat carries over: a pinned constraint consumes no dice, so two runs on one seed
diverge below the first pin, and only the unconstrained sequence is byte-stable. SC-003 is
satisfied by pinning the unconstrained path per seed and asserting equality of two runs on the
constrained paths.

Also carried over: `ships/generator.py` uses up-front pool filtering rather than
`rolls.bounded_retry`, which keeps a degenerate `ScriptedRolls` from hanging. Vehicles do the same.

### R-011: floating point and the display edge

FR-033 requires floats throughout with rounding only at the display edge, and the Air/Raft shows
why: its true component sum is Cr104,614.51 where the book prints Cr104,614.5. Spaces are tracked at
twelve to the displacement ton and Chapter 1 prices components in fractions of a space, so
intermediate rounding would drift.

**Decision**: `float` everywhere in the engine; `prose.money` and `prose.number` do all rounding.
Comparison against `published.py` uses `math.isclose` with an explicit tolerance rather than `==`,
and the tolerance is stated in the test so a figure that differs by more than a printing artifact
is a divergence rather than noise.

### R-012: the CLI surface

`cli/main.py` is thirteen lines: one `app.add_typer(<module>.app, name=...)` per group. Adding
`vehicle` is one import edit, one `add_typer` line, and an update to the root callback docstring,
which enumerates the groups.

`cetools vehicle build` takes a design file path or `--catalog NAME`, plus `--table`, `--toml` and
`--out`. `cetools vehicle generate` takes `--seed`, `--tech-level`, `--chassis`, `--locomotion`,
`--table`, `--toml` and `--out`. A third command `cetools vehicle catalog` lists the fifteen names.

Conventions carried from `cli/ship.py`: mutually exclusive flags are checked by hand at the top of
the body with `typer.echo(msg, err=True)` then `raise typer.Exit(1)`; the exact existing message
`--out requires --toml` is reused verbatim; engine `ValueError` becomes `str(exc)` on stderr with
exit 1; unmet constraints go to stderr with **exit 0**, because a vehicle really was produced and
must still pipe; an auto-chosen seed is echoed to stderr as `seed: {seed}`.

**No wizard.** FR-027 forbids it, and the ship wizard is 1,000 of `cli/ship.py`'s 1,143 lines. The
vehicle CLI should land near 200.

### R-013: locomotion aliases

FR-026a wants the propulsion table's own sixteen names plus coarse aliases. The natural alias set
groups the table rows: `grav`, `wheeled`, `tracked`, `rotor`, `jet`, `legged`, `rail`, `mole`,
`non-powered`. `ALIASES: dict[str, tuple[str, ...]]` maps each to propulsion table keys, and a table
test asserts every alias resolves to at least one row (SC-010) so the two vocabularies cannot drift.
Watercraft propulsion (Screw Propeller, Sails) is transcribed but no alias points at it.

## Open items for `/speckit-tasks`

None blocking. Two things the task list should carry explicitly:

- The seven rules-table defects in R-003 each need a transcription decision recorded at the
  definition site in `tables.py`, in the ships house style of documenting the *why* in prose next
  to the data.
- The comparison test in R-007 needs writing before the catalog designs are authored, so authoring
  is driven red-to-green against the published figures rather than tuned until it passes.
