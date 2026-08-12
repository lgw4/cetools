# Contract: Command-Line Interface

**Feature**: `001-dice-task-engine`

Entry point `cetools`, plus `python -m cetools` (needed by the subprocess guard
test). One Typer app with two subcommands.

## `cetools roll`

```
cetools roll NOTATION [--seed TEXT] [--json]
```

| Argument / option | Required | Default | Meaning |
|---|---|---|---|
| `NOTATION` | yes | - | What to throw. See grammar below. |
| `--seed` | no | fresh | Integer or arbitrary text. |
| `--json` | no | off | Emit machine-readable output instead of text. |

### Notation grammar

```
NOTATION := "d66"                        (case-insensitive, matched first)
          | [COUNT] ("d" | "D") SIDES [SIGN MOD]

COUNT := digits        default 1
SIDES := digits        must be >= 1
SIGN  := "+" | "-"
MOD   := digits
```

Whitespace around the `d` and the sign is tolerated and stripped. Accepted:
`2d6`, `d6`, `2D6+1`, `3d6 - 2`, `1d100`, `d66`.

`d66` is matched before the general rule, so it always means the two-digit table
throw. A genuine 66-sided die is written `1d66`.

Rejected with `DiceError` (exit 1): a count or side count of zero or less, and any
string the grammar does not match.

### Examples

```
$ cetools roll 2d6+1 --seed session-alpha
2d6+1 = 7
  Dice:     1, 5 (sum 6)
  Modifier: +1
  Seed:     14333185781139156525

$ cetools roll d66 --seed session-alpha
d66 = 15
  Dice: 1, 5
  Seed: 14333185781139156525
```

The numbers in these examples are **not illustrative**. They were computed by
running the algorithm this plan specifies (blake2b fold, then `getrandbits`
rejection sampling) and are what a correct implementation must produce. They are
suitable as the first literal expected values in the test suite.

## `cetools check`

```
cetools check [--difficulty NAME] [--characteristic N] [--skill N]
              [--dm "label=value"]... [--seed TEXT] [--json]
```

| Option | Required | Default | Meaning |
|---|---|---|---|
| `--difficulty` | no | the zero-modifier rung (`Average` as shipped) | Name from the ladder. Matched exactly, character for character: case-sensitive, no abbreviation, no whitespace tolerance. |
| `--characteristic` | no | omitted | Characteristic **score**, not a modifier. Omitted means no characteristic modifier is applied. |
| `--skill` | no | omitted | Skill **level**. Omitted means untrained and applies the unskilled penalty. `0` means trained at level 0 and applies nothing. |
| `--dm` | no | none | Repeatable labelled situational modifier. |
| `--seed` | no | fresh | Integer or arbitrary text. |
| `--json` | no | off | Machine-readable output. |

### `--dm` value format

`label=value`, split on the **last** `=` so a label may itself contain `=`. The
value must match `^[+-]?[0-9]+$`. The label must be non-empty after trimming.

A malformed `--dm` is a **usage error (exit 2)**, not a library error, because it is
a malformed option value.

Putting the label first means the token never begins with `-`, so no `--`
separator or `=`-attachment is needed for negative modifiers.

### Example

```
$ cetools check --difficulty Difficult --characteristic 9 --skill 2 \
    --dm "cover=-2" --seed session-alpha
Check: FAILURE
  Dice:  1, 5 (sum 6)
  Modifiers:
    Difficulty (Difficult) -2
    Characteristic 9       +1
    Skill 2                +2
    cover                  -2
  Total: 5 vs target 8
  Seed:  14333185781139156525
```

Note the exit status here is **0**. A reported failure is the tool working.

## Human-readable rendering rules

Pinned by golden files, so these are contract, not incidental formatting.

**Throw**

1. Header: `{notation} = {total}`.
2. Indented two spaces: `Dice:` with faces joined by `, `.
3. `(sum N)` is appended to the dice line **only when `modifier != 0`**; otherwise
   the sum already equals the header total and would be noise.
4. `Modifier:` line appears **only when `modifier != 0`**, formatted signed (`+1`, `-2`).
5. `Seed:` line always appears.
6. Labels are padded to the width of the longest label actually present in that
   output.

**Check**

1. Header: `Check: SUCCESS` or `Check: FAILURE`.
2. `Dice:` line, always with `(sum N)` since modifiers are always present.
3. `Modifiers:` followed by one four-space-indented line per modifier, label padded
   to the longest label in the list, value formatted signed including `+0`.
4. `Total: {total} vs target {target}`.
5. `Seed:` line.

Modifier order is fixed: difficulty, characteristic (if given), skill, then the
caller's `--dm` values in the order supplied.

Every output ends with a trailing newline.

## Streams and exit codes

| Situation | Stream | Exit |
|---|---|---|
| Successful throw or check, including a **failed** check | stdout | 0 |
| `CetoolsError` (bad notation, unknown difficulty, bad rules data) | stderr | 1 |
| Usage error (unknown option, missing argument, malformed `--dm`) | stderr | 2 |

Errors are emitted as plain text on stderr even under `--json`. A JSON error
envelope is deliberately not provided (YAGNI); nothing consumes one yet.

On any error, **nothing** is written to stdout, so a consumer never sees a partial
result.

## `cetools --version`

Prints the package version and exits 0. Included because the reproducibility
promise is "same seed **and same version**", so a user sharing a seed needs a
supported way to report the version alongside it.
