# Feature Specification: Universal Ship Description Format

**Feature Branch**: `011-universal-ship-format`

**Created**: 2026-07-24

**Status**: Draft

**Input**: User description: "We need to output ship designs in this format: https://evolvedexperiment.github.io/cepheus-srd/ship-design-and-construction.html#universal-ship-description-format"

## Overview

The Cepheus Engine SRD prescribes a Universal Ship Description Format (USDF) for
presenting a finished ship design: a single prose paragraph, preceded by a
`[Tech Level] [Name]` heading line, that walks a reader through hull, drives,
fuel, computer, sensors, quarters, weapons, screens, hangars, cargo, armour,
special features, crew, passenger capacity, cost and build time in a fixed
sentence order.

Today `cetools ship build` and `cetools ship generate` emit a bespoke
label-per-line sheet. That sheet is readable but is not the format any Cepheus
Engine reader, referee or third-party document expects, so a generated ship
cannot be pasted straight into a game document alongside SRD Chapter 9 vessels.
This feature replaces that sheet with USDF output.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read a generated ship in the format the rules use (Priority: P1)

A referee generates a random ship and reads back a paragraph that matches, sentence
for sentence, the shape of the vessel writeups in SRD Chapter 9: Common Vessels. They
can hand it to a player at the table without rewriting anything.

**Why this priority**: This is the whole point of the feature. Without it, output is
still in a house format that no other Cepheus Engine material uses. Delivering only
this story already gives a complete, useful product.

**Independent Test**: Run the ship generator with a fixed seed and confirm the output
is a tech-level-and-name heading followed by one paragraph whose sentences appear in
the SRD's prescribed order and use the SRD's prescribed wording.

**Acceptance Scenarios**:

1. **Given** a randomly generated 200-ton starship, **When** its description is
   produced, **Then** the output is a heading line of the form `TL<n> <name>` followed
   by a blank line and a single prose paragraph.
2. **Given** that same ship, **When** the paragraph is read, **Then** its first
   sentence begins `Using a <n>-ton hull (<h> Hull, <s> Structure), the <name> is ...`
   and its last sentence is `The ship costs MCr<n> (including discounts and fees) and
   takes <n> weeks to build.`
3. **Given** two ships built from the same design, **When** both are described,
   **Then** the two paragraphs are byte-identical.

---

### User Story 2 - Describe a hand-authored design file (Priority: P1)

A ship designer writes a TOML design file, builds it, and gets a USDF paragraph they
can paste into their own supplement, matching how the SRD presents its own vessels.

**Why this priority**: Hand-authored designs are the case where a publishable
writeup matters most, and it exercises the same rendering path as story 1. It is
P1 alongside story 1 because both are served by one renderer.

**Independent Test**: Build the checked-in example design files and confirm each
produces a well-formed USDF paragraph naming the design's own components.

**Acceptance Scenarios**:

1. **Given** a design file that names the ship "Free Trader", **When** it is built and
   described, **Then** the ship's name appears in the heading line and in the first
   sentence.
2. **Given** a design file with an author-supplied purpose description, **When** it is
   built and described, **Then** that description completes the first sentence.
3. **Given** a design file with no author-supplied purpose description, **When** it is
   built and described, **Then** the first sentence still reads as a grammatical
   English sentence.

---

### User Story 3 - Omit sentences for equipment the ship does not carry (Priority: P2)

A reader of a small unarmed courier is not shown "This ship has zero screens" or
"There are no small craft hangars". The SRD's own examples simply leave those
sentences out.

**Why this priority**: The SRD examples demonstrate this behaviour, and without it
every unarmed civilian ship reads as a list of negations. It refines P1 output
rather than enabling a new use, so it is P2.

**Independent Test**: Describe a ship with no turrets, no screens and no hangars and
confirm the corresponding sentences are absent while the rest of the paragraph is
unchanged and still grammatical.

**Acceptance Scenarios**:

1. **Given** a ship with no screens, **When** it is described, **Then** the paragraph
   contains no screens sentence.
2. **Given** a ship with no turrets and no bays, **When** it is described, **Then** the
   paragraph contains no "Installed on the hardpoints are ..." sentence, though the
   hardpoint-count sentence remains.
3. **Given** a ship with no special features, **When** it is described, **Then** the
   paragraph contains no "Special features include ..." sentence.

---

### User Story 4 - Describe a small craft (Priority: P3)

A designer builds a 30-ton launch and gets a description that reads correctly for a
non-jump-capable vessel: no jump drive, no jump fuel, no jump performance, and a
cockpit rather than a bridge.

**Why this priority**: Small craft are already supported by the builder, so their
descriptions must not read as broken starships. It is P3 because the majority of
described vessels are starships.

**Independent Test**: Describe a generated small craft and confirm no jump-related
wording appears and the computer sentence refers to its cockpit.

**Acceptance Scenarios**:

1. **Given** a small craft, **When** it is described, **Then** the drives sentence names
   only maneuver drive and power plant, and states G-acceleration without a Jump rating.
2. **Given** a small craft, **When** it is described, **Then** the fuel sentence states
   power plant endurance only and makes no claim about jumps.

---

### Edge Cases

- **Zero cargo**: a ship whose every ton is committed still needs a grammatical cargo
  sentence ("Cargo capacity is zero tons").
- **Unarmed ship with hardpoints**: hull tonnage grants hardpoints even when nothing is
  mounted; the hardpoint sentence is kept and the installed-weapons sentence dropped.
- **Unnamed design**: a generated ship or a design file with no name still needs a
  heading line and a grammatical first sentence.
- **No armour fitted**: the armour clause must not claim "armored with nothing
  (0 points)".
- **Fractional cost**: costs such as 33.219 MCr must render at full precision without
  scientific notation or a trailing dangling decimal point.
- **Multiple armour layers**: a design carrying more than one armour type needs a
  single readable armour clause rather than a repeated one.
- **Repeated identical turrets**: three identical triple turrets should read as a
  single grouped phrase, not three separate clauses.
- **Crew of one**: the crew sentence must read "a crew of one: one pilot", not
  "a crew of 1: 1 pilots".
- **Zero non-crew staterooms**: the passenger sentence must not offer capacity the ship
  does not have.

## Requirements *(mandatory)*

### Functional Requirements

#### Output shape

- **FR-001**: The system MUST render a built ship as a heading line of the form
  `TL<tech level> <name>`, followed by a blank line, followed by exactly one prose
  paragraph, matching the SRD's Universal Ship Description Format.
- **FR-001a**: The paragraph MUST be a single unwrapped run of text: sentences are separated
  by one space and never by a line break, and no column width is imposed. The rendered value
  MUST NOT carry a trailing newline; supplying the one a terminal needs is the caller's job.
- **FR-002**: The USDF rendering MUST replace the existing label-per-line ship sheet as
  the default output of both `cetools ship build` and `cetools ship generate`.
- **FR-003**: The rendering MUST be a pure function of the built ship: no generator
  seed, no timestamp, no host locale, and no other ambient state may appear in the output,
  and no list may be ordered by iteration over an unordered collection. Two equal ships MUST
  render byte-identically.
- **FR-004**: Sentences MUST appear in the SRD's prescribed order: hull and purpose,
  drives and performance, fuel and endurance, computer, sensors, quarters, hardpoints
  and fire control, installed weapons, screens, hangars, cargo, hull configuration and
  armour, special features, crew, passenger capacity, cost and build time.

#### Sentence content

- **FR-005**: The hull sentence MUST state hull displacement in tons, Hull damage value,
  Structure damage value, the ship's name, and its purpose description.
- **FR-006**: The drives sentence MUST name the ship's jump drive code, maneuver drive
  code and power plant code, and state the resulting Jump rating and G-acceleration.
