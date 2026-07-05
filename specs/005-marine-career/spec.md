# Feature Specification: Marine Career

**Feature Branch**: `005-marine-career`

**Created**: 2026-07-01

**Status**: Draft

**Input**: User description: "Using https://evolvedexperiment.github.io/cepheus-srd/index.html as the data source, we need to add the Marine career to this project."

## Clarifications

### Session 2026-07-01

- Q: Registering "marine" in the career registry will make four pre-existing tests fail, since they use the literal string "marine" as their example of an *unrecognized/unimplemented* career (tests/test_cli.py T023/T024 and tests/test_generator.py T016 — asserting exit-1/GenerationFailure behavior that would flip to success once Marine is registered). How should this be resolved? → A: Update the four tests to use "surface system defense" instead of "marine" as the unrecognized/unimplemented-career placeholder, since it remains an unregistered career after this feature (FR-008). This preserves each test's original intent (exercising the error path with a real, not-yet-implemented SRD career name) without contradicting SC-005.

- Q: Planning uncovered that the chosen placeholder "surface system defense" (and "maritime system defense") shares the "... system defense" suffix with the already-registered "Aerospace System Defense", so `difflib.get_close_matches` (cutoff 0.6) scores it at 0.766–0.826 similarity — well above the threshold. This flips the CLI into the "Did you mean: Aerospace System Defense?" near-miss path instead of the "no close match → Valid careers list" path that `test_career_unknown_stderr_message_exact` specifically asserts, permanently failing that test regardless of implementation correctness. How should this be resolved? → A: Use `"merchant"` instead of `"surface system defense"` as the placeholder in all four FR-012 tests. "Merchant" is a real, unimplemented Cepheus SRD career (consistent with the original intent of using a real not-yet-implemented career name) with low similarity (~0.3) to all four registered career keys, so it reliably exercises the "no close match" path. This supersedes the placeholder value chosen in the prior clarification entry; FR-012 and its associated edge case are updated accordingly.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate a Marine Character (Priority: P1)

A user invokes the character generator with `--career "Marine"` and receives a fully generated
character who served in the Marine corps, with all career-specific skills, ranks, benefits, and
mustering-out rolls applied according to the SRD.

**Why this priority**: Core deliverable — this is the primary use case for the feature and is
required for all other stories to have meaning.

**Independent Test**: Run `cetools character generate --career "Marine"` and verify the output
character sheet shows the career as "Marine", uses Marine rank titles (e.g., Trooper, Lieutenant),
and includes skills drawn from the Marine skill tables.

**Acceptance Scenarios**:

1. **Given** the character generator, **When** invoked with `cetools character generate --career "Marine"`,
   **Then** the character sheet displays the career as "Marine", uses Marine rank titles (Trooper
   through Brigadier), and includes skills drawn from the Marine skill tables.

