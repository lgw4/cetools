"""SC-003 through SC-008, SC-019, SC-020: the sampled audits. Marked
`slow` (research R14) — a thousand seeds for the always-living and
consistency audits, ten thousand rolled names for the regional weighting
check — so the inner development loop (`-m "not slow"`) stays fast while
CI still runs every seed SC-003 requires.
"""

import pytest

from cetools.dice import Roller
from cetools.generator import _Walk, generate_character
from cetools.names import roll_name
from cetools.notation import SkillGrant, SkillReference
from cetools.rules import load_rules

pytestmark = pytest.mark.slow

RULES = load_rules()
_SAMPLE_SIZE = 1000


@pytest.fixture(scope="module")
def sample():
    return [generate_character(Roller(i), RULES) for i in range(_SAMPLE_SIZE)]


def _steps_by_service(character):
    """Partition `character.history` into one slice per `CareerService`, by
    position: a "career-entered" step opens a new slice, matching
    `character.careers`'s own order one for one (generator.py's `run`
    appends both in lockstep). Lets a re-entered career (two separate
    Drifter stints, say) be told apart by position rather than by name
    alone.
    """
    slices: list[list] = []
    for step in character.history:
        if step.kind == "career-entered":
            slices.append([])
        if slices:
            slices[-1].append(step)
    return slices


def _mishap_row(service_steps):
    """The mishap row that ended this service, or `None` if it did not end
    in one — the first "mishap" step carrying a throw. A later
    effect-recording sub-step (T183) also carries one, but the
    row-selection roll's own step is always appended first, so `next(...)`
    still finds it; `selected` is only ever populated on the row-selection
    step, which the second `next(...)` below relies on.
    """
    step = next((s for s in service_steps if s.kind == "mishap" and s.throw), None)
    if step is None:
        return None
    return next(row for row in RULES.mishaps.rows if row.description == step.selected)


def _replay_characteristics(history):
    """Reconstruct every characteristic's final score purely from the
    history's own `characteristic` effects (T153): the `"characteristics"`
    step's effects are absolute starting scores, and every later
    `characteristic` effect is a signed delta.

    A floor clamp's called-for reduction carries its own kind,
    `characteristic-called-for`, distinct from `characteristic` (T165), so
    it is excluded here by kind alone rather than by an adjacency
    convention that could not tell a clamp pair from two genuine
    independent reductions of the same characteristic in one step — which
    a `"debt-settled"` step's restoration loop (T157) can produce, one real
    `+1` per point restored.
    """
    scores: dict[str, int] = {}
    for step in history:
        if step.kind == "characteristics":
            for effect in step.effects:
                scores[effect.subject] = effect.amount
            continue
        for effect in step.effects:
            if effect.kind == "characteristic":
                scores[effect.subject] = scores.get(effect.subject, 0) + effect.amount
    return scores


def _replay_funds(history):
    """Reconstruct `character.funds` from the history alone (T153): every
    `credits` effect is money gained (a mustering-out cash roll), and every
    `debt` effect on a `"debt-settled"` step is money spent paying a debt
    down — the only two places `_Walk.funds` is ever mutated. A `debt`
    effect on any other step kind (a mishap, `medical-bills`, or
    `medical-crisis`) records a debt being *created*, which does not touch
    funds at all.
    """
    funds = 0
    for step in history:
        for effect in step.effects:
            if effect.kind == "credits":
                funds += effect.amount
            elif effect.kind == "debt" and step.kind == "debt-settled":
                funds -= effect.amount
    return funds


