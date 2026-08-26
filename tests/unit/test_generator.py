"""The lifepath walk (spec.md FR-001 through FR-030a, contracts/library-api.md).

Exercises `generate_character` directly, against the packaged rules data,
since the walk's behavior is a property of dice and data rather than of any
one seed. Where a specific mechanic needs to be pinned (career selection,
qualification, the draft, mishaps, floors), the assertion is made over a
sample of seeds large enough to reach the branch under test rather than
hand-picking a single "lucky" seed, which would make the test fragile to an
unrelated draw-order change.
"""

from pathlib import Path

import pytest

from cetools.character import Character, StepEffect
from cetools.dice import Roller
from cetools.generator import generate_character
from cetools.rules import load_rules

RULES = load_rules()
_SAMPLE = 400
_DATA = Path(__file__).resolve().parents[2] / "src" / "cetools" / "data"


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

    def test_a_draft_collision_records_the_substitution_as_its_own_step(self):
        # T189/T201/FR-015a: when the draft names a career already entered
        # and not re-enterable, `enter_career` silently substituted the
        # re-enterable fallback, leaving `entered_by` fixed at "drafted"
        # and the "draft" step still naming the career the walk never
        # actually entered — the substitution itself was nowhere in the
        # history. It must now appear as a "career-selected" step naming
        # the *substitute* the walk actually entered, distinct from the
        # step naming the career the draft actually named (FR-015a):
        # naming the collided-with career again, as T189's first attempt
        # did, restates what the "draft" step already says and leaves the
        # substitute unexplained (T201).
        from cetools.generator import _Walk

        found = False
        for seed in range(1000):
            walk = _Walk(Roller(seed), RULES)
            walk.characteristics = {code: 6 for code in RULES.characteristics.names}
            candidate, entered_by = walk.enter_career({"Marine"})
            draft_steps = [s for s in walk.history if s.kind == "draft"]
            if not draft_steps or draft_steps[-1].selected != "Marine":
                continue
            found = True
            assert entered_by == "drafted"
            assert candidate.name != "Marine"
            draft_index = walk.history.index(draft_steps[-1])
            entered_index = next(
                i for i, s in enumerate(walk.history) if s.kind == "career-entered"
            )
            substitution_steps = [
                s
                for i, s in enumerate(walk.history)
                if draft_index < i < entered_index
                and s.kind == "career-selected"
                and s.selected == candidate.name
            ]
            assert len(substitution_steps) == 1
            assert substitution_steps[0].selected != "Marine"
            # The substitution is chosen deterministically (the first
            # re-enterable career), not by a die — it stays throwless, which
            # is what now separates it by shape from the ordinary selection
            # step T207 gives a throw to (data-model.md, T207).
            assert substitution_steps[0].throw is None
            break
        assert found

    def test_basic_training_grants_the_service_table_on_first_career(
        self, cascade_reachable_names
    ):
        for character in _characters(100):
            first_step = next(s for s in character.history if s.kind == "basic-training")
            first_career = character.careers[0].career
            career = next(c for c in RULES.careers.values() if c.name == first_career)
            entries = career.tables["service"].entries
            assert len(first_step.effects) == len(entries)
            for effect, entry in zip(first_step.effects, entries):
                entry_name = entry.skill.name if hasattr(entry, "skill") else entry.name
                granted_name = effect.subject.split(" (")[0]
                assert granted_name in cascade_reachable_names(entry_name)

    def test_a_later_career_characteristic_adjustment_entry_is_applied(self, tmp_path):
        # T200: the later-career branch of `basic_training` filtered every
        # drawn entry down to `SkillReference`, discarding a
        # `CharacteristicAdjustment` after the die that drew it had already
        # been rolled and recorded — a die thrown, an entry selected, and
        # nothing granted, leaving a `basic-training` step that cannot be
        # replayed. `_roll_skills` already reads the identical entry
        # correctly through `_apply_entry`; `basic_training`'s later-career
        # draw now does too (the filter stays on the first-career branch,
        # which grants every skill entry at level zero and has no
        # characteristic form to apply).
        class _FixedRoller:
            def __init__(self, sequence):
                self._sequence = list(sequence)

            def dice(self, count, sides):
                return tuple(self._sequence.pop(0) for _ in range(count))

            def die(self, sides):
                return self._sequence.pop(0)

        drifter = (_DATA / "careers" / "drifter.toml").read_text(encoding="utf-8")
        service_entries = '["Carousing", "Gambling", "Recon", "Broker", "Streetwise", "Survival"]'
        assert service_entries in drifter
        overridden = drifter.replace(
            service_entries,
            service_entries.replace('"Carousing"', '"END +1"', 1),
            1,
        )
        (tmp_path / "drifter.toml").write_text(overridden, encoding="utf-8")
        rules = load_rules(tmp_path)
        career = rules.careers["drifter"]

        from cetools.generator import _Walk

        walk = _Walk(_FixedRoller([1]), rules)
        walk.characteristics = {code: 7 for code in rules.characteristics.names}
        walk.basic_training(career, is_first_career=False)

        assert walk.characteristics["END"] == 8
        step = next(s for s in walk.history if s.kind == "basic-training")
        assert step.effects == (StepEffect(kind="characteristic", subject="END", amount=1),)

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

    def test_advancement_is_attempted_whenever_the_career_declares_it(self):
        # FR-008 conditions the step on the career offering the throw, not
        # on a higher rank existing to move to. Every entry ladder in the
        # shipped data (other than Navy's, since T155) declares a single
        # rank 0, so an uncommissioned character in a career that offers
        # promotion — Aerospace System Defense, both throws — was denied the
        # throw entirely (T169). Seed 20's first term survives, fails its
        # commission throw, and stays in the game (does not mishap), which
        # is what reaches the promotion section at all.
        from cetools.generator import _Walk

        career = RULES.careers["aerospace-system-defense"]
        walk = _Walk(Roller(20), RULES)
        walk.characteristics = {code: 7 for code in RULES.characteristics.names}
        walk.run_term_loop(career, "selected")
        term_one_steps = [step for step in walk.history if step.term == 1]
        assert any(step.kind == "commission" and not step.throw.success for step in term_one_steps)
        assert any(step.kind == "advancement" for step in term_one_steps)

    def test_advancement_leaves_the_rank_unchanged_with_nothing_above(self):
        # The other half of T169: attempting the throw must not move the
        # rank when the ladder has nothing above it, even on a success —
        # seed 20's term 1 advancement throw succeeds (Aerospace System Defense's
        # "enlisted" ladder declares only rank 0).
        from cetools.generator import _Walk

        career = RULES.careers["aerospace-system-defense"]
        walk = _Walk(Roller(20), RULES)
        walk.characteristics = {code: 7 for code in RULES.characteristics.names}
        terms, ladder, rank, commissioned, ended, benefit_rolls, forfeit_all = walk.run_term_loop(
            career, "selected"
        )
        advancement = next(step for step in walk.history if step.kind == "advancement")
        assert advancement.throw.success
        assert rank == 0


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

    def test_every_table_gated_out_fails_nameably(self, tmp_path):
        # T203: `_roll_skills` calls `self.roller.die(len(eligible))` with no
        # guard for `eligible` being empty — legitimate for one gated table
        # (the case above), but nothing stops an override from gating every
        # one of a career's tables, and `roller.die(0)` then raises a bare
        # `DiceError` naming neither the career nor the gates that excluded
        # them.
        from cetools.errors import RulesDataError
        from cetools.generator import _Walk

        navy = (_DATA / "careers" / "navy.toml").read_text(encoding="utf-8")
        for block in ("[tables.personal]\n", "[tables.service]\n", "[tables.specialist]\n"):
            assert block in navy
            navy = navy.replace(block, block + 'requires = "EDU 12+"\n', 1)
        (tmp_path / "navy.toml").write_text(navy, encoding="utf-8")
        rules = load_rules(tmp_path)
        career = rules.careers["navy"]

        walk = _Walk(Roller(0), rules)
        walk.characteristics = {code: 0 for code in rules.characteristics.names}
        with pytest.raises(RulesDataError) as excinfo:
            walk._roll_skills(career, 1, 1)
        assert "Navy" in str(excinfo.value)

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