2. **Given** a character who survived all terms as a Marine, **When** mustering out, **Then**
   benefits are drawn from the Marine cash table (1,000–50,000 Cr) and material table (Low
   Passage, +1 Edu, Weapon, Mid Passage, +1 Soc, High Passage, Explorers' Society).

3. **Given** a character who failed the survival roll as a Marine, **When** the generator
   handles the result, **Then** the character is processed according to the existing
   injury/death rules (same as Navy, Scout, and Aerospace System Defense).

---

### User Story 2 - Commission and Advancement in the Marines (Priority: P2)

A user generating a Marine character can be commissioned as an officer (rank 1+) and advance
through officer ranks each term, gaining rank-associated bonus skills and additional
mustering-out benefit rolls at senior ranks.

**Why this priority**: Commission and advancement distinguish the Marine career from careers
like Scout (which has neither). The advancement stat (Social Standing) also differs from every
currently implemented commissioned career, so this story validates that the engine's
career-agnostic commission/advancement logic handles a new stat correctly.

**Independent Test**: Run multiple character generations for Marine and observe that some
characters receive officer ranks, that the rank 0 bonus skill Zero-G-1 and rank 3 bonus skill
Tactics-1 are correctly applied, and that characters reaching rank 4+ receive extra
mustering-out benefit rolls.

**Acceptance Scenarios**:

1. **Given** a Marine character in their first term, **When** the commission roll (Education
   6+) succeeds, **Then** the character's rank advances from 0 (Trooper) to 1 (Lieutenant) and
   they receive one extra skill roll for commissioning.

2. **Given** a commissioned Marine officer, **When** the advancement roll (Social Standing 7+)
   succeeds, **Then** the character's rank increases by one (up to rank 6, Brigadier).

3. **Given** a character who reaches rank 3 (Major), **Then** the bonus skill Tactics-1 is
   added to their skills, and a character at rank 0 (Trooper) always has the bonus skill
   Zero-G-1 added to their skills, retained even after the character is later commissioned or
   advances to a higher rank (see FR-013).

4. **Given** a Marine character who reaches rank 4 (Lt Colonel) or higher, **When** mustering
   out, **Then** the character receives the existing rank-based bonus benefit rolls (one extra
   roll at rank 4, two at rank 5, three at rank 6) in addition to one roll per term served.

---

### User Story 3 - Marine Character Enters the Draft (Priority: P3)

A user who does not specify a career, or whose character fails qualification for another
career, may be drafted into the Marines via the existing draft table (draft roll of 2).

**Why this priority**: The draft table currently substitutes a "navy" placeholder for the
Marine slot because the career was not yet implemented. This story corrects that placeholder
and ensures the existing draft mechanism works correctly with the new career, matching how
Scout and Aerospace System Defense were previously wired into the draft table.

**Independent Test**: Run `cetools character generate` (no `--career` flag) repeatedly and
confirm that characters drafted into the Marines (roll of 2) are generated correctly using
Marine career data.

**Acceptance Scenarios**:

1. **Given** a draft roll of 2, **When** the draft assigns Marine, **Then** the character is
   generated using the Marine career data with the same rules as `--career "Marine"` (bypass
   qualification roll, use career data).

2. **Given** a drafted Marine character, **Then** the character sheet indicates they were
   drafted (same drafted flag mechanism as other draft-assigned careers).

---

### Edge Cases

- What happens when a character reaches rank 6 (Brigadier) and rolls for advancement? The
  advancement roll is ignored once the maximum rank is reached (same as Aerospace System
  Defense) (see FR-002, Acceptance Scenario 2.2).
- What happens when a character's Social Standing is below 7 and they cannot advance past
  rank 1? They remain at rank 1 (Lieutenant) for the rest of their career once commissioned
  (see FR-002, Acceptance Scenario 2.2).
- What happens when a character's Education is below 6 and they cannot commission? They
  remain at rank 0 (Trooper) for their entire career (see FR-002, Acceptance Scenario 2.1).
- What if the name-normalized variant "marines" (plural) or "MARINE" (any case) is passed to
  `--career`? The existing case-insensitive normalization resolves any casing of "marine" to
  the canonical career; "marines" does not exactly match and falls through to the existing
  "did you mean" suggestion logic (see FR-007, FR-010).
- What happens to the draft table slots for careers still unimplemented (Maritime System
  Defense at roll 3, Surface System Defense at roll 6)? They remain mapped to the "navy"
  placeholder until those careers are implemented in a future feature; this feature only
  corrects the roll-2 (Marine) slot (see FR-008, Assumptions).
- What happens to the pre-existing tests that used "marine" as their example of an
  unrecognized/unimplemented career, now that "marine" is a registered career? They are updated
  to use `"merchant"` instead, which remains unregistered after this feature (see FR-012),
  preserving the original intent of each test without contradicting SC-005.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST implement the Marine career as a new data structure instance
  conforming to the existing `Career` dataclass — zero changes to engine logic are permitted
  (Constitution §V).

- **FR-002**: The Marine career data MUST match the Cepheus Engine SRD exactly:
  - Qualification: Intelligence 6+
  - Survival: Endurance 6+
  - Commission: Education 6+
  - Advancement: Social Standing 7+
  - Re-enlistment: 6+

- **FR-003**: The Marine rank table MUST include all seven ranks with correct titles and bonus
  skills per SRD:

  | Rank | Title | Bonus Skill |
  |------|-------|-------------|
  | 0 | Trooper | Zero-G-1 |
  | 1 | Lieutenant | — |
  | 2 | Captain | — |
  | 3 | Major | Tactics-1 |
  | 4 | Lt Colonel | — |
  | 5 | Colonel | — |
  | 6 | Brigadier | — |

  "Zero-G-1" and "Tactics-1" use SRD table notation (skill name + level awarded). The
  `RankEntry.bonus_skills` field stores bare skill names — `("Zero-G",)` and `("Tactics",)` —
  and the engine awards level 1 at the time of application, consistent with how Navy's rank 0
  bonus skill ("Zero-G") is already stored. Ranks 1, 2, 4, 5, and 6 (marked "—" above)
  intentionally have no bonus skill — `RankEntry.bonus_skills` MUST be the empty tuple `()` for
  these ranks, not an omitted or inferred value.

- **FR-004**: The Marine skill tables MUST match the SRD exactly:

  | Table | Skills (positions 1–6) |
  |-------|------------------------|
  | Personal Development | +1 Str, +1 Dex, +1 End, +1 Int, +1 Edu, Melee Combat |
  | Service Skills | Comms, Demolitions, Gun Combat, Gunnery, Melee Combat, Battle Dress |
  | Specialist Skills | Electronics, Gun Combat, Melee Combat, Survival, Recon, Vehicle |
  | Advanced Education (Edu 8+) | Advocate, Computer, Gravitics, Medicine, Navigation, Tactics |

  The Advanced Education table MUST be available for skill rolls only when the character's
  Education is 8 or higher, using the engine's existing generic Education-gate mechanism
  (already exercised by Scout in `tests/test_generator.py`) — no Marine-specific gating logic is
  required.

- **FR-005**: The Marine mustering-out tables MUST match the SRD exactly:

  | Roll | Cash | Material |
  |------|------|-----------------|
  | 1 | 1,000 | Low Passage |
  | 2 | 5,000 | +1 Edu |
  | 3 | 10,000 | Weapon |
  | 4 | 10,000 | Mid Passage |
  | 5 | 20,000 | +1 Soc |
  | 6 | 50,000 | High Passage |
  | 7 | 50,000 | Explorers' Society |

  The result-7 material benefit MUST use the exact string `Explorers' Society` (plural
  possessive), matching the spelling already established for the same benefit on the Scout
  career's material table, for consistency across the codebase.

- **FR-006**: The Marine career MUST be registered in the career registry under the key
  `"marine"` so that `--career "Marine"` resolves to the correct career data structure, with
  canonical display name `"Marine"`.

- **FR-007**: The existing career name normalization (case-insensitive matching, hyphen-to-space
  conversion) MUST continue to work unchanged for the single-word name "Marine" — no new
  normalization logic is required.

- **FR-008**: The draft table entry for roll result 2 MUST be updated from the current "navy"
  placeholder to reference Marine, consistent with the SRD draft table. Draft table entries for
  rolls still mapped to unimplemented careers (3 and 6) MUST remain unchanged in this feature.

- **FR-009**: The `--career` flag's `--help` text MUST enumerate "Marine" alongside all other
  registered canonical career names in sorted alphabetical order, using the existing
  registry-derived listing mechanism (no hardcoded list).

- **FR-010**: When an unrecognized `--career` value is supplied (including near-matches such as
  "Marines"), the CLI MUST continue to use the existing "did you mean" / valid-careers-list
  error behavior, now with Marine included in the set of candidate career names.

- **FR-011**: The existing rank-based mustering-out bonus roll rule (one extra roll at rank 4,
  two extra rolls at rank 5, three extra rolls at rank 6, in addition to one roll per term
  served) MUST apply to Marine characters without any Marine-specific override, since this
  behavior is already implemented generically in the engine.

- **FR-012**: The pre-existing tests that used the string "marine" as a placeholder value for an
  unrecognized/unimplemented career (`tests/test_cli.py`: `test_career_unknown_exits_1`,
  `test_career_unknown_stderr_message_exact`, `test_career_unknown_original_value_in_message`;
  `tests/test_generator.py`: `test_draft_character_unimplemented_career_returns_failure`) MUST be
  updated to use `"merchant"` in place of `"marine"`, since it remains an unregistered career
  after this feature (FR-008). "Merchant" was chosen over the originally-proposed "surface system
  defense" because the latter (and "maritime system defense") scores 0.766–0.826 similarity
  against the already-registered "aerospace system defense" under
  `difflib.get_close_matches(cutoff=0.6)`, which flips the CLI into its "Did you mean:
  Aerospace System Defense?" near-miss path instead of the "no close match → Valid careers list"
  path that `test_career_unknown_stderr_message_exact` asserts exactly. "Merchant" scores ~0.3
  similarity against all four registered career keys, reliably exercising the "no close match"
  path. This preserves each test's original intent (exercising the CLI's "unknown career" error
  path and the generator's unimplemented-draft-career failure path with a real, not-yet-implemented
  SRD career name) without contradicting SC-005.

  `test_career_unknown_original_value_in_message` specifically verifies that the CLI echoes the
  *original, unnormalized* input casing (not the lowercased/normalized form) back in the error
  message. It MUST use the mixed-case variant `"Merchant"` (capital M), not the all-lowercase
  `"merchant"` used by the other two FR-012 tests — otherwise the input and its normalized form
  are identical strings and the assertion no longer distinguishes original-casing preservation
  from normalization.

