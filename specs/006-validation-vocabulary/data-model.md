# Data Model: Validation Vocabulary

This feature adds no new data. It moves checks, so the "model" that matters is
the inventory of what moves and where it goes. The entities below are the
spec's Key Entities, mapped onto the code that already implements them; the
inventory that follows is the complete work list, gathered mechanically rather
than by reading, and is what `tasks.md` consumes.

## Entities

### Field check

A decision about whether one field of one data file holds an acceptable value.

| Aspect | Representation |
|---|---|
| Identity | A module-level function in `src/cetools/schema.py` |
| Inputs | The container and key (or, for `require_dict`, the value), plus `file`, `location`, and the caller's `problems` list |
| Output | The accepted value, or `None` when rejected; `optional_bool` always yields a `bool` |
| Side effect | Appends zero or one `ValidationProblem` to `problems` |
| Invariant | Never raises, never prints, never short-circuits a parse |

Seven of them, specified field by field in
[`contracts/schema-vocabulary.md`](contracts/schema-vocabulary.md).

### Validation problem

Already modeled, in `src/cetools/errors.py:52-66`. Unchanged by this feature.

```python
@dataclass(frozen=True, slots=True, order=True)
class ValidationProblem:
    file: str
    location: str = ""
    found: str = ""
    expected: str = ""
```

Sorts by `(file, location)` so a report is stable run to run. The vocabulary
constructs these and nothing else; it does not define, extend, or reorder them.

`errors.type_name` (`errors.py:32-49`) supplies the `found` half for a type
problem, naming a type the way a data file spells it. The vocabulary is the
layer that was missing on top of it: `type_name`'s own docstring gives the
motive for this whole feature, "Settled here rather than at each site so the
three schema modules cannot drift apart."

### Dotted location

The path identifying a field inside its file (`throws.survival.target`,
`mustering-out.rank-benefits[0].rank`). Built by the caller with f-string
concatenation as parsing descends, and passed to a check already finished.

Unchanged in form. Giving the `(file, location)` pair a carrier of its own is
explicitly out of scope (FR-020) and is easier to do later against one shared
module than now against five.

### Data-file kind

One category of rules data, each with its own schema and its own parser. Five
modules parse the kinds between them, and each will import the vocabulary
rather than restate it.

| Module | Kinds it parses | Lines |
|---|---|---|
| `rules.py` | task parameters; the composition and validation entry points | 1205 |
| `careers.py` | the twenty-four career files | 1037 |
| `registries.py` | characteristics, skills, benefits; pseudo-hex | 573 |
| `names.py` | given names, surnames | 251 |
| `chargen.py` | the universal chargen tables | 1320 |

### Declarative field table

`chargen._CHARGEN_GROUPS` (`chargen.py:1087-1137`): twelve groups, roughly
thirty-five flat scalar fields, each declared as `{key: (kind, minimum)}` where
`kind` is one of `"roll"`, `"bool"`, `"string"`, `"int"`.

Stays in `chargen.py` (FR-017). `_parse_chargen_group` (`chargen.py:1249-1305`)
keeps dispatching on `kind`; only the four functions it dispatches *to* change,
from chargen's private copies to the vocabulary. The table is not generalized:
`chargen.py` is the only module with enough flat fields for it to pay for
itself, and its own comment at `chargen.py:1080-1086` says so.

## Inventory: definitions to remove

Sixteen definitions of seven checks, across five modules. Every one is deleted;
`schema.py` gains one definition of each.

| Check | `rules.py` | `careers.py` | `registries.py` | `names.py` | `chargen.py` |
|---|---|---|---|---|---|
| `unrecognized_key_problems` | 142 | 117 | 131 | 17 | 30 |
| `require_int` | 269 | 169 | — | — | 80 |
| `require_string` | — | 145 | — | 32 | 115 |
| `require_roll` | — | 200 | — | — | 45 |
| `require_dict` | — | 132 | — | — | — |
| `require_bool` | — | — | — | — | 139 |
| `require_nonempty_string` | — | — | 253 | — | — |
| **Total** | **2** | **5** | **2** | **2** | **5** |