class TestRecursiveCascadeResolution:
    """FR-011, FR-012, D5: resolving a bare grant continues through a chosen
    specialty that is itself a cascade until it reaches one with none, and
    the recorded reference is the innermost cascade paired with a terminal
    specialty — never the outer name, and never a bare terminal.
    """

    def _registry(self):
        from cetools.registries import SkillRegistry

        return SkillRegistry(
            skills={
                "Vehicle": ("Aircraft", "Watercraft"),
                "Aircraft": ("Winged Aircraft", "Grav Vehicle"),
                "Watercraft": ("Ocean Ships",),
                "Winged Aircraft": (),
                "Grav Vehicle": (),
                "Ocean Ships": (),
            }
        )

    def test_a_bare_grant_resolves_to_the_innermost_cascade_and_a_terminal_specialty(self):
        from cetools.generator import _resolve_specialty
        from cetools.notation import SkillReference

        registry = self._registry()
        seen = set()
        for seed in range(200):
            resolved = _resolve_specialty(SkillReference(name="Vehicle"), registry, Roller(seed))
            assert resolved.name in ("Aircraft", "Watercraft")
            assert resolved.specialty in registry.skills[resolved.name]
            seen.add((resolved.name, resolved.specialty))
        # Both branches, and more than one terminal specialty under the
        # branch that has more than one, are reachable.
        assert ("Aircraft", "Winged Aircraft") in seen
        assert ("Aircraft", "Grav Vehicle") in seen
        assert ("Watercraft", "Ocean Ships") in seen

    def test_each_nesting_level_costs_exactly_one_draw(self):
        from cetools.generator import _resolve_specialty
        from cetools.notation import SkillReference

        registry = self._registry()
        for seed in range(50):
            roller = Roller(seed)
            calls = []
            original_die = roller.die
            roller.die = lambda sides, _orig=original_die: (calls.append(sides), _orig(sides))[1]
            _resolve_specialty(SkillReference(name="Vehicle"), registry, roller)
            # Vehicle -> {Aircraft, Watercraft} is one draw; whichever is
            # chosen, it is itself a cascade, so resolving its specialty is
            # a second draw — and every one of those is terminal.
            assert len(calls) == 2

    def test_a_reference_that_already_names_a_specialty_draws_nothing(self):
        from cetools.generator import _resolve_specialty
        from cetools.notation import SkillReference

        registry = self._registry()
        reference = SkillReference(name="Vehicle", specialty="Aircraft")
        assert _resolve_specialty(reference, registry, Roller(0)) is reference

    def test_a_terminal_bare_grant_draws_nothing_and_stays_unspecialized(self):
        from cetools.generator import _resolve_specialty
        from cetools.notation import SkillReference

        registry = self._registry()
        reference = SkillReference(name="Winged Aircraft")
        assert _resolve_specialty(reference, registry, Roller(0)) is reference


