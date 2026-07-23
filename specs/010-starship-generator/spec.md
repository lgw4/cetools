# Feature Specification: Starship Generator

**Feature Branch**: `010-starship-generator`

**Created**: 2026-07-22

**Status**: Draft

**Input**: User description: "I'm interested in making a starship generator using the rules described here: https://evolvedexperiment.github.io/cepheus-srd/ship-design-and-construction.html."

## User Scenarios & Testing *(mandatory)*

The Cepheus Engine ship rules are a deterministic design-and-costing system: a designer chooses
components (hull, drives, power plant, fuel, bridge, computer, electronics, quarters, fittings, and
armaments) and the rules compute tonnage allocation, total cost, crew, hull and structure points,
fuel requirements, and build time while enforcing a web of dependencies and limits. This feature
delivers that system as a library plus command-line tool, with two ways to produce a ship: an
explicit **builder** and a seed-driven **random generator** layered on top of it.

### User Story 1 - Design a custom ship deterministically (Priority: P1)

A referee or player specifies the components of a standard-hull ship (100–5,000 tons) and receives a
complete, validated ship sheet: tonnage used and remaining (cargo), total cost in MCr, minimum and
full crew, hull and structure points, jump and power-plant fuel, and build time. The tool rejects
designs that violate SRD rules (e.g. a power plant weaker than the drives, over-allocated tonnage, or
too many turrets for the hull) with a clear explanation.

**Why this priority**: This is the MVP and the foundation. The SRD ship rules are fundamentally a
construction exercise; every other capability (random generation, small craft) is built on top of a
correct, validating builder. Delivered alone, it is already a usable ship-design calculator.

**Independent Test**: Provide a known design (e.g. a 200-ton streamlined hull, jump-1, 1-G maneuver,
matching power plant, two staterooms, one double turret with a pulse laser) and confirm the computed
tonnage, cost, crew, hull/structure points, and fuel match a hand-worked SRD example. Confirm an
invalid design (power plant below drive rating) is rejected with a specific error.

**Acceptance Scenarios**:

1. **Given** a valid set of component choices for a standard hull, **When** the ship is built,
   **Then** the tool reports total tonnage used, remaining tonnage allocated to cargo, total cost in
   MCr, minimum crew, hull points, structure points, jump fuel, power-plant fuel, and build time.
2. **Given** a design whose components exceed the hull tonnage, **When** the ship is built, **Then**
   the tool reports the over-allocation and identifies it as invalid rather than emitting a sheet.
3. **Given** a power plant rated below the higher of the jump or maneuver drive, **When** the ship is
   built, **Then** the tool reports the violated power-plant requirement.
4. **Given** more turrets requested than the hull's hardpoints allow (1 per 100 tons), **When** the
   ship is built, **Then** the tool reports the hardpoint limit.
5. **Given** a design flagged as a common/standard design, **When** the ship is built, **Then** the
   final cost reflects the 10% standard-design discount.

---

### User Story 2 - Randomly generate a complete ship from a seed (Priority: P2)

A referee wants a ready-made, rules-legal ship without specifying every component. They request a
random ship, optionally supplying a seed and/or a target hull size. The tool selects a valid
combination of components, builds it through the same deterministic engine used in User Story 1, and
returns a finished ship sheet. The same seed always produces the same ship.

**Why this priority**: This is the "generator" the request centers on, but it depends entirely on a
correct builder existing first. Layering it on top keeps randomness confined to component *selection*
while all costing and validation reuse the proven deterministic core.

**Independent Test**: Generate a ship with a fixed seed twice and confirm the two results are
identical. Generate with the same seed across separate runs and confirm reproducibility. Confirm every
generated ship passes the builder's own validation.

**Acceptance Scenarios**:

1. **Given** a seed, **When** a random ship is generated, **Then** the result is a fully valid ship
   sheet identical to a second generation with the same seed.
2. **Given** no seed, **When** a random ship is generated, **Then** the result is a valid ship sheet
   and the seed used is reported so the result can be reproduced.
3. **Given** a requested hull size, **When** a random ship is generated, **Then** the resulting ship
   uses that hull size and remains rules-legal.

---

### User Story 3 - Design and generate small craft (Priority: P3)

