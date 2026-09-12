---
title: One rendering per result type
strength: Worth exploring
status: open
files: [src/cetools/render.py, src/cetools/character.py, tests/contract/test_npc_json.py, tests/unit/test_render.py, CLAUDE.md]
---

## Problem

`as_text` and `as_dict` are two independent `singledispatch` registries with
no shared structure and no parity check, so the rule that a new result type
must be added to both lives in `CLAUDE.md` as prose.

## Solution

Register each result type once, with its text and dict renderings together,
so a type registered on one path cannot be missing from the other.

## Wins

- Parity becomes structural, not documented
- Cross-path invariants stop being duplicated
- `_effect_text`'s silent fallback gets caught
- Removes an unused extension seam

## Diagram

Mass diagram. Before: two tall parallel columns — `as_text` with five
registrations, `as_dict` with five — and between them a dotted line labelled
"kept in agreement by CLAUDE.md", with a third small box off to the side
(`_effect_text`'s seven-arm `match` on a string kind) dotted across to
`_STEP_EFFECT_KINDS` in `character.py`. After: five rows, each holding both
renderings, and the dotted lines gone.

## Detail

Both generics live in `src/cetools/render.py`: `as_text` at `:96-97` with
registrations for `ThrowResult` (`:129`), `CheckResult` (`:151`),
`ValidationReport` (`:175`), `Character` (`:354`), `CharacterBatch` (`:373`);
`as_dict` at `:381-382` with the matching five at `:396`, `:408`, `:425`,
`:489`, `:516`. `as_json` (`:525-527`) delegates to `as_dict` by design.

Nothing compares the two registries. `tests/unit/test_render.py:537-539`
parametrizes over `[as_text, as_dict, as_json]` but only asserts each raises
for one *unregistered* type — it cannot detect a type registered on one and
missing from the other. `tests/contract/test_npc_json.py:137-150` checks
field-vs-emitted parity within the dict path only, and its own comment records
that `characteristic_symbols` was once added to `Character` and missed by
`as_dict`. The miss the design is meant to catch has already happened once.

The two paths share almost nothing:

| Concept | text | dict | shared |
|---|---|---|---|
| Provenance | `_provenance_lines` `:22-67` | `_provenance_dict` `:70-79` | no |
| Skill label | `_skill_label` `:195-198` | inlined at `:444-445` | no |
| `StepThrow` | `_throw_text` `:263-281` | `_step_throw_dict` `:462-471` | no |
| `StepEffect` | `_effect_text` `:284-302` | `_step_effect_dict` `:474-475` | no |
| `HistoryStep` | `_step_message` + `_history_lines` `:305-338` | `_history_step_dict` `:478-486` | no |
| `CareerService` | `_careers_line` `:220-225`, 2 of 9 fields | `_career_service_dict` `:448-459`, all 9 | no |

The skill-ordering expression is character-for-character identical on both
paths (`render.py:233` and `:494`); the comment at `:491-493` acknowledges the
duplication, and `tests/contract/test_npc_json.py:166-179` exists to catch the
two drifting by comparing JSON labels against line 3 of the rendered sheet.
Modifier formatting is written twice on the text side and twice on the dict
side.

Two further seams to weigh in the same conversation:

- **`_effect_text` (`render.py:288-302`)** is a `match` on `StepEffect.kind`,
  a string, over seven literal arms plus `case _`. Its `case _` silently falls
  back to `effect.subject` rather than raising, unlike both `singledispatch`
  fallbacks. The closed vocabulary it must track is `_STEP_EFFECT_KINDS`
  (`src/cetools/character.py:51-67`); the two lists agree by convention only.
  This is a third place a new concept needs editing, and the only one that
  fails quietly.
- **`characteristic_symbols`** is not a seam but a workaround for a missing
  one. It is computed at `generator.py:1642-1644`, stored on `Character`
  (`character.py:171`), and read once at `render.py:217`, because `as_text`
  has no parameter to receive the rules that generated the character — a
  constraint pinned by `specs/003-npc-generator/contracts/library-api.md`.
  One producer, one consumer, documented three times.

On the deletion test, `singledispatch` itself is the weak part: five
registrations, all co-located with their generic, nothing outside `render.py`
ever calling `.register`. That is one adapter's worth of variation behind an
open-extension mechanism — a hypothetical seam. It is not free: two
independent registries are exactly what makes the parity obligation
impossible to see at a glance.

Note the blast radius. `--json` output is pinned by `tests/contract/`, and
human-readable output by `tests/golden/`, so this is a structural change that
must leave both byte-identical. That is a good property for grilling: the
suite will say plainly whether the collapse was behavior-preserving.
