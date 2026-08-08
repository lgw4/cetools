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
5. **Given** a design whose chassis or configuration is only legal under the over-20-ton rules,
   **When** it is built, **Then** the build fails with a message stating that watercraft and
   over-20-ton vehicles are not yet supported.
6. **Given** a design that omits the tech level, **When** it is built, **Then** the build fails
   with an error saying tech level is required.
7. **Given** a referee who wants to see how a price was reached, **When** they build the design and
   ask for the component table, **Then** the paragraph is printed unchanged and the table follows
   it, and the table's lines sum to the printed price.

---

### User Story 2 - Re-derive the published catalog and see where the book disagrees with itself (Priority: P2)

Fifteen vehicles published in Chapter 1—three aircraft, six grav vehicles, five ground vehicles
and the tunnel boring machine—ship with cetools as authored design files rather than as
transcribed stat blocks. Every one is rebuilt by the same builder a referee's own designs go
through. Where the published stat block disagrees with what Chapter 1's rules produce, cetools
prints the rules' answer, and the disagreement is recorded in user-facing prose so a referee who
notices the difference can tell where it came from.

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
3. **Given** the Air/Raft—whose component table totals Cr104,614.5, whose 10% discount is
   Cr94,153.05, whose own footnote says Cr94,160 and whose prose says KCr94.340—**When** it is
   built, **Then** cetools prints Cr94,153.05 and the three published figures are recorded as
   divergences.
4. **Given** any divergence between a published stat block and cetools' output, **When** a referee
   reads the shipped documentation, **Then** the divergence is findable there without reading the
   source.
5. **Given** a referee who knows no file paths, **When** they ask for the list of catalog vehicles
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
- Two designs identical except for the discount election differ only in final price.
- Generation asked for a locomotion that no chassis size in the constrained tech level supports
  reports the conflict rather than silently substituting.

## Requirements *(mandatory)*

### Functional Requirements

#### Domain boundary

- **FR-001**: The vehicles domain MUST be a sibling of the ships domain and MUST NOT import from it.
  Configuration, armor, propulsion, turret and weapon vocabularies MUST be defined independently
  within vehicles, even where the SRD reuses a word across the two systems, because the underlying
  tables differ (vehicle armor varies by type and tech level; ship armor does not).
- **FR-002**: Every capability MUST be reachable as a library function without a process boundary,
  and the command-line surface MUST contain no rules logic.

#### Tables and construction

- **FR-003**: The complete tables of Vehicle Design System Chapter 1 MUST be transcribed as data,
  including rows that no v1 catalog vehicle or generation path exercises.
- **FR-004**: The build MUST follow Chapter 1's own order: chassis and spaces, configuration
  (open or closed), armor, propulsion and power plant with their performance codes, fuel, controls,
  communications, sensors, computer and software, crew and accommodations, additional components,
  armaments, cargo as the remainder, then final price and build time.
- **FR-005**: Chassis capacity MUST be computed at twelve spaces to the displacement ton, and space
  consumption MUST be tracked fractionally rather than rounded per component.
- **FR-006**: Cargo capacity MUST be derived as the unconsumed space remainder; a design file MUST
  NOT declare cargo.
- **FR-007**: Final price MUST support the optional 10% standard-design discount, applied to the
  summed component price.
- **FR-008**: Build time MUST be produced alongside price.
- **FR-009**: Components priced negatively by Chapter 1 MUST reduce the total rather than being
  floored at zero.
- **FR-010**: Rules that only change a printed number—lift envelope sizing, speed by drive
  performance—MUST be implemented.

#### Validation

- **FR-011**: Tech level MUST be a required field on every design; a design without one MUST fail
  to build.
- **FR-012**: Naming any component above the vehicle's tech level MUST be a build error, not a
  warning.
- **FR-013**: A configuration or chassis that is only legal under the over-20-ton rules MUST be
  rejected at build time with a message stating that watercraft and over-20-ton vehicles are not
  yet supported.
- **FR-014**: A design consuming more spaces than its chassis provides MUST be rejected with an
  error identifying the overage.

#### Armaments

- **FR-015**: Turrets, gun ports, ordinance bays and missile racks MUST be expressible in a design
  file as mounts, each mount carrying the vehicular weapon fitted to it, and each weapon carrying
  its own ammunition. Ammunition is a property of the weapon that fires it, not a free-standing
  component line, so a magazine cannot exist in a design without the weapon it feeds.
- **FR-016**: Weapon and mount combinations that Chapter 1 does not permit MUST be rejected at build
  time, as MUST ammunition specified for a weapon that takes none.