A user designs a sub-100-ton small craft (10–95 tons) under the modified small-craft rules: cockpits
instead of a bridge, maneuver drive and power plant but no jump drive, small-craft fuel minimums, and
restricted armaments. The builder and the random generator both support small craft.

**Why this priority**: Small craft are a distinct, self-contained second ruleset. They extend the
tool's reach (fighters, launches, ship's boats) but are not required for the core starship MVP.

**Independent Test**: Build a known small craft (e.g. a 10-ton fighter) and confirm tonnage, cost,
crew, and fuel match a hand-worked small-craft example, including small-craft-specific rules (no jump
drive permitted, one-week fuel minimum, cockpit in place of a bridge).

**Acceptance Scenarios**:

1. **Given** a small-craft hull under 100 tons, **When** it is built, **Then** small-craft rules apply
   (cockpit rather than bridge, one-week minimum power-plant fuel, restricted energy armaments) and no
   jump drive is permitted.
2. **Given** a request for a random small craft, **When** it is generated, **Then** the result is a
   valid small craft produced through the same builder.

---

### User Story 4 - Equip large ships with bay weapons and screens (Priority: P3)

A user designing a larger warship adds 50-ton weapon bays (missile bank, particle, meson, fusion) and
defensive screens (meson screen, nuclear damper), with the tool accounting for their tonnage, cost,
hardpoint, and fire-control requirements and enforcing the applicable limits.

**Why this priority**: Bays and screens matter only for larger military hulls and are additive to the
core armament model. They round out warship design but are not part of the minimum viable tool.

**Independent Test**: Add a 50-ton particle bay and a meson screen to a large hull and confirm the
tonnage, cost, hardpoint consumption, and fire-control tonnage are accounted for, and that bays are
rejected on hulls too small to support them.

**Acceptance Scenarios**:

1. **Given** a hull large enough for a weapon bay, **When** a bay is added, **Then** its 50 tons,
   hardpoint, and fire-control tonnage are accounted for and its cost is included.
2. **Given** a defensive screen, **When** it is added, **Then** its tonnage and cost are accounted for.
3. **Given** a small craft, **When** a bay weapon is requested, **Then** it is rejected as disallowed
   for small craft.

---

### Edge Cases

- **Zero remaining tonnage**: a design that exactly fills the hull yields zero cargo, which is valid.
- **Fractional tonnage rounding**: hull points (tonnage ÷ 50, rounded down), structure points (rounded
  up), and small-craft fuel (rounded to 0.1 ton) must round per the SRD, not by ad-hoc truncation.
- **Missing required systems**: a starship without a jump drive, or any powered ship without a power
  plant, is invalid and must be reported as such.
- **Armor increments**: armor requested in a non-5% increment, or below the 1-ton-per-5% minimum, must
  be normalized or rejected per the SRD.
- **Fuel for a stated jump range**: jump fuel scales with the intended jump distance (0.1 × hull ×
  jump number); the tool must state the assumed range used when reporting fuel.
- **Crew scaling**: engineers scale with drive-plus-plant tonnage, stewards and medics with passenger
  counts; a ship with no passengers needs no steward.
- **Standard vs. custom cost**: the 10% common-design discount applies only when the design is marked
  standard; custom designs do not receive it.

## Clarifications

### Session 2026-07-22

- Q: How should a user provide a full custom ship design (US1 builder) through the CLI? → A: A structured TOML design file (`ship build <file.toml>`), chosen over flat flags for the multi-component design; TOML needs no new runtime dependency (stdlib `tomllib` on Python 3.13).
- Q: What output should the CLI produce for a built or generated ship? → A: A human-readable ship sheet by default, plus an option to emit the design as a builder-compatible TOML file; a randomly generated ship can be round-tripped into an editable design file, so the design schema MUST be able to represent any generated ship.

## Requirements *(mandatory)*

### Functional Requirements

**Rules source and fidelity**

- **FR-001**: The tool MUST implement the Cepheus Engine "Ship Design and Construction" rules as the
  sole authority for all tables, formulas, limits, and terminology, per the project's SRD-fidelity
  principle.
- **FR-002**: Where the SRD defers a step to referee discretion (e.g. crew role assignment beyond the
  stated minimums, mission-specific fittings), the tool MUST NOT invent rules; such steps are out of
  automated scope and MUST be documented as omitted.

