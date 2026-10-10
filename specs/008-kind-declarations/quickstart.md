# Quickstart: validating Kind Declarations

How to verify each user story. The design is in
[contracts/kind-declarations.md](contracts/kind-declarations.md) and
[data-model.md](data-model.md); the commit sequence is in
[research.md](research.md) R8.

## Prerequisites

```sh
uv sync
```

Record the baseline before the first commit:

```sh
git rev-parse HEAD > "$SCRATCH/base.txt"
wc -l < src/cetools/rules.py          # 1103 at 0074436
```

`$SCRATCH` is the session scratchpad. Nothing below is committed.

## Inner loop and commit gate

```sh
uv run pytest -m "not slow"           # after every step
uv run pytest                         # before every commit
```

## User Story 1: nothing a user sees moves (P1)

### 1a. Corpora untouched

```sh
uv run pytest tests/golden tests/contract tests/integration
git diff --stat main -- tests/golden tests/contract
```

Empty `git diff` output is the pass condition (FR-012). A failure here means
stop and reconsider, never edit a fixture or move the sort.

### 1b. Existing tests changed only as FR-012 permits

```sh
git diff main -- tests/ ':!tests/unit/test_rules.py'
git diff main -- tests/unit/test_rules.py
```

The first is empty. The second shows only: the rewritten pinning test, the two
version-bump patches and the `_KINDS` version loop (research R6), and the new
FR-015 tests (research R7).

### 1c. The header harness

The suite names some combinations of the kind machinery's reports; the harness
covers the rest by driving mutations from the packaged files. Write
`$SCRATCH/kinds_harness.py` to do the following, printing every problem of
every run as `case|file|location|found|expected`:

- For each packaged `.toml`, an override holding that basename with its header
  changed each of these ways: `schema` deleted; `schema` set to an unknown
  string; `schema` set to each other kind's name; `schema-version` deleted,
  raised by one, set to `"1"`, set to `true`; the whole file replaced by
  invalid TOML; the whole file replaced by invalid UTF-8.
- For each one-file kind, an override adding a second file declaring it under
  a new basename (duplicate declarer).
- For each one-file kind, an override replacing its canonical file with one
  declaring an unknown kind (the kind goes missing while the slot is occupied),
  and one declaring a different valid kind under a new basename while the
  canonical file is rejected on version.

Read the kind list and canonical files from the packaged data, not from
`_KINDS` or the old tables, so the harness is identical before and after.

```sh
git switch --detach "$(cat "$SCRATCH/base.txt")"
uv run python "$SCRATCH/kinds_harness.py" > "$SCRATCH/before.txt"
git switch 008-kind-declarations       # or the commit under test
uv run python "$SCRATCH/kinds_harness.py" > "$SCRATCH/after.txt"
diff "$SCRATCH/before.txt" "$SCRATCH/after.txt" && echo "no report moved"
```

An empty diff is the pass condition **for each of the three commits**. Commit 3
is the one that changes parse order, so its diff is the one that proves
research R4.

For body-level reports, 007's mutation harness
(`specs/007-parse-context-carrier/quickstart.md`, 1b) still applies; run it
once before commit 1 and once after commit 3.

### 1d. The named scenarios

Scenarios 2-4 (unknown kind, bad version, removed/duplicated/replaced kind)
are exercised by the existing suite and by the harness. Scenario 2's wording
depends on the kind names being sorted before joining; the harness's
unknown-kind cases pin it.

## User Story 2: a kind is described in one place (P1)

```sh
rg -n '_SUPPORTED_VERSION|_SINGLETON_KINDS|_CANONICAL_FILE|_KIND_AT_CANONICAL_FILE' src tests
rg -n 'load-bearing|moving a call moves a report' src/cetools/rules.py
```

Both empty (FR-011). Then, for a few kinds, for example:

```sh
rg -n '"draft-table"' src/cetools/rules.py
rg -n '"background-skills"' src/cetools/rules.py
```

Each hit is either the `_KINDS` declaration or code specific to that kind: the
background-skills step, a cross-file rule's local, or the explicit
`RulesData(...)` constructor. None is a list whose job is to enumerate kinds.

```sh
uv run pytest tests/unit/test_rules.py -k "declar or canonical"
rg -n '== 11|len\(.*_KINDS' tests
```

The FR-015 tests pass; the `rg` is empty (SC-005).

## User Story 3: the loader gets smaller (P2)

```sh
wc -l < src/cetools/rules.py
```

Strictly less than the baseline (SC-004).

## Commit hygiene

```sh
git log --format='%s' main..HEAD
git diff --stat main -- CHANGELOG.md
```

Every subject after the spec commits starts `refactor(rules):`; the
`CHANGELOG.md` diff is empty (FR-014).
