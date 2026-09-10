---
title: Give the field checks a parsing context
strength: Strong
status: open
files: [src/cetools/schema.py, src/cetools/careers.py, src/cetools/chargen.py, src/cetools/registries.py, src/cetools/names.py, src/cetools/rules.py, tests/unit/test_schema.py, tests/guards/test_no_duplicate_checks.py]
---

## Problem

`schema.py` is the shallowest module in the package: seven checks, 178 lines,
five or six parameters each, and every caller must re-supply `file`,
`location`, and a `problems` list it mutates in place.

## Solution

Move `(file, location, problems)` behind one small carrier the parsers
descend with, so a check reads `ctx.require_int("target", minimum=1)` and the
dotted location, the file name, and the problem list stop being arguments.

## Wins

- Interface shrinks from six parameters to two
- Dotted location becomes behavior, not idiom
- Out-parameter mutation stops being a contract
- `_HEADER_KEYS`, defined five times, collapses
- `unrecognized_key_problems` stops being the odd one

## Diagram

Mass diagram. Before: seven boxes, each drawn with a wide interface bar
(6 parameters) sitting on a thin implementation body (15-30 lines), plus a
sixtieth-repeat annotation showing `file` threaded through 53 function
signatures across five modules. After: one narrow context bar feeding a
stack of the same seven bodies, with the `(file, location, problems)` triple
drawn once, inside.

## Detail

`schema.py` was created six commits ago by `006-validation-vocabulary` and
passes the deletion test decisively: its own docstring records that "the five
parsers each hand-rolled these same seven checks"
(`src/cetools/schema.py:5-8`), and `tests/guards/test_no_duplicate_checks.py`
exists to stop them re-appearing. The module earns its keep. It is the
*shape* of its interface that did not get finished.

What a caller must know today, none of it in the signatures:

- `problems` is mutated in place by six of seven functions, but
  `unrecognized_key_problems` *returns* a list instead
  (`src/cetools/schema.py:166`). Both idioms appear four lines apart in the
  same function: `src/cetools/careers.py:224` extends, `careers.py:250`
  mutates.
- `require_dict` takes a *value* first, not `(container, key)`, and takes a
  caller-supplied `expected` string no sibling takes
  (`src/cetools/schema.py:132-134`).
- A `None` return means "a problem was appended", re-checked by hand at
  roughly sixty sites.
- `allowed` is annotated `frozenset[str]` (`schema.py:167`) but every caller
  passes a plain set (`registries.py:239`, `careers.py:223`,
  `chargen.py:434`).

The threading is the measurable part. `file: str` appears in **53 function
signatures** — `chargen.py` 20, `careers.py` 12, `registries.py` 7,
`schema.py` 7, `names.py` 4, `rules.py` 3 — and `file=file` is written at
essentially every `ValidationProblem` construction site. `location` is built
by f-string concatenation at every level of descent
(`f"{location}.{key}"` / `f"{location}[{index}]"` at `careers.py:311`, `319`,
`361`, `497`, `591`, `621`; `chargen.py:159`, `198`, `221`, `502`, `571`,
`851`, `1067`), so the dotted-path convention the spec names as an entity
exists only as a repeated idiom. `_HEADER_KEYS = frozenset({"schema",
"schema-version"})` is defined five times: `rules.py:63`, `careers.py:45`,
`chargen.py:28`, `registries.py:26`, `names.py:15`.

Three more idioms travel with the triple and would ride along:

- `found = type_name(raw) if not isinstance(raw, list) else "an empty array"`
  — 15 verbatim occurrences plus two hand-rolled variants
  (`registries.py:250-254`, `488-491`).
- the `ok = True` sentinel loop — 19 occurrences.
- `return None, tuple(problems)` — 18 occurrences.

Testability: `tests/unit/test_schema.py` currently calls each check with a
hand-built `problems: list[ValidationProblem] = []` out-parameter and asserts
exact `ValidationProblem` equality; its docstring admits the test is a
transcription of a contract document, so the vocabulary is pinned to prose
rather than to behavior. A context makes the natural test "parse this
fragment, get these problems" — which is what a caller actually does.

FR-020 of `006-validation-vocabulary` put the `(file, location)` carrier
explicitly out of scope, with the note that it is "easier to do later against
one shared module than now against five." That later is now.

## Constitution

Principle VI (Simplicity) rejects speculative abstraction. This is not
speculative: the abstraction is already present, spelled out 53 times as a
threaded parameter, and the deletion test says the complexity concentrates
rather than moves. Worth stating in the spec so the review has the argument.