**Deterministic builder (P1)**

- **FR-003**: The tool MUST let a caller specify a standard hull size from the SRD hull table (100 to
  5,000 tons) and a hull configuration (distributed, standard, or streamlined), applying the
  configuration's cost modifier.
- **FR-004**: The tool MUST let a caller add jump drive, maneuver drive, and power plant by SRD drive
  code, deriving each drive's performance rating from the hull size, and MUST enforce that the power
  plant rating equals or exceeds the higher of the jump and maneuver drive ratings.
- **FR-005**: The tool MUST require a jump drive and a power plant for starships, and a power plant for
  any powered craft, reporting an invalid design when a required system is absent.
- **FR-006**: The tool MUST compute jump fuel as 0.1 × hull tonnage × jump distance and power-plant
  fuel from the power-plant tonnage and a stated number of weeks (minimum two weeks for starships),
  and MUST report the jump range assumed.
- **FR-007**: The tool MUST size and cost the bridge from the hull size per the SRD stepped table, and
  MUST let a caller choose a computer model (with optional jump-control and hardened options) and add
  compatible ship software within the computer's rating.
- **FR-008**: The tool MUST let a caller add armor by type (titanium steel, crystaliron, bonded
  superdense) in 5% tonnage increments with the SRD protection and cost, plus the armor options
  (reflec, self-sealing, stealth), and MUST compute hull points (tonnage ÷ 50, rounded down) and
  structure points (tonnage ÷ 50, rounded up).
- **FR-009**: The tool MUST let a caller add electronics packages, staterooms (4 tons, includes life
  support), low passage berths, emergency low berths, and additional fittings from the SRD list
  (e.g. armory, fuel scoops, fuel processors, laboratory, library, luxuries, vehicle hangar,
  detention cells, vault), each with its SRD tonnage and cost.
- **FR-010**: The tool MUST let a caller add turrets (single, double, triple, pop-up, and fixed
  mountings) and turret weapons and ammunition (pulse/beam laser, sandcaster, particle beam, missile
  rack, missiles by type), enforcing one hardpoint per 100 tons of hull.
- **FR-011**: The tool MUST treat all tonnage not consumed by other components as cargo capacity and
  report it.
- **FR-012**: The tool MUST compute minimum crew (pilot, engineer, gunners, and — where the ship's
  contents require them — navigator, medic, steward) per the SRD crew rules.
- **FR-013**: The tool MUST compute total cost in MCr as the sum of all components and MUST apply a 10%
  discount only when the design is marked as a common/standard design.
- **FR-014**: The tool MUST report build time from the SRD hull table.
- **FR-015**: The tool MUST reject any design whose combined component tonnage exceeds the hull
  tonnage, and MUST report which constraint each rejected design violates (over-allocation, drive/plant
  mismatch, hardpoint limit, missing required system, or an armament disallowed for the hull class).

**Random generator (P2)**

- **FR-016**: The tool MUST generate a complete, rules-legal ship by selecting components and building
  them through the same deterministic engine used by the builder, so every generated ship passes the
  same validation.
- **FR-017**: Random generation MUST be reproducible: the same seed MUST always yield the same ship,
  using the project's existing reproducible-chance mechanism. When no seed is supplied, the tool MUST
  report the seed it used.
- **FR-018**: The tool MUST allow constraining random generation to a requested hull size while keeping
  the result rules-legal.

**Small craft (P3)**

- **FR-019**: The tool MUST support the modified small-craft rules for hulls of 10–95 tons: cockpits in
  place of a bridge, maneuver drive and power plant with no jump drive, the small-craft fuel minimum
  (one week), and small-craft armament restrictions (energy-weapon limits by power plant; no bay
  weapons). Both the builder and the random generator MUST support small craft.

**Bay weapons and screens (P3)**

- **FR-020**: The tool MUST support 50-ton weapon bays (missile bank, particle, meson, fusion) and
  defensive screens (meson screen, nuclear damper), accounting for their tonnage, cost, hardpoint, and
  fire-control requirements, and MUST reject bay weapons on small craft.

**Interface**

- **FR-021**: All ship-design logic MUST be usable as a library independent of any command-line or
  other delivery layer; the command-line interface MUST only route input to that library and format
  its output. The builder MUST accept a custom design as a structured TOML design file (parsed with
  the standard-library `tomllib`, introducing no new runtime dependency), and MUST report a clear
  error for a malformed or schema-invalid design file.