- **FR-006a**: Where a design fits no maneuver drive — which the rules permit for a
  jump-capable starship — the maneuver-drive clause and the G-acceleration clause MUST both be
  omitted, leaving a grammatical sentence.
- **FR-007**: The fuel sentence MUST state fuel tankage in tons, the number of weeks the
  power plant is supported, and the number of jumps at the ship's jump rating that the
  jump fuel supports.
- **FR-007a**: The number of jumps MUST be the whole number of jumps at the ship's rated Jump
  number that its jump tankage pays for. Where a design carries no jump fuel, the clause MUST
  still appear and state zero jumps, so the stated tankage is fully accounted for.
- **FR-008**: The computer sentence MUST state the computer's model number together with
  any purchased options, using the SRD's `Model N/bis` and `Model N/fib` notation: `/bis` for
  the jump-control specialization, `/fib` for hardened systems, and `/bis/fib` for a computer
  carrying both.
- **FR-009**: The sensors sentence MUST name the installed electronics package using the
  SRD's display name and state its dice modifier with an explicit sign (for example
  "Basic Civilian sensors (DM-2)"). The sign MUST be explicit at every magnitude, zero
  included ("DM+0").
- **FR-009a**: Where a design purchases no electronics package, the sensors sentence MUST name
  the standard package every ship carries as part of its bridge or cockpit, rather than being
  omitted.
- **FR-010**: The quarters sentence MUST state the number of staterooms and the number of
  low berths, distinguishing emergency low berths from standard low berths.
- **FR-010a**: Where a ship has no staterooms, no low berths and no emergency low berths, the
  quarters sentence MUST be omitted entirely.
- **FR-011**: The hardpoints sentence MUST state the ship's hardpoint count and the tons
  allocated to fire control. The tons allocated to fire control MUST equal the hardpoint count
  — the rules allocate one ton per hardpoint whether or not that hardpoint carries a weapon —
  and stating the figure MUST NOT change any tonnage the ship actually allocates.
- **FR-011a**: Where no weapon system is installed, the hardpoints sentence MUST say so, in
  place of a separate installed-weapons sentence.
- **FR-012**: When weapons are installed, the weapons sentence MUST describe the number
  and type of each turret and its weapons, grouping identical turrets, and MUST state any
  ammunition carried for missile and sandcaster weapons.
- **FR-012a**: Two turrets are identical for grouping purposes when they share both a mount
  type and a weapon loadout. Weapon bays MUST be described before turrets within the sentence.
  Ammunition MUST be aggregated across every turret carrying the same kind and type, and each
  ammunition clause MUST name the weapon its rounds feed.
- **FR-013**: When screens are installed, the screens sentence MUST state the total screen
  count and describe the number and type of each screen, grouping identical screens as FR-012a
  groups identical turrets.
- **FR-014**: When small craft hangars are installed, the hangars sentence MUST state the
  number of hangars and each hangar's capacity in tons of small craft. It MUST NOT name the
  craft carried: a design records a hangar's tonnage, not its contents.
- **FR-015**: The cargo sentence MUST state cargo capacity in tons.
- **FR-016**: The hull-configuration sentence MUST state the hull configuration and, when
  armour is fitted, the armour type and total protection rating, plus any armour options
  installed.
- **FR-016a**: When more than one armour layer is fitted, the sentence MUST carry a single
  armour clause naming every layer's type joined per FR-024, followed by one total
  protection rating for the ship — not a repeated clause and not a per-layer rating.
- **FR-016b**: Armour options MUST be named in a clause following the protection rating, using
  each option's display name, and MUST be stated once for the ship even when more than one
  layer carries the same option.
- **FR-017**: When additional components are fitted, the special-features sentence MUST
  list them, and for fuel processors MUST state the daily tonnage of unrefined fuel they
  can process, at the SRD's rate of 20 tons of unrefined fuel per ton of processor per day.
