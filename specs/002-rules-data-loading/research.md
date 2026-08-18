# Phase 0 Research: Validated Rules Data Loading

**Feature**: `002-rules-data-loading` | **Date**: 2026-08-13

Every Technical Context unknown is resolved below. Findings marked **verified** were
confirmed by running code on this machine against the working tree, not asserted from
memory. Findings marked **decision** are design choices with no empirical component.

## R1: File format for rules data

**Decision**: TOML for every rules data file, read with `tomllib`, as `tasks.toml`
already is.

**Rationale**: `tomllib` is standard library on the supported floor, so the format
costs no runtime dependency (Principle VI). The existing shipped file is TOML, and
FR-044 folds it into this data set rather than converting it. TOML's table syntax
expresses the career schema (nested throws, named tables, arrays of tables for rank
ladders) without indentation-sensitive parsing, and its parse errors carry line and
column, which FR-022 needs.

**Alternatives considered**: JSON, rejected because it has no comments and every data
file must carry an Open Game Content designation comment (FR-046). YAML, rejected
because it is a third-party runtime dependency for content TOML expresses adequately,
and because its implicit typing would silently turn a rank title such as `NO` into a
boolean.

## R2: How a file's kind is determined

**Decision**: every data file declares its kind in a `schema` key alongside
`schema-version`. The kind selects which schema validates the file. The filename,
not the kind, remains the composition identity (FR-019a).

**Rationale**: this is forced by FR-032 and FR-040a taken together. FR-040a says a
single file's position is read from its basename alone, "ignoring the directory it
sits in", and FR-032 says a basename matching nothing is an addition. An added file
therefore arrives with no directory to classify it and no matching packaged slot to
inherit a kind from, so nothing outside the file can say what schema it should be
held to. Declaring the kind in the file is the only place left, and it costs one line
in a file that already carries a declared version.

A replacement's declared kind must equal the kind of the packaged file whose basename
it matched; a mismatch is a validation problem. This makes the check strictly
stronger than inferring the kind, because it catches a file saved under the wrong
name.

**Alternatives considered**: infer the kind from the directory within the override,
rejected because FR-040a explicitly discards the directory, so `validate` on a file
would classify it differently from a load of the directory containing it, which is
exactly the disagreement FR-040 forbids. Infer the kind from the shape of the
contents, rejected because FR-002 forbids interpreting a file's contents before its
version is accepted, and because a career file missing its `[tables]` section would
be diagnosed as an unrecognized shape rather than as a career with a missing section.

**No longer a Principle VI tension.** This was recorded in `plan.md` Complexity Tracking
as a declared field beyond the one FR-001 names. The requirements checklist found that the
field was forced by requirements that did not themselves state it, and FR-001a now
requires the kind declaration outright, so the field implements a requirement rather than
exceeding one.

## R3: Composition key: basename everywhere

**Decision**: an override file is positioned by its basename alone, whether it was
found in a directory override or supplied as a single file. Two files in one override
sharing a basename is a validation problem naming both.

**Rationale**: one rule rather than two. The clarified FR-040a already fixes basename
keying for the single-file case; using relative path keying for directory overrides
would make `cetools validate override/navy.toml` report a replacement while
`cetools validate override/` reported an addition for the same file sitting outside
`careers/`. FR-040 requires that what the command reports is what a run would do, so
the two must agree, and only basename keying makes them agree in every case.

**Superseded rationale, kept for the record.** This finding originally had to argue that
basename keying honored FR-029's "MUST mirror the layout" as a superset rather than a
departure. That reconciliation is no longer needed: the requirements checklist found that
the two readings give opposite outcomes for a flat-layout override, a replacement under
one and a rejected duplicate career name under the other, and FR-029 was amended to state
basename positioning directly, with layout mirroring reduced to a recommendation. The
decision above is unchanged; only its standing is. It now implements a requirement rather
than reinterpreting one.

**Consequence to guard**: basenames must be unique across the packaged layout, or the
key stops identifying a slot. This is a test, not a convention (see `plan.md`).

## R4: Provenance fingerprint

**Decision**: SHA-256 over the file's raw bytes, reported as `sha256:` followed by
the full 64-character lowercase hex digest.

**Rationale**: FR-036 requires the fingerprint to depend on content and nothing else,
which hashing the bytes as read satisfies exactly. SHA-256 over raw bytes is what
`shasum -a 256 <file>` and `sha256sum <file>` already compute, so a user handed a
result can reproduce the reported fingerprint with a command they already have. That
is the whole value of reporting it, and it is lost if the bytes are decoded,
normalized, or re-serialized first. The algorithm is named in the value so a later
change is visible rather than silent.

