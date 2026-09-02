# Feature Specification: Release Publishing

**Feature Branch**: `005-release-publishing`

**Created**: 2026-08-31

**Status**: Draft

**Input**: User description: "cetools needs a defined way to cut a release, which it has never done: version 2026.08.1 sits declared but unreleased, no tag exists, and the only automation runs tests. This feature establishes what a release is for this project, produces the first one, and fixes the packaging metadata that a publicly distributed artifact is expected to carry."

## Clarifications

### Session 2026-08-31

- Q: When a release is published, should the trademark attribution and
  non-affiliation statement be added to the release page alongside the
  changelog text, or must the changelog text alone stand as the release
  notes? (FR-002 vs FR-021) → A: The release notes are the changelog section
  verbatim, followed by a fixed attribution/non-affiliation footer that the
  release automation appends; "verbatim" is scoped to the changelog-derived
  body.
- Q: When a version tag is pushed for a version that has already been
  published, what must the release attempt do? (FR-009) → A: Check for an
  existing published release of that version, abort before publishing
  anything, and report that the version is already published.
- Q: Should each published artifact get its own checksum file, or should one
  combined checksum file cover all artifacts in the release? (FR-006,
  SC-002) → A: One combined checksum file listing every artifact, one line
  per artifact, verifiable in a single stock-tool command.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cut a release by pushing a tag (Priority: P1)

A maintainer has finished the work that belongs in a version. They date the
changelog heading for that version, confirm the declared version still names
the current month, commit, and push a version tag. Everything after the tag
is automatic: a clean machine checks out exactly the tagged commit, runs the
full test suite, builds both distribution formats, and publishes them on the
project's public repository as a release announced with that version's
changelog text. Alongside the artifacts sit a plain checksum anyone can
verify and a signed record tying each artifact to the commit and build that
produced it.

**Why this priority**: This is the feature. Without it the project has no
way to ship anything, and every other story here is a refinement of a
release that does not yet exist.

**Independent Test**: Push a version tag at a commit whose declared version
and dated changelog heading agree with it, and confirm a public release
appears carrying both formats, checksums, provenance, and the changelog text
as its notes — with no manual step between the push and the published
release.

**Acceptance Scenarios**:

1. **Given** a commit whose declared version is `2026.08.1` and whose
   changelog carries a dated `## 2026.08.1` heading, **When** the matching
   version tag is pushed, **Then** a public release for that version is
   published carrying a source distribution, a built distribution, a
   checksum file, a signed provenance record, and release notes whose body
   is that changelog section verbatim, followed by the fixed attribution and
   non-affiliation footer.
2. **Given** the same commit, **When** the release runs, **Then** the build
   and the test run both happen on a clean machine checked out at the tagged
   commit, not on any maintainer's working tree.
3. **Given** a tagged commit whose test suite fails, **When** the release
   runs, **Then** nothing is published and the failure is reported.
4. **Given** a release has been published for a version, **When** anyone
   downloads an artifact, **Then** its checksum can be verified against the
   release's combined checksum file with tools present on a stock system,
   and its provenance record identifies the exact source commit and build
   that produced it.

---

### User Story 2 - Install the released tool (Priority: P1)

Someone who wants to use cetools reads the README's installation
instruction, runs it, and ends up with the released version installed. The
instruction names the published artifact, because no package index carries
this project. A second instruction covers installing from the tagged source
for anyone who prefers to build it themselves.

**Why this priority**: The README currently tells readers to install from a
package index that has never carried this package. That instruction is false
today, and it stays false the moment a release exists unless it is replaced —
so it ships with the first release, not after it.

**Independent Test**: Follow the README's primary installation instruction
on a machine with no prior cetools install and confirm the released version
is installed and the `cetools` command runs; then follow the alternative
instruction from the tagged source and confirm the same.

**Acceptance Scenarios**:

1. **Given** a published release, **When** a reader runs the README's
   primary installation command, **Then** the released version installs and
   `cetools --version` reports it.
2. **Given** a published release, **When** a reader follows the alternative
   source instruction against the release tag, **Then** the same version is
   built and installed.
