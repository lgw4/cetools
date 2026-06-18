# Implementation Readiness Checklist: Aerospace System Defense Career

**Purpose**: Author pre-implementation self-audit — identify gaps, ambiguities, and missing test
coverage before writing any code (T002+)
**Created**: 2026-06-18
**Feature**: [spec.md](../spec.md) | [plan.md](../plan.md) | [tasks.md](../tasks.md)

---

## SRD-Fidelity & Career Data Requirements

- [x] CHK001 - Are all five career thresholds (qualification, survival, commission, advancement,
  re-enlistment) specified with both the stat and the minimum roll value, leaving no threshold
  ambiguous? [Completeness, Spec §FR-002]
  > **PASS**: FR-002 specifies all five: Endurance 5+ (qual), Dexterity 5+ (surv), Education 6+
  > (comm), Education 7+ (adv), 5+ (reenlist). data-model.md repeats each as an explicit named
  > field. No threshold is ambiguous.

- [x] CHK002 - Is the re-enlistment roll target (5+) explicitly distinguished from survival and
  other rolls, and is the absence of a Scout-style hard term cap clearly documented so the author
  is not tempted to add one? [Clarity, Spec §FR-002]
  > **PASS**: FR-002 lists reenlistment separately. The Edge Cases section explicitly answers: "No
  > — it uses the standard re-enlistment model (5+ per term, no special hard cap)." The engine's
  > `generate_career_character` applies `hard_max_terms=True` universally, so no Aerospace-specific
  > logic is needed and the spec correctly directs the author away from adding any.

- [x] CHK003 - Does FR-004 enumerate all six individual positions of each skill table (personal
  development, service, specialist, advanced education) — with no "etc." shorthand that could
  produce a wrong implementation? [Completeness, Spec §FR-004]
  > **PASS**: FR-004 provides a complete table with all four rows, 6 named entries each (24 total).
  > data-model.md independently enumerates all 24 as Python tuple literals with no placeholders or
  > shorthand.

- [x] CHK004 - Is the Advanced Education table eligibility threshold (Education 8+) explicitly
  stated in FR-004, and is it confirmed to match the threshold used by Navy and Scout? [Clarity,
  Consistency, Spec §FR-004]
  > **PASS**: FR-004 labels the table "Advanced Education (Edu 8+)". The engine (`generator.py:67`)
  > uses `if characteristics.get("Education", 0) >= 8` for all careers generically — the same
  > threshold applies to Navy, Scout, and Aerospace with no career-specific code required.

- [x] CHK005 - Is the skill name "Aircraft" (service skills position 6 and rank 0 bonus) confirmed
  to be a valid, existing token in the engine's skill dictionary — or is this left as an
  assumption? [Assumption, Spec §Assumptions]
  > **PASS (with clarification)**: The engine has no skill dictionary. `generator.py` stores skills
  > as arbitrary strings in `skills: dict[str, int]`; `_apply_skill_entry` accepts any non-stat-bump
  > string. "Aircraft" is valid by design. The spec assumption is correct, though the accurate
  > framing is: "the engine accepts any skill string, so no pre-existing token is required."

- [x] CHK006 - Is the bonus skill storage convention in `RankEntry.bonus_skills` (bare name
  without level suffix) specified unambiguously enough to prevent confusion with the SRD's
  "Aircraft-1" display notation — particularly for a developer reading FR-003 cold?
  [Clarity, Spec §FR-003]
  > **PASS**: FR-003 includes an explicit note: "The `RankEntry.bonus_skills` field stores bare
  > skill names — `('Aircraft',)` and `('Leadership',)` — and the engine awards level 1 at the
  > time of application." Confirmed by `_grant_rank_bonus` in `generator.py:95-97` and by
  > data-model.md. The notation distinction is clear and actionable.

- [x] CHK007 - Is the "+1 Soc" material benefit string at roll 7 specified to be the exact token
  the engine's stat-bump handler expects, rather than an assumed match with "+1 Edu"?
  [Clarity, Spec §FR-005]
  > **PASS**: FR-005 and data-model.md both specify `"+1 Soc"` exactly. The engine's
  > `_apply_material_benefit` (`generator.py:164-171`) has `"+1 Soc": "Social Standing"` in its
  > stat_map — a direct match. No mismatch risk.