class TestAlwaysLivingAndConsistency:
    def test_sc003_every_seed_produces_a_living_complete_character(self, sample):
        for character in sample:
            assert character.name
            assert character.careers
            assert character.history

    def test_sc004_every_character_is_internally_consistent(self, sample, cascade_reachable_names):
        cap = RULES.chargen.terms_cap
        params = RULES.chargen
        for character in sample:
            assert character.funds >= 0
            assert character.debt >= 0
            total_terms = sum(service.terms for service in character.careers)
            assert total_terms <= cap
            assert character.age >= params.terms_starting_age
            for service in character.careers:
                career = next(c for c in RULES.careers.values() if c.name == service.career)
                ladder = next(lad for lad in career.ladders if lad.name == service.ladder)
                assert any(rank.rank == service.rank for rank in ladder.ranks)
            # No consequence appears that no history step produced: every
            # career the character served has at least a career-entered step.
            entered_careers = {
                step.career for step in character.history if step.kind == "career-entered"
            }
            assert {service.career for service in character.careers} <= entered_careers

            slices = _steps_by_service(character)
            assert len(slices) == len(character.careers)
            expected_age = params.terms_starting_age
            expected_pension = 0
            for service, steps in zip(character.careers, slices):
                row = _mishap_row(steps) if service.ended == "mishap" else None

                # Age matches the terms served and how each ended (SC-004,
                # T152): a mishap-ended term costs the shorter number of
                # years plus whatever extra years its row names, every
                # other term costs the ordinary number.
                if row is not None:
                    extra_years = sum(
                        int(effect.amount) for effect in row.effects if effect.kind == "years"
                    )
                    expected_age += (
                        (service.terms - 1) * params.terms_term_years
                        + params.terms_mishap_term_years
                        + extra_years
                    )
                else:
                    expected_age += service.terms * params.terms_term_years

                # The benefit rolls taken match the terms served (FR-020's
                # exactly-once forfeiture) and the rank reached (the rank
                # bonus `muster_out_service` adds before rolling) — both
                # halves, since `benefit_rolls` records the rolls actually
                # taken, not the term-derived half alone (T188).
                forfeit_all = row is not None and any(
                    effect.kind == "forfeit-career-benefits" for effect in row.effects
                )
                forfeited_terms = 1 if row is not None else 0
                rank_bonus = _Walk._highest_matching_rank_row(
                    params.mustering_out_rank_benefits, service.rank
                )
                expected_benefit_rolls = (
                    0 if forfeit_all else max(0, service.terms - forfeited_terms) + rank_bonus
                )
                assert service.benefit_rolls == expected_benefit_rolls
                mustering_steps = sum(1 for s in steps if s.kind == "benefit" and s.term == 0)
                # A forfeited service takes no rolls at all, rank-derived
                # bonus included — not merely the term-count half of it
                # `benefit_rolls` already records (T168).
                expected_mustering_steps = 0 if forfeit_all else service.benefit_rolls
                assert mustering_steps == expected_mustering_steps

                # A pension matches the terms served in a single career,
                # never summed across several (FR-018, research R10 item 7).
                pension_steps = [s for s in steps if s.kind == "pension"]
                if service.terms >= params.pension_minimum_terms:
                    assert len(pension_steps) == 1
                    amount = params.pension_base + params.pension_per_additional_term * (
                        service.terms - params.pension_minimum_terms
                    )
                    assert pension_steps[0].effects[0].amount == amount
                    expected_pension += amount
                else:
                    assert pension_steps == []
            assert character.age == expected_age
            assert character.pension == expected_pension

            # Every skill traces to a table in a career the character
            # actually served, or to background skills / basic training,
            # which carry no career (SC-004, T152). T211 strengthens this
            # beyond career-label membership, which cannot catch a skill
            # drawn from a table belonging to another career, a table the
            # character's characteristics gate out being drawn anyway, or
            # a `rank-bonus` skill no reached rank declares: a single pass
            # over the whole history replays characteristics and ladder
            # position in order, since a table's gate or a ladder's rank
            # can change mid-walk between one skill roll and the next.
            served = {service.career for service in character.careers}
            running_characteristics: dict[str, int] = {}
            service_index = -1
            current_career = None
            current_ladder = None
            current_rank = 0
            for step in character.history:
                if step.kind == "characteristics":
                    for effect in step.effects:
                        running_characteristics[effect.subject] = effect.amount
                    continue

                if step.kind == "career-entered":
                    service_index += 1
                    entered_service = character.careers[service_index]
                    current_career = next(
                        c for c in RULES.careers.values() if c.name == entered_service.career
                    )
                    current_ladder = next(
                        lad for lad in current_career.ladders if lad.role == "entry"
                    )
                    current_rank = 0

                if any(effect.kind == "skill" for effect in step.effects):
                    assert step.career in served | {""}

                if step.kind == "skill-roll":
                    # `step.term` lies within the service that rolled it
                    # (SC-004's "in a term they served"), the table
                    # `selected` names was gate-eligible for the character
                    # at the time of the roll (not necessarily at replay
                    # time — a later term's aging can still lower the
                    # gating characteristic), and the granted skill is one
                    # of that table's own entries.
                    service = character.careers[service_index]
                    assert 1 <= step.term <= service.terms
                    table = current_career.tables[step.selected]
                    if table.requires is not None:
                        assert (
                            running_characteristics[table.requires.characteristic]
                            >= table.requires.target
                        )
                    entry_names = {
                        entry.skill.name if isinstance(entry, SkillGrant) else entry.name
                        for entry in table.entries
                        if isinstance(entry, (SkillGrant, SkillReference))
                    }
                    # A cascade entry's bare grant may resolve into a nested
                    # cascade's own name rather than the entry's literal one
                    # (FR-012, D5) — `Vehicle` drawing `Aircraft` reports
                    # `Aircraft (...)`, not `Vehicle (...)`.
                    reachable_names = set().union(
                        *(cascade_reachable_names(name) for name in entry_names)
                    )
                    for effect in step.effects:
                        if effect.kind == "skill":
                            assert effect.subject.split(" (", 1)[0] in reachable_names
                elif step.kind == "commission" and step.throw is not None and step.throw.success:
                    commissioned_ladder = next(
                        (lad for lad in current_career.ladders if lad.role == "commissioned"),
                        None,
                    )
                    if commissioned_ladder is not None:
                        current_ladder = commissioned_ladder
                        current_rank = commissioned_ladder.ranks[0].rank
                elif step.kind == "advancement" and step.throw is not None and step.throw.success:
                    ranks_above = sorted(
                        r.rank for r in current_ladder.ranks if r.rank > current_rank
                    )
                    if ranks_above:
                        current_rank = ranks_above[0]
                elif step.kind == "rank-bonus":
                    # The granted skill matches the bonus the reached
                    # ladder rank actually declares — no rank of that
                    # career's ladders declaring one, or a bonus from a
                    # ladder or rank the walk did not reach, both caught.
                    rank_row = next(r for r in current_ladder.ranks if r.rank == current_rank)
                    if rank_row.bonus is None:
                        assert step.effects == ()
                    elif isinstance(rank_row.bonus, (SkillGrant, SkillReference)):
                        bonus_name = (
                            rank_row.bonus.skill.name
                            if isinstance(rank_row.bonus, SkillGrant)
                            else rank_row.bonus.name
                        )
                        skill_effects = [e for e in step.effects if e.kind == "skill"]
                        assert skill_effects
                        for effect in skill_effects:
                            assert effect.subject.split(" (", 1)[0] == bonus_name

                for effect in step.effects:
                    if effect.kind == "characteristic":
                        running_characteristics[effect.subject] = (
                            running_characteristics.get(effect.subject, 0) + effect.amount
                        )

    def test_sc005_every_field_traces_to_a_history_step(self, sample):
        """Every characteristic, skill, career, credit, and item on a sheet
        traces to a step (US2 goal), read from the steps' named parts and
        never from rendered text.
        """
        for character in sample:
            skill_effects = {
                effect.subject
                for step in character.history
                for effect in step.effects
                if effect.kind == "skill"
            }
            for skill in character.skills:
                label = (
                    skill.name if skill.specialty is None else f"{skill.name} ({skill.specialty})"
                )
                assert label in skill_effects

            characteristic_effects = {
                effect.subject
                for step in character.history
                for effect in step.effects
                if effect.kind == "characteristic"
            }
            assert set(character.characteristics) <= characteristic_effects

            # Subject presence alone would still pass with the right names
            # and the wrong numbers; replaying the history's own effects
            # must reproduce the sheet's actual scores and funds (T153,
            # what makes this check able to fail on a T144-style
            # regression: an unrecorded settlement leaves funds too high).
            assert _replay_characteristics(character.history) == dict(character.characteristics)
            assert _replay_funds(character.history) == character.funds

            entered_careers = {
                step.career for step in character.history if step.kind == "career-entered"
            }
            assert {service.career for service in character.careers} <= entered_careers

            credit_effects = [
                effect
                for step in character.history
                for effect in step.effects
                if effect.kind == "credits"
            ]
            if character.funds > 0:
                assert credit_effects

            benefit_effects = {
                effect.subject
                for step in character.history
                for effect in step.effects
                if effect.kind == "benefit"
            }
            for item in character.benefits:
                assert item in benefit_effects


