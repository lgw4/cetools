# Sum Stat-Boost Benefits Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render repeated characteristic-boost mustering-out benefits as a single summed entry (`+2 Soc`) instead of repeat-count notation (`+1 Soc x 2`).

**Architecture:** Display-only change in `src/cetools/formatter.py`. The function `_combine_material_benefits` is rewritten to split material benefits into stat boosts (summed) and genuine items (unchanged `x N` notation). No changes to the generator, the `Benefit` model, or how characteristics are applied — the UPP is already correct.

**Tech Stack:** Python 3.14, pytest, Black, flake8, isort, managed with `uv`.

## Global Constraints

- Format with Black before finishing: `uv run black .`
- Lint clean with flake8: `uv run flake8 src tests`
- Full suite must pass with coverage ≥85%: `uv run pytest`
- Commit messages use Conventional Commits (e.g. `fix:`, `test:`).
- Stat-boost detection convention: a `material_name` is a stat boost iff it starts
  with the literal prefix `"+1 "`. This mirrors `_apply_stat_boost`
  (`src/cetools/engine/generator.py:117-124`); do not diverge from it.
- Benefit-line ordering: stat boosts first, then material-item singles, then
  material-item repeats — each group ordered by first appearance.

---

### Task 1: Sum stat-boost benefits in the formatter

**Files:**
- Modify: `src/cetools/formatter.py:10-28` (`_combine_material_benefits`)
- Test: `tests/test_formatter.py`

**Interfaces:**
- Consumes: `Benefit` records with `kind == "material"` and a `material_name`
  string (`src/cetools/engine/models.py:51-61`).
- Produces: `_combine_material_benefits(benefits: list[Benefit]) -> list[str]` —
  unchanged signature. Each returned string is one comma-joined segment of the
  benefit line. Stat boosts render as `+{sum} {label}` (e.g. `+2 Soc`); items
  render as `Name` or `Name x N`.

- [ ] **Step 1: Update the existing test that asserts the old behavior**

The current test at `tests/test_formatter.py:215-229` expects stat boosts to appear
inline as `+1 Edu` / `+1 Soc` among the items. Under the new ordering (boosts first),
its expected output changes. Replace the whole test with:

```python
def test_material_benefits_sum_boosts_and_group_items() -> None:
    """Stat boosts are summed and listed first; material items keep singles-then-
    repeats ordering, each group ordered by first occurrence."""
    character = _make_empty_character()
    character.benefits = [
        Benefit(kind="material", material_name="Weapon"),
        Benefit(kind="material", material_name="+1 Edu"),
        Benefit(kind="material", material_name="High Passage"),
        Benefit(kind="material", material_name="Weapon"),
        Benefit(kind="material", material_name="+1 Soc"),
        Benefit(kind="material", material_name="Weapon"),
    ]
    output = format_character(character)
    lines = output.split("\n")
    assert lines[-1] == "+1 Edu, +1 Soc, High Passage, Weapon x 3"
```

- [ ] **Step 2: Add the new boost-summing tests**

Append these tests to `tests/test_formatter.py`:

```python
def test_repeated_stat_boost_sums_into_single_entry() -> None:
    """Two "+1 Soc" rolls render as "+2 Soc", not "+1 Soc x 2"."""
    character = _make_empty_character()
    character.benefits = [
        Benefit(kind="material", material_name="+1 Soc"),
        Benefit(kind="material", material_name="+1 Soc"),
    ]
    output = format_character(character)
    assert output.split("\n")[-1] == "+2 Soc"


def test_single_stat_boost_renders_as_plus_one() -> None:
    """A stat boost rolled once stays "+1 Edu" (no "x 1")."""
    character = _make_empty_character()
    character.benefits = [Benefit(kind="material", material_name="+1 Edu")]
    output = format_character(character)
    assert output.split("\n")[-1] == "+1 Edu"


def test_triple_stat_boost_sums_to_plus_three() -> None:
    character = _make_empty_character()
    character.benefits = [
        Benefit(kind="material", material_name="+1 Str"),
        Benefit(kind="material", material_name="+1 Str"),
        Benefit(kind="material", material_name="+1 Str"),
    ]
    output = format_character(character)
    assert output.split("\n")[-1] == "+3 Str"


def test_boosts_and_items_full_example() -> None:
    """Reproduces the reported bug: "+1 Edu, +1 Soc x 2, Mid Passage, Weapon x 2"
    must render with Soc summed and boosts first."""
    character = _make_empty_character()
    character.benefits = [
        Benefit(kind="material", material_name="+1 Edu"),
        Benefit(kind="material", material_name="Mid Passage"),
        Benefit(kind="material", material_name="+1 Soc"),
        Benefit(kind="material", material_name="+1 Soc"),
        Benefit(kind="material", material_name="Weapon"),
        Benefit(kind="material", material_name="Weapon"),
    ]
    output = format_character(character)
    assert output.split("\n")[-1] == "+1 Edu, +2 Soc, Mid Passage, Weapon x 2"
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_formatter.py -k "boost or full_example or sum_boosts" -v --no-cov`

