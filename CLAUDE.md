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
- Tidy First: structural and behavioral changes never share a commit,
  structural goes first, and the commit message says which it is.

## Gotchas

- Changing human-readable CLI output means updating `tests/golden/` in the
  same commit; changing `--json` output breaks `tests/contract/`.
- New result types must be added to both `as_text` and `as_dict`/`as_json`
  in `src/cetools/render.py`.
- Every user-visible change adds a `CHANGELOG.md` entry in the same
  commit. Commits follow Conventional Commits with a scope: `feat(dice): …`.
