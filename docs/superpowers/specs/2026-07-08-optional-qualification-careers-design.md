# Optional Qualification for Careers (Batch 0)

**Date:** 2026-07-08
**Status:** Approved, ready for implementation planning

## Context: the 18-career effort

The six SRD draft-table careers (Aerospace System Defense, Marine, Maritime
System Defense, Navy, Scout, Surface System Defense) are complete. The SRD
lists 18 further careers to add:

Agent, Athlete, Barbarian, Belter, Bureaucrat, Colonist, Diplomat, Drifter,
Entertainer, Hunter, Mercenary, Merchant, Noble, Physician, Pirate, Rogue,
Scientist, Technician.

Full per-career data (qualification, survival, commission, advancement,
re-enlistment, the four skill tables, ranks, cash and material benefits) is
present on the SRD character-creation page, so no data-sourcing gap exists.

### Decomposition roadmap

The work is broken into one foundational engine change followed by four
themed career batches. Each batch is its own spec → plan → PR cycle and
updates the README supported-careers list.

- **Batch 0 — Optional qualification (this spec):** the only non-data work.
- **Batch 1 — Social (Soc-based):** Agent, Bureaucrat, Diplomat, Entertainer,
  Noble.
- **Batch 2 — Frontier/survival:** Athlete, Barbarian, Colonist, Hunter,
  Drifter (first real consumer of optional qualification).
- **Batch 3 — Rogue & spacer:** Belter, Mercenary, Pirate, Rogue, Merchant.
- **Batch 4 — Learned professions (Edu-based):** Physician, Scientist,
  Technician.

Everything the career batches need beyond Batch 0 is already supported by the
data-driven engine: careers without commission/advancement (the Scout
`None` pattern), careers with a single rank-0 title ("no ranks"), and
variable-length benefit tables.

## Batch 0 goal

Let a `Career` declare "no qualification requirement" so always-open careers
fit the data model, the same way `commission` and `advancement` already
express "not applicable" via `None`. The immediate motivation is Drifter,
which per the SRD has **no qualification** and is always open when
qualification for another career fails.

## Design

### 1. Model (`src/cetools/engine/careers/base.py`)

- Change the field types:
  - `qualification_stat: str` → `str | None`
  - `qualification_target: int` → `int | None`
- In `__post_init__`, move `qualification_stat` out of the mandatory-stat
  validation loop (which currently rejects anything not a valid stat) into
  the optional group alongside `commission_stat` and `advancement_stat`, so
  its stat name is validated only when it is not `None`.
- Add a consistency guard: `qualification_stat` and `qualification_target`
  must be **both `None` or both set**. A half-specified pairing raises
  `ValueError`. This mirrors the implicit commission/advancement pairing and
  prevents malformed career data.

### 2. Generator (`src/cetools/engine/generator.py`)

- `generate_character` (the qualification check around line 251): change the
  guard to
  `if not bypass_qualification and career.qualification_stat is not None:`
  so a `None`-qualification career auto-passes enlistment instead of calling
  `_check` with `None` arguments.
- `roll_until_qualified`: if `career.qualification_stat is None`, return the
  first characteristics roll immediately (no reroll loop) instead of indexing
  `characteristics[None]`. This is the path the user-facing
  `generate_career_character` (`--career <name>`) takes.

### 3. Not touched

- CLI: the `--career` option and valid-career list are registry-derived, so
  no change is needed.
- Formatter: unaffected.
- Draft table: Drifter is not draftable, so `draft_character` is unchanged.
- All existing careers keep concrete qualification values; their behavior is
  unchanged.

### 4. Testing

- **Model** (`tests/test_careers.py` or the base-model test): a
  `None`-qualification `Career` constructs successfully; a half-specified
  career (`stat=None, target=5`, and the reverse) raises `ValueError`.
- **Generator** (`tests/test_generator.py`): using a synthetic
  no-qualification `Career` fixture (not registered),
  `generate_character(..., bypass_qualification=False)` still produces a
  `Character`, and `roll_until_qualified` returns without looping. A
  regression check confirms an existing career with concrete qualification
  still gates enlistment as before.
- The first real consumer, Drifter, is validated in Batch 2. Batch 0 proves
  the capability with a synthetic fixture so the thematic batches stay clean.

## Out of scope

- Any of the 18 career data files (they belong to Batches 1–4).
- Changes to commission/advancement, mustering out, aging, or the draft
  table.
- README supported-careers updates (no new career ships in Batch 0).
