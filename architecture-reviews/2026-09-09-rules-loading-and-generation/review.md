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
refreshed: 2026-09-30 at 9027e90a46a592469a79f827234ffb4cc424a182
---

# Architecture review: rules loading and generation

Nine candidates, all of them deepening opportunities: places where a large
amount of behavior could sit behind a smaller interface than it does today.
Nothing here is a bug, and nothing here changes what the package produces —
`tests/golden/` and `tests/contract/` pin both output surfaces, so every
candidate is checkable as a structural change under Tidy First.

## Candidates

- [Give the field checks a parsing context](candidates/parse-context.md) -
  `Strong` - **specified** as `specs/007-parse-context-carrier/`, merged in
  PR #9.
- [Collapse the six kind-keyed tables into one](candidates/one-kind-registry.md) -
  `Strong` - adding a kind still means nine hand-kept edits across six
  structures in `rules.py`; 007's `parse_singleton` only makes one kind
  record easier to write.
- [Let each kind answer what makes it valid](candidates/validation-with-its-kind.md) -
  `Strong` - single-file checks still live in `rules.py`; `ParseContext`
  now makes moving them into their parsers cheap.
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
  `Speculative` - the 865-line `chargen.py` still holds six file schemas
  behind banner comments; the split pays only alongside validation-with-its-kind.
- [Close the CLI's reach past the library](candidates/cli-leaks.md) -
  `Worth exploring` - three private imports from `render`, and four
  validation rules restated with their message strings.

## Top recommendation

With the parsing context shipped, start with [One career throw behind five
copies](candidates/one-career-throw.md): `generator.py` is the package's
most-changed module, 007 left it untouched so the candidate holds exactly as
written, and it touches five sites in one module that the existing suite fully
pins. If you would rather build on 007's momentum, [Let each kind answer what
makes it valid](candidates/validation-with-its-kind.md) is the rules-side move
that `ParseContext` just made cheap.
