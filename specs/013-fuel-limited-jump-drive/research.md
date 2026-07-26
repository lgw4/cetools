# Phase 0 Research: Fuel-Limited Jump Drive Rating

**Feature**: `013-fuel-limited-jump-drive` | **Date**: 2026-07-26

Every question below was answered by reading `src/cetools/engine/ships/` and by running
measurements against the current tables. No `NEEDS CLARIFICATION` remains.

Reproduction script for every measurement in this document:
`specs/013-fuel-limited-jump-drive/scripts/survey_drive_fit.py` (see quickstart.md).

---

## Part A: Where the defect actually lives

**Question**: Which line produces the "zero Jump-6 jumps" sentence?

**Finding**: Two lines, one file each.

`engine/ships/generator.py:380-382` buys jump fuel out of whatever tonnage is left *after* the drive
has already been paid for:

```python
max_jump_distance = math.floor(remaining / (0.1 * hull_tons))
jump_distance = max(0, min(jump_rating, max_jump_distance))
```

`engine/ships/description.py:165` then reports the ship's range as an integer division:

```python
jumps = ship.assumed_jump_distance // ship.jump_rating if ship.jump_rating else 0
```

**Decision**: The two lines together explain the report. A Jump-6 drive with fuel for 5 jump-numbers
has `assumed_jump_distance == 5`, and `5 // 6 == 0`, so the description says "zero Jump-6 jumps"
even though 5 tons-per-jump-number of fuel were paid for. The fix belongs in the generator, not the
renderer: the renderer is presentation-only (CONTEXT.md) and its arithmetic is correct — a ship that
cannot complete one jump genuinely has a range of zero.

**Rationale**: Correcting `description.py` would launder the defect into prose while leaving the
wasted tonnage in place. FR-002 asks for a smaller drive, not a kinder sentence.

**Alternatives considered**: Rounding the reported jump count up (hides the waste); raising an error
on a short-fuelled generated ship (turns a 5.5% defect into a 5.5% crash rate).

---

## Part B: Confirming the reported frequency

**Question**: Do the spec's "111 of 2000 (5.5%)" and "zero jumps" claims describe the same set?

**Finding**: Yes, and the metric to use is the *description's* jump count, not
`assumed_jump_distance`.

| Metric | 2000 seeds | 10000 seeds |
| --- | --- | --- |
| `assumed_jump_distance < jump_rating` (short-fuelled) | 111 (5.55%) | 534 (5.34%) |
| `assumed_jump_distance == 0` (no jump fuel at all) | 0 | 0 |
| `assumed_jump_distance // jump_rating == 0` (reports zero jumps) | 111 | 534 |

**Decision**: "Fewer than one full jump" and "reports zero jumps" are the same condition, because
`assumed_jump_distance` never exceeds `jump_rating` on the generated path. SC-001 and SC-004
therefore measure one population by two routes, and a test may assert either.

**Rationale**: Confirms the spec's own observation that every affected ship carries *partial* fuel,
never zero. The spec's Overview quotes a ship with "56 tons" of tankage reporting zero Jump-6 jumps
— that is partial fuel misreported, exactly as Part A predicts.

---

## Part C: Two table invariants the search can rely on

**Question**: Is the "lightest drive at a rating" always findable, and is the search well-ordered?

**Finding**: Over the whole of `DRIVE_COSTS` and `DRIVE_PERFORMANCE`, in letter order:

1. `jump_tons` is **strictly increasing** — 0 non-monotone pairs across all 276 letter pairs.
2. Per hull, `rating` is **non-decreasing** — 0 hulls out of 18 violate it.

Together: for any hull, the lightest drive at a given rating is the *earliest legal letter* holding
that rating, and scanning legal letters in order visits ratings in non-decreasing order.

**Decision**: Implement the search by explicit `min(..., key=jump_tons)` per rating rather than by
relying on letter order. State the invariant and pin it with a table test
(`test_ship_tables.py`), so a future SRD table edit that breaks it fails loudly instead of silently
selecting a heavier drive.

**Rationale**: Constitution V (Data-Driven Extensibility) says adding a table row must not require
engine changes. Depending on an unstated ordering invariant would violate that in spirit: the row
would be accepted and the engine would quietly do the wrong thing.

**Alternatives considered**: Precomputing a `LIGHTEST_JUMP_DRIVE[hull][rating]` lookup table in
`tables.py` (adds derived data to a file that is meant to hold transcribed SRD rows, and would
itself need regenerating on a table edit); trusting letter order implicitly (silent failure mode).

---

## Part D: How often FR-004 moves a ship that was never broken

**Question**: The spec warns that the same-rating substitution moves more seeds than the downgrade
does. How many?

**Finding**: Rating ties exist on every hull of 300 tons and up, and on the larger hulls at every
rating from 1 to 6. Examples: at 400 tons, drives B and C both give Jump-1 (15 t vs 20 t); at 700
tons, drives U through Z all give Jump-6 (100 t vs 125 t — a 25-ton saving).

Across 2000 seeds, **1087 (54.4%)** carry a jump drive whose rating is available from a lighter
letter. That is the population whose output moves, against 111 (5.5%) moved by the downgrade alone.

**Decision**: Accept it, as the spec's Assumptions section already does. Do **not** try to preserve
byte-for-byte output. Confirms the plan must re-establish the feature-012 baseline guard rather than
attempt to satisfy it.

**Rationale**: A 20-ton drive delivering what a 15-ton drive delivers is strictly wasted tonnage;
FR-004 makes it cargo. Preserving the old output would mean preserving the waste.

**Alternatives considered**: Applying the lightest-drive rule only to downgraded ships (would leave
the other 976 seeds carrying pointless tonnage, and makes the rule conditional and harder to state).

---

