# Contract: the release workflow

`.github/workflows/release.yaml`. The publication surface of this project, and
the only thing that may create a release.

## Trigger

```yaml
on:
  push:
    tags:
      - 'v*'
```

Nothing else triggers it. No `workflow_dispatch`, no `release` event, no
schedule (FR-003). A tag that does not match `v*` starts no run at all, which
is one of the two acceptable answers to the spec's "a tag that does not parse
as a version" edge case; the preflight is the other.

## Job

One job, `release`, on `ubuntu-latest`, Python 3.13.

```yaml
permissions:
  contents: write        # create the release, upload assets
  id-token: write        # attest-build-provenance
  attestations: write    # attest-build-provenance
```

`contents: write` is the widest permission here and it is required: a
read-only token cannot create a release. No other permission is granted.

## Step order, and what each step guarantees

| # | Step | Guarantee |
| --- | --- | --- |
| 1 | `actions/checkout` at the pushed tag | The build and test run happen at the tagged commit, on a clean machine (FR-004) |
| 2 | `astral-sh/setup-uv` with Python 3.13 | A pinned, reproducible toolchain |
| 3 | `sh scripts/release-preflight.sh "$GITHUB_REF_NAME" pyproject.toml CHANGELOG.md` | Every abort condition, all before anything is published (FR-007, FR-008 including the dated-but-empty section, FR-025 including its fail-closed clause, and the missing-section edge case) |
| 4 | `uv sync` | Dev group installed, package installed editable |
| 5 | `uv run pytest` | The **full** suite, no `-m` filter (FR-005) |
| 6 | `uv build` | Both distribution formats into `dist/` |
| 7 | `sha256sum cetools-*` in `dist/`, redirected to `dist/SHA256SUMS.txt` | The combined manifest (FR-006) |
| 8 | `actions/attest-build-provenance` over `dist/cetools-*` | A signed record per artifact, binding it to this run and this commit (FR-006) |
| 9 | Build the notes file | `sh scripts/changelog-section.sh <declared> CHANGELOG.md` followed by `.github/release-footer.md` (FR-002, FR-021) |
| 10 | `gh release create` | Publication |

Every step runs only if the previous one succeeded, which is the default. No
step carries `continue-on-error`, and none may be added: a step that tolerates
its own failure would break FR-005's "nothing is published" guarantee.

**Step 7 must not hash the manifest into itself.** Globbing `cetools-*` rather
than `*` is what keeps `SHA256SUMS.txt` out of its own listing, and it is why
the manifest is written into `dist/` after the artifacts rather than before.

**Step 8 covers the artifacts only**, not the manifest. A checksum file is not
a build output worth attesting, and including it would make the attestation
subject list depend on step 7's ordering.

## The publish call

```sh
gh release create "$GITHUB_REF_NAME" \
  dist/cetools-*.tar.gz \
  dist/cetools-*.whl \
  dist/SHA256SUMS.txt \
  --title "$GITHUB_REF_NAME" \
  --notes-file "$NOTES" \
  --verify-tag
```

- `--verify-tag` refuses to create a tag that does not already exist, so a
  typo in the ref cannot cause the workflow to invent a tag.
- No `--draft`: FR-003 requires no maintainer action after the push, and a
  draft needs a human to publish it.
- No `--latest` flag either way: the default is correct, and pinning it would
  make an older-version hotfix release mark itself latest.
- No `--generate-notes`: the notes are the changelog section, not a commit
  list (FR-002).
- **Never** `gh release edit`, `gh release upload`, or `--clobber`. Their
  absence is what makes FR-025's "MUST NOT overwrite, replace, or add
  artifacts" structural rather than dependent on the preflight alone.

## Guarded invariants

`tests/guards/test_release_workflow.py` holds this contract against the file,
in two halves. The prohibitions are the obvious half; the requirements are the
half worth stating, because every guarantee in the step table above is carried
by a step being *present*, and a file that omitted one would satisfy every
prohibition.

| Half | Asserted |
| --- | --- |
| Prohibitions | triggers only on `push:` `tags: ['v*']`; grants exactly the three permissions above; no `continue-on-error`; none of `gh release edit`, `gh release upload`, `--clobber`, `--draft`, `--generate-notes` |
| Requirements | checkout resolves the pushed tag, not a branch tip (step 1); `release-preflight.sh` is invoked (step 3); `pytest` runs with no `-m`, `-k`, `--deselect`, or narrowing path argument (step 5); the notes file is assembled from `changelog-section.sh` *and then* `.github/release-footer.md` (step 9) |

The footer assertion is the one that matters most, and it is ordered: the
constitution's compatibility-claim clause reaches the release page, FR-021
discharges it with a fixed footer specifically "so no release can be published
without it", and a workflow that dropped step 9's second half would publish an
unattributed claim with nothing but a maintainer's eye at T062 between it and
the public.

The guard reads the file as text and matches with anchored regexes, following
`tests/guards/test_python_support.py`'s reading of `ci.yaml`. No YAML parser is
installed and none is added for this (Principle VI).

## The published release

| Property | Value |
| --- | --- |
| Tag | `v<declared version>` |
| Title | the same string |
| Body | the changelog section body, verbatim, then a blank line, then `.github/release-footer.md` verbatim |
| Assets | `cetools-<reported>.tar.gz`, `cetools-<reported>-py3-none-any.whl`, `SHA256SUMS.txt` |
| Attestations | one per distribution artifact, stored by GitHub |

The body contains no checksums, no download links, no generated commit list,
and no per-version attribution text (FR-002 as clarified; research.md R7, R9).

## Abort behavior

Any preflight failure, or any test failure, ends the run with a non-zero exit
and publishes nothing. The version number stays available for a retry, which
the constitution names as the sole exception to the never-reuse rule.

An aborted run leaves no partial release, because publication is a single
`gh release create` call and it is the last step.

## What this workflow does not do

- It does not publish to any package index, gated or commented (spec, Out of
  Scope).
- It does not run the platform or interpreter matrix; `ci.yaml` owns that.
- It does not bump versions, date changelog headings, or push commits. Those
  are the maintainer's steps, taken before the tag, and the preflight is what
  catches them being skipped.
- It does not check whether the declared version's month is the current month
  (research.md R17).
