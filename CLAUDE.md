# cetools

Seeded dice and 2D6 task-check engine (library + `cetools` CLI), developed
with Spec Kit. `.specify/memory/constitution.md` governs all work and
supersedes everything else, including this file; CONTRIBUTING.md explains
the full workflow. Non-trivial changes go through the `/speckit-*` arc,
with artifacts in `specs/<NNN>-<slug>/`.

## Non-negotiables

- Test-first, strictly: write the test, watch it fail, then implement.
  One test at a time, and run the whole suite (minus long-running tests)
  after each step.
- All randomness flows from a seeded `Roller`. Never call `random`, read
  the clock, or let output depend on anything the seed does not determine.
- Rules content lives in `.toml` files under `src/cetools/data/`, at any
  depth, never hard-coded in engine code. New SRD-derived data files are
  Open Game Content: OGC header comment, under the directory the README
  licensing section and the Section 15 game-data notice both designate, and
  never containing the strings "Cepheus Engine" or "Samardan Press".
  Everything else is GPL-3.0. See CONTRIBUTING.md before adding any file.

## Tidy First approach

- Separate all changes into two distinct types:
    1. Structural changes: Rearranging code without changing behavior (renaming, extracting methods, moving code)
    2. Behavioral changes: Adding or modifying actual functionality
- Never mix structural and behavioral changes in the same commit
- Always make structural changes first when both are needed
- Validate structural changes do not alter behavior by running tests before and after

## Commit discipline

- Only commit when:
    1. ALL tests are passing
    2. ALL compiler/linter warnings have been resolved
    3. The change represents a single logical unit of work
    4. Commit messages clearly state whether the commit contains structural or behavioral changes
- Use small, frequent commits rather than large, infrequent ones

## Gotchas

- Changing human-readable CLI output means updating `tests/golden/` in the
  same commit; changing `--json` output breaks `tests/contract/`.
- New result types must be added to both `as_text` and `as_dict`/`as_json`
  in `src/cetools/render.py`.
- Every user-visible change adds a `CHANGELOG.md` entry in the same
  commit. Commits follow Conventional Commits with a scope: `feat(dice): …`.
