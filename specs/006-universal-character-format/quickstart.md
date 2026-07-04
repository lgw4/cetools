# Quickstart: Validating Universal Character Format Output

## Prerequisites

```bash
uv sync
```

## Scenario 1 — generated output is exactly the UCF line set (US1, SC-001)

```bash
uv run cetools character generate --career navy
```

**Expected**: stdout is 3 or 4 lines (4th only if the character has any material benefit), with no
`UPP:`, `Characteristics:`, `Mustering-Out Benefits:`, or `Retirement Pension:` headers, and no
`(Drafted)` marker anywhere. See `contracts/ucf-output.md` for the exact grammar and worked
examples.

## Scenario 2 — every character has a name (US2, SC-002)

```bash
for i in 1 2 3; do uv run cetools character generate --career scout; echo ---; done
```

**Expected**: each run's first line starts with `<Rank> <FirstName> <LastName>` (two or more
words before the UPP field), and different runs may repeat a name — that's acceptable
(spec Edge Cases).

## Scenario 3 — funds and equipment folded into the summary (US3)

```bash
uv run cetools character generate --career navy
```

**Expected**: line 2 ends with a single `Cr<amount>` figure (comma-thousands, e.g. `Cr70,000`,
or `Cr0` if the character mustered out with no cash benefits) — never a cash/material breakdown.
If the character has any material mustering-out benefit, a 4th line lists each by name,
comma-separated; if not, there is no 4th line at all.

## Scenario 4 — draft path produces the same shape (Edge Cases)

```bash
uv run cetools character generate
```

**Expected**: same UCF shape as Scenarios 1–3, with no drafted annotation, even though the
character was drafted rather than chosen by `--career`.

## Regression check (SC-004)

```bash
uv run pytest
```

**Expected**: full suite green, ≥85% coverage on `src/cetools`. Existing characteristic-roll,
qualification/survival/commission/advancement, and skill/benefit-table tests must be unaffected
by this feature (only name-related and display-format tests should differ from before this
feature).
