# CLI Contract: cetools navy

This document is the authoritative interface contract for the `cetools navy` command. It is the external-facing commitment that tests and documentation must match.

---

## Command Signature

```
cetools navy [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|---|---|---|---|
| `--count INTEGER` | int | `1` | Number of characters to generate |
| `--json` | flag (bool) | `False` | Emit structured JSON output instead of human-readable text |

---

## Exit Codes

| Code | Condition |
|---|---|
| `0` | All characters generated and displayed successfully |
| `1` | Validation error (e.g., `--count` ≤ 0) |
| non-zero | Any unexpected runtime error |

---

## Human-Readable Output Format

One character per block. When multiple characters are generated, blocks are separated by a line containing only `---`.

### Single character

```
UPP: 7A8976
Age: 30
Rank: Lieutenant
Terms: 3
Skills: Comms-1, Gunnery-2, Piloting-1, Zero-G-1
Benefits: Cr5000, Weapon, High Passage
```

Field rules:
- `UPP`: Six pseudo-hex characters per the CE SRD table. Digits 0–9 map to `0`–`9`; 10–33 map to `A B C D E F G H J K L M N P Q R S T U V W X Y Z` (letters `I` and `O` are skipped). See research.md §2.
- `Age`: Integer. Computed as 18 + 4 × terms.
- `Rank`: Navy rank title from SRD table. Never blank for Navy characters (rank 0 = "Starman").
- `Terms`: Integer count of terms served.
- `Skills`: Comma-separated list, each entry formatted as `Name-Level`. Sorted alphabetically. Empty list displayed as `(none)`.
- `Benefits`: Comma-separated list. Cash benefits displayed as `Cr<amount>` (e.g., `Cr5000`). Material benefits displayed by SRD name (e.g., `Weapon`, `High Passage`).

### Multiple characters (`--count 3`)

```
UPP: 867799
Age: 26
Rank: Starman
Terms: 2
Skills: Engineering-1, Zero-G-1
Benefits: Cr1000, Low Passage
---
UPP: 9A8867
Age: 34
Rank: Commander
Terms: 4
Skills: Gun Combat-1, Leadership-1, Navigation-2, Tactics-1, Zero-G-1
Benefits: Cr10000, High Passage, Explorers' Society
---
UPP: 776978
Age: 22
Rank: Midshipman
Terms: 1
Skills: Melee Combat-1, Zero-G-1
Benefits: Cr5000
```

---

## JSON Output Format (`--json`)

### Single character (`--count 1 --json`)

```json
{
  "upp": "7A8976",
  "age": 30,
  "rank": "Lieutenant",
  "terms": 3,
  "skills": {
    "Comms": 1,
    "Gunnery": 2,
    "Piloting": 1,
    "Zero-G": 1
  },
  "benefits": [
    {"type": "cash", "value": 5000},
    {"type": "material", "value": "Weapon"},
    {"type": "material", "value": "High Passage"}
  ]
}
```

### Multiple characters (`--count 3 --json`)

```json
[
  { "upp": "867799", "age": 26, "rank": "Starman", "terms": 2, "skills": {"Engineering": 1, "Zero-G": 1}, "benefits": [{"type": "cash", "value": 1000}, {"type": "material", "value": "Low Passage"}] },
  { "upp": "9A8867", "age": 34, "rank": "Commander", "terms": 4, "skills": {"Gun Combat": 1, "Leadership": 1, "Navigation": 2, "Tactics": 1, "Zero-G": 1}, "benefits": [{"type": "cash", "value": 10000}, {"type": "material", "value": "High Passage"}, {"type": "material", "value": "Explorers' Society"}] }
]
```

Field types:
- `upp`: string (pseudo-hexadecimal, six characters, per research.md §2)
- `age`: integer
- `rank`: string (never null; "Starman" for rank 0)
- `terms`: integer
- `skills`: object (string keys, integer values; `{}` if no skills)
- `benefits`: array of `{type: string, value: integer|string}` objects

---

## Validation Errors

| Input | Message | Exit code |
|---|---|---|
| `--count 0` | `Error: count must be a positive integer` | `1` |
| `--count -5` | `Error: count must be a positive integer` | `1` |

Error messages are written to stderr.

---

## Constraints

- The command MUST exit with code 0 on any successful run (including when every character fails survival on term 1).
- The command MUST be reachable as `cetools navy` after `uv sync` installs the package.
- No interactive prompts. The generator is fully non-interactive.
- All output for `--json` MUST be valid JSON parseable by standard tools (e.g., `python -m json.tool`, `jq`).
