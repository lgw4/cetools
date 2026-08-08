# Feature Specification: Vehicle Design System

**Feature Branch**: `001-vehicle-design`

**Created**: 2026-08-05

**Status**: Draft

**Input**: User description: Decisions brief, "Vehicle Design System module"—a new vehicles domain implementing Chapter 1 of the Cepheus Engine Vehicle Design System, with a thin `cetools vehicle` CLI, a re-derived fifteen-vehicle catalog, and seeded generation.

## Clarifications

### Session 2026-08-07

- Q: Where should the fifteen catalog design files live, and can a referee reach them from the
  command line without knowing a file path? (FR-021) → A: Installed with the package inside the
  vehicles domain, reachable from the CLI by name, with a way to list what is available.
- Q: Are the fifteen published stat blocks transcribed as expected-value test data so every figure
  is compared automatically, or is the divergence page the only place a published number is written
  down? (SC-002, FR-020a) → A: Transcribe all fifteen; a test compares every figure and fails on any
  mismatch not listed on the divergence page.
- Q: When generation is given a seed and no constraints, how much of the vehicle is rolled—the
  structural spine only, every category independently, or a role-appropriate loadout? (FR-026,
  US3) → A: Roll a vehicle role first, then fill each category from a loadout profile that fits
  that role.
- Q: Which file is the divergence page, and does it join the three documents the docs check already
  maintains? (FR-020, FR-020a) → A: A new top-level `DIVERGENCES.md`, added to the check's
  maintained-documents list the docs check reads, opening with the vehicles section.
- Q: Does the build command offer a way to see the component-by-component table, or is the
  description paragraph the only prose output? (FR-025) → A: An opt-in flag prints the component
  table beneath the description paragraph.

### Session 2026-08-07 (checklist pass)

Raised by the pre-tasks requirements checklist, [checklists/pre-tasks.md](./checklists/pre-tasks.md).

- Q: FR-026b names roles by example and never fixes the set, which leaves SC-011 uncheckable. Which
  roles exist? → A: Six, mirroring the catalog's own spread so that each of the fifteen published
  vehicles falls in exactly one: civil transport, military ground, military air, grav utility,
  aircraft, industrial.
- Q: FR-026c requires roles documented in user-facing prose; a role is not a divergence, so which
  page carries them? → A: `DIVERGENCES.md`, in a generation-policy section, keeping every "this is
  cetools, not the SRD" statement on one page.
- Q: Where the construction chapter contradicts itself, which reading wins? → A: Prose in the same
  chapter beats a table; where nothing contradicts, the table is transcribed as printed. Recorded
  as a rules divergence either way (FR-017a).

### Session 2026-08-07 (analysis pass)

Raised by `/speckit-analyze` and settled against the SRD text rather than by judgment. Each changed
a requirement rather than only a task.

- Q: FR-003 said "forty tables" and made the count the completeness test, but three of the forty were
  out of scope and two more merge. What is the number? → A: The chapter prints forty. Thirty-eight
  are transcribed as thirty-seven constants; the two missile play tables are the only exclusions,
  and Submersible Dive Depth is transcribed on FR-003's own watercraft clause (FR-003).
- Q: The six option families—configuration, armor, drive, control, computer, armament—are prose
  definition lists, not tables, so they fell outside FR-003's count and had no vocabulary, no
  validation and no price rule. Are they in? → A: In, and required: the build cannot price a design
  without them and three description slots render from them. Thirty-four entries in six constants,
  carrying modifier semantics rather than fixed figures (FR-003a).
- Q: Is `standard_design` one flag or two? FR-007 discounted on it and FR-008 multiplied build time
  by ten on "custom-made," while an edge case asserted the two designs differ *only* in price. → A:
  One flag. The chapter defines base construction time as being "for mass production of a standard
  design," so the election governs discount, fee and build time together (FR-007, FR-008).
- Q: The chapter charges a new design a specialist's fee of "approximately 1% of the final price of
  the vehicle, to a minimum of Cr100," and the description template asks for a price "including
  discounts and fees." Was the fee in scope? → A: In. It was missing outright; without it the
  printed price is one the chapter's own template calls incomplete (FR-007).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build a vehicle from a design file (Priority: P1)

A referee writes a vehicle design as a TOML file—tech level, chassis size, configuration, armor,
propulsion, power plant, fuel, controls, electronics, crew, accommodations, additional components
and armaments—and asks cetools to build it. cetools applies Chapter 1 of the Vehicle Design
System end to end and prints a Universal Vehicle Description Format paragraph describing the
finished vehicle: its performance codes, its price, its build time, and what it carries.

**Why this priority**: This is the whole feature in one command. Without it there is no catalog to
re-derive and nothing for generation to produce. It is the minimum that delivers value: a referee
can design a vehicle and get a table-ready description.

**Independent Test**: Author one design file by hand, run the build command against it, and confirm
the printed paragraph reports the values Chapter 1's tables produce for those choices. No other
story needs to exist.

**Acceptance Scenarios**:

1. **Given** a valid design file naming components all at or below the vehicle's tech level,
   **When** the referee builds it, **Then** cetools prints the Universal Vehicle Description Format
   paragraph and nothing else, and exits successfully.
