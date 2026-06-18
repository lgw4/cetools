# Feature Specification: Scout Career & Career Selection Flag

**Feature Branch**: `002-scout-career-character`

**Created**: 2026-06-17

**Status**: Draft

**Input**: User description: "We need to add the Scout career to the character generator. We also need to add an optional flag to specify the requested career when invoking the character generator. In these cases, the character generator should automatically generate a new set of characteristics until the character meets the admission requirements for the requested career. If a career is not specified, the character should enter the draft."

## Clarifications

### Session 2026-06-17

- Q: When the draft assigns Navy, does the enlistment roll still apply, or does the draft bypass it? → A: The draft bypasses the enlistment roll for all draft results. The draft directly assigns a career (same mechanism as `--career`); no qualification roll is made for draft-assigned characters.
- Q: Does the `--career` re-roll loop use a raw characteristic value check or a 2D6 qualification roll? → A: Raw characteristic value check - re-roll the full UPP until the `qualification_stat` score is >= `qualification_target` as a raw number; no extra dice roll is made.
- Q: Scout's Pilot-1 basic training conflicts with the current engine granting all `service_skills` at level 0 in term 1. How is this resolved? → A: There is no conflict. The SRD basic training rule applies to Scout unchanged: all service skills (Comms, Electronics, Gun Combat, Gunnery, Recon, Piloting) are granted at level 0 in the first term. The Pilot-1 outcome comes from the Scout rank table: Rank 0 carries a bonus skill of Piloting-1, which raises Piloting from 0 to 1. No `basic_training_skills` field is needed. FR-001's "zero changes to the generation algorithm" holds; the rank table mechanism already exists.
- Q: What is the canonical spelling of the "Explorer's Society" / "Explorer's Society" benefit? → A: "Explorer's Society" per the SRD Important Terms definition (singular possessive). Normalized across spec; existing `navy.py` spelling is already correct.
- Q: When the qualification re-roll loop iterates, what state is in scope for each re-roll attempt? → A: Only the six raw characteristic values are re-rolled in a tight loop until the qualification threshold is met; background skills and rank bonuses are applied exactly once after the loop exits with a qualifying set.
- Q: Where does the qualification re-roll loop live in the codebase? → A: Engine library (`src/cetools/engine/`); the loop is a game mechanic per the SRD and must not reside in the CLI layer (Constitution §II). The CLI calls a single engine function and prints the result.
- Q: How is the draft table data structure represented? → A: A `tuple[str, ...]` of 6 career identifiers indexed by `(roll - 1)`, consistent with all existing skill table tuples in the codebase. Example: `("navy", "navy", "navy", "navy", "scout", "navy")`.
- Q: How is Scout's two-skill-roll count derived from the career data structure? → A: The existing generator conditional (`if not commissioned_this_term and not promoted_this_term: skill_rolls = 2`) is sufficient. Scout's `commission_stat=None` causes both flags to remain False every term, yielding 2 rolls via the current code path with no new Career field or algorithm change required.
- Q: What is the precise boundary of "zero changes to the generation algorithm" (FR-001)? → A: "Zero algorithm changes" means the per-career term-processing logic in `generate_character` and its helpers requires no modification for Scout. Adding new engine functions or a new module (e.g., to house the re-roll loop for `--career`) is explicitly permitted and is not a violation of FR-001.
- Q: What does the career line in the output look like for a draft-assigned character? → A: `Scout (Drafted) (Scout, Rank 0) — 2 terms, age 26` — "(Drafted)" is appended to the career name, before the rank parenthetical. For `--career` paths, no origin marker appears (career name alone).
- Q: What exact text is printed to stderr for an unrecognized `--career` value? → A: `Unknown career 'X'. Valid careers: navy, scout` — single line, the invalid value quoted, valid names listed in canonical lowercase.
- Q: What is the complete exit code contract? → A: Code 0 = success (character generated); code 1 = all user-facing failures (character death, unrecognized career name). No other exit codes are used.
- Q: Is `--career Scout` (mixed case) accepted or rejected? → A: Normalized to lowercase before validation; `Scout`, `SCOUT`, and `scout` are all accepted and treated as `scout`. The error message uses the original input value.
- Q: Is `--career " scout"` (whitespace-padded) accepted or rejected? → A: Leading/trailing whitespace is stripped after lowercasing; `" scout"`, `"scout "`, and `"  SCOUT  "` are all treated as `scout`.

