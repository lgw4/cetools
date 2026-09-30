# Contract: kind declarations (internal)

The loader's one statement of what it knows about each kind of rules-data
file. **Internal**: `_Kind` and `_KINDS` are private to `src/cetools/rules.py`,
are not exported from `cetools`, and add nothing to
`contracts/library-api.md` (FR-002). The public contracts this feature must
leave byte-identical are the CLI's human-readable output (`tests/golden/`), its
`--json` output (`tests/contract/`), and the validation report's problems
(FR-012).

## The record

```python
@dataclass(frozen=True, slots=True)
class _Kind:
    name: str
    version: int
    arity: Literal["one", "many"]
    canonical_file: str | None = None
    parser: Callable[[Mapping[str, object], ParseContext], object] | None = None
```

- `parser`, when set, has the uniform one-file signature
  `(data, ctx) -> value | None` every loop-parsed kind already has.
- A declaration states a `parser` only if the general loop parses it.
  `background-skills`, `career`, and `surnames` state none; their explicit
  steps call `parse_background_skills`, `_parse_career`, and `_parse_surnames`
  directly, so no parser is named in two places (FR-001).

## The table

`_KINDS: tuple[_Kind, ...]`, one declaration per kind, in the order and with
the values listed in [../data-model.md](../data-model.md). It is the only
enumeration of kinds in the loader (FR-011).

## Readers

Every reader reads `_KINDS` at call time. No module-level value is derived
from it, so patching `rules._KINDS` is patching every reader (research R2).

| Reader | Question it asks | Requirement |
|---|---|---|
| `_packaged_kind_map` | is this `schema` string a kind? | FR-004 |
| `_validate` header check | is it a kind; what version does it support; what are all the kinds, sorted, for the unknown-kind problem | FR-005 |
| `_singleton_slots` | is this a one-file kind; which one-file kind lives at this basename | FR-006 |
| `_validate` missing/duplicate check | which kinds are one file; where does each live | FR-006 |
| `_validate` parse loop | which kinds does the general loop parse, and with what | FR-007 |
| `_validate` presence check | which kinds must each have produced a value | FR-008 |

## Invariants (tested, FR-015)

1. `name` is unique across `_KINDS`.
2. `arity` is `"one"` or `"many"`; `canonical_file` is set exactly when
   `arity == "one"`.
3. The one-file declarations without a `parser` are exactly
   `background-skills`; no many-file declaration has a `parser`.
4. Each one-file declaration's `canonical_file` is the packaged file that
   declares its `name` (the rewritten pinning test, FR-012).

No test asserts how many kinds there are (SC-005).

## Behavior the readers must preserve

- The unknown-kind problem's `expected` joins the kind names **sorted**, not in
  declaration order.
- Declaration order carries no behavior. One-file kinds are parsed in it;
  `problems.sort()` stays where it is and is what makes that unobservable
  (FR-013).
- A rejected file still occupies its one-file slot, by what it declared and by
  its basename, exactly as today.
- Presence: every one-file kind has a value, and at least one surname table is
  in force. No career requirement is added.

## Adding a kind (SC-003)

One `_Kind(...)` line, its parser, its `RulesData` field, and that field's
argument in the explicit constructor. A one-file kind with a uniform parser
needs nothing else; a many-file kind also needs its own loop, as `career` and
`surnames` have.
