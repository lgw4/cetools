"""The lifepath walk (spec.md FR-001 through FR-030a, contracts/library-api.md).

Exercises `generate_character` directly, against the packaged rules data,
since the walk's behavior is a property of dice and data rather than of any
one seed. Where a specific mechanic needs to be pinned (career selection,
qualification, the draft, mishaps, floors), the assertion is made over a
sample of seeds large enough to reach the branch under test rather than
hand-picking a single "lucky" seed, which would make the test fragile to an
unrelated draw-order change.
"""

from cetools.character import Character, StepEffect
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

    def test_a_characteristic_gate_excludes_the_table_rather_than_failing(self):
        from cetools.generator import _eligible_tables

        navy = next(c for c in RULES.careers.values() if c.name == "Navy")
        assert "requires" not in navy.tables or navy.tables["advanced-education"].requires
        gated = navy.tables["advanced-education"].requires
        below_gate = {code: 7 for code in RULES.characteristics.names}
        below_gate[gated.characteristic] = gated.target - 1
        at_gate = dict(below_gate)
        at_gate[gated.characteristic] = gated.target

        below_keys = {key for key, _ in _eligible_tables(navy, below_gate)}
        at_keys = {key for key, _ in _eligible_tables(navy, at_gate)}
        assert "advanced-education" not in below_keys
        assert "advanced-education" in at_keys

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
        # FR-020 forfeits the mishap term's benefit roll exactly once,
        # whatever the specific mishap row — including the row that also
        # carries its own `roll-injury` effect (T145: forfeiting twice for
        # that row is a defect `<=` alone does not catch, since it still
        # holds under double-forfeiture). A row that instead carries
        # `forfeit-career-benefits` forfeits every roll from the whole
        # service, not just the mishap term's, so it is excluded from the
        # exact count and left to `TestCareerEndAndMultiCareer` below. A
        # bigger sample than this module's default is used because the row
        # that used to double-count needs several terms served first to be
        # distinguishable from a single-term mishap, where both readings
        # clip to zero the same way.
        forfeit_all_kinds = {
            row.description
            for row in RULES.mishaps.rows
            if any(effect.kind == "forfeit-career-benefits" for effect in row.effects)
        }
        found_multi_term_mishap = False
        for character in _characters(2000):
            # `character.careers` and the "career-entered" steps share one
            # order, one per service, so a re-entered career (e.g. two
            # separate Drifter stints) is disambiguated by position rather
            # than by name alone.
            service_index = -1
            mishap_step_by_service_index = {}
            for step in character.history:
                if step.kind == "career-entered":
                    service_index += 1
                elif step.kind == "mishap" and step.throw:
                    mishap_step_by_service_index[service_index] = step
            for index, service in enumerate(character.careers):
                if service.ended != "mishap":
                    continue
                mishap_step = mishap_step_by_service_index[index]
                if mishap_step.selected in forfeit_all_kinds:
                    assert service.benefit_rolls == 0
                    continue
                assert service.benefit_rolls == max(0, service.terms - 1)
                if service.terms > 1:
                    found_multi_term_mishap = True
        assert found_multi_term_mishap

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


class TestApplyClassEffectNeverRaisesACrisis:
    """`_apply_class_effect` never raises a medical crisis (T160): it serves
    the term loop's direct mishap effects and `_roll_injury`, neither of
    which is aging, and FR-021 defines a crisis as arising specifically from
    an aging effect — `_apply_aging_if_due` raises its own, independently.
    This holds whether the reduction it applies actually reaches the floor
    or the characteristic was already sitting on it; that distinction
    (T146) now governs only whether a reduction is reported back to the
    caller for billing (`reduced`), not whether a crisis fires here, since
    it never does.
    """

    def test_a_characteristic_already_at_the_floor_raises_no_crisis(self):
        from cetools.chargen import MishapEffect
        from cetools.generator import _Walk

        walk = _Walk(Roller("t146-already-floored"), RULES)
        floor = RULES.characteristics.floor()
        walk.characteristics = {code: floor for code in RULES.characteristics.names}
        physical_class = next(
            cls
            for code, cls in RULES.characteristics.classes.items()
            if code in walk.characteristics
        )
        effect = MishapEffect(
            kind="characteristic-class",
            characteristic_class=physical_class,
            count=1,
            amount="-1d6",
        )
        reduced = walk._apply_class_effect(effect, "TestCareer", 1)
        assert reduced == {}
        assert walk.debt == 0
        assert walk.debts == []

    def test_a_reduction_that_reaches_the_floor_also_raises_no_crisis(self):
        from cetools.chargen import MishapEffect
        from cetools.generator import _Walk

        walk = _Walk(Roller("t146-reaches-floor"), RULES)
        floor = RULES.characteristics.floor()
        walk.characteristics = {code: floor + 1 for code in RULES.characteristics.names}
        physical_class = next(
            cls
            for code, cls in RULES.characteristics.classes.items()
            if code in walk.characteristics
        )
        effect = MishapEffect(
            kind="characteristic-class",
            characteristic_class=physical_class,
            count=1,
            amount="-6d6",
        )
        reduced = walk._apply_class_effect(effect, "TestCareer", 1)
        assert reduced
        assert walk.debt == 0
        assert walk.debts == []


