# Contract: JSON Output

**Feature**: `001-dice-task-engine`

Per FR-028 this shape is a **committed public interface**. Any change to a key
name, a value type, or the meaning of a field is a breaking change and must be
flagged prominently in the changelog, because CalVer cannot signal it.

Serialization is `json.dumps(payload, indent=2, ensure_ascii=False)` plus a
trailing newline. Key order is the insertion order shown below and is stable, so
golden files can pin it. Keys are not sorted alphabetically.

## Shared rules

- **`seed` is a JSON string**, always, in every payload. Seeds are 64-bit and
  routinely exceed 2^53, where IEEE-754 doubles lose precision; a JavaScript
  consumer would silently corrupt the low digits and end up with a seed that no
  longer reproduces its own result. The string always contains only decimal digits
  (with a leading `-` only if the user supplied a negative integer seed).
- Every other numeric field is a JSON number. All are small and safe.
- `kind` discriminates the payload type and is always present.

## `cetools roll --json`

```json
{
  "kind": "roll",
  "notation": "2d6+1",
  "faces": [1, 5],
  "modifier": 1,
  "total": 7,
  "seed": "14333185781139156525"
}
```

| Key | Type | Notes |
|---|---|---|
| `kind` | string | Always `"roll"`. |
| `notation` | string | Canonical form of the throw: `"2d6+1"`, `"1d6"`, `"d66"`. |
| `faces` | array of int | Individual faces, draw order. |
| `modifier` | int | Flat modifier. Always `0` for `d66`. |
| `total` | int | **See below.** |
| `seed` | string | Decimal digits. |

**`total` is overloaded by design.** For a dice throw it is
`sum(faces) + modifier`. For `d66` it is the composed two-digit value
`faces[0] * 10 + faces[1]`, which is not a sum. Consumers must branch on
`notation == "d66"`. This is called out explicitly because it is the one place the
shape hides a rule.

`d66` example:

```json
{
  "kind": "roll",
  "notation": "d66",
  "faces": [1, 5],
  "modifier": 0,
  "total": 15,
  "seed": "14333185781139156525"
}
```

## `cetools check --json`

```json
{
  "kind": "check",
  "faces": [1, 5],
  "dice_total": 6,
  "modifiers": [
    { "label": "Difficulty (Difficult)", "value": -2 },
    { "label": "Characteristic 9", "value": 1 },
    { "label": "Skill 2", "value": 2 },
    { "label": "cover", "value": -2 }
  ],
  "total": 5,
  "target": 8,
  "success": false,
  "seed": "14333185781139156525"
}
```

| Key | Type | Notes |
|---|---|---|
| `kind` | string | Always `"check"`. |
| `faces` | array of int | Faces of the check throw. |
| `dice_total` | int | `sum(faces)`, before modifiers. |
| `modifiers` | array of object | Ordered. Each has `label` (string) and `value` (int). |
| `total` | int | `dice_total` plus every modifier value. |
| `target` | int | From the rules data, echoed so the payload is self-explaining. |
| `success` | bool | `total >= target`. |
| `seed` | string | Decimal digits. |

**Guaranteed arithmetic invariants**, which a consumer may rely on:

- `total == dice_total + sum(m.value for m in modifiers)`
- `success == (total >= target)`

**Modifier order** is fixed: difficulty, characteristic (omitted entirely if not
supplied), skill, then the caller's situational modifiers in supplied order. A
skill at level 0 appears with `"value": 0` rather than being omitted, so a reader
can see it was considered rather than forgotten.

## Errors

Errors are **not** JSON. They are plain text on stderr, even under `--json`, and
stdout stays empty. See [cli.md](cli.md).

## Contract tests

`tests/contract/test_json_contract.py` pins, for both payloads: the exact key set,
the type of every value, `kind` values, the two arithmetic invariants above, and
specifically that `seed` is a `str` and not an `int`. That last assertion exists to
fail loudly if someone "tidies" the type later.
