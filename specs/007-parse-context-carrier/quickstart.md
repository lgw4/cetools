# Quickstart: validating the Parse Context Carrier

How to run and verify each user story. Nothing here is implementation; the
design is in [contracts/parse-context.md](contracts/parse-context.md) and the
site inventory in [data-model.md](data-model.md).

## Prerequisites

```sh
uv sync
```

The suite is the regression net for this whole feature, and it must be green at
**every** commit in the sequence:

```sh
.venv/bin/python -m pytest
```

The long-running property tests are the only ones that may be deferred between
steps within a commit; they run before the commit lands.

## User Story 1 — the reports do not move (P1)

Two checks, in order of strength.

### 1a. The corpora, unedited

```sh
.venv/bin/python -m pytest tests/golden tests/contract tests/integration
```

These were written before this feature existed. FR-016 forbids editing them to
accommodate it: a failure here is a signal to stop, not to adjust a fixture.
Confirm they are untouched before claiming the story:

```sh
git diff --stat main -- tests/golden tests/contract
```

Empty output is the pass condition.

### 1b. The mutation harness

The suite alone is not proof — it names a fraction of the distinct `expected`
strings the source emits, and the phrasings it never names are concentrated in
exactly the conversions this feature makes riskiest (006 learned this; research
R10). The harness closes that gap by deriving its inputs from the data files
rather than from what anyone thought to test.

Write it once, in the scratchpad, **not** in the repo:

```python
# mutate.py — every shipped .toml, broken every way, every problem printed
import copy, sys, tomllib, tempfile
from pathlib import Path
import tomli_w  # or hand-write TOML; any serializer that round-trips is fine
from cetools.rules import validate_rules

DATA = Path("src/cetools/data")

def paths(obj, prefix=()):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield prefix + (k,), v
            yield from paths(v, prefix + (k,))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield prefix + (i,), v
            yield from paths(v, prefix + (i,))

def mutants(doc):
    for path, value in paths(doc):
        for kind, new in (("delete", None), ("retype", 0 if not isinstance(value, int) else "x"),
                          ("empty", [] if isinstance(value, list) else {} if isinstance(value, dict) else "")):
            m = copy.deepcopy(doc)
            parent = m
            for part in path[:-1]:
                parent = parent[part]
            if kind == "delete":
                del parent[path[-1]]
            else:
                parent[path[-1]] = new
            yield path, kind, m

for toml_path in sorted(DATA.rglob("*.toml")):
    doc = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    for path, kind, mutant in mutants(doc):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / toml_path.name
            out.write_text(tomli_w.dumps(mutant), encoding="utf-8")
            for p in sorted(validate_rules(Path(tmp)).problems):
                print(f"{toml_path.name}|{'.'.join(map(str, path))}|{kind}|"
                      f"{p.file}|{p.location}|{p.found}|{p.expected}")
```

An override directory holding one file composes over the packaged tree, so one
mutant file per run is enough. `tomli_w` is not a project dependency and must
not become one; run the harness with `uv run --with tomli-w python mutate.py`,
which keeps it out of the environment the package declares.

Use it like this:

```sh
git switch main
.venv/bin/python mutate.py > /tmp/before.txt
git switch 007-parse-context-carrier   # or the commit under test
.venv/bin/python mutate.py > /tmp/after.txt
diff /tmp/before.txt /tmp/after.txt && echo "no report moved"
```

**An empty diff is the pass condition for every commit in the sequence.** The
full sweep takes a few minutes; per-commit, restrict the outer loop to the
files the converted module parses (`careers/*.toml` for `careers.py`,
`registries/*.toml` for `registries.py`, and so on) and run the full sweep
before the first commit and after the last.

### 1c. The two named scenarios

Story 1's scenarios 2 and 3 are already covered by the suite and are worth
naming so a reviewer can point at them:

```sh
.venv/bin/python -m pytest tests/integration/test_validation_categories.py -k "cycle or duplicate"
```

The cycle scenario proves the cross-reference gate still skips on an unrelated
bad field (FR-017); the duplicate-career scenario proves the pair-of-files
problem still names one file in `file` and both in `found`, which is the shape
the carrier deliberately cannot describe (FR-012).

## User Story 2 — a contributor stops threading context (P2)

The story's own independent test, on a scratch branch that is thrown away:

1. Add a checked field to one data-file kind — say `[pension] maximum-terms`
   to `chargen-parameters`.
2. Inspect the diff:

```sh
git diff | grep -nE '\bfile\b|f"\{location\}|problems\.(append|extend)|_HEADER_KEYS'
```

Empty output is the pass condition: no file name, no location built by string
concatenation, no choice of how problems travel, no local header-key constant.

The same grep run against today's tree, for the same field, is the before
picture.

## User Story 3 — a reviewer reads the migration one parser at a time (P3)

```sh
git log --oneline main..HEAD
```

Expect the shape below (exact granularity is `/speckit-tasks`' call):

| Commit | Content | Suite |
|---|---|---|
| 1 | `ParseContext` + `HEADER_KEYS` + `require_list`, checks delegating to the free functions; guards rewritten with the temporary tolerance | green |
| 2 | `names.py` converted | green |
| 3 | `rules.parse_task_parameters` + `_class_effect_problems` + the loader's carrier construction | green |
| 4 | `registries.py` converted | green |
| 5 | `careers.py` converted | green |
| 6 | `chargen.py` converted | green |
| 7 | free functions deleted, bodies moved into the class, both guards tightened | green |

Then, for each:

```sh
git switch --detach <commit> && .venv/bin/python -m pytest
```

Every one passes. Each diff changes structure only — this feature has no
behavioral commit at all (FR-018), which is why there is no `CHANGELOG.md`
entry: nothing a library user or a data-file author can see has changed.

Confirm the final commit really finished the job:

```sh
.venv/bin/python -m pytest tests/guards/test_no_duplicate_checks.py tests/guards/test_parsing_layer_shape.py
rg -n "def (require_|optional_bool|unrecognized)" src/cetools/schema.py
```

The second command must show eight definitions, all indented inside
`ParseContext`.

## User Story 4 — wording problems are written down, not fixed (P3)

```sh
cat specs/007-parse-context-carrier/inventory.md
git diff main --stat -- src/cetools/
```

Every inventory entry names a concrete site; none has been acted on. The
entries seeded during planning are I-1 through I-6; the migration adds more as
it reads.

## The guards can fail

FR-023's obligation, and the reason a guard is worth having:

```sh
.venv/bin/python -m pytest tests/guards/ -k "can_fail"
```

Each self-test plants the shape its guard forbids — a second `require_int`
outside `ParseContext`, a second `HEADER_KEYS`, a function taking `file`, a
`list[ValidationProblem]` parameter, a stray `"an empty array"` literal — and
confirms the detector rejects it, then removes it.
