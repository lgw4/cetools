# Quickstart: NPC Generator

**Feature**: `003-npc-generator`

How to prove this feature works end to end. Every scenario below is a check a reviewer can
run by hand; the automated equivalents live in `tests/`. The file schemas are in
`contracts/data-files.md` and the rendering rules in `contracts/cli.md`, and neither is
repeated here.

## Prerequisites

- Python 3.13 or newer (`uv` will fetch one if needed)
- `uv` on `PATH`

## Setup

```sh
uv sync
uv run pytest
```

The full suite includes two sampled populations that take noticeably longer than the rest.
The inner loop skips them:

```sh
uv run pytest -m "not slow"
```

CI runs everything. Skipping them locally is a convenience, not a licence: SC-003 fixes the
sample at one thousand seeds with no seed excluded, and SC-019 at ten thousand names.

## Scenario 1: The grown data set still validates (User Story 4)

```sh
uv run cetools validate
```

Expected: exit 0 and

```text
Rules data is valid.
  Files: 26
  Rules: packaged (cetools 2026.8.1)
```

Twenty-six files, up from five: task parameters, three registries, six universal chargen
tables, eight name tables, and eight careers.

## Scenario 2: One seed, one usable NPC (SC-001, User Story 1)

```sh
uv run cetools npc --seed session-alpha
```

Expected: exit 0, a character sheet on standard output, and the seed and provenance on
standard error. The sheet's first line carries a name, a six-symbol characteristic profile,
and an age; its second a career with terms and the funds; its third the skills in
alphabetical order.

Run it twice and compare, which is the whole of SC-001:

```sh
diff (uv run cetools npc --seed session-alpha | psub) \
     (uv run cetools npc --seed session-alpha | psub)
```

Expected: no output. In `sh`, use `diff <(...) <(...)`.

The separators are tabs, which is worth seeing rather than trusting:

```sh
uv run cetools npc --seed session-alpha | cat -A | head -2
```

Expected: `^I` between the name and the profile, and between the profile and `Age`.

## Scenario 3: A redirected sheet is exactly a sheet (SC-011, FR-051)

```sh
uv run cetools npc --seed session-alpha > /tmp/ce-sheet.txt
```

Expected: the seed line, the version, and the provenance appeared on the terminal, and
`/tmp/ce-sheet.txt` contains none of them. Grep it to be sure:

```sh
grep -c -E 'Seed:|Rules:|cetools' /tmp/ce-sheet.txt
```

Expected: `0`. That file is a character sheet and nothing else, which is what FR-051 buys.

The same holds for a batch, whose redirected output is exactly its sheets with one blank
line between consecutive ones and no other text.

## Scenario 4: The history explains a surprising sheet (User Story 2)

```sh
uv run cetools npc --seed session-alpha --full
```

Expected: the same sheet, then a blank line, then the outstanding debt, the pension, and
the generation history. Every characteristic, skill, career, credit, and item on the sheet
above traces to a step in the history below.

Pick something surprising on a sheet and find the step that produced it. A forty-two year
old with one skill and an admiral with no Tactics are both possible; the history is how you
tell either from a broken engine. Try a few seeds until you find one.

The history's parts are separately addressable, not prose:

```sh
uv run cetools npc --seed session-alpha --json | \
  python -c 'import json,sys; [print(s["kind"], s["career"], s["term"], s["effects"]) for s in json.load(sys.stdin)["characters"][0]["history"]]'
```

Expected: one line per step with its named parts. That is what SC-004's consistency audit
and SC-005's traceability check read; neither parses a sentence.

## Scenario 5: A batch, and the prefix property (SC-002, User Story 3)

```sh
uv run cetools npc --seed table-of-twelve --count 12
```

Expected: twelve sheets, one blank line between consecutive ones, nothing else on standard
output.

The first characters of a larger batch equal a smaller batch from the same seed, so a count
is a request for more of one sequence rather than for a different sequence:

```sh
uv run cetools npc --seed table-of-twelve --count 12 > /tmp/ce-12.txt
uv run cetools npc --seed table-of-twelve --count 3  > /tmp/ce-3.txt
head -n (wc -l < /tmp/ce-3.txt) /tmp/ce-12.txt | diff - /tmp/ce-3.txt
```