Confirmed identical by an AST comparison that hashed each definition on its
signature and body with docstrings stripped. Every group matches except:

- **`require_int`**, three variants. `careers.py:169` special-cases
  `minimum == 1` as `"a positive integer"`; `chargen.py:80` always writes
  `f"an integer >= {minimum}"`; `rules.py:269` has no `minimum` parameter.
- **`require_string` versus `require_nonempty_string`**, which differ on the
  absent-key case alone (`"a string"` versus `"a non-empty string"`) and agree
  on all three others.

Those two divergences are the whole of the behavioral change. FR-013 holds the
line against a third being absorbed silently.

## Inventory: named call sites to rewire

Seventy-three of them. Each becomes a call to the same-named function on the
vocabulary; no argument changes.

| Module | Check | Count | Lines |
|---|---|---|---|
| `rules.py` | `unrecognized_key_problems` | 2 | 166, 182 |
| `rules.py` | `require_int` | 2 | 212, 213 |
| `careers.py` | `unrecognized_key_problems` | 8 | 334, 381, 421, 506, 541, 660, 810, 924 |
| `careers.py` | `require_int` | 2 | 360, 544 |
| `careers.py` | `require_string` | 3 | 663, 941, 942 |
| `careers.py` | `require_roll` | 1 | 361 |
| `careers.py` | `require_dict` | 5 | 329, 416, 536, 655, 806 |
| `registries.py` | `unrecognized_key_problems` | 5 | 243, 290, 348, 445, 532 |
| `registries.py` | `require_nonempty_string` → `require_string` | 2 | 246, 247 |
| `names.py` | `unrecognized_key_problems` | 3 | 102, 143, 184 |
| `names.py` | `require_string` | 4 | 104, 145, 187, 188 |
| `chargen.py` | `unrecognized_key_problems` | 15 | 179, 283, 363, 401, 570, 581, 671, 729, 862, 929, 965, 1028, 1215, 1270, 1312 |
| `chargen.py` | `require_int` | 7 | 287, 587, 932, 933, 1216, 1217, 1283 |
| `chargen.py` | `require_string` | 6 | 286, 366, 586, 674, 968, 1281 |
| `chargen.py` | `require_bool` | 2 | 1032, 1279 |
| `chargen.py` | `require_roll` | 6 | 181, 404, 734, 735, 1031, 1277 |
| **Total** | | **73** | |

Per module: `rules.py` 4, `careers.py` 19, `registries.py` 7, `names.py` 7,
`chargen.py` 36.

## Inventory: inline sites to convert

Sites that express one of the seven checks by hand without ever naming it.
FR-015 covers these: leaving a known duplicate in place because nobody named it
does not count as finished.

| Site | Shape today | Becomes | Note |
|---|---|---|---|
| `rules.py:169-179` | dict check, `"missing" if task is None` | `require_dict` | keeps `"a [task] table"` |
| `rules.py:185-210` | roll check, fully inlined | `require_roll` | the third copy of `require_roll` |
| `rules.py:231-240` | int check inside `for name, value in dd.items()` | `require_int(dd, name, …)` | see below |
| `registries.py:176-186` | int check inside `for key, value in data.items()` | `require_int(data, key, …)` | see below |
| `registries.py:231-240` | dict check, no absent case | `require_dict` | keeps `"a table with label and class"` |
| `registries.py:279-288` | dict check, `"missing" if data is None` | `require_dict` | keeps `"a [pseudo-hex] table"` |
| `registries.py:292-300` | int check, `"missing" if "minimum" not in data` | `require_int(data, "minimum", …)` | |
| `chargen.py:1207-1213` | dict check, no absent case | `require_dict` | keeps `"a table"` |
| `chargen.py:1259-1268` | dict check, `"missing" if group not in data` | `require_dict` | keeps `"a table"` |
| `careers.py:944-957` | optional bool, `always-available` | `optional_bool` | |
| `careers.py:959-972` | optional bool, `re-enterable` | `optional_bool` | |