### Session 2026-06-18

- Q: Does the spec name the concrete Career dataclass fields Scout requires (CHK036)? → A: `ranks: tuple[RankEntry, ...]` already exists in `Career`; Scout requires zero new dataclass fields. FR-001 updated to enumerate all existing fields and confirm no schema change is needed.
- Q: Does SC-003 explicitly require direct engine invocation without CLI (CHK037)? → A: Yes. SC-003 updated to name the engine entry point (`generate_character(scout_career, ...)`) and state "without invoking the CLI".
- Q: Are test-first requirements explicit in the spec (CHK039)? → A: Extend SC-004 to name the three new functions requiring test-first coverage and mandate tests written and confirmed failing before implementation.
- Q: What should happen if a future draft table expansion yields an unimplemented career at runtime? → A: Treat it as an error: fail generation with exit code 1 and a clear stderr message rather than silently remapping or re-rolling.
- Q: How should Explorer's Society and Courier Vessel be represented in generated output data? → A: Use existing material-benefit representation with exact SRD names in `material_name`: `Explorer's Society` and `Courier Vessel`.
- Q: When should the draft table be expanded beyond Navy/Scout in future phases? → A: Expand only when a new career is fully implemented and registered in career data with tests; then update the 6-entry draft mapping.
- Q: What happens when `--career` is supplied with a whitespace-only value such as `--career "   "`? → A: After stripping and lowercasing, the value becomes an empty string `""`. An empty string is not a key in `CAREER_REGISTRY`, so FR-007's "unrecognized value after normalization" rule applies: FR-012 fires, the CLI exits with code 1, and stderr reads `Unknown career '   '. Valid careers: navy, scout` (original input before normalization is preserved in the message, per FR-012).
- Q: What is the precondition for `roll_until_qualified` regarding `qualification_stat`? → A: `roll_until_qualified` requires `career.qualification_stat` to be a non-None string — it is a caller precondition. Passing a `Career` with `qualification_stat=None` is a programming error; behavior is undefined and no defensive handling is required inside the function. All careers registered in `CAREER_REGISTRY` must satisfy this precondition; the current two careers (Navy, Scout) both have `qualification_stat="Intelligence"`.
- Q: What is the explicit rationale for deferring Explorer's Society and Courier Vessel mechanics in this phase? → A: Defer both because they depend on travel/asset subsystems outside current character-generation scope; record name-only benefits in this phase.
- Q: What happens if a natural-12 re-enlistment would push a character past the 7-term cap (CHK043)? → A: The 7-term cap is hard. If a natural-12 would grant an extra term past 7, mustering-out begins instead.
- Q: What happens when a Scout musters out after exactly one term (CHK040)? → A: Normal first-term rules apply: basic training, two skill rolls, and one mustering-out benefit roll for the single term served.
- Q: What happens when Education is below 8 and Scout skill rolls are resolved (CHK041)? → A: Advanced Education is unavailable; only Personal Development, Service Skills, and Specialist Skills may be rolled.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate a Scout Character (Priority: P1)

A game referee or player invokes the character generator with the Scout career flag and receives a fully-formed Cepheus Engine Scout character, including generated UPP, career history (terms served, skills gained via two rolls per term), and mustering-out benefits. Characteristics are re-rolled until the Intelligence 6+ qualification threshold is met.

**Why this priority**: The Scout career is the primary deliverable of this feature. Without a working Scout generator, no other scenario in this feature has value.

**Independent Test**: Invoke the generator with `--career scout` and verify a complete Scout character record is returned with a valid UPP, at least one Scout career term, skills consistent with Scout skill tables, and correct benefit results.

**Acceptance Scenarios**:

1. **Given** the generator is invoked with `--career scout`, **When** the initial characteristic rolls do not meet Intelligence 6+, **Then** the system silently re-rolls all six characteristics and repeats the qualification check until it passes, then proceeds with character generation.
2. **Given** a character qualifies for the Scout career, **When** the first term is processed, **Then** the character receives basic training (Pilot-1) and two skill rolls from any combination of the four Scout skill tables.
3. **Given** no commission or advancement system exists for Scouts, **When** each term is processed, **Then** the character receives exactly two skill rolls per term (not one), and no commission or advancement roll is attempted.
4. **Given** a Scout character who fails the survival roll (Endurance 7+), **When** generation is attempted, **Then** the CLI exits with code 1 and prints the cause of death to stderr; no character record is produced.
5. **Given** a Scout character completing at least one term, **When** the mustering-out phase runs, **Then** the character receives one benefit roll per term served, drawn from the Scout material benefits and cash tables, with the cash cap of 3 rolls enforced per character overall.
6. **Given** a Scout character completing a term, **When** re-enlistment is rolled (6+ target), **Then** the character continues or mustering-out begins; the 7-term cap and mandatory extra term on a natural 12 apply identically to Navy rules.

---

### User Story 2 - Default to Draft When No Career Specified (Priority: P2)

A player or referee invokes the character generator without specifying a career. Rather than defaulting to Navy enlistment, the character enters the draft, rolling on the draft table to determine their career assignment.

**Why this priority**: This changes the default behavior of the existing command and ensures the two-career system is coherent: the draft produces a deterministic Navy or Scout assignment and serves as the fallback for unspecified invocations.

**Independent Test**: Invoke `cetools character generate` (no `--career` flag) multiple times and verify that the resulting character enters a career determined by the draft table, with no enlistment attempt made.

**Acceptance Scenarios**:

1. **Given** the generator is invoked without `--career`, **When** generation begins, **Then** no enlistment roll is made; instead, a draft roll determines the character's career (Navy or Scout per the draft table for the careers supported at this phase).
2. **Given** a draft roll lands on Scout, **When** the character proceeds, **Then** the Scout career rules apply (no commission, two skill rolls per term, Scout skill tables, Scout mustering-out tables).
3. **Given** a draft roll lands on Navy, **When** the character proceeds, **Then** the enlistment roll is bypassed and existing Navy career progression rules apply unchanged (commission, advancement, survival, skill tables, mustering-out).
4. **Given** a draft outcome, **When** the character output is displayed, **Then** the career line begins with `{career} (Drafted)` (e.g., `Scout (Drafted) (Scout, Rank 0) — 2 terms, age 26`).

---

### User Story 3 - Specify a Career at Invocation (Priority: P3)

A player or referee can request a specific career at invocation using a `--career` flag. The generator re-rolls characteristics as many times as needed until the qualification threshold for the requested career is met, then proceeds with character generation.

**Why this priority**: Career selection by request is a quality-of-life feature that allows targeted character concepts without manual re-rolling. It builds on User Story 1's re-roll mechanism.

**Independent Test**: Invoke the generator with `--career navy` and verify the resulting character always qualifies for Navy enlistment, with correct Navy career progression applied.

**Acceptance Scenarios**:

1. **Given** `--career navy` is specified, **When** characteristics are generated, **Then** the system re-rolls until Intelligence 6+ is met and the character is enrolled in Navy without an enlistment roll.
2. **Given** `--career scout` is specified, **When** characteristics are generated, **Then** the system re-rolls until Intelligence 6+ is met and the character is enrolled in Scout without an enlistment roll.
3. **Given** an unrecognized career name is passed via `--career`, **When** invocation occurs, **Then** the CLI exits with code 1 and prints a list of valid career names to stderr.

---

### Edge Cases

- What happens when re-rolling for qualification produces the same failing results many times? (The system loops indefinitely until qualification is met; no maximum re-roll limit is imposed, consistent with the SRD intent of guaranteed enrollment when a career is chosen.)
- What happens when the draft table assigns a career that is not yet implemented? (This is treated as a runtime configuration error: generation fails with exit code 1 and a clear stderr message. For this phase, the table remains restricted to Navy and Scout.)
- What happens when a Scout character has Education below 8? (The Advanced Education skill table is not available; skill rolls are limited to the other three tables.)
- What happens when a Scout exhausts re-enlistment on the first term? (The character mustering out with only basic training and two skill rolls is a valid outcome.)
- What happens if a Scout has no valid skill table to roll on? (Cannot occur: Personal Development, Service Skills, and Specialist Skills are always available regardless of Education.)
- What happens when a natural-12 re-enlistment would exceed the 7-term cap? (The cap is hard; the character mustering-out begins instead of taking an 8th term.)
- What happens when cash mustering-out rolls are counted across multiple terms? (The cap is 3 cash rolls per character overall, not per term.)
- What happens when a Scout musters out after exactly one term? (Normal first-term rules apply: basic training, two skill rolls, and one mustering-out benefit roll for the single term served.)
- What happens when Education is below 8 and Scout skill rolls are resolved? (Advanced Education is unavailable; only Personal Development, Service Skills, and Specialist Skills may be rolled.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST implement the Scout career as a data structure. The generation algorithm MUST require zero changes to process it. "Zero algorithm changes" means the per-career term-processing logic in `generate_character` and its helpers is untouched for Scout. The Career dataclass requires **zero new fields** for Scout: every field it uses (`name`, `qualification_stat`, `qualification_target`, `survival_stat`, `survival_target`, `commission_stat`, `commission_target`, `advancement_stat`, `advancement_target`, `reenlistment_target`, `service_skills`, `personal_development`, `specialist_skills`, `advanced_education`, `ranks`, `cash_benefits`, `material_benefits`) already exists in `src/cetools/engine/careers/base.py`. Scout simply provides a `ranks` tuple with a single `RankEntry`; no schema change is required. New engine functions or modules added to support `--career` re-rolling (e.g., a wrapper entry point) are explicitly permitted and do not constitute algorithm changes. Adding optional parameters with backward-compatible defaults to `generate_character` (`preset_characteristics`, `bypass_qualification`, `hard_max_terms`, `drafted` — see plan.md §Complexity Tracking) also does not violate this constraint: when all four params take their default values, the existing code path is executed without modification, and the per-career term-processing logic is unreachable by those params.
- **FR-002**: The Scout career data MUST specify: qualification stat Intelligence, qualification target 6; survival stat Endurance, survival target 7; `commission_stat=None, commission_target=None`; `advancement_stat=None, advancement_target=None`; re-enlistment target 6; a ranks table with a single entry `RankEntry(rank=0, title="Scout", bonus_skills=("Piloting",))`. Basic training follows the standard SRD rule: all service skills at level 0 in the first term; no `basic_training_skills` override is required.
- **FR-003**: The Scout career data MUST include all four skill roll tables exactly as specified in the SRD: Personal Development (+1 Str, +1 Dex, +1 End, Jack o' Trades, +1 Edu, Melee Combat), Service Skills (Comms, Electronics, Gun Combat, Gunnery, Recon, Piloting), Specialist Skills (Engineering, Gunnery, Demolitions, Navigation, Medicine, Vehicle), and Advanced Education (Advocate, Computer, Linguistics, Medicine, Navigation, Tactics; available only if Education 8+). These tuples govern skill rolls only; they are NOT used as the basic training source (see FR-002).
- **FR-004**: The Scout career data MUST include the material benefits mustering-out table: 1. Low Passage, 2. +1 Edu, 3. Weapon, 4. Mid Passage, 5. Explorer's Society, 6. Courier Vessel. For results 5 and 6, benefits are represented using the existing material benefit structure (`kind="material"`) with exact `material_name` values `Explorer's Society` and `Courier Vessel`.
- **FR-005**: The Scout career data MUST include the cash benefits mustering-out table: 1. Cr1,000, 2. Cr5,000, 3. Cr10,000, 4. Cr10,000, 5. Cr20,000, 6. Cr50,000, 7. Cr50,000.
- **FR-006**: The generation engine MUST award exactly two skill rolls per Scout term, because Scouts have no commission or advancement track. The derivation uses the existing conditional: `skill_rolls = 1; if not commissioned_this_term and not promoted_this_term: skill_rolls = 2`. Since Scout has `commission_stat=None`, both flags remain False every term, yielding 2 rolls with no new Career field and no algorithm change.
- **FR-007**: The CLI MUST accept an optional `--career <name>` flag on the `cetools character generate` subcommand. Valid values for this phase are `navy` and `scout`. The input MUST be stripped of leading/trailing whitespace and normalized to lowercase before validation, so `Scout`, `" scout "`, and `SCOUT` are all accepted equivalents of `scout`. Unrecognized values (after normalization) trigger FR-012.
- **FR-008**: When `--career <name>` is supplied, the system MUST generate characteristics and re-roll them as a complete set until the raw value of the career's `qualification_stat` is >= `qualification_target` (e.g., for both Navy and Scout: Intelligence raw score >= 6). No 2D6 qualification roll is made; the check is a direct comparison of the characteristic value. Only the six raw characteristic values are re-rolled in the loop; background skills and rank bonuses are applied exactly once after the loop exits with a qualifying set. The re-roll loop MUST be implemented in the engine library (`src/cetools/engine/`), not the CLI; the CLI calls a single engine function. The system then proceeds to the first term without an enlistment roll. Two parameter contracts govern how this integrates with `generate_character`: (1) `bypass_qualification=True` skips the **entire** existing enlistment check — both the DM computation (`qual_dm = _dm(...)`) and the 2D6 roll (`roller.roll(6, count=2) + qual_dm < career.qualification_target`); no partial skip of just the comparison is intended. (2) When `preset_characteristics` is supplied, `generate_character` MUST trust the caller's values without re-validating them against the qualification threshold; `roll_until_qualified` is the sole authority for guaranteeing the threshold is met before calling `generate_character`.
- **FR-009**: When `--career` is not supplied, the system MUST determine the character's career by rolling on the draft table rather than attempting enlistment. The draft result assigns the career directly, bypassing the qualification roll entirely; a draft-assigned character cannot fail enlistment.
- **FR-010**: The draft table for this phase MUST cover only the two implemented careers and MUST be represented as a `tuple[str, ...]` of 6 career identifiers indexed by `(roll - 1)`. Scouts (draft result 5 per SRD) and Navy (all other results) are the valid outcomes: `("navy", "navy", "navy", "navy", "scout", "navy")`. The table expands only when a new career is fully implemented and registered in career data with automated tests; documentation-only additions do not qualify. If a draft result resolves to an unimplemented career identifier at runtime, generation MUST fail with exit code 1 and print the exact message `Draft assigned unimplemented career '{name}'` to stderr (where `{name}` is the unresolved career string from `DRAFT_TABLE`).
- **FR-011**: The character output MUST indicate how career assignment occurred. For draft-assigned characters, the career line MUST read `{career} (Drafted) ({rank_title}, Rank {rank}) — {terms} terms, age {age}` (e.g., `Scout (Drafted) (Scout, Rank 0) — 2 terms, age 26`). For `--career`-assigned characters, no origin marker appears; the career line format is unchanged from the current formatter output.
- **FR-012**: When an unrecognized career name is passed to `--career`, the CLI MUST exit with code 1 and print the following message to stderr: `Unknown career '{name}'. Valid careers: {career_list}` (where `{name}` is the raw value supplied by the user before any normalization, and `{career_list}` is the sorted keys of `CAREER_REGISTRY` joined by `, `; for this phase: `navy, scout`). The career list MUST be derived from `CAREER_REGISTRY` at runtime so it stays accurate as new careers are added. The complete exit code contract is: code 0 for all successes (character generated); code 1 for all user-facing failures (character death, unrecognized career name, invalid draft result that maps to an unimplemented career). No other exit codes are used.
- **FR-013**: Scout characters who complete 5 or more terms are entitled to a yearly retirement pension per the standard SRD pension table (5 terms: Cr10,000/year; 6 terms: Cr12,000/year; 7+ terms: Cr14,000/year + Cr2,000/year per term beyond 7). The SRD pension rule applies universally to all careers; it is not restricted to commissioned careers. The engine already computes pension for all careers via `_pension(terms_served)`; no changes to the pension logic are required for Scout.
- **FR-014**: All existing Navy career progression behavior MUST be preserved unchanged: commission, advancement, survival, re-enlistment, skill tables, and mustering-out tables. When the draft assigns Navy, the qualification roll is bypassed identically to `--career navy`; the character proceeds directly to term 1 with no enlistment check.
- **FR-015**: The 7-term cap MUST be enforced as a hard limit for Scout re-enlistment. If a natural-12 re-enlistment result would extend the character beyond 7 terms, the character MUST muster out instead of taking an 8th term. This is implemented via `hard_max_terms=True` passed to `generate_character` by `generate_career_character` and `draft_character`. As a consequence, the hard cap applies to all careers that flow through these entry points (including Navy via `--career navy` and Navy via the draft), deviating from the SRD's forced-re-enlistment rule for all those paths. This deviation is intentional and uniform: the character generator makes no distinction between career types for the term cap.

