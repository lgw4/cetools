# Quickstart: validating Complete SRD Careers

Runnable checks that the feature does what the spec asks. Every command runs from the repository
root. Nothing here is a substitute for the suite; these are the scenarios a human runs to see
the thing work.

## Prerequisites

```sh
uv sync
uv run pytest -q          # the whole suite; 1253 tests were green at the branch point
```

Use `uv run pytest`, not `.venv/bin/python -m pytest`: the latter hides collection failures.

## SC-001: every one of the twenty-four careers is in force and traversable

```sh
uv run python -c "
from cetools.rules import load_rules
careers = load_rules().careers
print(len(careers))
for stem, c in sorted(careers.items()):
    print(f'{stem:26} {c.name}')
"
```

Expect 24 lines and the twenty-four names of [research.md](./research.md) R1, including the
three long planetary-defense names.

Traversal is proved per career by the integration suite rather than by hand, because a walk has
to be steered into a chosen career:

```sh
uv run pytest tests/integration -k traversal -q
```

Expect 24 passing cases, one per career, each qualifying in, serving a term, and mustering out
with cash and material benefits drawn from that career's own tables (FR-026, FR-027).

## SC-002: validation is clean, and each invariant rejects a violating file

```sh
uv run cetools validate
```

Expect `Rules data is valid.`, `Files: 42`, and exit status 0.

The three rejections, each against a scratch override rather than the packaged data:

```sh
mkdir -p /tmp/houserule

# 1. an unresolvable skill name (FR-018)
sed 's/"Comms"/"Coms"/' src/cetools/data/careers/navy.toml > /tmp/houserule/navy.toml
uv run cetools validate /tmp/houserule

# 2. a rank ladder with a gap (FR-019)
sed '/rank = 2, title = "Lieutenant"/d' src/cetools/data/careers/navy.toml > /tmp/houserule/navy.toml
uv run cetools validate /tmp/houserule

# 3. a mustering-out table too short for the rows its ranks can reach (FR-020)
sed 's/^cash = \[1000, 5000, 10000, 10000, 20000, 50000, 50000\]/cash = [1000, 5000, 10000, 10000, 20000, 50000]/' \
    src/cetools/data/careers/navy.toml > /tmp/houserule/navy.toml
uv run cetools validate /tmp/houserule
```

Each exits non-zero and names the file, the location, what was found, and what was expected. The
third names `mustering-out.cash`, the six rows found, and the seven rows required. Add `--json`
to any of them to see the same report as a machine-readable document.

Case 3 is the point of the feature's fourth story: an override author learns their table is
short when they validate, not partway through a batch when a benefit roll finds no row.

## SC-004: both vocabularies match the source in both directions

```sh
uv run python -c "
from cetools.rules import load_rules
r = load_rules()
print(len(r.skills.skills), 'skills')
print(len(r.benefits.items), 'benefit items')
print(sorted(r.benefits.items))
"
```

Expect 70 skills and 8 benefit items, the sets research R4 and R5 enumerate. The two-directional
comparison against the source is a test (`tests/unit`), not a command: the source-side set is
committed as the expected value there, and the re-read artifacts are what tie that set back to
the printed pages.

Every shipped file that references those vocabularies must still resolve against them, which is
what `cetools validate` above already proves. The background-skills table is the one that would
otherwise have stopped resolving (FR-014a), and its repeated rows are load-bearing:

```sh
uv run python -c "
import collections, tomllib, pathlib
d = tomllib.loads(pathlib.Path('src/cetools/data/chargen/background-skills.toml').read_text())
for key in ('law-level', 'trade-code', 'education'):
    rows = d[key]
    print(f'{key:11} {len(rows):2} rows', dict(collections.Counter(rows).most_common(3)))
"
```

Expect 4, 14, and 15 rows, and repeats in the first two: `Gun Combat 0` three times in
`law-level`, and `Animals 0` and `Zero-G 0` three times each in `trade-code`. The homeworld draw
is uniform over those rows, so a deduplicated list is a silently reweighted one (research R8).

