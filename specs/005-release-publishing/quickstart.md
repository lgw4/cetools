# Quickstart: validating Release Publishing

Runnable scenarios that prove this feature works. Scenarios 1 through 6 run
locally with no network and no GitHub permissions, and are the ones to work
through during implementation. Scenarios 7 through 10 need a repository the
maintainer can push tags to, and 7 is the first release itself, which by
definition happens once.

## Prerequisites

```sh
uv sync
```

Python 3.13 or newer, `uv`, and a POSIX `sh`. Scenarios 8 and later also need
`gh` authenticated against `lgw4/cetools`.

Details referenced below live in
[contracts/release-scripts.md](./contracts/release-scripts.md),
[contracts/release-workflow.md](./contracts/release-workflow.md), and
[contracts/package-metadata.md](./contracts/package-metadata.md).

## 1. The suite is green and the new guards run

```sh
uv run pytest
```

Expected: everything passes, and the run includes
`tests/guards/test_release_scripts.py`. Confirm it was not silently skipped:

```sh
uv run pytest tests/guards/test_release_scripts.py -v
```

Expected: individually named cases, not `s` for skipped. A skip here means no
`sh` on PATH, which on a POSIX machine means something is wrong rather than
something is unsupported.

Validates FR-005's premise, and Principle III for the new scripts.

## 2. The changelog extractor reproduces a section verbatim

```sh
sh scripts/changelog-section.sh 2026.08.1 CHANGELOG.md | head -5
sh scripts/changelog-section.sh 2026.08.1 CHANGELOG.md | wc -l
```

Expected: the first lines of the release's own changelog body, starting at
"First release: the dice and 2D6 task-check engine", with no `## ` heading line
and no leading blank line. The line count is the section's length, which today
is most of the file, because there is only one section.

Then the refusal:

```sh
sh scripts/changelog-section.sh 9999.99.9 CHANGELOG.md; echo "exit $?"
```

Expected: `exit 1`, a message on stderr naming the version and the file, and
nothing on stdout.

Validates FR-002, and the "no section at all" edge case.

## 3. The preflight refuses each wrong release

Run each against a fixture rather than the real tree, so nothing has to be
edited and reverted. A scratch directory with a two-line `pyproject.toml` and a
short `CHANGELOG.md` is enough; the pytest cases in scenario 1 already build
these, so this scenario is the by-hand confirmation that the messages are
legible.

```sh
sh scripts/release-preflight.sh v2026.08.2 pyproject.toml CHANGELOG.md; echo "exit $?"
```

Expected: `exit 1`, and a stderr line naming both `v2026.08.2` and the declared
`2026.08.1`. A message that says only "version mismatch" fails this scenario.

```sh
sh scripts/release-preflight.sh v2026.08.1 pyproject.toml CHANGELOG.md; echo "exit $?"
```

Expected **before** the changelog is dated: `exit 1`, with a stderr line saying
the section is still marked unreleased. Expected **after** dating it: the tag
and changelog checks pass, and only the already-published check remains.

```sh
sh scripts/release-preflight.sh 2026.08.1 pyproject.toml CHANGELOG.md; echo "exit $?"
sh scripts/release-preflight.sh v2026.8.1 pyproject.toml CHANGELOG.md; echo "exit $?"
```

Expected: `exit 1` for both. The first has no `v`; the second is the reported
spelling in tag position, which is the mistake most likely to be made by hand.

Validates FR-007, FR-008, and User Story 3's first two acceptance scenarios.

## 4. A stale version in the install command fails the suite

Edit `README.md` and change the tag segment of the installation URL from
`v2026.08.1` to `v2026.08.9`, then:

```sh
uv run pytest tests/guards/test_documented_version.py
```

Expected: a failure naming `README.md`, the stale value, and the version it
should have carried. Revert, and confirm the suite is green again.

Repeat with the wheel filename segment, changing `2026.8.1` to `2026.8.9`.
Expected: a failure again, and one that compares against the **reported** form,
not the padded one.

Then the case that proves the two groups are really separate: swap the
spellings, putting the unpadded form in the tag segment and the padded form in
the filename. Expected: failures for both positions. If this passes, the guard
is normalizing before comparing and FR-012 is not satisfied.

Validates FR-011, FR-012, SC-006, and User Story 3's third acceptance scenario.

## 5. A flattened build fails the packaging guard

The guard builds from the real tree, so simulate the flatten in a scratch
checkout rather than by editing `pyproject.toml` in place:

```sh
git worktree add /tmp/cetools-flat HEAD
```

In the worktree, move the nested rules-data files up into
`src/cetools/data/` and remove the emptied subdirectories, then:

```sh
cd /tmp/cetools-flat && uv run pytest tests/guards/test_packaging.py
```

Expected: `test_wheel_contains_every_packaged_data_file` and
`test_sdist_contains_every_packaged_data_file` both fail, and the failure names
the differing paths. Confirm the tightening actually bit by checking that the
same worktree passes on `main`'s version of the guard, which is the behavior
FR-015 exists to remove.