3. **Given** the README, **When** a reader looks for how to install,
   **Then** no instruction directs them to a package index that does not
   carry this package.
4. **Given** a reader who wants the library rather than the command, **When**
   they follow the README's dependency instruction, **Then** the released
   version is added to their project and `import cetools` resolves to it.

---

### User Story 3 - A wrong release is refused, not shipped (Priority: P1)

A release attempt that would ship something wrong stops before publishing
anything. A tag that names a different version than the one declared in the
project's metadata aborts. A tag pushed while the changelog heading for that
version still marks itself unreleased aborts, because that same section is
the announcement text and would go out saying "unreleased". A stale version
string anywhere in the documented outputs — including the installation
command, where a stale value hands a reader a download link that 404s — fails
the test suite, and the test suite gates publication.

**Why this priority**: The value of an automatic release is that a mistake
fails loudly instead of shipping. Each of these three has already been
identified as a recurring failure mode, and each produces a defect that
cannot be fixed in place, because a published version number is spent.

**Independent Test**: Attempt a release three ways — with a tag that
disagrees with the declared version, with an undated changelog heading, and
with a stale version in the installation command — and confirm each attempt
publishes nothing and reports why.

**Acceptance Scenarios**:

1. **Given** a declared version of `2026.08.1`, **When** a tag naming
   `2026.08.2` is pushed, **Then** the release aborts before publishing
   anything and reports the disagreement.
2. **Given** a changelog whose heading for the declared version still marks
   itself unreleased, **When** the matching tag is pushed, **Then** the
   release aborts before publishing anything.
3. **Given** an installation command in the README naming a version other
   than the one the project declares, **When** the test suite runs, **Then**
   it fails and names the stale value and the file it sits in.
4. **Given** a version that has already been published, **When** a defect in
   it is found, **Then** the fix ships as the next increment with a
   changelog entry explaining what was wrong, and the published version
   number is not reused.

---

### User Story 4 - The released package carries the metadata a public artifact needs (Priority: P2)

Someone looking at the released package — its metadata, its release page, or
the output of an inspection tool — finds a description, keywords,
classifiers, and links back to the source, the changelog, and the issue
tracker. Where the package's public-facing text claims compatibility with the
rules system it implements, it carries the attribution and non-affiliation
statement the project's licensing obligations require. A type checker
consuming the installed package sees its annotations instead of treating it
as untyped.

**Why this priority**: This is what distinguishes a distributed artifact
from a local build, and the first release is the moment it starts to matter.
It is separable from the release mechanism itself: the release can be cut
without it, and it can be completed without a release existing.

**Independent Test**: Build the distributions and inspect their metadata for
the descriptive fields, the repository links, and the type-annotation marker;
read the published release page for the compatibility and non-affiliation
statement.

**Acceptance Scenarios**:

1. **Given** a built distribution, **When** its metadata is inspected,
   **Then** it carries a description, keywords, classifiers, and links to
   the source repository, the changelog, and the issue tracker.
2. **Given** a built distribution, **When** a type checker consumes the
   installed package, **Then** the package's annotations are visible to it
   rather than the package being treated as unannotated.
3. **Given** any public-facing text that claims compatibility with the rules
   system — including the published release page — **When** it is read,
   **Then** it carries the required trademark attribution and a statement of
   non-affiliation.

---

### User Story 5 - The build is guarded against a flattened layout (Priority: P2)

The rules data ships in nested directories. A build that flattened those
directories into one would still contain every file by name, so the existing
packaging guard would pass it. The guard is tightened to compare full paths,
so a layout change that the loader could not read fails at build-inspection
time.

**Why this priority**: A latent hole in an existing guard, not a new
capability. It matters more once builds are published rather than discarded,
but it does not block the first release.

**Independent Test**: Compare the guard's behavior against a build whose data
files sit at a different depth than the source tree; the tightened guard
fails it, the current one passes it.

**Acceptance Scenarios**:

1. **Given** a build whose rules-data files are present but at flattened
   paths, **When** the packaging guard runs, **Then** it fails and names the
   paths that differ.
2. **Given** a correct build, **When** the packaging guard runs, **Then** it
   passes for both distribution formats.

---