Expected: no output.

And a batch of one is the single character of that seed, byte for byte:

```sh
diff (uv run cetools npc --seed table-of-twelve --count 1 | psub) \
     (uv run cetools npc --seed table-of-twelve | psub)
```

Expected: no output.

## Scenario 6: A quoted derived seed reproduces one person (SC-010, FR-050a)

Take the fifth character out of the table and regenerate that person alone:

```sh
uv run cetools npc --seed table-of-twelve --count 12 --json | \
  python -c 'import json,sys; print(json.load(sys.stdin)["characters"][4]["seed"])'
```

Feed the value back:

```sh
uv run cetools npc --seed <that value>
```

Expected: the fifth sheet of the batch, byte for byte. The seed at the top of the document
is the one a referee quotes for the whole table; the one on each character is the one that
regenerates that person, and both are in the output so neither has to be reconstructed.

## Scenario 7: One document shape, whatever the count (SC-010)

```sh
uv run cetools npc --seed session-alpha --json | python -c 'import json,sys; print(list(json.load(sys.stdin)))'
uv run cetools npc --seed session-alpha --count 12 --json | python -c 'import json,sys; print(list(json.load(sys.stdin)))'
```

Expected: `['kind', 'seed', 'provenance', 'characters']` both times. A run of one emits a
`characters` list of one, not a bare object, so a consumer writes one code path.

In machine-readable mode standard error is silent on a success, because the seed, the
version, and the provenance are in the document:

```sh
uv run cetools npc --seed session-alpha --json 2>/tmp/ce-err.txt > /dev/null
wc -c < /tmp/ce-err.txt
```

Expected: `0`.

## Scenario 8: Naming a character does not change who they are (SC-018, FR-047b)

```sh
uv run cetools npc --seed session-alpha --json > /tmp/ce-rolled.json
uv run cetools npc --seed session-alpha --name "Kestrel Vane" --json > /tmp/ce-named.json
diff /tmp/ce-rolled.json /tmp/ce-named.json
```

Expected: differences in `name`, `given_name`, `surname`, and `surname_region`, and in
nothing else. The characteristics, the skills, the careers, the age, the funds, the debt,
the pension, the benefits, and every step of the history are identical.

That is the property the name's separate seeded stream exists to give (research R3). The
natural implementation, rolling the name from the walk's own roller, fails this scenario and
passes every other one in this document.

## Scenario 9: Every seed produces a living character (SC-003, SC-004)

```sh
uv run pytest -m slow -k always_living
```

The sample is one thousand seeds with none excluded. Every one produces a character that is
alive, complete, and internally consistent: age matching the terms served and how each
ended, every rank on a ladder of a career actually joined, every skill traceable to a table
reachable in a term served, benefit rolls matching terms and rank, funds non-negative, and
no consequence that no history step produced.

By hand, a smaller version of the same thing:

```sh
for s in (seq 1 50)
  uv run cetools npc --seed $s > /dev/null; or echo "FAILED at $s"
end
```

Expected: no output. In `sh`, `for s in $(seq 1 50); do ...; done`.

## Scenario 10: House rules take effect with no code edit (SC-013, User Story 4)

FR-038 enumerates the constants that must live in data and SC-013 names five places a
change must be demonstrated through. Each is the same shape:

```sh
mkdir -p /tmp/ce-house
cp src/cetools/data/chargen/chargen-parameters.toml /tmp/ce-house/
```

Change `[terms] cap` from 7 to 3 in the copy, then:

```sh
uv run cetools npc --seed session-alpha --rules-data /tmp/ce-house --full
```

Expected: a character who served no more than three terms, a provenance block on standard
error naming `chargen-parameters.toml` as `replaced`, and no code edited. Repeat for a
Draft table row (`draft.toml`), an aging table entry (`aging.toml`), a Survival Mishaps
entry (`mishaps.toml`), and a career's medical tier (any career file).

Add a career that did not ship, by copying one and changing its `name`, and it can be
entered, reported as `added` in the provenance.

## Scenario 11: Inconsistent data fails before any character exists (User Story 4)

```sh
mkdir -p /tmp/ce-broken
cp src/cetools/data/chargen/draft.toml /tmp/ce-broken/
```

Change one entry in `careers` to a name no career declares, then:

```sh
uv run cetools npc --seed session-alpha --rules-data /tmp/ce-broken
```

Expected: exit 1, nothing on standard output, and a problem on standard error naming the
unresolvable career. Not a fallback to Drifter: a fallback here would be a rule in engine
code with no reason to exist once the data is complete (FR-005).

The same shape holds for a career naming a medical tier that does not exist, two surname
tables declaring one region, and a name table with no entries (FR-043h).

## Scenario 12: Usage errors name what was wrong (FR-053a, FR-054)

```sh
uv run cetools npc --seed 1 --count 0
uv run cetools npc --seed 1 --count 12 --name "Kestrel Vane"
```

Expected: exit 2 both times, nothing on standard output, and a message on standard error
naming `--count` in the first case and both `--count` and `--name` in the second. A name
names one character; applying it to twelve or to the first alone would each silently
discard part of what was asked for.

## Scenario 13: The same seed renders identically under another locale (SC-012)

```sh
env LC_ALL=tr_TR.UTF-8 uv run cetools npc --seed session-alpha > /tmp/ce-tr.txt
env LC_ALL=C uv run cetools npc --seed session-alpha > /tmp/ce-c.txt
diff /tmp/ce-tr.txt /tmp/ce-c.txt
```

Expected: no output. The skill ordering the format requires is `(casefold, codepoint)`, and
the guard that actually forbids the mistake is the one asserting nothing under `src/`
imports `locale`:

```sh
uv run pytest tests/guards -k locale
```

Running that is the check; the locale comparison above can only ever be best-effort, since
it depends on a locale being installed (research R8).

## Scenario 14: A task check still resolves exactly as it did (SC-014)

The characteristic modifier bands moved out of `tasks.toml` and into the characteristics
registry. Nothing about a check may change as a consequence:

```sh
diff (uv run cetools check --difficulty Difficult --characteristic 9 --skill 2 \
        --dm cover=-2 --seed session-alpha | psub) \
     tests/golden/check_difficult.txt
```

Expected: a difference only in the version substitution, if any. The committed check
goldens are the previous feature's evidence and are **not** regenerated in this feature;
regenerating them is how a changed number gets absorbed, which is what SC-014 exists to
prevent.

## Licensing

```sh
uv run pytest tests/guards/test_packaging.py tests/unit/test_licensing.py
```

This feature ships the first data files that are **not** Open Game Content. Every shipped
data file carries exactly one designation: the thirteen new OGC files carry the Open Game
Content line and are covered by the Section 15 game-data notice; the eight name tables carry
the GPL-3.0 line, carry no OGC designation, and are claimed by neither notice. A file
carrying both is a failure and a file carrying neither is a failure (SC-015).

Adding a data file under either designation without extending the corresponding check must
break the suite (SC-015a). Verify it by hand:

```sh
printf '# Open Game Content per OGL 1.0a; see LICENSE-OGL.txt\n' > tests/fixtures_ogc.toml
uv run pytest tests/unit/test_licensing.py
rm tests/fixtures_ogc.toml
```

Expected: a failure naming the uncovered file. Then the mirror, a GPL-designated file
inside a covered subtree:

```sh
printf '# GPL-3.0-only project content; not Open Game Content. See LICENSE.\n' \
  > src/cetools/data/chargen/probe.toml
uv run pytest tests/unit/test_licensing.py
rm src/cetools/data/chargen/probe.toml
```

Expected: a failure too. A check that passes unchanged when a file is added is a check that
will pass while a name table travels under a notice that does not cover it, or while a
career table travels under no notice at all.

Every name the generator can produce comes from a table recording where its entries were
drawn from, every entry in the indigenous-peoples table names the people it comes from, no
name table carries a gender field, and the shipped tables meet their size floors
(SC-015b):

```sh
uv run pytest tests/unit -k name_tables
```

## Names weight by region, not by table size (SC-019)

```sh
uv run pytest -m slow -k surname_region
```

Ten thousand characters, and each surname region appears within a narrow band of an equal
share. The shipped tables are deliberately of differing sizes, so a weighting mistakenly
taken over names rather than over regions fails this rather than passing by coincidence.
The check counts the `surname_region` each character records, never a region recovered by
splitting a rendered name.
