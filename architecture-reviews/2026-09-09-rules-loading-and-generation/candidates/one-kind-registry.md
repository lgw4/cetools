---
title: Collapse the six kind-keyed tables into one
strength: Strong
status: open
files: [src/cetools/rules.py, src/cetools/__init__.py, tests/unit/test_rules.py]
---

## Problem

Adding one data-file kind means editing nine places in `rules.py` and two in
`__init__.py`, because six parallel structures are keyed by the same kind
strings (thirteen in `_SUPPORTED_VERSION`, eleven in the singleton tables)
and kept in agreement by hand.

## Solution

Declare each kind once, as a record naming its canonical file, its supported
schema version, its parser, its arity, and its `RulesData` field; drive
discovery, version-gating, parsing, and composition off that one table.

## Wins

- One edit per new kind, not eleven
- Parallel tables cannot drift apart
- Deletes a test that exists to pin tables
- Kind vocabulary becomes readable in one place

## Diagram

Hand-built boxes-and-arrows. Before: one column of thirteen kind strings on
the left, six boxes to its right (`_SUPPORTED_VERSION`, `_SINGLETON_KINDS`,
`_CANONICAL_FILE`, the `parse_singleton` call list, the `RulesData` field
list, the final `None`-check block), each with its own arrows back to the
column: a dense fan. After: one `Kind` record box per kind, and four thin
arrows out of the single table into discovery, version gate, parse, and
compose.

## Detail

For a single kind, `draft-table`, the sites are: type import
`src/cetools/rules.py:26`, parser import `:32`, `_SUPPORTED_VERSION` `:64`,
`_SINGLETON_KINDS` `:78`, `_CANONICAL_FILE` `:91`, the `RulesData` field
`:111`, the `parse_singleton` call `:645`, the final `None`-check `:1040`,
and the constructor argument `:1058`; plus `src/cetools/__init__.py:18-31`
and `:120`.

Feature 007 changed the shape of one of the six without removing it. The
`_SINGLETON_PARSERS` table was dissolved during the `ParseContext`
migration, and commit `92263bd` then single-sourced the eleven resulting
blocks into a nested `parse_singleton` helper (`rules.py:618-633`) called
once per kind (`:635-650`, `:660-662`). Every singleton parser now has the
uniform signature `(data, ctx, *extra) -> value | None`, which makes a kind record
easier to write than it was at review time, but the call list is still one
more hand-kept enumeration of the kinds, and its order is load-bearing for
problem insertion order (the helper's docstring says so).

The cost is already visible as a test. `tests/unit/test_rules.py:605-623`
reaches past the interface into `rules_module._discover_packaged()` and
`rules_module._packaged_kind_map(...)` purely to assert that `_CANONICAL_FILE`
and `_SINGLETON_KINDS` agree, ending with
`assert len(rules_module._SINGLETON_KINDS) == 11`. Its docstring says as much.
That test is not testing behavior; it is a hand-built consistency check
standing in for a structure the code does not have. Similarly
`tests/unit/test_rules.py:324` and `:342` reach in with
`monkeypatch.setitem(rules_module._SUPPORTED_VERSION, "benefits", 2)` to fake
a schema bump, and `:824` iterates `_SUPPORTED_VERSION.values()` directly.

Two kinds still do not fit the tables and are handled as hard-coded special
cases: `background-skills` is the one singleton parser needing a registry,
so its `parse_singleton` call is pulled out of the list and placed after
the empty-registry substitutes (`rules.py:655-662`), and the surname tables
are many-per-kind rather than singleton, parsed in their own loop like
careers. A kind record makes both ordinary fields rather than exceptions.

A related seam sits underneath: `_singleton_slots` (`rules.py:438-462`) draws
from two sources, and its docstring records that a *third* was removable "one
at a time with the suite green"; redundant sources here are undetectable by
test. Each source needed a bespoke monkeypatched test to isolate
(`tests/unit/test_rules.py:502-534`, `:536-561`).

Deletion test: the tables do not vanish, they fuse. Complexity concentrates
in one record type, and eleven edit sites become one.

Refreshed against 9027e90 on 2026-09-30.