Expected: FAIL. The current implementation prints `+1 Soc x 2` and orders boosts
inline, so the new assertions do not match.

- [ ] **Step 4: Rewrite `_combine_material_benefits`**

Replace `src/cetools/formatter.py:10-28` with:

```python
def _combine_material_benefits(benefits: list[Benefit]) -> list[str]:
    names = [b.material_name for b in benefits if b.kind == "material"]

    boost_totals: dict[str, int] = {}
    boost_first_index: dict[str, int] = {}
    item_counts: dict[str, int] = {}
    item_first_index: dict[str, int] = {}
    for i, name in enumerate(names):
        if name.startswith("+1 "):
            label = name[3:]
            boost_totals[label] = boost_totals.get(label, 0) + 1
            boost_first_index.setdefault(label, i)
        else:
            item_counts[name] = item_counts.get(name, 0) + 1
            item_first_index.setdefault(name, i)

    boosts = [
        f"+{boost_totals[label]} {label}"
        for label in sorted(boost_totals, key=lambda label: boost_first_index[label])
    ]
    singles = sorted(
        (name for name, count in item_counts.items() if count == 1),
        key=lambda name: item_first_index[name],
    )
    repeats = sorted(
        (name for name, count in item_counts.items() if count > 1),
        key=lambda name: item_first_index[name],
    )

    return boosts + singles + [f"{name} x {item_counts[name]}" for name in repeats]
```

- [ ] **Step 5: Run the full formatter suite to verify it passes**

Run: `uv run pytest tests/test_formatter.py -v --no-cov`

Expected: PASS, including the updated `test_material_benefits_sum_boosts_and_group_items`
and the still-green `test_material_benefits_multiple_repeated_names_ordered_by_first_occurrence`
(no boosts, so its `High Passage x 2, Weapon x 2` output is unchanged).

- [ ] **Step 6: Format, lint, and run the full suite with coverage**

Run: `uv run black . && uv run flake8 src tests && uv run pytest`

Expected: Black reports no reformatting needed (or reformats cleanly), flake8 is
silent, pytest passes with coverage ≥85%.

- [ ] **Step 7: Verify against the real CLI**

Run: `uv run cetools character generate`

Expected: any repeated characteristic boost on the benefit line shows as `+N Stat`
(e.g. `+2 Soc`), never `+1 Stat x N`. Genuine items (`Weapon`, `Mid Passage`) still
use `x N` for repeats.

- [ ] **Step 8: Commit**

```bash
git add src/cetools/formatter.py tests/test_formatter.py
git commit -m "fix: sum repeated stat-boost mustering-out benefits"
```

---

## Self-Review

**Spec coverage:**
- Sum stat boosts into `+N Stat` → Task 1, Steps 2 & 4 (tests + `boost_totals`).
- Leave material items on `x N` path → Task 1, Step 4 (`item_counts`/`repeats`).
- Ordering: boosts, then singles, then repeats → Task 1, Step 4 return statement.
- Single boost stays `+1 Edu` → Task 1, Step 2 (`test_single_stat_boost_renders_as_plus_one`).
- `+1 X` unknown stat still sums → covered by detection using only the `"+1 "` prefix
  (no stat-name lookup), consistent with `_apply_stat_boost`.
- Update existing test asserting old form → Task 1, Step 1.

**Placeholder scan:** No TBD/TODO; every code and command step is concrete.

**Type consistency:** `_combine_material_benefits(benefits: list[Benefit]) -> list[str]`
signature is unchanged across spec, tests, and implementation. Helper dict names are
internal to the one function.
