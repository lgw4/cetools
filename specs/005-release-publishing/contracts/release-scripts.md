# Contract: the release scripts

Two scripts in `scripts/`, both `#!/usr/bin/env sh` with no bashisms. Both take
every input as an argument, including the paths they read, so both are testable
against fixtures rather than only against the real repository.

Neither ships. `scripts/` is not in the sdist `include` list.

## `scripts/changelog-section.sh`

Extract one version's section body from a changelog.

### Usage

```sh
sh scripts/changelog-section.sh <version> <changelog-path>
```

`<version>` is the declared padded form, with no `v` prefix and no
surrounding markup.

### Behavior

Finds the line matching `## <version>` at the start of a line, where the
heading may carry trailing text (a date, or `(unreleased)`). Prints every line
after it, up to but not including the next line beginning `## `, or to end of
file if there is none. Leading and trailing blank lines are trimmed; everything
between is reproduced byte for byte.

The heading line itself is not printed. GitHub renders the release title
separately, so repeating the version in the body would duplicate it.

### Exit codes

| Code | Condition | stderr |
| --- | --- | --- |
| 0 | The section was found and its body written to stdout | empty |
| 1 | No `## <version>` heading in the file | names the version and the file |
| 2 | Wrong argument count, or the changelog path does not exist | usage |

An empty section body is **not** an error here. It is a legitimate, if odd,
changelog state, and FR-008's dating check is what actually stops a release
with nothing to announce.

### Cases the tests must cover

1. The section is the last in the file and runs to end of file. **This is the
   first release's case**, because `CHANGELOG.md` currently has exactly one
   `## ` section, so it is the case to write first.
2. The section is followed by another `## ` heading and stops there.
3. The section is absent: exit 1, nothing on stdout.
4. The heading carries `(unreleased)` and is still found. Extraction does not
   judge; the preflight does.
5. The heading carries a date and is still found.
6. A body containing `###` subsection headings is reproduced with them intact.
7. A body whose first or last lines are blank is trimmed at both ends without
   touching interior blank lines.
8. A version whose digits are a prefix of another heading's (`2026.08.1` must
   not match `## 2026.08.10`) selects the right section.

Case 8 is the one an obvious implementation gets wrong. Matching must be
anchored so the heading is `## <version>` followed by end-of-line or
whitespace, not `## <version>` followed by anything.

## `scripts/release-preflight.sh`

Refuse a release that would ship something wrong.

### Usage

```sh
sh scripts/release-preflight.sh <tag> <pyproject-path> <changelog-path>
```

`<tag>` is the raw ref name, `v2026.08.1`.

### Checks, in order

| # | Check | Fails when |
| --- | --- | --- |
| 1 | Tag shape | `<tag>` is not one `v` followed by a `YYYY.0M.INC1` string |
| 2 | Tag agrees with the declared version | the tag with one leading `v` stripped differs from `project.version` |
| 3 | The changelog has a section | no `## <version>` heading exists |
| 4 | The section is dated | the heading carries `(unreleased)`, or carries no ISO date |
| 5 | The version is not already published | `gh release view <tag>` exits zero |

Each failure exits non-zero and writes one line to stderr naming the check and
both values involved. The message is the whole diagnostic a maintainer gets, so
"tag v2026.08.2 does not match the declared version 2026.08.1" is the standard,
not "version mismatch".

### Exit codes

| Code | Condition |
| --- | --- |
| 0 | Every check passed |
| 1 | A check failed; stderr names which and why |
| 2 | Wrong argument count, or a named file does not exist |

### Reading the declared version in shell

`project.version` is read from `pyproject.toml` without a TOML parser, because
the release job must be able to run this before `uv sync`. Anchor on a
`version = "..."` line inside the `[project]` table specifically, not the first
`version =` in the file, or `[tool.*]` tables will eventually shadow it. An
`awk` state machine over the table headers is the intended shape.

### Check 5 needs the network; the others do not

Checks 1 through 4 are pure text and are what the pytest coverage exercises.
Check 5 calls `gh`, which needs a token and a network, so the tests must be
able to run the first four without it. Either take the check-5 command as an
overridable variable, or split it behind a flag; decide at task time and say
which in the script's own header comment.

### Cases the tests must cover

1. A well-formed tag matching a dated changelog section: exit 0, no output.
2. Tag disagrees with the declared version: exit 1, message names both.
3. Tag is not `v` plus CalVer (`2026.08.1`, `vv2026.08.1`, `v2026.8.1`,
   `v2026.13.1`, `release-2026.08.1`): exit 1 in each case.
4. Changelog has no section for the version: exit 1.
5. Changelog section is marked `(unreleased)`: exit 1.
6. Changelog section is dated: passes check 4.
7. Missing `pyproject.toml` or `CHANGELOG.md`: exit 2.
8. `project.version` read correctly from a fixture whose `[tool.x]` table also
   carries a `version =` line.

Case 3's `v2026.8.1` entry matters: the unpadded form is a real spelling of
this version, and it must still be refused in tag position, because the tag is
compared against the padded declared string.

## Testing both from pytest

`tests/guards/test_release_scripts.py`, invoking each script with
`subprocess.run(["sh", ...])` against fixture files in `tmp_path`, skipping when
`shutil.which("sh")` is `None`. This follows the skip pattern
`tests/guards/test_packaging.py` already uses for a missing `uv`.