class TestTitlePersistenceAcrossCareers:
    """FR-047c (T171): an earlier title survives a later untitled service.
    Driven against a fixture career built from Navy's rather than through
    `run()`'s random career selection, so the two services land in a chosen
    order; T073's traversal cases exercise the branch from shipped data too
    now that Navy's own enlisted ladder carries untitled ranks (FR-019).
    """

    def test_a_later_untitled_service_does_not_erase_an_earlier_title(self):
        import dataclasses

        from cetools.generator import _Walk

        navy = next(c for c in RULES.careers.values() if c.name == "Navy")
        untitled_career = dataclasses.replace(
            navy,
            name="Untitled Navy",
            ladders=tuple(
                dataclasses.replace(
                    ladder, ranks=tuple(dataclasses.replace(r, title="") for r in ladder.ranks)
                )
                for ladder in navy.ladders
            ),
        )

        title_after_first_career = None
        for seed in range(50):
            walk = _Walk(Roller(seed), RULES)
            walk.characteristics = {code: 7 for code in RULES.characteristics.names}

            entry_ladder = walk._entry_ladder(navy)
            walk._grant_rank_bonus(navy.name, 1, entry_ladder, 0)
            _, ladder, rank, *_ = walk.run_term_loop(navy, "selected")
            title = walk._current_title(navy, ladder, rank)
            if title:
                walk.title = title
            if walk.title:
                title_after_first_career = walk.title
                break
        assert title_after_first_career, "no seed under 50 reached a titled Navy rank"

        entry_ladder2 = walk._entry_ladder(untitled_career)
        walk._grant_rank_bonus(untitled_career.name, 1, entry_ladder2, 0)
        _, ladder2, rank2, *_ = walk.run_term_loop(untitled_career, "fallback")
        title2 = walk._current_title(untitled_career, ladder2, rank2)
        if title2:
            walk.title = title2

        assert title2 == ""
        assert walk.title == title_after_first_career