- **FR-018**: The crew sentence MUST state the total crew size followed by a breakdown of
  crew positions, omitting positions the ship does not require. The positions are the seven the
  builder derives — pilot, navigator, engineers, gunners, screen operators, medic and stewards
  — and MUST print in that order.
- **FR-019**: The passenger sentence MUST state the number of additional passengers
  carried at double occupancy in non-crew staterooms and the number of low passengers. Non-crew
  staterooms are those left once the crew is accommodated, and never fewer than none.
- **FR-019a**: Emergency low berths MUST NOT be offered as passenger capacity: the rules make
  them survival equipment that carries no passengers. They remain stated in the quarters
  sentence.
- **FR-019b**: Where a ship offers neither additional staterooms nor low passages, the sentence
  MUST state that it cannot carry additional passengers, rather than being omitted.
- **FR-020**: The closing sentence MUST state total cost in MCr, note that the figure
  includes discounts and fees, and state build time in weeks.

#### Omission and grammar

- **FR-021**: Sentences — and clauses within sentences — describing equipment the ship does not
  carry, such as weapons, screens, hangars, special features, quarters and armour, MUST be
  omitted entirely rather than rendered with zero or empty values, and the paragraph MUST remain
  grammatical after omission.
- **FR-021a**: "Grammatical after omission" means, at minimum: no doubled space, no sentence
  fragment, no dangling comma or conjunction, no empty parentheses, and no clause stating a
  quantity of zero except where a requirement calls for one (FR-007a, FR-019b, and the
  zero-cargo edge case).
- **FR-022**: Counts of things in running prose — crew, staterooms, low berths, hardpoints,
  turrets, bays, screens, hangars, fittings, jumps, weeks of power, passengers — MUST be
  spelled as words from zero to ten and as digits above ten, matching the SRD's
  "a crew of three" / "a crew of 18".
- **FR-022a**: Measured and rated values MUST always be rendered as digits regardless of
  magnitude: the hull sentence's displacement, Hull and Structure points, dice modifiers, MCr
  costs, tech level, computer model number, armour protection rating, Jump rating and
  G-acceleration. This matches the SRD's "Using a 100-ton hull (2 Hull, 2 Structure)".
- **FR-022b**: Tonnage stated elsewhere in running prose — fire-control tons, cargo capacity,
  fuel tankage, fuel-processor tonnage and throughput, hangar capacity — MUST follow FR-022's
  count rule when the value is a whole number, and MUST render as digits whenever it is
  fractional. This matches the SRD's "two tons allocated to fire control" and "three tons of
  fuel processors" alongside "Cargo capacity is 84 tons" and "Fuel tankage of 1.3 tons".
- **FR-022c**: FR-022, FR-022a and FR-022b MUST between them classify every number the
  paragraph can print; their listed examples are illustrative, not exhaustive. A quantity that
  counts discrete things follows FR-022; a value the rules measure or rate follows FR-022a;
  tonnage follows FR-022b. No number may fall under two of them or under none.
- **FR-023**: Singular and plural forms MUST agree with the quantity in every sentence
  (one stateroom / two staterooms, one week / four weeks, one jump / two jumps). Agreement
  covers verbs as well as nouns: "There is one stateroom" against "There are two staterooms".
- **FR-023a**: Where a sentence introduces an item with an indefinite article, the article MUST
  agree with the sound the following word begins with: "an armory", "a meson screen",
  "an 800-ton hull".
- **FR-024**: Lists of two or more items MUST be joined with commas and a final "and", with no
  comma before that final "and". A list of one item MUST render as that item alone.
- **FR-024a**: Every list MUST be ordered from a stable source — the order in which the design
  records its components, or the order in which the rules data tabulates them — so that FR-003
  holds.
- **FR-025**: Tonnage and cost figures MUST render without scientific notation, without
  trailing zeros beyond the significant digits, and without a trailing decimal point. Costs
  MUST carry thousands separators; tonnage MUST NOT.