### User Story 6 - A type checker is available but not mandatory (Priority: P3)

A contributor who wants static type checking finds it configured and
documented, runs it locally, and gets useful output. A contributor who does
not want it is not blocked by it: it gates nothing, exactly as the project's
markdown linter already does.

**Why this priority**: A convenience for contributors that changes nothing
about what ships. The project's own governing principle declines to mandate
tooling gates beyond tests, so this must be optional by construction.

**Independent Test**: Run the documented type-check command from a fresh
checkout and confirm it runs; then confirm that its failure does not fail
the test suite or any merge gate.

**Acceptance Scenarios**:

1. **Given** the contributor documentation, **When** a contributor looks for
   how to type-check, **Then** the tool and its invocation are documented
   alongside the other optional tooling.
2. **Given** a type error in the source, **When** the test suite and the
   merge gate run, **Then** neither fails on account of it.

---

### Edge Cases

- **A tag points at an unexpected commit.** The release builds and tests the
  tagged commit rather than any branch tip, so a tag on a commit whose tests
  fail, or whose declared version disagrees with the tag, aborts rather than
  shipping.
- **The month rolls over between dating the changelog and tagging.** The
  declared version's month no longer names the current month. The release
  procedure requires bumping the version before tagging rather than shipping
  a version stamped with a month that has passed.
- **A tag is pushed for a version already published.** The version number is
  spent. The attempt detects the existing release, aborts before publishing
  anything, and reports that the version is already published; it never
  overwrites, replaces, or adds to the existing release.
- **A release fails partway.** Nothing is published unless the whole
  sequence succeeds, so a failed attempt leaves the version number available
  for a retry. This is the single exception to the never-reuse rule: a build
  that failed before publishing anything published nothing. Retrying means
  correcting the commit and moving the tag onto it, then pushing the tag
  again; a tag that already exists is not itself evidence that the version is
  spent, because only a published release spends it.
- **The changelog has no section for the declared version at all.** There is
  no announcement text to publish, and the release aborts.
- **The changelog section is dated but empty.** Dating alone does not make an
  announcement. The release aborts rather than publishing notes that are the
  attribution footer and nothing else.
- **A version heading is a prefix of a longer one.** `## 2026.08.1` and
  `## 2026.08.10` are different versions, and selecting the section for one
  must never match the other. Getting this wrong ships the wrong
  announcement text under a correct version number, which the never-reuse
  rule makes unfixable in place.
- **A tag that does not parse as a version.** It does not trigger a release,
  or it aborts; either way it publishes nothing.
- **The declared and reported version strings differ in form.** The declared
  form is zero-padded (`2026.08.1`) and the form the packaging metadata
  reports drops the padding (`2026.8.1`). Both forms appear in the
  installation command — the tag in the URL path, the normalized form in the
  artifact filename — so the drift guard must accept the correct value in
  each position rather than one string everywhere.

## Requirements *(mandatory)*

### Functional Requirements

#### What a release is

- **FR-001**: A release MUST be a tagged, immutable bundle published on the
  project's public source repository, carrying both a source distribution
  and a built distribution.
- **FR-002**: A release MUST be announced with the changelog text for that
  version, reproduced verbatim as the body of the release notes. That
  changelog text is the section's *body* — every line below the version
  heading, up to the next version heading or the end of the file — and not the
  heading line itself, which the release title already carries. "Verbatim"
  means reproduced byte for byte, with leading and trailing blank lines
  trimmed and nothing else altered: no reflowing, reformatting, summarizing,
  or re-ordering. The release automation MUST append a fixed attribution and
  non-affiliation footer (FR-021) below that body; nothing else may be added,
  and the changelog-derived body itself MUST NOT be edited or summarized.
- **FR-003**: Pushing a version tag MUST be the only trigger that publishes
  a release, and every step after the tag MUST be automatic, requiring no
  further maintainer action.
- **FR-004**: The build and the test run MUST happen on a clean machine
  provisioned fresh for that release run and discarded after it, checked out
  at the tagged commit, never on a maintainer's working tree and never on a
  machine carrying state from a previous run.