## Part E: Is the FR-014 starved-hull fallback reachable?

**Question**: The spec says the fallback was not observed in a 2000-seed sweep. Is it reachable at
all?

**Finding**: No — not for any seed, ever, given the current tables. Enumerating the **full cross
product** of (hull size x legal maneuver code x legal power code) — every combination the generator
could ever draw, 2,404 in total — yields **zero** cases where no legal jump drive fits its own
tonnage plus one full jump of fuel inside the post-mandatory budget.

The tightest case is the 100-ton hull, whose lowest-rated legal drive is A (Jump-2, 10 t). Its worst
budget is 69 tons against a 30-ton requirement (10 t drive + 20 t fuel).

**Decision**: Implement FR-014 anyway, and test it by calling the fit helper directly with a
synthetic budget rather than by hunting for a seed that triggers it.

**Rationale**: FR-014 exists to give the rule a defined boundary. A branch that no seed can reach is
still a branch the tables could reach after an SRD edit — and an unreachable branch that is never
exercised is worse than one covered by a direct unit test. Testing it through `generate_ship` is
impossible; testing the helper directly is trivial. This also keeps the 85% coverage gate honest.

**Alternatives considered**: Raising `ValueError` on a starved hull instead of falling back (would
make a currently-buildable ship unbuildable — a regression FR-014 explicitly forbids); omitting the
branch (leaves `min()` on an empty sequence, an `IndexError` on a rule boundary).

---

## Part F: Does the adjustment disturb the power plant?

**Question**: `_select_drive_codes` filters power-plant candidates by
`rating >= max(jump_rating, maneuver_rating)`. Downgrading the jump drive after the draw could leave
that filter stale.

**Finding**: The constraint is a floor, and the adjustment only ever lowers the jump rating (FR-003:
never raises). `builder._build_power` enforces the same floor at build time. Lowering `jump_rating`
strictly relaxes `max(jump_rating, maneuver_rating)`, so a power plant legal before the adjustment
is legal after it. Under FR-004 the rating does not move at all, so nothing changes.

**Decision**: Leave `_select_drive_codes` untouched. Do not re-derive the power plant.

**Rationale**: FR-008 forbids consuming extra draws, and re-drawing the power plant would consume
one. It is also unnecessary: the resulting ship is rules-legal, merely carrying a power plant rated
above its jump drive — which the SRD permits and hand-authored designs already do.

**Alternatives considered**: Downgrading the power plant to match (changes a second component the
spec's Assumptions explicitly place out of scope, and would alter `power_fuel`, which feeds the
budget the drive search reads — a circular dependency).

---

## Part G: Re-establishing the feature-012 baseline guard

**Question**: `tests/test_ship_generator.py:139` pins 100 pre-feature designs from
`specs/012-ship-names/baseline/designs.json` to prove the ship-name draw lands last. This feature
moves 54% of those designs. How is the guard preserved?

**Finding**: The pinned file is a *proxy*. The invariant it defends (feature 012's FR-010a: the
`SHIP_NAME` draw is the final draw on every path) can be asserted directly, because `Rolls` is a
`Protocol` and every draw carries a `RollName`. A recording decorator over `RandomRolls` observes
the draw sequence for a seed; asserting the last recorded name is `RollName.SHIP_NAME` tests the
invariant itself, with no pinned data and no sensitivity to legitimate output changes.

**Decision**: A two-part replacement.

1. **Direct invariant test** — a `RecordingRolls` wrapper defined in `tests/`, asserting over a seed
   sweep on both the starship and small-craft paths that `SHIP_NAME` is the last `RollName` drawn
   and is drawn exactly once. This *strengthens* the guard: it catches a draw inserted after the
   name, which the old byte-comparison could also catch, and it names the offending roll.
2. **Re-pinned stability baseline** — regenerate the design dump at this feature's merge commit into
   `specs/013-fuel-limited-jump-drive/baseline/designs.json`, keeping the seed-to-ship
   byte-comparison as a regression anchor for *future* features. The 012 file stays in the repo as
   history; its test is retired and its docstring references updated.

**Rationale**: The spec's Assumptions section explicitly hands this decision to planning and states
the intent to preserve is "no extra draws before the name". Part 1 preserves that intent better than
the data ever did. Part 2 keeps a cheap, blunt regression net for the next feature without
pretending the old bytes still mean something.

The `RecordingRolls` wrapper lives in `tests/`, not in `rolls.py`: it serves no production caller,
and Constitution's simplicity posture ("no abstractions until a second concrete use case exists")
argues against adding a fourth `Rolls` adapter to the engine for one test.

**Alternatives considered**: Regenerating `012/baseline/designs.json` in place (destroys the record
that feature 012 was additive, and the 012 research explicitly says the file MUST NOT be
regenerated); masking jump-drive fields out of the TOML comparison (fragile, and the freed tonnage
propagates into cargo, fittings and turrets, so the mask would have to cover most of the design);
deleting the guard outright (loses the protection FR-008 depends on).

---

## Part H: SRD fidelity

**Question**: Does any of this deviate from the Cepheus Engine SRD?

**Finding**: No. The SRD prices jump fuel at 10% of hull tonnage per parsec jumped and tabulates
which drive letters are legal on which hulls; both are already transcribed in `tables.py` and are
read unchanged. The SRD does not prescribe *how a referee chooses* a drive for a random ship — that
is generator policy, not a rule.

**Decision**: No SRD deviation to record in the Constitution Check. The feature changes selection
policy inside `generator.py` and adds no rule, alters no table, and touches `builder.py` not at all.

**Rationale**: Constitution I makes the SRD the sole authority for *rules*. "Prefer the lightest
drive at a rating" is a design-agent preference, the same kind of judgement the generator already
makes when it picks a hull size or an armor fit.