- **FR-025a**: Figures MUST be rendered at a bounded precision — no more than six decimal
  places — before trailing zeros are stripped, so that a cost accumulated from many components
  prints as `MCr29.772` and never exposes a binary floating-point artefact such as
  `29.771999999999998`. Six places is fine enough to represent the smallest figure the rules
  price exactly (a standard missile at MCr0.00125) and coarse enough to suppress any artefact.

#### Small craft

- **FR-026**: For a small craft, the drives sentence MUST omit jump drive and Jump
  rating, and the fuel sentence MUST omit jump endurance.
- **FR-027**: For a small craft, the computer sentence MUST refer to the vessel's
  cockpit rather than a bridge.

#### Supporting data

- **FR-028**: The system MUST derive a ship's tech level as the highest tech level among
  the components it carries, and MUST let a designer override that derived value with an
  explicit tech level on the design. Where a designer supplies no tech level, the derived
  value is used.
- **FR-028a**: Every component category the SRD assigns a tech level MUST carry that tech level
  in the rules data, and all of them MUST contribute to the derived value, so the derived tech
  level covers the whole ship. A category the SRD leaves untabulated contributes nothing, as
  does an individual row whose tech-level cell the SRD leaves blank; no tech level may be
  invented to fill a gap. Which categories the SRD does and does not tabulate is a finding to
  be established by reading every table, not assumed from the category's importance.
- **FR-028b**: An explicitly supplied tech level MUST be used as given, whether it is higher or
  lower than the derived value. It is a statement about the yard that built the ship, not a
  constraint the system re-checks, warns about, or clamps.
- **FR-028c**: A derived tech level MUST always exist. Every ship carries the standard
  electronics package included in its bridge or cockpit, and the derivation reads that package's
  tech level like any other, so no ship can lack one.
- **FR-029**: The system MUST be able to state a purpose description for every ship it
  can build, sourced from the design file where the designer supplies one. A supplied
  description carries no sentence-ending punctuation of its own; the renderer supplies it.
- **FR-029a**: Where a design supplies no purpose description, the clause MUST name the
  ship's hull class instead — "a starship" or "a small craft" — so the sentence stays
  grammatical while asserting nothing the builder has not already determined.
- **FR-029b**: Where a design supplies no name, the heading line and the first sentence MUST
  both use `Unnamed Ship`, the placeholder the existing ship output already uses, so an unnamed
  ship reads consistently in both places.
- **FR-030**: Every rules-data row the paragraph can name — electronics packages, turret
  mounts, turret weapons, ammunition, weapon bays, screens, fittings, armour types, armour
  options and hull configurations — MUST carry the SRD display name used in prose, so no
  component wording is hard-coded in the renderer. Where the paragraph can state a count of a
  component, its row MUST carry the plural spelling as well, because the SRD's plurals are not
  uniformly regular. Every such spelling MUST be the SRD's own, taken from a table or from the
  prose that names the component; no display name may be invented, on the same terms as
  FR-028a's rule for tech levels.
- **FR-030a**: Electronics packages MUST additionally carry an SRD sensor dice modifier, so
  the sensors sentence states its modifier from data.
- **FR-031**: Adding a new SRD component row MUST NOT require editing the renderer:
  the wording for a component MUST come from its data row. "Editing the renderer" includes
  adding a branch, adding a string literal that names a component, and comparing against a
  component's key — a component's kind MUST be recognised by a column on its row, never by the
  spelling of its key.

#### Existing behaviour

- **FR-032**: This feature MUST NOT change any computed ship value — tonnage, cost,
  crew, hull and structure points, hardpoints or build time. It changes presentation
  only.
- **FR-033**: Round-tripping a design through TOML MUST remain lossless, including any
  new design fields this feature introduces.

### Key Entities

- **Ship description**: The rendered USDF text for one built ship — a heading line and
  one paragraph. Derived entirely from a built ship; holds no state of its own.
- **Ship purpose**: A short human-authored phrase completing "the <name> is ...",
  describing what the vessel is for. Optional on a design.
