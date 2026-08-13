# Contract: Command-Line Surface

**Feature**: `002-rules-data-loading`

Extends the surface `001-dice-task-engine` established. Only the changes are given
here; `cetools roll` is untouched in every respect, because it resolves against no
rules data.

## `cetools check`

```text
cetools check [--difficulty NAME] [--characteristic N] [--skill N]
              [--dm LABEL=VALUE ...] [--seed SEED] [--rules-data PATH] [--json]
```

One new option:

| Option | Meaning |
|---|---|
| `--rules-data PATH` | Override location, a directory or a single file. Composed over the packaged data set exactly as a library load composes it (FR-042). |

Rendered output gains one block, and nothing else changes (FR-045).

## `cetools validate`

```text
cetools validate [PATH] [--json]
```

| Argument | Meaning |
|---|---|
| `PATH` | Optional. Absent: validate the packaged data set (FR-039). A directory: validate it composed over the packaged data (FR-040). A single file: the same, positioned by its basename alone (FR-040a). |

The command name is `validate` rather than `validate-rules` because rules data is the
only thing the package validates; a later second kind of validation takes a
subcommand of its own rather than renaming this one.

### Exit codes

| Code | When |
|---|---|
| 0 | No problem found |
| 1 | One or more problems found |
| 2 | Usage error, including a `PATH` that does not exist |

The choice of output mode changes neither the code nor the outcome (FR-041, SC-010).
No code outside `{0, 1, 2}` is used, which is the set the project already had.

### Streams

Problems go to **stdout**: they are the report the command was asked for, not a
diagnostic about the command failing. `--json` must produce a parseable stdout, and
splitting the report across streams by mode would break that. stderr carries usage
errors and nothing else.

## Text rendering

### Provenance block, shared by `check` and `validate`

Packaged:

```text
  Rules: packaged
```

Overridden:

```text
  Rules: overridden
    navy.toml     replaced  sha256:3b1f...c0
    scouts.toml   added     sha256:9ad4...71
```

The file column is padded to the longest basename present and the disposition column
to the longest disposition present, matching the padding rule the `Modifiers` block
already uses. Files are listed sorted by name. Fingerprints are printed whole.

### `cetools check`

The existing rendering with the provenance block appended after `Seed:`:

```text
Check: FAILURE
  Dice:  1, 5 (sum 6)
  Modifiers:
    Difficulty (Difficult) -2
    Characteristic 9       +1
    Skill 2                +2
    cover                  -2
  Total: 5 vs target 8
  Seed:  14333185781139156525
  Rules: packaged
```

The outer label column stays seven characters wide, because `Rules:` is no longer
than `Total:`. Every line above the new one is byte-for-byte what it was, which is
what SC-009 checks.

### `cetools validate`, no problems

```text
Rules data is valid.
  Files: 5
  Rules: packaged
```

### `cetools validate`, with problems

One line per problem, then a summary:

```text
navy.toml:tables.service.entries[2]: found unrecognized skill name 'Vac Suit'; expected a name in the skills registry
navy.toml:throws.survival.target: found a string; expected an integer
navy.toml:mustering-out: found an unrecognized key 'chash'; expected one of cash, benefits
skills.toml:skills: found no entries; expected at least one

Rules data is invalid.
  Files:    5
  Problems: 4
  Rules:    packaged
```

The problem line is `FILE:LOCATION: found FOUND; expected EXPECTED`, dropping
`:LOCATION` when the problem is about the file as a whole:

```text
navy.toml: found invalid TOML at line 12, column 3; expected a well-formed TOML document
```

One problem per line and the file first makes the report greppable and sortable, and
makes a test able to assert a single problem's presence without matching the whole
report. Problems are sorted by file then location, so a run is stable.

## Failure of a load during `check`

An invalid data set raises out of the library and is caught at the single site
`cli.py` already has. The problems are printed to stderr in the same one-line form,
and the command exits 1. A check that cannot trust its rules data produces no result
rather than a result with a caveat (FR-025).

## Help text

`--rules-data` and `validate` carry help strings. The licensing guard treats CLI help
as a claim surface, so no help string may name the trademark as something this tool
works with.
