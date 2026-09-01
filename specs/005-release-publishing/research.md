# Phase 0 Research: Release Publishing

Every decision this plan rests on, with what it rejected. Nothing in the
Technical Context is marked NEEDS CLARIFICATION; the two questions that were
genuinely open (the type checker, and the feature directory name) were put to
the user and are recorded as R10 and R21.

## R1. Distribution channel and asset set

**Decision**: GitHub Releases on `lgw4/cetools`. Each release carries exactly
four assets: the hatchling-built sdist (`cetools-<normalized>.tar.gz`), the
wheel (`cetools-<normalized>-py3-none-any.whl`), a combined
`SHA256SUMS.txt`, and the attestation bundles GitHub stores alongside the
release for each artifact.

**Rationale**: the constitution, as amended on 2026-08-31, ratifies "a tagged,
immutable bundle published on the project's public source repository" and
records index publication as the intended *future* channel. No account exists
on any index, so an index step today would be untested automation guessing at
configuration values that do not exist (spec, Out of Scope).

**Alternatives considered**: PyPI (blocked by the amended constitution and by
the absent account); a git tag alone with no published artifacts (fails FR-001,
which requires both distribution formats to be carried).

## R2. Tag format and the version's three spellings

**Decision**: tags are `v` plus the declared padded CalVer form, so
`v2026.08.1`. The preflight strips exactly one leading `v` and compares the
remainder byte-for-byte against `project.version`.

**Rationale**: this is the prevailing convention for tagged releases and it is
what the spec's Assumptions section already fixed. Stripping exactly one `v`
(rather than any run of them, or any non-digit prefix) means `vv2026.08.1` and
`version-2026.08.1` are rejected rather than silently accepted.

**The consequence worth naming**: the version now has three spellings, and each
belongs in one position only.

| Spelling | Where it appears | Produced by |
| --- | --- | --- |
| `2026.08.1` | `pyproject.toml` `project.version`, the `## ` changelog heading, the tag with `v` stripped, the release URL path | Written by hand; the single authority |
| `2026.8.1` | `importlib.metadata`, every rendered provenance block, the built artifact filenames | PEP 440 normalization, which drops the zero padding |
| `v2026.08.1` | the git tag, the release title, the `releases/download/v…/` URL segment, the `git+…@v…` source install | The tagging step |

FR-012 exists because of this table: the drift guard must accept the padded
form where the tag appears and the normalized form where the filename appears,
rather than demanding one string everywhere. The existing guard compares
everything against `package_version()`, which is the normalized form, so it has
to grow a second pattern group rather than a third pattern.

**Alternatives considered**: a bare `2026.08.1` tag (loses the conventional
signal that a ref is a release, and makes a tag indistinguishable from a branch
name at a glance); tagging the normalized form `v2026.8.1` (would make the tag
disagree with the declared version, which is exactly what FR-007 aborts on).

## R3. Static version, no dynamic versioning

**Decision**: `project.version` stays a literal string in `pyproject.toml`. No
`hatch-vcs`, no `dynamic = ["version"]`.

**Rationale**: FR-007 makes the declared version "the single authority for what
version is being released", and the whole abort-on-disagreement check exists to
compare the tag against it. Deriving the version *from* the tag would delete
the disagreement the check is there to find: every tag would trivially agree
with itself, and a mistyped tag would ship as a real release rather than
aborting. Dynamic versioning also breaks the existing CalVer-shape guard, which
reads the declared string out of `pyproject.toml` before any build happens.

**Alternatives considered**: `hatch-vcs` (rejected as above, and it adds a
build-time dependency for no benefit this project wants).

## R4. Workflow shape

**Decision**: a new `.github/workflows/release.yaml`, triggered on
`push: tags: ['v*']`, one job on `ubuntu-latest` with Python 3.13.

