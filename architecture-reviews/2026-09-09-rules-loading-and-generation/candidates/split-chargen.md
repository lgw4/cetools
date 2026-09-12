---
title: Split chargen.py into the six schemas it holds
strength: Speculative
status: open
files: [src/cetools/chargen.py, src/cetools/rules.py]
---

## Problem

`chargen.py` is 1164 lines holding six unrelated file schemas that share
nothing but two imports, with banner comments already marking the seams.

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
two thin shared threads (`_HEADER_KEYS`, the `schema.py` imports) running the
full height. After: six separate slabs, and the two threads redrawn as
imports.

## Detail

The banners are at `chargen.py:38`, `:100`, `:321`, `:632`, `:749`, `:934`,
marking: draft (`:38-97`), aging (`:100-318`), mishaps (`:321-629`),
background skills (`:632-746`), medical tiers (`:749-931`), chargen
parameters (`:934-1164`). The only things crossing them are
`_HEADER_KEYS` (`:28`) — itself defined five times package-wide, see
[Give the field checks a parsing context](parse-context.md) — and the shared
`schema.py` imports.

This is listed as speculative because the split alone changes no interface:
`rules.py` imports six parsers today and would import six parsers after. It
buys reading locality and nothing else, which is why it is worth doing *with*
[Let each kind answer what makes it valid](validation-with-its-kind.md)
rather than on its own — once each parser also owns its file's rules, the
modules stop being arbitrary slices and become the kinds.

Two observations for whoever grills it:

**`ChargenParameters` is a 36-field flat record** (`chargen.py:1021-1056`),
every field public, and its field names are generated from `_CHARGEN_GROUPS`
(`:943-993`) by `_chargen_attribute` (`:1000-1001`) doing
`replace('-', '_')`, then handed to `ChargenParameters(**values)` at `:1164`.
The comment at `:940-942` claims a misspelling in that table is "an
`AttributeError` at import". It is not — the coupling runs through the
`**values` call, so a misspelling is a `TypeError` at first parse, and
nothing tests the correspondence directly. `_Walk` reads 34 of the 36 fields.

**The table-driven shape exists exactly once.** `_CHARGEN_GROUPS` plus the
dispatch loop at `:1117-1129` replaces what its own comment calls "forty
near-identical `_require_*` call sites" — for one file kind. The other twelve
kinds in the package are hand-written. Whether that table generalizes is a
better question than whether the file should be six files.
