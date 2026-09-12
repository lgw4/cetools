---
title: Name the term loop's carried state
strength: Strong
status: open
files: [src/cetools/generator.py, tests/unit/test_generator.py, tests/integration/test_traversal.py]
---

## Problem

`run_term_loop` is 297 lines carrying eight loop locals it must hand back as
an unannotated seven-tuple, while `(career_name, term)` is re-supplied by hand
to nine other methods that only need it to label a history step.

## Solution

Give one career's service a record — career, ladder, rank, commission, term,
benefit rolls, how it ended — that the loop mutates and every step-recording
method reads, instead of parameters and a tuple.

## Wins

- Seven-tuple return becomes one value
- `(career_name, term)` stops threading nine signatures
- `_apply_entry`'s five-argument bundle collapses
- Term loop's sections become nameable
- Tests stop re-implementing `run`

## Diagram

Mass diagram plus call-graph collapse. Before: one very tall `run_term_loop`
box (297 lines, five `break` sites setting a sentinel string) with eight
loop-local state pins along its left edge and a seven-wire ribbon leaving the
bottom into `muster_out_service` and `CareerService`; around it, nine method
boxes each with a `(career_name, term)` stub bolted on. After: a `Service`
record box the loop and the nine methods both touch, one wire out, and the
stubs gone.

## Detail

`run_term_loop` (`generator.py:662`) has no return annotation at all; the
contract is a docstring sentence: "Returns `(terms, ladder, rank,
commissioned, ended, benefit_rolls, forfeit_all)`." The destructure is a
single statement at `generator.py:1564-1566`, and six of the seven values are
immediately re-passed positionally into `muster_out_service` and
`CareerService(...)` (`:1570-1584`).

The state is split against itself. `_Walk` keeps `self.age`,
`self.total_terms_served`, `self.title` as fields, but rank, ladder and
commission live only as loop locals (`generator.py:667-674`) and must be
plumbed out. Nothing distinguishes the two groups except history.

`(career_name, term)` is threaded through nine signatures purely for
labeling: `_grant_rank_bonus` (`:442`), `_apply_class_effect` (`:960`),
`_trigger_medical_crisis` (`:1023`), `_roll_injury` (`:1061`),
`_raise_medical_bill` (`:1090`), `_apply_aging_if_due` (`:1186`),
`_roll_skills` (`:1303`), `settle_debts` (`:315`), `add_debt` (`:370`).
`_Walk` has no current-career or current-term field, so the pair is
re-supplied at every call site.

A related bundle: `_apply_entry` (`generator.py:173-180`) takes six
parameters, five of which are pieces of one `_Walk`
(`characteristics`, `skills_registry`, `skills`, `roller`, `floor`). The
identical five-argument bundle is re-assembled from `self` at `:448-455`,
`:637-644`, and `:1324-1331`. `_resolve_specialty` and
`_apply_characteristic_delta` do the same at smaller scale.

Two symptoms confirm the shape is wrong rather than merely large:

- `muster_out_service`'s `ladder: str` parameter (`generator.py:1366`) is
  never read in its 184-line body — the only occurrence of the token in
  `:1362-1545` is the signature line. It is still supplied by the production
  call site and by every test that drives the method directly.
- `pension_qualified` and `cash_taken` are character-wide accumulators whose
  scope is documented in prose comments (`:1379-1384`, `:1400-1402`) rather
  than expressed by any type.

Testability is where this bites hardest.
`tests/integration/test_traversal.py:24-49` re-implements the per-career body
of `_Walk.run` step by step, ending in the seven-tuple destructure, and its
docstring says the reconstruction is deliberate. The same reconstruction
appears twice more in `tests/unit/test_generator.py` (`:510-524`, `:571-576`).
No test calls `walk.run()` at all. Three test modules rebuild the sequence
because there is no value they can hold that represents one service in
progress.

Duplication that a service record would let collapse: "choose N
characteristics of a class and reduce them" is written twice, near-identically
— `_apply_class_effect` (`:984-1005`) and `_apply_aging_if_due` (`:1253-1277`),
the second differing only by also collecting `crisis_codes`, with a comment
at `:1273-1274` pointing at the first. "Record before `add_debt`" is written
three times (`:743-756`, `:1028-1059`, `:1154-1167`).
