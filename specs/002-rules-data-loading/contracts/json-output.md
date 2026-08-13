# Contract: JSON Output

**Feature**: `002-rules-data-loading`

Extends the committed shape from `001-dice-task-engine`. The `roll` payload is
unchanged in every respect. Key order is part of the contract, as it was before.

## Provenance object

Emitted wherever provenance is reported.

Packaged:

```json
{
  "source": "packaged",
  "files": []
}
```

Overridden:

```json
{
  "source": "overridden",
  "files": [
    {
      "file": "navy.toml",
      "disposition": "replaced",
      "fingerprint": "sha256:3b1f0d...c0"
    },
    {
      "file": "scouts.toml",
      "disposition": "added",
      "fingerprint": "sha256:9ad4e2...71"
    }
  ]
}
```

| Key | Type | Notes |
|---|---|---|
| `source` | string | `"packaged"` or `"overridden"`. Redundant with `files` being empty, and emitted anyway so a consumer never infers "packaged" from an absence (FR-037). |
| `files` | array | Sorted by `file`. Empty exactly when `source` is `"packaged"`. |
| `files[].file` | string | The composition key, which is the basename. |
| `files[].disposition` | string | `"replaced"` or `"added"` (FR-032, FR-035). |
| `files[].fingerprint` | string | `"sha256:"` and the 64-character lowercase hex digest of the file's bytes. Reproducible with `shasum -a 256`. |

## `check` payload

One key appended; every existing key, its position, and its type are unchanged.

```json
{
  "kind": "check",
  "faces": [1, 5],
  "dice_total": 6,
  "modifiers": [
    {"label": "Difficulty (Difficult)", "value": -2},
    {"label": "Characteristic 9", "value": 1},
    {"label": "Skill 2", "value": 2},
    {"label": "cover", "value": -2}
  ],
  "total": 5,
  "target": 8,
  "success": false,
  "seed": "14333185781139156525",
  "provenance": {"source": "packaged", "files": []}
}
```

Key order: `kind`, `faces`, `dice_total`, `modifiers`, `total`, `target`, `success`,
`seed`, `provenance`. Appending rather than inserting is deliberate, so a consumer
reading keys positionally is unaffected and a diff against the previous contract is
one added line.

## `validation` payload

New. Produced by `cetools validate --json` and by `as_dict(ValidationReport)`.

```json
{
  "kind": "validation",
  "valid": false,
  "file_count": 5,
  "provenance": {"source": "packaged", "files": []},
  "problems": [
    {
      "file": "navy.toml",
      "location": "tables.service.entries[2]",
      "found": "unrecognized skill name 'Vac Suit'",
      "expected": "a name in the skills registry"
    }
  ]
}
```

| Key | Type | Notes |
|---|---|---|
| `kind` | string | Always `"validation"`. |
| `valid` | boolean | `true` exactly when `problems` is empty. |
| `file_count` | number | Files composed and checked. |
| `provenance` | object | Present whether or not validation succeeded, because composition precedes validation. |
| `problems` | array | Sorted by `file` then `location`. Empty when valid. |
| `problems[].file` | string | Composition key of the file. |
| `problems[].location` | string | Dotted key path with array indices. `""` for a problem about the file as a whole. |
| `problems[].found` | string | What was there. |
| `problems[].expected` | string | What would have been acceptable. |

`found` and `expected` are separate keys so a consumer gets both without parsing prose
(Acceptance Scenario 2.4, FR-022). Both are prose in English; what the contract fixes
is that they are distinct fields, not their wording.

## Invariants that hold across every payload

- `seed` stays a JSON **string**, for the reason the previous contract records:
  64-bit seeds exceed 2^53 and a JavaScript consumer would corrupt them silently.
- Output is `json.dumps(..., indent=2, ensure_ascii=False)` with a trailing newline.
- `--json` never changes an exit code (FR-041).
