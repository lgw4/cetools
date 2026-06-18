# Research: Aerospace System Defense Career

## SRD Table Values

**Decision**: Use the values specified in FR-002 through FR-005 of the spec verbatim.

**Rationale**: The spec was authored by cross-referencing the Cepheus Engine SRD at
https://evolvedexperiment.github.io/cepheus-srd/index.html and is considered authoritative
for this feature.

**Alternatives considered**: N/A — the SRD is the single source of truth per Constitution §I.

---

## "Did You Mean" Suggestion Algorithm

**Decision**: Use `difflib.get_close_matches(normalized_input, CAREER_REGISTRY.keys(), n=1, cutoff=0.6)`.

**Rationale**: `difflib` is Python stdlib (no new dependency). `get_close_matches` uses
SequenceMatcher ratios (character-level similarity) which works well for career name typos
(e.g., "Areospace" → "aerospace system defense", "nave" → "navy"). Cutoff 0.6 matches common
CLI conventions (conservative enough to avoid false positives).

**Alternatives considered**:
- Levenshtein distance via third-party library (`python-Levenshtein`) — rejected because it
  adds a dependency where stdlib suffices.
- Prefix matching — rejected because it doesn't handle transpositions or middle-of-word typos.

---

## Material Benefits Table Length

**Decision**: The Aerospace material table has 7 entries (same as Navy, rolls 1–7). The engine
already handles variable-length material tables via `len(career.material_benefits) - 1` as the
index cap in `_muster_out`. No engine change needed.

**Rationale**: The SRD Aerospace mustering-out table has 7 rows (1,000 Cr through +1 Soc).

**Alternatives considered**: N/A — this is purely a data correctness observation.

---

## Draft Table Correction

**Decision**: Change `DRAFT_TABLE` index 0 from `"navy"` to `"aerospace system defense"` in
`registry.py`. Update `test_draft_table_other_entries_are_navy` to whitelist index 0 as the
Aerospace slot.

**Rationale**: The SRD assigns draft roll 1 (index 0) to Aerospace System Defense. The spec
assumption that "The draft table already references 'Aerospace System Defense' by name" was
incorrect — the current code has `"navy"` at index 0. This must be corrected for FR-008
compliance.

**Alternatives considered**: Leaving draft table as-is — rejected as an SRD-fidelity violation.

---

## Registry Key Convention

**Decision**: Use `"aerospace system defense"` (all lowercase, spaces) as the registry key.
Normalization in the CLI converts input to lowercase and replaces hyphens with spaces before
lookup, enabling both `"Aerospace System Defense"` and `"aerospace-system-defense"` to resolve.

**Rationale**: Consistent with existing keys `"navy"` and `"scout"` (lowercase, no hyphens).
The CLI is the only lookup site; normalization belongs there (CLI layer, not engine).

**Alternatives considered**: Using the canonical name as the key (`"Aerospace System Defense"`)
— rejected to maintain consistency with existing registry key convention.

---

## Help Text Career Name Enumeration

**Decision**: Derive the help text career name list from `CAREER_REGISTRY.values()`, using
`career.name` for canonical casing. Computed at module import time (no runtime cost).

**Rationale**: FR-010 requires the help text to enumerate all valid canonical career names.
Deriving from the registry means adding a new career automatically updates the help text without
any CLI code change.

**Alternatives considered**: Hardcoding the list — rejected because it creates a maintenance
hazard every time a new career is added (contradicts the spirit of Constitution §V).