- [x] CHK008 - Is the mustering-out DM mechanic (rank 5+ grants +1 DM, Gambling grants +1 DM)
  explicitly addressed — either specified as handled by the existing engine or intentionally
  out of scope for this feature? [Coverage, Gap, Spec §FR-005]
  > **RESOLVED**: The engine applies both DMs generically for all careers. Rank-5 material DM was
  > already tested via `test_material_benefit_row_7_reachable_at_rank_5_plus`. Gambling cash DM
  > gap closed by adding `test_gambling_skill_grants_cash_dm_on_muster_out` to
  > `tests/test_generator.py` — directly tests `_muster_out` with roll=5 and confirms the DM
  > shifts the cash amount from 20,000 to 50,000. 148 tests pass, coverage 92%.

---

## Registry & Draft Table Requirements

- [x] CHK009 - Is the registry key format specified as the lowercase-with-spaces string
  "aerospace system defense", distinguished from the canonical career name "Aerospace System
  Defense" — so the author does not mix them up in registry lookups? [Clarity, Spec §FR-006]
  > **PASS (via data-model.md)**: FR-006 alone does not name the key format; it only states
  > "MUST be registered so that `--career "Aerospace System Defense"` resolves." However,
  > data-model.md (§Registry Change) shows the dict literal explicitly:
  > `"aerospace system defense": AEROSPACE_CAREER` — lowercase, with spaces. The contrast
  > with the title-cased canonical name is unambiguous in that snippet. An author reading
  > both artifacts cannot confuse the two. No spec amendment needed; the data-model is the
  > appropriate location for this implementation detail.

- [x] CHK010 - Is FR-008 (draft table correction) explicit that index 0 (not index 1) maps to
  SRD roll result 1 — resolving the 0-indexed code vs. 1-indexed SRD table gap for the author?
  [Clarity, Spec §FR-008]
  > **PASS (via data-model.md + generator.py)**: FR-008 says "roll result 1 MUST reference
  > Aerospace System Defense" without naming an index. The 0-indexed convention is established
  > in two places: (1) data-model.md shows `DRAFT_TABLE[0] = "aerospace system defense"` with
  > the inline comment `# roll 1 — was "navy", corrected per FR-008`; (2) `generator.py:352`
  > uses `DRAFT_TABLE[roll - 1]`, making the roll-to-index mapping unambiguous to any author
  > reading the existing code. No spec amendment needed.

---

## CLI Contract Requirements

- [x] CHK011 - Is the normalization sequence in FR-007 fully specified (strip → lower → replace
  hyphens with spaces), and is it clear whether the raw input or the normalized value is
  displayed inside error messages in FR-009? [Clarity, Spec §FR-007, FR-009]
  > **PASS via contract doc**: `contracts/cli-career-flag.md` specifies the full algorithm:
  > `input.strip().lower().replace("-", " ")`. The contract's error examples confirm that
  > `<input>` in the error message is the raw user-typed value (e.g., a mistyped input or `'marine'`) —
  > not the normalized form. FR-009 updated to make both points explicit in spec.md.

- [x] CHK012 - Does FR-009 specify that the `<closest match>` displayed in "Did you mean: …?"
  is the canonical career name (title-cased, e.g., "Aerospace System Defense") rather than the
  lowercase registry key — and is there a step in the implementation to perform that lookup?
  [Clarity, Ambiguity, Spec §FR-009]
  > **PASS via contract doc + T019**: `contracts/cli-career-flag.md` states "`<canonical name>`
  > is the `career.name` field of the closest match." T019 confirms: "list all canonical names
  > from `CAREER_REGISTRY.values()` sorted by `career.name`." FR-009 updated to include
  > "`career.name` (canonical title-cased name) of the matching registry entry."

- [x] CHK013 - Does FR-009 specify the `n` parameter for `difflib.get_close_matches`? The spec
  states `cutoff=0.6` but not `n=1`; the default (`n=3`) would return multiple matches, which
  conflicts with the singular "Did you mean: …?" phrasing. [Clarity, Ambiguity, Spec §FR-009]
  > **RESOLVED**: Spec FR-009 updated to include `n=1` in the `difflib.get_close_matches` call
  > signature. This was already specified correctly in `contracts/cli-career-flag.md` and T019;
  > the gap was solely in spec.md.

