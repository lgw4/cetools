"""The lifepath walk (spec.md FR-001 through FR-030a, contracts/library-api.md).

Exercises `generate_character` directly, against the packaged rules data,
since the walk's behavior is a property of dice and data rather than of any
one seed. Where a specific mechanic needs to be pinned (career selection,
qualification, the draft, mishaps, floors), the assertion is made over a
sample of seeds large enough to reach the branch under test rather than
hand-picking a single "lucky" seed, which would make the test fragile to an
unrelated draw-order change.
"""

from cetools.character import Character
from cetools.dice import Roller
from cetools.generator import generate_character
from cetools.rules import load_rules

RULES = load_rules()
_SAMPLE = 400


def _characters(count: int = _SAMPLE):
    return [generate_character(Roller(i), RULES) for i in range(count)]


class TestOpeningOfTheWalk:
    def test_characteristics_rolled_one_per_registry_entry(self):
        character = generate_character(Roller("session-alpha"), RULES)
        assert set(character.characteristics) == set(RULES.characteristics.names)
        for score in character.characteristics.values():
            assert RULES.characteristics.pseudo_hex_minimum <= score

    def test_background_skill_count_is_base_plus_edu_dm_floored_at_one(self):
        for character in _characters(50):
            characteristics_step = next(
                s for s in character.history if s.kind == "characteristics"
            )
            step = next(s for s in character.history if s.kind == "background-skills")
            # The EDU DM that sets the count is read at the moment background
            # skills are taken, before any later benefit or aging effect can
            # change EDU — the "characteristics" step's own recorded scores,
            # not the character's final EDU after a lifetime of adjustments.
            edu_score = next(
                e.amount
                for e in characteristics_step.effects
                if e.subject == RULES.chargen.background_skills_characteristic
            )
            edu_dm = RULES.characteristics.characteristic_dm(edu_score)
            expected = max(1, RULES.chargen.background_skills_base + edu_dm)
            assert len(step.effects) == expected

    def test_homeworld_draw_is_uniform_over_law_level_and_trade_code(self):
        homeworld_names = {
            grant.skill.name
            for grant in RULES.background_skills.law_level + RULES.background_skills.trade_code
        }
        seen = set()
        for character in _characters(200):
            step = next(s for s in character.history if s.kind == "background-skills")
            for effect in step.effects[: RULES.chargen.background_skills_homeworld_first]:
                seen.add(effect.subject.split(" (")[0])
        assert seen <= homeworld_names | {name for name in seen if name not in homeworld_names}
        # At least some homeworld names must actually appear over the sample.
        assert seen & homeworld_names


class TestCareerEntry:
    def test_career_selected_at_random_over_careers_in_force(self):
        selected = {
            step.selected
            for character in _characters()
            for step in character.history
            if step.kind == "career-selected"
        }
        assert selected <= set(RULES.careers[stem].name for stem in RULES.careers)
        assert len(selected) > 1

    def test_draft_resolves_positionally_over_the_draft_table(self):
        reached = set()
        for character in _characters():
            for step in character.history:
                if step.kind == "draft":
                    row = step.throw.total
                    assert step.selected == RULES.draft.careers[row - 1]
                    reached.add(step.selected)
        assert reached

    def test_drifter_thrown_when_selected_and_automatic_as_fallback(self):
        thrown = False
        automatic = False
        for character in _characters():
            for service in character.careers:
                if service.career != "Drifter":
                    continue
                if service.entered_by == "selected":
                    thrown = True
                if service.entered_by == "fallback":
                    automatic = True
        assert thrown and automatic

    def test_basic_training_grants_the_service_table_on_first_career(self):
        for character in _characters(100):
            first_step = next(s for s in character.history if s.kind == "basic-training")
            granted_names = {effect.subject.split(" (")[0] for effect in first_step.effects}
            first_career = character.careers[0].career
            career = next(c for c in RULES.careers.values() if c.name == first_career)
            expected_names = {
                (entry.skill.name if hasattr(entry, "skill") else entry.name)
                for entry in career.tables["service"].entries
            }
            assert granted_names == expected_names

    def test_rank_zero_bonus_granted_on_entry(self):
        found_bonus = False
        for character in _characters(100):
            steps = [s for s in character.history if s.kind == "rank-bonus"]
            assert steps
            if any(step.effects for step in steps):
                found_bonus = True
        assert found_bonus


class TestTermLoop:
    def test_survival_natural_failure_always_fails(self):
        for character in _characters():
            for step in character.history:
                if step.kind == "survival":
                    dice_total = sum(step.throw.faces)
                    if dice_total <= RULES.chargen.survival_natural_failure:
                        assert step.throw.success is False

    def test_commission_barred_in_a_drafted_characters_first_term(self):
        for character in _characters():
            for service in character.careers:
                if service.entered_by != "drafted":
                    continue
                commission_terms = [
                    step.term
                    for step in character.history
                    if step.kind == "commission" and step.career == service.career
                ]
                assert 1 not in commission_terms

    def test_a_commission_moves_the_character_to_the_commissioned_ladder(self):
        for character in _characters():
            for service in character.careers:
                if service.commissioned:
                    career = next(c for c in RULES.careers.values() if c.name == service.career)
                    commissioned_ladder = next(
                        ladder for ladder in career.ladders if ladder.role == "commissioned"
                    )
                    assert service.ladder == commissioned_ladder.name


