# CLI Contract: `cetools character generate`

**Feature**: 002-scout-career-character | **Date**: 2026-06-18

---

## Command

```
cetools character generate [--career <name>]
```

---

## Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--career` | string | No | (absent) | Career name to enroll in. When absent, the draft determines the career. |

---

## Input Normalization

1. Strip leading and trailing whitespace from `--career` value.
2. Lowercase the result.
3. Validate against `CAREER_REGISTRY` keys.

Examples of equivalent inputs for `scout`:
- `--career scout`
- `--career Scout`
- `--career SCOUT`
- `--career "  scout  "`

---

## Valid Career Names (phase 1)

- `navy`
- `scout`

---

## Behavior

### With `--career <name>` (recognized)

1. Normalize the input value.
2. Look up career in `CAREER_REGISTRY`.
3. Call `generate_career_character(career)`.
   - Re-rolls all six characteristics until `qualification_stat` raw value ≥ `qualification_target`.
   - No enlistment roll is made.
4. On success: print formatted character to stdout, exit 0.
5. On generation failure (character death): print reason to stderr, exit 1.

### Without `--career` (draft path)

1. Call `draft_character()`.
   - Rolls 1D6, maps to career via `DRAFT_TABLE`.
   - Bypasses qualification roll entirely.
2. On success: print formatted character to stdout, exit 0.
3. On generation failure (character death, or draft maps to unimplemented career): print reason to stderr, exit 1.

### With `--career <name>` (unrecognized, after normalization)

1. Print to stderr: `Unknown career '{original_value}'. Valid careers: {career_list}`
   - `{original_value}` is the raw user-supplied string before any normalization.
   - `{career_list}` is `', '.join(sorted(CAREER_REGISTRY))` — for this phase: `navy, scout`. Derived at runtime so the message stays accurate as new careers are registered.
2. Exit 1.

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Character generated successfully |
| 1 | Any user-facing failure: unrecognized career name, character death, unimplemented draft career |

No other exit codes are used.

---

## Output Format (stdout on success)

```
UPP: <6-character pseudohex string>

<career> [" (Drafted)"] (<rank_title>, Rank <rank>) — <terms> terms, age <age>

Characteristics:
  Strength: <value>
  Dexterity: <value>
  Endurance: <value>
  Intelligence: <value>
  Education: <value>
  Social Standing: <value>

Skills:
  <name>-<level>[, <name>-<level>, ...]

Mustering-Out Benefits:
  Cash:     Cr<amount>[, Cr<amount>, ...]
  Material: <name>[, <name>, ...]

[Retirement Pension: Cr<amount>/year]
```

`(Drafted)` is included in the career line only when the career was assigned via the draft table.

---

## Error Output Format (stderr on failure)

```
Unknown career '<original_value>'. Valid careers: <sorted CAREER_REGISTRY keys>
```

(For this phase the rendered output is `navy, scout`. The list is derived at runtime from `CAREER_REGISTRY` so it expands automatically when new careers are registered.)

or (for character death):

```
Character died during term <N> survival check
```

or (for unimplemented draft career — should not occur in phase 1):

```
Draft assigned unimplemented career '<name>'
```

---

## Examples

```bash
# Scout by career flag
cetools character generate --career scout

# Navy by career flag (any casing)
cetools character generate --career Navy

# Default to draft
cetools character generate

# Error: unrecognized career
cetools character generate --career marine
# stderr: Unknown career 'marine'. Valid careers: navy, scout
# exit code: 1
```
