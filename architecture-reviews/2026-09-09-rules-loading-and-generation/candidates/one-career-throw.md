---
title: One career throw behind five copies
strength: Strong
status: open
files: [src/cetools/generator.py, tests/unit/test_generator.py]
---

## Problem

The same thirty-line "roll a career check and record it" block is written
five times in `generator.py`, distinguished only by hand-mangled local names
like `faces_c`, `faces_p`, `faces_r`.

## Solution

One method that takes a `Throw` plus any extra modifiers, performs the roll,
appends the `HistoryStep`, and returns the outcome; the five sites become
five calls.

## Wins

- Five copies become one implementation
- Modifier assembly stops being re-derived
- `HistoryStep` labeling settles in one place
- Shrinks the 297-line term loop materially

## Diagram

Call-graph collapse. Before: five stacked lanes — qualification, survival,
commission, promotion, re-enlistment — each running the identical six-step
sequence (`_dice` → `_roll_modifier` → `characteristic_dm` → append
`Modifier` → sum and compare → append `HistoryStep`), with only the
`career.throws[...]` key and one optional extra modifier differing. After:
one `attempt(throw, extra)` box with five arrows into it and one arrow out
carrying the outcome.

## Detail

The five sites:

| Throw | Span | Key | Extra |
|---|---|---|---|
| qualification | `generator.py:479-510` | `throws["qualification"]` | previous-careers penalty (`:489-491`) |
| survival | `:678-707` | `throws["survival"]` | natural-failure clamp (`:690`) |
| commission | `:782-810` | `throws["commission"]` | — |
| promotion | `:829-857` | `throws["promotion"]` | — |
| re-enlistment | `:905-932` | `throws["re-enlistment"]` | — |

Each independently runs `_dice(self.roller, throw.dice)`, then
`_roll_modifier(...)`, then `self.characteristic_dm(throw.characteristic)`,
appends `Modifier(f"Characteristic {…}", char_dm)`, sums faces and modifier
values, compares against `throw.target`, and appends a `HistoryStep`. Because
three of them share a scope, the locals are disambiguated by suffix:
`faces_c/roll_mod_c/mods_c/total_c/success_c` at `:783-794`,
`faces_p/…_p` at `:830-841`, `faces_r/…_r` at `:906-916`, `faces_k` at `:882`.
That suffixing is the tell — the five blocks are one function that never got
named.

`self.history.append(HistoryStep(...))` occurs **31 times** across the file
and is its single most common statement. The five throw sites account for the
most regular of those; consolidating them puts the step's label, modifiers,
and success flag in one place instead of five, which is also where the
`--json` contract and the golden text both read from.

Deletion test: delete the proposed method and the same six-step sequence
reappears five times. It concentrates.

Risk is low and the work is purely structural under Tidy First. Every one of
the five outcomes is already pinned end-to-end — `tests/unit/test_generator.py`
sweeps 2000 seeds in several places and asserts `found` on each branch — so
the suite can be run green before and after with no behavioral commit.

This is also the smallest of the generator candidates and makes
[Name the term loop's carried state](service-record.md) easier: once each
throw is one call, `run_term_loop`'s remaining structure is visible.
