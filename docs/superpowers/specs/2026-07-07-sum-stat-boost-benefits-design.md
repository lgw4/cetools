# Sum stat-boost mustering-out benefits

## Problem

When `cetools character generate` displays mustering-out benefits, characteristic
increases are shown with repeat-count notation instead of being summed. For example:

```
+1 Edu, Mid Passage, +1 Soc x 2, Weapon x 2
```

Here `+1 Soc x 2` means the character rolled the `+1 Soc` benefit twice, so their
Social Standing went up by 2. The intended display is `+2 Soc`.

The character's stats are already correct: each `+1 Soc` roll is applied to the UPP
in the generator (`generator.py:215-218`, via `_apply_stat_boost`). The defect is
purely in how the benefit line is formatted.

## Root cause

Each mustering-out roll produces one `Benefit(kind="material", material_name=...)`,
including stat-boost rolls whose `material_name` is a string like `"+1 Soc"`. The
formatter's `_combine_material_benefits` (`src/cetools/formatter.py:10-28`) counts
duplicate material names and renders any name seen more than once as `name x N`.
That is correct for genuine items (two `Weapon` rolls really are `Weapon x 2`) but
wrong for stat boosts, which should be summed.

## Scope

Display-only change in `src/cetools/formatter.py`. No change to the generator, the
`Benefit` model, or how characteristics are applied — those are already correct.

## Design

In `_combine_material_benefits`, partition material benefits into two groups:

- **Stat boosts** — `material_name` begins with `"+1 "` (the same convention
  `_apply_stat_boost` uses at `generator.py:117-124`). Sum the counts for each label
  and render `+{count} {label}`, where `label` is the text after `"+1 "`
  (`Soc`, `Edu`, …). A boost seen once renders as `+1 Edu`.
- **Material items** — everything else. Unchanged behavior: singles listed first,
  then repeats rendered as `name x N`.

### Ordering

Stat boosts first (in first-appearance order), then material item singles (in
first-appearance order), then material item repeats (in first-appearance order).

For the example character, the benefit line becomes:

```
+1 Edu, +2 Soc, Mid Passage, Weapon x 2
```

### Edge cases

- A `+1 X` whose `X` is not a known stat abbreviation still counts as a boost and is
  summed by its literal label. This matches `_apply_stat_boost`, which returns `True`
  for any `"+1 "` prefix regardless of whether the stat is recognized.
- A boost rolled once renders as `+1 Edu` (count of 1), not `+1 Edu x 1`.

## Testing

Follow the project's TDD workflow. Add `tests/test_formatter.py` cases:

- Two `+1 Soc` benefits render as `+2 Soc`.
- A single `+1 Edu` benefit renders as `+1 Edu`.
- Three of the same boost render as `+3 <stat>`.
- Stat boosts and repeated material items coexist and appear in the specified order
  (e.g. `+1 Edu, +2 Soc, Mid Passage, Weapon x 2`).

Update any existing formatter test that currently asserts the `+1 Soc x 2` form.

Run `uv run black . && uv run flake8 src tests && uv run pytest` before finishing;
the suite enforces coverage.