### Key Entities

- **Scout Career**: A career data structure extending the existing career interface. Has `commission_stat=None` and `advancement_stat=None`; uses standard basic training (all service skills at level 0); has a ranks table with a single entry `RankEntry(0, "Scout", ("Piloting",))` which raises Piloting from 0 to 1; awards two skill rolls per term via the existing "not commissioned and not promoted" branch; has unique mustering-out tables. Explorer's Society and Courier Vessel are emitted as material benefits with exact `material_name` strings.
- **Draft Table**: A `tuple[str, ...]` of 6 career identifiers indexed by `(roll - 1)`, mapping a 1D6 roll to a career assignment. For this phase, it covers Navy and Scout only. Future expansion occurs only when additional careers are fully implemented, registered, and test-covered.
- **Career Flag**: The `--career` CLI argument. Selects a specific career for guaranteed enrollment via characteristic re-rolling. Absence triggers the draft.
- **Qualification Re-roll Loop**: The process of re-rolling all six characteristics until the requested career's qualification threshold is met. Does not alter any other generation step.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can invoke `cetools character generate --career scout` and always receive a complete, valid Scout character record with Intelligence 6+ and correct Scout career output.
- **SC-002**: A user can invoke `cetools character generate` (no flag) and always receive a character whose career was assigned via the draft, with the draft origin indicated in the output.
- **SC-003**: The Scout career data structure can be defined and the generation engine processes it without any modification to engine logic, validated by a test that calls `generate_career_character(SCOUT_CAREER)` directly without invoking the CLI, and asserts a `Character` is returned (not a `GenerationFailure`). `generate_career_character` has return type `Character | GenerationFailure`; `GenerationFailure` is defined in `src/cetools/engine/models.py` and carries a `reason: str` and `exit_code: int = 1`.
- **SC-004**: All Scout-specific rules (two skill rolls per term, no commission/advancement, correct skill tables, correct mustering-out tables) are covered by automated tests, with 100% of Scout SRD rules verified. Per Constitution §IV (Test-First), tests for each new function MUST be written and confirmed failing (red) before any implementation is committed. The three functions requiring this treatment are: (1) the qualification re-roll loop entry point, (2) the draft table lookup function, and (3) the Scout career data structure instantiation and processing.
- **SC-005**: Passing an unrecognized career name to `--career` exits with code 1 and produces a human-readable error on stderr in all cases.