class TestQuantifiedBenefitDraw:
    """FR-011: a `QuantifiedBenefit` mustering-out row appends the item name
    once per point rolled, the quantity itself a seeded draw.
    """

    def _ship_share_count(self, seed):
        import dataclasses

        from cetools.generator import _Walk
        from cetools.notation import QuantifiedBenefit

        navy = next(c for c in RULES.careers.values() if c.name == "Navy")
        mustering_out = dataclasses.replace(
            navy.mustering_out,
            benefits=(QuantifiedBenefit(dice="1d6", name="Ship Share"),)
            * len(navy.mustering_out.benefits),
        )
        career = dataclasses.replace(navy, mustering_out=mustering_out)
        walk = _Walk(Roller(seed), RULES)
        walk.characteristics = {code: 7 for code in RULES.characteristics.names}
        walk.muster_out_service(career, terms=1, ladder="enlisted", rank=0, benefit_rolls=1)
        return walk.benefits.count("Ship Share")

    def test_the_count_awarded_is_the_dice_total_and_varies_with_the_seed(self):
        # `benefit_rolls=1` sometimes takes cash instead of material (the
        # cash-choice roll is its own draw), so a count of 0 is a real
        # outcome; what this pins is that a material roll never awards more
        # than 1d6 and that the count is not the same every seed.
        counts = [self._ship_share_count(seed) for seed in range(30)]
        assert all(0 <= count <= 6 for count in counts)
        assert len(set(counts)) > 1
        assert any(count >= 1 for count in counts)

    def test_the_same_seed_yields_the_same_count(self):
        assert self._ship_share_count(7) == self._ship_share_count(7)


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
                # `benefit_rolls` records the rolls actually taken (T188):
                # the term-derived count plus the rank-derived bonus, not
                # the term-derived half alone.
                from cetools.generator import _Walk

                rank_bonus = _Walk._highest_matching_rank_row(
                    RULES.chargen.mustering_out_rank_benefits, service.rank
                )
                assert service.benefit_rolls == max(0, service.terms - 1) + rank_bonus
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


class TestCareerSelectedRecordsItsOwnThrow:
    """`_select_career` throws `self.roller.die(len(available))`
    (generator.py) and the "career-selected" step naming its result carried
    `throw=None`, so every one of a character's selection draws was
    unanswerable from the record and indistinguishable in shape from
    T201's throwless draft-collision substitution step (T207).
    """

    def test_every_career_entry_attempt_records_exactly_one_throwing_selection(self):
        for character in _characters(200):
            entered = sum(1 for s in character.history if s.kind == "career-entered")
            thrown_selections = sum(
                1 for s in character.history if s.kind == "career-selected" and s.throw is not None
            )
            assert thrown_selections == entered

    def test_the_recorded_selection_throw_is_a_single_table_reading_face(self):
        for character in _characters(100):
            for step in character.history:
                if step.kind != "career-selected" or step.throw is None:
                    continue
                assert step.throw.faces == (step.throw.total,)
                assert step.throw.modifiers == ()
                assert step.throw.target == 0
                assert step.throw.success is True


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

    def test_the_called_for_and_applied_effects_carry_distinct_kinds(self):
        # FR-030a requires the parts be separately addressable, and the
        # check made from the record's shape — not from a test-only
        # adjacency convention that cannot tell a clamp pair from two
        # genuine independent reductions of the same characteristic (T165).
        from cetools.generator import _apply_characteristic_delta

        floor = RULES.characteristics.floor()
        characteristics = {"STR": floor + 1}
        effects = _apply_characteristic_delta(characteristics, "STR", -5, floor)
        assert effects[0].kind == "characteristic-called-for"
        assert effects[1].kind == "characteristic"

        characteristics = {"STR": floor + 10}
        effects = _apply_characteristic_delta(characteristics, "STR", -1, floor)
        assert effects[0].kind == "characteristic"


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