2. **Given** a design whose components consume fewer spaces than the chassis provides, **When** it
   is built, **Then** the unused spaces are reported as cargo capacity without the design file
   having declared any cargo.
3. **Given** a design that names a component above the vehicle's stated tech level, **When** it is
   built, **Then** the build fails with an error naming the component, its tech level and the
   vehicle's tech level, and nothing is printed to standard output.
4. **Given** a design that elects the standard-design discount, **When** it is built, **Then** the
   printed price is 10% below the summed component price.
5. **Given** a design whose chassis is only legal under the over-20-ton rules, **When** it is
   built, **Then** the build fails with a message stating that vehicles over 20 tons are not yet
   supported, and saying nothing about watercraft support the design never asked for (FR-013).
6. **Given** a design that omits the tech level, **When** it is built, **Then** the build fails
   with an error saying tech level is required.
7. **Given** a referee who wants to see how a price was reached, **When** they build the design and
   ask for the component table, **Then** the paragraph is printed unchanged and the table follows
   it, and the table's lines sum to the printed price.

---

### User Story 2 - Re-derive the published catalog and see where the book disagrees with itself (Priority: P2)

Fifteen published vehicles—three aircraft, six grav vehicles, five ground vehicles and the tunnel
boring machine—ship with cetools as authored design files rather than as transcribed stat blocks.
They are drawn from Chapters 2, 3, 4 and 6, which is where the Vehicle Design System prints its
worked examples; the construction chapter itself carries none. Every one is rebuilt by the same
builder a referee's own designs go through. Where the published stat block disagrees with what the
construction rules produce, cetools prints the rules' answer, and the disagreement is recorded in
user-facing prose so a referee who notices the difference can tell where it came from.

**Why this priority**: Re-deriving published vehicles is the only check that exercises the tables,
the builder and the description renderer against something the SRD itself printed. It is what turns
the tables from transcription into verified transcription. It also forces genuinely awkward cases
into the design—the TL3 Stagecoach brings animal power, non-powered propulsion and
negative-price components; the G/Carrier, Grav Tank and tracked AFV bring turrets and vehicular
weapons—that a hand-picked example set would have quietly skipped.

**Independent Test**: Build all fifteen shipped design files and compare every figure against the
published stat blocks. Each figure either matches or appears in the divergence list. This is
testable with the build command alone.

**Acceptance Scenarios**:

1. **Given** the fifteen shipped catalog designs, **When** each is built, **Then** every build
   succeeds.
2. **Given** a built catalog vehicle, **When** its figures are compared with the published stat
   block, **Then** every figure either matches or is named in the divergence documentation with the
   published value, the value cetools produces, and why.
3. **Given** the Air/Raft—whose component table totals Cr104,614.5, whose own footnote says
   Cr94,160 and whose prose says KCr94.340—**When** it is built, **Then** cetools prints the price
   the rules produce and every published price figure that differs from it is recorded as a
   divergence. That price is *not* Cr104,614.5 × 0.9: the Air/Raft carries fuel, fuel is exempt from
   the discount (FR-007), and the exact figure follows from the design once authored rather than
   being asserted here.
4. **Given** the Air/Raft, whose published Spaces column does not balance—its component rows leave
   5.11 spaces unaccounted for, and it prints 24.57 spaces of cargo where the remainder is
   29.68—**When** it is built, **Then** cetools prints the remainder per FR-006 and the published
   cargo figure is recorded as a divergence.
5. **Given** any divergence between a published stat block and cetools' output, **When** a referee
   reads the shipped documentation, **Then** the divergence is findable there without reading the
   source.
6. **Given** a referee who knows no file paths, **When** they ask for the list of catalog vehicles
   and then build one by name, **Then** the fifteen names are listed and the named vehicle's
   description is printed.

---

### User Story 3 - Generate a vehicle from a seed (Priority: P3)

A referee needs a vehicle now and does not want to design one. They ask cetools to generate one
from a seed, optionally constraining tech level, chassis size and locomotion, and get back a
complete, legal, described vehicle. The same seed and the same constraints always produce the same
vehicle.

**Why this priority**: Generation is the referee-at-the-table use, and it is what the rest of
cetools does for characters, worlds and ships. It depends on the builder existing, so it follows
P1, and it is not what verifies the tables, so it follows P2.

**Independent Test**: Run generation twice with the same seed and constraints and compare output
byte for byte; run it with different seeds and confirm the vehicles differ. Testable without the
catalog.

**Acceptance Scenarios**:

1. **Given** a seed and no constraints, **When** a vehicle is generated, **Then** a complete legal
   vehicle is described, identified by its tech level and type rather than by a rolled name, and its
   fittings are consistent with the role it was generated for rather than a grab bag across
   unrelated categories.
2. **Given** the same seed and constraints, **When** generation is run again, **Then** the output is
   byte-identical.
3. **Given** constraints on tech level, chassis size and locomotion, **When** a vehicle is
   generated, **Then** the result honors every constraint it can, and any constraint it could not
   honor is reported to the referee.
4. **Given** any generated vehicle, **When** it is built through the build path, **Then** it passes
   the same tech-level and over-20-ton validation a hand-authored design faces.

---

### User Story 4 - Round-trip a design as TOML (Priority: P4)

