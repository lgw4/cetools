# Phase 0 Research: Starship Generator

Source: the Cepheus Engine SRD "Ship Design and Construction" page
(<https://evolvedexperiment.github.io/cepheus-srd/ship-design-and-construction.html>), the sole rules
authority (Constitution I, FR-001). All numbers below are taken from that page. Two ambiguities are
resolved to the SRD's literal text and flagged; nothing is house-ruled.

## Part A—Build sequence (drives tonnage/cost order)

The SRD checklist, which the builder follows so tonnage and cost accumulate in a fixed order:

1. Hull displacement + configuration → base cost, hull points, structure points, build time,
   hardpoints.
2. Armor (optional).
3. Maneuver drive (optional for starships; required for other powered craft).
4. Jump drive (optional in general; **required for starships**; forbidden on small craft).
5. Power plant (**required**; rating ≥ the higher of the jump and maneuver drive ratings).
6. Fuel storage (jump fuel + power-plant fuel weeks).
7. Bridge (by hull size) / cockpit (small craft).
8. Computer + software.
9. Electronics suite.
10. Crew accommodations (staterooms, low berths, emergency low berths).
11. Additional fittings (armory, fuel processors, labs, hangars, vault, …).
12. Weapons (turrets, bays) and defensive screens, consuming hardpoints + fire control.
13. Remaining tonnage = cargo.
14. Total cost and build time.
15. Apply the 10% common-design discount **iff** the design is marked standard.

## Part B—Hull table (standard hulls 100–5,000 tons)

| Tons | Code | Cost (MCr) | Build (weeks) | Hull Pts | Struct Pts |
|------|------|-----------|---------------|----------|-----------|
| 100 | 1 | 2 | 36 | 2 | 2 |
| 200 | 2 | 8 | 44 | 4 | 4 |
| 300 | 3 | 12 | 52 | 6 | 6 |
| 400 | 4 | 16 | 60 | 8 | 8 |
| 500 | 5 | 32 | 68 | 10 | 10 |
| 600 | 6 | 48 | 76 | 12 | 12 |
| 700 | 7 | 64 | 84 | 14 | 14 |
| 800 | 8 | 80 | 92 | 16 | 16 |
| 900 | 9 | 90 | 100 | 18 | 18 |
| 1,000 | A | 100 | 108 | 20 | 20 |
| 1,200 | C | 120 | 124 | 24 | 24 |
| 1,400 | E | 140 | 140 | 28 | 28 |
| 1,600 | G | 160 | 156 | 32 | 32 |
| 1,800 | J | 180 | 172 | 36 | 36 |
| 2,000 | L | 200 | 188 | 40 | 40 |
| 3,000 | M | 300 | 268 | 60 | 60 |
| 4,000 | N | 400 | 348 | 80 | 80 |
| 5,000 | P | 500 | 428 | 100 | 100 |

**Hull points** = tons ÷ 50, rounded **down**. **Structure points** = tons ÷ 50, rounded **up**
(FR-008). The Cost/HullPts/etc. columns above are stored data, but the point formulas are computed
so a caller who adds a non-tabulated hull still gets correct points.

**Configuration cost modifier** (multiplies base hull cost, FR-003):

| Config | Modifier | Notes |
|--------|----------|-------|
| Distributed | ×0.9 | Cannot mount fuel scoops |
| Standard | ×1.0 | (default) |
| Streamlined | ×1.1 | Includes fuel scoops |

**Hardpoints** = tons ÷ 100 (one per 100 tons, FR-010). A small craft has exactly **one** hardpoint
despite being < 100 tons.

## Part C—Drives and power plant

Two data tables drive this (FR-004):

**C1. Drive-code cost/tonnage**—for codes A–Z (skipping I and O, per the SRD sequence), each code
has a fixed (tonnage, cost) for jump drive, maneuver drive, and power plant. Excerpt (full table in
`tables.py`): A = J(10t/10MCr) M(2t/4MCr) P(4t/8MCr); B = J(15/20) M(3/8) P(7/16); … Z = J(125/240)
M(47/96) P(73/192). Each step adds 5t/10MCr (jump), 2t/4MCr (maneuver), 3t/8MCr (power).

**C2. Drive-performance matrix**—`(drive_code, hull_tons) → rating`. On a **standard hull** the
**same** matrix governs jump rating, maneuver-G, and power-plant rating alike. It is tabulated only
for the 100–5,000-ton hull sizes of Part B; small craft read a *separate* matrix at their own scale
(Part K). A blank cell means that code is not installable on that hull (→ rejection). Representative
rows (100–1000t):

| Code | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900 | 1000 |
|------|-----|-----|-----|-----|-----|-----|-----|-----|-----|------|
| A | 2 | 1 | – | – | – | – | – | – | – | – |
| B | 4 | 2 | 1 | 1 | – | – | – | – | – | – |
| E | – | 5 | 3 | 2 | 2 | 1 | 1 | 1 | 1 | 1 |
| Z | – | – | 6 | 6 | 6 | 5 | 5 | 5 | 5 | 5 |

(Full 100–5,000 matrix stored in `tables.py`; larger hulls need higher codes to jump at all.)

**Decisions**:

- A caller specifies each drive by **code letter**; the builder looks up its rating from C2 using the
  hull size, and its tonnage/cost from C1. This keeps performance data-driven (SC-006).
- **Power-plant requirement** (FR-004): the power plant's rating (from C2) MUST be ≥ the higher of the
  jump and maneuver ratings, else reject ("power plant rating N below required M").
- **Required systems** (FR-005): a starship MUST have a jump drive and a power plant; any powered
  craft MUST have a power plant. A small craft MUST NOT have a jump drive. Maneuver drive is optional
  on starships but the generator always includes one (plausible ships).
- A blank matrix cell for the chosen (code, hull) → reject ("drive code X not available on N-ton
  hull").

## Part D—Fuel

- **Jump fuel** (FR-006) = 0.1 × hull tons × jump distance. The design states the intended jump
  distance; when unstated, the builder assumes a single jump at the ship's full jump rating and
  **reports the assumed range** (spec Assumption; FR-006 final clause).
- **Power-plant fuel** = ⌊power-plant tonnage ÷ 3⌋ per week × weeks. Weeks default to and are
  floored at **2** for starships (FR-006), **1** for small craft (FR-019).
- Both fuel loads are tonnage that counts against the hull budget.

## Part E—Bridge, computer, electronics

**Bridge** (FR-007), size by hull, cost MCr 0.5 per 100 tons of ship:

| Hull tons | Bridge tons |
|-----------|-------------|
| ≤ 200 | 10 |
| 300–1,000 | 20 |
| 1,100–2,000 | 40 |
| > 2,000 | 60 |

**Computer** (FR-007)—models 1–7 with (TL, rating, cost): 1 (Cr 30k, r5), 2 (Cr 160k, r10),
3 (MCr 2, r15), 4 (MCr 5, r20), 5 (MCr 10, r25), 6 (MCr 20, r30), 7 (MCr 30, r35). Options:
jump-control specialization (+5 jump rating, +50% cost), hardened (+50% cost); both = +100% cost.
Ship **software** each has a rating cost against the computer's rating and an MCr cost (Fire Control
5/weapon @ MCr 2, Jump Control 5×Jn @ MCr 0.1×Jn, Evade, Auto-Repair, etc.); total software rating
MUST NOT exceed the computer's rating (reject otherwise).

**Ambiguity resolved**: jump-control specialization's "+5 jump rating" raises the computer's
*effective rating* by 5 for the software-rating check, not the ship's Jump-N drive number (which is
derived from hull + drive code alone, Part C2)—the option lets the computer run 5 more points of
software than its bare model rating would allow. The builder applies this bonus in the same step
that rejects over-rating software.

