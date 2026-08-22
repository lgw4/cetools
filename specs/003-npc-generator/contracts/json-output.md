# Contract: JSON Output

**Feature**: `003-npc-generator`

Extends the committed shapes from the two previous features. The `roll`, `check`, and
`validation` payloads are unchanged in every respect, including key order. Key order is
part of this contract as it was of theirs.

## `npc` payload

New. Produced by `cetools npc --json` and by `as_dict(CharacterBatch)`.

**One shape whatever the count** (FR-050a). A run of one character emits the same document
a run of twelve does, with a `characters` list of one, so a consumer writes one code path
rather than branching on how many characters it asked for.

```json
{
  "kind": "npc",
  "seed": "14333185781139156525",
  "provenance": {
    "source": "packaged",
    "version": "2026.8.1",
    "files": [],
    "ignored": []
  },
  "characters": [
    {
      "seed": "14333185781139156525",
      "name": "Amara Okonkwo",
      "given_name": "Amara",
      "surname": "Okonkwo",
      "surname_region": "Africa",
      "title": "Lieutenant",
      "characteristics": {
        "STR": 9, "DEX": 10, "END": 7, "INT": 11, "EDU": 8, "SOC": 6
      },
      "skills": [
        {"name": "Comms", "specialty": null, "level": 1},
        {"name": "Gun Combat", "specialty": "Slug Rifle", "level": 1},
        {"name": "Leadership", "specialty": null, "level": 0}
      ],
      "careers": [
        {
          "career": "Navy",
          "terms": 4,
          "ladder": "officer",
          "rank": 2,
          "title": "Lieutenant",
          "commissioned": true,
          "entered_by": "selected",
          "ended": "re-enlistment",
          "benefit_rolls": 4
        }
      ],
      "age": 34,
      "funds": 55000,
      "debt": 12000,
      "pension": 0,
      "benefits": ["High Passage", "High Passage", "Weapon"],
      "history": [
        {
          "kind": "qualification",
          "career": "Navy",
          "term": 1,
          "throw": {
            "faces": [2, 5],
            "modifiers": [{"label": "Characteristic 11", "value": 1}],
            "total": 8,
            "target": 6,
            "success": true
          },
          "selected": "",
          "effects": []
        },
        {
          "kind": "rank-bonus",
          "career": "Navy",
          "term": 1,
          "throw": null,
          "selected": "",
          "effects": [{"kind": "skill", "subject": "Zero-G", "amount": 1}]
        }
      ]
    }
  ]
}
```

### Top level

| Key | Type | Notes |
|---|---|---|
| `kind` | string | Always `"npc"`. |
| `seed` | string | The **master** seed, as a decimal string. What a referee quotes for a whole table. |
| `provenance` | object | The existing provenance object, unchanged in shape. Carries the package version, so a consumer never has to obtain it separately. |
| `characters` | array | Non-empty. One entry per position, in order. A list of one when one character was asked for. |

Key order: `kind`, `seed`, `provenance`, `characters`.

The seed, the version, and the provenance sit here rather than being echoed to standard
error, so the document is self-contained and the stream is not split. FR-051's routing to
standard error is a text-mode arrangement, made so that a redirected sheet is exactly a
sheet.

### A character

| Key | Type | Notes |
|---|---|---|
| `seed` | string | The **derived** seed that reproduces this character alone (FR-050a). Quoted back to `--seed` it regenerates this one person. At position 0 it equals the master seed, by construction (research R2). |
| `name` | string | Always non-empty. What every rendering writes. The rank title is not part of it. |
| `given_name` | string | The rolled given name, or `""` when the caller supplied the name. |
| `surname` | string | The rolled surname, or `""`. |
| `surname_region` | string | The region the surname table declared, or `""`. SC-019 counts this field rather than splitting a rendered name. |
| `title` | string | The rank title attached to the rendered name, or `""`. |
| `characteristics` | object | Code to score. Key order is the characteristics registry's file order, which is the order the profile renders in. |
| `skills` | array | See below. Sorted the way the sheet sorts them, so the two agree. |
| `careers` | array | Non-empty, in the order entered. See below. |
| `age` | number | |
| `funds` | number | Never negative. |
| `debt` | number | Never negative. Separate from `funds`, so a character never has a negative balance. |
| `pension` | number | The annual amount, or `0`. |
| `benefits` | array of string | Named items, in the order received. Repeats are kept as repeats; only the text rendering collapses them. |
| `history` | array | Non-empty. See below. |