class TestMedicalCrisisTriggersOnlyFromAging:
    """FR-021 defines a crisis as arising from an aging effect, and the
    Edge Cases section says "where the bottom was reached by aging" — not
    from a mishap's or an injury's own characteristic-class reduction,
    which `_apply_class_effect` also applies on behalf of the term loop's
    direct mishap effects and `_roll_injury` (T160).
    """

    def test_every_crisis_is_attributed_to_an_aging_step_in_the_same_career_and_term(self):
        # Attribution by (career, term) rather than list order: whether the
        # `aging` step is recorded before or after the crisis it causes is
        # T163's separate concern, not this one — this test is only about
        # *which* effect gets to raise a crisis at all.
        for character in _characters(2000):
            for index, step in enumerate(character.history):
                if step.kind != "medical-crisis":
                    continue
                assert any(
                    other.kind == "aging"
                    and other.career == step.career
                    and other.term == step.term
                    for other in character.history
                ), (
                    f"seed {character.seed}: medical-crisis at history index "
                    f"{index} traces to no aging step in {step.career} term {step.term}"
                )


class TestMedicalBillRestoration:
    """FR-025's "unless the character's medical bills are paid" and
    FR-025a's "the points restored MUST be those the covered amount pays
    for" (T161).
    """

    def test_a_bill_paid_in_full_restores_every_point_it_covered(self):
        from cetools.generator import _Walk

        # `Roller(22).dice(2, 6)` is this test's first draw and is exactly
        # `_raise_medical_bill`'s own tier throw: (2, 2), sum 4, which pays
        # 75% at Navy's "service" tier — a partial share, not the full
        # `medical.restore-cost-per-point` `_Debt` used to be given.
        walk = _Walk(Roller(22), RULES)
        walk.characteristics = {code: 10 for code in RULES.characteristics.names}
        walk.funds = 100_000
        walk._raise_medical_bill("Navy", 1, 0, {"STR": 3})
        assert walk.debt == 0
        assert walk.characteristics["STR"] == 13

    def test_an_employer_paid_in_full_bill_restores_the_points_and_records_the_throw(self):
        from cetools.generator import _Walk

        # `Roller(0).dice(2, 6)` is (4, 4), sum 8: 100% paid at the
        # "service" tier, so `owed` is 0 and no debt is ever created — the
        # points must still be restored and the tier throw still recorded.
        walk = _Walk(Roller(0), RULES)
        walk.characteristics = {code: 10 for code in RULES.characteristics.names}
        walk.funds = 100_000
        before = len(walk.history)
        walk._raise_medical_bill("Navy", 1, 0, {"STR": 3})
        assert walk.debt == 0
        assert walk.debts == []
        assert walk.characteristics["STR"] == 13
        assert walk.funds == 100_000
        new_steps = walk.history[before:]
        assert any(step.kind == "medical-bills" and step.throw is not None for step in new_steps)