## SC-005: no invented rank title, no padded row

```sh
uv run python -c "
from cetools.rules import load_rules
for stem, c in sorted(load_rules().careers.items()):
    untitled = [r.rank for l in c.ladders for r in l.ranks if not r.title]
    print(f'{stem:26} cash={len(c.mustering_out.cash)} material={len(c.mustering_out.benefits)} untitled={untitled}')
"
```

Expect `cash=7` for all twenty-four; `material=6` for `athlete`, `barbarian`, `belter`,
`drifter`, `entertainer`, `hunter`, and `scout`, and `material=7` for the other seventeen; and a
non-empty `untitled` list for those same seven careers and no others.

## Story 2: an untitled rank renders as no title, in both renderings

```sh
uv run cetools npc --seed drifter-sheet --json | python -m json.tool | grep -n '"title"'
```

The `title` field is present and holds `""` for a character whose only rank is untitled; it is
neither removed nor null (FR-009). The human-readable sheet for the same seed shows the name
with no title in front of it and no dangling separator:

```sh
uv run cetools npc --seed drifter-sheet
```

## Story 2: a ship-share award records the rolled quantity

```sh
uv run cetools npc --seed shares --count 20 | grep 'Ship Share'
```

A sheet that drew the ship-share row shows `Ship Share (x3)` (or whatever the seed rolled), the
existing repeat display doing the work. The same character's `--json` `benefits` array holds
that many identical `"Ship Share"` strings and carries no quantity field.

## Story 2: a nested cascade resolves through to a terminal skill

```sh
uv run cetools npc --seed cascade --count 20 --full | grep -E 'Aircraft|Watercraft'
```

Every recorded skill naming `Aircraft` or `Watercraft` carries a specialty: `Aircraft (Grav
Vehicle)`, `Watercraft (Ocean Ships)`, and so on. A bare `Vehicle (Aircraft)` never appears on a
sheet, because resolution continues until it reaches a name a rule gives a level to (FR-012).

## SC-006 and SC-007: the pool grew, and the pinned outputs moved exactly twice

```sh
git log --oneline --stat -- README.md tests/golden/
```

Expect exactly two commits touching the pinned outputs, one file each: the structural re-pin of
`tests/golden/npc_*.txt`, which changes no engine behavior, and one regeneration of `README.md`
after every content change landed — including the corrections Phase 7's re-read found, which is
why the regeneration is the last behavioral step. `cetools validate`'s `Files:` line moves from 26
to 42 in the second.

The two do not overlap: the `npc_*.txt` goldens are rendered from hand-built `Character` literals
in `tests/unit/test_render_character.py`, not from a generation walk, so career content never
moves them. `README.md`'s pinned `npc` block is generated, so it does.

```sh
uv run cetools npc --seed table-of-twelve --count 12 | grep -E '^\S.*\(' | cut -f1
```

Expect careers outside the previously shipped eight to appear (FR-028, SC-007).

## SC-003: the re-read is complete and inspectable

```sh
ls specs/004-complete-srd-careers/verification/
```

Expect twenty-seven files: twenty-four career artifacts, `index.md`, `roster.md` (the roster-level
verification of FR-023b), and `background-skills.md` (FR-014a). Open any one and confirm it
enumerates the source's printed values first and the committed file's values against them, field
by field, with a verdict per field, and that every discrepancy it raised is either fixed in the
data file or recorded there with its reason (FR-023, FR-023a, FR-024).

## SC-008: the release notes flag the break

```sh
sed -n '/^### Breaking changes/,/^###/p' CHANGELOG.md | head -60
```

Expect an entry covering the enlarged pool changing what every seed produces with no
compatibility path, the two schema bumps, the corrected Scout and Drifter data, the three
renamed composition keys, and the note that the previous pool can be reproduced only by shipping
it as an override.
