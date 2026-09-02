# Tasks: Release Publishing

**Input**: Design documents from `/specs/005-release-publishing/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: REQUIRED. Constitution Principle III (Test-First) is
NON-NEGOTIABLE, so every behavioral task below is preceded by the failing test
that motivates it. Write the test, watch it fail, then implement, then run the
suite.

**Organization**: Tasks are grouped by user story. US1, US2, and US3 are all
P1 and ship together as the first release; US4 and US5 are P2; US6 is P3.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US6)
- Every task names the exact file it touches

## Path Conventions

Single Python project. `src/cetools/` ships; `scripts/`, `.github/`, and
`tests/` do not. Repository root is `/Users/lgw4/Developer/python/cetools`.

## Tidy First

Structural and behavioral changes never share a commit, structural goes
first, and the commit message says which it is. The two tasks below that are
purely structural are marked **(structural)**; commit each on its own.

---

## Phase 1: Setup

**Purpose**: establish the baseline and confirm the feature's prerequisite.

- [ ] T001 Confirm the FR-023 prerequisite is discharged: `.specify/memory/constitution.md` is at version 2026.08.2, its Development Workflow section defines a release as a tagged bundle on the public source repository, and its Licensing section names the public release page. Stop the feature if any of this is missing.
- [ ] T002 Record the green baseline: run `uv run pytest` from the repository root and note the passing count, so every later red-green step is measured against it.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: resolve the three decisions research.md deferred to task time.
Each is a fact to establish, not code to write, and each blocks a story below.

**⚠️ CRITICAL**: no user story work begins until these three are answered.

- [ ] T003 [P] Confirm `tests/guards/test_data_layout.py::test_data_file_basenames_are_unique` exists and is the sole owner of basename uniqueness (research.md R12), so the full-path tightening in `tests/guards/test_packaging.py` does not silently drop a property nothing else holds. Blocks US5.
- [ ] T004 [P] Determine the exact way `gh release view` reports "no such release" versus an unobtainable answer (missing token, no network, rate limit) on the installed `gh`: run `gh release view v9999.99.9 --repo lgw4/cetools --json id` and capture the exit code and stderr wording, then repeat with `GH_TOKEN=` unset or an invalid host. Record both in a note for T023. Blocks US1's preflight check 6 (research.md R18, FR-025's fail-closed clause).
- [ ] T005 [P] Confirm the pin for each action `.github/workflows/release.yaml` will use — `actions/checkout`, `astral-sh/setup-uv`, `actions/attest-build-provenance` — against each action's current releases, and against the pinning convention already used in `.github/workflows/ci.yaml` (exact tag where the vendor stopped publishing floating majors, floating major otherwise). Blocks US1's workflow.

**Checkpoint**: the deferred decisions are answered; story work can begin.

---

## Phase 3: User Story 1 - Cut a release by pushing a tag (Priority: P1) 🎯 MVP

**Goal**: pushing `v<declared version>` publishes a release on `lgw4/cetools`
carrying both distribution formats, `SHA256SUMS.txt`, an attestation per
artifact, and release notes that are the changelog section verbatim followed
by the fixed footer — with no manual step after the push.

**Independent Test**: quickstart.md scenarios 1, 2, and 3 pass locally, and
scenario 7 (the first release) publishes a release matching the asset and body
contract in `contracts/release-workflow.md`.

**Note on scope**: the preflight script built here is also the mechanism US3
depends on. It lives in US1 because the workflow cannot exist without it.

### The changelog extractor (`contracts/release-scripts.md`)

- [ ] T006 [US1] Create `tests/guards/test_release_scripts.py` with a module-level `pytest.mark.skipif(shutil.which("sh") is None, ...)` following the missing-`uv` skip pattern in `tests/guards/test_packaging.py`, a helper that writes a fixture changelog into `tmp_path`, and the first failing case for `scripts/changelog-section.sh`: a section that is the last in the file and runs to end of file (contract case 1, the case the first release actually exercises). Confirm it fails because the script does not exist.
- [ ] T007 [US1] Create `scripts/changelog-section.sh` (`#!/usr/bin/env sh`, no bashisms) taking `<version> <changelog-path>`, printing every line after the `## <version>` heading to end of file with leading and trailing blank lines trimmed and the heading line itself omitted. An `awk` state machine is the intended shape. Make T006 pass.
- [ ] T008 [US1] Add the failing case for a section followed by another `## ` heading (contract case 2) to `tests/guards/test_release_scripts.py`, then extend `scripts/changelog-section.sh` to stop at the next `## ` line.
- [ ] T009 [US1] Add the failing prefix-collision case (contract case 8: `2026.08.1` must not select `## 2026.08.10`) to `tests/guards/test_release_scripts.py`, then anchor the heading match in `scripts/changelog-section.sh` so `## <version>` must be followed by end-of-line or whitespace.
- [ ] T010 [US1] Add the failing exit-code cases to `tests/guards/test_release_scripts.py` — absent section is exit 1 with the version and the file named on stderr and nothing on stdout, wrong argument count or a nonexistent changelog path is exit 2 with usage — then implement both in `scripts/changelog-section.sh`.
- [ ] T011 [US1] Add the remaining extractor cases to `tests/guards/test_release_scripts.py` (contract cases 4, 5, 6, 7: an `(unreleased)` heading is still found, a dated heading is still found, `###` subsection headings are reproduced intact, interior blank lines survive while the leading and trailing ones are trimmed) and make each pass in `scripts/changelog-section.sh`.

