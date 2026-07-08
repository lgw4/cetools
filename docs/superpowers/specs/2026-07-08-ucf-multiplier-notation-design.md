# UCF Repeated-Benefit Multiplier Notation

**Date:** 2026-07-08
**Status:** Approved

## Problem

The Universal Character Format (UCF) output renders repeated mustering-out
items with a spaced `x N` multiplier, e.g.:

```
+1 Edu, Low Passage, Mid Passage x 2
```

The [Cepheus SRD UCF specification][srd] writes repeated benefits with a
parenthesized, space-free multiplier, as in its example line `High passage
(x2)`. Our output should match:

```
+1 Edu, Low Passage, Mid Passage (x2)
```

[srd]: https://evolvedexperiment.github.io/cepheus-srd/character-creation.html#universal-character-format

## Change

Single production change in `src/cetools/formatter.py`, in
`_combine_material_benefits` (the final `return`, currently line 39):

```python
# before
return boosts + singles + [f"{name} x {item_counts[name]}" for name in repeats]
# after
return boosts + singles + [f"{name} (x{item_counts[name]})" for name in repeats]
```

## Scope and non-goals

- **Only** repeated material items (count ≥ 2) change notation.
- Stat boosts (`+2 Soc`) are unaffected — they are additive labels, not
  multipliers, and keep their `+N Label` form.
- Single-occurrence items are unaffected.
- Cash (the `Cr...` figure), the skills line, the name/UPP/age line, and the
  mishap line are untouched.

## Testing

Update the affected assertions in `tests/test_formatter.py` to expect the
`(xN)` form instead of `x N`:

- `test_material_benefits_sum_boosts_and_group_items`
- `test_boosts_and_items_full_example`
- `test_material_benefits_multiple_repeated_names_ordered_by_first_occurrence`
- any golden full-string assertion that includes a repeated item

Stat-boost tests such as `test_repeated_stat_boost_sums_into_single_entry`
(which asserts `+2 Soc`) are unaffected — boosts are not multipliers and keep
their `+N Label` form.

Then run the full quality gate: `uv run black . && uv run flake8 src tests &&
uv run pytest` (coverage must stay ≥ 85%).
