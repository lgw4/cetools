# Implementation Readiness Checklist: Marine Career

**Purpose**: Comprehensive pre-implementation validation of requirement quality across SRD data
fidelity, registry/draft/CLI integration, and test-migration safety — for the author to run
against spec.md/plan.md before writing `marine.py` and updating tests (Constitution §IV,
test-first).
**Created**: 2026-07-01
**Feature**: [spec.md](../spec.md)

**Note**: This checklist tests whether the *requirements* are complete, clear, consistent, and
measurable — not whether the eventual implementation works. Items ask "is this specified?", not
"does this behave correctly?".

## SRD Data Fidelity — Rank Table Requirements

- [x] CHK001 Is the relationship between the SRD's bonus-skill level notation ("Zero-G-1") and
      the `RankEntry.bonus_skills` storage format (bare "Zero-G") explicit enough to prevent an
      implementer from storing the wrong value? [Clarity, Spec §FR-003] — **Verified**: FR-003's
      paragraph immediately after the rank table states the bare-name convention explicitly with
      concrete tuple examples, tied to the existing `NAVY_CAREER` precedent (verified against
      navy.py).
- [x] CHK002 Are rank titles specified for all seven ranks (0–6) with no gaps? [Completeness,
      Spec §FR-003] — **Verified**: all seven ranks 0–6 have titles in the FR-003 table,
      matching data-model.md's `MARINE_CAREER.ranks` tuple exactly.
- [x] CHK003 Is "no bonus skill" for ranks 1, 2, 4, 5, and 6 stated as an intentional empty
      value rather than left to be inferred by omission? [Clarity, Spec §FR-003] — **Resolved**:
      added a sentence to FR-003 stating these ranks intentionally use the empty tuple `()`, not
      an omitted value.
- [x] CHK004 Are Marine rank titles checked for consistency (capitalization pattern, no name
      collisions) against the rank titles of already-registered careers? [Consistency, Spec
      §FR-003, Data Model] — **Verified**: cross-checked all 7 Marine titles against
      `NAVY_CAREER`/`SCOUT_CAREER`/`AEROSPACE_CAREER` (navy.py, scout.py, aerospace.py).
      Capitalization is consistent Title Case, and the "Lt X" abbreviation matches Navy's "Lt
      Commander". Two titles ("Lieutenant", "Captain") intentionally overlap with Navy's — real
      military branches share generic officer rank names, and `career.ranks[rank].title` is
      per-career display only with no cross-career uniqueness requirement anywhere in the
      engine or tests, so this is not a defect.

## SRD Data Fidelity — Skill Table Requirements

- [x] CHK005 Are all four skill tables (Personal Development, Service Skills, Specialist,
      Advanced Education) specified with an explicit six-entry count requirement, rather than a
      count only implied by the table as printed? [Completeness, Spec §FR-004] — **Verified**:
      FR-004's table header literally states "Skills (positions 1–6)"; `Career.__post_init__`
      (base.py) enforces exactly 6 entries per table at import time, and data-model.md's
      Validation section confirms this passes for `MARINE_CAREER`.
- [x] CHK006 Is the Education 8+ gating condition on the Advanced Education table stated as a
      requirement in its own right, not only as a table label a reader could skip? [Clarity,
      Spec §FR-004] — **Resolved**: added a sentence to FR-004 (beyond the table's parenthetical
      label) stating the gate uses the engine's existing generic Education-8+ mechanism, already
      exercised by Scout in `tests/test_generator.py::test_education_8_or_above_can_access_advanced_education`
      — no Marine-specific logic needed.
- [x] CHK007 Are skill name spellings ("Gun Combat", "Melee Combat", "Vehicle", etc.) checked
      for consistency against identical skill names in other registered careers' tables, so no
      skill exists under two different spellings? [Consistency, Spec §FR-004, Data Model] —
      **Verified**: cross-checked every Marine skill name against navy.py/scout.py/aerospace.py;
      all shared names ("Gun Combat", "Melee Combat", "Vehicle", "Comms", "Demolitions",
      "Gunnery", "Electronics", "Survival", "Recon", "Advocate", "Computer", "Gravitics",
      "Medicine", "Navigation", "Tactics") use identical spelling/casing across all four
      careers. "Battle Dress" is new to Marine with no collision risk.

## SRD Data Fidelity — Mustering-Out Table Requirements

- [x] CHK008 Are cash and material benefits paired unambiguously by roll number (1–7), leaving
      no risk of misaligning a cash value with the wrong material row? [Clarity, Spec §FR-005] —
      **Verified**: FR-005's table pairs cash/material by roll number 1–7 unambiguously; matches
      the parallel `cash_benefits`/`material_benefits` tuples in data-model.md, indexed
      identically.