## Assumptions

- The SRD at `https://evolvedexperiment.github.io/cepheus-srd/character-creation.html` is authoritative; the Scout career details (qualification, survival, skill tables, mustering-out) match those sourced during specification.
- The SRD pension rule applies to all careers including Scout; the engine already computes it via `_pension(terms_served)` with no Scout-specific changes required (see FR-013 and research.md §11).
- The SRD mustering-out DM rules (+1 DM to the material table for rank 1+; +1 DM to the cash table for Gambling skill level 1+; bonus benefit rolls for rank 4+) apply generically to all careers via the existing engine with no Scout-specific override. For Scout, all three are structurally inapplicable: the maximum rank is 0, so the material DM and rank bonus rolls are never triggered; Gambling does not appear in any Scout skill table, so the cash DM cannot be earned through normal skill rolls. Scout therefore receives exactly one benefit roll per term served with no DM adjustments, consistent with US1-Scenario 5.
- The qualification check for `--career` re-rolls is identical for both Navy and Scout (Intelligence 6+); no DM for prior careers is applied, as this generator creates new characters with no prior career history.
- The draft table is restricted to Navy and Scout for this phase. Expanding the draft table to all twelve SRD careers is deferred until those careers are fully implemented, registered, and test-covered; if configuration drift produces an unimplemented draft career at runtime, generation fails with exit code 1 and a clear stderr error.
- The `--career` flag normalizes input to lowercase before validation; any casing is accepted.
- The Explorer's Society benefit (Scout material table, result 5) is recorded as material benefit data with `material_name="Explorer's Society"`; its in-game mechanical effect (free passage bookings, etc.) is not simulated in this phase because it requires travel/booking mechanics outside current generation scope.
- The Courier Vessel benefit (Scout material table, result 6) is recorded as material benefit data with `material_name="Courier Vessel"`; ownership and maintenance rules are not simulated in this phase because they require asset/economy subsystems outside current generation scope.
- Characteristic DM penalties from multiple prior careers (SRD rule: −2 per prior career to qualification) do not apply here, as the generator always creates a character with no prior career history.
- Output format remains plain text to standard output; no structured format changes are introduced in this phase.