The digest is reported in full rather than truncated: a truncation length is a
parameter with no principled value, and SC-008 needs only equality.

**Consequence, accepted**: a file differing only in line endings fingerprints
differently. That is correct under FR-036, which makes the fingerprint a function of
content, and line endings are content.

**Alternatives considered**: blake2b, used by `seeds.py` for text seeds, rejected here
because no standard command-line tool reproduces a truncated blake2b digest, and the
two uses have different requirements: the seed fold needs a specific output width,
the fingerprint needs external verifiability.

## R5: Reading the packaged data set, including subdirectories

**Decision**: walk `importlib.resources.files("cetools.data")` recursively for
`*.toml`, sorted, with no filesystem path construction and no `__file__`.

**Verified**: `resources.files("cetools.data").joinpath("sub").is_dir()`,
`.iterdir()`, and `.joinpath(name).read_text()` all work for a subdirectory that is
not itself a package, on CPython 3.14.5 against this working tree. A recursive walk
returned both `sub/probe.toml` and `tasks.toml`. No `__init__.py` is needed in
`data/careers/` or `data/registries/`.

**Rationale**: FR-027 forbids searching any location the caller did not name, and
`resources.files` reads the installed package rather than the working directory,
which is what makes the `src/` layout's guarantee honest (the packaging guard test
would catch a wheel that dropped a data file). Report stability across platforms,
which SC-002 and SC-003 depend on to assert content, does not in fact come from this
walk order: `_discover_packaged` returns a basename-keyed dict, `_validate` re-iterates
`sorted(composed)`, and every collected problem passes through `problems.sort()` before
a report is built. Those two sorts are what earn the guarantee; this one is normalized
downstream and could be dropped without changing report order (`rules.py` `_walk_toml`,
`_validate`).

## R6: Proving that no outside location is opened (SC-007)

**Decision**: a guard test installs a `sys.addaudithook` hook that records `open`
audit events while armed, arms it around a packaged load, and asserts every recorded
path lies inside the installed `cetools` package directory.

**Verified**: the hook fires for the `resources.files(...).read_text()` read, capturing
the absolute path of `tasks.toml`. It also captures import machinery reads of `.pyc`
files, so the test must import everything it needs before arming, and filter
`__pycache__` paths.

**Rationale**: SC-007 requires an automated check rather than inspection. An audit
hook observes the interpreter itself rather than a mocked seam, so it cannot be
satisfied by a load path that bypasses the mock. Audit hooks cannot be removed once
installed, so the hook is installed once at module import in the single guard module
and does nothing unless armed.

**Alternatives considered**: monkeypatching `builtins.open` and `pathlib.Path.open`,
rejected because it verifies only the seams the test thought to patch, and
`importlib.resources` may reach the filesystem by another route on another platform.

## R7: Collecting every problem rather than raising at the first

**Decision**: validation is a function from a composed set of files to a
`ValidationReport` holding a tuple of `ValidationProblem`. Nothing in the validation
path raises on a data problem. `load_rules` calls the same function and raises
`RulesDataError` carrying `.problems` when the report is not clean; `validate_rules`
returns the report.

**Rationale**: FR-021 requires all problems together and FR-023 requires the on-demand
and on-load checks to be the same check, which is satisfied structurally rather than
by discipline if there is exactly one implementation and the difference between the
two entry points is only what they do with the report. A file that fails to parse
yields one problem and contributes no content; the remaining files are still checked,
which is what makes SC-003's four-problems-in-one-run case work when one of the four
is in another file.

`RulesDataError` keeps its message-only constructor, because `tasks.py` raises it for
runtime invariant failures that are not data-file problems.

## R8: Where provenance rides

**Decision**: `CheckResult` gains a `provenance` field, and `check` takes
`rules: RulesData | None` in place of `parameters: TaskParameters | None`.

