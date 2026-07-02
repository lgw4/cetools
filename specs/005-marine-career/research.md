# Research: Marine Career

## SRD Table Values

**Decision**: Use the values specified in FR-002 through FR-005 of the spec verbatim.

**Rationale**: The spec was authored by cross-referencing the Cepheus Engine SRD at
https://evolvedexperiment.github.io/cepheus-srd/index.html and is considered authoritative
for this feature.

**Alternatives considered**: N/A — the SRD is the single source of truth per Constitution §I.

---

## Rank Table Bonus-Skill Encoding ("Zero-G-1", "Tactics-1")

**Decision**: Store bare skill names in `RankEntry.bonus_skills` — `("Zero-G",)` for rank 0 and
`("Tactics",)` for rank 3 — matching the SRD notation "Zero-G-1"/"Tactics-1" (skill + level 1).

**Rationale**: The engine already applies bonus skills at level 1 when awarding them
(`generator.py` iterates `rank_entry.bonus_skills` and grants each at level 1). `NAVY_CAREER`
already stores its rank-0 bonus as bare `"Zero-G"` and rank-3 bonus as bare `"Tactics"` — Marine
uses the identical convention. No engine change needed.

**Alternatives considered**: Storing `"Zero-G-1"` as a literal string — rejected because it
would require new parsing logic in the engine (violates Constitution §V: adding a career must
require zero engine changes) and is inconsistent with the existing Navy/Aerospace pattern.

---

## Draft Table Correction

**Decision**: Change `DRAFT_TABLE` index 1 (roll result 2, via `DRAFT_TABLE[roll - 1]`) from
`"navy"` to `"marine"` in `registry.py`. Update `test_draft_table_other_entries_are_navy` to
also exclude index 1 from the "must be navy" assertion.

**Rationale**: The SRD assigns draft roll 2 to Marines (FR-008). Indices 2 and 5 (rolls 3 and
6 — Maritime System Defense and Surface System Defense) remain `"navy"` placeholders; those
careers are out of scope for this feature per spec Assumptions.

**Alternatives considered**: Leaving the draft table as-is — rejected as an SRD-fidelity
violation and a direct contradiction of FR-008/User Story 3.

---

## Registry Key Convention

**Decision**: Use `"marine"` (all lowercase, single word) as the registry key.

**Rationale**: Consistent with existing keys `"navy"`, `"scout"`, `"aerospace system defense"`.
The CLI's existing `.strip().lower().replace("-", " ")` normalization (unchanged, FR-007)
resolves any casing of "Marine" to this key without new code.

**Alternatives considered**: N/A — single-word name has no hyphen/multi-word ambiguity to
resolve, unlike "Aerospace System Defense".

---

## Placeholder Test Value: "marine" → "merchant" (supersedes spec's original "surface system defense")

**Decision**: Replace the literal `"marine"` placeholder in four pre-existing tests with
`"merchant"`, not `"surface system defense"` as originally specified in FR-012.

**Rationale**: `test_career_unknown_stderr_message_exact` asserts the CLI's exact "no close
match → Valid careers list" error format. Verified via `difflib.SequenceMatcher`:

```
"surface system defense"  vs "aerospace system defense" → ratio 0.826
"maritime system defense" vs "aerospace system defense" → ratio 0.766
"merchant"                vs all four registered keys    → ratio ≤ ~0.31
```

The CLI's cutoff is 0.6 (`difflib.get_close_matches(normalized, CAREER_REGISTRY.keys(), n=1,
cutoff=0.6)` in `character.py`). Both SRD-derived candidates named in the spec's Edge Cases
section share the `"... system defense"` suffix with the already-registered
`"aerospace system defense"`, scoring well above cutoff — the CLI would emit
`"Did you mean: Aerospace System Defense?"` instead of the `"Valid careers: ..."` list the test
expects, permanently failing it regardless of implementation correctness. "Merchant" is a real,
unimplemented Cepheus SRD career (preserving the original intent of using a real
not-yet-implemented career name as the placeholder) with no textual overlap with any registered
career name.

Confirmed with the user (AskUserQuestion, 2026-07-01): use `"merchant"` uniformly across all
four FR-012 tests. Spec updated accordingly (see spec.md Clarifications, second entry; FR-012;
Edge Cases).

**Alternatives considered**:
- Keep `"surface system defense"`, update the exact-message test's expected string to the
  "did you mean" format — rejected: changes what the test verifies (from "no match" behavior to
  "near match" behavior), losing coverage of the "no close match" code path entirely.
- Split placeholders (different strings per test) — rejected: adds inconsistency for no benefit
  once a single non-colliding value (`"merchant"`) satisfies every test's constraints.

---

## Canonical Career List in Existing Hardcoded Assertions

**Decision**: Beyond the four FR-012 tests, two more pre-existing `test_cli.py` assertions
hardcode the full sorted canonical-name list (`"Aerospace System Defense, Navy, Scout"`) and
must be updated to insert `"Marine"` alphabetically (`"Aerospace System Defense, Marine, Navy,
Scout"`): `test_career_unknown_stderr_message_exact` and
`test_career_no_match_valid_careers_format`. No production code changes accompany this — the
list is derived from `CAREER_REGISTRY` at import time (FR-009), already exercised by feature 003.

**Rationale**: These two tests were not enumerated in FR-012 because their trigger value
(`"marine"` vs `"xyzzy"`) differs, but both independently break once Marine is registered,
since the registry now yields a 4-name list, not 3. This is a discovered SC-005 regression risk
requiring a test-only fix, not a spec ambiguity.

**Alternatives considered**: N/A — purely mechanical, follows directly from FR-006/FR-009.