#### SRD fidelity and divergence

- **FR-017**: Where a published stat block contradicts Chapter 1's rules, or contradicts its own
  arithmetic, cetools MUST print what the rules produce. Chapter 1 is the single source of truth.
- **FR-018**: Every divergence between a published stat block and cetools' output that a referee
  could notice MUST be recorded in user-facing prose, naming the published value, the value cetools
  produces, and the reason.
- **FR-019**: These divergences MUST NOT be exposed as a selectable house-rule policy. They are
  errata in the book's worked examples, not departures from the SRD, and cetools implements the
  rules in both readings.
- **FR-020**: Divergence documentation MUST live on a documentation page of its own: a new top-level
  `DIVERGENCES.md`, opening with the vehicles section so later domains have somewhere to record
  their own. It MUST list every divergence by vehicle and figure with the published value, the value
  cetools produces, and the reason.
- **FR-020a**: `DIVERGENCES.md` MUST join the maintained documents the existing documentation check
  reads, so it inherits every prose rule already applied to them—symbol resolution, tight dashes
  and American spelling—and so a divergence whose prose no longer matches what cetools produces
  fails the quality gate rather than shipping. The check's own description in the maintained docs
  MUST be updated to name the new page.

#### Catalog

- **FR-021**: Fifteen published vehicles MUST ship as authored design files: three aircraft, six
  grav vehicles, five ground vehicles and the tunnel boring machine. These files MUST be installed
  with the package as data inside the vehicles domain, not kept as test fixtures, and MUST be
  reachable as a library function that loads a catalog design by name and one that lists the
  available names.
- **FR-021a**: Each of the fifteen published stat blocks MUST be transcribed as expected-value data
  alongside its design file, figure by figure. A test MUST build every catalog design and compare
  every transcribed figure against what the builder produces; any mismatch MUST fail unless that
  vehicle and figure appear on the divergence page with the same published and produced values.
  Transcribed figures MUST be verified against the SRD text rather than against another
  implementation.
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
  no component table by default.
- **FR-025a**: An opt-in flag MUST print the component table beneath the description paragraph:
  every component line with the spaces it consumes and the price it costs, then the summed price,
  the discount if elected, the final price and the build time. The flag MUST NOT change the
  paragraph itself, and it MUST be available wherever a vehicle is described. Asking for the table
  and for design-file output at once MUST fail with an error explaining that the two are different
  representations of the same vehicle.
- **FR-026**: Generation MUST accept a seed and constraints on tech level, chassis size and
  locomotion.
- **FR-026a**: The locomotion constraint MUST accept the propulsion table's own names, and MUST also
  accept a small set of coarse aliases (grav, wheeled, tracked, rotor and the like) that each stand
  for a group of those names. Both vocabularies MUST be documented, and an alias MUST be rejected if
  it no longer names any propulsion row, so the two cannot drift apart silently.
- **FR-026b**: Generation MUST roll a vehicle role first—civil transport, military ground, grav
  utility, aircraft and the like—and then fill each Chapter 1 category from a loadout profile that
  fits that role, so that armaments, electronics, accommodations and additional components are
  consistent with what the vehicle is for. A role MUST be selected only from those its constraints
  permit, and every generated vehicle MUST remain buildable by the ordinary build path.
- **FR-026c**: The roles and their loadout profiles are cetools' generation policy, not Chapter 1
  rules. They MUST live in the generator rather than in the transcribed tables, MUST NOT influence
  the build path, and MUST be documented in user-facing prose so a referee can tell a generation
  choice from a rule.
- **FR-027**: Generation MUST be non-interactive. No interactive design wizard is in scope.
- **FR-028**: Both commands MUST offer design-file output and a write-to-path option, mirroring the
  existing ship behavior, including the error when a path is given without asking for design-file
  output.
- **FR-029**: Generated vehicles MUST be identified by tech level and type, as Chapter 1 identifies
  them. No name generation is in scope.

#### Determinism

- **FR-030**: Every random decision MUST pass through the existing rolls seam and MUST be named
  there. New roll names MUST be added for the vehicle decisions.
- **FR-031**: The same seed and the same constraints MUST produce byte-identical output across runs.
- **FR-032**: Generation MUST report any constraint it could not honor, since there is no
  interactive session in which to negotiate one.

#### Numbers

- **FR-033**: Quantities MUST be carried as floating-point values throughout, matching ships, and
  rounded only at the display edge.

### Key Entities