- **FR-005**: The full test suite MUST run against the tagged commit and
  MUST pass before anything is published; a failure MUST abort the release
  with nothing published. "Full" excludes nothing: the marker-based and
  path-based filters the contributor documentation recommends for the inner
  loop MUST NOT be applied here.
- **FR-006**: Every published artifact MUST be covered by a plain checksum a
  user can verify with no special tooling, and MUST carry a signed
  provenance record binding the artifact to the exact source commit and
  build that produced it. The checksums MUST be published as a single
  combined file carrying one line per artifact, verifiable in one command
  with a stock checksum utility. A "published artifact" here means a
  distribution artifact. The combined checksum file is not one: it does not
  list itself, and it carries no provenance record of its own.

#### What blocks a release

- **FR-007**: The version declared in the project metadata MUST be the
  single authority for what version is being released; the pushed tag MUST
  agree with it, and a disagreement MUST abort the release before anything
  is published.
- **FR-008**: A release MUST be blocked unless the changelog heading for the
  declared version carries a release date. A heading that still marks itself
  unreleased, and a heading carrying no date at all, MUST each abort the
  release, because that section is the announcement text. A dated heading
  whose section body is empty MUST abort for the same reason: there is
  nothing to announce.
- **FR-009**: A version number MUST never be reused. Once a version is
  published it is spent; a defect in it ships as the next increment,
  accompanied by a changelog entry stating what was wrong. The sole
  exception is a release attempt that failed before publishing anything.
- **FR-010**: The release procedure MUST require bumping the version before
  tagging when the current month no longer matches the month the declared
  version names.
- **FR-025**: The release MUST check whether a release for the declared
  version has already been published and, if one has, MUST abort before
  publishing anything and report that the version is already published. It
  MUST NOT overwrite, replace, or add artifacts to the existing release. The
  check MUST fail closed: an answer it cannot obtain — no network, no
  credential, or any other inconclusive result — MUST abort the release
  rather than be read as "no release exists".

#### Mechanical enforcement of the recurring failure modes

- **FR-011**: The existing documented-version drift guard MUST be extended
  to cover the README's installation command, so a stale version there fails
  the test suite rather than shipping a download instruction that resolves
  to nothing.
- **FR-012**: The drift guard MUST accept the declared zero-padded form
  where the tag appears and the normalized unpadded form where the artifact
  filename appears, rather than requiring one string in both positions.
- **FR-013**: Updating every documented occurrence of the version MUST be an
  explicit step in the release procedure, relying on the drift guard to fail
  loudly if the step is skipped.
- **FR-014**: The release procedure — including the tagging sequence, the
  changelog dating step, the version-update step, and the month-rollover
  rule — MUST live in the existing contributor documentation, not in a new
  file.
- **FR-015**: The existing packaging guard MUST compare the full relative
  paths of shipped rules-data files against the source tree rather than
  their file names alone, for both distribution formats, so a build that
  flattened the nested rules-data directories fails.

#### Installation documentation

- **FR-016**: The README's primary installation instruction MUST point at
  the published release artifact.
- **FR-017**: The README MUST offer installation from the tagged source as
  an alternative.
- **FR-018**: Project documentation MUST NOT direct a reader to install from
  a package index that does not carry this package.
- **FR-026**: The README MUST also carry an instruction for adding the
  released artifact as a project dependency, distinct from the two that
  install the command-line tool. Principle I makes the importable library the
  primary artifact and the CLI a thin consumer of it; an installation section
  documenting only the tool leaves the library's own consumer with nothing to
  follow. The declared and reported spellings are subject to FR-012 here as
  they are in the primary instruction.

#### Package metadata

- **FR-019**: The distribution metadata MUST carry the descriptive fields a
  released package is expected to have — keywords and classifiers alongside
  the existing description — and links to the source repository, the
  changelog, and the issue tracker.
- **FR-020**: The package MUST advertise that it ships type annotations, so
  a type checker consuming the installed package uses them rather than
  treating the package as unannotated. The marker MUST be present in both
  distribution formats, verified by a packaging guard.