class TestSpreadAndCoverage:
    def test_sc006_ages_spread_rather_than_parked_at_the_cap(self, sample):
        cap = RULES.chargen.terms_cap
        term_counts = {sum(service.terms for service in c.careers) for c in sample}
        assert len(term_counts) >= 5
        at_cap = sum(1 for c in sample if sum(s.terms for s in c.careers) >= cap)
        assert at_cap <= len(sample) / 4

    def test_sc007_multi_career_characters_occur(self, sample):
        assert any(len(c.careers) == 2 for c in sample)
        assert any(len(c.careers) == 3 for c in sample)

    def test_sc008_every_shape_the_engine_handles_is_exercised(self, sample):
        commissioned = any(service.commissioned for c in sample for service in c.careers)
        not_commissioned = any(not service.commissioned for c in sample for service in c.careers)
        assert commissioned and not_commissioned

        tiers_charged = set()
        for character in sample:
            for step in character.history:
                if step.kind == "medical-bills":
                    career = next(c for c in RULES.careers.values() if c.name == step.career)
                    tiers_charged.add(career.medical_tier)
        assert tiers_charged == set(RULES.medical_tiers.tiers)

        drifter_fallback = any(
            service.career == "Drifter" and service.entered_by == "fallback"
            for c in sample
            for service in c.careers
        )
        drifter_reentered = any(
            sum(1 for service in c.careers if service.career == "Drifter") >= 2 for c in sample
        )
        assert drifter_fallback and drifter_reentered

        draft_rows_reached = {
            step.selected for c in sample for step in c.history if step.kind == "draft"
        }
        assert draft_rows_reached == set(RULES.draft.careers)

        # FR-033, FR-007b (T155): promotion off the entry ladder is a shape
        # the engine already handles, but until the shipped data gives at
        # least one entry ladder a rank above zero, `ranks_above` is always
        # empty for an uncommissioned character and the path goes
        # unexercised by every shipped career.
        uncommissioned_rank_above_zero = any(
            not service.commissioned and service.rank > 0 for c in sample for service in c.careers
        )
        assert uncommissioned_rank_above_zero


