# Feature Specification: Aerospace System Defense Career

**Feature Branch**: `003-aerospace-system-defense`

**Created**: 2026-06-18

**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Aerospace System Defense Character (Priority: P1)

A user invokes the character generator with `--career "Aerospace System Defense"` and receives a
fully generated character who served in the planetary air force, with all career-specific skills,
ranks, benefits, and mustering-out rolls applied according to the SRD.

**Why this priority**: Core deliverable — this is the primary use case for the feature and is
required for all other stories to have meaning.

**Independent Test**: Run `cetools character --career "Aerospace System Defense"` and verify
the output character sheet shows the correct career, rank titles (e.g., Airman, Flight Officer),
and skills from the Aerospace System Defense tables.

**Acceptance Scenarios**:

1. **Given** the character generator, **When** invoked with `--career "Aerospace System Defense"`,
   **Then** the character sheet displays the career as "Aerospace System Defense", uses Aerospace
   rank titles (Airman through Air Commodore), and includes skills drawn from the Aerospace skill
   tables.

2. **Given** a character who survived all terms in Aerospace System Defense, **When** mustering
   out, **Then** benefits are drawn from the Aerospace cash table (1,000–50,000 Cr) and material
   table (Low Passage, +1 Edu, Weapon, Mid Passage, Weapon, High Passage, +1 Soc).

3. **Given** a character who failed the survival roll in Aerospace System Defense, **When**
   the generator handles the result, **Then** the character is processed according to the
   existing injury/death rules (same as Navy and Scout).

---

### User Story 2 - Commission and Advancement in Aerospace (Priority: P2)

A user generating an Aerospace System Defense character can be commissioned as an officer (rank 1+)
and advance through officer ranks each term, gaining rank-associated bonus skills.

**Why this priority**: Commission and advancement distinguish Aerospace from careers like Scout
(which have neither). Testing them independently validates that the engine handles the
Aerospace-specific commission/advancement thresholds correctly.

**Independent Test**: Run multiple character generations for Aerospace and observe that some
characters receive officer ranks and the Squadron Leader (rank 3) bonus skill Leadership-1 is
correctly applied.

**Acceptance Scenarios**:

1. **Given** an Aerospace character in their first term, **When** the commission roll (Education
   6+) succeeds, **Then** the character's rank advances from 0 (Airman) to 1 (Flight Officer) and
   they receive one extra skill roll for commissioning.

2. **Given** a commissioned Aerospace officer, **When** the advancement roll (Education 7+)
   succeeds, **Then** the character's rank increases by one (up to rank 6, Air Commodore).

3. **Given** a character who reaches rank 3 (Squadron Leader), **Then** the bonus skill
   Leadership-1 is added to their skills.

---

### User Story 3 - Aerospace Character Enters Draft (Priority: P3)

A user who does not specify a career, or whose character fails qualification for another career,
may be drafted into Aerospace System Defense via the existing draft table (draft roll of 1).

**Why this priority**: The draft table already lists Aerospace System Defense as draft result 1.
This story ensures the existing draft mechanism works correctly with the new career.

**Independent Test**: Run `cetools character` (no `--career` flag) repeatedly and confirm that
characters drafted into Aerospace System Defense are generated correctly.

**Acceptance Scenarios**:

1. **Given** a draft roll of 1, **When** the draft assigns Aerospace System Defense, **Then** the
   character is generated using the Aerospace career data with the same rules as `--career
   "Aerospace System Defense"` (bypass qualification roll, use career data).

2. **Given** a drafted Aerospace character, **Then** the character sheet indicates they were
   drafted (same drafted flag mechanism as other draft-assigned careers).

---

### Edge Cases

- What happens when a character reaches rank 6 (Air Commodore) and rolls for advancement?
  The advancement roll is ignored once the maximum rank is reached.
- What happens when a character's Education is below 6 and they cannot commission? They remain
  at rank 0 (Airman) for their entire career.
- Does the Aerospace career have a "Scout-style" hard term cap? No — it uses the standard
  re-enlistment model (5+ per term, no special hard cap).
- What if a character name-normalized variant "Aerospace" (without "System Defense") is passed
  to `--career`? The existing `--career` normalization logic must match "Aerospace System Defense"
  as the canonical name; partial-match behavior is out of scope.
- What if `--career "aerospace-system-defense"` (hyphenated) is passed? Hyphens are converted
  to spaces before the case-insensitive lookup, so this resolves to "Aerospace System Defense"
  correctly.

## Clarifications

### Session 2026-06-18

- Q: Beyond case-insensitive matching, should the CLI also accept hyphenated or underscored variants of the career name? → A: Accept hyphenated form ("aerospace-system-defense") by converting hyphens to spaces before lookup; no underscore variant.
- Q: When a user passes an unrecognized `--career` value, what should the error output be? → A: Output `"Unknown career '<input>'. Did you mean: <closest match>?"` with exit code 1; if no close match, list all valid career names.
- Q: Should `--help` enumerate valid career names? → A: Yes — list all canonical career names in the `--career` flag help text, derived from the career registry.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST implement the Aerospace System Defense career as a new data
  structure instance conforming to the existing `Career` dataclass — zero changes to engine
  logic are permitted (Constitution §V).

