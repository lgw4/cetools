# Quickstart: Validated Rules Data Loading

**Feature**: `002-rules-data-loading`

How to prove this feature works end to end. Every scenario below is a check a
reviewer can run by hand; the automated equivalents live in `tests/`. Details of the
file schemas are in `contracts/data-files.md` and are not repeated here.

## Prerequisites

- Python 3.13 or newer (`uv` will fetch one if needed)
- `uv` on `PATH`

## Setup

```sh
uv sync
uv run pytest
```

## Scenario 1: The shipped data set validates (SC-001, User Story 1)

```sh
uv run cetools validate
```

Expected: exit 0 and

```text
Rules data is valid.
  Files: 5
  Rules: packaged
```

Machine-readable, same outcome:

```sh
uv run cetools validate --json
echo "exit: $status"        # fish; use $? in sh
```

Expected: `"valid": true`, an empty `problems` array, and exit 0.

## Scenario 2: A corrupted file is rejected, with everything located (SC-002)

```sh
mkdir -p /tmp/ce-broken
cp src/cetools/data/careers/navy.toml /tmp/ce-broken/
```

Edit the copy to introduce four distinct problems at once: misspell one skill name in
`tables.service.entries`, misspell one key (`[mustering-out] chash = ...`), write a
target as a string, and give a specialty for a skill that has none. Then:

```sh
uv run cetools validate /tmp/ce-broken/navy.toml
```

Expected: exit 1, and **all four** problems in that single run, each naming the file
and its location within it (SC-003). One run is always enough.

Check each remaining category the same way, one at a time: an unsupported
`schema-version` (expect a version-mismatch problem and no other problem from that
file), a required element removed (expect a problem naming what is missing, SC-004),
and a file that is not well-formed TOML at all (expect one problem naming the file
and the parse position).

## Scenario 3: An override replaces one file and nothing else (SC-005, SC-006)

```sh
mkdir -p /tmp/ce-house
cp src/cetools/data/careers/navy.toml /tmp/ce-house/
```

Change one survival target in the copy, and delete one optional element that the
packaged file has. Then:

```sh
uv run cetools validate /tmp/ce-house
```

Expected: exit 0, and the provenance block reports `navy.toml` as `replaced` with a
fingerprint. Programmatically:

```python
from cetools import load_rules
rules = load_rules("/tmp/ce-house")
rules.careers["navy"].throws["survival"].target   # the override's value
rules.task_parameters.target                      # still the packaged value
rules.provenance.files                            # one entry, disposition REPLACED
```

The element deleted from the override file is absent from the loaded career, not
inherited from the shipped one (SC-006).

## Scenario 4: A misspelled override filename is visible (SC-005)

```sh
cp src/cetools/data/careers/navy.toml /tmp/ce-house/navvy.toml
uv run cetools validate /tmp/ce-house
```

Expected: exit 1. `navvy.toml` is an **addition**, not a replacement, so the data set
now holds two careers declaring the name `Navy`, and the report names both files
(FR-019b). Change the declared `name` inside `navvy.toml` and rerun: exit 0, with
`navvy.toml` reported as `added` and `navy.toml` still packaged.

## Scenario 5: Provenance describes content, not location (SC-008)

```sh
mkdir -p /tmp/ce-elsewhere
cp /tmp/ce-house/navy.toml /tmp/ce-elsewhere/
uv run cetools check --seed 1 --rules-data /tmp/ce-house --json     | grep fingerprint
uv run cetools check --seed 1 --rules-data /tmp/ce-elsewhere --json | grep fingerprint
```

Expected: identical fingerprints from two different locations. Change one byte in one
copy and rerun: the fingerprints differ. The reported value is reproducible outside
the tool:

```sh
shasum -a 256 /tmp/ce-house/navy.toml
```

## Scenario 6: Provenance rides with the seed, always (FR-037)

```sh
uv run cetools check --seed 1
uv run cetools check --seed 1 --json
```

Expected: `Rules: packaged` under the seed in text, and
`"provenance": {"source": "packaged", "files": []}` in JSON. The line is present for
a packaged load, so a reader never infers it from an absence.

## Scenario 7: Nothing changed about how a check resolves (SC-009, FR-045)

```sh
uv run cetools check --difficulty Difficult --characteristic 9 --skill 2 \
    --dm cover=-2 --seed session-alpha
diff <(uv run cetools check --difficulty Difficult --characteristic 9 --skill 2 \
    --dm cover=-2 --seed session-alpha) tests/golden/pre-loader/check_difficult.txt
```

Expected: the only difference is the added `Rules:` line. The dice, every modifier and
its label, the total, the target, the outcome, and the seed are identical. The `roll`
goldens differ not at all:

```sh
diff <(uv run cetools roll 2d6+1 --seed session-alpha) tests/golden/pre-loader/roll_2d6_plus1.txt
```

## Scenario 8: House rules take effect with no code edit (SC-011)

For each of a career throw, a skill table entry, a rank bonus, and a registry entry:
copy the packaged file, change the value, load with `--rules-data`, and observe the
change reflected in what loads. A registry edit is the sharpest case, because
removing a skill name from the registry must make every career file that uses it
fail (FR-013), which proves the registry is what gives names meaning.

## Scenario 9: No hidden location is consulted (SC-007)

```sh
uv run pytest tests/guards/test_no_outside_reads.py
```

The guard arms an audit hook, loads the packaged data set, and asserts every file the
interpreter opened lies inside the installed package. Running it is the check;
inspection is not.

## Licensing

```sh
uv run pytest tests/guards/test_packaging.py tests/unit/test_licensing.py
```

Every data file this feature adds must carry its Open Game Content designation and
neither Product Identity string, checked against the built wheel and sdist rather
than the working tree (SC-014). The Section 15 game-data copyright line must cover
the new files, not just `tasks.toml`.
