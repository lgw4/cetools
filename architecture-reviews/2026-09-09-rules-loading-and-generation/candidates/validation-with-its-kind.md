---
title: Let each kind answer what makes it valid
strength: Strong
status: open
files: [src/cetools/rules.py, src/cetools/careers.py, src/cetools/chargen.py, src/cetools/registries.py]
---

## Problem

Roughly 300 lines of `rules.py` are checks about other modules' data
structures, so "what makes an aging table valid" is answered in two modules
and "what makes a rank ladder valid" in four.

## Solution

Move every check that reads one file's own contents into that file's parser,
and leave `rules.py` holding only what it alone can see: composition,
version-gating, and cross-file references.

## Wins

- One module answers one kind's rules
- `parse_*` becomes the seam tests already want
- Comments pointing at `generator.py` become local
- Two range-table parsers can merge

## Diagram

Cross-section. Before: a horizontal band for `rules.py` drawn wide, with five
labelled slabs inside it (`mustering-out length`, `band contiguity`, `aging
row order`, `class-effect references`, `commission ladder`), each with a
dotted line reaching down into the module that owns the data — `chargen.py`,
`registries.py`, `careers.py`. After: the slabs relocated into those modules,
and the `rules.py` band narrowed to composition plus the genuinely
cross-file arrows.

## Detail

The relocatable checks, each carrying a comment naming the `generator.py`
line that would crash without it:

| Check | Lives in | Reads |
|---|---|---|
| Mustering-out array lengths vs rank ladders | `rules.py:799-846` | careers + `ChargenParameters` |
| Characteristic band contiguity / unbounded top | `rules.py:939-980` | `CharacteristicRegistry` |
| Aging row ordering and overlap | `rules.py:982-1013` | `AgingTable` |
| Characteristic-class references | `rules.py:1015-1056` | characteristics + aging + mishaps |
| `throws.commission` requires a `commissioned` ladder | `rules.py:860-870` | one career file |
| Pseudo-hex symbol table covers the score range | `rules.py:889-916` | `CharacteristicRegistry` |

Only the first and the fourth genuinely span files. The rest read a single
file's contents and belong to that file's parser.

Two traces show the cost.

**A rank ladder's rules are split four ways.** Positions distinct
(`careers.py:502-512`), positions contiguous (`:519-531`), sorted
(`:533`), exactly one `entry` ladder (`:643-652`), at most one
`commissioned` (`:655-665`), entry ladder has a rank 0 (`:670-680`) — then
the commission pairing rule sits in `rules.py:860-870`, and
`careers.py:91-97` is a docstring whose job is to tell you so.

**Two positional range tables, two grammars, two validators.**
Characteristic bands parse in `registries.py:137-204` with regexes at `:28-29`
accepting `"N-M"` / `"N+"`, are consumed by `registries.py:62-68`, and are
validated in `rules.py:939-980`. Aging rows parse in `chargen.py:134-143`
with *different* regexes at `:30-32` accepting `N`, `N-M`, `N+` and
negatives, are consumed by `generator._table_row`, and are validated in
`rules.py:982-1013`. The comment at `rules.py:984-991` says out loud that this
is "the T180/T199 shape, for the one other positional range table in the
package." Same concept, three modules, nothing shared.

Two duplicated behaviors would collapse with the move:

- **Skill-resolution wording**, written twice character-for-character:
  `careers._skill_problem` (`careers.py:176-207`) and the inline block in
  `chargen._parse_skill_grant` (`chargen.py:669-686`).
- **`_highest_matching_rank_row`**, written three times with byte-identical
  bodies: `generator.py:1350`, `rules.py:508` (whose docstring says
  "duplicated rather than imported, because this module validates before any
  `_Walk` exists"), and `tests/integration/test_data_driven.py:399`.

Testability: today a band-contiguity failure can only be provoked by
composing a whole override tree and calling `validate_rules`. With the check
in `parse_characteristics`, it is a two-line unit test against the parser —
which is the interface the existing tests already reach for.

Two dead branches would also go. `rules.py:785` and `rules.py:899` both guard
`if parsed is not None` on rolls that already passed `require_roll`, which
rejects `d66` — the only input for which `parse_notation` returns `None`.
Those branches cannot be false and cannot be tested.