- [x] CHK014 - Is the exact punctuation of both error message variants fully specified in FR-009
  — including apostrophes around `<input>`, trailing question mark on the "did you mean" branch,
  and the colon-space separator in "Valid careers: …"? [Clarity, Spec §FR-009]
  > **PASS**: Both spec FR-009 and `contracts/cli-career-flag.md` specify the same punctuation:
  > single quotes around `<input>`, period after `<input>`, question mark terminating the
  > "Did you mean" branch, and colon-space before the career list in the "Valid careers" branch
  > (no trailing punctuation on that branch). No change needed.

- [x] CHK015 - Is the ordering of career names in the "Valid careers: …" error message (FR-009,
  no-match branch) specified — alphabetical, insertion order, or other — so the assertion in
  T017 can be written unambiguously? [Clarity, Spec §FR-009]
  > **RESOLVED**: Spec FR-009 updated to state "sorted alphabetical order." Confirmed by
  > `contracts/cli-career-flag.md` ("listed in sorted order by canonical name") and T019
  > ("sorted by `career.name`"). T017 can now write its assertion against a deterministic list.

- [x] CHK016 - Is the ordering of canonical career names in the `--career` flag help text (FR-010)
  specified and consistent with the ordering used in the "Valid careers: …" error message?
  [Consistency, Spec §FR-009, FR-010]
  > **RESOLVED**: Spec FR-010 updated to require sorted alphabetical order and to explicitly
  > state consistency with FR-009's "Valid careers" ordering. The prior example
  > `{Navy,Scout,"Aerospace System Defense"}` (non-alphabetical) replaced with the canonical
  > example from `contracts/cli-career-flag.md`: `Aerospace System Defense, Navy, Scout`.

- [x] CHK017 - Is there a dedicated test task for FR-010 (help text enumerates career names)?
  T020 is implementation-only; no corresponding TDD test task appears in tasks.md. [Coverage,
  Gap, Tasks §T020]
  > **RESOLVED**: Added T017b to tasks.md: "Write failing test for `--career --help` output
  > showing all canonical career names in sorted alphabetical order in tests/test_cli.py."
  > T017b runs in parallel with T016/T017 and must be confirmed FAILING before T020 begins.
  > Scenario 9 ("Help text enumerates careers: T017b, T020") added to the coverage table.

---

## TDD Task Completeness

- [x] CHK018 - Do T002–T005 test tasks collectively and explicitly cover all five career thresholds
  (T002), all 24 individual skill positions across four tables (T003), all 7 rank entries with
  both bonus skill entries (T004), and both mustering-out tables with all 7 entries each (T005)?
  [Coverage, Tasks §T002–T005]
  > **RESOLVED**: T003 was under-specified — "6 entries each" did not require per-position
  > assertions. Updated to: "asserting the exact skill name at each of the 6 positions per table
  > (24 positions total — no count-only or 'etc.' assertions)." T002, T004, T005 were already
  > explicit; no changes needed there.

- [x] CHK019 - Does T006 define a specific set of valid Aerospace rank title strings for the
  assertion — rather than "any non-empty rank field" — so the test can catch a wrong title?
  [Clarity, Tasks §T006]
  > **RESOLVED**: T006 updated to require the rank title to be "one of the seven valid Aerospace
  > rank strings (Airman, Flight Officer, Flight Lieutenant, Squadron Leader, Wing Commander,
  > Group Captain, Air Commodore)." A wrong rank title from a different career would now fail
  > the assertion.

- [x] CHK020 - Do T011–T012 behavior tests address all three acceptance scenarios in US2:
  commission roll success (rank 0 → 1), commission roll failure (stays at rank 0), advancement
  increment, and rank 3 bonus skill (Leadership) applied? [Coverage, Spec §US2]
  > **RESOLVED**: T011 was missing the "extra skill roll for commissioning" from US2 scenario 1.
  > Updated T011 to assert three sub-cases explicitly: (a) commission success → rank 0→1 AND
  > one extra skill roll; (b) commission failure → stays at rank 0; (c) advancement success →
  > rank increments by 1. T012 already covers Leadership at rank 3 ✅.

