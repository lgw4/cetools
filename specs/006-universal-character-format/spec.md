# Feature Specification: Universal Character Format Output

**Feature Branch**: `006-universal-character-format`

**Created**: 2026-07-03

**Status**: Draft

**Input**: User description: "We need to make the character output conform to the Universal
Character Format (https://evolvedexperiment.github.io/cepheus-srd/character-creation.html#universal-character-format)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read a character in the standard format (Priority: P1)

A player generates a character and sees it printed in the same 5-line Universal Character
Format (UCF) used across the wider Cepheus/Traveller community, so it can be dropped directly
into notes, a virtual tabletop, or a character log without reformatting.

**Why this priority**: This is the core deliverable — conforming to UCF is the entire point of
the feature, and every other story only refines what appears within that format.

**Independent Test**: Generate a character for any implemented career and verify the printed
output contains only the UCF lines (name/rank/UPP/age; career/terms/funds; skills;
equipment-if-any) with no extra sections such as a characteristic breakdown or pension line.

**Acceptance Scenarios**:

1. **Given** a completed career character, **When** the character is generated, **Then** the
   output is exactly the UCF line set — name+UPP+age, career+terms+funds, skills, and an
   equipment line when applicable — with no additional sections.
2. **Given** a character with no material mustering-out benefits, **When** the character is
   displayed, **Then** the equipment line is omitted entirely rather than shown empty.

---

### User Story 2 - Every character has a name (Priority: P2)

A player generating a character wants it to have a name, so it reads as an individual rather
than an anonymous stat block, matching how UCF always leads with a character's name.

**Why this priority**: UCF's first line requires a name; without one, line 1 cannot conform to
the format at all. This is a prerequisite for User Story 1 to be fully satisfied, but is called
out separately because it is also the one new piece of data the system must produce (everything
else in UCF already exists somewhere in the current output).

**Independent Test**: Generate several characters and verify each one's output begins with a
two-or-more-word name, prefixed by the character's current rank title when they hold one,
followed by their UPP code and age.

**Acceptance Scenarios**:

1. **Given** any generated character, **When** the character is displayed, **Then** line 1 shows
   the character's rank title (if any) followed by a first and last name, then the UPP code and
   "Age <n>".
2. **Given** two separately generated characters, **When** both are displayed, **Then** each has
   an independently assigned name (duplicate names across characters are acceptable).

---

### User Story 3 - Funds and equipment at a glance (Priority: P3)

A player wants total liquid funds and notable equipment folded into the compact summary instead
of the current separate cash/material mustering-out benefit breakdown.

**Why this priority**: This consolidates existing data (mustering-out benefits) into the UCF
shape; it depends on Story 1's line structure already being in place, and is lower-impact than
having a name at all (Story 2).

**Independent Test**: Generate a character with multiple cash and material mustering-out
benefits and verify the funds line shows one combined "Cr<amount>" total and the equipment line
lists each material benefit by name.

**Acceptance Scenarios**:

1. **Given** a character with multiple cash mustering-out benefits, **When** displayed, **Then**
   line 2 shows a single funds figure equal to the sum of all cash benefits, formatted as
   "Cr<amount>" with thousands separators.
2. **Given** a character with no cash mustering-out benefits, **When** displayed, **Then** the
   funds figure reads "Cr0" rather than omitting the funds portion of the line.
3. **Given** a character with one or more material mustering-out benefits, **When** displayed,
   **Then** the equipment line lists each benefit's name, comma-separated.

---

### Edge Cases

- What happens when a character has no skills at all? The skills line is still present, just
  with an empty skill list.
- What happens when a character has no cash mustering-out benefits? The funds figure on line 2
  reads "Cr0" rather than being omitted.
- What happens when a character has no material mustering-out benefits? The equipment line is
  omitted entirely, not shown as a blank line.
- What happens when two generated characters are assigned the same random name? This is
  acceptable and not treated as an error.
- What happens when a single character's independently drawn first name and last name are
  identical strings (e.g. "Grant Grant")? This is acceptable and not treated as an error,
  consistent with the cross-character duplicate-name case above.
- What happens to a drafted character's output? It is generated normally; the output no longer
  indicates drafted status, since that annotation is not part of UCF and is dropped along with
  the rest of the previous output's extra detail (see FR-009).

## Clarifications

### Session 2026-07-03

- Q: Should generated first names be gender-differentiated (e.g., separate male/female name lists), or drawn from a single unisex list? → A: Single unisex list — no gender concept is introduced anywhere in the character model.
- Q: Should first and last names be drawn independently from two separate lists (cross-product), or come from a single list of pre-paired full names? → A: Two independent lists (first names, last names), each drawn independently and combined.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST assign a randomly generated name (first name + last name) to every
  generated character, drawn from a new tool-defined name data source, following the same
  data-driven convention already used for careers and skills. First names MUST be drawn from a
  single unisex list; no gender concept is introduced anywhere in the character model. The first
  name and last name MUST be drawn independently from two separate lists and combined, rather
  than selected as a pre-paired full name. Each list MUST contain at least 10 entries, to ensure
  meaningful variety (no upper bound is imposed). The two draws MUST be two independent random
  selections (e.g. two separate dice rolls) — never derived from a single shared random value or
  a shared list index. The two results MUST be combined as "<first> <last>" (single space, no
  middle name or initial).
- **FR-002**: The character summary MUST consist of exactly these lines, in order: (1) rank
  title (if the character holds one) followed by name, UPP code, and age; (2) career name, terms
  served, and total funds; (3) skills, alphabetical; (4) equipment, included only when the
  character has any.
- **FR-003**: Line 1 MUST prefix the character's name with their current rank title from their
  career's rank table when that title is non-empty. The rank-title segment, including its
  trailing space, MUST be omitted entirely (not shown as an empty prefix) when the character holds
  no rank title.
- **FR-004**: Line 2 MUST show terms served as "(<N> terms)", reusing the character's existing
  terms-served count.
- **FR-005**: Line 2's funds figure MUST equal the sum of all cash mustering-out benefit
  amounts, formatted with a "Cr" prefix and thousands separators (e.g. "Cr70,000"), and MUST
  read "Cr0" when the character has no cash benefits.
- **FR-006**: The skills line MUST list every skill the character has, sorted alphabetically by
  name, formatted as "<Name>-<Level>" and comma-separated.
- **FR-007**: The equipment line MUST list the name of every material mustering-out benefit the
  character received, comma-separated, and MUST be omitted entirely (not shown as an empty
  line) when the character has none.
- **FR-008**: The species-traits portion of the format MUST always be omitted, since the system
  generates only human characters.
- **FR-009**: The new format MUST fully replace the current output — the per-characteristic
  breakdown, the cash/material benefit split, the retirement-pension line, and the "(Drafted)"
  annotation MUST NOT appear in the default output.
- **FR-010**: Generating a character MUST NOT change any existing characteristic rolls, career
  qualification/survival/commission/advancement mechanics, or skill/benefit tables — only the
  character's name (new) and the display format change.

### Key Entities

- **Character**: The existing generated-character result. Gains one new attribute holding the
  character's generated name, in addition to its existing characteristics, career, rank, terms
  served, skills, benefits, and pension data.
- **Name Source**: Two new data sets — a list of first names and a list of last names — drawn
  independently and combined to assemble a character's name at generation time, mirroring the
  existing data-driven pattern already used for career and skill tables. First names are a single
  unisex list; no gender attribute exists on the character. Each list MUST contain at least 10
  entries; entries are ordinary proper-cased words, and duplicate entries within a single list
  are permitted (they only affect draw probability, never correctness).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of generated character outputs contain exactly the Universal Character Format
  line set — name/UPP/age, career/terms/funds, skills, and equipment when present — with no
  extraneous sections.
- **SC-002**: Every generated character's output begins with a two-or-more-word name followed by
  a valid UPP code and age.
- **SC-003**: A generated character's output can be copied directly into another
  UCF-compliant log or tool without manual reformatting, for every character the tool produces.
- **SC-004**: All previously-passing character-generation mechanics (characteristic rolls,
  career qualification, progression, and skill/benefit tables) remain unchanged, with zero
  regressions outside of display-format and name-related tests.

## Assumptions

- Only human characters are generated by this tool today, so the Universal Character Format's
  species-traits line is always omitted.
- "Character Funds" equals the sum of all cash mustering-out benefits; there is no separate
  starting-credits mechanic in this tool.
- "Significant equipment" equals the existing material mustering-out benefits (e.g., weapons,
  passage tickets, society memberships); no new equipment-tracking data is introduced.
- Every implemented career's rank table has a title at every rank, so a rank title is always
  available to show before the name. Verified by inspection: all four currently implemented
  careers (Navy, Marine, Aerospace, Scout) have a non-empty title on every rank entry. This is a
  documented data-authoring convention, not an invariant enforced by `Career.__post_init__` — any
  future career must uphold it manually; nothing currently rejects an empty rank title.
- Randomly generated names are drawn from new tool-defined first-name and last-name lists; no
  attempt is made to vary names by culture, homeworld, species, or gender — first names are a
  single unisex list. The cited SRD page defines only the Universal Character Format's output
  layout, not a name-generation or name-sourcing mechanism, so this assumption does not conflict
  with Constitution Principle I (SRD-Fidelity).
- The first-name and last-name lists are tool-authored placeholder data — generic
  English-language given/family names, with no real individuals, trademarked characters, or
  licensing constraints; no thematic or cultural curation is required beyond the unisex
  constraint already stated.
- Duplicate names across different generated characters are acceptable and not treated as an
  error; the same acceptance applies when a single character's independently drawn first and last
  name happen to be identical strings (e.g. "Grant Grant").
- The existing career-selection behavior (e.g. the `--career` flag) is unchanged; only the
  generated character's data (the new name field) and its display format change.
- Drafted status, individual characteristic scores, the cash/material benefit-type breakdown,
  and the retirement pension line are no longer part of the default character output, superseded
  by the Universal Character Format.
