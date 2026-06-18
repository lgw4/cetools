# CLI Contract: `--career` Flag (Updated)

**Scope**: `cetools character generate --career <value>`

This document defines the contract for the `--career` flag after the Aerospace System Defense
feature lands. It supersedes the prior implicit contract for the two-career (Navy/Scout) state.

---

## Accepted Inputs

| Input | Normalizes To | Result |
|-------|--------------|--------|
| `"Aerospace System Defense"` | `"aerospace system defense"` | Aerospace character generated |
| `"aerospace system defense"` | `"aerospace system defense"` | Aerospace character generated |
| `"aerospace-system-defense"` | `"aerospace system defense"` | Aerospace character generated |
| `"AEROSPACE SYSTEM DEFENSE"` | `"aerospace system defense"` | Aerospace character generated |
| `"Navy"` | `"navy"` | Navy character generated |
| `"navy"` | `"navy"` | Navy character generated |
| `"Scout"` | `"scout"` | Scout character generated |
| `"scout"` | `"scout"` | Scout character generated |

**Normalization algorithm**: `input.strip().lower().replace("-", " ")`

---

## Error Responses

### Unrecognized career — close match found

```
Unknown career '<input>'. Did you mean: <canonical name>?
```

- Written to stderr, exit code 1.
- `<canonical name>` is the `career.name` field of the closest match from
  `difflib.get_close_matches(normalized, CAREER_REGISTRY.keys(), n=1, cutoff=0.6)`.

**Example**: `--career "Areospace"` (typo)
```
Unknown career 'Areospace'. Did you mean: Aerospace System Defense?
```

### Unrecognized career — no close match

```
Unknown career '<input>'. Valid careers: <comma-separated canonical names>
```

- Written to stderr, exit code 1.
- Career names are listed in sorted order by canonical name.

**Example**: `--career "marine"`
```
Unknown career 'marine'. Valid careers: Aerospace System Defense, Navy, Scout
```

---

## Help Text

```
--career TEXT   Career name. Valid: Aerospace System Defense, Navy, Scout
```

The list of valid names is derived from `CAREER_REGISTRY` at import time and reflects whatever
careers are currently registered, so it stays accurate as more careers are added.

---

## Exit Codes

| Condition | Exit Code |
|-----------|-----------|
| Character generated successfully | 0 |
| Unrecognized career | 1 |
| Enlistment failure | 1 |
| Character death during generation | 1 |
