# UCF Repeated-Benefit Multiplier Notation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render repeated mustering-out benefits as `Name (xN)` instead of `Name x N`, matching the Cepheus SRD Universal Character Format.

**Architecture:** A single f-string in `_combine_material_benefits` builds the repeated-item entries. Change its template; update the three test assertions that encode the old form.

**Tech Stack:** Python 3, pytest, Black, flake8, `uv`.

## Global Constraints

- Format with Black; lint with flake8 (`uv run black . && uv run flake8 src tests`).
- Full suite must pass with coverage ≥ 85% (`uv run pytest`).
- Conventional Commits for the commit message.
- Only repeated material items (count ≥ 2) change; stat boosts (`+N Label`), singles, cash, skills, name/UPP/age, and mishap lines are untouched.

---

### Task 1: Change repeated-benefit multiplier to `(xN)`

**Files:**
- Modify: `src/cetools/formatter.py:39`
- Test: `tests/test_formatter.py` (assertions at lines 229, 275, 288)

**Interfaces:**
- Consumes: `_combine_material_benefits(benefits: list[Benefit]) -> list[str]` (existing, unchanged signature).
- Produces: repeated-item entries formatted `f"{name} (x{item_counts[name]})"`; no other output changes.

- [ ] **Step 1: Update the failing test assertions**

In `tests/test_formatter.py`, change these three assertion lines to the parenthesized form:

Line 229 (in `test_material_benefits_sum_boosts_and_group_items`):
```python
    assert lines[-1] == "+1 Edu, +1 Soc, High Passage, Weapon (x3)"
```

Line 275 (in `test_boosts_and_items_full_example`):
```python
    assert output.split("\n")[-1] == "+1 Edu, +2 Soc, Mid Passage, Weapon (x2)"
```

Line 288 (in `test_material_benefits_multiple_repeated_names_ordered_by_first_occurrence`):
```python
    assert lines[-1] == "High Passage (x2), Weapon (x2)"
```

Leave the docstrings at lines 233 and 263 unchanged — they describe counterexamples, not assertions.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_formatter.py -k "sum_boosts_and_group_items or boosts_and_items_full_example or multiple_repeated_names" -v --no-cov`
Expected: 3 FAILs, each an AssertionError showing actual `x N` vs expected `(xN)`.

- [ ] **Step 3: Make the production change**

In `src/cetools/formatter.py`, change the final return of `_combine_material_benefits` (line 39):

```python
    return boosts + singles + [f"{name} (x{item_counts[name]})" for name in repeats]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_formatter.py -k "sum_boosts_and_group_items or boosts_and_items_full_example or multiple_repeated_names" -v --no-cov`
Expected: 3 PASS.

- [ ] **Step 5: Run the full quality gate**

Run: `uv run black . && uv run flake8 src tests && uv run pytest`
Expected: Black reports no reformatting (or reformats nothing relevant), flake8 clean, full suite PASS with coverage ≥ 85%.

- [ ] **Step 6: Commit**

```bash
git add src/cetools/formatter.py tests/test_formatter.py
git commit -m "fix: render repeated UCF benefits as (xN) per SRD"
```