- **FR-021**: Wherever the project's public-facing text claims compatibility
  with the rules system it implements — which now includes the published
  release page — it MUST carry the required trademark attribution and a
  statement of non-affiliation. On the release page this MUST arrive as a
  fixed footer appended by the release automation rather than as text
  maintained per version in the changelog, so no release can be published
  without it. The attribution is the exact Compatibility-Statement License
  string the constitution's Licensing & Distribution Constraints fixes, and
  the non-affiliation statement is one the project's existing licensing guard
  already recognizes; neither is reworded for the release page.

#### Development tooling

- **FR-022**: A type checker MUST be declared in the project's development
  dependency group, so a contributor gets it from the standard environment
  setup, and MUST be documented in the contributor documentation's tooling
  section with the command that invokes it. It MUST NOT gate the test suite,
  the merge check, or the release, and a clean run MUST NOT be a deliverable
  of this feature.

#### Governing-document prerequisite

- **FR-023**: The constitution MUST be amended before this feature is
  implemented, so that the ratified distribution channel is the tagged
  public release rather than a package index. The amendment MUST record
  index publication as the intended future path and MUST name the reserved
  package name in its rationale.
- **FR-024**: Every project document that describes how the project ships
  *today* and repeats the superseded "published to a package index" clause
  MUST be updated to match the amendment. That is the README and the
  contributor documentation. Completed feature artifacts under `specs/` and
  the pre-Spec-Kit planning notes under `wayfinder/` are historical records of
  what was decided when they were written, and are explicitly out of scope:
  amending them retroactively would falsify the record rather than correct
  it.

### Key Entities

- **Release**: A published, immutable bundle identified by a version. Holds
  two distribution artifacts, one combined checksum file covering both,
  their provenance records, and the announcement text. Bound to exactly one
  source commit, and never republished once it exists.
- **Version**: The project's single declared identifier for a release, in
  the project's `YYYY.0M.INC1` calendar form. Exists in a padded declared
  form and an unpadded reported form that name the same release. Never
  reused once published.
- **Release tag**: The deliberate trigger. Must agree with the declared
  version or the release aborts.
- **Changelog entry**: The curated, per-version section that doubles as the
  public announcement text. Must be dated before its version can be
  released.
- **Distribution artifact**: A source distribution or a built distribution.
  Platform-independent. Carries the licensing texts, the rules data at its
  nested paths, and the type-annotation marker.
- **Provenance record**: A signed statement binding a distribution artifact
  to the source commit and the build that produced it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer cuts a release with exactly one deliberate
  action — pushing the version tag — and takes no manual step between that
  push and the published release.
- **SC-002**: 100% of published releases carry both distribution formats,
  one combined checksum file with a line for each artifact, a signed
  provenance record for each artifact, and release notes whose body matches that version's changelog
  section verbatim and which end with the attribution and non-affiliation
  footer.
- **SC-003**: A release attempt whose tag disagrees with the declared
  version publishes nothing, in 100% of such attempts.
- **SC-004**: A release attempt whose changelog heading for that version
  still marks itself unreleased publishes nothing, in 100% of such attempts.
- **SC-005**: A release attempt whose test suite fails on the tagged commit
  publishes nothing, in 100% of such attempts.
- **SC-006**: A stale version string in a documented output, in a position the
  drift guard scans — which after this feature includes both spellings inside
  the README's installation command — fails the test suite and names both the
  stale value and the file containing it. "A position the guard scans" is a
  real limit, not a hedge: this feature's own `quickstart.md` and `contracts/`
  carry version strings that are deliberately *wrong* (`v2026.8.1` and
  `v2026.13.1` as tags the preflight must refuse, `## 2026.08.10` as the
  heading a prefix match must not select), and a guard broad enough to sweep
  every version-shaped string in those files would fail on the counter-examples
  the specification needs them to contain.
- **SC-007**: A new user with no prior installation and no package-index
  account installs the released version by following the README's primary
  instruction, with no additional steps.
- **SC-008**: A user verifies a downloaded artifact's checksum using tools
  already present on a stock system, without installing anything.
- **SC-009**: No version number is ever published twice; every published
  version maps to exactly one artifact set and one source commit.
- **SC-010**: A build whose rules-data files sit at paths other than the
  source tree's fails the packaging guard, for both distribution formats.