Key order: `seed`, `name`, `given_name`, `surname`, `surname_region`, `title`,
`characteristics`, `skills`, `careers`, `age`, `funds`, `debt`, `pension`, `benefits`,
`history`.

**Every key is present unconditionally** (FR-050), whether or not its value is non-empty.
`given_name` is `""` rather than absent for a supplied name, `pension` is `0` rather than
absent, `benefits` is `[]` rather than absent. A consumer never has to infer a field's
absence.

`as_dict(batch)["characters"][i]` equals `as_dict(batch.characters[i])`, so a consumer that
already handles one character handles a batch.

### A skill

| Key | Type | Notes |
|---|---|---|
| `name` | string | The parent skill's name as the registry spells it. |
| `specialty` | string or null | `null` means the parent itself. At level 0 that is a skill the character has without a specialty chosen. |
| `level` | number | Non-negative. Level 0 entries are present. |

Key order: `name`, `specialty`, `level`. `specialty` is `null`, never `""`: an empty string
is a specialty whose name is empty, and the two must stay distinguishable for the same
reason `SkillReference.specialty` distinguishes them.

### A career service

| Key | Type | Notes |
|---|---|---|
| `career` | string | The career's declared name. |
| `terms` | number | At least one. Counts mishap-ended terms. |
| `ladder` | string | The ladder the character was on when the service ended. |
| `rank` | number | |
| `title` | string | The ladder's title for that rank, or `""`. |
| `commissioned` | boolean | |
| `entered_by` | string | `"selected"`, `"drafted"`, or `"fallback"`. |
| `ended` | string | `"mishap"`, `"re-enlistment"`, `"chose to leave"`, or `"term cap"`. |
| `benefit_rolls` | number | |

Key order as listed.

### A history step

| Key | Type | Notes |
|---|---|---|
| `kind` | string | From the closed set in `data-model.md`. |
| `career` | string | `""` where the step falls outside a career. |
| `term` | number | `0` where the step falls outside a term. |
| `throw` | object or null | `null` for a step that decided rather than threw. |
| `selected` | string | What was chosen at random, or `""`. |
| `effects` | array | Possibly empty. |

Key order: `kind`, `career`, `term`, `throw`, `selected`, `effects`.

A throw object: `faces` (array of number), `modifiers` (array of the existing
`{"label", "value"}` shape), `total` (number), `target` (number), `success` (boolean), in
that order. `total` equals `sum(faces)` plus the modifier values, which is the same
arithmetic invariant the `check` payload carries and which a contract test asserts.

An effect object: `kind` (string), `subject` (string), `amount` (number), in that order.
`amount` is `0` where the effect is not numeric, and the contract states rather than hides
that: for `kind` values such as `commission` the field carries no meaning.

**This is what SC-005 reads.** Every characteristic, skill, career, credit, and item on a
sheet traces to a step here, checked over the sample by reading these named parts rather
than by parsing any rendered text, which is why `effects` is structured and why the step
carries no prose field at all.

## Invariants that hold across every payload

Unchanged from the previous contract, and restated because this feature adds a payload that
has to honor them:

- Every `seed` is a JSON **string**, both the master seed and each character's derived one.
  64-bit seeds exceed 2^53 and a JavaScript consumer would corrupt them silently. Nothing
  else numeric is a string.
- Output is `json.dumps(..., indent=2, ensure_ascii=False)` with a trailing newline. Name
  tables carry characters outside ASCII and they are emitted as themselves, not escaped.
- `--json` never changes an exit code.
- The committed fixture holds the package version as a placeholder substituted at
  comparison time, so a release rewrites no fixture. One test asserts the emitted value
  against the installed package version directly.
