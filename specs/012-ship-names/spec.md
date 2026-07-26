# Feature Specification: Ship Names

**Feature Branch**: `012-ship-names`

**Created**: 2026-07-25

**Status**: Draft

**Input**: User description: "I want to add ship names to the ship generator. In classic Traveller, names from mythology and folklore are commonly used for ship name (for example, the archetypical ship name is Free Trader Beowulf), so that could be a good source of names. Also, ship names from written science fiction media would be a good source, as would ship names from Star Trek and Star Wars."

## Clarifications

### Session 2026-07-25

- Q: Does FR-016's sourcing constraint apply to written science fiction as well as to film and television? → A: Yes—extend FR-016 to every fiction tradition; each such entry records its independent basis per FR-016a.
- Q: In what form is the FR-016a basis recorded? → A: Two parts—an enumerated basis kind (ordinary word / real vessel / public-domain work) plus a short free-text reference naming the specific word, vessel, or work.
- Q: Must a seed shared before this feature still produce the same ship once naming ships? → A: Yes—naming is purely additive; for any seed, every other generation choice is unchanged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A generated ship arrives already named (Priority: P1)

A referee needs a ship on the table right now. They ask cetools to generate one, and the ship
comes back with a name that reads like it belongs in a Traveller campaign—a name drawn from
myth, legend, or the science fiction canon—rather than the placeholder "Unnamed Ship". The
referee can announce the vessel to their players without inventing anything themselves.

**Why this priority**: This is the whole feature. Today every randomly generated ship renders as
"Unnamed Ship", which forces the referee to stop and improvise at exactly the moment the tool was
supposed to save them work. Naming the ship is what turns generator output into usable table
material, and it delivers value on its own with nothing else built.

**Independent Test**: Generate a ship with no extra options and confirm the rendered description
names it, that the name is one of the catalogued names, and that "Unnamed Ship" no longer appears.
Fully testable by itself.

**Acceptance Scenarios**:

1. **Given** no name is supplied, **When** a referee randomly generates a starship, **Then** the
   ship carries a name from the name catalogue and the description names it rather than calling it
   "Unnamed Ship".
2. **Given** no name is supplied, **When** a referee randomly generates a small craft, **Then** the
   craft is named on the same terms as a starship.
3. **Given** a randomly generated ship, **When** the referee exports it in the round-trippable
   design format, **Then** the generated name is recorded in the export.
4. **Given** an exported design carrying a generated name, **When** the referee builds a ship from
   that design, **Then** the ship renders under the same name it was generated with.

---

### User Story 2 - The same seed yields the same ship, name included (Priority: P2)

A referee shares a seed with a co-referee, or re-runs a seed weeks later to recover a ship they
liked. The ship that comes back is identical in every respect, including its name.

**Why this priority**: Reproducible-by-seed generation is an established promise of the ship
generator. A name that varied between runs of the same seed would quietly break that promise, so
this constrains *how* User Story 1 is built rather than adding capability on top of it. It is
second only because User Story 1 has table value even before determinism is verified.

**Independent Test**: Generate two ships from the same seed and confirm the names match; generate
from a different seed and confirm names vary across seeds; regenerate from a seed pinned before
this feature and confirm only the name is new.

**Acceptance Scenarios**:

1. **Given** a fixed seed, **When** a referee generates a ship twice, **Then** both ships carry the
   same name.
2. **Given** two different seeds, **When** a referee generates a ship from each, **Then** the names
   are drawn independently and are not forced to match.
3. **Given** a seed shared before this feature existed, **When** a referee generates from it now,
   **Then** the ship is the same in every other respect and differs only by carrying a name.
4. **Given** a design that already specifies a name, **When** a ship is built from it, **Then** the
   specified name is preserved and never replaced by a catalogue name.

---

### User Story 3 - Names span the source traditions, without repeating themselves (Priority: P3)

A referee generating a dozen ships for a subsector gets a varied roster—Norse and Greek myth
alongside folklore heroes and vessels from the science fiction canon—rather than the same handful
of names cycling round.

**Why this priority**: Variety is what makes the names feel authored rather than randomly stamped
on, but a small catalogue would still satisfy User Stories 1 and 2. This story is about the depth
and balance of the catalogue, which can be enriched after the naming mechanism works.

**Independent Test**: Inspect the catalogue for the required minimum size and for representation
from every named source tradition; generate a batch of ships and measure how often names repeat.

**Acceptance Scenarios**:

1. **Given** the assembled name catalogue, **When** it is inspected, **Then** every source tradition
   in scope contributes names, and no single tradition dominates the catalogue.
2. **Given** a batch of twenty ships generated from distinct seeds, **When** the names are compared,
   **Then** most names in the batch are distinct.
3. **Given** the catalogue, **When** it is inspected, **Then** it contains no duplicate entries.

---

### Edge Cases

- **A design already names the ship.** The supplied name wins. Naming applies only where no name
  was given, so a referee's own name is never overwritten.
- **A design supplies an empty or whitespace-only name.** Existing behaviour is unchanged: the ship
  renders as "Unnamed Ship". Building a design is a deterministic operation and must not invent a
  name.
- **A design file omits the name entirely.** Building it still yields "Unnamed Ship"; only random
  generation supplies names. This keeps builds reproducible from the file alone.
- **The catalogue is exhausted within a single run.** Names are drawn independently per ship, so two
  ships generated in the same session may share a name. The catalogue is sized so this is uncommon,
  not impossible.
- **Names with non-English origins.** Catalogue entries use plain unaccented spellings so a name
  renders identically in a description, in an exported design file, and on any terminal.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST supply a name for every randomly generated ship when the requester has
  not specified one.
- **FR-002**: The system MUST name randomly generated small craft on the same terms as randomly
  generated starships.
- **FR-003**: The system MUST draw names from a catalogue of curated ship names, and MUST NOT
  assemble names from syllables or other generated fragments.
- **FR-004**: The name catalogue MUST include names drawn from mythology and folklore.
- **FR-005**: The name catalogue MUST include vessel names drawn from written science fiction,
  subject to the sourcing constraint in FR-016.
- **FR-006**: The name catalogue MUST include vessel names drawn from science fiction film and
  television, subject to the sourcing constraint in FR-016.
- **FR-007**: Each catalogue entry MUST record which source tradition it came from, so the balance
  of the catalogue can be verified and future entries can be added in proportion.
- **FR-008**: The catalogue MUST contain at least 150 names, with every source tradition in scope
  contributing at least 20.
- **FR-009**: The catalogue MUST contain no duplicate names.
- **FR-010**: Name selection MUST be reproducible: generating with the same seed MUST produce the
  same name.
- **FR-010a**: Naming MUST be purely additive to seeded generation: a seed that produced a
  particular ship before this feature MUST still produce that same ship, now carrying a name. No
  other generation outcome—hull, drives, fittings, armament—may shift for any seed.
- **FR-011**: Name selection MUST be made through the same randomness mechanism as every other
  generation choice, so a name can be recorded, replayed, and audited alongside the rest of the
  ship's rolls.
- **FR-012**: A generated name MUST appear in the ship's rendered description wherever the
  description already refers to the ship by name.
- **FR-013**: A generated name MUST be carried into the round-trippable exported design, and
  building from that export MUST reproduce the same name.
- **FR-014**: The system MUST NOT overwrite a name supplied in a design; a supplied name always
  wins.
- **FR-015**: The system MUST NOT assign names when building a ship from a design file. Building
  stays deterministic and file-driven.
- **FR-016**: Catalogue names drawn from a fiction tradition—written science fiction as well as
  film and television—MUST be limited to vessel names that stand on their own outside their source
  work: ordinary English words, names of real historical naval vessels, or names the source work
  itself borrowed from public-domain literature. Distinctive coined names identified with a
  particular work or franchise MUST NOT be catalogued.
- **FR-016a**: Every written science fiction entry and every film and television entry MUST record
  the independent basis that qualifies it under FR-016 in two parts: a basis kind drawn from a
  fixed set—ordinary word, real vessel, or public-domain work—and a short reference naming the
  specific word, vessel, or work. Mythology and folklore entries do not carry a basis; the
  tradition is its own warrant.
- **FR-016b**: The basis record MUST be machine-checkable: it MUST be possible to verify
  automatically that every entry from a fiction tradition carries a basis kind from the fixed set
  and a non-empty reference, so the FR-016 constraint is audited by test rather than by inspection.
- **FR-017**: Catalogue names MUST be recorded as bare proper names, without a ship-type
  designation attached, since the ship's type and role are already described elsewhere in its
  description.
- **FR-018**: Catalogue names MUST use plain unaccented spellings so they render identically across
  descriptions, exported design files, and terminals.

### Key Entities

- **Ship name catalogue**: The curated body of names available to the generator. Each entry pairs a
  name with the source tradition it came from; entries from a fiction tradition also carry the
  independent basis that qualifies them under FR-016. The catalogue is content, not logic: names
  can be added or removed without changing how naming works.
