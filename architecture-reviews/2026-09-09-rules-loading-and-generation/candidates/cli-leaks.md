---
title: Close the CLI's reach past the library
strength: Worth exploring
status: open
files: [src/cetools/cli.py, src/cetools/render.py, src/cetools/generator.py, src/cetools/rules.py]
---

## Problem

The CLI imports three private names from `render`, restates four of the
generator's validation rules verbatim, reproduces three of `rules.py`'s error
messages, and formats one output line itself.

## Solution

Widen the library's interface at the four places the CLI already needs to
cross it, and delete the restatements.

## Wins

- No private imports across modules
- Message strings stop being kept in sync
- All rendering lives in `render.py`
- Principle I holds in spirit, not just letter

## Diagram

Hand-built boxes-and-arrows. Before: a `cli.py` box with four arrows leaving
it — three landing on private members *inside* `render.py`'s boundary
(`_RULES_LABEL_WIDTH`, `_problem_line`, `_provenance_lines`), and one leading
to a small duplicate box drawn beside `generator.py` holding copies of its
name and count rules. After: four arrows landing on `render.py`'s and
`generator.py`'s outer boundary; the duplicate box gone.

## Detail

No *game* logic leaked — no dice, tables, rules constants, or character-shape
knowledge — so Principle I's literal wording holds. Four smaller things did.

**Private imports.** `src/cetools/cli.py:11-17` pulls `_RULES_LABEL_WIDTH`,
`_problem_line`, and `_provenance_lines` from `render`. `_problem_line`'s
docstring (`render.py:88-91`) names this as a deliberate cross-module seam,
which is a reasonable argument for three of the CLI's five `render` imports
being public rather than for them being private.

**Duplicated validation.** `cli.py:194-205` restates four rules with the same
message strings as `generator._validate_name` (`generator.py:1606-1609`) and
`generate_batch`'s guards (`:1673-1676`): non-empty name, no tab or newline,
`count >= 1`, and name-with-count-above-1. The contract at
`specs/003-npc-generator/contracts/library-api.md:92-93` sanctions turning
these into usage errors "rather than restating the rule" — but the code does
restate the rule, and the strings agree only by hand.

Separately, `cli._check_override_location` (`cli.py:39-51`) reproduces the
three usage errors of `rules._compose` (`rules.py:413-430`), message strings
included: `"override location is empty"`, `"override location does not
exist: …"`, `"override location is neither a file nor a directory: …"`. This
one exists because `load_rules` and `validate_rules` split their error modes
differently — `load_rules` raises for both a bad location and bad content,
`validate_rules` raises for the first and returns a report for the second —
a split visible in neither signature.

**Formatting in the CLI.** `cli.py:222` is the only place the `npc` command's
`Seed:` line exists:

```python
typer.echo(f"{'Seed:'.ljust(_RULES_LABEL_WIDTH)}{batch.seed}", err=True)
```

a label-padding decision living outside `render.py`, and the sole reason
`_RULES_LABEL_WIDTH` is imported.

**An unused helper.** `_report_cetools_error` is defined at `cli.py:54-59` and
used by `npc` (`:211`, `:227`), but `check` inlines the identical four lines
at `cli.py:138-142`.

One piece of friction worth noting because it belongs to another candidate:
`npc` needs two separate `try/except CetoolsError` blocks (`cli.py:207-212`,
`:218-228`) because rendering can raise after generation succeeded, with a
five-line comment explaining why (`:213-217`). That is the
`characteristic_symbols` workaround surfacing in the caller — see
[One rendering per result type](one-rendering-per-type.md).

Deletion test on the restatements: delete the CLI copies and the rules do not
reappear anywhere, because the library already enforces them. That makes them
pass-throughs, not depth. The interesting question for grilling is what the
CLI needs in exchange — a way to render a library error as a usage error with
a `param_hint`.