**Electronics** (FR-009)—packages with (tons, cost): Standard (0t, included in bridge), Basic
Civilian (1t, Cr 50k), Basic Military (2t, MCr 1), Advanced (3t, MCr 2), Very Advanced (5t, MCr 4).

## Part F—Armor

Types with (protection per 5% increment, cost as % of **base hull cost** per 5%): Titanium Steel
(2 pts, 5%), Crystaliron (4 pts, 20%), Bonded Superdense (6 pts, 50%). Armor is added in **5% of hull
tonnage** increments, minimum 1 ton per 5% (FR-008).
Options (once-only where noted): reflec (MCr 0.1/ton), self-sealing (MCr 0.01/ton), stealth
(MCr 0.1/ton). Small-craft armor caps armor type by TL but the tonnage math is unchanged.

**Ambiguity resolved**: "a non-5% request is rejected/normalized" is two different rules folded into
one sentence, and each is resolved independently:

- A `percent` that is not a multiple of 5 is a shape violation the *design* could never legally
  represent (there is no such thing as "7% armor"), so the builder **rejects** it outright
  (`"armor must be added in 5% increments (min 1 ton)"`).
- The "minimum 1 ton" clause is different: the SRD's Ship Armor by Type table states, per type,
  "N per 5%, **minimum 1 ton**"—a literal per-increment tonnage floor, not a conditional rejection.
  On a hull whose 5% of tonnage is under 1 ton (any small craft ≤ 15 t), the builder **floors** each
  increment to 1 ton rather than rejecting the layer; this is the SRD's stated rule, not a house
  normalization. spec.md's Edge Cases section reads "below the 1-ton-per-5% minimum, is rejected as
  invalid", which describes the *first* rule (a non-multiple-of-5 percent) correctly but does not
  intend the second (the floor) to be a rejection—the SRD text leaves no room for one.