A referee can ask either command to emit its result as a design file rather than as prose, and can
write that file to a path. Feeding the emitted file back in reproduces the same vehicle. This is
also how the fifteen catalog designs are authored and pinned.

**Why this priority**: It is a small surface over work the other stories already do, but it is what
makes generated vehicles editable and what makes the catalog maintainable, so it is not optional.

**Independent Test**: Generate a vehicle as a design file, build that file, and confirm the
description matches the one generation would have printed.

**Acceptance Scenarios**:

1. **Given** any buildable design, **When** the referee asks for design-file output, **Then** a
   design file is emitted instead of the description paragraph.
2. **Given** an emitted design file, **When** it is built, **Then** the description matches the
   original vehicle's.
3. **Given** a request to write output to a path without asking for design-file output, **Then** the
   command fails with an error explaining that the two go together, matching the existing ship
   behavior.

---

### Edge Cases

- A design whose components consume more spaces than the chassis provides is rejected with an error
  naming the overage, rather than reporting negative cargo.
- A design with no propulsion at all (the animal-drawn TL3 Stagecoach) builds, and its performance
  codes reflect that.
- A component with a negative price (a Chapter 1 case, not a data-entry error) reduces the total
  and is not clamped at zero.
- Spaces are tracked fractionally at twelve spaces to the displacement ton; a design consuming a
  fraction of a space is not silently rounded up or down before the total is taken.
- A design at a tech level below the minimum for its chassis or configuration fails at build rather
  than producing an impossible vehicle.
- An armament that requires a turret but is not mounted in one is rejected.
- Ammunition specified for a weapon that takes none is rejected.
- A mount with no weapon fitted builds, and costs what an empty mount costs.
- A coarse locomotion alias that no longer matches any propulsion row is rejected rather than
  matching nothing and generating an unconstrained vehicle.
- Two designs identical except for the standard-design election differ in final price, in the
  design fee and in build time. The election is one flag with three effects, because the SRD makes
  "standard design" and "mass produced" the same thing: a standard design earns the 10% discount,
  pays no design fee and builds in its base hours, while a new design earns no discount, pays the
  specialist's fee and takes ten times as long (FR-007, FR-008).
- A design naming an option that is not in its family's vocabulary is rejected with an error naming
  the option and the family, exactly as an unknown component is (FR-003a).
- Generation asked for a locomotion that no chassis size in the constrained tech level supports
  reports the conflict rather than silently substituting.
- An unarmored vehicle's build time is its chassis base hours rather than zero, so the armor
  multiplier in FR-008 has a floor of one.
- A design whose role would fill a category its chassis has no room for drops that category rather
  than failing, because a rolled preference is not a promise (FR-032).

## Requirements *(mandatory)*

### Functional Requirements

#### Domain boundary

- **FR-001**: The vehicles domain MUST be a sibling of the ships domain and MUST NOT import from it.
  Configuration, armor, propulsion, turret and weapon vocabularies MUST be defined independently
  within vehicles, even where the SRD reuses a word across the two systems, because no row type is
  shareable: the vehicle tables are keyed by chassis code and by spaces where the ship tables are
  keyed by tonnage. (An earlier reading of this requirement justified it by saying vehicle armor
  varies by type and tech level. It varies by type; tech level gates availability, as it does almost
  everywhere else in the chapter. The conclusion stands for the stronger reason given here.)
- **FR-002**: Every capability MUST be reachable as a library function without a process boundary,
  and the command-line surface MUST contain no rules logic.

#### Tables and construction

- **FR-003**: The construction chapter prints forty tables. **Thirty-eight** MUST be transcribed as
  data, as **thirty-seven** module constants, because the two Drive Performance tables are one table
  split for page width and merge into one constant. The two that are not transcribed are Missile
  Time to Impact and Missile To-Hit, which resolve an attack at the table and are out of scope by
  FR-010's test. Rows that no v1 catalog vehicle or generation path exercises MUST be transcribed,
  and so MUST rows that are legal only for watercraft or only above 20 tons, which are then refused
  at build time (FR-013); the Submersible Dive Depth table is transcribed on that clause and read by
  nothing. "Complete" is checkable against the count: thirty-seven constants over thirty-eight
  tables, not a judgment made at review.
- **FR-003a**: Six option families are printed as prose definition lists rather than as tables, and
  MUST be transcribed as data all the same, because the build cannot price a design without them:
  **configuration options** (11), **armor options** (5), **drive options** (10), **control options**
  (1), **computer options** (1) and **armament options** (5). Thirty-three entries, plus Extended
  Operational Environment Range, which FR-010 keeps in scope and which the chapter prints under
  Atmospheres and Aircraft rather than with the drive options it belongs with; it is transcribed as
  a drive option and the relocation recorded at the transcription site. Thirty-four entries in six
  constants, and that count is checkable the same way FR-003's is.

  These are modifiers rather than fixed rows, and the row type MUST carry that: an option's price
  is a percentage of chassis price, a figure per ton of chassis, a figure per space of chassis, or a
  flat figure, and its space cost is a figure, a percentage of chassis spaces, or nothing. An option
  naming no entry in its family MUST be rejected at build with the offending name and the legal set,
  which is what makes FR-013's refusal of the submersible, hydrofoil and wave-piercing hull
  configuration options a membership test rather than a special case.
