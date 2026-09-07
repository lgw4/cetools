# Contract: the rules-data field-checking vocabulary

**Module**: `src/cetools/schema.py`

**Audience**: the five modules that parse rules data files—`rules.py`,
`careers.py`, `registries.py`, `names.py`, `chargen.py`.

**Status**: package-internal. Nothing here appears in `cetools/__init__.py`'s
`__all__`, and nothing outside the package is expected to import it
(spec FR-016).

This is not a public API contract in the sense of
`specs/001-dice-task-engine/contracts/library-api.md`. It is the internal
agreement the five parsers hold each other to, written down so that a rule
about what a data file may contain is stated once (FR-001).

## Shared conventions

Every check in this module follows the same shape, which is the shape the
sixteen private helpers already have. None of it is new.

- **`file`** is the data file's name, as it appears in a `ValidationProblem`.
- **`location`** is the field's dotted path, assembled by the caller as it
  descends (`throws.survival.target`). The vocabulary never builds a path; it
  receives the finished one. Giving the pair `(file, location)` a carrier of
  its own is out of scope (FR-020).
- **`problems`** is a caller-owned `list[ValidationProblem]` that every check
  appends to. Checks never raise and never return a problem; they accumulate,
  so one run reports everything wrong with a file rather than the first thing.
- **Return value** is the accepted value, or `None` when the field was
  rejected. `None` is the caller's failure signal. The one exception is
  `optional_bool`, which always returns a `bool` (FR-005).
- A **boolean is never an integer.** Every integer check rejects `bool`
  explicitly, because Python's `bool` subclasses `int` and a bare
  `isinstance(v, int)` would accept `true` in a numeric field (FR-012).
- **Absent and wrong-typed stay distinguishable** (FR-011). An absent key
  reports `found="missing"`; a present key of the wrong type reports
  `found=type_name(value)`, the data file's own word for the type.

## Interface

Seven functions. Bare-named, not underscore-prefixed: the parsers themselves
(`parse_career`, `parse_characteristics`, `parse_skills`, `parse_benefits`,
`parse_given_names`, `parse_surnames`, `parse_task_parameters`) are all bare
and all unexported, and this module follows them. The leading underscore is
reserved by `specs/001-dice-task-engine/contracts/library-api.md:124-125` for a
stronger promise about two specific symbols.

```python
def require_int(
    container: Mapping[str, object],
    key: str,
    file: str,
    location: str,
    problems: list[ValidationProblem],
    *,
    minimum: int | None = None,
) -> int | None: ...

def require_string(
    container: Mapping[str, object],
    key: str,
    file: str,
    location: str,
    problems: list[ValidationProblem],
) -> str | None: ...

def require_bool(
    container: Mapping[str, object],
    key: str,
    file: str,
    location: str,
    problems: list[ValidationProblem],
) -> bool | None: ...

def require_roll(
    container: Mapping[str, object],
    key: str,
    file: str,
    location: str,
    problems: list[ValidationProblem],
) -> str | None: ...

def require_dict(
    value: object,
    file: str,
    location: str,
    expected: str,
    problems: list[ValidationProblem],
) -> dict | None: ...

def optional_bool(
    container: Mapping[str, object],
    key: str,
    file: str,
    location: str,
    problems: list[ValidationProblem],
    *,
    default: bool = False,
) -> bool: ...

def unrecognized_key_problems(
    data: Mapping[str, object],
    allowed: frozenset[str],
    file: str,
    prefix: str = "",
) -> list[ValidationProblem]: ...
```

`require_dict` is the one check that takes a value rather than a container and
a key. Its five existing call sites in `careers.py` all pass a loop element or
a parameter already in hand; asking them to re-look-it-up would be a worse
interface than the one they have. See `research.md` R3 for why reading `None`
as "missing" is sound rather than a guess.

`unrecognized_key_problems` is the one check that returns its problems instead
of appending, because every call site does `problems.extend(...)` on the
result. It is left as it is; changing it would be a change for its own sake
across thirty-three call sites.