## Part G—Quarters and fittings

**Quarters** (FR-009): stateroom 4t / Cr 500k (includes life support); low berth 0.5t / Cr 50k;
emergency low berth 1t / Cr 100k (four persons).

**Fittings** (FR-009), each with (tons, cost): armory 2t / MCr 0.5; detention cell 2t / MCr 0.25;
fuel scoops 0t / MCr 1 (only meaningful on non-streamlined hulls; forbidden on distributed);
fuel processor 1t / Cr 50k; laboratory 4t / MCr 1; library 4t / MCr 4; luxuries 1t / Cr 100k;
vault 12t / MCr 6 (+4 hull/structure points); vehicle hangar (vehicle tons +30%, MCr 0.2/ton).
Fittings are the most likely place for future data-only additions (SC-006).

## Part H—Armaments

**Turrets** (FR-010)—single 1t/MCr 0.2 (1 weapon), double 1t/MCr 0.5 (2), triple 1t/MCr 1 (3),
pop-up (+2t, +MCr 1), fixed mounting (0t, ×0.5 turret cost—MCr 0.1 for a single, MCr 0.25 for a
double, MCr 0.5 for a triple). Each turret consumes **one hardpoint**.
**Turret weapons**—pulse laser MCr 0.5, beam laser, sandcaster MCr 0.25 (+ ammo), particle beam
MCr 4, missile rack MCr 0.75 (+ missiles by type: standard/smart/nuclear, 12 per ton).

**Ammunition**—sandcaster barrels: 20 per ton, Cr10,000 per ton (Cr500 per barrel). Missiles: 12 per
ton regardless of type, priced per missile—standard Cr1,250, smart Cr2,500, nuclear Cr3,750.

**Bays** (FR-020, P3)—50t each, one hardpoint, +1t fire control: missile bank MCr 12, particle
MCr 20, meson MCr 50, fusion MCr 8. **Forbidden on small craft** (reject).

**Screens** (FR-020, P3)—meson screen 50t / MCr 60, nuclear damper 50t / MCr 50.