### The preflight (`contracts/release-scripts.md`)

- [ ] T012 [US1] Add the failing tag-shape cases to `tests/guards/test_release_scripts.py` (contract case 3: `2026.08.1`, `vv2026.08.1`, `v2026.8.1`, `v2026.13.1`, `release-2026.08.1` each exit 1), then create `scripts/release-preflight.sh` (`#!/usr/bin/env sh`) taking `<tag> <pyproject-path> <changelog-path>` and implementing check 1 — one `v` followed by a `YYYY.0M.INC1` string.
- [ ] T013 [US1] Add the failing declared-version cases to `tests/guards/test_release_scripts.py` (a tag that disagrees exits 1 with a message naming both `v2026.08.2` and `2026.08.1`; contract case 8's fixture whose `[tool.x]` table also carries a `version =` line is read correctly), then implement check 2 in `scripts/release-preflight.sh` with an `awk` state machine over table headers that reads `version` from the `[project]` table specifically.
- [ ] T014 [US1] Add the failing changelog cases to `tests/guards/test_release_scripts.py` (contract cases 4 and 5: no `## <version>` heading exits 1; a heading carrying `(unreleased)` or carrying no ISO date exits 1), then implement checks 3 and 4 in `scripts/release-preflight.sh` as two separate checks with two distinct messages.
- [ ] T015 [US1] Add the failing empty-body case to `tests/guards/test_release_scripts.py` (contract case 9: a dated heading followed immediately by the next `## ` heading, and one followed only by blank lines to end of file, both exit 1 naming the empty section), then implement check 5 in `scripts/release-preflight.sh`.
- [ ] T016 [US1] Add the failing argument and happy-path cases to `tests/guards/test_release_scripts.py` (contract cases 7 and 1: a missing `pyproject.toml` or `CHANGELOG.md` exits 2; a well-formed tag over a dated, non-empty section exits 0 with no output once check 6 is stubbed out), then finish those paths in `scripts/release-preflight.sh`.
- [ ] T017 [US1] Implement check 6 in `scripts/release-preflight.sh` using the T004 finding: `gh release view "$TAG"` aborts when a release exists **and** when the question could not be answered (FR-025 fails closed). Make the command overridable by an environment variable so the first five checks are testable without `gh`, and state the override in the script's header comment as `contracts/release-scripts.md` requires. Add the tests for both outcomes to `tests/guards/test_release_scripts.py` first.

### The fixed footer (FR-021)

- [ ] T018 [US1] Add a failing guard to `tests/unit/test_licensing.py` asserting `.github/release-footer.md` exists and contains the module's own `ATTRIBUTION` constant and one of its `NON_AFFILIATION_PHRASES`, reusing those constants rather than restating the strings (research.md R9).
- [ ] T019 [US1] Create `.github/release-footer.md` carrying the exact attribution string and a non-affiliation statement, making T018 pass.

### The workflow (`contracts/release-workflow.md`)

- [ ] T020 [US1] Add a failing guard for the workflow's *prohibitions* in a new `tests/guards/test_release_workflow.py`, asserting that `.github/workflows/release.yaml` exists, triggers only on `push:` `tags: ['v*']`, grants exactly `contents: write`, `id-token: write`, and `attestations: write`, carries no `continue-on-error` anywhere, and contains none of `gh release edit`, `gh release upload`, `--clobber`, `--draft`, or `--generate-notes`.
- [ ] T020a [US1] Add the failing guard for the workflow's *required steps* to `tests/guards/test_release_workflow.py`. Everything T020 asserts is an absence; a `release.yaml` that simply omitted the preflight, ran a filtered suite, or forgot the footer would pass it, and the only remaining backstop would be a maintainer reading the release page at T062. Assert instead that the workflow: checks out the pushed tag rather than a branch tip (FR-004); invokes `scripts/release-preflight.sh` (FR-007, FR-008, FR-025); runs `pytest` with no `-m` filter and no `--deselect`, `-k`, or path argument narrowing the run (FR-005); and assembles its notes file from both `scripts/changelog-section.sh` and `.github/release-footer.md`, with the footer written *after* the section body (FR-002, FR-021). Read `release.yaml` as text and match with anchored regexes, the way `tests/guards/test_python_support.py` already reads `ci.yaml`: no YAML parser is installed, and adding one would be a dev dependency bought for a single assertion (Principle VI).
- [ ] T021 [US1] Create `.github/workflows/release.yaml` with the ten steps of `contracts/release-workflow.md` in order — checkout at the tag, `astral-sh/setup-uv` with Python 3.13, `sh scripts/release-preflight.sh "$GITHUB_REF_NAME" pyproject.toml CHANGELOG.md`, `uv sync`, `uv run pytest` with no `-m` filter, `uv build`, `sha256sum cetools-* > SHA256SUMS.txt` inside `dist/`, `actions/attest-build-provenance` over `dist/cetools-*`, the notes file assembled from `scripts/changelog-section.sh` plus `.github/release-footer.md`, and a single `gh release create ... --verify-tag` — using the T005 pins. Make T020 and T020a pass.

### Release procedure documentation (FR-013, FR-014, FR-010)

- [ ] T022 [US1] Rewrite the "Changelog and releases" section of `CONTRIBUTING.md` in place (no new file) to state the tagging sequence, the changelog-dating step, the step that updates every documented occurrence of the version, and the month-rollover rule that requires bumping the version before tagging when the declared month is no longer the current month (research.md R16, R17; SC-016). This is the same edit that removes "Releases are published to PyPI." from that section.

### Story validation

- [ ] T023 [US1] Run quickstart.md scenarios 1, 2, and 3 by hand and confirm each message is legible: a preflight failure must name both values ("tag v2026.08.2 does not match the declared version 2026.08.1"), not merely report a mismatch.
- [ ] T024 [US1] Add the `CHANGELOG.md` entry for the release mechanism under the declared version's section, in the same commit as the change it describes.

**Checkpoint**: the release mechanism exists and is tested; the first release
can be cut once US2 and US3 land (they change the same commit's README).

---

## Phase 4: User Story 2 - Install the released tool (Priority: P1)

**Goal**: the README's primary installation instruction points at the
published artifact, an alternative installs from the tagged source, and no
project document sends a reader to a package index that has never carried this
package.

**Independent Test**: quickstart.md scenario 9 — follow the primary
instruction on a machine with no prior install, confirm `cetools --version`
reports the released version, then follow the alternative and confirm the
same.

- [ ] T025 [US2] Replace the `uv add cetools` fence at `README.md:12` with three instructions, each carrying the current version in the spelling its position requires (research.md R15, R2): the primary `uv tool install https://github.com/lgw4/cetools/releases/download/v<declared>/cetools-<reported>-py3-none-any.whl` (FR-016); the source alternative `uv tool install git+https://github.com/lgw4/cetools@v<declared>` (FR-017); and, for a project depending on the library rather than installing the command, `uv add <the same wheel URL>` (FR-026). The third exists because Principle I makes the library the primary artifact, and a section documenting only `uv tool install` leaves a library consumer with nothing to follow.
- [ ] T026 [US2] Sweep for any remaining instruction that installs from a package index — `rg -n 'uv add cetools|pip install cetools' README.md CONTRIBUTING.md` — and remove or correct each (FR-018).
- [ ] T027 [US2] Update the two remaining superseded PyPI references in `CONTRIBUTING.md` (the "the README is the description PyPI…" line near line 101 and the "README, PyPI description, CLI help" list near line 211) to name the public release page and the built package's description, matching the amended constitution's Licensing section (FR-024). Leave `specs/` and `wayfinder/` untouched: they are historical records and FR-024 excludes them.
- [ ] T028 [US2] Add the `CHANGELOG.md` entry for the installation documentation change.

**Checkpoint**: the README tells a reader something that will be true the
moment the release exists.

---

## Phase 5: User Story 3 - A wrong release is refused, not shipped (Priority: P1)

**Goal**: a stale version anywhere in the documented outputs — including both
spellings inside the new installation command — fails the test suite, and the
test suite gates publication.

**Independent Test**: quickstart.md scenario 4, including its third leg: swap
the two spellings between the tag segment and the filename segment and confirm
both positions fail. If that swap passes, the guard is normalizing before
comparing and FR-012 is not satisfied.

**Note on scope**: the two abort legs of this story (a disagreeing tag, an
undated changelog heading) are the preflight checks delivered in US1 by
T012–T015; this phase delivers the third leg and the guard that carries it.

- [ ] T029 [US3] **(structural)** Split the single `_PATTERNS` tuple in `tests/guards/test_documented_version.py` into two named groups with no behavior change — a reported group holding the existing `\(cetools ([^)]+)\)` and `"version": "([^"]+)"` patterns, and an empty declared group — and route both tests through the grouped structure. Run the suite before and after to confirm nothing changed. Commit alone.
- [ ] T030 [US3] Add the failing cases to `tests/guards/test_documented_version.py`: a stale value in the `releases/download/v(...)/` tag segment fails naming `README.md` and the stale value; a stale value in the wheel-filename segment fails against the **reported** form; and the two spellings swapped fails in both positions (research.md R13, FR-012). Confirm they fail against the current guard.
- [ ] T031 [US3] Extend `tests/guards/test_documented_version.py` so the reported group also matches the wheel filename in the install command and is compared against `package_version()`, while the new declared group matches the `releases/download/v(...)/` segment and the `@v(...)` source-install ref and is compared against `project.version` read from `pyproject.toml`. Make T030 pass.
- [ ] T032 [US3] Update `test_the_guard_has_something_to_check` in `tests/guards/test_documented_version.py` so each group must have matched at least once and every match in a group must equal that group's expected value, preserving the property that a glob or a pattern matching nothing fails.
- [ ] T033 [US3] Run quickstart.md scenario 4 end to end, including the swap leg, and revert each edit afterward.
- [ ] T034 [US3] Add the `CHANGELOG.md` entry for the extended drift guard.

**Checkpoint**: US1, US2, and US3 are complete; the first release can be cut.

---

## Phase 6: User Story 4 - The released package carries the metadata a public artifact needs (Priority: P2)

**Goal**: both distributions carry keywords, classifiers, repository links,
and the PEP 561 marker, verified by a packaging guard rather than by
inspection.

**Independent Test**: quickstart.md scenario 6 — build, confirm
`cetools/py.typed` in the wheel and `src/cetools/py.typed` in the sdist, and
the `Keywords`, `Classifier`, and `Project-URL` lines in both the wheel's
`METADATA` and the sdist's `PKG-INFO`, with no `Classifier: License ::` line
in either.

- [ ] T035 [P] [US4] Verify every classifier in `contracts/package-metadata.md` against the canonical trove list (`Development Status :: 4 - Beta`, `Environment :: Console`, `Intended Audience :: End Users/Desktop`, `Operating System :: OS Independent`, `Programming Language :: Python :: 3.13`, `Programming Language :: Python :: 3.14`, `Topic :: Games/Entertainment :: Role-Playing`, `Typing :: Typed`); nothing in this repository catches a misspelling.
- [ ] T036 [US4] Add the failing `py.typed` guards to `tests/guards/test_packaging.py`: `cetools/py.typed` is a member of the wheel, and `<name>-<version>/src/cetools/py.typed` is a member of the sdist (FR-020).
- [ ] T037 [US4] Create an empty `src/cetools/py.typed` — no content, not even a comment (research.md R11) — making T036 pass and confirming hatchling's `packages = ["src/cetools"]` carries it with no `pyproject.toml` change.
- [ ] T038 [US4] Add the failing metadata guards to `tests/guards/test_packaging.py`, at the shape `contracts/package-metadata.md` recommends: a non-empty `Keywords` line, at least one `Classifier` line, `Project-URL` entries for the repository, the changelog, and the issue tracker, no `Classifier: License ::` line, and neither `Cepheus Engine` nor `Samardan Press` in `Keywords` or any `Classifier`. Do not pin the exact classifier list. Run every assertion against **both** formats — the wheel's `cetools-<version>.dist-info/METADATA` and the sdist's `<name>-<version>/PKG-INFO` — because SC-014 binds both, and a build-backend change that dropped a field from one and not the other is exactly what a one-format guard would miss. Factor the field extraction into a helper taking the metadata text so both legs share it.
- [ ] T039 [US4] Add `keywords`, `classifiers`, `authors = [{ name = "Chip Warden" }]` (name only; research.md R22), and a `[project.urls]` table with `Homepage`, `Repository`, `Changelog`, and `Issues` to `pyproject.toml`'s `[project]` section per `contracts/package-metadata.md`, leaving `license`, `license-files`, and `description` untouched. Make T038 pass.
- [ ] T040 [US4] Extend `tests/guards/test_python_support.py` so it also holds the two `Programming Language :: Python ::` classifiers in step with `requires-python` and `ci.yaml`'s matrix — failing test first. `contracts/package-metadata.md` left this open; it is settled yes, because those three already drift independently and that guard exists for exactly that drift. Derive the expected classifier set from the matrix the guard already parses rather than restating the versions.
- [ ] T041 [US4] Add the `CHANGELOG.md` entry for the package metadata and the `py.typed` marker.

**Checkpoint**: an inspection tool pointed at the built artifact finds what a
published package is expected to carry.

---

## Phase 7: User Story 5 - The build is guarded against a flattened layout (Priority: P2)

**Goal**: a build whose rules-data files sit at paths other than the source
tree's fails the packaging guard, for both distribution formats, with the
differing paths named.

**Independent Test**: quickstart.md scenario 5 — a worktree whose data files
are flattened fails both guards under the tightened comparison and passes
under the current one.

- [ ] T042 [US5] **(structural)** Extract the source-versus-archive comparison in `tests/guards/test_packaging.py` into a helper taking the two sets and returning the differing paths, and route `test_wheel_contains_every_packaged_data_file` and `test_sdist_contains_every_packaged_data_file` through it with their current basename behavior unchanged. Run the suite before and after. Commit alone.
- [ ] T043 [US5] Add a failing unit case for that helper in `tests/guards/test_packaging.py` using a synthetic flattened input — every basename present, every path different — asserting it reports the differing paths rather than an empty difference (FR-015, SC-010).
- [ ] T044 [US5] Change both `test_wheel_contains_every_packaged_data_file` and `test_sdist_contains_every_packaged_data_file` in `tests/guards/test_packaging.py` to compare full relative paths: the source side as each `.toml` under `src/cetools/data/` relative to `src/cetools/`, the wheel side as each member under `cetools/data/` with that prefix stripped, the sdist side as each member under `<name>-<version>/src/cetools/data/` with the version prefix and `src/cetools/` stripped (research.md R12). The failure message names the differing paths, not a set inequality.
- [ ] T045 [US5] Run quickstart.md scenario 5 in a throwaway worktree and confirm both guards fail on the flattened layout and pass on the real tree, then remove the worktree.
- [ ] T046 [US5] Add the `CHANGELOG.md` entry for the tightened packaging guard.

**Checkpoint**: a layout change the loader could not read fails at
build-inspection time.

---

## Phase 8: User Story 6 - A type checker is available but not mandatory (Priority: P3)

**Goal**: `mypy` is installed by the standard environment setup and documented
alongside the other optional tooling, and it gates nothing.

**Independent Test**: `uv run mypy src/cetools` runs from a fresh checkout,
and introducing a type error fails neither `uv run pytest` nor `ci.yaml`.

**⚠️ Read `tests/guards/test_lint_commands.py` first.** It asserts the
commands in `CONTRIBUTING.md`'s "Style and tooling" `sh` fence are exactly
`{black, isort, flake8}` **and that each reports clean**. Documenting mypy
inside that fence would make a clean mypy run a suite gate, which FR-022 and
Principle III both forbid. T047 exists to settle that before anything is
documented.

- [ ] T047 [US6] Decide how `mypy` is documented without entering the guarded fence in `tests/guards/test_lint_commands.py` — a separate fence outside the `## Style and tooling` … first-```sh``` window the `_FENCE` regex captures, or an explicit exemption in the guard — and add the failing test for whichever shape is chosen, so the non-gating property is itself held by a test.
- [ ] T048 [US6] Add `mypy` to the `dev` dependency group in `pyproject.toml` and a `[tool.mypy]` table beside the existing `[tool.black]`, `[tool.isort]`, and `[tool.rumdl]` tables. Change nothing in `[tool.pytest.ini_options]` and nothing in `.github/workflows/ci.yaml`.
- [ ] T049 [US6] Document the type checker and its invocation in `CONTRIBUTING.md`'s "Style and tooling" section in the shape T047 chose, stating plainly that it gates nothing, exactly as the section already says of `rumdl`. Make T047 pass.
- [ ] T050 [US6] Run `uv run mypy src/cetools`, record the baseline error count in the task notes, and fix only what is cheap. A clean run is explicitly **not** a deliverable (research.md R10, FR-022).
- [ ] T051 [US6] Confirm the non-gating property directly: introduce a deliberate type error, run `uv run pytest`, confirm it still passes, and revert.
- [ ] T052 [US6] Add the `CHANGELOG.md` entry for the optional type checker.

**Checkpoint**: a contributor who wants type checking has it; one who does not
is not blocked by it.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [ ] T053 Run the full suite with no filter — `uv run pytest` — and confirm it is green, including `tests/guards/test_release_scripts.py` running rather than skipping (quickstart.md scenario 1).
- [ ] T054 [P] Run the documented lint commands from `CONTRIBUTING.md`'s "Style and tooling" fence and confirm each reports clean.
- [ ] T055 [P] Run `rumdl check .` over the markdown this feature added and edited (`CONTRIBUTING.md`, `README.md`, `CHANGELOG.md`, `.github/release-footer.md`) and fix what it reports.
- [ ] T056 Confirm `CHANGELOG.md` carries an entry for every user-visible change in this feature, that each sits under the right `###` heading, and that the declared version's section is non-empty — the preflight's check 5 refuses a dated section with nothing in it.
- [ ] T057 Confirm `scripts/` is still absent from `[tool.hatch.build.targets.sdist]`'s `include` list in `pyproject.toml`, and that `tests/guards/test_packaging.py::test_sdist_ships_no_file_outside_its_own_include_list` still passes: the release scripts are maintainer tooling and must not ship.

---

## Phase 10: Release Execution (the first release, SC-012)

**Purpose**: cut the release this feature exists to make. Maintainer action,
after everything above is merged to `main` and `ci.yaml` is green.

- [ ] T058 Confirm the declared version's month is the current month; if it is not, bump `project.version` in `pyproject.toml` and take the `## ` heading in `CHANGELOG.md` and every documented occurrence with it (FR-010), then re-run `uv run pytest tests/guards/test_documented_version.py`.
- [ ] T059 Date the declared version's `## <version> (unreleased)` heading in `CHANGELOG.md`, commit, and push to `main`; wait for `ci.yaml` to go green.
- [ ] T060 Push the version tag — `git tag v<declared>` then `git push origin v<declared>` — and take no further action (quickstart.md scenario 7, SC-001).
- [ ] T061 Verify the published release against quickstart.md scenario 8: download the assets, run `sha256sum -c SHA256SUMS.txt` (or `shasum -a 256 -c`), and run `gh attestation verify` on each of the two distribution artifacts.
- [ ] T062 Verify the release body: its text is the changelog section verbatim, it ends with the footer, and it carries no checksums, download links, or generated commit list (FR-002, research.md R7).
- [ ] T063 Verify the installation instructions as a reader would, per quickstart.md scenario 9: the primary wheel URL resolves, `cetools --version` reports the released version, the worked example in the README reproduces, the `git+…@v<tag>` alternative installs the same version, and the `uv add` dependency line resolves in a throwaway project with `import cetools` succeeding (FR-026).
- [ ] T064 Verify the already-published refusal per quickstart.md scenario 10: capture `gh release view --json publishedAt,assets`, force-push the same tag, confirm the run aborts at the preflight naming the version as already published, and confirm the release is byte-identical afterward (FR-025, SC-013).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup. Blocks US1 (T004, T005) and US5 (T003).
- **US1 (Phase 3)**: depends on Foundational. Delivers both scripts, the footer, the workflow, and the release procedure.
- **US2 (Phase 4)**: depends on Foundational only. Independent of US1.
- **US3 (Phase 5)**: depends on US2 for the install command its new patterns match. The two abort legs it validates are US1's T012–T015.
- **US4 (Phase 6)**: depends on Foundational only.
- **US5 (Phase 7)**: depends on T003.
- **US6 (Phase 8)**: depends on Foundational only.
- **Polish (Phase 9)**: depends on every story that is being shipped.
- **Release Execution (Phase 10)**: depends on US1, US2, and US3 being merged to `main`. US4, US5, and US6 are not required for the first release, but nothing prevents them shipping in it.

### Within Each Story

Test first, watch it fail, implement, run the whole suite. One test at a time.
Structural tasks (T029, T042) commit alone and before the behavioral change
they enable.

### Parallel Opportunities

- T003, T004, T005 are three independent lookups and can run together.
- US2 (T025–T028), US4 (T035–T041), US5 (T042–T046), and US6 (T047–T052) touch disjoint files and can proceed in parallel once Phase 2 is done. US1 and US3 are the only pair with an ordering constraint between stories, through the README.
- Within US1, T006–T011 (the extractor) and T018–T019 (the footer) are independent of each other; T012–T017 (the preflight) depend on nothing in the extractor except that both are exercised from the same test module, so keep them sequential to avoid conflicting edits to `tests/guards/test_release_scripts.py`.
- T035 (classifier verification) and T054/T055 (lint runs) are independent of everything around them.

### Files with Multiple Writers

Serialize edits to these rather than parallelizing across them:

- `tests/guards/test_release_scripts.py` — T006, T008–T017
- `tests/guards/test_release_workflow.py` — T020, T020a
- `tests/guards/test_packaging.py` — T036, T038, T042–T044
- `tests/guards/test_documented_version.py` — T029–T032
- `pyproject.toml` — T039, T048
- `CONTRIBUTING.md` — T022, T027, T049
- `CHANGELOG.md` — T024, T028, T034, T041, T046, T052, T056, T059

---

## Parallel Example: Phase 2

```bash
Task: "Confirm test_data_file_basenames_are_unique owns basename uniqueness"
Task: "Determine gh release view's not-found versus cannot-answer signals"
Task: "Confirm the pins for checkout, setup-uv, and attest-build-provenance"
```

## Parallel Example: after Phase 2, with capacity

```bash
Task: "US2 — README installation instructions (T025–T028)"
Task: "US4 — package metadata and py.typed (T035–T041)"
Task: "US5 — full-path packaging guard (T042–T046)"
Task: "US6 — optional mypy (T047–T052)"
```

---

## Implementation Strategy

### MVP (the first release)

1. Phase 1 and Phase 2.
2. Phase 3 (US1) — the mechanism.
3. Phase 4 (US2) — the installation instructions that ship with it.
4. Phase 5 (US3) — the guard that keeps them true.
5. **STOP and VALIDATE**: quickstart scenarios 1 through 4 pass locally.
6. Phase 9, then Phase 10 — cut the release.

That is SC-012: the first release cetools has ever published.

### Incremental Delivery

US4, US5, and US6 are P2/P3 and each is independently shippable, before or
after the first release. If they land before Phase 10, they ship in it; if
after, they ship in the next increment, with a changelog entry, and the
published version number is not reused (FR-009).

---

## Notes

- Nothing in `scripts/` or `.github/` ships. The single new file inside `src/` is `py.typed`, which exists precisely in order to ship.
- The version has three spellings and each belongs in one position: declared `2026.08.1` (`pyproject.toml`, the `## ` heading, the tag with `v` stripped, the release URL path), reported `2026.8.1` (`importlib.metadata`, artifact filenames), and tag `v2026.08.1`. Getting one wrong in the install command hands a reader a 404 under a version number that is already spent.
- The release body carries no checksums. FR-002 fixes it as the changelog section plus the fixed footer and nothing else; the checksums live in `SHA256SUMS.txt` (research.md R7).
- No pytest guard compares the declared month against the current month (research.md R17); the month-rollover rule is documented in `CONTRIBUTING.md` and enforced by the maintainer at T058.
- A clean `mypy` run is not a deliverable of this feature, and no task may make it one.