## Behavior, check by check

Each table below is the complete set of outcomes. The `found` and `expected`
columns are the exact strings, and are the contract: `SC-003` requires that
validating the packaged data and the invalid-fixture corpus produce messages
identical to today's, except where marked **CHANGED**.

### `require_int` (FR-002, FR-009, FR-010, FR-012)

| Condition | `found` | `expected` | Returns |
|---|---|---|---|
| key absent | `"missing"` | `"an integer"` | `None` |
| value is a `bool` | `"a boolean"` | `"an integer"` | `None` |
| value not an `int` | `type_name(value)` | `"an integer"` | `None` |
| `minimum is None` | — | — | the value |
| `value < minimum`, `minimum == 1` | `str(value)` | `"a positive integer"` | `None` |
| `value < minimum`, `minimum != 1` | `str(value)` | `f"an integer >= {minimum}"` | `None` |
| `value >= minimum` | — | — | the value |

The `minimum == 1` row is `careers._require_int`'s behavior, adopted as the
one behavior of the merged check. It is **CHANGED** for the six fields that
reach it through `chargen._require_int` today: `chargen.py:287` and
`chargen.py:587` (both a table row's `count`), and the `_CHARGEN_GROUPS`
entries `terms.term-years`, `terms.mishap-term-years`, `terms.cap`, and
`pension.minimum-terms`. `careers.py:360` (`throws.*.target`) already reports
"a positive integer" and does not change. `rules.py`'s two call sites pass no
`minimum` and are unaffected.

### `require_string` (FR-003, FR-009a)

| Condition | `found` | `expected` | Returns |
|---|---|---|---|
| key absent | `"missing"` | `"a non-empty string"` **CHANGED** | `None` |
| value is `""` | `"an empty string"` | `"a non-empty string"` | `None` |
| value not a `str` | `type_name(value)` | `"a non-empty string"` | `None` |
| value is a non-empty `str` | — | — | the value |

This is `registries._require_nonempty_string`'s behavior. The absent-key row is
the sole point on which the two merged checks differ, and it is **CHANGED** for
the thirteen `_require_string` call sites (three in `careers.py`, four in
`names.py`, six in `chargen.py`, including every `("string", …)` entry in
`_CHARGEN_GROUPS`). The two `_require_nonempty_string` sites
(`registries.py:246-247`) are unchanged.

The old wording described one rule two ways depending on how it was broken:
`"a string"` when the key was missing, `"a non-empty string"` when the value
was present and empty. The surviving wording is the accurate one.

### `require_bool` (FR-004)

| Condition | `found` | `expected` | Returns |
|---|---|---|---|
| key absent | `"missing"` | `"a boolean"` | `None` |
| value not a `bool` | `type_name(value)` | `"a boolean"` | `None` |
| value is a `bool` | — | — | the value |

### `require_roll` (FR-006, FR-010a)

| Condition | `found` | `expected` | Returns |
|---|---|---|---|
| key absent | `"missing"` | `"a string"` | `None` |
| value not a `str` | `type_name(value)` | `"a string"` | `None` |
| `_check_dice` raises | `repr(value)` | `str(exc)` | `None` |
| notation accepted | — | — | the value |

The absent-key row keeps `"a string"` and is deliberately **not** swept into
FR-009a's unification: this field requires valid dice notation, not a name with
something in it, so the two rules are different rules (FR-010a).

No existing test pins that row. `test_rules.py:459` is the only test asserting
`expected == "a string"`, and it sets `roll = 6`: it pins the *wrong-type* row,
one line below. `test_chargen.py:71-74` deletes `roll` and asserts `location`
and `found` but not `expected`. The behavioral commit adds the missing pin
before it edits any string check, and `test_rules.py:459` keeps passing
unchanged beside it.

Rejecting `d66` is `_check_dice`'s job, not this module's: the row a table
reads is the throw's total, and `d66` composes two faces into a two-digit
table value (001-dice-task-engine FR-029).

### `require_dict` (FR-007, FR-011)

| Condition | `found` | `expected` | Returns |
|---|---|---|---|
| `value is None` | `"missing"` | the caller's `expected` | `None` |
| value not a `dict` | `type_name(value)` | the caller's `expected` | `None` |
| value is a `dict` | — | — | the value |

The `expected` string is the caller's, because it names the table
(`"a [task] table"`, `"a table with label and class"`), which only the caller
knows.

The `None` row is **new to the named helper** but is not a behavior change: it
is what three of the sites this check absorbs already do by hand, and
preserving it is the point.

| Site | How it detects absence today |
|---|---|
| `rules.py:175` | `"missing" if task is None else type_name(task)` |
| `registries.py:284` | `"missing" if data is None else type_name(data)` |
| `chargen.py:1264` | `"missing" if group not in data else type_name(table)` |

The first two test the value; the third tests membership. They agree because
`table = data.get(group)` and a data file cannot write an empty value, so
`group not in data` and `table is None` are the same condition (research R3).

The remaining sites—`careers._require_dict`'s five callers,
`registries.py:231`, `chargen.py:1207`—have no absent case to preserve:
each passes an element obtained by iterating a table or an array, or a
parameter already known to be a value, so `None` never arrives. A merge that
dropped the row would have silently downgraded the first three sites from
`"missing"` to `"NoneType"`.

### `optional_bool` (FR-005)

| Condition | `found` | `expected` | Returns |
|---|---|---|---|
| key absent | *no problem reported* | — | `default` |
| value not a `bool` | `type_name(value)` | `"a boolean"` | `default` |
| value is a `bool` | — | — | the value |

The only check that always yields a value. A rejected optional boolean reports
the problem **and** still hands back the declared default, so no call site has
to branch on the rejected case. This is what `careers.py:944-972` does today
for `always-available` and `re-enterable`, twice, inline.

`default` is a keyword argument with the value `False` because that is what
both existing sites want. It is a parameter rather than a constant so the
signature does not have to change the first time a field defaults to `True`.

### `unrecognized_key_problems` (FR-008)

Returns one `ValidationProblem` per key in `data` that is not in `allowed`,
sorted by key name, each with:

- `location`: `f"{prefix}{key}"`
- `found`: `f"unrecognized key {key!r}"`
- `expected`: `f"one of: {', '.join(sorted(allowed))}"`

Returns the empty list when every key is admitted. The sort is what keeps a
report of the same file reading the same way on every run.

Byte-identical in all five modules today, so this one is a pure move.

## What this module does not do

Recorded so the boundary is explicit, and because FR-020 forbids reaching for
any of it in this feature:

- It does not carry a `(file, location)` cursor. Callers pass the pair and
  assemble dotted paths by f-string, exactly as they do now.
- It does not check arrays of parsed elements. The four candidate sites
  (`names._require_name_array`, `chargen._parse_rank_bonus_list`,
  `registries`' symbols loop, `careers`' entries arrays) parse four different
  element types and each carries its own did-any-element-fail bookkeeping.
- It does not host a declarative field table. `chargen._CHARGEN_GROUPS` stays
  in `chargen.py` and resolves each declared kind through these checks
  (FR-017).
- It does not resolve a skill, benefit, or characteristic name against a
  registry. `careers._notation_field` and `careers._skill_problem` are
  domain logic, not TOML type-checking, and stay where they are.

## Import position

```text
errors.py  ──┐
             ├──> schema.py ──> rules.py, careers.py, registries.py,
tasks.py   ──┘                  names.py, chargen.py
```

`schema.py` imports `ValidationProblem` and `type_name` from `errors.py`, and
`_check_dice` from `tasks.py`. It cannot live in `errors.py`: `require_roll`
needs `tasks._check_dice`, and `tasks.py` already does
`from cetools.errors import DiceError, RulesDataError, TaskError`
(`tasks.py:8`), so folding it in would close a cycle.
