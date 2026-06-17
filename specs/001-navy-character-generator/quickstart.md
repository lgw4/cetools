# Quickstart: Navy Character Generator Validation

This guide describes how to validate the feature end-to-end once implementation is complete. It is not an implementation guide; see [data-model.md](data-model.md) for entity definitions and [contracts/cli.md](contracts/cli.md) for the full interface contract.

---

## Prerequisites

```bash
uv sync          # install project + dev dependencies
uv run pytest    # confirm full test suite passes before manual validation
```

The `cetools` CLI must be on your PATH after `uv sync`. Verify:

```bash
cetools --help   # should list available commands including `navy`
```

---

## Scenario 1: Generate a single Navy character (happy path)

```bash
cetools navy
```

**Expected**: A character block printed to stdout with `UPP`, `Age`, `Rank`, `Terms`, `Skills`, and `Benefits` fields. Exit code 0.

**Hand-verification checklist** (see CE SRD at https://cepheus-srd.opengamingnetwork.com/cepheus-engine-srd/cepheus-engine-character-creation/):

- [ ] `UPP` is exactly six hex characters; each digit is 0–9 or A–F.
- [ ] Each individual characteristic value implied by the UPP digit is in the range 2–15 (initial 2d6 range is 2–12; Personal Development can push it to 13–15).
- [ ] `Age` = 18 + (4 × Terms).
- [ ] `Rank` is one of: Starman, Midshipman, Lieutenant, Lt Commander, Commander, Captain, Commodore.
- [ ] `Skills` are only names appearing in the four Navy skill tables or the two rank bonus skills (Zero-G, Tactics); no unlisted skill names.
- [ ] Each skill level ≥ 1 (skills are not displayed at level 0).
- [ ] `Terms` is 1–7.
- [ ] Cash benefits match the SRD Cash Benefits table values (1000, 5000, 10000, 20000, 50000).
- [ ] Material benefits are names from the SRD Material Benefits table.
- [ ] Total benefit count = Terms + rank_bonus (0 for ranks 0–3, 1 for rank 4, 2 for rank 5, 3 for rank 6).

---

## Scenario 2: Generate multiple characters

```bash
cetools navy --count 5
```

**Expected**: Five character blocks separated by lines containing only `---`. Exit code 0.

**Check**: Each block passes the Scenario 1 checklist independently. No shared state between characters.

---

## Scenario 3: JSON output — single character

```bash
cetools navy --json
```

**Expected**: A valid JSON object on stdout. Validate:

```bash
cetools navy --json | python -m json.tool
```

**Check**:
- [ ] `jq` or `python -m json.tool` parses without error.
- [ ] All required fields present: `upp`, `age`, `rank`, `terms`, `skills`, `benefits`.
- [ ] `skills` is an object (`{}`  if no skills).
- [ ] Each benefit has `type` ("cash" or "material") and `value` (int for cash, string for material).

---

## Scenario 4: JSON output — multiple characters

```bash
cetools navy --count 3 --json
```

**Expected**: A JSON array of three character objects. Validate:

```bash
cetools navy --count 3 --json | python -m json.tool
cetools navy --count 3 --json | python -c "import json,sys; d=json.load(sys.stdin); assert isinstance(d, list) and len(d)==3"
```

---

## Scenario 5: Validation error on invalid count

```bash
cetools navy --count 0
```

**Expected**: `Error: count must be a positive integer` on stderr. Exit code 1.

```bash
cetools navy --count -1
```

**Expected**: same message, exit code 1.

Confirm exit code:

```bash
cetools navy --count 0; echo "Exit: $?"
# should print: Exit: 1
```

---

## Scenario 6: Batch stress test (SC-003)

```bash
cetools navy --count 100
```

**Expected**: 100 characters generated, no errors, exit code 0. Spot-check that `---` separators appear between each block (99 separators total).

---

## Scenario 7: JSON batch stress test

```bash
cetools navy --count 100 --json | python -c "
import json, sys
chars = json.load(sys.stdin)
assert len(chars) == 100, f'Expected 100, got {len(chars)}'
for c in chars:
    assert 'upp' in c and len(c['upp']) == 6
    assert 'skills' in c and isinstance(c['skills'], dict)
print('All 100 characters valid.')
"
```

**Expected**: Prints `All 100 characters valid.`

---

## Manual SRD Verification (SC-002)

Generate 10 characters and verify each field against the CE SRD tables:

```bash
cetools navy --count 10 --json > sample.json
```

For each character, manually confirm against the SRD:
- Enlistment/draft logic would have produced a Navy character.
- Each skill name appears in the Naval skill tables ([research.md §8](research.md#8-navy-skill-tables)) or as a rank bonus.
- Each cash benefit amount is in the Cash Benefits table ([research.md §9](research.md#9-mustering-out-rules)).
- Each material benefit name is in the Material Benefits table.
- Rank title matches the SRD rank table for the character's final rank.

All 10 characters must pass without discrepancy (SC-002).
