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
   sentence begins "Using a <n>-ton hull (<h> Hull, <s> Structure), the <name> is ..."
   and its last sentence is "The ship costs MCr<n> (including discounts and fees) and
   takes <n> weeks to build."
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

- **FR-001**: The system MUST render a built ship as a heading line containing the
  ship's tech level and name, followed by a blank line, followed by exactly one prose
  paragraph, matching the SRD's Universal Ship Description Format.
- **FR-002**: The USDF rendering MUST replace the existing label-per-line ship sheet as
  the default output of both `cetools ship build` and `cetools ship generate`.
- **FR-003**: The rendering MUST be a pure function of the built ship: no generator
  seed, no timestamp, and no other ambient state may appear in the output. Two equal
  ships MUST render byte-identically.
- **FR-004**: Sentences MUST appear in the SRD's prescribed order: hull and purpose,
  drives and performance, fuel and endurance, computer, sensors, quarters, hardpoints
  and fire control, installed weapons, screens, hangars, cargo, hull configuration and
  armour, special features, crew, passenger capacity, cost and build time.

#### Sentence content

- **FR-005**: The hull sentence MUST state hull displacement in tons, Hull damage value,
  Structure damage value, the ship's name, and its purpose description.
- **FR-006**: The drives sentence MUST name the ship's jump drive code, maneuver drive
  code and power plant code, and state the resulting Jump rating and G-acceleration.
- **FR-007**: The fuel sentence MUST state fuel tankage in tons, the number of weeks the
  power plant is supported, and the number of jumps at the ship's jump rating that the
  jump fuel supports.
- **FR-008**: The computer sentence MUST state the computer's model number together with
  any purchased options, using the SRD's `Model N/bis` and `Model N/fib` notation.
- **FR-009**: The sensors sentence MUST name the installed electronics package using the
  SRD's display name and state its dice modifier with an explicit sign (for example
  "Basic Civilian sensors (DM-2)").
- **FR-010**: The quarters sentence MUST state the number of staterooms and the number of
  low berths, distinguishing emergency low berths from standard low berths.
- **FR-011**: The hardpoints sentence MUST state the ship's hardpoint count and the tons
  allocated to fire control.
- **FR-012**: When weapons are installed, the weapons sentence MUST describe the number
  and type of each turret and its weapons, grouping identical turrets, and MUST state any
  ammunition carried for missile and sandcaster weapons.
- **FR-013**: When screens are installed, the screens sentence MUST state the total screen
  count and describe the number and type of each screen.
- **FR-014**: When small craft hangars are installed, the hangars sentence MUST state the
  number of hangars and describe each hangar's capacity.
- **FR-015**: The cargo sentence MUST state cargo capacity in tons.
- **FR-016**: The hull-configuration sentence MUST state the hull configuration and, when
  armour is fitted, the armour type and total protection rating, plus any armour options
  installed.
- **FR-017**: When additional components are fitted, the special-features sentence MUST
  list them, and for fuel processors MUST state the daily tonnage of unrefined fuel they
  can process.
- **FR-018**: The crew sentence MUST state the total crew size followed by a breakdown of
  crew positions, omitting positions the ship does not require.
- **FR-019**: The passenger sentence MUST state the number of additional passengers
  carried at double occupancy in non-crew staterooms and the number of low passengers.
- **FR-020**: The closing sentence MUST state total cost in MCr, note that the figure
  includes discounts and fees, and state build time in weeks.

#### Omission and grammar

- **FR-021**: Sentences describing equipment the ship does not carry — weapons, screens,
  hangars, special features, armour — MUST be omitted entirely rather than rendered with
  zero or empty values, and the paragraph MUST remain grammatical after omission.
- **FR-022**: Whole numbers from one to ten MUST be spelled as words in prose; larger
  numbers MUST be rendered as digits, matching the SRD's own examples.
- **FR-023**: Singular and plural forms MUST agree with the quantity in every sentence
  (one stateroom / two staterooms, one week / four weeks, one jump / two jumps).
- **FR-024**: Lists of two or more items MUST be joined with commas and a final "and".
- **FR-025**: Tonnage and cost figures MUST render without scientific notation and
  without trailing zeros beyond the significant digits.

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
- **FR-028a**: Every component the SRD assigns a tech level — drives, computers,
  electronics packages and armour types — MUST carry that tech level in the rules data so
  the derived value covers the whole ship.
- **FR-028b**: An explicitly supplied tech level MUST be used as given, even when it is
  higher than the derived value. It is a statement about the yard that built the ship,
  not a constraint the system re-checks.
- **FR-029**: The system MUST be able to state a purpose description for every ship it
  can build, sourced from the design file where the designer supplies one.
- **FR-030**: Electronics packages MUST carry an SRD dice modifier and display name so
  the sensors sentence can be rendered from data rather than from hard-coded strings.
- **FR-031**: Adding a new SRD component row MUST NOT require editing the renderer:
  the wording for a component MUST come from its data row.

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
- **Electronics package**: Gains a display name and a sensor dice modifier alongside its
  existing tonnage and cost, so the sensors sentence is data-driven.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of ships the system can build render as a heading line plus exactly
  one paragraph, with no placeholder text, no empty parentheses and no orphaned
  punctuation.
- **SC-002**: A described ship can be pasted into a game document beside an SRD Chapter 9
  vessel and read as the same kind of writeup, with sentences in the same order and the
  same wording patterns.
- **SC-003**: Re-describing the same ship any number of times produces byte-identical
  output.
- **SC-004**: Every SRD Chapter 9 sentence pattern that applies to a given ship appears in
  that ship's description, and no sentence appears for equipment the ship lacks.
- **SC-005**: All previously-passing ship build, generation, TOML round-trip and cost
  calculations continue to pass unchanged.
- **SC-006**: A reader can determine a ship's jump rating, thrust, crew size, cargo
  capacity, cost and build time from the description alone, without consulting the design
  file.
- **SC-007**: Adding a new component row to the rules data produces correct description
  wording with no change to the rendering logic.

## Assumptions

- The USDF heading and paragraph fully replace the current sheet output, following the
  precedent set by feature 006 (Universal Character Format), which replaced the
  per-characteristic character output rather than adding a second format.
- The SRD's sentence templates are authoritative for wording; where the template and the
  Chapter 9 worked examples differ in phrasing, the worked examples are followed, since
  they show the format actually in use.
- Number-spelling style (words for one through ten, digits above) is inferred from the
  Chapter 9 examples, which write "a crew of three" but "a crew of 18".
- A design with no author-supplied purpose gets a neutral generic phrase rather than a
  fabricated one, since the system cannot infer a vessel's intended role.
- Bays, which the current builder supports but the SRD's USDF template does not name
  explicitly, are described in the installed-weapons sentence alongside turrets.
- The TOML design schema gains two optional fields — purpose description and tech level.
  Both absent keeps every existing design file valid and every existing design buildable.
- Component tech levels the SRD states but the current rules data omits (electronics,
  armour, drives) are transcribed from the SRD tables; no tech level is invented.
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

## Dependencies

- The existing ship builder, which supplies every computed value the description states.
- The existing rules data tables, which must gain sensor dice modifiers and display names.
- The Cepheus Engine SRD's Universal Ship Description Format section and Chapter 9:
  Common Vessels worked examples.

## Out of Scope

- Changing any ship-design rule, cost, tonnage or crew calculation.
- Adding new ship components, hull types, weapons or fittings.
- Deck plans, illustrations or any non-textual presentation.
- Rendering formats other than USDF and the existing TOML dump (no JSON, HTML or PDF).
- Parsing USDF text back into a design.