- **Ship tech level**: The technology level shown in the heading line. Derived as the
  highest tech level among the ship's components, overridable by an optional value on the
  design.
- **Component display name**: The SRD's prose spelling of a component, carried on the
  component's own rules-data row. Every nameable component kind gains one, so the renderer
  never spells a component itself (for example the fitting keyed `vehicle_hangar` carries
  the SRD's "small craft hangar").
- **Electronics package**: Gains a display name and a sensor dice modifier alongside its
  existing tonnage and cost, so the sensors sentence is data-driven.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of ships the system can build render as a heading line plus exactly
  one paragraph, with no placeholder text, no empty parentheses and no orphaned
  punctuation.
- **SC-002**: A described ship can be pasted into a game document beside an SRD Chapter 9
  vessel and read as the same kind of writeup: its sentences appear in the FR-004 order, and
  each sentence it carries matches the SRD's wording for that sentence with only this ship's
  own values substituted.
- **SC-003**: Re-describing the same ship any number of times produces byte-identical
  output.
- **SC-004**: Every sentence in the FR-004 order that applies to a given ship appears in that
  ship's description, and no sentence appears for equipment the ship lacks.
- **SC-005**: Every ship build, generation, TOML round-trip and cost test that passes before
  this feature continues to pass afterwards, unmodified. Only the tests that assert rendered
  output are replaced.
- **SC-006**: A reader can determine a ship's jump rating, thrust, crew size, cargo
  capacity, cost and build time from the description alone, without consulting the design
  file — from the sentences required by FR-006, FR-018, FR-015 and FR-020 respectively.
- **SC-007**: Adding a new component row to the rules data — carrying the display name, the
  plural where the paragraph can count it, and the tech level where the SRD tabulates one —
  produces correct description wording and a correct derived tech level, with no change to the
  rendering logic.

## Assumptions

- The USDF heading and paragraph fully replace the current sheet output, following the
  precedent set by feature 006 (Universal Character Format), which replaced the
  per-characteristic character output rather than adding a second format.
- The SRD's sentence templates are authoritative for wording; where the template and the
  Chapter 9 worked examples differ in phrasing, the worked examples are followed, since
  they show the format actually in use. This applies to *phrasing* only. Where the examples
  contradict a stated **rule** — as Chapter 9's "four emergency low passengers" contradicts
  Chapter 8's "emergency low berths will not carry passengers" — the rule governs, and the
  contradiction is recorded rather than silently resolved.
- Number-spelling style is inferred from the Chapter 9 examples, which write "a crew of
  three" but "a crew of 18", and "a 100-ton hull (2 Hull, 2 Structure)". Counts of things
  follow the words-to-ten rule; measured and rated values stay in digits; tonnage in running
  prose follows the count rule, because the examples write "two tons allocated to fire
  control" and "three tons of fuel processors". The SRD is itself inconsistent above ten
  ("twelve staterooms" but "25 staterooms"), so no rule can be extracted there and FR-022
  fixes the boundary at ten, knowingly departing from some examples.
- A design with no author-supplied purpose is described by its hull class rather than by a
  fabricated role, since the system cannot infer a vessel's intended role.
- Bays, which the current builder supports but the SRD's USDF template does not name
  explicitly, are described in the installed-weapons sentence alongside turrets.
- The TOML design schema gains two optional fields — purpose description and tech level.
  Both absent keeps every existing design file valid and every existing design buildable.
- Component tech levels the SRD states but the current rules data omits are transcribed
  from the SRD tables. Computers and armour already carry one; the remaining categories
  gain one where the SRD tabulates it. No tech level is invented.
- Machine-readable and per-line detail remain available through the existing TOML dump;
  USDF is the human-readable presentation only.

## Clarifications

### Session 2026-07-24

- Q: Where does the ship's tech level come from? → A: Derived as the highest tech level
  among fitted components, with an optional designer-supplied override on the design
  (FR-028, FR-028a, FR-028b).
- Q: What happens to the existing label-per-line ship sheet? → A: USDF replaces it
  entirely as the human-readable output, following the feature 006 precedent. The TOML
  dump remains for detail the paragraph does not carry (FR-002).
- Q: Which rules tables gain display names for prose rendering? → A: Every nameable
  component kind, not electronics alone — mounts, weapons, ammunition, bays, screens,
  fittings, armour types and options, configurations and cockpits (FR-030, FR-030a).
- Q: Which numbers are spelled as words? → A: Counts of things in prose only (one to ten);
  measured and rated values — tonnage, Hull/Structure, DMs, costs, TL, ratings — are always
  digits, per the SRD examples (FR-022, FR-022a).
- Q: Which components contribute to the derived tech level? → A: Every category the SRD
  tabulates a TL for — hulls, drives, computers, electronics, armour, turret weapons, bays,
  screens and fittings — with no TL invented where the SRD states none (FR-028a).
- Q: What completes the first sentence when a design supplies no purpose? → A: The ship's
  hull class — "a starship" or "a small craft" — rather than a fixed constant phrase or an
  inferred role (FR-029a).
- Q: How is multi-layer armour described? → A: One clause naming every layer's type,
  followed by a single total protection rating for the ship (FR-016a).

### Session 2026-07-24 (post-plan checklist review)

Raised by the requirements-quality, SRD-fidelity, prose and extensibility checklists after
Phase 0/1 research read the SRD's own worked examples.

- Q: FR-022a said tonnage is *always* digits, but every Chapter 9 example writes "two tons
  allocated to fire control" and "three tons of fuel processors". Which wins? → A: The
  examples. FR-022a is narrowed to the hull sentence's displacement and the rated values, and
  new FR-022b puts tonnage in running prose under the count rule. The zero-cargo edge case's
  "Cargo capacity is zero tons" is now consistent rather than contradictory.
- Q: What figure is "the tons allocated to fire control", given the builder folds a turret's
  fire control into the turret's own ton? → A: The hardpoint count, which is what all 20
  examples print, including ships with unused hardpoints. Presentation only; no allocated
  tonnage changes (FR-011).
- Q: Do emergency low berths count as low passengers? Chapter 8 says they carry none;
  Chapter 9 prints "four emergency low passengers". → A: Chapter 8 governs — this is a rules
  conflict, not a phrasing one, so the worked-examples-win assumption does not apply
  (FR-019a).
- Q: What is the tech level when no fitted component carries one? → A: The question does not
  arise: every ship carries the standard electronics package included in its bridge or
  cockpit, so a derived value always exists (FR-028c).
- Q: Where a design purchases no electronics, is the sensors sentence omitted? → A: No — the
  standard package is still fitted, and every Chapter 9 vessel without a purchased package
  still prints "Standard sensors" (FR-009a).

## Dependencies

- The existing ship builder, which supplies every computed value the description states.
- The existing rules data tables, which must gain sensor dice modifiers and display names.
- The Cepheus Engine SRD's Universal Ship Description Format section and Chapter 9:
  Common Vessels worked examples.

## Out of Scope

- Changing any ship-design rule, cost, tonnage or crew calculation.
- Adding new ship components, hull types, weapons or fittings.
- Ship features the SRD's own Chapter 9 examples state but the builder does not model, and
  which this feature therefore cannot describe: escape pods, mining and probe drones, barracks
  and troop complements, ship sections and their divided Hull/Structure, named small craft
  carried in hangars, and crew roles beyond the seven the builder derives (commanding officers,
  marines, scientists, flight crew). Their absence from a description is correct, not a gap.
- The SRD's referee-discretion parentheticals, such as "(If weapons are installed, this vessel
  will also require two gunners)".
- Deck plans, illustrations or any non-textual presentation.
- Rendering formats other than USDF and the existing TOML dump (no JSON, HTML or PDF).
- Parsing USDF text back into a design.
