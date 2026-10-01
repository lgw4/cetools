---
title: Let each kind answer what makes it valid
strength: Strong
status: open
files: [src/cetools/rules.py, src/cetools/careers.py, src/cetools/chargen.py, src/cetools/registries.py, src/cetools/schema.py]
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
dotted line reaching down into the module that owns the data: `chargen.py`,
`registries.py`, `careers.py`. After: the slabs relocated into those modules,
and the `rules.py` band narrowed to composition plus the genuinely
cross-file arrows.

## Detail

The relocatable checks, each carrying a comment naming the `generator.py`
line that would crash without it:

| Check | Lives in | Reads |
|---|---|---|
| Mustering-out array lengths vs rank ladders | `rules.py:746-816` | careers + `ChargenParameters` |
| Characteristic band contiguity / unbounded top | `rules.py:909-950` | `CharacteristicRegistry` |
| Aging row ordering and overlap | `rules.py:952-982` | `AgingTable` |
| Characteristic-class references | `rules.py:985-1027` | characteristics + aging + mishaps |
| `throws.commission` requires a `commissioned` ladder | `rules.py:830-840` | one career file |
| Characteristics roll fits the pseudo-hex range | `rules.py:859-885` | `ChargenParameters` + `CharacteristicRegistry` |

The first, fourth, and sixth genuinely span files (the sixth compares
`chargen-parameters.toml`'s roll against the registry's pseudo-hex range).
The other three read a single file's contents and belong to that file's
parser.

Feature 007 moved none of these. It did lower the cost of moving them:
every parser now takes a `ParseContext` (`schema.py`), so a check relocated
into `parse_characteristics`, `parse_aging_table`, or `_parse_ladders`
reports through the same `ctx.at(...).report(...)` calls the parser
already uses, with no new plumbing.

Two traces show the cost.

**A rank ladder's rules are split four ways.** Positions distinct
(`careers.py:379-384`), positions contiguous (`:391-398`), sorted
(`:401`), exactly one `entry` ladder (`:472-478`), at most one
`commissioned` (`:480-486`), entry ladder has a rank 0 (`:488-497`); then
the commission pairing rule sits in `rules.py:830-840`, and
`careers.py:82-87` is a docstring whose job is to tell you so.

**Two positional range tables, two grammars, two validators.**
Characteristic bands parse in `registries.py:130-179` with regexes at `:21-22`
accepting `"N-M"` / `"N+"`, are consumed by `registries.py:55-61`, and are
validated in `rules.py:909-950`. Aging rows parse in `chargen.py:103-112`
and `:149-171` with *different* regexes at `:21-23` accepting `N`, `N-M`,
`N+` and negatives, are consumed by `generator._table_row`, and are
validated in `rules.py:952-982`. The comment at `rules.py:953-961` says out loud that this
is "the T180/T199 shape, for the one other positional range table in the
package." Same concept, three modules, nothing shared.

Two duplicated behaviors would collapse with the move:

- **Skill-resolution wording**, written twice character-for-character:
  `careers._skill_problem` (`careers.py:155-185`) and the inline block in
  `chargen._parse_skill_grant` (`chargen.py:479-497`). 007 converted both
  to report through `ParseContext` but left the duplication intact.
- **`_highest_matching_rank_row`**, written three times with byte-identical
  bodies: `generator.py:1350`, `rules.py:465` (whose docstring says
  "duplicated rather than imported, because this module validates before any
  `_Walk` exists"), and `tests/integration/test_data_driven.py:399`.

Testability: today a band-contiguity failure can only be provoked by
composing a whole override tree and calling `validate_rules`. With the check
in `parse_characteristics`, it is a two-line unit test against the parser
(`parse_characteristics(data, ParseContext("characteristics.toml"))`, then
read `ctx.problems`), which is the interface the existing tests already
reach for.

Two dead branches would also go. `rules.py:755` and `rules.py:869` both guard
`if parsed is not None` on rolls that already passed `require_roll`, which
rejects `d66`, the only input for which `parse_notation` returns `None`.
Those branches cannot be false and cannot be tested.

Refreshed against 9027e90 on 2026-09-30.
