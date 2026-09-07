# Quickstart: Validation Vocabulary

How to run this feature's checks and see for yourself that it did what it
claims. Every command below runs from the repository root.

This feature is internal: nothing about the CLI's interface changes, and the
only user-visible difference is two validation messages. So "does it work" is
answered by the test suite and by four direct observations, not by a new
command.

## Prerequisites

```sh
uv sync
```

Python 3.13 or newer, per `pyproject.toml`'s `requires-python`.

## The inner loop

```sh
uv run pytest -m "not slow"
```

`slow` is registered in `pyproject.toml` and marks tests that exercise a large
sampled population. Run the whole suite before any commit:

```sh
uv run pytest
```

Per the constitution's Principle III, each step is Red first: write the test,
watch it fail, then implement. `uv run pytest tests/unit/test_schema.py` on its
own is the fastest way to watch the vocabulary's own tests fail before
`src/cetools/schema.py` exists.

## Scenario 1: the two wording changes (User Story 1)

Runs against the behavioral commit alone, before any extraction.

Build a chargen file whose `terms.term-years` is below its minimum, and one
whose required `name` is absent, then validate:

```sh
mkdir -p /tmp/cetools-check
# start from the packaged file, then break the one field
uv run python - <<'PY'
import pathlib, shutil
import cetools
src = pathlib.Path(cetools.__file__).parent / "data"
dst = pathlib.Path("/tmp/cetools-check")
shutil.copytree(src, dst, dirs_exist_ok=True)
PY
```

Edit `/tmp/cetools-check/chargen.toml` so `term-years = 0`, then:

```sh
uv run cetools validate /tmp/cetools-check --json
```

**Expected**: the problem for `terms.term-years` carries
`"expected": "a positive integer"`, not `"an integer >= 1"`.

Now remove a required text field—say a career file's `name` key—and
validate again.

**Expected**: the problem carries `"expected": "a non-empty string"`, not
`"a string"`.

**Also expected, and the point of FR-010a**: remove `roll` from `[task]` in
`tasks.toml` and the problem for `task.roll` still carries
`"expected": "a string"`. That field wants dice notation, not a name, and it
is deliberately not swept into the unification.

The full list of what may and may not change is in
[`data-model.md`](data-model.md), *Inventory: behavioral blast radius*.

## Scenario 2: the vocabulary itself (User Story 2)

```sh
uv run pytest tests/unit/test_schema.py -v
```

**Expected**: roughly 25-30 cases, covering each of the seven checks across its
absent-key, wrong-type, empty-string, `minimum` boundary, and accepted paths,
plus `unrecognized_key_problems`' sort order and its `expected` list.

The exact strings each case asserts are the tables in
[`contracts/schema-vocabulary.md`](contracts/schema-vocabulary.md). Those tables
are the contract; the tests are their transcription.

This scenario passes before any parser module has been touched. That is what
makes it an independent test of Story 2.

## Scenario 3: the extraction changed nothing (User Story 3)

The whole existing suite is the regression net:

```sh
uv run pytest
```

**Expected**: everything passes, with no test edited except the wording
assertions added in Scenario 1's commit. In particular the forty-three tests in
`tests/integration/test_validation_categories.py` pass untouched—they are the
broadest statement of what the validator says about broken data, and they are
the reason the extraction can be trusted.

**This next step is required, not optional** (FR-013a). The suite names nine of
the sixty-three distinct expected phrasings the source emits, so it cannot
report a message it never mentions. Capture the validator's full output before
and after each structural change and diff it:

```sh
git stash                       # or check out the pre-extraction commit
uv run cetools validate /tmp/cetools-broken --json > /tmp/before.json
git stash pop
uv run cetools validate /tmp/cetools-broken --json > /tmp/after.json
diff /tmp/before.json /tmp/after.json
```

**Expected**: no differences, for any broken data set, across the structural
commits. Differences across the *behavioral* commit are expected and are
exactly the ones Scenario 1 names.

Use a broken corpus wide enough to reach the messages the suite does not: the
five table phrasings the required-table conversions carry
(`"a table"`, `"a table with label and class"`, `"a [task] table"`,
`"a [pseudo-hex] table"`, `"a mustering-out table"`) are all in the set no test
names, and they sit on the migration's riskiest step.

## Scenario 4: the duplication cannot grow back (FR-014a)

```sh
uv run pytest tests/guards/test_no_duplicate_checks.py -v
```

**Expected**: passes, and its self-test demonstrates the detector is not
vacuous—following the convention every guard in `tests/guards/` observes.

**What it does not catch** (FR-014b, stated here because the requirement obliges
every description of the guard to state it): the guard recognizes a check by its
name at a module's top level. A check written fresh and inline, without a name,
goes undetected—which is the very shape this feature spends eleven conversions
removing. Closing that would mean recognizing a check by its structure, a much
larger machine aimed at a rarer mistake than the one that actually happened: the
copies that accumulated were copies of a named helper, five times over.

To confirm by hand that each check is defined exactly once:

```sh
for h in unrecognized_key_problems require_int require_string \
         require_bool require_roll require_dict optional_bool; do
    printf '%-28s ' "$h"
    rg -n "^def _?$h\(" src/cetools/ | tr '\n' ' '
    echo
done
```

**Expected**: one line each, every one naming `src/cetools/schema.py`. Before
this feature the same loop reports sixteen definitions across five files.

## What to check before committing

Per the project's commit discipline, and CONTRIBUTING.md's Style and tooling
section:

```sh
uv run pytest
uv run black src tests
uv run isort src tests
uv run flake8 src tests
```

The three lint commands are scoped to `src tests` deliberately; unscoped they
report thousands of errors from the virtualenv and the vendored trees. They are
not constitutional gates, but the project's commit discipline resolves their
warnings before a commit.

And the Tidy First rule this feature turns on: the wording changes and their
changelog entry ship in their own commit, before any duplicate is removed, and
each commit message says whether it is behavioral or structural.
