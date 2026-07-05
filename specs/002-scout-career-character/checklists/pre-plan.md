# Pre-Plan Requirements Quality Checklist: Scout Career & Career Selection Flag

**Purpose**: Validate specification completeness, clarity, and consistency before planning begins; expose gaps while architecture is still malleable
**Created**: 2026-06-17
**Audience**: Feature author (self-check)
**Feature**: [spec.md](../spec.md)

---

## SRD Fidelity

- [x] CHK001 - Are the Scout qualification values (Intelligence 6+) sourced to a specific SRD section or page reference, not assumed from memory? [Traceability, Spec §FR-002] — Values confirmed correct against SRD. Assumptions section URL is sufficient; no inline citation required.
- [x] CHK002 - Are the Scout survival values (Endurance 7+) cited with a specific SRD reference? [Traceability, Spec §FR-002] — Values confirmed correct against SRD.
- [x] CHK003 - Are the Scout re-enlistment target (6+) and the 7-term cap both cited with SRD references? [Traceability, Spec §FR-002, US1-Scenario 6] — Both values confirmed correct against SRD.
- [x] CHK004 - Are all four Scout skill table entries (Personal Development, Service Skills, Specialist Skills, Advanced Education) verified against the SRD verbatim, or do they rely on transcription from memory? [Completeness, Spec §FR-003] — **Fixed 2026-06-17**: Personal Development corrected to (+1 Str, +1 Dex, +1 End, Jack o' Trades, +1 Edu, Melee Combat); spec had wrong entries. Service Skills, Specialist Skills, Advanced Education confirmed correct.
- [x] CHK005 - Is "Pilot" in FR-002's `basic_training_skills` and "Piloting" in FR-003's Service Skills tuple the same skill, or a naming inconsistency that requires resolution in the spec? [Clarity, Spec §FR-002/FR-003] — **Resolved 2026-06-17**: `basic_training_skills` concept removed (see CHK006). FR-002 now uses "Piloting-1" consistently; naming is consistent across the spec.
- [x] CHK006 - Is the "Pilot-1 from basic training" rule (level 0 granted in term 1 + rank-0 bonus raises to level 1) traced to specific SRD text, not derived from inference? [Traceability, Spec §FR-002] — **Fixed 2026-06-17**: `basic_training_skills` concept removed. SRD basic training rule (all service skills at level 0) applies to Scout unchanged. Piloting-1 is sourced to the Scout rank table (Rank 0 bonus). Clarification note in spec updated.
- [x] CHK007 - Is the "no commission, no advancement for Scout" rule cited with a specific SRD reference? [Traceability, Spec §FR-002] — Confirmed correct against SRD.
- [x] CHK008 - Is the draft table assignment (result 5 = Scout, all other results = Navy) sourced to the SRD, and is the full six-entry SRD draft table reproduced so the truncation rationale is clear? [Traceability, Spec §FR-010] — Result 5 = Scout confirmed. Full SRD draft table: 1=Aerospace System Defense, 2=Marine, 3=Maritime System Defense, 4=Navy, 5=Scout, 6=Surface System Defense. FR-010's non-Scout/Navy→Navy mapping is a documented phase shortcut; expansion path addressed in CHK034/CHK035.
- [x] CHK009 - Is the "no retirement pension for Scouts" rule cited with a specific SRD reference rather than inferred from the absence of a commission track? [Traceability, Spec §FR-013] — **Fixed 2026-06-17**: FR-013 was incorrect; SRD pension applies universally to all careers (5+ terms in any single service). FR-013 rewritten to require pension entitlement output with full calculation deferred. Incorrect Assumptions entry also corrected.
- [x] CHK010 - Is the Education 8+ threshold for the Advanced Education table availability cited with a specific SRD reference? [Traceability, Spec §Edge Cases] — Confirmed correct against SRD ("You may only roll on the Advanced Education table if your character has Education 8+").

---

## Career Data Schema

- [x] CHK011 - Is the type and default value of the new `basic_training_skills` field specified in the requirements (e.g., `tuple[str, ...]`, optional with a default)? [Completeness, Spec §FR-001] — **Superseded 2026-06-17**: `basic_training_skills` concept removed (CHK006 fix). Standard basic training rule applies; no new field needed here.
- [x] CHK012 - Are the semantics of `basic_training_skills` vs. the `service_skills` (or equivalent) field precisely defined: which field drives term-1 skill grants and which drives skill roll table selection? [Clarity, Spec §FR-001/FR-002] — **Superseded 2026-06-17**: `basic_training_skills` concept removed. Standard basic training (all service skills at level 0) drives term-1 grants; Rank 0 bonus drives Piloting-1.
- [x] CHK013 - Is it specified how the engine represents "no commission" for Scout (e.g., `None` target, boolean flag, absent field), so the data schema is unambiguous before planning? [Clarity, Spec §FR-006] — **Pass 2026-06-17**: Existing `commission_stat: str | None` / `commission_target: int | None` schema already handles this. FR-002 updated to explicitly state `commission_stat=None, commission_target=None`. Generator guards on `is not None` at `generator.py:239-243`.
- [x] CHK014 - Is it specified how the engine represents "no advancement" for Scout in the Career data structure? [Clarity, Spec §FR-006] — **Pass 2026-06-17**: Same pattern as CHK013. FR-002 explicitly states `advancement_stat=None, advancement_target=None`. Generator guards at `generator.py:250, 258-263`.
- [x] CHK015 - Are the Scout rank table entries (rank names/bonuses) fully specified in the requirements, or is only the rank-0 Pilot bonus mentioned? [Completeness, Spec §FR-002] — **Pass 2026-06-17**: FR-002 updated to specify `RankEntry(rank=0, title="Scout", bonus_skills=("Piloting",))` precisely. Only one rank entry exists per SRD. Rank bonus applied before term loop; basic training skips Piloting (already at 1) — net result Piloting-1 as SRD requires.
- [x] CHK016 - Is it clear whether the existing rank-bonus mechanism in the engine handles the Scout rank-0 Pilot bonus without modification, or whether a new mechanism is required? [Clarity, Spec §FR-002] — **Pass 2026-06-17**: `_grant_rank_bonus` is generic (`generator.py:94-96`). Scout `("Piloting",)` works identically to Navy `("Zero-G",)`. Zero engine changes required; confirms FR-001.
- [x] CHK017 - Are the exact entries of the Scout material benefits table (6 entries) and cash table (7 entries) specified with their result numbers (1–6 and 1–7)? [Completeness, Spec §FR-004/FR-005] — **Pass 2026-06-17**: FR-004 (6 entries, 1–6) and FR-005 (7 entries, 1–7) correct. No index risk: Scout max rank=0 so `material_dm=0`; Gambling not in Scout tables so `cash_dm=0` in practice. Note: FR-013 "deferred" clause also corrected — engine already computes pension via `_pension(terms_served)`; no deferral needed.

---

## Engine Algorithm

- [x] CHK018 - Is the rule for deriving the skill roll count from the career data structure fully specified: what field or condition triggers "always 2" vs. "up to 2 depending on commission/advancement"? [Completeness, Spec §FR-006] — **Resolved 2026-06-17**: Existing `if not commissioned_this_term and not promoted_this_term: skill_rolls = 2` is sufficient. Scout's `commission_stat=None` keeps both flags False every term, yielding 2 rolls with no new field and no algorithm change. FR-006 updated.
- [x] CHK019 - Is the boundary of "zero changes to the generation algorithm" precisely defined? The spec permits Career dataclass field additions — are any other categories of change explicitly permitted or forbidden? [Clarity, Spec §FR-001] — **Resolved 2026-06-17**: "Zero algorithm changes" means the per-career term logic in `generate_character` and its helpers is untouched for Scout. New engine functions or modules (e.g., a re-roll wrapper) are explicitly permitted. FR-001 updated.
- [x] CHK020 - Is the qualification re-roll loop termination condition unambiguous: raw INT >= 6, no maximum iteration count, and no 2D6 roll involved? [Clarity, Spec §FR-008] — **Resolved by prior session**: FR-008 and Clarifications §Session 2026-06-17 both state raw INT >= 6, direct comparison, no 2D6 roll, no iteration cap.
- [x] CHK021 - Is the scope of "re-roll all six characteristics" defined: does the re-roll reset any derived state (e.g., DMs already computed), or only the six raw characteristic values? [Clarity, Spec §FR-008] — **Resolved 2026-06-17**: Only the six raw characteristic values are re-rolled in the loop; background skills and rank bonuses are applied exactly once after the loop exits with a qualifying set. FR-008 updated.
- [x] CHK022 - Is the draft table data structure format (1D6 roll → career identifier) specified sufficiently for the planner to design it without ambiguity? [Completeness, Spec §FR-010] — **Resolved 2026-06-17**: `tuple[str, ...]` of 6 career identifiers indexed by `(roll - 1)`, consistent with existing skill table pattern. FR-010 and Key Entities updated with concrete example.
- [x] CHK023 - Is it specified where the qualification re-roll loop lives: in the engine library (per Constitution §II) or permitted in the CLI layer? [Clarity, Spec §FR-008, Constitution §II] — **Resolved 2026-06-17**: Engine library only. FR-008 updated to require the loop in `src/cetools/engine/`; CLI calls a single engine function.

---

## CLI & Output

- [x] CHK024 - Is the exact format of the `--career` argument fully specified: case-insensitive normalization described, and the canonical accepted values listed? [Clarity, Spec §FR-007] — **Resolved 2026-06-17**: FR-007 updated: input stripped of whitespace and lowercased before validation; canonical values are `navy` and `scout`.
- [x] CHK025 - Is the stderr error message format for an unrecognized `--career` value specified precisely (exact wording, whether valid career names are listed, message ordering)? [Clarity, Spec §FR-012] — **Resolved 2026-06-17**: FR-012 updated: exact format is `Unknown career '{name}'. Valid careers: navy, scout` (single line, original input quoted).
- [x] CHK026 - Is "Scout (Drafted)" an exact required output string, or an illustrative example? If it is an example, is the actual required format specified? [Clarity, Spec §FR-011] — **Resolved 2026-06-17**: FR-011 updated: required format is `{career} (Drafted) ({rank_title}, Rank {rank}) — {terms} terms, age {age}`. US2-S4 updated to match.
- [x] CHK027 - Are output requirements defined for all three career assignment paths: `--career scout`, `--career navy`, and no `--career` (draft)? [Completeness, Spec §FR-011] — **Resolved 2026-06-17**: FR-011 covers all three paths: `--career` → career name alone (unchanged formatter); draft → `{career} (Drafted)` prefix.
- [x] CHK028 - Are the re-roll loop output requirements specified: must the loop be silent (no output during re-rolling), or is some progress indication permitted? [Completeness, Spec §FR-008] — **Resolved by US1-Scenario 1**: "silently re-rolls" already in spec; no output during re-rolling.
- [x] CHK029 - Are exit code semantics fully enumerated: which specific failures produce code 1 (death, unrecognized career, others), and is code 0 defined as the only success state? [Completeness, Spec §FR-012, US1-Scenario 4] — **Resolved 2026-06-17**: FR-012 updated: code 0 = success, code 1 = all user-facing failures (character death, unrecognized career). No other codes used.
- [x] CHK030 - Is it specified whether `--career` with leading/trailing whitespace or mixed casing (e.g., "Scout", "  scout  ") is accepted, rejected, or normalized? [Clarity, Spec §FR-007] — **Resolved 2026-06-17**: FR-007 updated: whitespace stripped and lowercased; `" scout "`, `Scout`, `SCOUT` all accepted as `scout`.

---

## Deferred Items & Scope Boundaries

- [x] CHK031 - Is the deferral of Explorers' Society mechanics stated with an explicit rationale, not merely implied by "noted but not mechanically simulated"? [Completeness, Spec §Assumptions] — **Resolved 2026-06-18**: Assumptions now state explicit rationale: deferred because travel/booking mechanics are outside current character-generation scope.
- [x] CHK032 - Is the deferral of Courier Vessel mechanics stated with an explicit rationale? [Completeness, Spec §Assumptions] — **Resolved 2026-06-18**: Assumptions now state explicit rationale: deferred because asset ownership/maintenance mechanics are outside current character-generation scope.
- [x] CHK033 - Is "recorded as a named benefit" specified precisely enough for the planner: what string or data structure represents Explorers' Society and Courier Vessel in the output? [Clarity, Spec §Assumptions] — **Resolved 2026-06-18**: Spec defines existing material benefit representation with exact `material_name` values `Explorers' Society` and `Courier Vessel`.
- [x] CHK034 - Is there a documented expansion condition for the draft table (e.g., "expands when a new career is implemented")? Is it clear enough to avoid a breaking data-structure change when the first new career is added? [Clarity, Spec §FR-010] — **Resolved 2026-06-18**: FR-010 now requires expansion only when a career is fully implemented, registered in career data, and test-covered.
- [x] CHK035 - Is it specified what happens if a future phase's draft table expansion produces a roll for an unimplemented career during this phase's runtime? [Gap, Spec §FR-010] — **Resolved 2026-06-18**: FR-010/FR-012 now require fail-fast behavior (exit code 1 + clear stderr error) for unimplemented draft outcomes.

---

## Constitution Compliance

- [x] CHK036 - Does the spec demonstrate, not merely assert, that adding the Scout career satisfies Principle V (data-driven extensibility): is there a concrete statement that Scout requires zero engine logic changes, supported by naming the new data fields? [Constitution §V, Spec §FR-001] — **Resolved 2026-06-18**: FR-001 updated to enumerate all existing Career dataclass fields and confirm Scout requires zero new fields; `ranks: tuple[RankEntry, ...]` already exists in `base.py`. No schema change required; Principle V fully satisfied by data alone.
- [x] CHK037 - Is there an acceptance scenario that validates the engine independently of the CLI (e.g., SC-003 calls the engine directly)? Does it cover the Scout data structure producing a valid character without any CLI invocation? [Constitution §II, Spec §SC-003] — **Resolved 2026-06-18**: SC-003 updated to explicitly name `generate_character(scout_career, ...)` as the engine entry point and require the test to operate "without invoking the CLI".
- [x] CHK038 - Is the specification free of any requirement that would place game logic (re-roll loop, draft roll, skill assignment) in the CLI layer rather than the engine library? [Constitution §II] — **Resolved 2026-06-17**: FR-008 now explicitly requires the re-roll loop in `src/cetools/engine/`; FR-009 (draft) is also an engine concern. No spec requirement places game logic in the CLI.
- [x] CHK039 - Are test-first requirements explicit: does the spec require tests to be written before implementation for each new function (qualification re-roll, draft table, Scout skill tables)? [Constitution §IV, Spec §SC-004] — **Resolved 2026-06-18**: SC-004 extended to name the three new functions (re-roll loop, draft table lookup, Scout career instantiation) and mandate tests written and confirmed failing before any implementation is committed.

---

## Edge Case Coverage

- [x] CHK040 - Are requirements defined for a Scout who mustering outs after exactly one term (basic training + two skill rolls + one benefit roll only)? [Completeness, Spec §Edge Cases] — **Resolved 2026-06-18**: Normal first-term rules apply: basic training, two skill rolls, and one mustering-out benefit roll for the single term served.
- [x] CHK041 - Is the interaction between Education < 8 and the skill roll table selection process (only three tables available) specified as a requirement, not only as an edge case note? [Completeness, Spec §Edge Cases] — **Resolved 2026-06-18**: Advanced Education is unavailable below Education 8; only Personal Development, Service Skills, and Specialist Skills may be rolled.
- [x] CHK042 - Is the cash cap (3 rolls maximum) specified as applying per character overall or per career term? Is this consistent with the Navy implementation? [Clarity, Spec §US1-Scenario 5] — **Resolved 2026-06-18**: The cash cap is 3 cash rolls per character overall, not per term.
- [x] CHK043 - Are requirements defined for the natural-12 mandatory extra term: what happens if the character would exceed the 7-term cap on a natural-12 re-enlistment? [Completeness, Spec §US1-Scenario 6] — **Resolved 2026-06-18**: The 7-term cap is hard; if a natural-12 would push past 7 terms, mustering-out begins instead of granting an 8th term.
- [x] CHK044 - Is it specified what the character output looks like when characteristics are re-rolled many times before qualification: are intermediate rolls discarded entirely, or is the re-roll count reported? [Clarity, Spec §FR-008] — **Resolved by US1-Scenario 1**: "silently re-rolls" means intermediate rolls are discarded; no count or progress is reported in the output.
