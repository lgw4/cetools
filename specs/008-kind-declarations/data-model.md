# Data model: Kind Declarations

One internal entity and one table of it. Nothing here is public: neither name
is exported from `cetools`, and `contracts/library-api.md` is unchanged
(FR-002). The full field-by-field contract is
[contracts/kind-declarations.md](contracts/kind-declarations.md).

## `_Kind` (private, `src/cetools/rules.py`)

| Field | Type | Meaning |
|---|---|---|
| `name` | `str` | The `schema` string a file declares in its header. Unique across the table. |
| `version` | `int` | The supported `schema-version`, an integer literal never derived from the package version. |
| `arity` | `Literal["one", "many"]` | Whether the kind is one file or many. |
| `canonical_file` | `str \| None` | The packaged basename a one-file kind lives at, and the name an override replaces it under. `None` if and only if `arity == "many"`. |
| `parser` | parser callable `\| None` | Set if and only if the general one-file loop parses the kind. |

Frozen and slotted. No `RulesData` field name.

### Validation rules (pinned by tests, FR-015)

- `name` is unique across `_KINDS`.
- `arity` is `"one"` or `"many"`.
- `arity == "one"` ⇔ `canonical_file is not None`.
- `parser is not None` ⇔ `arity == "one"` and `name != "background-skills"`.
- For every `"one"` declaration, the packaged file at `canonical_file`
  declares `name` (the rewritten pinning test).

No count of declarations is asserted anywhere (SC-005).

## `_KINDS: tuple[_Kind, ...]`

Thirteen declarations in reader order, grouped by the module owning the
kind's parser (FR-003). The order carries no behavior.

| name | version | arity | canonical_file | parser |
|---|---|---|---|---|
| `task-parameters` | 2 | one | `tasks.toml` | `parse_task_parameters` |
| `characteristics` | 2 | one | `characteristics.toml` | `parse_characteristics` |
| `skills` | 2 | one | `skills.toml` | `parse_skills` |
| `benefits` | 1 | one | `benefits.toml` | `parse_benefits` |
| `career` | 4 | many | | |
| `draft-table` | 1 | one | `draft.toml` | `parse_draft_table` |
| `aging-table` | 1 | one | `aging.toml` | `parse_aging_table` |
| `mishap-table` | 1 | one | `mishaps.toml` | `parse_mishap_table` |
| `background-skills` | 1 | one | `background-skills.toml` | (explicit step) |
| `medical-tiers` | 1 | one | `medical-tiers.toml` | `parse_medical_tiers` |
| `chargen-parameters` | 2 | one | `chargen-parameters.toml` | `parse_chargen_parameters` |
| `given-names` | 1 | one | `given-names.toml` | `parse_given_names` |
| `surnames` | 1 | many | | |

Every value is transcribed from the four tables it replaces
(`rules.py:58-99` at `0074436`); none changes.

## What it replaces

| Today | After |
|---|---|
| `_SUPPORTED_VERSION` (13 entries; its keys are also the set of kinds) | `k.version`, `k.name` |
| `_SINGLETON_KINDS` (11) | `k.arity == "one"` |
| `_CANONICAL_FILE` (11) | `k.canonical_file` |
| `_KIND_AT_CANONICAL_FILE` (derived) | a scan for `k.canonical_file == basename` in `_singleton_slots` |
| ten `parse_singleton(...)` calls, lines 636-651 | one loop over `k.parser is not None` |
| the eleven `... is None` clauses, lines 1036-1046 | `any(values.get(k.name) is None for one-file k)` |

Kept as they are: the background-skills step (now storing into `values`), the
career and surname loops with their duplicate checks (FR-009), the
`not surnames` clause (FR-008), the explicit `RulesData(...)` construction
reading `values[...]` field by field (FR-010), and `problems.sort()` (FR-013).

## Transient state inside `_validate`

`values: dict[str, Any]`, keyed by kind name, holding each one-file kind's
parsed value or `None`. The parse loop and the background-skills step store an
entry for every one-file kind; a kind that did not resolve to exactly one file
stores `None`, because `parse_singleton` returns `None` for it, as today.