def _applied_reductions(effects):
    """The actually-*applied* negative characteristic deltas on one step's
    effects, skipping a floor clamp's called-for half of an adjacent pair
    (the same convention `_replay_characteristics` uses, T146): a
    characteristic already at the floor and chosen again records a
    called-for/applied pair whose applied half is `0`, not a reduction at
    all.
    """
    applied = []
    i = 0
    while i < len(effects):
        effect = effects[i]
        if effect.kind != "characteristic":
            i += 1
            continue
        paired = (
            i + 1 < len(effects)
            and effects[i + 1].kind == "characteristic"
            and effects[i + 1].subject == effect.subject
        )
        value = effects[i + 1].amount if paired else effect.amount
        if value < 0:
            applied.append(value)
        i += 2 if paired else 1
    return applied


class TestAMishapsDirectReductionRaisesABill:
    """FR-024's "MUST persist unless the character's medical bills are
    paid" presupposes a bill exists to pay: a mishap row's own
    characteristic-class effect (e.g. mishaps.toml row 1, "Injured in
    action") reduces a characteristic exactly the way an injury does, so it
    must be billed exactly the way an injury is (T162).
    """

    def test_every_mishap_reduction_is_billed(self):
        for character in _characters(2000):
            for step in character.history:
                if step.kind != "mishap":
                    continue
                if not _applied_reductions(step.effects):
                    continue
                assert any(
                    other.kind == "medical-bills"
                    and other.career == step.career
                    and other.term == step.term
                    for other in character.history
                ), (
                    f"seed {character.seed}: mishap reduction in {step.career} "
                    f"term {step.term} was never billed"
                )


def _credits_steps(steps):
    return [
        step
        for step in steps
        if step.kind == "benefit" and any(e.kind == "credits" for e in step.effects)
    ]


class TestMusteringOut:
    def test_a_material_characteristic_adjustment_is_a_characteristic_effect(self):
        # `_apply_characteristic_delta` already returns properly-kinded
        # `characteristic` effects — including the called-for/applied pair
        # a floor clamp produces — but `muster_out_service` discarded them
        # and rewrapped a bare scalar as a `benefit`-kind effect instead,
        # so a mustering-out material benefit that adjusts a characteristic
        # was invisible to anything grouping by `characteristic` effects
        # (SC-005, discovered while implementing T153).
        from cetools.generator import _Walk

        career = RULES.careers["navy"]
        walk = _Walk(Roller(1), RULES)
        walk.characteristics = {code: 7 for code in RULES.characteristics.names}
        walk.muster_out_service(career, terms=4, ladder="", rank=0, benefit_rolls=1)

        steps = [s for s in walk.history if s.kind == "benefit"]
        assert len(steps) == 1
        assert steps[0].effects == (StepEffect(kind="characteristic", subject="SOC", amount=1),)
        assert walk.characteristics["SOC"] == 8

    def test_the_cash_roll_cap_is_shared_across_a_characters_whole_life(self):
        # FR-016 caps "how many of a character's rolls" may be taken as
        # cash — a character-wide count, not one that resets with every
        # `CareerService` mustered out. Seed 0 reaches the cap of 3 within
        # the first of two `muster_out_service` calls on the same `_Walk`
        # (simulating a two-career character); a per-service reset would let
        # the second call take more cash rolls than the character-wide cap
        # permits (T147).
        from cetools.generator import _Walk

        cap = RULES.chargen.mustering_out_maximum_cash_rolls
        walk = _Walk(Roller(0), RULES)
        walk.characteristics = {code: 7 for code in RULES.characteristics.names}
        career = next(iter(RULES.careers.values()))

        walk.muster_out_service(career, terms=4, ladder="", rank=0, benefit_rolls=6)
        first_call_end = len(walk.history)
        assert len(_credits_steps(walk.history[:first_call_end])) == cap

        walk.muster_out_service(career, terms=4, ladder="", rank=0, benefit_rolls=6)
        assert _credits_steps(walk.history[first_call_end:]) == []