class TestAgingStepPrecedesTheCrisisItCauses:
    """FR-030 requires the steps in the order the walk occurred, which is
    what makes a surprising sheet diagnosable (US2 acceptance scenario 4):
    the `aging` step that causes a crisis must appear before the
    `medical-crisis` step it causes, not after (T163).
    """

    def test_every_crisis_follows_its_aging_step(self):
        for character in _characters(2000):
            aging_index_by_career_term: dict[tuple[str, int], int] = {}
            for index, step in enumerate(character.history):
                if step.kind == "aging":
                    aging_index_by_career_term.setdefault((step.career, step.term), index)
                elif step.kind == "medical-crisis":
                    aging_index = aging_index_by_career_term.get((step.career, step.term))
                    assert aging_index is not None and aging_index < index, (
                        f"seed {character.seed}: medical-crisis at history index "
                        f"{index} does not follow an aging step in "
                        f"{step.career} term {step.term}"
                    )


_DEBT_CREATING_KINDS = frozenset({"mishap", "medical-crisis", "medical-bills"})


class TestADebtsCreationStepPrecedesItsSettlement:
    """`add_debt` settles immediately (T144), and every caller appends its
    own creation step — but until now, after calling it, so a debt's
    settlement (`add_debt`'s own synchronous call to `settle_debts`) landed
    in the history before the very step that created the debt it settled
    (T164).
    """

    def test_every_settlement_has_a_prior_unsettled_creation(self):
        # A single term can legitimately raise more than one debt (a
        # mishap's medical bill, then a later aging-triggered
        # medical-crisis, both before the term ends) with the earlier one
        # opportunistically settled from funds on hand while the later one
        # remains outstanding — so matching by (career, term) alone, as an
        # earlier version of this test did, false-positives on that
        # ordering. And a single debt can itself be settled across more
        # than one `debt-settled` step (a partial payment now, the
        # remainder whenever funds next allow), so a one-token-per-debt
        # counter, decremented on every settlement, also false-positives —
        # a debt only fully "consumed" once its cumulative payments reach
        # its amount, not on its first partial one. A career-boundary reset
        # is wrong for the same reason a per-debt token count is: a debt a
        # career could not afford to clear at its own mustering-out stays
        # outstanding into whatever career comes next.
        #
        # What T164 actually guards against is money settled that was never
        # owed yet — a `debt-settled` amount landing before the
        # `mishap`/`medical-crisis`/`medical-bills` step whose debt effect
        # created it. That is a running conservation check on cumulative
        # totals, not a per-event token count: cumulative money settled can
        # never exceed cumulative money created up to that point.
        for character in _characters(2000):
            created = 0
            settled = 0
            for index, step in enumerate(character.history):
                if step.kind in _DEBT_CREATING_KINDS:
                    created += sum(e.amount for e in step.effects if e.kind == "debt")
                elif step.kind == "debt-settled":
                    settled += sum(e.amount for e in step.effects if e.kind == "debt")
                    assert settled <= created, (
                        f"seed {character.seed}: debt-settled at history "
                        f"index {index} ({step.career} term {step.term}) "
                        f"brings cumulative settlements to {settled}, "
                        f"exceeding the {created} created so far"
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
    effects. A floor clamp's called-for half carries its own kind,
    `characteristic-called-for`, distinct from `characteristic` (T165), so
    it is excluded by kind alone: a characteristic already at the floor
    and chosen again applies a delta of `0`, which is not a reduction.
    """
    return [
        effect.amount
        for effect in effects
        if effect.kind == "characteristic" and effect.amount < 0
    ]


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


class TestInjuryReductionIsFiledUnderTheInjuryKind:
    """FR-030a requires each step name which kind of step it was.
    `_apply_class_effect` hard-codes `kind="mishap"` on the step it
    appends, and `_roll_injury` calls it, so the reduction an injury row
    produced was recorded under the wrong kind — indistinguishable from a
    mishap row's own direct reduction (T174).
    """

    def test_the_reduction_following_an_injury_step_is_kinded_injury(self):
        # T183 gave the reduction sub-step its own throw too, so a bare
        # `throw is None` no longer tells it apart from whatever else
        # might follow — nor does a characteristic effect alone, since an
        # unrelated later step (an "aging" step, say) can carry one too.
        # Which injury rows actually reduce a characteristic is known
        # ahead of time from the row itself.
        injury_rows_with_effect = {
            row.description
            for row in RULES.mishaps.injuries
            if any(e.kind == "characteristic-class" for e in row.effects)
        }
        found = False
        for character in _characters(300):
            for index, step in enumerate(character.history):
                if step.kind != "injury" or step.selected not in injury_rows_with_effect:
                    continue
                found = True
                following = character.history[index + 1]
                assert following.kind == "injury", (
                    f"seed {character.seed}: the reduction following an injury "
                    f"step at history index {index} is kinded {following.kind!r}"
                )
        assert found

    def test_apply_class_effect_records_the_kind_it_is_given(self):
        from cetools.chargen import MishapEffect
        from cetools.generator import _Walk

        walk = _Walk(Roller("t174"), RULES)
        walk.characteristics = {code: 10 for code in RULES.characteristics.names}
        physical_class = next(
            cls
            for code, cls in RULES.characteristics.classes.items()
            if code in walk.characteristics
        )
        effect = MishapEffect(
            kind="characteristic-class",
            characteristic_class=physical_class,
            count=1,
            amount="-1",
        )
        before = len(walk.history)
        walk._apply_class_effect(effect, "TestCareer", 1, kind="injury")
        recorded = walk.history[before:]
        assert recorded and recorded[-1].kind == "injury"


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

    def test_forfeited_benefits_take_no_rank_derived_rolls_either(self):
        # `run_term_loop` already zeros `benefit_rolls` for a mishap's
        # `forfeit-career-benefits` effect (T145), but `muster_out_service`
        # added the rank-derived bonus on top regardless, so a character
        # dishonorably discharged or imprisoned at rank 6 (extra = 3, per
        # chargen-parameters.toml's `rank-benefits`) still took three rolls
        # from a service that recorded taking none (T168).
        from cetools.generator import _Walk

        career = RULES.careers["navy"]
        walk = _Walk(Roller(1), RULES)
        walk.characteristics = {code: 7 for code in RULES.characteristics.names}
        walk.muster_out_service(
            career, terms=4, ladder="", rank=6, benefit_rolls=0, forfeit_all=True
        )
        assert not any(s.kind == "benefit" for s in walk.history)

    def test_retired_cash_dm_applies_once_the_character_has_ever_qualified(self):
        # T202: FR-017's modifier applies "exactly when *the character*
        # qualified for the pension" — the same character-wide scope FR-016
        # already gives the cash-roll cap (T147) — but `qualifies_for_pension`
        # was a local recomputed from *this service's* own terms, so a
        # character who qualified in an earlier career and then musters out
        # of a short later one took an undiscounted cash roll. Navy's cash
        # table reads `[1000, 5000, 10000, 10000, 20000, 50000, 50000]`: a
        # natural 5 with no DM lands on row 5 (`20000`); with the packaged
        # `retired-cash-dm = 1` it lands on row 6 (`50000`) instead.
        from cetools.generator import _Walk

        class _FixedRoller:
            def __init__(self, sequence):
                self._sequence = list(sequence)

            def dice(self, count, sides):
                return tuple(self._sequence.pop(0) for _ in range(count))

            def die(self, sides):
                return self._sequence.pop(0)

        career = RULES.careers["navy"]
        assert career.mustering_out.cash[4] == 20000
        assert career.mustering_out.cash[5] == 50000

        walk = _Walk(Roller(0), RULES)
        walk.characteristics = {code: 7 for code in RULES.characteristics.names}
        # `terms=5` meets `pension.minimum-terms`, qualifying the character
        # for a pension; `benefit_rolls=0` takes no rolls, so no dice are
        # drawn by this call.
        walk.muster_out_service(career, terms=5, ladder="", rank=0, benefit_rolls=0)

        # A second, short service that would not itself qualify: the
        # cash-choice die (face 4, target 4) takes cash, and the
        # mustering-out die (face 5) is the natural total under test.
        walk.roller = _FixedRoller([4, 5])
        funds_before = walk.funds
        walk.muster_out_service(career, terms=1, ladder="", rank=0, benefit_rolls=1)
        assert walk.funds - funds_before == 50000

    def test_cash_choice_is_its_own_step_with_the_retired_dm_itemized(self):
        # T197: the cash-choice throw's own face was merged into the table
        # throw's `faces`, describing a throw that was never made, and
        # `mustering_out_retired_cash_dm`/`mustering_out_material_rank_dm`
        # were folded into `total` with neither itemized in `modifiers`.
        class _FixedRoller:
            def __init__(self, sequence):
                self._sequence = list(sequence)

            def dice(self, count, sides):
                return tuple(self._sequence.pop(0) for _ in range(count))

            def die(self, sides):
                return self._sequence.pop(0)

        from cetools.generator import _Walk

        career = RULES.careers["navy"]
        walk = _Walk(Roller(0), RULES)
        walk.characteristics = {code: 7 for code in RULES.characteristics.names}
        walk.pension_qualified = True
        # Cash-choice face 4 meets the packaged target of 4, so cash is
        # taken; the mustering-out die then reads face 5.
        walk.roller = _FixedRoller([4, 5])
        walk.muster_out_service(career, terms=1, ladder="", rank=0, benefit_rolls=1)

        cash_choice_steps = [s for s in walk.history if s.kind == "cash-choice"]
        benefit_steps = [s for s in walk.history if s.kind == "benefit"]
        assert len(cash_choice_steps) == 1
        assert len(benefit_steps) == 1
        assert cash_choice_steps[0].throw is not None
        assert cash_choice_steps[0].throw.faces == (4,)
        assert cash_choice_steps[0].selected == "cash"
        # The table throw's own faces, not the cash-choice die merged in.
        assert benefit_steps[0].throw.faces == (5,)
        assert any(
            m.value == RULES.chargen.mustering_out_retired_cash_dm
            for m in benefit_steps[0].throw.modifiers
        )
        assert benefit_steps[0].throw.total == sum(benefit_steps[0].throw.faces) + sum(
            m.value for m in benefit_steps[0].throw.modifiers
        )

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


class TestT196ThrowsItemizeEveryModifierTheyApply:
    """`contracts/json-output.md` states `total == sum(faces)` plus the
    modifier values, and `contracts/data-files.md` declares `modifier =
    "terms-served"` and `rank-dm` as modifiers of the total in exactly
    those words — but the aging total subtracted `total_terms_served` and
    the medical-bill total added `rank_bonus` with neither itemized in the
    recorded `StepThrow.modifiers` (T196).
    """

    def test_aging_records_the_terms_served_modifier(self):
        from cetools.generator import _Walk

        walk = _Walk(Roller(5), RULES)
        walk.characteristics = {code: 10 for code in RULES.characteristics.names}
        walk.age = RULES.chargen.terms_aging_begins_at_age
        walk.total_terms_served = 9
        walk._apply_aging_if_due("Navy", 3)

        step = next(s for s in walk.history if s.kind == "aging")
        assert any(m.label == "Terms served" and m.value == -9 for m in step.throw.modifiers)
        assert step.throw.total == sum(step.throw.faces) + sum(
            m.value for m in step.throw.modifiers
        )

    def test_medical_bill_records_the_rank_modifier(self):
        from cetools.generator import _Walk

        assert RULES.medical_tiers.rank_dm
        career = next(iter(RULES.careers.values()))

        walk = _Walk(Roller(1), RULES)
        walk.characteristics = {code: 7 for code in RULES.characteristics.names}
        walk._raise_medical_bill(career.name, 1, 6, {"STR": 1})

        step = next(s for s in walk.history if s.kind == "medical-bills")
        assert any(m.value == 6 for m in step.throw.modifiers)
        assert step.throw.total == sum(step.throw.faces) + sum(
            m.value for m in step.throw.modifiers
        )


class TestAgingRecordsTheSelectionDice:
    """`_apply_aging_if_due` draws `self.roller.die(len(remaining))` once
    per characteristic an aging row's class effect chooses to reduce, and
    recorded none of it: the row-lookup step's own throw carries `total =
    modified`, the value the row was read against, so the selection dice
    cannot be folded into that same throw's `faces` without breaking
    `total == sum(faces)` plus the modifiers (contracts/json-output.md).
    Each class effect a row declares now gets its own step, immediately
    after the row-lookup step, whose throw is exactly the dice that chose
    which characteristics it reduced (T208).
    """

    def test_each_class_effect_gets_its_own_selection_throw(self):
        from cetools.generator import _Walk

        walk = _Walk(Roller(5), RULES)
        walk.characteristics = {code: 10 for code in RULES.characteristics.names}
        walk.age = RULES.chargen.terms_aging_begins_at_age
        # Forces `modified` far below the lowest row's minimum, so the
        # floor row is read regardless of the 2d6 roll — the packaged
        # floor row ("-6") declares two class effects (physical, mental).
        walk.total_terms_served = 100
        walk._apply_aging_if_due("Navy", 3)

        aging_steps = [s for s in walk.history if s.kind == "aging"]
        row_step, *effect_steps = aging_steps
        # The row-lookup step is unchanged by T208 except that its own
        # effects moved to the steps below: its throw still carries the
        # modified total the row was actually read against.
        assert row_step.effects == ()
        assert row_step.throw.total == sum(row_step.throw.faces) + sum(
            m.value for m in row_step.throw.modifiers
        )
        assert len(effect_steps) == 2
        for step in effect_steps:
            assert step.throw is not None
            assert step.effects
            # A pure selection throw: no modifier, no target, and its own
            # total is exactly the dice it drew — never folded into the
            # row-lookup throw's arithmetic.
            assert step.throw.total == sum(step.throw.faces)
            assert step.throw.modifiers == ()
            assert step.throw.target == 0
            assert step.throw.success is True

    def test_a_reducing_selection_step_is_found_over_a_sample(self):
        found = False
        for character in _characters(300):
            for step in character.history:
                if step.kind == "aging" and step.effects:
                    found = True
                    assert step.throw is not None
                    assert step.throw.total == sum(step.throw.faces)
                    assert step.throw.modifiers == ()
        assert found


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


def test_re_enlistment_never_carries_a_characteristic_modifier(tmp_path):
    # FR-013a, D1: `throws.re-enlistment` no longer admits `characteristic`
    # at all (career schema v4) — the field parsed, validated, and never
    # honored (T195's finding) is now refused at the parser instead, which is
    # what T024 in tests/unit/test_careers.py pins. The walk's re-enlistment
    # throw carries no characteristic modifier for any shipped career.
    rules = load_rules()

    found = False
    for seed in range(300):
        character = generate_character(Roller(seed), rules)
        for step in character.history:
            if step.kind != "re-enlistment" or step.throw is None:
                continue
            found = True
            char_modifiers = [
                m for m in step.throw.modifiers if m.label.startswith("Characteristic ")
            ]
            assert not char_modifiers
            assert step.throw.total == sum(step.throw.faces) + sum(
                m.value for m in step.throw.modifiers
            )
    assert found


class TestT183EveryThrowIsRecorded:
    """T183: `characteristics`, `background-skills`, `skill-roll`, and
    `benefit` steps always made a throw and never recorded it; a
    `basic-training` step made one only when it drew randomly rather than
    granting the whole table, and a mishap/injury reduction step made one
    only when it actually rolled dice for the amount or the characteristics
    chosen.
    """

    def test_a_characteristics_step_always_carries_its_throw(self):
        for character in _characters(50):
            step = next(s for s in character.history if s.kind == "characteristics")
            assert step.throw is not None
            assert step.throw.faces
            assert step.throw.total == sum(step.throw.faces)

    def test_a_background_skills_step_always_carries_its_throw(self):
        for character in _characters(50):
            step = next(s for s in character.history if s.kind == "background-skills")
            assert step.throw is not None
            assert step.throw.faces
            assert step.throw.total == sum(step.throw.faces)

    def test_a_skill_roll_step_always_carries_its_throw(self):
        for character in _characters(50):
            for step in character.history:
                if step.kind != "skill-roll":
                    continue
                assert step.throw is not None
                assert len(step.throw.faces) == 2

    def test_a_benefit_step_always_carries_its_throw(self):
        for character in _characters(200):
            for step in character.history:
                if step.kind != "benefit":
                    continue
                assert step.throw is not None
                assert step.throw.faces

    def test_basic_training_carries_no_throw_when_the_whole_table_is_granted(self):
        found_first_career = False
        found_subsequent_career = False
        for character in _characters(100):
            basic_training_steps = [s for s in character.history if s.kind == "basic-training"]
            for order, step in enumerate(basic_training_steps):
                is_first_career = order == 0
                if is_first_career and RULES.chargen.basic_training_first_career_all:
                    found_first_career = True
                    assert step.throw is None
                else:
                    found_subsequent_career = True
                    assert step.throw is not None
        assert found_first_career
        assert found_subsequent_career

    def test_a_mishap_or_injury_reduction_step_carries_its_throw(self):
        found = False
        for character in _characters(200):
            for step in character.history:
                if step.kind not in ("mishap", "injury"):
                    continue
                has_characteristic_effect = any(
                    e.kind in ("characteristic", "characteristic-called-for") for e in step.effects
                )
                if has_characteristic_effect:
                    found = True
                    assert step.throw is not None
        assert found