- **SC-011**: A type checker consuming the installed package resolves the
  package's annotations rather than reporting it as untyped. This is
  satisfied by the marker being honored, not by the type checker reporting
  zero errors, which FR-022 forbids anyone from requiring.
- **SC-012**: The project's first release is published, meeting every
  criterion above — the first release cetools has ever cut. It carries
  whatever version the project declares at the moment it is tagged, which
  FR-010 requires to name the month it is cut in.
- **SC-013**: A release attempt for a version that is already published
  aborts and leaves the existing release's artifacts, checksums, provenance
  records, and notes byte-identical, in 100% of such attempts.
- **SC-014**: Both distribution formats of a published release carry the
  type-annotation marker and the descriptive fields and repository links
  FR-019 names, and a packaging guard establishes this rather than a
  maintainer inspecting the build by hand.
- **SC-015**: A user verifies a downloaded artifact's provenance record and
  it names the source commit and the build that produced it.
- **SC-016**: The contributor documentation's release procedure states the
  tagging sequence, the changelog-dating step, the version-update step, and
  the month-rollover rule, so a maintainer cuts a release without consulting
  anything outside it.

## Assumptions

- **Tag form.** Version tags carry a `v` prefix over the declared padded
  CalVer form (`v2026.08.1`), the prevailing convention for tagged releases.
  The tag-versus-declared-version agreement check compares the tag with the
  `v` stripped against the declared version.
- **Checksum algorithm.** "Plain checksum, usable with no tooling" means
  SHA-256, the algorithm whose verification utility ships on every supported
  platform.
- **Public repository.** The project's public repository is the existing
  GitHub remote (`lgw4/cetools`), and its release feature is the publication
  surface, its attestation feature the signed-provenance surface.
- **Automation host.** The release automation lives alongside the existing
  test automation, as a separate workflow triggered by the tag rather than a
  change to the existing merge-time workflow.
- **Single release job.** Because the artifacts are platform-independent and
  the merge-time automation already covers the platform and interpreter
  matrix, the release runs the suite once on a single platform rather than
  repeating that matrix. This is called out in scope exclusions below.
- **Version occurrences.** The version string currently appears 23 times
  across the documented outputs the existing drift guard scans — 3 in the
  README and 20 across the four feature directories — plus the installation
  command this feature adds. The guard derives its coverage from a glob, so
  no requirement here depends on that count staying fixed.
- **Type checker.** The choice of type checker is left to implementation
  planning; the requirement is that one exists, is documented as optional,
  and gates nothing.
- **Release notes source.** The announcement body is the changelog section
  for the version, taken verbatim, with the attribution and non-affiliation
  footer appended by the automation. No separate release-notes document is
  written or maintained, and the footer text lives with the release
  automation rather than being repeated in every changelog entry.

## Dependencies

- **Constitution amendment (prerequisite, not deliverable).** The
  constitution's Development Workflow section currently ratifies "Releases
  are published to PyPI." This feature contradicts that clause. The
  amendment described in FR-023 must be made and ratified before this
  feature is planned or implemented; it is not a side effect of the work. In
  practice: run the constitution-amendment workflow first.
- The existing documented-version drift guard, which this feature extends
  rather than replaces.
- The existing packaging guards, which this feature tightens rather than
  replaces.
- The existing merge-time test automation, which continues to cover the
  cross-platform and cross-interpreter matrix.
- The existing contributor documentation, which gains the release procedure
  rather than a new document being created.

## Out of Scope

- **Any package-index publishing step**, gated, commented, or otherwise. No
  account exists, so such a step would be untested code guessing at
  configuration values that do not yet exist. Index publication is recorded
  in the constitution amendment as the intended future path and is a later
  feature.
- **Formal deprecation ceremony for withdrawn releases.** The never-reuse
  rule and a changelog entry on the superseding version are the whole of the
  policy.
- **A cross-platform matrix at release time.** The artifacts are
  platform-independent and the merge-time automation already covers the
  matrix.
- **The unguarded version-lookup failure when running from an uninstalled
  checkout.** A real defect, but not one a released artifact encounters, and
  fixing it here would widen this feature past the release it exists to cut.