- **FR-013**: The existing generic rank-bonus-skill mechanism (which grants each rank's bonus
  skill cumulatively at the moment that rank is reached — rank 0 at career entry, higher ranks
  upon commission or advancement — without ever removing a bonus skill already granted for a
  lower rank) MUST apply to Marine characters without any Marine-specific override. A Marine
  character commissioned to rank 1 (Lieutenant) or higher therefore retains the rank 0 Zero-G-1
  bonus skill gained at career entry, consistent with how Navy's rank 0 "Zero-G" and Scout's
  rank 0 "Piloting" bonus skills already behave under this same mechanism.

### Key Entities

- **MarineCareer**: A `Career` dataclass instance containing all Marine tables, qualification
  thresholds, commission and advancement targets, and rank entries. Identical in structure to
  `NAVY_CAREER`, `SCOUT_CAREER`, and `AEROSPACE_CAREER`.
- **Draft Table (roll 2 entry)**: The existing draft table's second entry, corrected from the
  "navy" placeholder to reference the Marine career.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running `cetools character generate --career "Marine"` 100 times produces zero
  unhandled exceptions, and every run that results in a successfully mustered-out or discharged
  character contains a rank title from the Marine rank table. A character who fails a survival
  roll and dies (Acceptance Scenario 1.3) is a handled outcome, not an "error," and is excluded
  from this count.

