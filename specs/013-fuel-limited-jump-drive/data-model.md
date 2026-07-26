# Phase 1 Data Model: Fuel-Limited Jump Drive Rating

**Feature**: `013-fuel-limited-jump-drive` | **Date**: 2026-07-26

This feature introduces **no new persisted types**. `ShipDesign`, `Ship`, `DriveRow` and the TOML
schema are all unchanged, so every design written before this feature still loads and every design
written after it still round-trips. What changes is *which* `jump_code` the generator writes into an
existing `ShipDesign` field.

The entities below are the spec's Key Entities mapped onto the code that already holds them, plus
the one new in-memory value the search introduces.

---

## Existing entities (unchanged shape, changed selection)

### Jump drive option

The spec's "drive letter legal for a hull, with a tonnage cost and a hull-dependent rating". Already
split across two tables, joined by the letter:

| Field | Source | Notes |
| --- | --- | --- |
| letter | `DRIVE_COSTS` key / `DRIVE_PERFORMANCE` key | `"A"`–`"Z"`, skipping `I` and `O` |
| `jump_tons` | `DRIVE_COSTS[letter].jump_tons` | Strictly increasing in letter order (research Part C) |
| rating | `DRIVE_PERFORMANCE[letter][hull_tons]` | Absent key means the letter is illegal on that hull |

**Legality**: a letter is legal for a hull iff `hull_tons in DRIVE_PERFORMANCE[letter]`. This is the
same predicate `generator._codes_valid_for_hull` already uses; the fit search reuses it rather than
restating it.

**Invariants** (research Part C, newly pinned by a table test):

- `jump_tons` is strictly increasing in letter order across all of `DRIVE_COSTS`.
- For each hull, rating is non-decreasing in letter order across that hull's legal letters.

These are properties of the transcribed SRD tables, not assumptions the search may rely on
implicitly: the search selects the lightest drive by explicit comparison, and the table test exists
so a future SRD row that breaks either invariant fails visibly.

### Jump fuel

Not a stored field. Derived twice, from the same arithmetic:

- `builder.build_ship`: `jump_fuel = 0.1 * hull_tons * jump_distance`, recorded as a
  non-discountable `LineItem` and surfaced as `Ship.jump_fuel`.
- `generator`: the same expression, to decide how much fuel the remaining tonnage buys.

One complete jump at rating `N` costs `0.1 * hull_tons * N`. Unchanged by this feature.

### Mandatory systems

The allocations made before any discretionary fitting, and therefore the baseline the drive search
measures against. Already computed in `generate_ship`:

| Component | Expression | Note |
| --- | --- | --- |
| maneuver drive | `DRIVE_COSTS[maneuver_code].maneuver_tons` | |
| power plant | `DRIVE_COSTS[power_code].power_tons` | |
| power-plant fuel | `(power_tons // 3) * 2` | 2 weeks, starship floor |
| bridge | `_bridge_tons(hull_tons)` | from `BRIDGE_SIZES` |

The jump drive is **excluded** — it is what the search is choosing.

### Generated ship

`Ship`, returned by `build_ship`. Two fields must agree after this feature, and did not before:

- `Ship.jump_rating` — derived from the installed `jump_code`.
- `Ship.assumed_jump_distance` — the `jump_distance` the design bought fuel for.

**New post-condition on the generated path**: `assumed_jump_distance == jump_rating`, except under
the FR-014 fallback. Note this is *stronger* than FR-001's "at least one complete jump": the
generator never buys more than one jump's worth of fuel, so "at least one" and "exactly the rating"
coincide here. Authored designs are unaffected and may still set any `jump_distance >= 0`.

---

## New value: the jump-drive fit

A pure, in-memory computation in `generator.py`. Not a dataclass, not persisted, not exported.

**Inputs**

| Name | Type | Meaning |
| --- | --- | --- |
| `hull_tons` | `int` | A tabulated standard hull size |
| `drawn_code` | `str` | The letter `RollName.SHIP_JUMP_CODE` produced; the search's ceiling |
| `budget` | `float` | Hull tonnage less the mandatory systems above |

**Output**: a single drive letter — the code to install.

**Selection rule** (FR-003, FR-004, FR-014), stated as a total function:

1. Let `ceiling = DRIVE_PERFORMANCE[drawn_code][hull_tons]`.
2. Let `candidates` be the legal letters for `hull_tons` whose rating is `<= ceiling`, reduced to
   the **lightest letter per distinct rating** (FR-004, applied unconditionally).
3. Return the candidate of **highest rating** satisfying
   `jump_tons + 0.1 * hull_tons * rating <= budget` (FR-003).
4. If no candidate satisfies it, return the candidate of **lowest rating** (FR-014).

**Properties**

- **Total**: `drawn_code` is itself legal for `hull_tons`, so `candidates` is never empty and step 4
  always has an answer. No exception path.
- **Non-increasing rating**: the returned rating is `<= ceiling` by construction (FR-006, SC-007).
- **Idempotent**: feeding the result back as `drawn_code` with the same budget returns the same
  letter — the rule has no oscillation.
- **Draw-free**: reads only tables and arithmetic; touches no `Rolls` (FR-008).
- **Hull-preserving**: `hull_tons` is an input, never an output (FR-011).

---

## Allocation order in `generate_ship`

The one structural change. Today the jump drive is paid for before `remaining` is known; after this
feature `remaining` is split into a pre-drive budget and a post-drive remainder, so freed tonnage
flows on to fuel and fittings (FR-005).

**Before**

```text
remaining = max(0, hull - (jump + maneuver + power + bridge + power_fuel))
jump_distance = min(jump_rating, floor(remaining / (0.1 * hull)))
remaining -= 0.1 * hull * jump_distance
→ armor, computer, electronics, staterooms, fitting, turrets, bay, screen
```

**After**

```text
budget    = hull - (maneuver + power + bridge + power_fuel)      # jump drive excluded
jump_code = fit(hull, drawn_jump_code, budget)                   # new step, no draws
remaining = max(0, budget - jump_tons(jump_code))
jump_distance = min(jump_rating, floor(remaining / (0.1 * hull)))   # arithmetic unchanged
remaining -= 0.1 * hull * jump_distance
→ armor, computer, electronics, staterooms, fitting, turrets, bay, screen   # unchanged
```

The `jump_distance` arithmetic is deliberately kept verbatim. Under FR-003 it now always resolves to
the full rating; under FR-014 it degrades to partial fuel with no special-casing, which is exactly
the fallback's stated behaviour. The `max(0, ...)` clamp is retained as the FR-013 safety net.

Draw sequence is untouched: `SHIP_JUMP_CODE`, `SHIP_MANEUVER_CODE` and `SHIP_POWER_CODE` are drawn
in the same order by the same `_select_drive_codes`, and `SHIP_NAME` stays last.

---

## Small-craft path

Not modelled. `_generate_small_craft` mounts no jump drive, computes no jump budget, and is not
touched by this feature (FR-010, SC-005). Its output is byte-for-byte unchanged.