**Hardpoint limit** (FR-010, FR-015): total turrets + bays MUST NOT exceed hull hardpoints (tons ÷
100, or 1 for a small craft). Fire control: 1 ton per weapon group.

**Ambiguity resolved**: "fire control: 1 ton per weapon group" reads, on its own, as a rule that
applies uniformly to every weapon group—turret or bay. The builder does not read it that way. The
turret costs given above (single 1t, double 1t, triple 1t) are each already a complete, all-in
tonnage for that mount; there is no separate fire-control ton to add on top without double-counting
the turret's own listed weight. A 50-ton bay's tonnage, by contrast, is the weapon system alone—the
SRD bay-weapons rule adds "+1t fire control" explicitly because a bay's listed 50t does not already
include it. The builder therefore allocates `BAY_FIRE_CONTROL_TONS` for bays only
(`_build_bays`/`_build_turrets` in `builder.py`) and reads "1 ton per weapon group" as restating that
every weapon group—mounted turret or bay—consumes tonnage for its own fire control, already folded
into the turret's tons and called out separately for the bay. This is the deliberate reading, not an
oversight.

## Part I—Crew (minimum)

FR-012 asks for the SRD **minimum** crew. The SRD "Minimum" column:

| Role | Minimum rule |
|------|--------------|
| Pilot | 1 always |
| Navigator | 1 (SRD notes "optional with software"—see decision below) |
| Engineer | 1 per 35 tons of drives + power plant, rounded up (min 1 if any drive/plant) |
| Turret gunner | 1 per turret |
| Bay gunner | 1 per bay |
| Screen operator | 1 per screen |
| Medic | 1 per 120 crew + passengers, but 0 on a ship carrying no passengers |
| Steward | 1 per 4 high / 10 middle passengers |

**Ambiguity resolved**: the SRD lists the navigator minimum as "One (optional with software)". The
builder treats a navigator as required (minimum 1) unless the computer carries Jump-Control software,
in which case it is 0; this is the literal reading and is documented, not a house rule.

**Ambiguity resolved**: that navigator rule applies unchanged to a **small craft**, which by rule
carries no jump drive at all (Part K). A reader may expect a jump-incapable hull to need no navigator,
since plotting jump courses is the role's purpose—but the SRD's minimum-crew table states one flat
rule with exactly one exception (Jump-Control software), and the small-craft section modifies the
bridge, the jump drive, the fuel floor, the hardpoint count and the armament caps without touching
crew. Inventing a small-craft carve-out would be a house rule the source page does not support, which
FR-002 forbids, so `_build_crew` in `builder.py` applies the same navigator minimum to both rulesets:
`examples/fighter.toml` reports a navigator. Where the SRD is silent, cetools follows the rule it
states rather than the rule a reader might infer.

A ship with no passengers needs no steward and no medic (spec Edge Cases, FR-012). Note the medic rule
is a *conditional* per-120 headcount, not a bare `⌈(crew + passengers) ÷ 120⌉`: the bare formula would
round up to one medic on every ship, however small, which contradicts the SRD minimum column and the
spec. "Passengers" here means high and middle passengers; occupied low berths trigger neither a medic
nor a steward. Referee role assignment beyond these minimums is out of scope (FR-002).

## Part J—Cost and build time

Total cost (FR-013) = Σ(component costs) with the configuration modifier applied to hull cost. The
**10% common-design discount** applies to the whole vessel **only** when the design's `standard` flag
is set; it does not apply to fuel or ammunition (per SRD), so the builder discounts hull+components
but not fuel/ammo lines. Build time (FR-014) is read from the hull table (Part B).

## Part K—Small craft (10–95 tons, P3, FR-019)

Distinct ruleset: hull codes s1–sJ with their own (cost, build-time) table; **no jump drive**;
**cockpit** (1.5t 1-man / 3t 2-man; MCr 0.1 per 20 tons) in place of a bridge; power-plant **fuel
minimum one week**, rounded **down to the nearest 0.1 ton** (the SRD's explicit small-craft rounding
rule); exactly one hardpoint; **no bay weapons**; energy-weapon count capped by power-plant code
(sA–sF: 0, sG–sK: 1, sL–sR: 2, sS–sZ: 3; missile/projectile weapons uncapped). Both the builder and
the generator support small craft.