- **SC-002**: A Marine character's skills always come from the four Marine skill tables
  (Personal Development, Service Skills, Specialist, Advanced Education) — no skill from
  another career's table appears.

- **SC-003**: The career registry resolves "Marine" (and its case-insensitive variants) to the
  Marine career data structure with 100% accuracy, verified by automated tests.

- **SC-004**: A drafted character with a draft roll of 2 is always generated using Marine
  career data, verified by automated tests that fix the roll outcome.

- **SC-005**: All existing tests continue to pass after the Marine career is added — zero
  regressions in Navy, Scout, or Aerospace System Defense character generation.

- **SC-006**: Test coverage for `src/cetools/` does not fall below 85% after the new career
  module and any supporting changes are added.

## Assumptions

- The existing `Career` dataclass in `src/cetools/engine/careers/base.py` requires no
  structural changes to represent the Marine career — the existing fields (`commission_stat`,
  `advancement_stat`, `ranks` tuple) are sufficient, including using "Social Standing" as
  `advancement_stat`, which is already a valid stat name in the engine.

- The existing `--career` flag normalization, validation, and "did you mean" suggestion logic
  (added in feature 002, extended in feature 003) is extensible by registering a new career
  name with no changes to that logic itself.

- The existing rank-based mustering-out bonus roll mechanism (`_RANK_BONUS_ROLLS` in the
  generation engine: +1 roll at rank 4, +2 at rank 5, +3 at rank 6) already matches the SRD's
  Marine-specific description of this rule exactly, and is generic to all careers — no
  Marine-specific engine change is needed.

- The existing rank-bonus-skill mechanism (`_grant_rank_bonus` in the generation engine) already
  grants bonus skills cumulatively per rank achieved without clearing bonus skills from
  previously held ranks, and is generic to all careers — no Marine-specific engine change is
  needed for a commissioned Marine officer to retain the rank 0 Zero-G-1 bonus skill (FR-013).

- The material benefit "Explorers' Society" follows the exact spelling already established for
  the Scout career's equivalent benefit, per the SRD Important Terms definition (plural
  possessive), rather than the singular "Explorer's Society" phrasing used in earlier drafts.

- The draft table is expanded by exactly one entry (roll 2) in this feature. The remaining
  unimplemented career slots (Maritime System Defense at roll 3, Surface System Defense at
  roll 6) continue to use the "navy" placeholder until those careers are implemented in future
  features, consistent with the incremental-expansion pattern established in features 002 and
  003.
