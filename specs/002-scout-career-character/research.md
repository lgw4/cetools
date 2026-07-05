# Research: Scout Career & Career Selection Flag

**Feature**: 002-scout-career-character | **Date**: 2026-06-18

All NEEDS CLARIFICATION items from the Technical Context have been resolved. This document records the decisions and rationale for each.

---

## 1. Scout Career Data (SRD Source)

**Decision**: Scout career data is sourced directly from the Cepheus Engine SRD (https://evolvedexperiment.github.io/cepheus-srd/character-creation.html). All values match the spec FR-002 through FR-005.

**Rationale**: SRD is the authoritative source per Constitution §I.

**Alternatives considered**: None — SRD values are fixed.

### Scout Career Summary (from SRD)

| Field | Value |
|-------|-------|
| Qualification | Intelligence 6+ (raw value, no 2D6 roll) |
| Survival | Endurance 7+ |
| Commission | None |
| Advancement | None |
| Re-enlistment | 6+ |
| Skill rolls per term | 2 (via existing `not commissioned_this_term and not promoted_this_term` branch) |
| Basic training | All service skills at level 0, term 1 |
| Rank 0 bonus | Piloting (raises from 0 to 1 after basic training grants it at 0) |

### Skill Tables (SRD)

| Table | Entries |
|-------|---------|
| Personal Development | +1 Str, +1 Dex, +1 End, Jack o' Trades, +1 Edu, Melee Combat |
| Service Skills | Comms, Electronics, Gun Combat, Gunnery, Recon, Piloting |
| Specialist Skills | Engineering, Gunnery, Demolitions, Navigation, Medicine, Vehicle |
| Advanced Education (Edu 8+) | Advocate, Computer, Linguistics, Medicine, Navigation, Tactics |

### Mustering-Out Tables (SRD)

| Roll | Cash | Material |
|------|------|----------|
| 1 | Cr1,000 | Low Passage |
| 2 | Cr5,000 | +1 Edu |
| 3 | Cr10,000 | Weapon |
| 4 | Cr10,000 | Mid Passage |
| 5 | Cr20,000 | Explorers' Society |
| 6 | Cr50,000 | Courier Vessel |
| 7 | Cr50,000 | — (no 7th material entry per SRD) |

**Note**: The SRD Scout material table has only 6 entries. The cash table has 7. This matches the existing `Career.material_benefits` tuple (6 entries in the Navy material table also use a 6-index 1D6 roll; the `_muster_out` function uses `roller.roll(6)` which yields 1–6).

---

## 2. Qualification Re-roll Loop Architecture

**Decision**: Implement `roll_until_qualified(career, roller) -> dict[str, int]` in `src/cetools/engine/generator.py`. This function loops, rolling all six characteristics each iteration, until `characteristics[career.qualification_stat] >= career.qualification_target`. It returns the qualifying characteristic set. Background skills and rank bonuses are NOT applied in this function.

**Rationale**: The spec requires the loop to be engine-side (FR-008, SC-003). The function is pure (only dice + career data) and trivially testable with a seeded roller. Constitution §II requires all game logic in `src/cetools/engine/`.

**Alternatives considered**:
- Loop inside `generate_character`: rejected because it entangles re-roll concerns with term processing, making the function harder to test in isolation.
- Loop in CLI: rejected; violates Constitution §II.

---

## 3. `generate_character` Extension Parameters

**Decision**: Add three optional parameters to `generate_character`:
- `preset_characteristics: dict[str, int] | None = None` — when provided, skips the internal characteristic roll and uses these values.
- `bypass_qualification: bool = False` — when True, skips the enlistment/qualification roll.
- `hard_max_terms: bool = False` — when True, natural-12 at the 7-term cap triggers mustering-out instead of a mandatory 8th term (FR-015).
- `drafted: bool = False` — when True, sets `Character.drafted = True` on the returned character.

**Rationale**: The re-roll loop (`roll_until_qualified`) produces pre-qualified characteristics externally; `generate_character` must accept them to avoid double-rolling. `bypass_qualification` separates the enrollment model from the existing enlistment-roll model. `hard_max_terms` enforces FR-015 for Scout without a Career field (FR-001). `drafted` propagates the draft origin to the output model (FR-011).

**Alternatives considered**:
- New Career field for hard cap: rejected per FR-001.
- Separate `generate_character_for_scout`: rejected per §V (no duplication of engine logic).
- Infer hard cap from `commission_stat is None`: rejected as undocumented coupling.

---

## 4. New Engine Entry Points

**Decision**: Add two public engine functions to `generator.py`:

```python
def generate_career_character(
    career: Career,
    roller: DiceRoller | None = None,
    drafted: bool = False,
) -> Character | GenerationFailure:
    """Re-roll characteristics until qualified, then generate."""

def draft_character(
    roller: DiceRoller | None = None,
) -> Character | GenerationFailure:
    """Roll draft table, look up career, and generate (no enlistment roll)."""
```

`draft_character` looks up the career name in `CAREER_REGISTRY`. If the name is not found, returns `GenerationFailure` (exit code 1, clear message) per FR-010.

**Rationale**: The CLI calls a single engine function for both paths (FR-008, spec intent). Separating these into named functions makes them independently testable.

**Alternatives considered**:
- Single function with a `mode` enum: rejected as unnecessary complexity.

---

## 5. Career Registry and Draft Table

**Decision**: Create `src/cetools/engine/careers/registry.py` containing:

```python
CAREER_REGISTRY: dict[str, Career] = {
    "navy": NAVY_CAREER,
    "scout": SCOUT_CAREER,
}

DRAFT_TABLE: tuple[str, ...] = ("navy", "navy", "navy", "navy", "scout", "navy")
```

**Rationale**: Centralises the career map for both CLI validation (FR-007) and the draft function (FR-010). Expanding to future careers requires only a new entry in each structure. The registry is the single source of truth for valid career names.

**Alternatives considered**:
- Inline dict in `character.py` CLI: rejected per Constitution §II.
- Auto-discover careers via `__subclasses__`: over-engineered; no second use case yet.

---

## 6. `Character.drafted` Field

**Decision**: Add `drafted: bool = False` to the `Character` dataclass.

**Rationale**: The formatter must know whether the career line should include "(Drafted)" (FR-011). Encoding this in the model keeps the formatter stateless and the call site clean.

**Alternatives considered**:
- Pass `drafted` as a separate formatter argument: rejected because it leaks call-site knowledge and breaks the value-object contract of `Character`.

---

## 7. Formatter Update

**Decision**: In `formatter.py`, change the career line from:

```python
f"{character.career} ({character.rank_title}, Rank {character.rank}) — ..."
```

to:

```python
origin = " (Drafted)" if character.drafted else ""
f"{character.career}{origin} ({character.rank_title}, Rank {character.rank}) — ..."
```

**Rationale**: FR-011 requires `{career} (Drafted) ({rank_title}, Rank {rank}) — {terms} terms, age {age}` for drafted characters.

---

## 8. CLI Update

**Decision**: Add `career: Optional[str] = typer.Option(None, "--career")` to the `generate` command. Strip and lowercase before validation. On unrecognized name: print `Unknown career '{original}'. Valid careers: navy, scout` to stderr, exit 1. Call `generate_career_character(CAREER_REGISTRY[name])` for named careers, `draft_character()` when flag is absent.

**Rationale**: FR-007, FR-012. The error message uses the pre-normalization value per spec clarification.

---

## 9. FR-015 Hard Cap — Deviation from SRD

**Decision**: When `hard_max_terms=True` is passed to `generate_character`, the natural-12 branch at the 7-term cap is suppressed; the character mustering-out immediately. This flag is passed by `generate_career_character` and `draft_character` when the career is Scout (or any future career that warrants a hard cap via the calling wrapper).

**Rationale**: FR-015 is an explicit, documented deviation from the SRD. The re-roll loop entry point controls this behavior; direct callers of `generate_character(scout_career, ...)` (such as SC-003 tests) operate with the default `hard_max_terms=False` and retain the existing natural-12 behavior. This is acceptable because SC-003 tests valid Character output, not the exact term count boundary.

**Alternatives considered**:
- Enforce hard cap in `generate_character` unconditionally: breaks Navy behavior.
- `Career` field: violates FR-001.

---

## 11. Pension Table (SRD)

**Source**: SRD (https://evolvedexperiment.github.io/cepheus-srd/character-creation.html), Aging & Retirement section.

| Terms Served | Annual Pension |
|--------------|----------------|
| 1–4 | None |
| 5 | Cr10,000 |
| 6 | Cr12,000 |
| 7 | Cr14,000 |
| 8 | Cr16,000 |
| 9+ | Cr16,000 + Cr2,000 per term beyond 8 |

The SRD pension rule applies to all careers (it is not restricted to commissioned careers). The engine constant `_PENSION = {5: 10000, 6: 12000, 7: 14000, 8: 16000}` and its fallback formula `16000 + (terms_served - 8) * 2000` match these values exactly. FR-013 references these amounts; this table is the SRD citation backing them.

**Note**: Scout's 7-term hard cap (FR-015) means a Scout character can receive at most Cr14,000/year pension. The 8-term entry is included for completeness and for Navy characters who may reach 8 terms.

---

## 10. Best Practices: typer Optional Flag

**Decision**: Use `typer.Option(None)` for `--career`. When `None`, call `draft_character()`; when a string, normalize and validate.

**Rationale**: typer's `Optional[str]` with `None` default is the idiomatic pattern for optional flags. No additional dependencies needed.