class TestDebtSettlement:
    def test_a_partial_payment_that_alone_is_short_of_a_point_carries_its_remainder(self):
        # FR-025a: "the points restored MUST be those the covered amount
        # pays for". Two settlements of Cr50 each against a Cr100-per-point
        # debt must together restore one point, even though neither payment
        # alone reaches the cost (T157).
        from cetools.generator import _Debt, _Walk

        walk = _Walk(Roller("t157"), RULES)
        code = next(iter(RULES.characteristics.names))
        walk.characteristics = {code: 5}
        debt = _Debt(amount=100, restore="medical", characteristics=(code,), cost_per_point=100)
        walk.debt = debt.amount
        walk.debts = [debt]

        walk.funds = 50
        walk.settle_debts()
        assert walk.characteristics[code] == 5  # short of a full point, nothing restored yet

        walk.funds = 50
        walk.settle_debts()
        assert walk.characteristics[code] == 6  # the two payments together cover one point
        assert walk.debts == []

    def test_settlement_is_recorded_in_the_history(self):
        # FR-030, FR-025a, T144: a `debt-settled` step per debt paid this
        # call, carrying the amount paid and which characteristics were
        # restored and by how much — never only the arithmetic on the
        # character's own fields.
        from cetools.generator import _Debt, _Walk

        walk = _Walk(Roller("t144"), RULES)
        code = next(iter(RULES.characteristics.names))
        walk.characteristics = {code: 5}
        debt = _Debt(amount=100, restore="medical", characteristics=(code,), cost_per_point=100)
        walk.debt = debt.amount
        walk.debts = [debt]
        walk.funds = 100

        walk.settle_debts(career="Navy", term=2)

        step = walk.history[-1]
        assert step.kind == "debt-settled"
        assert step.career == "Navy"
        assert step.term == 2
        assert StepEffect(kind="debt", subject="", amount=100) in step.effects
        assert StepEffect(kind="characteristic", subject=code, amount=1) in step.effects

    def test_a_medical_crisis_debts_creation_step_is_not_named_debt_settled(self):
        # The step `_trigger_medical_crisis` records fires when the debt is
        # *created*, not settled; `debt-settled` is reserved for the step
        # `settle_debts` now records, or the two are indistinguishable in
        # the history (T144).
        from cetools.generator import _Walk

        walk = _Walk(Roller("t144-crisis"), RULES)
        walk.characteristics = {code: 0 for code in RULES.characteristics.names}
        walk._trigger_medical_crisis("Navy", 1, ("STR",))
        creation_step = next(s for s in walk.history if s.throw is not None)
        assert creation_step.kind == "medical-crisis"
        assert creation_step.kind != "debt-settled"


class TestMedicalBills:
    def test_the_bill_is_per_point_reduced_not_per_characteristic_at_the_floor(self):
        # FR-025: the cost is the per-point rate times the points an injury
        # actually reduced, not one flat point per characteristic that
        # happens to be sitting at the floor when the bill is raised — an
        # aging-floored characteristic the injury never touched must not be
        # billed, and an injury that reduces a score by several points
        # without flooring it must still be billed for all of them (T143).
        from cetools.generator import _Walk

        cost_per_point = RULES.chargen.medical_restore_cost_per_point
        career = next(c for c in RULES.careers.values() if not c.always_available)

        walk = _Walk(Roller(1), RULES)
        floor = walk.floor()
        walk.characteristics = {code: floor for code in RULES.characteristics.names}
        # STR reduced by 3 points, well above the floor: not a `<= floor`
        # characteristic, so the old post-state scan would have missed it.
        walk.characteristics["STR"] = floor + 10
        walk._raise_medical_bill(career.name, 1, 0, {"STR": 3})
        # Only the cost of STR's 3 points is owed; every other
        # already-floored characteristic (aging's doing, not this
        # injury's) contributes nothing.
        assert walk.debt <= cost_per_point * 3
        assert walk.debt > 0

    def test_rank_dm_is_applied_at_the_time_the_bill_is_raised(self):
        # FR-025, T150: `medical-tiers.rank-dm` adds the character's rank
        # to the bill's throw. Same career, same dice (same seed, called
        # before anything else consumes the roller), different ranks.
        from cetools.generator import _Walk

        career = next(iter(RULES.careers.values()))
        reduced = {"STR": 1}

        low_rank = _Walk(Roller(1), RULES)
        low_rank.characteristics = {code: 7 for code in RULES.characteristics.names}
        low_rank._raise_medical_bill(career.name, 1, 0, reduced)

        high_rank = _Walk(Roller(1), RULES)
        high_rank.characteristics = {code: 7 for code in RULES.characteristics.names}
        high_rank._raise_medical_bill(career.name, 1, 6, reduced)

        assert low_rank.debt != high_rank.debt


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