- [x] CHK021 - Is T018 ("update test_career_unknown_stderr_message_exact") described as updating
  a currently passing test that will break — rather than a new failing test — so the TDD flow
  remains red-green without ambiguity about sequencing? [Clarity, Tasks §T018]
  > **RESOLVED**: T018 updated to state explicitly: "this test is currently PASSING (old format);
  > updating it makes it RED immediately; T019's implementation makes it GREEN (T018 MUST precede
  > T019 to keep the TDD red-green cycle unambiguous)." The sequencing constraint is now
  > unambiguous.

- [x] CHK022 - Does any test task cover the "rank cap" edge case (rank 6 character: advancement
  roll is ignored and rank does not exceed 6)? This edge case appears in spec.md §Edge Cases but
  maps to no specific task. [Coverage, Gap, Spec §Edge Cases]
  > **RESOLVED**: Added T011b to Phase 4: "Write failing test asserting that a character already
  > at rank 6 (Air Commodore) who succeeds on a mocked advancement roll remains at rank 6 — the
  > rank cap edge case from spec.md §Edge Cases — in tests/test_aerospace_career.py." T011b runs
  > in parallel with T011 and T012; the Phase 4 Checkpoint updated to include it.

- [x] CHK023 - Does any test task cover the "Education below commission threshold — stays at
  rank 0 for entire career" edge case from spec.md §Edge Cases? [Coverage, Gap, Spec §Edge Cases]
  > **RESOLVED**: The engine does not gate the commission roll on Education — it rolls and
  > compares to `commission_target`; a low-Education character can still roll (with characteristic
  > modifiers making success less likely) but is not mechanically barred. T011 assertion (b)
  > ("commission roll fails → stays at rank 0") directly covers this per-term behavior.
  > T011 updated to call this out explicitly: "covering the 'low-Education, never commissions'
  > edge case from spec.md §Edge Cases." No separate task needed; the per-term failure path is
  > the correct unit-level test for the spec's stated outcome.

---

## Scenario & Edge Case Coverage

- [x] CHK024 - Is the partial-name rejection edge case ("Aerospace" without "System Defense")
  covered by T016/T017 or a dedicated test, given that the spec explicitly calls it out as
  out-of-scope for partial matching? [Coverage, Spec §Edge Cases, Clarifications]
  > **RESOLVED**: `difflib.SequenceMatcher(None, "aerospace", "aerospace system defense").ratio()`
  > returns 0.5455 — below the 0.6 cutoff. `get_close_matches` returns an empty list, so "Aerospace"
  > falls into the **"no close match"** branch, not the "did you mean" branch. T017 covers this
  > path: its test input must be chosen to score below 0.6 against all registry keys (confirmed for
  > "Aerospace" at 0.5455 and the proposed "marine" input). No dedicated test task needed; the spec
  > edge-case note ("partial-match behavior is out of scope") is consistent with this outcome —
  > the user sees the "Valid careers:" list rather than a suggestion. T017's assertion can use
  > "Aerospace" as a concrete, score-verified example input.

- [x] CHK025 - For US3 (draft path): is it specified whether a drafted character still undergoes
  a qualification roll or bypasses it, and is this rule stated explicitly in the acceptance
  scenarios rather than implied by analogy to other careers? [Completeness, Spec §US3]
  > **PASS**: US3 Scenario 1 states explicitly: "the character is generated using the Aerospace
  > career data with the same rules as `--career "Aerospace System Defense"` **(bypass qualification
  > roll, use career data)**." The parenthetical is unambiguous — the qualification roll is
  > bypassed for drafted characters. This is stated inline in the acceptance scenario rather than
  > implied by analogy, satisfying the requirement for explicitness. No spec amendment needed.

---

## Non-Functional & Constitution Compliance

- [x] CHK026 - Is the assumption that the existing `Career` dataclass requires no structural
  changes validated against the current code (not assumed from memory), and is the validation
  documented in the plan's Constitution Check or Assumptions? [Assumption, Spec §Assumptions,
  Plan §Constitution Check]
  > **PASS**: base.py confirmed by inspection: `Career` is a 17-field frozen dataclass
  > (name, qualification_stat/target, survival_stat/target, commission_stat/target (Optional),
  > advancement_stat/target (Optional), reenlistment_target, service_skills,
  > personal_development, specialist_skills, advanced_education, ranks, cash_benefits,
  > material_benefits). Every Aerospace SRD data point maps directly to an existing field;
  > no new fields are required. The plan's project structure table ("base.py — unchanged")
  > and Constitution Check §V ("zero engine changes") collectively document this. The spec's
  > Assumptions section names the critical optional fields (commission_stat/target,
  > advancement_stat/target) — the fields that would be absent for a career like Scout that
  > has neither commission nor advancement — confirming the author identified the right
  > structural concern. No gap.