```sh
git worktree remove /tmp/cetools-flat --force
```

Validates FR-015, SC-010, and User Story 5.

## 6. The built artifacts carry the marker and the metadata

```sh
uv build
python -c "import zipfile,sys; z=zipfile.ZipFile(sys.argv[1]); print('\n'.join(n for n in z.namelist() if 'py.typed' in n or n.endswith('METADATA')))" dist/cetools-2026.9.2-py3-none-any.whl
```

Expected: `cetools/py.typed` listed, and a `METADATA` path.

```sh
uv run python -m zipfile -e dist/cetools-2026.9.2-py3-none-any.whl /tmp/whl
grep -E '^(Keywords|Classifier|Project-URL|License-Expression):' /tmp/whl/cetools-*.dist-info/METADATA
```

Expected: a `Keywords` line, several `Classifier` lines including
`Typing :: Typed`, four `Project-URL` lines, and the existing
`License-Expression: GPL-3.0-only`. No `Classifier: License ::` line.

The same fields in the sdist, which SC-014 binds equally:

```sh
tar -xzf dist/cetools-*.tar.gz -C /tmp
grep -E '^(Keywords|Classifier|Project-URL|License-Expression):' /tmp/cetools-*/PKG-INFO
tar -tzf dist/cetools-*.tar.gz | grep 'src/cetools/py.typed'
```

Expected: the same field set as the wheel, and the marker at
`src/cetools/py.typed`.

Then the type checker actually resolving the annotations:

```sh
uv run mypy --version
uv run mypy -c "import cetools; reveal_type(cetools.throw)"
```

Expected: a revealed type rather than a "module is installed, but missing
library stubs or py.typed marker" note.

Validates FR-019, FR-020, SC-011, and User Story 4.

## 7. Cut the first release

The one-time scenario, and User Story 1 end to end.

1. Confirm the declared version's month is the current month. If it is not, bump
   the version first (FR-010) and take the changelog heading with it.
2. Date the `## 2026.08.1 (unreleased)` heading in `CHANGELOG.md`.
3. Confirm every documented occurrence of the version is current:
   `uv run pytest tests/guards/test_documented_version.py`.
4. Commit, and push to `main`. Wait for `ci.yaml` to go green.
5. Tag and push:

   ```sh
   git tag v2026.08.1
   git push origin v2026.08.1
   ```

6. Take no further action.

Expected, with no manual step between the push and the result:

- A public release at `v2026.08.1` on `lgw4/cetools`.
- Three assets: the sdist, the wheel, and `SHA256SUMS.txt`.
- Release notes whose body is the changelog section verbatim, ending with the
  attribution and non-affiliation footer.
- An attestation for each of the two distribution artifacts.

Validates SC-001, SC-002, SC-012, and every acceptance scenario of User
Story 1.

## 8. Verify what was published

```sh
gh release download v2026.08.1 --repo lgw4/cetools --dir /tmp/rel
cd /tmp/rel && sha256sum -c SHA256SUMS.txt
```

Expected: `OK` for each of the two artifacts, from a stock utility, with
nothing installed. On macOS use `shasum -a 256 -c SHA256SUMS.txt`.

```sh
gh attestation verify /tmp/rel/cetools-2026.9.2-py3-none-any.whl --repo lgw4/cetools
```

Expected: verification succeeds and reports the source commit and the workflow
that built it.

Validates FR-006, SC-002, SC-008, and User Story 1's fourth acceptance
scenario.

## 9. Install as a reader would

On a machine with no prior cetools install, run the README's primary
instruction exactly as written, then:

```sh
cetools --version
cetools roll 2d6+1 --seed session-alpha
```

Expected: the version reported is `2026.8.1`, and the roll matches the README's
worked example. Then the alternative instruction, `uv tool install` against the
tagged source, and confirm the same version.

Then the library instruction, in a throwaway project rather than a tool
install:

```sh
uv init /tmp/cetools-consumer && cd /tmp/cetools-consumer
# the README's `uv add` line, verbatim
uv run python -c "import cetools; print(cetools.__name__)"
```

Expected: the dependency resolves and the import succeeds.

Validates FR-016, FR-017, FR-026, SC-007, and User Story 2.

## 10. A second push of the same tag publishes nothing

```sh
gh release view v2026.08.1 --repo lgw4/cetools --json publishedAt,assets > /tmp/before.json
git push origin v2026.08.1 --force
```

Expected: the workflow run aborts at the preflight, reporting that the version
is already published. Then:

```sh
gh release view v2026.08.1 --repo lgw4/cetools --json publishedAt,assets > /tmp/after.json
diff /tmp/before.json /tmp/after.json
```

Expected: no difference. The existing release's assets, notes, and publication
time are untouched.

Validates FR-025, SC-009, SC-013, and the "tag pushed for a version already
published" edge case.
