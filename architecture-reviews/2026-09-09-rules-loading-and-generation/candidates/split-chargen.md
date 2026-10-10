---
title: Split chargen.py into the six schemas it holds
strength: Speculative
status: open
files: [src/cetools/chargen.py, src/cetools/rules.py, src/cetools/schema.py]
---

## Problem

`chargen.py` is 865 lines holding six unrelated file schemas that share
nothing but their imports, with banner comments already marking the seams.

## Solution

Move each schema into its own module, so the boundary the comments describe
becomes the boundary the import graph enforces.

## Wins

- Six modules, six kinds, one map
- Banner comments become module docstrings
- Smaller unit of reading per kind
- No behavior crosses the new lines

## Diagram

Cross-section. Before: one tall `chargen.py` slab with five horizontal rules
drawn across it at the banner-comment lines, the sections labelled draft,
aging, mishaps, background skills, medical tiers, and chargen parameters, and
one thin shared thread (`HEADER_KEYS` and `ParseContext`, imported from
`schema.py`) running the full height. After: six separate slabs, each
importing that thread directly.

## Detail

The banners are at `chargen.py:29`, `:69`, `:217`, `:446`, `:537`, `:658`,
marking: draft (`:29-66`), aging (`:69-214`), mishaps (`:217-443`),
background skills (`:446-534`), medical tiers (`:537-655`), chargen
parameters (`:658-865`). Nothing defined in the module crosses them: the
module-level regexes at `:21-26` each serve one section (`_RANGE_*` aging,
`_AMOUNT_*` mishaps), and the shared names come in as imports (`:15-19`).
The one real thread at review time, a local `_HEADER_KEYS` defined five
times package-wide, was single-sourced by feature 007 as
`schema.HEADER_KEYS` alongside `ParseContext`
([Give the field checks a parsing context](parse-context.md)). The file
shrank from 1164 to 865 lines in the same feature, all of it from folding
location and problem-list threading into `ParseContext`; the six-way
structure is unchanged.

This is listed as speculative because the split alone changes no interface:
`rules.py` imports six parsers today and would import six parsers after. It
buys reading locality and nothing else, which is why it is worth doing *with*
[Let each kind answer what makes it valid](validation-with-its-kind.md)
rather than on its own: once each parser also owns its file's rules, the
modules stop being arbitrary slices and become the kinds.

Two observations for whoever grills it:

**`ChargenParameters` is a 36-field flat record** (`chargen.py:740-780`),
every field public, and its field names are generated from `_CHARGEN_GROUPS`
(`:667-717`) by `_chargen_attribute` (`:724-725`) doing
`replace('-', '_')`, then handed to `ChargenParameters(**values)` at `:865`.
The comment at `:663-665` claims a misspelling in that table is "an
`AttributeError` at import". It is not: the coupling runs through the
`**values` call, so a misspelling is a `TypeError` at first parse, and
nothing tests the correspondence directly. `_Walk` reads all 36 fields.

**The table-driven shape exists exactly once.** `_CHARGEN_GROUPS` plus the
dispatch loop at `:828-837` replaces what its own comment calls "forty
near-identical `_require_*` call sites", for one file kind. The other twelve
kinds in the package are hand-written. Whether that table generalizes is a
better question than whether the file should be six files.

Refreshed against 9027e90 on 2026-09-30.