- **Source tradition**: The provenance of a name—mythology and folklore, written science fiction,
  or science fiction film and television. Used to keep the catalogue balanced and to make its
  composition auditable.
- **Sourcing basis**: The evidence that a fiction-tradition name stands on its own outside its
  source work. A basis kind from a fixed set—ordinary word, real vessel, or public-domain
  work—paired with a short reference naming the specific word, vessel, or work. Present on every
  written science fiction and film and television entry; absent on mythology and folklore entries.
- **Ship design**: The existing declarative description of a ship, which already carries an optional
  name. Naming populates that name when the generator produces the design and the requester left it
  unset.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of randomly generated ships come back with a name; "Unnamed Ship" never appears
  in the output of random generation.
- **SC-002**: Generating from the same seed twice yields the identical name 100% of the time, and a
  generated ship exported and rebuilt renders under the same name 100% of the time.
- **SC-003**: Across 20 ships generated from distinct seeds, at least 17 carry distinct names.
- **SC-004**: A referee can produce a named, table-ready ship in a single command, with no manual
  naming step and no editing of files.
- **SC-005**: Every source tradition named in the scope contributes at least 20 catalogue entries,
  and no single tradition accounts for more than half the catalogue.
- **SC-006**: A design that names its own ship renders under that name in 100% of cases, unchanged
  from today's behaviour.
- **SC-007**: 100% of catalogue entries from a fiction tradition carry a basis kind from the fixed
  set and a non-empty reference, verified automatically rather than by inspection.
- **SC-008**: For every seed whose output was pinned before this feature, the ship generated after
  it is identical in 100% of respects except that it now carries a name.

## Assumptions

- **Bare names, not type-prefixed titles.** The user's example, "Free Trader Beowulf", combines a
  ship type with a proper name. The ship's type, configuration, and role are already stated in its
  rendered description, so the catalogue holds "Beowulf" and the description supplies the rest.
  Storing the prefix in the name would duplicate information and would be wrong whenever the
  generated hull is not a free trader.
- **One combined pool, no source filter.** Names are drawn from the whole catalogue. There is no
  option to restrict generation to a single tradition; nothing in the request calls for one, and it
  can be added later without disturbing the catalogue's shape.
- **No name-override option on the generator.** A referee who wants a specific name can export the
  design and set the name there, which already works. Adding a naming option to the generate command
  is out of scope.
- **Uniqueness is not enforced across ships.** Each ship draws independently. The catalogue is sized
  so repeats within a normal batch are uncommon, but two ships in one session may share a name.
- **Existing "Unnamed Ship" fallback is retained.** It remains the rendering for designs that carry
  no name, which is still reachable through hand-authored design files.
- **Naming reaches every path that produces a random ship**, including the small-craft path.

## Out of Scope

- Generating names for characters, worlds, or anything other than ships.
- Naming ships that are built from a design file rather than randomly generated.
- Selecting or weighting names by source tradition, ship type, hull size, or culture.
- Guaranteeing globally unique names across runs or maintaining a used-name registry.
- Adding a name option to the generate command.

## Resolved Decisions

### Sourcing posture for vessel names taken from fiction (FR-016)

**Resolved 2026-07-25**: Public-domain and generic-word names only, across every fiction tradition.

Vessel names in the science fiction canon are not a uniform body. Many are ordinary English words
or real naval names the works borrowed rather than coined—*Enterprise*, *Reliant*, *Excelsior*,
*Intrepid*, and *Defiant* have all been Royal Navy or US Navy ships, and written science fiction
borrows just as freely (*Nostromo* from Conrad, *Rocinante* from Cervantes). Others are distinctive
coined names closely identified with a single work or franchise—*Millennium Falcon*, *Tantive IV*,
*Executor*. Cataloguing the first group carries essentially no risk; cataloguing the second would
ship a redistributable list of trademark-adjacent names inside the package.

The constraint was first raised for Star Trek and Star Wars, but it applies with equal force to
written science fiction: the risk attaches to how distinctive and how closely identified a name is,
not to the medium it appeared in. A single rule across both traditions is also the auditable one,
since FR-016a's per-entry basis field already provides the evidence.

The catalogue therefore takes only names with an independent basis, and records that basis per
entry (FR-016a). This costs a handful of the most instantly recognisable names, but both fiction
traditions still read as science-fictional, because the canon borrowed most of its best names from
naval and literary tradition in the first place—which is the same well mythology and folklore draw
from.
