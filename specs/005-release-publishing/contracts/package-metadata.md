# Contract: package metadata

What the built distributions must carry in their metadata, and what must not
appear there. Discharges FR-019, FR-020, and the constitution's
compatibility-claim clause as it applies to the package's own description.

## Unchanged fields

`name`, `version`, `description`, `readme`, `requires-python`, `license`,
`license-files`, `dependencies`, and `[project.scripts]` are all already
correct and this feature does not touch them. In particular:

- `license` stays the SPDX expression `GPL-3.0-only`. A `License ::`
  classifier is **not** added alongside it.
- `description` stays "Dice and task check engine for SRD-derived 2D6
  roleplaying rules", which is deliberately claim-free and therefore owes no
  trademark attribution.

## Added fields

### `keywords`

Descriptive terms for what the tool does. Illustrative, not binding on the
exact list:

```toml
keywords = ["dice", "rpg", "tabletop", "2d6", "srd", "task-resolution",
            "character-generation", "seeded", "reproducible"]
```

**Hard constraint**: no keyword may contain `Cepheus Engine` or
`Samardan Press`. A Product Identity string in the package's own metadata
would violate the constitution's Product Identity clause directly, and
depending on phrasing would add an unattributed compatibility claim to a
surface that carries no attribution.

### `classifiers`

```toml
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: End Users/Desktop",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Topic :: Games/Entertainment :: Role-Playing",
    "Typing :: Typed",
]
```

- Every entry must be a valid, non-deprecated trove classifier. A misspelling
  is not caught by anything in this repository; verify against the canonical
  list at task time.
- The two `Programming Language` entries must stay in step with
  `requires-python` and with `ci.yaml`'s matrix. `tests/guards/
  test_python_support.py` already exists to keep those in step; check whether
  it should also cover the classifiers.
- `Typing :: Typed` is the metadata half of the `py.typed` marker. Shipping one
  without the other is a contradiction.

### `authors`

```toml
authors = [{ name = "Chip Warden" }]
```

Name only. Adding `email` publishes an address in every distribution's metadata
and on the release page, which is a disclosure decision left to the maintainer
(research.md R22), not a packaging one.

### `[project.urls]`

```toml
[project.urls]
Homepage = "https://github.com/lgw4/cetools"
Repository = "https://github.com/lgw4/cetools"
Changelog = "https://github.com/lgw4/cetools/blob/main/CHANGELOG.md"
Issues = "https://github.com/lgw4/cetools/issues"
```

FR-019 names three of these as required: the source repository, the changelog,
and the issue tracker. `Homepage` is added because tooling that shows one link
shows that one.

`Changelog` points at `main` rather than at a tag, so it tracks the current
file rather than freezing at the released version.

## The `py.typed` marker

An empty `src/cetools/py.typed`. No content, not even a comment: PEP 561 gives
the file's contents no meaning.

Hatchling's `packages = ["src/cetools"]` ships non-Python files inside the
package directory, so no `pyproject.toml` change is required to carry it.
That is exactly the kind of assumption a guard exists to hold.

## Guards

`tests/guards/test_packaging.py` grows checks over the built artifacts, which
is what FR-020 requires ("verified by a packaging guard") and what SC-014
binds:

| Assertion | Wheel | Sdist |
| --- | --- | --- |
| The `py.typed` marker is present | `cetools/py.typed` | `src/cetools/py.typed` |
| Every rules-data file appears at its full relative path | `cetools/data/<rel>` | `src/cetools/data/<rel>` |

The full-path comparison replaces the current basename comparison in
`test_wheel_contains_every_packaged_data_file` and
`test_sdist_contains_every_packaged_data_file` (FR-015, SC-010). On failure it
must name the differing paths, not report a set inequality.

Whether the descriptive fields themselves get a guard is a task-time call. The
argument for one: FR-019 is a shipped-artifact requirement like every other
check in that module, and a dropped `[project.urls]` table is silent. The
argument against: a guard asserting the exact classifier list is a second copy
of `pyproject.toml` that has to be edited twice. A middle position, asserting
that the built metadata carries a non-empty `Keywords`, at least one
`Classifier`, and `Project-URL` entries for the three FR-019 names, without
pinning their values, is the one this contract recommends.

## What must not appear

- No Product Identity string (`Cepheus Engine`, `Samardan Press`) in `name`,
  `keywords`, `classifiers`, or `description`.
- No compatibility claim in `description` without the attribution and the
  non-affiliation statement in the same field.
  `tests/unit/test_licensing.py` already checks the description for exactly
  this and must keep doing so.
- No `License ::` classifier, which would duplicate the SPDX expression.
- No dependency added. This feature adds nothing to `dependencies`; `mypy` goes
  in the `dev` group only.