**Rationale**: FR-037 binds "every command that resolves against rules data".
`cetools roll` resolves against none (recorded in the spec's Assumptions), so
`ThrowResult` is untouched and the three `roll` golden files stay byte-for-byte
identical, which is itself evidence for SC-009. Putting provenance on the result
keeps rendering a single dispatch on one value and keeps the CLI from having to thread
a second argument into the renderer.

Replacing `parameters=` rather than adding `rules=` beside it follows FR-044, which
says the old reading is replaced rather than kept alongside. Package version
`2026.08.1` is unreleased, so the break costs no released consumer; it is recorded
under a **Breaking changes** heading in the changelog regardless.

**Added after the requirements review**: provenance also carries the package version
(FR-033a), read once from `importlib.metadata` rather than passed in, so a result cannot
report a version other than the one that produced it. Because that version reaches
rendered output, committed goldens and JSON fixtures hold it as a placeholder substituted
at comparison time (SC-009), and one test asserts the reported value against the installed
version directly (SC-008). Embedding the literal would rewrite every check golden on every
release, and each rewrite is another occasion to absorb an unrelated change, which is what
SC-009 exists to prevent.

## R9: Notation disambiguation

**Decision**: parse the four forms by anchoring on the tail of the entry, in this
order:

| Order | Pattern anchored at end | Form | Example |
|---|---|---|---|
| 1 | `\s+(\d+)\+$` | characteristic check | `INT 4+` |
| 2 | `\s+([+-]\d+)$` | characteristic adjustment | `STR +1` |
| 3 | `\s+(\d+)$` | grant with explicit level | `Pilot 2` |
| 4 | (none matched) | bare name | `Vacc Suit` |

The remainder is the name, which may contain spaces, apostrophes, slashes and
hyphens, and may end with a parenthesized specialty.

**Rationale**: the three suffixed forms are mutually exclusive because a trailing `+`
marks the check, an explicit sign marks the adjustment, and a bare integer marks a
level. Ordering matters only between rules 1 and 3, which the trailing `+` separates;
the order is pinned anyway so a later editor cannot reorder them harmlessly-looking.
Anchoring at the tail rather than tokenizing left to right is what lets a skill name
contain spaces without quoting.

**Trap recorded**: a name ending in a digit would be read as a grant. No name in any
shipped registry does, and the registry check catches it (the truncated name fails to
resolve), but the diagnostic would be confusing. Named here so review sees it.

## R10: Which forms are legal where

**Decision**: three notation contexts, fixed by the field, per FR-005.

| Context | Fields | Admissible forms | Registry for the name |
|---|---|---|---|
| Skill table | `tables.*.entries`, `ladders[].ranks[].bonus` | adjustment, grant, bare | characteristics for adjustment; skills for grant and bare |
| Benefit table | `mustering-out.benefits` | adjustment, bare | characteristics for adjustment; benefit items for bare |
| Gate | `tables.*.requires` | check only | characteristics |

**Rationale**: FR-005 fixes a bare name's meaning by position, and the explicitly
suffixed forms carry their own registry because an adjustment is a characteristic
adjustment wherever it appears. A form outside its context's set is a malformed entry
under FR-009 and reports the forms that were acceptable in that position.

## R11: Where file schemas live in the code

**Decision**: each module owns the schema of the files it produces types for.
`careers.py` validates career files, `registries.py` validates the three registry
files, and `rules.py` validates task parameters and owns discovery, composition,
provenance assembly, and dispatch to the other two.

**Rationale**: keeps `rules.py` from becoming the one place that knows everything,
and keeps a career's schema next to the type it builds, where a reader looks first.
The alternative, a `rules/` package with a `schema.py`, was rejected as more structure
than roughly 800 lines needs and as a departure from the flat module layout the
package already uses.

## R12: Discharging SC-009 without regenerating the evidence

**Decision**: before any behavior changes, the five current golden files are copied
verbatim to `tests/golden/pre-loader/` and committed. That directory is never
regenerated. A test asserts, for each check golden, that the new output equals the
old output with exactly the provenance block inserted, and for each roll golden, that
the new output is byte-identical to the old.

**Rationale**: SC-009 requires comparison against the outputs committed with the
previous feature "rather than against regenerated ones", and requires the regeneration
itself to be checked so that a changed number cannot be absorbed. Copying the evidence
before touching the code is what makes that possible; regenerating first would destroy
it. The same rule covers the JSON contract fixtures: every key except the new
`provenance` compares equal.

## R13: Deliberate omissions

Recorded so review does not read them as oversights.

- **No table length constraint.** Skill tables and mustering-out tables are validated
  as non-empty, not as exactly six or seven entries. How a table is indexed belongs to
  the generator that rolls on it, and pinning the length here would put a rules
  constant in engine code, which Principle V forbids.
- **No benefit item semantics.** A benefit item's name is checked against the registry
  and nothing else, per the spec's Out of Scope.
- **No schema migration.** One version per kind exists; the field is checked for
  equality and nothing more, per the spec's Assumptions.
- **No override caching.** The packaged load is cached, since the installed files
  cannot change within a process. An override load is not, because a caller may edit
  the file and load again in the same process, which is the authoring loop.
- **No grouping or bounding of a problem cascade.** One truncated skills registry makes
  every skill reference in every career an unrecognized name. FR-021 requires every
  problem, and folding some would put the loader in the business of guessing which mistake
  caused which. Now recorded in the spec's Out of Scope with its cost stated and deferred
  to the feature that authors the full career set, which will have evidence this one lacks.