class TestDefaultRenderingCoverage:
    def test_sc020_every_default_field_is_present_and_nothing_from_the_walk_leaks(self, sample):
        # SC-020's completeness half is a claim about every field the format
        # has a place for, not about the rendering as a whole being
        # non-empty — `assert text` passes for a sheet missing every field
        # but one, and checking only the first 200 of the thousand-seed
        # sample leaves 800 unchecked (T156). Every field below is one
        # `contracts/cli.md` requires unconditionally; the benefit-items
        # line is the one line the format itself may omit, so its absence is
        # not asserted against.
        from cetools.render import as_text

        for character in sample:
            text = as_text(character)
            lines = text.split("\n")
            assert len(lines) in (3, 4)

            line1_fields = lines[0].split("\t")
            assert len(line1_fields) == 3
            for field in line1_fields:
                assert field

            line2_fields = lines[1].split("\t")
            assert len(line2_fields) == 2
            for field in line2_fields:
                assert field

            assert lines[2]  # the skills line

            if len(lines) == 4:
                assert lines[3]  # the benefit-items line, when present

            for leak in ("Seed:", "Rules:", "cetools", "Debt:", "Pension:", "History:"):
                assert leak not in text

            # The labels above are one way SC-020's absence half could be
            # violated; the values themselves are another. A renderer that
            # dropped the "Debt:" label but folded the figure into another
            # field, or printed a step's own kind string, would leave every
            # assertion above intact. (The seed itself gets the same check,
            # separately below: this sample's seeds are small sequential
            # ints, so `str(character.seed)` collides with an unrelated
            # digit — an age, a fund total — too often here to be sound.)
            for step in character.history:
                assert step.kind not in text
            if character.debt:
                assert f"Cr{character.debt:,}" not in text
            if character.pension:
                assert f"Cr{character.pension:,}" not in text

    def test_the_seed_itself_does_not_leak_into_the_default_sheet(self):
        # Reusing `sample`'s small sequential seeds (0-999) for this check
        # would false-positive: `str(0)` or `str(34)` collides with an
        # unrelated digit elsewhere on the sheet (an age, a fund total, a
        # skill level) far too often to mean anything. A seed derived from
        # an arbitrary string instead folds to a ~19-digit int (FR-002,
        # `resolve_seed`), which cannot coincidentally appear in a sheet.
        from cetools.render import as_text

        for i in range(20):
            character = generate_character(Roller(f"sc020-seed-leak-check-{i}"), RULES)
            assert str(character.seed) not in as_text(character)


def test_sc019_name_weighting_is_over_tables_not_over_names():
    roller = Roller("name-weighting-sample")
    region_counts: dict[str, int] = {}
    for _ in range(10_000):
        name = roll_name(roller, RULES.given_names, RULES.surnames)
        region_counts[name.region] = region_counts.get(name.region, 0) + 1

    table_count = len(RULES.surnames)
    expected_share = 1 / table_count
    # Iterating only the regions the sample happened to draw would let a
    # weighting mistake that drops a region entirely — zero draws, so it
    # never becomes a key in `region_counts` — pass the very criterion it
    # exists to catch (T158, SC-019). Every surname table in force must be
    # represented.
    assert set(region_counts) == {table.region for table in RULES.surnames.values()}
    for region, count in region_counts.items():
        share = count / 10_000
        assert 0.9 * expected_share <= share <= 1.1 * expected_share, (region, share)


def test_sc019_a_characters_recorded_region_matches_the_table_its_surname_came_from(sample):
    # The weighting check above calls `roll_name` directly, bypassing
    # `generate_character` entirely — nothing anywhere asserted that a
    # *generated* character's own `surname_region` field is the region of
    # the table its surname actually came from. A defect in
    # `generate_character`'s `surname_region = rolled.region` line would
    # pass both SC-018 (field-by-field name comparison) and the weighting
    # check above, since neither reads a generated character's own field
    # against the table data (T176, FR-047d).
    names_by_region = {
        table.region: {entry.name for entry in table.names} for table in RULES.surnames.values()
    }
    checked = 0
    for character in sample:
        if character.surname_region == "":
            continue
        assert character.surname_region in names_by_region
        assert character.surname in names_by_region[character.surname_region]
        checked += 1
    assert checked