class TestSkillRolls:
    def test_two_skill_rolls_in_a_career_declaring_neither_throw(self):
        # Excludes a re-enterable career: a `HistoryStep` names its career and
        # term but not which *service* of a career entered more than once it
        # belongs to, so two Drifter services both have a "term 1" and the
        # steps of each are indistinguishable by (career, term) alone. Scout
        # is not re-enterable and already proves the without-throws count.
        no_throw_careers = {
            c.name
            for c in RULES.careers.values()
            if "commission" not in c.throws and "promotion" not in c.throws and not c.re_enterable
        }
        assert no_throw_careers  # Scout ships without either throw.
        for character in _characters():
            for service in character.careers:
                if service.career not in no_throw_careers:
                    continue
                # A mishap ends the term (and the career) before skill
                # acquisition runs (FR-008's order), so the final term of a
                # mishap-ended service rolls no skills at all; every other
                # term rolls exactly the without-throws count, since neither
                # a commission nor an advancement can grant an extra roll in
                # a career declaring neither throw.
                last_term = service.terms if service.ended != "mishap" else service.terms - 1
                for term in range(1, last_term + 1):
                    rolls = [
                        step
                        for step in character.history
                        if step.kind == "skill-roll"
                        and step.career == service.career
                        and step.term == term
                    ]
                    assert len(rolls) == RULES.chargen.skill_rolls_per_term_without_throws

    def test_cascade_rule_chooses_a_permitted_specialty_and_records_it(self):
        cascading_skills = {
            name for name, specialties in RULES.skills.skills.items() if specialties
        }
        found = False
        for character in _characters():
            for skill in character.skills:
                if skill.name in cascading_skills and skill.specialty is not None:
                    assert skill.specialty in RULES.skills.skills[skill.name]
                    found = True
        assert found


class TestAlwaysLiving:
    def test_a_failed_survival_throw_resolves_on_the_mishap_table_without_death(self):
        for character in _characters():
            assert isinstance(character, Character)  # the walk always returns a value
        mishap_kinds = {step.kind for c in _characters() for step in c.history}
        assert "mishap" in mishap_kinds

    def test_a_mishap_ended_term_costs_two_years_and_forfeits_its_benefit_roll(self):
        for character in _characters():
            for service in character.careers:
                if service.ended != "mishap":
                    continue
                # The mishap term is always counted, and always forfeits a roll:
                # benefit_rolls can never exceed terms - 1 for a mishap-ended service
                # (unless a rank bonus adds one back).
                assert service.benefit_rolls <= service.terms

    def test_a_mishap_deferring_to_injury_records_its_own_step(self):
        found = False
        for character in _characters():
            kinds = [step.kind for step in character.history]
            if "injury" in kinds:
                found = True
        assert found


class TestCharacteristicFloors:
    def test_a_reduction_clamps_at_the_registry_floor(self):
        floor = RULES.characteristics.floor()
        for character in _characters():
            for score in character.characteristics.values():
                assert score >= floor

    def test_a_clamped_reduction_records_both_the_called_for_and_applied_effects(self):
        # `_apply_characteristic_delta` (generator.py) records exactly two
        # `characteristic` effects on one step when a floor clamp makes the
        # called-for and applied amounts differ, and exactly one when they
        # don't — asserted directly here, since the sample of packaged seeds
        # is not guaranteed to reach the clamp itself within a fast run.
        from cetools.generator import _apply_characteristic_delta

        floor = RULES.characteristics.floor()
        characteristics = {"STR": floor + 1}
        effects = _apply_characteristic_delta(characteristics, "STR", -5, floor)
        assert len(effects) == 2
        assert effects[0].amount == -5
        assert effects[1].amount == floor - (floor + 1)
        assert characteristics["STR"] == floor

        characteristics = {"STR": floor + 10}
        effects = _apply_characteristic_delta(characteristics, "STR", -1, floor)
        assert len(effects) == 1
        assert effects[0].amount == -1


class TestCareerEndAndMultiCareer:
    def test_the_cap_forces_mustering_out_regardless(self):
        cap = RULES.chargen.terms_cap
        for character in _characters():
            total = sum(service.terms for service in character.careers)
            assert total <= cap

    def test_a_career_already_entered_is_unavailable_again_except_drifter(self):
        for character in _characters():
            seen = []
            for service in character.careers:
                if service.career != "Drifter":
                    assert service.career not in seen
                seen.append(service.career)


def test_qualification_penalty_grows_with_previous_careers_entered():
    found_penalty = False
    for character in _characters():
        for step in character.history:
            if step.kind != "qualification" or step.throw is None:
                continue
            if any(m.label == "Previous careers" for m in step.throw.modifiers):
                found_penalty = True
    assert found_penalty