- **FR-022**: A completed ship MUST be presentable as a human-readable ship sheet listing hull and
  configuration, drives and performance, power plant, fuel, computer and software, electronics, crew,
  quarters, fittings, armaments, tonnage summary (used/cargo), hull/structure points, total cost, and
  build time. The CLI MUST also, on request, emit a completed ship as a builder-compatible TOML design
  file so it can be saved, edited, and rebuilt.
- **FR-023**: A randomly generated ship (FR-016) MUST be emittable as a builder-compatible TOML design
  file that, when fed back to the builder, reproduces the same ship; the design-file schema MUST be
  expressive enough to represent any ship the random generator can produce.

### Out of Scope (v1)

- Alternative drives (warp, teleport, hyperspace).
- Alternative power plants (fission, antimatter).
- A named catalog of canonical standard designs (Scout/Courier, Free Trader, etc.); v1 supports custom
  designs with a manual standard-design discount flag. A catalog may follow later.
- Deck plans, spacecraft combat resolution, and pricing of trade cargo.

### Key Entities *(include if feature involves data)*

- **Ship**: a complete design. Attributes: hull size and configuration, drives and their performance
  ratings, power plant, fuel loads (jump and power), bridge/cockpit, computer and software,
  electronics, armor, quarters (staterooms, low berths), fittings, armaments (turrets, weapons, bays,
  screens), cargo tonnage, crew, hull and structure points, total cost, build time, standard/custom
  flag.
- **Hull**: a size class (tons, code, base cost, build time) with a configuration modifier and derived
  hardpoint count and hull/structure points.
- **Drive** (jump, maneuver, power plant): a coded component whose tonnage, cost, and rating derive
  from the drive code and hull size, subject to the power-plant requirement.
- **Component**: any tonnage-and-cost-bearing addition (armor, bridge, computer, software, electronics,
  quarters, fittings, turret, weapon, bay, screen) drawn from an SRD table.
- **Design constraint**: a rule the builder enforces (tonnage budget, hardpoint limit, power-plant
  requirement, required-system presence, small-craft/large-ship armament eligibility).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can produce a complete, valid ship sheet for a standard hull from a set of
  component choices in a single command.
- **SC-002**: For at least three hand-worked SRD reference designs (a small starship, a mid-size trader
  or scout, and a larger armed ship), the tool's tonnage, cost, crew, fuel, and hull/structure points
  match the worked figures exactly.
- **SC-003**: 100% of randomly generated ships pass the builder's own validation (no generated ship is
  ever rules-illegal).
- **SC-004**: Random generation is fully reproducible: the same seed yields byte-identical ship sheets
  across separate runs, 100% of the time.
- **SC-005**: Every design that violates an SRD constraint is rejected with a message naming the
  specific violated rule, with no false acceptances across the reference test set.
- **SC-006**: Adding or adjusting an SRD table entry (a new hull size, weapon, or fitting) requires
  only changing the corresponding data, with no change to the generation or costing logic.
- **SC-007**: Generating a single ship completes effectively instantly (well under one second).
- **SC-008**: A ship emitted as a TOML design file and fed back to the builder reproduces the same
  ship sheet, 100% of the time, including for randomly generated ships (design round-trip is lossless).

## Assumptions

- The Cepheus Engine SRD "Ship Design and Construction" page (linked above) is the complete and
  authoritative rules source; no house rules are introduced.
- The tool is a design calculator and generator, not a combat simulator or fleet manager; it computes
  static ship characteristics only.
- Costs are reported in the SRD's units (MCr / Cr) with no inflation, financing, or campaign-economy
  modeling.
- When a design does not state an intended jump range for fuel, the tool assumes a single jump at the
  ship's full jump rating and reports that assumption.
- Random component selection aims for rules-legal, plausible ships; it is not required to reproduce any
  specific canonical design or to weight choices toward any particular ship role in v1.
- The feature reuses the project's existing reproducible-chance seam so seeded generation matches the
  determinism guarantees of the existing character and world generators.
- This feature depends on no new third-party runtime dependencies beyond those already used by the
  existing command-line tool.
