# Quickstart Validation Guide: Aerospace System Defense Career

Use this guide to validate that the Aerospace System Defense career is implemented correctly.
Run each scenario after implementation and confirm the expected outcomes.

---

## Prerequisites

```bash
uv sync
```

---

## Scenario 1: Generate an Aerospace character by exact name

```bash
cetools character generate --career "Aerospace System Defense"
```

**Expected**:
- Exit code: 0
- Stdout contains `Career: Aerospace System Defense`
- Stdout contains one of the Aerospace rank titles:
  `Airman`, `Flight Officer`, `Flight Lieutenant`, `Squadron Leader`, `Wing Commander`,
  `Group Captain`, or `Air Commodore`
- No `(Drafted)` marker in stdout

---

## Scenario 2: Case-insensitive and hyphenated input

```bash
cetools character generate --career "aerospace system defense"
cetools character generate --career "aerospace-system-defense"
cetools character generate --career "AEROSPACE SYSTEM DEFENSE"
```

**Expected**: All three invocations exit 0 and produce an Aerospace character sheet.

---

## Scenario 3: Commission and advancement (statistical verification)

Run the generator 20 times and inspect results:

```bash
for i in $(seq 1 20); do cetools character generate --career "Aerospace System Defense"; done
```

**Expected**:
- Some characters will have `Flight Officer` or higher rank (commission occurred)
- At least one character across 20 runs should show `Squadron Leader` with `Leadership` in their
  skills (probability ~5–10% per run, so near-certain across 20 runs — retry if not seen)
- No character has a rank title from another career (Starman, Midshipman, etc.)

---

## Scenario 4: Mustering-out benefits

```bash
cetools character generate --career "Aerospace System Defense"
```

**Expected**: Benefits section shows values drawn only from:
- Cash: 1,000 / 5,000 / 10,000 / 20,000 / 50,000 Cr
- Material: Low Passage, +1 Edu, Weapon, Mid Passage, High Passage, +1 Soc

No `Explorers' Society` or `Courier Vessel` (those are Scout-only).

---

## Scenario 5: Unrecognized career — close match

```bash
cetools character generate --career "Areospace"
```

**Expected**:
- Exit code: 1
- Stderr: `Unknown career 'Areospace'. Did you mean: Aerospace System Defense?`
- Stdout: empty

---

## Scenario 6: Unrecognized career — no close match

```bash
cetools character generate --career "marine"
```

**Expected**:
- Exit code: 1
- Stderr: `Unknown career 'marine'. Valid careers: Aerospace System Defense, Navy, Scout`
- Stdout: empty

---

## Scenario 7: Draft produces Aerospace characters

The draft roll of 1 assigns Aerospace System Defense. Run draft repeatedly:

```bash
for i in $(seq 1 30); do cetools character generate; done 2>/dev/null | grep "Career:"
```

**Expected**: Mix of `Career: Navy`, `Career: Scout`, and `Career: Aerospace System Defense`
in the output. Since roll 1 (1/6 ≈ 17%) gives Aerospace, it should appear within 30 runs.

---

## Scenario 8: Full test suite

```bash
uv run black . && uv run flake8 src tests && uv run pytest
```

**Expected**: All tests green, coverage ≥ 85%, black and flake8 exit 0.