**Rationale**: `.yaml` is this repository's extension for every YAML file it
writes (recorded in 001's T005 amendment). A separate workflow rather than a
change to `ci.yaml` keeps the merge-time matrix untouched, which the spec's
Dependencies section requires. A single job is justified in the spec's
Assumptions: the artifacts are `py3-none-any`, and `ci.yaml` already covers
three platforms and two interpreters at merge time, so repeating the matrix at
release time would buy nothing. Python 3.13 because it is the supported floor,
and a wheel built on the floor is the conservative choice.

**Permissions**: `contents: write` (create the release and upload assets),
`id-token: write` and `attestations: write` (both required by
`actions/attest-build-provenance`).

**Alternatives considered**: a matrix release job (rejected in the spec's Out
of Scope); a `workflow_dispatch` trigger alongside the tag (rejected: FR-003
makes the tag push the *only* trigger, and a manual trigger would let a release
be cut from an untagged commit).

## R5. Preflight ordering

**Decision**: the four abort checks run first, in this order, before the test
suite:

1. The tag with `v` stripped equals `project.version` (FR-007).
2. `CHANGELOG.md` has a `## <version>` heading at all (spec, Edge Cases).
3. That heading is dated rather than marked unreleased (FR-008).
4. No release for that version already exists (FR-025).

Only then `uv sync`, `uv run pytest` (FR-005), `uv build`, attest, publish.

**Rationale**: FR-005's "nothing published" and FR-025's "abort before
publishing anything" are both satisfied by any ordering that puts the checks
before `gh release create`, but putting them before the *test run* is strictly
better: the already-published case and the mistyped-tag case are the two most
likely failures, and both are decidable in under a second. Checks 2 and 3 are
separate because they abort for different reasons and should say so: a missing
section means there is no announcement text at all, while an undated one means
the announcement would go out saying "unreleased".

**Alternatives considered**: running the checks after the build so the release
job produces artifacts for inspection even when it aborts (rejected: it wastes
a full matrix-free test run on a tag that was always going to be refused, and
an artifact from an aborted release is a thing nobody should have).

## R6. Provenance attestation

**Decision**: `actions/attest-build-provenance`, one invocation covering both
`dist/*` artifacts, run after the build and before `gh release create`.

**Rationale**: it is GitHub's own first-party attestation action, it produces a
signed, Sigstore-backed statement binding each artifact to the workflow run and
the source commit, and it is verifiable with `gh attestation verify` without
the project distributing a key. That is exactly FR-006's "signed provenance
record binding the artifact to the exact source commit and build that produced
it", with no key management this project would then have to own.

**Left to task time**: pin the action to its current major tag, confirmed
against the action's own releases at implementation time rather than guessed
here. The repository's existing convention (from `ci.yaml`) is to pin an exact
tag where a vendor has stopped publishing floating majors, and a floating major
otherwise.

**Alternatives considered**: detached GPG signatures (requires the maintainer
to hold and rotate a key, and gives a verifier nothing about *which build*
produced the artifact); no attestation (fails FR-006).

## R7. Checksums: the file, not the body

**Decision**: one combined `SHA256SUMS.txt`, generated with `sha256sum` in the
release job, uploaded as a release asset. The checksums do **not** appear in
the release body.

**Rationale, and a conflict resolved.** The planning input asked for "SHA-256
checksums in the release body". FR-002, as resolved in the spec's clarification
session, fixes the body as the changelog section verbatim followed by the fixed
attribution footer, and says "nothing else may be added". The footer is
described as *fixed*, so per-release checksums cannot be folded into it either,
and SC-002 requires the notes to *end* with the footer, so they cannot go after
it. The asset satisfies what the requirement is actually for: FR-006 asks for
"a single combined file carrying one line per artifact, verifiable in one
command with a stock checksum utility", and SC-008 asks a user to verify
"without installing anything". A body listing is a convenience the ratified
spec forbids; the file is the requirement.

`sha256sum`'s output format is what makes the one-command claim true, because
it is the format `sha256sum -c` reads back:

```text
<64 hex digits>  cetools-2026.8.1-py3-none-any.whl
<64 hex digits>  cetools-2026.8.1.tar.gz
```

Verification on each supported platform, none of which needs an install:

| Platform | Command |
| --- | --- |
| Linux | `sha256sum -c SHA256SUMS.txt` |
| macOS | `shasum -a 256 -c SHA256SUMS.txt` |
| Windows | `Get-FileHash <file> -Algorithm SHA256` and compare |

**Alternatives considered**: per-artifact `.sha256` files (rejected by the
spec's clarification, which chose one combined file); publishing the checksums
in both the file and the body (rejected by FR-002, as above).

## R8. Release notes: extraction in pure Bourne shell

**Decision**: `scripts/changelog-section.sh <version>` prints the body of the
`## <version>` section of `CHANGELOG.md`: everything after the heading line, up
to the next `## ` heading or end of file, with leading and trailing blank lines
trimmed. It exits non-zero with a message on stderr if no such heading exists.
The workflow concatenates its stdout with `.github/release-footer.md` and
passes the result to `gh release create --notes-file`.

**Rationale**: FR-002 requires the changelog section reproduced verbatim, which
means the extractor may not reflow, summarize, or reformat anything. `awk` with
a state flag does this in a few lines and is available on every runner. Pure
Bourne shell (`/usr/bin/env sh`, no bashisms) is the repository's stated
scripting standard.

**The end-of-file case matters right now.** `CHANGELOG.md` currently has
exactly one `## ` section, so the very first release exercises the
"runs to EOF" branch rather than the "stops at the next heading" branch. Both
branches need a test, and the EOF branch needs one first.

**Alternatives considered**: `gh release create --generate-notes` (produces a
commit-list summary, not the curated changelog text FR-002 requires); a Python
extractor (see the Principle VI note in plan.md).

## R9. The fixed footer, and why it is a file

**Decision**: `.github/release-footer.md` holds the attribution and
non-affiliation text, appended verbatim by the workflow. A guard in
`tests/unit/test_licensing.py` asserts the file exists and carries both the
exact `ATTRIBUTION` string that module already defines and one of its
`NON_AFFILIATION_PHRASES`.

**Rationale**: FR-021 requires the footer to arrive "as a fixed footer appended
by the release automation rather than as text maintained per version in the
changelog, so no release can be published without it". A file plus a guard is
what makes "cannot be published without it" true rather than aspirational: the
text cannot be dropped without failing the suite, and the suite gates the
release. Reusing the constants already in `test_licensing.py` means the footer
is checked against the same strings every other surface is checked against, so
the two cannot drift apart.

**Alternatives considered**: inlining the footer in `release.yaml` (harder to
guard, and puts license-obligation text in a file nobody reviews for that);
repeating it in every changelog entry (explicitly rejected by FR-021).

## R10. Type checker: mypy

**Decision**: `mypy` in the `dev` dependency group, configured under
`[tool.mypy]` in `pyproject.toml`, documented in CONTRIBUTING.md's "Style and
tooling" section alongside black, isort, flake8, and rumdl. It gates nothing:
not the suite, not `ci.yaml`, not the release.

**Rationale**: chosen by the user from the three the planning input offered. It
is a stable, pure-Python dev dependency whose configuration lives in the file
that already configures every other tool here, with no Node runtime to fetch
and no pre-1.0 churn to document around. Principle III says in as many words
that lint, format, and type-check tooling "may be used but is not
constitutionally required", and FR-022 repeats the prohibition, so the
non-gating property is not a convenience but the requirement.

**What this deliberately does not require**: a clean mypy run. Making zero
errors a deliverable would be the mandated gate that Principle III and FR-022
both forbid, arriving by the back door. The task list should record the
baseline the tool reports on first run and fix what is cheap, without treating
the remainder as blocking.

**Alternatives considered**: `ty` (same vendor as `uv`, but pre-1.0 with a
moving diagnostic and configuration surface, which is a poor thing to document
as the optional tool a newcomer should reach for); `pyright` (strongest
inference, but the pip-installable package fetches a Node runtime on first run,
a heavier ask for a tool that gates nothing).

## R11. `py.typed`

**Decision**: an empty `src/cetools/py.typed`. Hatchling's
`packages = ["src/cetools"]` ships non-Python files inside the package
directory, so no `pyproject.toml` change is needed to carry it. Guarded in
`tests/guards/test_packaging.py` for both formats: `cetools/py.typed` in the
wheel, `src/cetools/py.typed` in the sdist.

**Rationale**: PEP 561. Without the marker a type checker consuming an
installed `cetools` treats it as unannotated regardless of how thoroughly it is
annotated, which is exactly what FR-020 and SC-011 forbid. FR-020 requires the
marker "present in both distribution formats, verified by a packaging guard",
so the guard is part of the requirement rather than an extra.

**The file must be empty**, not a comment. PEP 561 gives `py.typed` contents no
meaning, and a `# ` line in it would be the sort of thing a later reader tries
to interpret.

## R12. Tightening the packaging guard to full paths

**Decision**: `test_wheel_contains_every_packaged_data_file` and
`test_sdist_contains_every_packaged_data_file` compare full relative paths
instead of basenames.

- Source side: each `.toml` under `src/cetools/data/`, as a path relative to
  `src/cetools/`, so `data/careers/diplomat.toml`.
- Wheel side: each member under `cetools/data/`, with the `cetools/` prefix
  stripped, giving the same shape.
- Sdist side: each member under `<name>-<version>/src/cetools/data/`, with the
  version prefix and `src/cetools/` stripped, giving the same shape.

The assertion compares the two sets and, on failure, names the paths that
differ rather than reporting a set inequality.

**Rationale**: FR-015 and SC-010. The current checks compare
`{p.name for p in ...rglob("*.toml")}` against
`{name.rsplit("/", 1)[-1] for name in ...}`, so a build that flattened all 42
files into one directory contains every basename and passes. The loader reads
the nested layout, so such a build is broken in a way the guard was blind to.
Comparing full relative paths is the whole fix; nothing else about the guard
changes.

**A dependency worth noting**: the existing basename comparison also happens to
enforce basename uniqueness across the tree (two `skills.toml` files at
different depths would collapse the source set and fail). The full-path
comparison does not, and there is a separate uniqueness requirement elsewhere
in the suite. Task time should confirm that separate check exists and is not
silently being relied on here.

**Alternatives considered**: asserting a fixed manifest of 42 paths (brittle,
and it would fail on every legitimate data addition); comparing directory
depths only (catches a flatten but not a rename or a move between subtrees).

## R13. Extending the documented-version drift guard

**Decision**: `tests/guards/test_documented_version.py` splits its single
`_PATTERNS` tuple into two groups compared against two different expected
values.

| Group | Patterns | Compared against |
| --- | --- | --- |
| Reported (normalized) | `\(cetools ([^)]+)\)`, `"version": "([^"]+)"`, the wheel filename in the install command | `package_version()`, i.e. `2026.8.1` |
| Declared (padded) | the `releases/download/v(...)/` tag segment, the `@v(...)` source-install ref | `project.version` from `pyproject.toml`, i.e. `2026.08.1` |

`test_the_guard_has_something_to_check` grows accordingly: each group must have
matched at least once, and every match in a group must equal that group's
expected value. A glob or a pattern that matched nothing must fail, which is
the property that test already exists to protect.

**Rationale**: FR-011 puts the install command under the guard, and FR-012 says
the guard must accept the right form in each position rather than one string
everywhere. A single expected value cannot express that, because the install
command genuinely contains both spellings, three characters apart:

```text
https://github.com/lgw4/cetools/releases/download/v2026.08.1/cetools-2026.8.1-py3-none-any.whl
```

The stale-version failure this prevents is specific and unrecoverable in place:
a stale value in the tag segment hands a reader a download URL that 404s, and
the version that shipped it is already spent.

**Alternatives considered**: normalizing both spellings before comparison
(would let a padded form sit in the filename position and an unpadded one in
the tag position, both of which produce a 404, and both of which the guard
would then pass).

## R14. `[project]` metadata additions

**Decision**: add `keywords`, `classifiers`, `authors`, and `[project.urls]`.
The existing `description`, `license`, `license-files`, and `readme` are
unchanged.

- **`classifiers`**: development status, `Environment :: Console`,
  `Intended Audience :: End Users/Desktop`,
  `Operating System :: OS Independent`,
  `Programming Language :: Python :: 3.13` and `3.14`,
  `Topic :: Games/Entertainment :: Role-Playing`, and `Typing :: Typed`.
- **No license classifier.** `license` is already an SPDX expression, and
  002's task notes record that mixing the two produced a metadata problem
  once. The SPDX expression is the modern spelling; a `License ::` classifier
  alongside it is redundant at best.
- **`keywords`**: descriptive terms only, and deliberately **not** `cepheus`.
  A keyword naming the trademark would be a Product Identity string in the
  package's own metadata, and depending on phrasing a compatibility claim in a
  surface that carries no attribution.
- **`authors`**: name only, no email. Recorded as an open call in R22.
- **`[project.urls]`**: `Homepage`, `Repository`, `Changelog`, `Issues`, all
  pointing at `https://github.com/lgw4/cetools`, with `Changelog` at the
  blob URL for `CHANGELOG.md` and `Issues` at `/issues`.

**Rationale**: FR-019 asks for "the descriptive fields a released package is
expected to have" plus links to the source, the changelog, and the issue
tracker. `Typing :: Typed` is the classifier half of R11's `py.typed`.

**Alternatives considered**: a `Development Status :: 5 - Production/Stable`
classifier (overclaims for a first release); `Topic :: Games/Entertainment`
without the `Role-Playing` leaf (less specific for no gain).

## R15. README installation

**Decision**: replace `uv add cetools` with the released wheel, and offer the
tagged source as the alternative.

```sh
uv tool install https://github.com/lgw4/cetools/releases/download/v2026.08.1/cetools-2026.8.1-py3-none-any.whl
```

```sh
uv tool install git+https://github.com/lgw4/cetools@v2026.08.1
```

**Rationale**: FR-016, FR-017, FR-018. `uv add cetools` is false today and
would stay false after this release, because `uv add` resolves from a package
index that has never carried this package. `uv tool install` is the right verb
for a CLI a reader wants on their PATH, and it accepts both a URL and a
`git+…@ref`, so the two instructions are the same shape. Both carry a version,
so both fall under R13's extended drift guard, which is how FR-011's "a stale
version there fails the test suite" is discharged.

**The chicken-and-egg is real and accepted**: the README names a URL that 404s
until the release exists. The release is cut from the same commit that carries
the README, so the window is the duration of one workflow run, and the
alternative (documenting the install only after the release) would mean the
first release ships with a README that still points at a package index.

**Alternatives considered**: `pip install <url>` (works, but the repository's
documented toolchain is `uv` throughout); linking to the releases page rather
than a pinned artifact (avoids the drift problem by giving the reader no
command to run, which fails SC-007's "no additional steps").

## R16. Where the release procedure is documented

**Decision**: CONTRIBUTING.md's existing "Changelog and releases" section is
rewritten in place. No new file.

**Rationale**: FR-014 says the procedure "MUST live in the existing contributor
documentation, not in a new file", and names what it has to cover: the tagging
sequence, the changelog dating step, the version-update step, and the
month-rollover rule. The same section currently ends with "Releases are
published to PyPI", which FR-024 requires replaced, so the two edits are the
same edit.

## R17. The month-rollover rule is documented, not automated

**Decision**: FR-010's rule ("bump the version before tagging when the current
month no longer matches the month the declared version names") is a documented
step in the release procedure and a line in the preflight's own documentation.
It is **not** a pytest guard and **not** a workflow check.

**Rationale**: a guard comparing the declared month against the current month
would fail the suite for every contributor on the first day of every month,
including on branches that are nowhere near a release. It would also fail
`ci.yaml` on `main` for reasons no PR introduced. The failure mode it guards
against (shipping a version stamped with a month that has passed) is cosmetic
and self-announcing, which is not worth a check that breaks the build on a
calendar.

**Alternatives considered**: a workflow-only check comparing the tag's month
against the run date (rejected on a narrower ground: it would refuse a
legitimate re-run of a release whose tag was pushed minutes before midnight on
the last day of a month, aborting a correct release for a clock).

## R18. The already-published check

**Decision**: `gh release view "$TAG"` in the preflight. If it exits zero, a
release exists; abort with a message naming the version as already published.
If it exits non-zero, proceed.

**Rationale**: FR-025 and SC-013. `gh release view` is the cheapest question
that answers exactly what FR-025 asks, and because the workflow never passes
`--clobber` and never calls `gh release edit` or `gh release upload`, the
"MUST NOT overwrite, replace, or add artifacts" clause holds structurally
rather than by the check alone. `gh release create` against an existing tag
would fail on its own, but failing at the *last* step is not the same as
aborting before publishing anything, and the error it gives says nothing about
a version being spent.

**Alternatives considered**: checking for the tag rather than the release
(wrong question: a tag exists at the moment the workflow runs, always).

## R19. Testing shell scripts from pytest

**Decision**: `tests/guards/test_release_scripts.py` invokes both scripts via
`subprocess.run(["sh", str(script), ...])` against fixture changelogs written
into `tmp_path`, asserting stdout, stderr, and exit code. It skips when
`shutil.which("sh")` is `None`.

**Rationale**: Principle III applies to these scripts as much as to library
code, and the extraction script in particular has branches (section runs to
EOF, section stops at the next heading, section absent, heading dated, heading
marked unreleased) that are cheap to test and expensive to debug in a workflow
run. The skip follows the pattern `test_packaging.py` already uses for a
missing `uv`, and the repository already documents that the suite runs on
Windows: GitHub's Windows runners carry a `sh`, but a contributor's may not,
and a skip is the established answer.

**Both scripts must take their inputs as arguments**, including the changelog
path, rather than assuming the repository root. That is what makes them
testable against a fixture at all, and it costs one parameter.

**Alternatives considered**: testing the scripts only by running a release
(untestable before the first release exists, which is the release this feature
has to cut).

## R20. What the release job runs, and the double build

**Decision**: `uv sync`, then `uv run pytest` with no `-m` filter, then
`uv build`.

**Rationale**: FR-005 says "the full test suite", so the `slow` marker is not
excluded here even though CONTRIBUTING.md recommends excluding it in the inner
loop. The consequence is that `tests/guards/test_packaging.py` runs `uv build`
four times inside the test run (a wheel and an sdist, each built once per
module-scoped fixture) and the job then builds both again for the artifacts.
That is accepted: the artifacts published must come from a build the workflow
controls and can hand to the attestation step, and reusing a build from inside
a pytest `tmp_path_factory` directory would couple the release to a test
fixture's internals.

## R21. Feature directory name

**Decision**: `specs/005-release-publishing`, unchanged.

**Rationale**: the planning input named `specs/005-packaging-release`. The
branch, the existing `spec.md`, and that file's own "Feature Branch" field all
say `005-release-publishing`, and `specs/001-*` refers to `packaging-release`
in prose as a *feature name* rather than as a directory that ever existed.
Confirmed with the user, who chose to keep the existing name. 001's references
are read as pointing here.

## R22. Open call for task time: the author email

**Decision deferred, deliberately.** `authors` is specified as name-only in
R14. Adding an email address to `[project]` publishes it in the metadata of
every distribution and on the release page, which is a disclosure decision
rather than a packaging one. The maintainer's address is already visible in the
git history, so nothing is being concealed by omitting it; it is simply not
this plan's call to make. If an address is wanted, adding
`email = "..."` to the `authors` entry is a one-line change with no other
consequence.