**K1. Small-craft hull table** (10–95 tons in 5-ton steps). Cost follows the rule **MCr 1.0 + tons ÷
100**; build weeks are tabulated:

| Tons | Code | Cost (MCr) | Build (weeks) | | Tons | Code | Cost (MCr) | Build (weeks) |
|------|------|-----------|---------------|---|------|------|-----------|---------------|
| 10 | s1 | 1.10 | 28 | | 55 | sA | 1.55 | 32 |
| 15 | s2 | 1.15 | 29 | | 60 | sB | 1.60 | 32 |
| 20 | s3 | 1.20 | 29 | | 65 | sC | 1.65 | 33 |
| 25 | s4 | 1.25 | 30 | | 70 | sD | 1.70 | 33 |
| 30 | s5 | 1.30 | 30 | | 75 | sE | 1.75 | 34 |
| 35 | s6 | 1.35 | 30 | | 80 | sF | 1.80 | 34 |
| 40 | s7 | 1.40 | 31 | | 85 | sG | 1.85 | 34 |
| 45 | s8 | 1.45 | 31 | | 90 | sH | 1.90 | 35 |
| 50 | s9 | 1.50 | 32 | | 95 | sJ | 1.95 | 35 |

Hull points and structure points use the same Part B formulas (⌊tons ÷ 50⌋ and ⌈tons ÷ 50⌉), so a
sub-50-ton craft has 0 hull points and 1 structure point.

**K2. Small-craft drive-performance matrix**—a **second, distinct** matrix from Part C2, and the one
place the small-craft ruleset departs from "one matrix governs everything". It is required because
no small-craft hull size (10–95 t) appears anywhere in the Part C2 matrix, and because the same code
letter performs differently at small-craft scale. Its axes are the same—`(drive_code, hull_tons) →
rating`, a blank cell meaning "not installable"—and it likewise governs maneuver-G and power-plant
rating together (there is no jump rating to govern). Codes carry the small craft's `s` prefix
(`sA`–`sZ`); component **tonnage and cost are unified across both rulesets**, read from the Part C1
table by the bare letter, so only *performance* needs the separate matrix. Representative rows:

| Code | 10 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | 90 | 95 |
|------|----|----|----|----|----|----|----|----|----|----|
| sA | 2 | 1 | – | – | – | – | – | – | – | – |
| sC | 6 | 3 | 2 | 1 | 1 | 1 | – | – | – | – |
| sE | – | 5 | 3 | 2 | 2 | 1 | 1 | 1 | 1 | 1 |
| sL | – | – | – | 6 | 4 | 4 | 3 | 3 | 2 | 2 |
| sW | – | – | – | – | – | – | – | – | – | 6 |

(Full 10–95 matrix stored in `tables.SMALL_CRAFT_DRIVE_PERFORMANCE`, exactly as the Part C2 matrix is
stored in `tables.DRIVE_PERFORMANCE`.)

**Not priced by the source page**: codes sX, sY and sZ appear in the energy-weapon cap band (sS–sZ: 3)
but the source page tabulates **no** small-craft performance for them at any hull size, so
`SMALL_CRAFT_DRIVE_PERFORMANCE` has no row for X, Y or Z and the builder rejects them on every
small-craft hull. Nothing is guessed to fill the gap (FR-002).

## Part L—Determinism and the random generator (FR-016–FR-018)

- The generator reuses the existing `Rolls` seam (`cetools.engine.rolls`). New `RollName` members
  (e.g. `SHIP_HULL_SIZE`, `SHIP_CONFIGURATION`, `SHIP_JUMP_CODE`, `SHIP_MANEUVER_CODE`,
  `SHIP_POWER_CODE`, `SHIP_TURRET_COUNT`, `SHIP_WEAPON`, …) are added to `RollName`.