- **FR-002**: The Aerospace career data MUST match the Cepheus Engine SRD exactly:
  - Qualification: Endurance 5+
  - Survival: Dexterity 5+
  - Commission: Education 6+
  - Advancement: Education 7+
  - Re-enlistment: 5+

- **FR-003**: The Aerospace rank table MUST include all seven ranks with correct titles and
  bonus skills per SRD:

  | Rank | Title | Bonus Skill |
  |------|-------|-------------|
  | 0 | Airman | Aircraft-1 |
  | 1 | Flight Officer | — |
  | 2 | Flight Lieutenant | — |
  | 3 | Squadron Leader | Leadership-1 |
  | 4 | Wing Commander | — |
  | 5 | Group Captain | — |
  | 6 | Air Commodore | — |

- **FR-004**: The Aerospace skill tables MUST match the SRD exactly:

  | Table | Skills (positions 1–6) |
  |-------|----------------------|
  | Personal Development | +1 Str, +1 Dex, +1 End, Athletics, Melee Combat, Vehicle |
  | Service Skills | Electronics, Gun Combat, Gunnery, Melee Combat, Survival, Aircraft |
  | Specialist Skills | Comms, Gravitics, Gun Combat, Gunnery, Recon, Piloting |
  | Advanced Education (Edu 8+) | Advocate, Computer, Jack o' Trades, Medicine, Leadership, Tactics |

- **FR-005**: The Aerospace mustering-out tables MUST match the SRD exactly:

  | Roll | Cash | Material |
  |------|------|----------|
  | 1 | 1,000 | Low Passage |
  | 2 | 5,000 | +1 Edu |
  | 3 | 10,000 | Weapon |
  | 4 | 10,000 | Mid Passage |
  | 5 | 20,000 | Weapon |
  | 6 | 50,000 | High Passage |
  | 7 | 50,000 | +1 Soc |

- **FR-006**: The Aerospace career MUST be registered in the career registry so that
  `--career "Aerospace System Defense"` resolves to the correct career data structure.

- **FR-007**: The career name normalization MUST accept "Aerospace System Defense" and
  "aerospace system defense" (case-insensitive) as valid inputs. The normalization MUST
  also accept the hyphenated form "aerospace-system-defense" (converting hyphens to spaces
  before the case-insensitive lookup). The canonical name MUST be "Aerospace System Defense".

- **FR-008**: The draft table entry for roll result 1 MUST reference Aerospace System Defense,
  consistent with the SRD draft table.

- **FR-009**: When `--career` is given an unrecognized value (including partial matches such as
  "Aerospace"), the CLI MUST output an error message of the form:
  `"Unknown career '<input>'. Did you mean: <closest match>?"` where the closest match is
  determined by normalized string distance against the registered career names. Exit code MUST
  be 1. If no close match exists, the message omits the suggestion and lists all valid career
  names instead.

- **FR-010**: The `--career` flag's `--help` text MUST enumerate all valid canonical career names
  (e.g., `--career {Navy,Scout,"Aerospace System Defense"}`). When a new career is registered,
  the help text MUST be updated to include it. This is a CLI-layer change only — the list of
  valid names is derived from the career registry, not hardcoded.

### Key Entities

- **AerospaceCareer**: A `Career` dataclass instance containing all Aerospace System Defense
  tables, qualification thresholds, commission and advancement targets, and rank entries.
  Identical in structure to `NAVY_CAREER` and `SCOUT_CAREER`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running `cetools character --career "Aerospace System Defense"` 100 times produces
  zero errors and every output contains a rank title from the Aerospace rank table.

- **SC-002**: An Aerospace character's skills always come from the four Aerospace skill tables
  (Personal Development, Service Skills, Specialist, Advanced Education) — no skill from another
  career's table appears.

- **SC-003**: The career registry resolves "Aerospace System Defense" (and its case-insensitive
  variant) to the Aerospace career data structure with 100% accuracy.

- **SC-004**: All existing tests continue to pass after the Aerospace career is added — zero
  regressions in Navy or Scout character generation.

- **SC-005**: Test coverage for `src/cetools/` does not fall below 85% after the new career
  module and any supporting engine changes are added.

## Assumptions

- The existing `Career` dataclass in `src/cetools/engine/careers/base.py` requires no structural
  changes to represent Aerospace System Defense — the existing fields (commission_stat,
  advancement_stat, ranks tuple) are sufficient.

- The existing `--career` flag normalization and validation logic (added in feature 002) is
  extensible by registering new career names. Minor CLI changes are required: updating the
  `--help` text to enumerate registered career names (FR-010) and ensuring the "did you mean"
  suggestion (FR-009) draws from the registry. No game logic moves into CLI code.

- The draft table already references "Aerospace System Defense" by name in the existing
  implementation — only data correctness needs to be verified, not a new mechanism.

- "Aircraft" is a valid skill name in the SRD context for this engine; it appears in Service
  Skills (position 6) and as the rank 0 bonus skill. This is consistent with how other skills
  like "Piloting" and "Zero-G" are stored as plain strings.

- The material benefit "+1 Soc" at roll 7 follows the same pattern as "+1 Edu" and other
  stat-bump strings used in existing career material tables.