- [x] CHK027 - Are the three CLI changes in FR-007, FR-009, and FR-010 verifiably free of game
  logic (pure string/I/O operations only), satisfying Constitution §III — or does "difflib
  scoring against career names" constitute game-adjacent logic that belongs in the engine?
  [Consistency, Spec §FR-007–FR-010]
  > **PASS**: All three CLI changes are verifiably I/O-only. (1) FR-007 hyphen normalization:
  > `input.strip().lower().replace("-", " ")` — pure string transform. (2) FR-009 "did you
  > mean": `difflib.get_close_matches(normalized, CAREER_REGISTRY.keys(), n=1, cutoff=0.6)`
  > operates on career name strings only — no dice, no character stats, no SRD rules. It is
  > equivalent to a form autocomplete: string similarity on a fixed name list, not game
  > computation. (3) FR-010 help text: derives a sorted list of `career.name` strings from
  > the registry — string enumeration only. The plan's Constitution Check §III explicitly
  > documents "I/O-only: hyphen normalization, error message, help text — all pure string
  > manipulation with no game logic" and Complexity Tracking notes "difflib.get_close_matches
  > is a single stdlib call in the CLI error path." No game-logic leakage.

---

## Consistency & Traceability

- [x] CHK028 - Does the rank table in FR-003 align exactly with US2 acceptance scenarios —
  specifically rank 1 = "Flight Officer" and rank 3 = "Squadron Leader" with Leadership-1?
  [Consistency, Spec §FR-003, US2]
  > **PASS**: FR-003 rank table and US2 acceptance scenarios are in exact alignment. Rank 0 =
  > Airman (US2 Scenario 1 starting point) ✅. Rank 1 = Flight Officer (US2 Scenario 1
  > post-commission title) ✅. Rank 3 = Squadron Leader with Leadership-1 (US2 Scenario 3) ✅.
  > Rank 6 = Air Commodore (US2 Scenario 2 maximum rank cap) ✅. No discrepancy found between
  > the FR-003 table and the four US2 rank references.

- [x] CHK029 - Do the mustering-out values in FR-005 align exactly with the US1 acceptance
  scenario description (cash "1,000–50,000 Cr" and material items "Low Passage … +1 Soc")?
  [Consistency, Spec §FR-005, US1]
  > **PASS**: FR-005 and US1 Scenario 2 are in exact alignment. Cash column spans 1,000 to
  > 50,000 Cr across 7 rows — consistent with "1,000–50,000 Cr" ✅. Material column in
  > order: Low Passage / +1 Edu / Weapon / Mid Passage / Weapon / High Passage / +1 Soc —
  > matches US1 Scenario 2's parenthetical list character-for-character ✅. The 7-item length
  > (matching NAVY_CAREER, not SCOUT_CAREER's 6-item table) is consistent between FR-005 and
  > data-model.md. No discrepancy found.

- [x] CHK030 - Are SC-001–SC-002 (manual smoke tests) clearly distinguished from SC-003–SC-005
  (automated or objectively verifiable criteria), ensuring no manual test is mistaken for a
  quality gate during T021? [Clarity, Spec §Success Criteria]
  > **RESOLVED**: SC-001 and SC-002 are explicitly labeled "*(manual smoke test)*" with
  > "no automated task required" / "Verified by inspection" — unambiguously manual. SC-004
  > ("all existing tests continue to pass") and SC-005 ("coverage ≥ 85%") reference the test
  > suite directly — clearly automated via T021. SC-003 ("The career registry resolves
  > 'Aerospace System Defense'… with 100% accuracy") was unlabeled, creating a gap: an author
  > reading T021 might wonder if SC-003 requires a separate manual registry check. SC-003
  > amended in spec.md §Success Criteria to add "*(automated via T007, T009, T021)*" label
  > and explicit note mapping it to the test suite, consistent with SC-004/005's pattern.