- `generate_ship(rolls, *, hull_size=None, small_craft=False)` picks components via `rolls.choose`
  and `rolls.d6` from the same tables the builder validates against, assembles a `ShipDesign`, and
  returns `build_ship(design)`. Because it always finishes by calling the builder, no generated ship
  can be rules-illegal (SC-003).
- Seeding is identical to every other command: `RandomRolls.seeded(seed)`; the same seed yields the
  same ship (SC-004). When no seed is given, the CLI reports the seed it used so a run is
  reproducible.
- The generator constrains its choices so the assembled design is legal *by construction* (e.g. it
  picks a power-plant code whose rating meets the drive requirement, and never over-allocates
  tonnage); `bounded_retry` is available if a rejected assembly needs re-selection, but the intent is
  to choose legal components directly rather than reject-and-retry.

## Part M—TOML design I/O (FR-021–FR-023)

- **Read**: `loads_design(text)` parses TOML text with stdlib `tomllib` into a `ShipDesign`;
  `load_design(path)` reads a file and delegates to it. Splitting the two follows the
  `json.load`/`json.loads` convention and avoids guessing whether a `str` is a path or TOML content.
  Both raise a clear `ValueError` for malformed input (unparseable TOML, unknown keys, wrong types,
  unknown enum strings, missing hull)—but never for an SRD *rule* violation, which is the builder's
  sole responsibility (FR-015). No new runtime dependency.
- **Write**: `dump_design(design)` emits builder-compatible TOML via a small in-repo serializer
  (stdlib has no TOML writer; a dependency is forbidden). The schema is bounded (see
  `contracts/design-schema.md`), so serialization is a direct type-driven walk.
- **Round-trip** (SC-008): `build_ship(loads_design(dump_design(ship.design)))` equals `ship`. The
  generator emits `ship.design`, so a generated ship round-trips into an editable file. The design
  schema is expressive enough to represent any component the builder or generator can produce
  (FR-023), which is why `Ship` carries its originating `ShipDesign`.

## Consolidated decisions

- **Decision**: Split `ShipDesign` (declarative input) from `Ship` (computed output); `Ship` holds
  its `ShipDesign`. **Rationale**: makes the builder a pure `design → ship` function and makes
  lossless round-trip (SC-008) and reproducibility testable. **Alternatives**: one conflated mutable
  model—rejected as untestable for round-trip and blurring the TOML schema.
- **Decision**: Drives specified by **code letter**, rating derived from the performance matrix by
  hull size. **Rationale**: SRD-faithful and data-driven (SC-006). **Alternatives**: caller states a
  jump number directly—rejected because it hides the code/tonnage/cost the SRD keys off.
- **Decision**: Hand-rolled TOML writer. **Rationale**: no stdlib writer, no new dependency allowed.
  **Alternatives**: `tomli-w`/`toml`—rejected (runtime dependency); JSON output—rejected (spec
  mandates builder-compatible TOML for editing/round-trip).
- **Decision**: SRD rule checks live **only** in `build_ship`, ordered by the SRD build order;
  `ShipDesign.__post_init__` and `loads_design` reject malformed shape only. **Rationale**: FR-015
  requires the *first* violation in build order to be the one reported, which only holds with a single
  ordered authority—an upstream duplicate of a late-order check would pre-empt an earlier one.
  **Alternatives**: validating rules in the model too ("fail fast")—rejected as unable to satisfy
  FR-015 and as two places to keep in sync.
- **Decision**: Invalid designs raise `ValueError` with a rule-specific message, surfaced by the CLI
  as exit 1 to stderr. **Rationale**: matches the engine's `__post_init__`/`_validate_*` convention
  and Constitution III exit codes. **Alternatives**: a result/error object—rejected as heavier than
  the established raise-and-catch pattern.
