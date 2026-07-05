# Quickstart Validation Guide: Marine Career

Use this guide to validate that the Marine career is implemented correctly. Run each scenario
after implementation and confirm the expected outcomes.

---

## Prerequisites

```bash
uv sync
```

---

## Scenario 1: Generate a Marine character by name

```bash
cetools character generate --career "Marine"
```

**Expected**:
- Exit code: 0
- Stdout contains `Career: Marine`
- Stdout contains one of the Marine rank titles: `Trooper`, `Lieutenant`, `Captain`, `Major`,
  `Lt Colonel`, `Colonel`, or `Brigadier`
- No `(Drafted)` marker in stdout

(See [User Story 1](spec.md#user-story-1---generate-a-marine-character-priority-p1).)

---

## Scenario 2: Case-insensitive input

```bash
cetools character generate --career "marine"
cetools character generate --career "MARINE"
```

**Expected**: Both invocations exit 0 and produce a Marine character sheet (existing
normalization, FR-007 — no code change).

---

## Scenario 3: Commission and advancement (statistical verification)

Run the generator repeatedly and inspect results:

```bash
for i in $(seq 1 20); do cetools character generate --career "Marine"; done
```

**Expected**:
- Some characters show `Lieutenant` or higher (commission occurred via Education 6+)
- Every character shows `Zero-G` in their skill list (rank-0 bonus, always applied)
- At least one character across 20 runs reaches `Major` with `Tactics` in their skills
  (near-certain across 20 runs — retry if not seen)
- A character reaching `Lt Colonel` (rank 4) or higher shows extra mustering-out benefit rolls

(See [User Story 2](spec.md#user-story-2---commission-and-advancement-in-the-marines-priority-p2).)

---

## Scenario 4: Mustering-out benefits

```bash
cetools character generate --career "Marine"
```

**Expected**: Benefits section shows values drawn only from:
- Cash: 1,000 / 5,000 / 10,000 / 20,000 / 50,000 Cr
- Material: Low Passage, +1 Edu, Weapon, Mid Passage, +1 Soc, High Passage, Explorers' Society

No material benefit from another career's table (e.g. no `Courier Vessel`, which is Scout-only).

---

## Scenario 5: Draft produces Marine characters

Draft roll of 2 assigns Marine (was "navy" placeholder before this feature):

```bash
for i in $(seq 1 30); do cetools character generate; done 2>/dev/null | grep "Career:"
```

**Expected**: Mix of `Career: Navy`, `Career: Scout`, `Career: Aerospace System Defense`, and
`Career: Marine` in the output. Since roll 2 (1/6 ≈ 17%) gives Marine, it should appear within
30 runs. Drafted Marine characters show the `(Drafted)` marker.

(See [User Story 3](spec.md#user-story-3---marine-character-enters-the-draft-priority-p3).)

---

## Scenario 6: Unrecognized career — still works with four careers registered

```bash
cetools character generate --career "merchant"
```

**Expected**:
- Exit code: 1
- Stderr: `Unknown career 'merchant'. Valid careers: Aerospace System Defense, Marine, Navy, Scout`
- Stdout: empty

```bash
cetools character generate --career "Marines"
```

**Expected**:
- Exit code: 1 (plural "Marines" does not exactly match "marine")
- Stderr: `Unknown career 'Marines'. Did you mean: Marine?` — this is deterministic, not "either
  outcome acceptable": `difflib.get_close_matches("marines", CAREER_REGISTRY.keys(), cutoff=0.6)`
  returns `["marine"]` (ratio ≈0.92, comfortably above the 0.6 cutoff), so the near-miss
  suggestion path always fires (FR-010; no new logic — existing `difflib` cutoff behavior)

```bash
cetools character generate --career --help
```

**Expected**: Help text enumerates all four canonical names, including `Marine`, in sorted order
(FR-009).

---

## Scenario 7: Full test suite

```bash
uv run black . && uv run flake8 src tests && uv run pytest
```

**Expected**: All tests green, coverage ≥ 85%, black and flake8 exit 0. Zero regressions in
Navy, Scout, or Aerospace System Defense generation (SC-005).