- [x] CHK009 Is the "Explorer's Society" vs. "Explorers' Society" spelling decision documented
      with its rationale (matches Scout), rather than left to implementer judgment? [Clarity,
      Spec §FR-005, Assumptions] — **Verified**: FR-005 states the rationale directly ("matching
      the spelling already established for the same benefit on the Scout career's material
      table"); cross-checked against scout.py — `SCOUT_CAREER.material_benefits[4] ==
      "Explorer's Society"` confirms an exact match.
- [x] CHK010 Is the roll-5 "+1 Soc" benefit's relationship to other careers' roll-5 benefits
      (matches Navy, differs from Aerospace) called out, so a reader won't assume all careers
      share a fixed roll-5 pattern? [Consistency, Data Model] — **Resolved**: data-model.md's
      field-notes table had a garbled, self-contradictory sentence ("differs from Navy's roll-5
      '+1 Soc' position match, but differs from Aerospace's...") — fixed to read "matches Navy's
      roll-5 '+1 Soc'; differs from Aerospace's roll-5 'Weapon'", verified against
      navy.py/aerospace.py source.

## Registry & Draft Table Integration Requirements

- [x] CHK011 Is the registry key format ("marine", lowercase, no hyphen) specified precisely
      enough to prevent an implementer from choosing a different key format? [Clarity, Spec
      §FR-006] — **Verified**: FR-006 states the key precisely as `"marine"` (lowercase, no
      hyphen); consistent with existing keys in registry.py.
- [x] CHK012 Does the spec state precisely which `DRAFT_TABLE` index/roll must change and which
      must not, preventing an implementer from also touching the still-unimplemented rolls 3
      and 6? [Clarity, Spec §FR-008] — **Verified**: FR-008 and plan.md's Implementation Notes
      both state index 1 (roll 2) changes and indices 2/5 (rolls 3/6) remain unchanged;
      cross-checked against the actual `DRAFT_TABLE` tuple in registry.py.
- [x] CHK013 Is the expected guarantee for registry lookup (identity vs. equality — e.g.
      `CAREER_REGISTRY["marine"] is MARINE_CAREER`) stated explicitly? [Measurability, Contract
      career-registry.md] — **Verified**: contracts/career-registry.md states the identity
      guarantee explicitly: `CAREER_REGISTRY["marine"] is MARINE_CAREER`.
- [x] CHK014 Are the registry-key requirement ("marine") and canonical-display-name requirement
      ("Marine") kept distinct enough that a reader won't conflate their expected casing?
      [Clarity, Spec §FR-006] — **Verified**: FR-006 distinguishes the registry key ("marine")
      from the canonical display name ("Marine") within the same sentence, with distinct casing.

## CLI Behavior & Near-Match Requirements

- [x] CHK015 Is the claim that zero CLI code changes are required backed by an explicit
      statement of why (registry-derived help text and near-match logic), so it can be verified
      rather than taken on faith? [Traceability, Spec §FR-009, §FR-010] — **Verified**: plan.md's
      Constitution Check and Implementation Notes both explain why (registry-derived
      `_CANONICAL_CAREERS`); cross-checked against src/cetools/cli/character.py:13-15 — confirmed
      `_CANONICAL_CAREERS` is computed from `CAREER_REGISTRY.values()` at import time with no
      career-specific code.
- [x] CHK016 Is the expected sorted-order position of "Marine" in the help text and error-message
      career list stated explicitly? [Completeness, Spec §FR-009, Plan] — **Verified**: plan.md
      and contracts/career-registry.md both give the exact sorted list "Aerospace System
      Defense, Marine, Navy, Scout".
- [x] CHK017 Are the near-match requirements for "Marines" (plural) and case variants tied to a
      concrete expected outcome, rather than a general "should still work"? [Measurability, Spec
      Edge Cases] — **Resolved**: verified `difflib.get_close_matches("marines", CAREER_REGISTRY
      .keys(), cutoff=0.6)` deterministically returns `["marine"]` (ratio ≈0.92); quickstart.md
      Scenario 6 now states the exact expected stderr (`Did you mean: Marine?`) instead of
      "either is acceptable," and tasks.md T009A adds a corresponding automated test.
- [x] CHK018 Is the exact unknown-career error string (punctuation and full valid-careers list)
      specified so it is objectively verifiable rather than paraphrased? [Measurability, Contract
      career-registry.md, Spec §FR-010] — **Verified**: contracts/career-registry.md and
      quickstart.md Scenario 6 both give the exact stderr string verbatim, including
      punctuation.

## Commission & Advancement Requirements

- [x] CHK019 Are the commission and advancement stat requirements (Education 6+, Social Standing
      7+) each tied unambiguously to a single stat name from the engine's existing stat set?
      [Clarity, Spec §FR-002] — **Verified**: FR-002 names "Education" and "Social Standing"
      exactly; both are literal entries in `STAT_NAMES` (models.py).
- [x] CHK020 Is the permanent-rank-1 case (Social Standing never reaches 7+) distinguished from
      the max-rank-reached edge case, so the two aren't conflated? [Coverage, Spec Edge Cases] —
      **Verified**: Edge Cases has two separate bullets — one for "Social Standing never reaches
      7+" (permanent rank 1) and one for "reaches rank 6" (max-rank cap) — now each
      cross-referenced to FR-002/Acceptance Scenario 2.2.
- [x] CHK021 Is the rank-based mustering-out bonus-roll rule (ranks 4/5/6) explicitly marked as
      reused generic engine behavior requiring no Marine-specific override, preventing duplicate
      logic? [Clarity, Spec §FR-011] — **Verified**: FR-011 explicitly states "without any
      Marine-specific override, since this behavior is already implemented generically";
      cross-checked against `_RANK_BONUS_ROLLS = {4: 1, 5: 2, 6: 3}` in generator.py — confirmed
      career-agnostic.
- [x] CHK022 Is the interaction between commissioning (rank 0→1) and the rank-0 bonus skill
      (Zero-G) — whether a newly commissioned officer retains it — addressed anywhere in the
      requirements? [Gap, Coverage] — **Resolved**: added FR-013 (spec.md) and a matching
      Assumptions bullet stating the existing `_grant_rank_bonus` mechanism is cumulative and
      generic (verified against `generator.py:191-192,239,246`); Acceptance Scenario 2.3 now
      cross-references it; plan.md gained an "Implementation Notes" entry with line refs.

## Test Migration & Regression Safety Requirements

- [x] CHK023 Are all four tests requiring the "marine"→"merchant" placeholder swap enumerated by
      name and file, leaving no ambiguity about scope? [Completeness, Spec §FR-012] —
      **Verified**: FR-012 enumerates all four tests by exact name and file; cross-checked
      against the actual test source — all four currently exist with the literal "marine"
      placeholder at the exact lines FR-012 describes (test_cli.py:189,195,203;
      test_generator.py:537,541).
- [x] CHK024 Is the rationale for rejecting "surface system defense" as the placeholder
      (similarity score, which CLI path it triggers) documented precisely enough to prevent a
      future contributor from reintroducing it? [Traceability, Spec Clarifications] —
      **Verified**: FR-012/research.md give exact similarity ratios; independently recomputed
      with `difflib.SequenceMatcher` — confirmed 0.826 ("surface system defense"), 0.766
      ("maritime system defense"), ≤0.31 ("merchant") against the four registered keys.
- [x] CHK025 Are the two additional pre-existing tests that hardcode the canonical-name list
      (not covered by FR-012 itself) identified as in-scope, with their exact expected updated
      strings specified? [Completeness, Plan Implementation Notes] — **Verified**: tasks.md
      T008/T009 give the exact updated expected strings for both tests
      (`test_career_unknown_stderr_message_exact`, `test_career_no_match_valid_careers_format`),
      matching plan.md's Implementation Notes verbatim.
- [x] CHK026 Is "zero regressions" (SC-005) defined precisely enough to be objectively verified,
      rather than left as a subjective judgment? [Measurability, Spec §SC-005] — **Verified**:
      SC-005 plus the Clarifications session and FR-012's closing sentence ("without
      contradicting SC-005") together establish that "zero regressions" means the full suite (as
      updated by FR-012's enumerated test edits) passes — not that no test file changes at all.
- [x] CHK027 Does the spec/plan distinguish tests that must change (FR-012 placeholder,
      canonical-list assertions) from tests that must not change (Navy/Scout/Aerospace-specific
      tests)? [Clarity, Consistency] — **Verified**: tasks.md enumerates every changing test by
      ID/name/file (T008, T009, T009A, T010, T019, T022) and explicitly notes (line 205) to
      re-run test_careers.py after T021 to confirm no Navy/Scout/Aerospace draft assertions
      regress.

## Edge Case & Scenario Coverage

- [x] CHK028 Is each edge case in the spec's Edge Cases section traceable to a specific
      functional requirement or acceptance scenario? [Traceability, Spec Edge Cases] —
      **Resolved**: added explicit "(see FR-XXX / Acceptance Scenario Y.Z)" cross-references to
      the five Edge Cases bullets that lacked one (the sixth already referenced FR-012).
- [x] CHK029 Is the behavior for a failed Marine survival roll specified precisely enough (reuse
      of existing injury/death rules) to prevent an implementer from inventing Marine-specific
      handling? [Clarity, Spec Acceptance Scenario 1.3] — **Verified**: Acceptance Scenario 1.3's
      "injury/death rules" phrasing matches identical wording already used in
      specs/003-aerospace-system-defense-career/spec.md — an established project convention, not
      a Marine-specific ambiguity. Confirmed the engine has a single generic failure path
      (`GenerationFailure` in generator.py) reused unchanged for all careers.
- [x] CHK030 Is it explicit that the still-unimplemented draft slots (rolls 3 and 6) are out of
      scope for this feature, to prevent scope creep during implementation? [Boundary, Spec
      Assumptions] — **Verified**: FR-008, the Assumptions section, and an Edge Cases bullet all
      state explicitly that rolls 3 and 6 remain unimplemented placeholders out of scope.

## Non-Functional Requirements

- [x] CHK031 Is the 85% coverage requirement (SC-006) scoped clearly to `src/cetools/` overall,
      rather than left ambiguous about whether the new module alone must hit 85%? [Clarity, Spec
      §SC-006] — **Verified**: SC-006 states coverage applies to `src/cetools/` overall ("after
      the new career module and any supporting changes are added"), not to marine.py in
      isolation.
- [x] CHK032 Does the spec establish a verifiable basis for "matches the SRD exactly" (FR-002–
      FR-005) beyond visual table comparison, so fidelity claims are checkable rather than
      asserted? [Measurability, Spec §FR-002-FR-005] — **Verified**: the practical verification
      basis is (a) the documented cross-fetch process in checklists/requirements.md Notes, and
      (b) tasks.md T003–T005's automated tests asserting exact position-by-position values
      against the spec's own tables — consistent with how Navy/Scout/Aerospace fidelity was
      previously established.

## Dependencies & Assumptions

- [x] CHK033 Is the assumption that the `Career` dataclass needs zero structural changes checked
      against the actual field set Marine requires, rather than asserted without cross-check?
      [Assumption, Spec Assumptions] — **Verified**: cross-checked `MARINE_CAREER`'s field list
      (data-model.md) against the actual `Career` dataclass fields in base.py — every field is
      used, none are missing or extraneous; `__post_init__` validates cleanly per
      data-model.md's Validation section.
- [x] CHK034 Is the assumption that "Social Standing" is already a valid engine stat name
      explicitly grounded, given Marine is the first career to use it as an advancement stat?
      [Assumption, Spec Assumptions, User Story 2] — **Verified**: `"Social Standing"` is
      confirmed present in `STAT_NAMES` (models.py) and is already used by `NAVY_CAREER` as
      `commission_stat` — Marine is the first to use it as `advancement_stat` specifically, which
      data-model.md's field-notes table already calls out.

## Ambiguities & Conflicts

- [x] CHK035 Could FR-003's SRD table notation ("Zero-G-1") and the `RankEntry.bonus_skills`
      storage format ("Zero-G") read as conflicting to someone unfamiliar with the Navy
      precedent, and is the reconciling sentence prominent enough to prevent misimplementation?
      [Ambiguity, Spec §FR-003] — **Verified**: the reconciling paragraph is the sentence
      immediately following the FR-003 rank table (not buried elsewhere), giving a concrete
      tuple example (`("Zero-G",)`) tied explicitly to the pre-existing Navy convention —
      prominent enough to prevent misimplementation.
- [x] CHK036 Does FR-011's "no Marine-specific override" risk conflicting with Acceptance
      Scenario 2.4, which restates the bonus-roll counts in Marine-specific terms — could a
      reader implement a duplicate override believing it's required? [Conflict, Spec §FR-011 vs
      Acceptance Scenario 2.4] — **Verified, not a conflict**: Acceptance Scenario 2.4 already
      says "the character receives **the existing** rank-based bonus benefit rolls," explicitly
      flagging the rolls as reused/generic rather than Marine-specific. No spec change needed.

## Notes

- Check items off as completed: `[x]`
- Add comments or findings inline
- This checklist is comprehensive (SRD data fidelity + registry/draft/CLI integration + test
  migration & regression safety) at standard depth, intended for the author to run against
  spec.md/plan.md before implementation begins.
- **2026-07-01 full review completed**: all 36 items verified against spec.md, plan.md,
  data-model.md, contracts/career-registry.md, research.md, quickstart.md, tasks.md, and the
  actual source (`base.py`, `navy.py`, `scout.py`, `aerospace.py`, `registry.py`,
  `generator.py`, `character.py`, `models.py`) and existing tests. Four genuine gaps were found
  and fixed: (1) FR-003 lacked an explicit statement that ranks 1/2/4/5/6 intentionally have no
  bonus skill; (2) FR-004 stated the Education 8+ gate only as a table-label parenthetical, not
  as prose; (3) data-model.md had a garbled, self-contradictory sentence about the roll-5 "+1
  Soc" benefit's relationship to Navy/Aerospace; (4) five of six Edge Cases bullets lacked
  explicit FR/Acceptance-Scenario cross-references. All four were corrected directly in
  spec.md/data-model.md. No other defects found; the remaining 32 items were already adequately
  specified and are annotated above with their verification basis.
