# Quickstart: validating the Vehicle Design System

**Feature**: `001-vehicle-design` | **Date**: 2026-08-07

Runnable checks that prove the feature works end to end, one per user story plus the gate. Each
names the requirement it validates. Implementation details are in [plan.md](./plan.md),
[data-model.md](./data-model.md) and [contracts/](./contracts/); the task list is
`/speckit-tasks`'s job.

## Prerequisites

```shell
uv sync
uv run pre-commit install --hook-type pre-push   # once per clone
```

## User Story 1—build a vehicle from a design file

```shell
uv run cetools vehicle build tests/data/vehicles/example.toml
```

**Expect**: one Universal Vehicle Description Format paragraph on stdout, nothing else, exit 0.

Then the failure paths, each of which must print nothing to stdout and exit 1:

```shell
uv run cetools vehicle build over-tech-level.toml   # names the component, its TL and the vehicle's
uv run cetools vehicle build no-tech-level.toml     # says tech level is required
uv run cetools vehicle build submersible.toml       # names watercraft as the missing capability
uv run cetools vehicle build overfull.toml          # identifies the spaces overage
```

**Validates**: FR-004, FR-011, FR-012, FR-013, FR-014, FR-025, SC-004, SC-005, SC-007.

Then the component table, which is how a referee sees where a price came from:

```shell
uv run cetools vehicle build tests/data/vehicles/example.toml --table
```

**Expect**: the same paragraph unchanged, then every component with its spaces and price, then the
summed price, the discount, the design fee where one is charged, the final price and the build time.
The lines sum to the printed price. Flip `standard_design` in the design file and re-run: the price,
the fee and the build time all move together, because the SRD makes that one election (FR-007,
FR-008).

**Validates**: FR-007, FR-025a, User Story 1 acceptance scenario 7.

## User Story 2—re-derive the published catalog

```shell
uv run cetools vehicle catalog
uv run cetools vehicle build --catalog air-raft
uv run cetools vehicle build --catalog stagecoach
```

**Expect**: fifteen names listed; each build succeeds and prints a description. The Air/Raft's price
is none of the book's three figures—not the Cr104,614.5 table total, not the Cr94,160 footnote, not
the KCr94.340 prose—and it is deliberately not written down here either: it is Cr104,614.5 × 0.9
only if the Air/Raft carried no fuel, and it carries fuel, which FR-007 exempts from the discount.
The figure follows from the design once authored, and every published price that differs from it is
recorded on `DIVERGENCES.md`. The Stagecoach builds with no propulsion at all and with a
negative-price component reducing its total.

```shell
uv run pytest tests/test_vehicle_catalog.py --no-cov
```

**Expect**: all fifteen build; every transcribed published figure either matches or is named on
`DIVERGENCES.md` with the same published and produced values. A figure that diverges without being
documented fails here.

**Validates**: FR-017 through FR-023, FR-024a, SC-001, SC-002, and the edge cases for animal power,
non-powered propulsion and negative prices.

## User Story 3—generate a vehicle from a seed

```shell
uv run cetools vehicle generate --seed 42
uv run cetools vehicle generate --seed 42 | diff - <(uv run cetools vehicle generate --seed 42)
uv run cetools vehicle generate --seed 42 --tech-level 12 --locomotion grav
uv run cetools vehicle generate --seed 42 --tech-level 5 --locomotion grav
```

**Expect**: a complete legal vehicle identified by tech level and type, with fittings that suit the
role it was generated for. The `diff` is empty. The grav constraint at TL12 is honored. The grav
constraint at TL5 cannot be, so the conflict is reported on **stderr** and the exit code stays 0.

```shell
uv run cetools vehicle generate --seed 42 --locomotion nonsense   # exits 1, alias names no row
```

**Validates**: FR-026, FR-026a, FR-026b, FR-026c, FR-030, FR-031, FR-032, SC-003, SC-011.

## User Story 4—round-trip a design as TOML

```shell
uv run cetools vehicle generate --seed 42 --toml --out /tmp/generated.toml
uv run cetools vehicle build /tmp/generated.toml
uv run cetools vehicle generate --seed 42 --out /tmp/nope.toml   # exits 1: --out requires --toml
```

**Expect**: the emitted file rebuilds to the same description the generate run would have printed.
The last command fails with the existing message.

**Validates**: FR-028, SC-008.

## The quality gate

```shell
uv run isort . && uv run black . && uv run flake8 src tests && uv run pytest && uv run python scripts/check_docs.py
```

**Expect**: all five green. Coverage of `src/cetools` at or above 85%, treated as a floor rather
than as evidence. The docs check now reads `DIVERGENCES.md` as a fourth maintained document, which
means every backticked identifier in it resolves in the package, its dashes are tight, and every
divergence it records still matches what the builder produces.

To see the last of those fail on purpose, change one figure in a `DIVERGENCES.md` row and run the
check again. It should name the vehicle and the figure.

**Validates**: FR-020, FR-020a, SC-006, SC-009, SC-010.

## Mutation check

Coverage near 100% has hidden real defects in this repo before, so before calling a table done:
alter a value in a `tables.py` row that no catalog vehicle and no generation path exercises, and
confirm a test fails. If none does, SC-006 is not met yet for that row. The unexercised rows are
listed in `tests/data/vehicles/unexercised_rows.json`, so this check reads a file rather than a
guess. Restore the altered row from a copy, never with `git checkout`.

The option families deserve the same treatment and are easy to overlook, being prose in the source:
change Streamlined's speed multiplier from 5 to 4 and confirm `tests/test_vehicle_tables.py` fails,
then change Reinforced Hull's `max_selections` from 2 to 3 and confirm `tests/test_vehicle_builder.py`
fails. Both are transcribed from sentences rather than from cells, which is exactly where a
transcription error is hardest to see (FR-003a).