- **FR-004**: The build MUST follow Chapter 1's own order: chassis and spaces, configuration
  (open or closed), armor, propulsion and power plant with their performance codes, fuel, controls,
  communications, sensors, computer and software, crew and accommodations, additional components,
  armaments, cargo as the remainder, then final price and build time.
- **FR-005**: Chassis capacity MUST be computed at twelve spaces to the displacement ton, and space
  consumption MUST be tracked fractionally rather than rounded per component.
- **FR-006**: Cargo capacity MUST be derived as the unconsumed space remainder; a design file MUST
  NOT declare cargo.
- **FR-007**: The standard-design election is **one flag with three effects**, because the chapter
  makes "standard design" and "mass produced" the same thing. A design that elects it:
  - takes the 10% discount, applied to the summed price of the *discountable* components only. Fuel
    and weapon ammunition are exempt; the rules say so in as many words ("Fuel and weapon ammunition
    are not covered by the Std Design Discount"). Several published examples appear to discount the
    whole total instead, so honoring this rule produces a divergence on every catalog vehicle that
    carries fuel or ammunition and elects the discount.
  - pays no design fee.
  - builds in its base hours rather than ten times them (FR-008).

  A design that does not elect it MUST instead carry a **design fee**: the chapter requires a new
  design be drawn up by a specialist, "approximately 1% of the final price of the vehicle, to a
  minimum of Cr100." The fee MUST be added after the discount arithmetic, MUST be its own line in
  the component table, and MUST NOT itself be discountable. The universal description format asks
  for a price "including discounts and fees," which is the slot this fills; a build that omitted it
  would print a number the chapter's own template says is incomplete. The month the specialist takes
  is elapsed time before construction starts, not construction time, and is out of scope.
- **FR-008**: Build time MUST be produced alongside price, derived as the chassis's base
  construction hours multiplied by the vehicle's total armor, times ten again when the vehicle is
  custom-made. "Custom-made" is not a field of its own: it is the absence of the FR-007
  standard-design election, and the two MUST read the same flag, because the chapter defines the
  base construction time as being "for mass production of a standard design." The armor multiplier
  MUST have a floor of one, so an unarmored vehicle takes its chassis base hours rather than zero.
  The chapter is self-contradictory here—its prose says to multiply by *additional* armor while its
  own worked example multiplies by a *total* of 12 Armor—and the worked example's reading is the one
  adopted, recorded as a rules divergence under FR-017a.
- **FR-009**: Components priced negatively by Chapter 1 MUST reduce the total rather than being
  floored at zero.
- **FR-010**: Rules that only change a printed number—lift envelope sizing, speed by drive
  performance—MUST be implemented. The test for whether a chapter rule is in scope is whether it
  feeds back into component selection or into a figure the description prints: if it does, it is
  construction and it stays; if it resolves an action at the table instead, it is play and it goes.
  Two rules that read as play rules are construction items by this test and stay in, because they
  are bought as components: Off-Road Capability and Extended Operational Environment Range. Both are
  transcribed as drive options under FR-003a.

#### Validation

- **FR-011**: Tech level MUST be a required field on every design; a design without one MUST fail
  to build.
- **FR-012**: Naming any component above the vehicle's tech level MUST be a build error, not a
  warning.
- **FR-013**: Two scope limits MUST be enforced at build time, each with a message that names the
  limit it actually hit rather than a combined message naming both:
  - **Over 20 tons.** The chassis table stops at 20 tons, and the hull, structure and drive
    performance tables stop with it, so this is decidable as "no chassis row for this displacement"
    rather than as a special case. The message MUST say that vehicles over 20 tons are not yet
    supported.
  - **Watercraft.** A fixed set of transcribed-but-refused names: the submersible, hydrofoil and
    wave-piercing hull configuration options; screw propeller and sails propulsion; the underwater
    sensor package; the torpedo rows of the ordinance bay table; and floats or pontoons. The message
    MUST name watercraft as the missing capability and MUST name the offending component.
- **FR-014**: A design consuming more spaces than its chassis provides MUST be rejected with an
  error identifying the overage.

#### Armaments

- **FR-015**: Turrets, gun ports, ordinance bays and missile racks MUST be expressible in a design
  file as mounts, each mount carrying the vehicular weapon fitted to it, and each weapon carrying
  its own ammunition. Ammunition is a property of the weapon that fires it, not a free-standing
  component line, so a magazine cannot exist in a design without the weapon it feeds.
- **FR-016**: Weapon and mount combinations the construction rules do not permit MUST be rejected at
  build time, as MUST ammunition specified for a weapon that takes none. Both tests are decidable by
  table membership rather than by judgment: a weapon is permitted in a mount when it appears in that
  mount kind's own weapon table—gun port weapons for a gun port, turret weapons for a turret,
  ordinance bay weapons for an ordinance bay, missiles for a missile rack—and a weapon takes
  ammunition when its family has a row in the weapon ammunition table.

#### SRD fidelity and divergence

- **FR-017**: Where a published stat block contradicts the construction rules, or contradicts its own
  arithmetic, cetools MUST print what the rules produce. The construction chapter governs the
  worked examples, never the reverse.
- **FR-017a**: The construction chapter also contradicts *itself*, in at least nine places found so
  far, and FR-017 does not settle those because both readings are the rules. Where a table and prose
  in the same chapter give different values for the same quantity, the prose MUST be taken and the
  table's printed value recorded as a divergence. Where nothing in the chapter contradicts a printed
  value, it MUST be transcribed as printed even when it looks like a typo, because "looks like a
  typo" is not a source. Every such decision MUST be recorded at the transcription site and on the
  divergence page.
- **FR-018**: Every divergence a referee could notice MUST be recorded in user-facing prose, naming
  the published value, the value cetools produces, and the reason. This covers both classes: a
  worked example disagreeing with the rules (FR-017) and the rules disagreeing with themselves
  (FR-017a).
- **FR-019**: Divergences of either class MUST NOT be exposed as a selectable house-rule policy.
  Neither class is a departure from the SRD: in the first cetools implements the rules and the
  example is wrong, and in the second the chapter offers two readings and cetools takes the one its
  own prose supports. A policy switch would offer a referee the choice to be wrong. The
  documentation obligation in FR-018 is what discharges the constitution's requirement here, and it
  binds in full.
- **FR-020**: Divergence documentation MUST live on a documentation page of its own: a new top-level
  `DIVERGENCES.md`, opening with the vehicles material so later domains have somewhere to record
  their own. The vehicles material MUST carry three sections, because three unlike things are being
  recorded: **worked examples** (FR-017), **rules defects** (FR-017a), and **generation policy**
  (FR-026c), the last being choices cetools makes where the SRD is silent rather than disagreements
  with it.
- **FR-020a**: `DIVERGENCES.md` MUST join the maintained documents the existing documentation check
  reads, so it inherits every prose rule already applied to them—symbol resolution, tight dashes
  and American spelling—and so a divergence whose prose no longer matches what cetools produces
  fails the quality gate rather than shipping. The check's own description in the maintained docs
  MUST be updated to name the new page.
- **FR-020b**: The two enforcement paths—the stat-block comparison test and the documentation
  check—MUST read the same rows, so they cannot disagree about what has been documented. The worked
  examples and rules defects sections MUST therefore be machine-readable: one table per section with
  the columns Vehicle, Figure, Published, cetools and Why. The generation-policy section is prose
  and is not parsed. The transcribed published figures MUST be readable by the documentation check
  without importing from the test tree.

#### Catalog

- **FR-021**: Fifteen published vehicles MUST ship as authored design files: three aircraft (biplane,
  helicopter, twin-engine jet), six grav vehicles (Air/Raft, G/Carrier, grav bike, grav floater,
  grav tank, speeder), five ground vehicles (tracked AFV, tracked ATV, ground car, stagecoach, van)
  and the tunnel boring machine. They come from Chapters 2, 3, 4 and 6. Chapter 5's five watercraft
  are deliberately excluded, four of them being over 20 tons. These files MUST be installed with the
  package as data inside the vehicles domain, not kept as test fixtures, and MUST be reachable as a
  library function that loads a catalog design by name and one that lists the available names.
- **FR-021a**: Each of the fifteen published stat blocks MUST be transcribed as expected-value data
  alongside its design file, figure by figure. "Figure" means each of the values the stat block
  itself labels: spaces, cargo, the component-table total, the discounted price, the prose price,
  agility, speed, armor, crew and build time. A vehicle whose stat block omits one simply has no
  entry for it. A test MUST build every catalog design and compare every transcribed figure against
  what the builder produces; any mismatch MUST fail unless that vehicle and figure appear on the
  divergence page with the same published and produced values. Transcribed figures MUST be verified
  against the SRD text rather than against another implementation.
- **FR-021b**: Each catalog vehicle MUST be addressable by a stable, lowercase, hyphenated name
  derived from the vehicle's published name. The name is a compatibility surface—a referee will put
  it in a script—so it MUST NOT change once shipped.
- **FR-022**: Catalog vehicles MUST be produced by the same builder a referee's designs go through.
  Transcribed stat blocks are not acceptable.
- **FR-023**: The catalog MUST include the TL3 Stagecoach, which requires animal power, non-powered
  propulsion and negative-price components, and the G/Carrier, Grav Tank and tracked AFV, which
  require turrets and vehicular weapons.

#### Command-line surface

- **FR-024**: A `vehicle` command group MUST sit alongside the existing `character`, `world` and
  `ship` groups, named in the singular to match them.
- **FR-024a**: Building MUST accept a catalog vehicle by name as an alternative to a filesystem
  path, and the command group MUST offer a way to list the available catalog names. Naming a
  catalog vehicle that does not exist MUST fail with an error listing the names that do. A catalog
  vehicle selected by name MUST go through the same builder and print the same description as
  building its installed design file by path.
- **FR-025**: Building a design MUST print the Universal Vehicle Description Format paragraph, with
  no component table by default. The chapter lays that paragraph out slot by slot, and cetools MUST
  fill the slots that describe a vehicle: tech level and descriptive name; configuration, chassis
  displacement, hull and structure; configuration options; power plant type and drive code;
  propulsion type and drive code; top speed, cruising speed and agility DM; drive options; fuel
  volume in kiloliters, fuel type and duration; controls, communications and its range, sensors and
  its comms DM, and computer model; accommodations by type and number; weapon points and the
  armaments and ammunition fitted; additional components; cargo capacity in both tons and
  kiloliters; armor type, level and options; crew total and positions; passengers by accommodation;
  price in KCr, inclusive of the discount and of the design fee, which is what the template's own
  "(including discounts and fees)" parenthesis asks for (FR-007); and construction time in hours.
  Three of these slots—configuration options, drive options, and the options half of armor type,
  level and options—are rendered from the vocabularies FR-003a transcribes, which is the second
  reason those vocabularies cannot stay unmodeled strings.
- **FR-025a**: An opt-in flag MUST print the component table beneath the description paragraph:
  every component line with the spaces it consumes and the price it costs, then the summed price,
  the discount if elected, the design fee if charged, the final price and the build time. The table
  MUST make the discount legible given FR-007, distinguishing discountable lines from exempt ones
  rather than showing a single 10% deduction that does not reconcile, and MUST show the design fee
  as its own line below the discount, since it is charged on the discounted total. The flag MUST NOT change the paragraph itself, and
  it MUST be available on both commands that describe a vehicle, building and generation. Asking for
  the table and for design-file output at once is an error, stated with the rest of the argument
  rules in FR-028, which is their single home.
- **FR-025b**: Four slots in the published template MUST be omitted, because they are starship
  concepts that reached the vehicle template by copy-paste and have no vehicle meaning: tons
  allocated for fire control, the "installed on the hardpoints" sentence (vehicle armaments are
  already covered by the weapon-points slot), screens, and small craft hangars. The template also
  says "This ship has" in the screens sentence, which is the tell. This omission MUST be recorded as
  a rules defect under FR-017a.
- **FR-026**: Generation MUST accept a seed and constraints on tech level, chassis size and
  locomotion.
- **FR-026a**: The locomotion constraint MUST accept the propulsion table's own sixteen names, and
  MUST also accept exactly these nine coarse aliases, each standing for a group of those names:
  `grav`, `wheeled`, `tracked`, `rotor`, `jet`, `legged`, `rail`, `mole`, `non-powered`. Watercraft
  propulsion is transcribed but no alias points at it. An alias MUST be rejected if it no longer
  names any propulsion row, so the two cannot drift apart silently. Both vocabularies MUST be
  documented in the vehicle section of `README.md`, which is the page a referee reaching for
  `--locomotion` will already have open, and both MUST be reachable as library functions so the
  documentation names them from the tables rather than from a second hand-maintained list.
- **FR-026b**: Generation MUST roll a vehicle role first and then fill each construction category
  from a loadout profile that fits that role, so that armaments, electronics, accommodations and
  additional components are consistent with what the vehicle is for. There are exactly six roles,
  chosen so that each of the fifteen catalog vehicles falls in exactly one: **civil transport**,
  **military ground**, **military air**, **grav utility**, **aircraft**, **industrial**. A role MUST
  be selected only from those its constraints permit, and every generated vehicle MUST remain
  buildable by the ordinary build path.
- **FR-026c**: The roles and their loadout profiles are cetools' generation policy, not SRD rules.
  They MUST live in the generator rather than in the transcribed tables, MUST NOT influence the
  build path, and MUST be documented in the generation-policy section of `DIVERGENCES.md` (FR-020),
  so that every "this is cetools, not the book" statement a referee might need sits on one page.
- **FR-026d**: A loadout profile MUST decide, for its role: which chassis sizes are eligible, which
  locomotion families are eligible, whether armaments are drawn at all, which accommodations are
  eligible, and which additional components are eligible. A generated vehicle MUST carry only
  components its role's profile admits, which is what makes SC-011 checkable rather than a matter of
  taste.
- **FR-027**: Generation MUST be non-interactive. No interactive design wizard is in scope.
- **FR-028**: Both commands MUST offer design-file output and a write-to-path option, mirroring the
  existing ship behavior. The argument rules MUST be checked before any rules work happens, and
  these are all of them: a write path requires design-file output, and is an error without it; the
  component table and design-file output are mutually exclusive (FR-025a); and building requires
  exactly one source, a file path or a catalog name, so neither and both are errors. The
  write-path error message MUST match the existing ship wording rather than inventing a second
  phrasing for the same rule.
- **FR-029**: Generated vehicles MUST be identified by tech level and type, as the SRD identifies
  them. No name generation is in scope.
- **FR-029a**: Standard output MUST carry the artifact and nothing else—the description paragraph,
  that paragraph with the component table, the design file, or the catalog listing—so that any
  command can be piped. Everything else MUST go to standard error: diagnostics, an auto-chosen seed,
  and the unmet-constraint report. A command MUST exit non-zero when it produced no artifact, and
  zero when it did. Reporting an unmet constraint MUST NOT change the exit code, because a vehicle
  really was produced and must still pipe.

#### Determinism

- **FR-030**: Every random decision MUST pass through the existing rolls seam and MUST be named
  there. New roll names MUST be added for the vehicle decisions, and the set MUST cover every field
  generation chooses, including the two a category-by-category reading of FR-026d overlooks:
  endurance in weeks, from which fuel volume follows, and crew count. Design options (FR-003a) are
  deliberately *not* drawn: a role fills categories, and an option is a refinement within one, so
  drawing options would widen the generator without making a vehicle more usable at the table.
- **FR-030a**: The role MUST be drawn before any other vehicle decision. The seam draws from one
  stream, so draw order is load-bearing for reproducibility, and the role decides every pool drawn
  after it. This ordering is a requirement rather than an implementation detail because changing it
  silently invalidates every pinned baseline.
- **FR-031**: The same seed and the same constraints MUST produce byte-identical output across runs.
  This is not a claim that one seed gives the same vehicle under *different* constraints: a pinned
  constraint consumes no dice, so two runs on one seed diverge below the first pin. Only the
  unconstrained sequence is stable across changes, and that is what a pinned baseline can cover.
- **FR-032**: Generation MUST distinguish two kinds of constraint failure, because they are not
  alike and a referee needs to tell them apart:
  - **Refused outright**, as an error, when the constraint is impossible from the tables alone: an
    unknown chassis code, a locomotion alias matching no propulsion row, a tech level below a
    chassis minimum. Nothing is generated.
  - **Degraded and reported**, when the constraint depends on the running spaces budget. A vehicle
    is still produced, and every constraint that could not be honored is reported with what was
    asked, what was given instead, and why.

  A pin is a promise and a roll is only a preference: a drawn value that will not fit is dropped
  silently and is not reported as an unmet constraint.

#### Numbers

- **FR-033**: Quantities MUST be carried as floating-point values throughout, matching ships, and
  rounded only at the display edge.
- **FR-034**: The display edge MUST round at a fixed precision high enough that no SRD figure is
  lost and no float-accumulation artifact is shown, with trailing zeros stripped, no dangling
  decimal point and no scientific notation. Money MUST additionally carry thousands separators.
  This matters more here than in ships: spaces run at twelve to the displacement ton and components
  are priced in fractions of a space, so the Air/Raft's true component sum is Cr104,614.51 where the
  book prints Cr104,614.5.

### Key Entities

- **Vehicle Design**: The referee's authored input. Carries tech level (required), chassis size,
  configuration, and the chosen components and options across every Chapter 1 category, plus the
  standard-design election, which is at once the discount election, the design-fee election and the
  mass-production election (FR-007). Does not carry cargo.
- **Vehicle**: The built result. Carries the design's choices plus everything derived from
  them—consumed and remaining spaces, performance codes, crew and passenger capacity, cargo,
  total price, design fee, build time—and is what the description paragraph is rendered from.
- **Component**: One line of a design: a name, a tech level, a space cost, a price, and whatever
  category-specific attributes Chapter 1 gives it. Space cost and price may be fractional; price may
  be negative.
- **Design Option**: A modifier on a component category rather than a component of its own, printed
  in the chapter as prose (FR-003a). Carries a name, a tech level where one is given, and a price
  and space cost expressed as a percentage of chassis price, a figure per ton or per space of
  chassis, or a flat figure. Belongs to exactly one of six families, and is legal only within it.
- **Mount**: A turret, gun port, ordinance bay or missile rack. Carries the vehicular weapon fitted
  to it. A mount may exist without a weapon; a weapon may not exist outside a mount.
- **Weapon**: A vehicular weapon fitted to a mount, carrying its own ammunition. Ammunition belongs
  to the weapon rather than standing alone, so a magazine without a weapon is not expressible.
- **Catalog Entry**: One of the fifteen installed design files, addressable by a stable name, paired
  with a figure-by-figure transcription of the published stat block it re-derives.
- **Divergence**: A recorded disagreement, of one of two classes: a published stat block against
  cetools' output, or the construction chapter against itself. Either way it names which vehicle or
  table, which figure, the published value, the produced value, and why they differ.
- **Vehicle Role**: What a generated vehicle is for. Exactly six: civil transport, military ground,
  military air, grav utility, aircraft, industrial. A cetools generation construct, not a Chapter 1
  concept.
- **Loadout Profile**: The pools one role draws from—eligible chassis sizes, eligible locomotion
  families, whether armaments are drawn at all, eligible accommodations, eligible additional
  components. One per role, and the thing SC-011 is checked against.
- **Generation Constraints**: Tech level, chassis size and locomotion limits supplied to generation,
  along with the seed.
- **Unmet Constraint**: A constraint generation could not honor, reported back to the referee.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All fifteen catalog designs build successfully, both as installed files and when
  selected by name from the command line, and every one of the fifteen names appears in the listing.
- **SC-002**: Across the fifteen, every published figure either matches cetools' output or appears in
  the divergence documentation. Figures are compared within an explicit tolerance rather than by
  exact equality, because both sides are floating-point and the book rounds its own printed totals.
  The tolerance is `math.isclose(rel_tol=0.0, abs_tol=0.01)`, named as a module constant in the
  comparison test: one centicredit, which absorbs the Air/Raft's Cr104,614.51-against-Cr104,614.5
  printing artifact and nothing larger. A figure the book prints to coarser precision than that is
  compared at the precision the book prints it, not at a looser blanket tolerance. Undocumented divergences: zero,
  enforced by the stat-block comparison test and the documentation check together rather than by
  review—the comparison test catches a divergence nobody noticed, the documentation check catches a
  divergence whose prose has gone stale.
- **SC-003**: The same seed and the same constraints produce byte-identical output on repeated runs.
  Verification is in two parts, because a pinned baseline cannot cover both: the unconstrained path
  is pinned per seed in the manner of the existing design baselines, and the constrained paths are
  verified by running generation twice and comparing, since a pinned constraint consumes no dice
  (FR-031).
- **SC-004**: No design naming a component above its vehicle's tech level builds successfully.
- **SC-005**: No design requiring the over-20-ton rules builds successfully, and no design naming a
  watercraft-only component builds successfully. Each is rejected with the message for the limit it
  actually hit: an oversized land vehicle is told it is oversized, and is not told about watercraft
  support it never asked for (FR-013).
- **SC-006**: Every construction table row that no catalog vehicle and no generation path exercises
  is covered by a test that fails when that row's values are altered. The set is identified rather
  than estimated: the exercised rows are collected by building all fifteen catalog vehicles and
  running generation across seeds and recording which rows were read, and the remainder is what
  needs the direct test. That remainder MUST be committed as a checked-in fixture the direct tests
  read, rather than left in a scratch file: it is the evidence for this criterion, and a list nobody
  can re-read is not evidence. Coverage of the package stays at or above the 85% floor, and the
  floor is treated as a floor rather than as evidence.
- **SC-007**: A referee can build a design and get a table-ready description in a single command,
  with no component table unless asked for.
- **SC-008**: A design file emitted by either command rebuilds to the identical description.
- **SC-009**: The five-command quality gate passes on the delivered change, including the
  documentation check with the divergence page inside its scope.
- **SC-010**: Every coarse locomotion alias resolves to at least one propulsion row, and all sixteen
  propulsion names and all nine aliases are named in the vehicle section of `README.md`, where the
  docs check already reads them (FR-026a).
- **SC-011**: Every generated vehicle carries only components its role's loadout profile admits, and
  all six roles are named in the generation-policy section of `DIVERGENCES.md` as cetools generation
  choices rather than SRD rules.
- **SC-012**: Every figure the description paragraph prints is reachable without the component
  table, and the paragraph contains no starship slot: no fire control tonnage, no hardpoints
  sentence, no screens, no small craft hangars (FR-025b).

## Assumptions

- **Construction rules only.** The feature implements the Vehicle Design System's construction
  chapter and re-derives the worked examples printed in Chapters 2, 3, 4 and 6. Chapter 5's
  watercraft are out of scope, because four of its five vehicles exceed 20 tons. The over-20-ton
  rules themselves are out of scope: they would require importing small-craft and ship hull and
  drive tables and applying conversion multipliers, and would inherit the known small-craft drive
  tonnage defect.
- **Construction, not play.** Chapter material that resolves play rather than construction is out of
  scope: missile time to impact, missile to-hit, off-road movement, and atmosphere effects on
  aircraft. FR-010 states the test that decides the boundary.
- **No wizard.** Generation is seeded and non-interactive, with no interactive flag. This
  deliberately declines to reproduce the ~1,100-line interactive pattern in the ship CLI a second
  time while extracting that wizard is still an open backlog item.
- **No names.** There is no vehicle names module and no rolled names. Roles are what a vehicle is
  for, not what it is called, so rolling a role does not reintroduce name generation.
- **Appendix A does not ship** as an artifact.
- **Singular CLI namespace.** The command group is `vehicle`, matching `ship` and `world`.
- **Robot brains, drone controllers and cyborg controls are in** as construction data, even though
  no v1 catalog vehicle uses cyborg controls, because Chapter 1's tables ship complete (FR-003).
- **Generation reports unmet constraints.** The absence of an interactive session makes the report
  more necessary, not less, so generation reports them the way ship generation does.
- **One pull request.** The constitution asks that a PR contain one logical change. Comparable work
  in the ships domain runs about 6,300 lines across nine modules, so this will be a large review.
  Splitting it was considered and rejected: the catalog is what verifies the tables, and a builder
  without its catalog is a half-change whose correctness cannot be demonstrated. This is a
  deliberate, reaffirmed call and is stated here so a reviewer is not surprised by the size.
- **Divergences are errata, not house rules.** The constitution requires that a deliberate departure
  from the SRD be a selectable policy. Neither class of divergence is a departure: cetools implements
  the construction rules, the book's worked examples disagree with those rules, and where the rules
  disagree with themselves cetools takes the reading the chapter's own prose supports. The
  constitution's documentation obligation still binds in full (FR-018), and is discharged in prose
  rather than by a policy switch.
- **No non-functional requirements.** There are deliberately none. A build is table lookups and
  arithmetic over tens of components and generation is a single pass, so no throughput, latency or
  concurrency target is stated. Determinism is treated as a correctness property under FR-031 rather
  than as a non-functional one. Nothing here is absent by oversight.

## Dependencies

- The existing rolls seam and its roll-name registry, extended with vehicle roll names.
- The existing design-file baseline testing pattern.
- The existing documentation check, whose maintained-documents list grows from three files to four
  with the addition of `DIVERGENCES.md` (FR-020a). This is the only dependency that changes the
  shared quality gate, so it is the one worth a reviewer's attention.
- The feature also touches, unavoidably and without changing their behavior, the CLI's command
  registration, the roll-name registry above, and the three maintained documents that describe the
  package to its users. These are the registration cost of a new domain rather than dependencies in
  their own right, and they are listed so that the previous bullet is not misread as claiming the
  documentation check is the only file touched outside the vehicles domain.