- **Vehicle Design**: The referee's authored input. Carries tech level (required), chassis size,
  configuration, and the chosen components across every Chapter 1 category, plus the discount
  election. Does not carry cargo.
- **Vehicle**: The built result. Carries the design's choices plus everything derived from
  them—consumed and remaining spaces, performance codes, crew and passenger capacity, cargo,
  total price, build time—and is what the description paragraph is rendered from.
- **Component**: One line of a design: a name, a tech level, a space cost, a price, and whatever
  category-specific attributes Chapter 1 gives it. Space cost and price may be fractional; price may
  be negative.
- **Mount**: A turret, gun port, ordinance bay or missile rack. Carries the vehicular weapon fitted
  to it. A mount may exist without a weapon; a weapon may not exist outside a mount.
- **Weapon**: A vehicular weapon fitted to a mount, carrying its own ammunition. Ammunition belongs
  to the weapon rather than standing alone, so a magazine without a weapon is not expressible.
- **Catalog Entry**: One of the fifteen installed design files, addressable by a stable name, paired
  with a figure-by-figure transcription of the published stat block it re-derives.
- **Divergence**: A recorded disagreement between a published stat block and cetools' output: which
  vehicle, which figure, the published value, the produced value, and why they differ.
- **Vehicle Role**: What a generated vehicle is for—civil transport, military ground, grav utility,
  aircraft and the like—carrying the loadout profile that decides which categories it fills and
  from what. A cetools generation construct, not a Chapter 1 concept.
- **Generation Constraints**: Tech level, chassis size and locomotion limits supplied to generation,
  along with the seed.
- **Unmet Constraint**: A constraint generation could not honor, reported back to the referee.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All fifteen catalog designs build successfully, both as installed files and when
  selected by name from the command line, and every one of the fifteen names appears in the listing.
- **SC-002**: Across the fifteen, every published figure either matches cetools' output exactly or
  appears in the divergence documentation. Undocumented divergences: zero, enforced by the
  stat-block comparison test and the documentation check together rather than by review—the
  comparison test catches a divergence nobody noticed, the documentation check catches a divergence
  whose prose has gone stale.
- **SC-003**: The same seed and constraints produce byte-identical output on repeated runs, verified
  against a pinned baseline in the manner of the existing design baselines.
- **SC-004**: No design naming a component above its vehicle's tech level builds successfully.
- **SC-005**: No design requiring the over-20-ton rules builds successfully, and each is rejected
  with a message naming watercraft support as the missing capability.
- **SC-006**: Every Chapter 1 table row that no catalog vehicle and no generation path exercises is
  covered by a test that fails when that row's values are altered. Coverage of the package stays at
  or above the 85% floor, and the floor is treated as a floor rather than as evidence.
- **SC-007**: A referee can build a design and get a table-ready description in a single command,
  with no component table unless asked for.
- **SC-008**: A design file emitted by either command rebuilds to the identical description.
- **SC-009**: The five-command quality gate passes on the delivered change, including the
  documentation check with the divergence page inside its scope.
- **SC-010**: Every coarse locomotion alias resolves to at least one propulsion row, and every
  accepted alias and table name is named in the documentation.
- **SC-011**: Every generated vehicle carries only components its role's loadout profile permits,
  and every role is named in user-facing prose as a cetools generation choice rather than a
  Chapter 1 rule.

## Assumptions

- **Chapter 1 only.** The watercraft chapter is out of scope, because four of its five vehicles
  exceed 20 tons. The over-20-ton rules themselves are out of scope: they would require importing
  small-craft and ship hull and drive tables and applying conversion multipliers, and would inherit
  the known small-craft drive tonnage defect.
- **Construction, not play.** Chapter 1 material that resolves play rather than construction is out
  of scope: missile time to impact, missile to-hit, off-road movement, and atmosphere effects on
  aircraft. Material that only changes a printed number stays in.
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
  from the SRD be a selectable policy. These are not departures: cetools implements Chapter 1, and
  the book's worked examples disagree with Chapter 1. The constitution's documentation obligation
  still binds in full (FR-018), and is discharged in prose rather than by a policy switch.

## Dependencies

- The existing rolls seam and its roll-name registry, extended with vehicle roll names.
- The existing design-file baseline testing pattern.
- The existing documentation check, whose maintained-documents list grows from three files to four
  with the addition of `DIVERGENCES.md` (FR-020a). This is the one place the feature reaches outside
  the vehicles domain and the CLI, and it changes the quality gate, so it is worth a reviewer's
  attention.
