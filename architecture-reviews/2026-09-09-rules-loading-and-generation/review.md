---
date: 2026-09-09
commit: c8324b7506cd3c9ef0219d146e8b537c96f7b800
scope: >
  The rules-loading stack (schema, registries, careers, chargen, names,
  rules) and the generation/rendering stack (generator, character, render,
  cli). Chosen because the last three features — 004-complete-srd-careers,
  005-release-publishing, 006-validation-vocabulary — landed almost entirely
  in rules.py, careers.py, chargen.py, registries.py and generator.py, which
  are also the five largest modules in the package.
feature: specs/006-validation-vocabulary/
---

# Architecture review: rules loading and generation

Nine candidates, all of them deepening opportunities: places where a large
amount of behavior could sit behind a smaller interface than it does today.
Nothing here is a bug, and nothing here changes what the package produces —
`tests/golden/` and `tests/contract/` pin both output surfaces, so every
candidate is checkable as a structural change under Tidy First.

## Candidates

- [Give the field checks a parsing context](candidates/parse-context.md) -
  `Strong` - `file` is threaded through 53 signatures and `location` is
  rebuilt by f-string at every level of descent.
- [Collapse the six kind-keyed tables into one](candidates/one-kind-registry.md) -
  `Strong` - adding one data-file kind means eleven hand-kept edits, and a
  test exists purely to pin two of the six tables against each other.
- [Let each kind answer what makes it valid](candidates/validation-with-its-kind.md) -
  `Strong` - ~300 lines of `rules.py` are checks about other modules' data,
  so a rank ladder's rules are split four ways.
- [One career throw behind five copies](candidates/one-career-throw.md) -
  `Strong` - the same thirty-line roll-and-record block is written five
  times, distinguished only by suffixed local names.
- [Name the term loop's carried state](candidates/service-record.md) -
  `Strong` - a 297-line loop hands eight locals back as an unannotated
  seven-tuple, and `(career_name, term)` threads nine signatures.
- [Put the walk's seam where the tests cross it](candidates/walk-seam.md) -
  `Worth exploring` - `_Walk` says it is not public; four test modules
  import it fifty-nine times.
- [One rendering per result type](candidates/one-rendering-per-type.md) -
  `Worth exploring` - two independent dispatch registries whose parity is
  documented in `CLAUDE.md` and checked nowhere.
- [Split chargen.py into the six schemas it holds](candidates/split-chargen.md) -
  `Speculative` - the banner comments already mark the seams; the split
  alone changes no interface.
- [Close the CLI's reach past the library](candidates/cli-leaks.md) -
  `Worth exploring` - three private imports from `render`, and four
  validation rules restated with their message strings.

## Top recommendation

Start with [Give the field checks a parsing
context](candidates/parse-context.md): it is the direct successor to
`006-validation-vocabulary`, which shipped six commits ago and deliberately
left the `(file, location)` carrier out of scope on the grounds that it would
be "easier to do later against one shared module than now against five" — and
`tests/guards/test_no_duplicate_checks.py` is already in place to keep the
result honest. If you would rather take a smaller first bite, [One career
throw behind five copies](candidates/one-career-throw.md) touches five sites
in one module and is fully pinned by the existing suite.
