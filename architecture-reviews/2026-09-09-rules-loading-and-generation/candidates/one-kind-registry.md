---
title: Collapse the six kind-keyed tables into one
strength: Strong
status: open
files: [src/cetools/rules.py, src/cetools/__init__.py, tests/unit/test_rules.py]
---

## Problem

Adding one data-file kind means editing nine places in `rules.py` and two in
`__init__.py`, because six parallel tables are keyed by the same thirteen
strings and kept in agreement by hand.

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
`_CANONICAL_FILE`, `_SINGLETON_PARSERS`, the `RulesData` field list, the
final `None`-check block), each with its own thirteen arrows back to the
column — a dense fan. After: one `Kind` record box per kind, and four thin
arrows out of the single table into discovery, version gate, parse, and
compose.

## Detail

For a single kind, `draft-table`, the sites are: type import
`src/cetools/rules.py:26`, parser import `:32`, `_SUPPORTED_VERSION` `:71`,
`_SINGLETON_KINDS` `:85`, `_CANONICAL_FILE` `:98`, `_SINGLETON_PARSERS`
`:228`, the `RulesData` field `:118`, the local unpack `:675`, the final
`None`-check `:1069`, and the constructor argument `:1087` — plus
`src/cetools/__init__.py:18-31` and `:120`.

The cost is already visible as a test. `tests/unit/test_rules.py:595-613`
reaches past the interface into `rules_module._discover_packaged()` and
`rules_module._packaged_kind_map(...)` purely to assert that `_CANONICAL_FILE`
and `_SINGLETON_KINDS` agree, ending with
`assert len(rules_module._SINGLETON_KINDS) == 11`. Its docstring says as much.
That test is not testing behavior; it is a hand-built consistency check
standing in for a structure the code does not have. Similarly
`tests/unit/test_rules.py:314` and `:332` reach in with
`monkeypatch.setitem(rules_module._SUPPORTED_VERSION, "benefits", 2)` to fake
a schema bump, and `:814` iterates `_SUPPORTED_VERSION.values()` directly.

Two kinds already do not fit the tables and are handled as hard-coded special
cases: `background-skills` is the one parser needing a registry, spelled out
at `rules.py:219-222` and `rules.py:689-695`, and the surname tables are
many-per-kind rather than singleton. A kind record makes both ordinary
fields rather than exceptions.

A related seam sits underneath: `_singleton_slots` (`rules.py:501-505`) draws
from two sources, and its docstring records that a *third* was removable "one
at a time with the suite green" — redundant sources here are undetectable by
test. Each source needed a bespoke monkeypatched test to isolate
(`tests/unit/test_rules.py:492-524`, `:526-551`).

Deletion test: the tables do not vanish, they fuse. Complexity concentrates
in one record type, and eleven edit sites become one.