**The two loop sites.** `rules.py:231` and `registries.py:176` check a value
already in hand inside a loop, which reads at first like a shape the
container-and-key signature cannot express. It can: both loops iterate
`.items()`, so the container and the key are both present, and
`require_int(container, key, …)` simply looks the value up again. The key is
present by construction, so the absent-key branch is unreachable and the
wrong-type branch produces the identical message. Each loop tracks its own
`ok = False; continue` bookkeeping today; that becomes `if … is None`.

This matters because it is the difference between converting these two sites
and adding an eighth, value-taking integer check to the vocabulary. No eighth
check is needed, and adding one would be speculative abstraction (Principle VI).

**Not converted.** `registries.py:160-170` and `rules.py:217-227` reject a
table that is absent, wrong-typed, *or* empty, in one message naming the table
(`"a [difficulty-dms] table with at least one entry"`). That is a different
rule from `require_dict`'s, carrying a third condition and a compound message,
and folding it in would mean either a fourth parameter or a wording change
FR-013 forbids. `names._require_name_array` and
`chargen._parse_rank_bonus_list` are array checks, out of scope by FR-020.

## Inventory: behavioral blast radius

The two wording changes, and everything they reach. Both ship first, together,
in one behavioral commit, before any structural work (FR-019).

### `"an integer >= 1"` → `"a positive integer"` (FR-009)

Six fields, all reaching `chargen._require_int` with `minimum=1`:

| Field | Where declared |
|---|---|
| a draft-table row's `count` | `chargen.py:287` |
| a skill-table row's `count` | `chargen.py:587` |
| `terms.term-years` | `_CHARGEN_GROUPS`, `chargen.py:1096` |
| `terms.mishap-term-years` | `_CHARGEN_GROUPS`, `chargen.py:1097` |
| `terms.cap` | `_CHARGEN_GROUPS`, `chargen.py:1098` |
| `pension.minimum-terms` | `_CHARGEN_GROUPS`, `chargen.py:1127` |

`careers.py:360` (`throws.*.target`) is the only other `minimum=1` site and
already reports `"a positive integer"`. Every `minimum=0` and `minimum=None`
site is untouched.

### absent required text field: `"a string"` → `"a non-empty string"` (FR-009a)

Thirteen `_require_string` call sites: `careers.py` 3, `names.py` 4,
`chargen.py` 6 (including every `("string", …)` entry in `_CHARGEN_GROUPS`).
The two `_require_nonempty_string` sites already report the surviving wording.

`require_roll`'s absent-key wording stays `"a string"` and is not swept in
(FR-010a).

### Exposure

Neither change is pinned anywhere:

- No `tests/golden/` file contains an `expected` or `found` string; the golden
  corpus covers `roll`, `check`, and `npc` output, not validation reports.
- `README.md:122-128`, the one documented `validate` run, shows the success
  path only.
- Across `tests/`, `"a positive integer"` and `"an integer >= "` appear zero
  times; the only two occurrences in the repository are the two source lines
  being merged.
- The one test asserting `expected == "a string"` is `test_rules.py:459`,
  which covers `task.roll`—the roll check, excluded by FR-010a. It must keep
  passing unchanged. Note what it does *not* cover: it sets `roll = 6`, so it
  pins the wrong-type row, not the absent-key one. `test_chargen.py:71-74`
  deletes `roll` but asserts only `location` and `found`. So the absent-key
  `"a string"` FR-010a protects is pinned nowhere today, which is why the
  behavioral commit adds that test before touching any string check.
- The five other `"a string"` matches under `tests/` are all `found ==`, not
  `expected ==`: a string value found where another type was required. Unaffected.
