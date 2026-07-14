import dataclasses
import random
from collections import Counter

import pytest

from cetools.engine.careers.aerospace import AEROSPACE_CAREER
from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.careers.scientist import SCIENTIST_CAREER
from cetools.engine.careers.scout import SCOUT_CAREER
from cetools.engine.generator import (
    _HOMEWORLD_SKILLS,
    _apply_material_benefit,
    _apply_skill_entry,
    _apply_stat_boost,
    _draw_distinct,
    _grant_background_skills,
    _muster_out,
    _roll_material_benefit,
    _roll_skill,
    draft_character,
    generate_career_character,
    generate_character,
    random_career_character,
    roll_until_qualified,
)
from cetools.engine.models import STAT_NAMES, Character, GenerationFailure
from cetools.engine.rolls import RandomRolls, RollName, ScriptedRolls


def _rolls(**overrides) -> ScriptedRolls:
    """A career where nothing goes wrong.

    Every check passes, every table roll lands on row 1, every choice takes the
    head of the list, every 2D6 is 10. Psionics is opted out (the gate fails) so
    that tests about careers are not perturbed by psionic rolls.

    Override any of it by name — a test says only what it is actually about.
    """
    checks = {RollName.PSI_GATE: False}
    checks.update(overrides.pop("checks", {}))
    params = dict(default_check=True, default_two_d6=10, default_d6=1, default_choice=0)
    params.update(overrides)
    return ScriptedRolls(checks=checks, **params)


# --- Check helper ---
# The 2D6 + DM >= target rule now lives on the Rolls seam; its tests are in
# tests/test_rolls.py. What remains here is the generator's own DM lookup, which
# is exercised end-to-end by the qualification and survival tests below.


# --- Enlistment ---


def test_enlistment_failure_returns_generation_failure() -> None:
    result = generate_character(NAVY_CAREER, rolls=_rolls(checks={RollName.QUALIFICATION: False}))
    assert isinstance(result, GenerationFailure)
    assert result.exit_code == 1
    assert "enlist" in result.reason.lower() or "navy" in result.reason.lower()


def test_enlistment_pass_returns_character() -> None:
    result = generate_character(NAVY_CAREER, rolls=_rolls())
    assert isinstance(result, Character)


# --- UPP ---


def test_character_upp_is_six_pseudohex_chars() -> None:
    result = generate_character(NAVY_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    assert len(result.upp) == 6
    assert "I" not in result.upp
    assert "O" not in result.upp


# --- Name generation (US2) ---


def test_generated_character_has_non_empty_two_word_name() -> None:
    result = generate_character(NAVY_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    assert result.name
    assert len(result.name.split(" ")) >= 2


# --- Survival failure ---


def test_survival_fail_returns_character_with_mishap() -> None:
    result = generate_character(NAVY_CAREER, rolls=_rolls(checks={RollName.SURVIVAL: False}))
    assert isinstance(result, Character)
    assert result.mishap is not None
    assert result.terms[-1].survived is False


def test_mishap_ended_character_still_rolls_psionics() -> None:
    # A dishonorable discharge (mishap 4) strips benefits, yet psionics is still
    # rolled on the sole return path. Psi 9 gives PsiDM +1, and the talent checks
    # are scripted highest-DM-first: Telepathy and Clairvoyance land, the rest do
    # not. A skipped psionics step would leave psi_strength 0 and fail this test.
    result = generate_character(
        NAVY_CAREER,
        rolls=_rolls(
            checks={
                RollName.SURVIVAL: False,
                RollName.PSI_GATE: True,
                RollName.PSI_TALENT: [True, True, False, False, False],
            },
            two_d6={RollName.PSI_STRENGTH: 9},
            d6={RollName.MISHAP: 4},
        ),
    )
    assert isinstance(result, Character)
    assert result.mishap is not None
    assert result.mishap.discharge_type == "dishonorable"
    assert result.benefits == []
    assert result.psi_strength == 9
    assert result.talents == {"Telepathy": 0, "Clairvoyance": 0}


def test_gate_failure_yields_non_psionic_character() -> None:
    # Minimal pair with the test above: same dishonorable mishap, but the
    # eligibility gate fails, so the character is non-psionic even though
    # generation ran through the psionics step.
    result = generate_character(
        NAVY_CAREER,
        rolls=_rolls(
            checks={RollName.SURVIVAL: False, RollName.PSI_GATE: False},
            two_d6={RollName.PSI_STRENGTH: 9},
            d6={RollName.MISHAP: 4},
        ),
    )
    assert isinstance(result, Character)
    assert result.psi_strength == 0
    assert result.talents == {}


# --- T010: one integration test per SURVIVAL_MISHAPS_TABLE roll ---


def _mishap_character(mishap: int, injury: int | None = None) -> Character:
    """A Navy character whose first term ends in the given mishap-table roll."""
    d6 = {RollName.MISHAP: mishap}
    if injury is not None:
        d6[RollName.INJURY] = injury
    result = generate_character(
        NAVY_CAREER, rolls=_rolls(checks={RollName.SURVIVAL: False}, d6=d6)
    )
    assert isinstance(result, Character)
    return result


def test_mishap_roll_1_injury_no_discharge() -> None:
    # Mishap 1 takes two injury rolls and uses the lower; both land on injury row
    # 6, "no permanent effect".
    result = _mishap_character(mishap=1, injury=6)
    assert result.mishap.roll == 1
    assert result.mishap.discharge_type == "none"
    assert result.mishap.imprisoned is False
    assert result.mishap.injury_reductions == {}
    assert result.mishap.injury_crisis is False
    assert result.debt == 0
    assert result.age == 20


def test_mishap_roll_2_honorable_discharge() -> None:
    result = _mishap_character(mishap=2)
    assert result.mishap.roll == 2
    assert result.mishap.discharge_type == "honorable"
    assert result.mishap.imprisoned is False
    assert result.debt == 0
    assert result.age == 20


def test_mishap_roll_3_honorable_discharge_with_legal_debt() -> None:
    result = _mishap_character(mishap=3)
    assert result.mishap.roll == 3
    assert result.mishap.discharge_type == "honorable"
    assert result.mishap.imprisoned is False
    assert result.debt == 10_000
    assert result.age == 20


def test_mishap_roll_4_dishonorable_discharge_not_imprisoned() -> None:
    result = _mishap_character(mishap=4)
    assert result.mishap.roll == 4
    assert result.mishap.discharge_type == "dishonorable"
    assert result.mishap.imprisoned is False
    assert result.debt == 0
    assert result.age == 20


def test_mishap_roll_5_dishonorable_discharge_imprisoned() -> None:
    # Outcome 5 adds an extra 4 years for imprisonment on top of the mishap
    # term's usual +2 (research.md D9): age == 18 + 2 + 4 == 24.
    result = _mishap_character(mishap=5)
    assert result.mishap.roll == 5
    assert result.mishap.discharge_type == "dishonorable"
    assert result.mishap.imprisoned is True
    assert result.debt == 0
    assert result.age == 24


def test_mishap_roll_6_medical_discharge_with_injury() -> None:
    # Mishap 6 takes a single injury roll; row 6 is "no permanent effect".
    result = _mishap_character(mishap=6, injury=6)
    assert result.mishap.roll == 6
    assert result.mishap.discharge_type == "medical"
    assert result.mishap.imprisoned is False
    assert result.mishap.injury_reductions == {}
    assert result.mishap.injury_crisis is False
    assert result.debt == 0
    assert result.age == 20


def test_draft_character_survival_failure_returns_character_not_failure() -> None:
    # Proves FR-011: draft_character funnels through the same mishap-resolution
    # path as generate_character/generate_career_character, never GenerationFailure.
    result = draft_character(
        rolls=_rolls(
            checks={RollName.SURVIVAL: False},
            d6={RollName.DRAFT: 5, RollName.MISHAP: 2},
        )
    )
    assert isinstance(result, Character)
    assert result.mishap is not None


# --- 7-term cap ---


def test_seven_term_cap_voluntary_musterout() -> None:
    # Re-enlistment of 10 passes Navy's target of 5 every term but is never a
    # natural 12, so the career ends by voluntary muster-out at the 7-term cap.
    result = generate_character(NAVY_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    assert result.terms_served == 7


# --- Natural 12 at term 7 forces term 8 ---


def test_natural_12_at_term_7_forces_term_8() -> None:
    result = generate_character(NAVY_CAREER, rolls=_rolls(two_d6={RollName.REENLISTMENT: 12}))
    assert isinstance(result, Character)
    assert result.terms_served == 8


# --- Basic training ---


def test_first_term_basic_training_grants_all_six_service_skills() -> None:
    result = generate_character(NAVY_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    for skill_name in NAVY_CAREER.service_skills:
        assert (
            skill_name in result.skills
        ), f"Service skill {skill_name!r} missing from character after basic training"


# --- Skills non-empty ---


def test_character_has_non_empty_skills() -> None:
    result = generate_character(NAVY_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    assert len(result.skills) > 0


# --- Aging ---


@pytest.mark.parametrize(
    ("aging", "reenlistment", "dexterity", "endurance", "intelligence"),
    [
        ([4], 10, 12, 12, 12),  # term 4: 4-4 = 0   -> Str-1
        ([3], 10, 11, 12, 12),  # term 4: 3-4 = -1  -> Str-1, Dex-1
        ([2], 10, 11, 11, 12),  # term 4: 2-4 = -2  -> Str/Dex/End -1
        ([12, 2], 10, 11, 11, 12),  # term 5: 2-5 = -3  -> Str-2, Dex-1, End-1
        ([12, 12, 2], 10, 10, 11, 12),  # term 6: 2-6 = -4  -> Str-2, Dex-2, End-1
        ([12, 12, 12, 2], 10, 10, 10, 12),  # term 7: 2-7 = -5  -> Str/Dex/End -2
        ([12, 12, 12, 12, 2], 12, 10, 10, 11),  # term 8: 2-8 = -6  -> and Int-1
    ],
    ids=["0", "-1", "-2", "-3", "-4", "-5", "-6"],
)
def test_aging_ladder_reduces_characteristics(
    aging: list[int],
    reenlistment: int,
    dexterity: int,
    endurance: int,
    intelligence: int,
) -> None:
    # Ageing starts once age reaches 34, i.e. at the end of term 4, and the rung
    # of the ladder is (2D6 - terms_served). Every characteristic starts at 12;
    # ageing is the only thing that touches Dexterity, Endurance and Intelligence
    # under this script (skill rolls only ever grant "+1 Str", so Strength is not
    # asserted on here). A 2D6 of 12 in the earlier terms reduces nothing.
    #
    # The last rung is only reachable in a 8th term: 2D6 bottoms out at 2, and
    # 2 - 7 is only -5. A natural 12 on re-enlistment forces that extra term.
    result = generate_character(
        NAVY_CAREER,
        rolls=_rolls(
            two_d6={
                RollName.CHARACTERISTIC: 12,
                RollName.AGING: aging,
                RollName.REENLISTMENT: reenlistment,
            }
        ),
    )
    assert isinstance(result, Character)
    assert result.characteristics["Dexterity"] == dexterity
    assert result.characteristics["Endurance"] == endurance
    assert result.characteristics["Intelligence"] == intelligence


def test_aging_check_triggers_at_term_4_or_later() -> None:
    # Aging starts once age reaches 34, i.e. from term 4. With a 2D6 of 10 the
    # aging roll (10 - terms_served) never drops below 1, so nothing is reduced —
    # this confirms the aging step runs without disturbing the character.
    result = generate_character(NAVY_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    assert result.terms_served >= 4
    assert result.age >= 34


# --- Pension ---


def test_pension_present_at_5_or_more_terms() -> None:
    result = generate_character(NAVY_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    assert result.terms_served >= 5
    assert result.pension is not None
    assert result.pension > 0


def test_pension_amount_for_seven_terms() -> None:
    result = generate_character(NAVY_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    assert result.terms_served == 7
    assert result.pension == 14000


# --- Cash roll cap ---


def test_cash_roll_cap_at_3() -> None:
    result = generate_character(NAVY_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    cash_benefits = [b for b in result.benefits if b.kind == "cash"]
    assert len(cash_benefits) <= 3


# --- Rank bonuses on mustering out ---


def test_rank_bonus_muster_rolls_applied() -> None:
    # Every check passing carries the character to rank 6 (Commodore), which is
    # worth +3 muster rolls on top of one per term.
    result = generate_character(NAVY_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    assert result.rank == 6
    expected_total = result.terms_served + 3  # O6 bonus = 3
    assert len(result.benefits) == expected_total


# --- Material benefit row 7 reachable via rank DM ---


def test_material_benefit_row_7_reachable_at_rank_5_plus() -> None:
    # rank 5 -> material_dm=1, so idx = clamp(roll + 1 - 1) = roll. A material
    # roll of 6 lands on idx 6 -> "Explorers' Society". Without the rank-5+ DM,
    # idx would clamp to 5 (High Passage), so this confirms row 7 is reachable.
    # terms_served=2 + rank-5 bonus (2) = 4 rolls: 3 cash (the cap), 1 material.
    result = _muster_out(
        career=NAVY_CAREER,
        terms_served=2,
        rank=5,
        skills={},
        characteristics={},
        rolls=_rolls(d6={RollName.CASH_BENEFIT: 6, RollName.MATERIAL_BENEFIT: 6}),
    )
    assert len(result) == 4
    material_benefits = [b for b in result if b.kind == "material"]
    assert any(
        b.material_name == "Explorers' Society" for b in material_benefits
    ), "rank 5+ DM should make material benefit row 7 (Explorers' Society) reachable"


def test_muster_out_grants_explorers_society_once_and_rerolls_repeat() -> None:
    # rank 5 -> material_dm=1, so idx = roll. Two material rolls: the first 6
    # grants "Explorers' Society"; the second 6 would repeat it, so the once-only
    # rule rerolls, and the 2 lands on "Weapon".
    result = _muster_out(
        career=NAVY_CAREER,
        terms_served=3,
        rank=5,
        skills={},
        characteristics={},
        rolls=_rolls(d6={RollName.MATERIAL_BENEFIT: [6, 6, 2]}),
    )
    assert len(result) == 5  # reroll must not add an extra roll (FR-008)
    material = [b.material_name for b in result if b.kind == "material"]
    assert material == ["Explorers' Society", "Weapon"]


# --- Cash DM from Gambling skill ---


def test_gambling_skill_grants_cash_dm_on_muster_out() -> None:
    # A cash roll of 5:
    #   without Gambling: idx = max(0, min(6, 5+0-1)) = 4 -> cash_benefits[4] = 20,000
    #   with Gambling:    idx = max(0, min(6, 5+1-1)) = 5 -> cash_benefits[5] = 50,000
    common = dict(
        career=NAVY_CAREER,
        terms_served=1,
        rank=0,
        characteristics={},
        rolls=_rolls(d6={RollName.CASH_BENEFIT: 5}),
    )
    without_dm = _muster_out(**common, skills={})
    with_dm = _muster_out(**common, skills={"Gambling": 0})
    assert len(without_dm) == 1
    assert len(with_dm) == 1
    assert without_dm[0].cash_amount == 20000
    assert with_dm[0].cash_amount == 50000


# --- Explorers' Society: reroll on repeat ---


def test_roll_material_benefit_grants_explorers_society_when_not_yet_granted() -> None:
    # NAVY_CAREER.material_benefits[6] = "Explorers' Society". material_dm=1, so
    # idx = clamp(roll + 1 - 1) = roll; a roll of 6 -> idx 6.
    name = _roll_material_benefit(NAVY_CAREER, 1, _rolls(d6={RollName.MATERIAL_BENEFIT: 6}), set())
    assert name == "Explorers' Society"


def test_roll_material_benefit_rerolls_once_when_already_granted() -> None:
    # First roll 6 -> "Explorers' Society", already granted, so it rerolls:
    # 3 -> idx 3 -> "Mid Passage".
    name = _roll_material_benefit(
        NAVY_CAREER,
        1,
        _rolls(d6={RollName.MATERIAL_BENEFIT: [6, 3]}),
        {"Explorers' Society"},
    )
    assert name == "Mid Passage"


def test_roll_material_benefit_rerolls_repeatedly_until_non_duplicate() -> None:
    # Three more 6s in a row (each still "Explorers' Society", already granted)
    # before a 2 finally lands on idx 2 -> "Weapon".
    name = _roll_material_benefit(
        NAVY_CAREER,
        1,
        _rolls(d6={RollName.MATERIAL_BENEFIT: [6, 6, 6, 2]}),
        {"Explorers' Society"},
    )
    assert name == "Weapon"


def test_roll_material_benefit_unaffected_for_career_without_explorers_society() -> None:
    # AEROSPACE_CAREER.material_benefits[6] = "+1 Soc" (no "Explorers' Society" entry
    # exists in this table at all), so the uniqueness check can never match —
    # behavior is identical to before this feature, even when `granted_names`
    # already contains that string. material_dm=1, so idx = clamp(6 + 1 - 1) = 6.
    name = _roll_material_benefit(
        AEROSPACE_CAREER,
        1,
        _rolls(d6={RollName.MATERIAL_BENEFIT: 6}),
        {"Explorers' Society"},
    )
    assert name == "+1 Soc"


# --- Research Vessel (Scientist) and Courier Vessel (Scout): once-only ---


def test_roll_material_benefit_grants_research_vessel_when_not_yet_granted() -> None:
    name = _roll_material_benefit(
        SCIENTIST_CAREER, 1, _rolls(d6={RollName.MATERIAL_BENEFIT: 6}), set()
    )
    assert name == "Research Vessel"


def test_roll_material_benefit_rerolls_research_vessel_when_already_granted() -> None:
    # First roll 6 -> "Research Vessel", already granted, so it rerolls:
    # 4 -> idx 4 -> "+1 Soc".
    name = _roll_material_benefit(
        SCIENTIST_CAREER,
        1,
        _rolls(d6={RollName.MATERIAL_BENEFIT: [6, 4]}),
        {"Research Vessel"},
    )
    assert name == "+1 Soc"


def test_roll_material_benefit_grants_courier_vessel_when_not_yet_granted() -> None:
    # SCOUT_CAREER.material_benefits has 6 entries; [5] = "Courier Vessel".
    # material_dm=1, roll 6 -> idx = clamp(6, 0, 5) = 5.
    name = _roll_material_benefit(
        SCOUT_CAREER, 1, _rolls(d6={RollName.MATERIAL_BENEFIT: 6}), set()
    )
    assert name == "Courier Vessel"


def test_roll_material_benefit_rerolls_courier_vessel_when_already_granted() -> None:
    name = _roll_material_benefit(
        SCOUT_CAREER,
        1,
        _rolls(d6={RollName.MATERIAL_BENEFIT: [6, 3]}),
        {"Courier Vessel"},
    )
    assert name == "Mid Passage"


def test_roll_material_benefit_terminates_with_fixed_script_on_granted_unique() -> None:
    # A material roll of 6 always lands on SCOUT_CAREER.material_benefits[5]
    # ("Courier Vessel"). With it already granted, the reroll loop would spin
    # forever without a cap; the fallback must return a non-duplicate benefit.
    name = _roll_material_benefit(
        SCOUT_CAREER,
        1,
        _rolls(d6={RollName.MATERIAL_BENEFIT: 6}),
        {"Courier Vessel"},
    )
    assert name != "Courier Vessel"
    assert name in SCOUT_CAREER.material_benefits


def test_roll_material_benefit_raises_when_no_eligible_benefit_remains() -> None:
    # Degenerate career whose entire material table is once-only benefits that
    # are all already granted: the reroll loop exhausts and the fallback finds
    # nothing, so the guard raises a descriptive error instead of a bare
    # StopIteration. Not reachable with any real career table.
    degenerate = dataclasses.replace(
        SCOUT_CAREER,
        material_benefits=("Explorers' Society", "Research Vessel", "Courier Vessel"),
    )
    granted = {"Explorers' Society", "Research Vessel", "Courier Vessel"}
    with pytest.raises(RuntimeError, match="no material benefit outside"):
        _roll_material_benefit(degenerate, 0, _rolls(), granted)


# --- Benefits non-empty ---


def test_character_has_non_empty_benefits() -> None:
    result = generate_character(NAVY_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    assert len(result.benefits) > 0


# --- terms_served >= 1 ---


def test_successful_character_served_at_least_one_term() -> None:
    result = generate_character(NAVY_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    assert result.terms_served >= 1


# --- Skill rolls per term ---


def _failed_commission_navy() -> ScriptedRolls:
    # Commission fails, so neither commission nor advancement is received and two
    # skill rolls must follow. Each picks the Service Skills table (index 1) and
    # rolls its first entry, "Comms". Re-enlistment of 1 ends the career after
    # one term.
    return _rolls(
        checks={RollName.COMMISSION: False},
        two_d6={RollName.CHARACTERISTIC: 8, RollName.REENLISTMENT: 1},
        choices={RollName.SKILL_TABLE: 1},
        d6={RollName.SKILL_ENTRY: 1},
    )


def test_failed_commission_grants_two_skill_rolls() -> None:
    # Comms is level 0 after basic training; two skill rolls push it to level 2.
    # With only 1 roll it would stay at 1.
    result = generate_character(NAVY_CAREER, rolls=_failed_commission_navy())
    assert isinstance(result, Character)
    assert result.terms_served == 1
    assert result.rank == 0
    assert result.skills.get("Comms") == 2, "failed commission should not reduce skill rolls to 1"


def test_per_term_skill_rolls_recorded_in_term_history() -> None:
    result = generate_character(NAVY_CAREER, rolls=_failed_commission_navy())
    assert isinstance(result, Character)
    term = result.terms[0]
    # 6 from basic training + 2 from skill rolls
    assert len(term.skills_gained) == 8
    # "Comms" appears once in basic training and twice from the two skill rolls
    assert term.skills_gained.count("Comms") == 3


# --- Skill table selection ---

# A career whose four Skills and Training tables have no entries in common, so
# the skill that comes back names the table it came from.
_TAGGED_CAREER = dataclasses.replace(
    NAVY_CAREER,
    personal_development=("PD",) * 6,
    service_skills=("SERVICE",) * 6,
    specialist_skills=("SPECIALIST",) * 6,
    advanced_education=("ADVANCED",) * 6,
)

_EDU_8 = {"Education": 8}  # opens the Advanced Education table


@pytest.mark.parametrize(
    ("index", "table"),
    [(0, "PD"), (1, "SERVICE"), (2, "SPECIALIST"), (3, "ADVANCED")],
)
def test_skill_table_is_chosen_by_index_not_by_a_die(index: int, table: str) -> None:
    # The SRD says to *choose* a Skills and Training table, so cetools picks one
    # uniformly rather than rolling a die and taking it modulo the table count.
    # Each table is addressed by its position, with no die in between.
    entry = _roll_skill(
        _TAGGED_CAREER,
        dict(_EDU_8),
        {},
        _rolls(choices={RollName.SKILL_TABLE: index}),
    )
    assert entry == table


def test_skill_table_selection_is_uniform_across_all_four_tables() -> None:
    # Regression: the table used to be picked with (1D6 - 1) % len(tables). With
    # Advanced Education in play there are four tables, so a d6 modulo 4 gave
    # 0,1,2,3,0,1 — Personal Development and Service Skills came up twice as
    # often as Specialist and Advanced Education. Every table must be equally
    # likely.
    rolls = RandomRolls(random.Random(20260713))
    counts = Counter(_roll_skill(_TAGGED_CAREER, dict(_EDU_8), {}, rolls) for _ in range(4000))
    assert set(counts) == {"PD", "SERVICE", "SPECIALIST", "ADVANCED"}
    for table, count in counts.items():
        assert 850 <= count <= 1150, f"{table} came up {count} times in 4000, expected ~1000"


def test_skill_table_selection_covers_three_tables_below_education_8() -> None:
    # Without Advanced Education there are only three tables, and all three must
    # be reachable.
    rolls = RandomRolls(random.Random(20260713))
    counts = Counter(_roll_skill(_TAGGED_CAREER, {"Education": 7}, {}, rolls) for _ in range(1200))
    assert set(counts) == {"PD", "SERVICE", "SPECIALIST"}


# --- Rank bonus skill levels ---


def test_rank_bonus_skills_granted_at_level_1() -> None:
    # Every skill roll lands on personal_development[0] = "+1 Str", a stat boost
    # rather than a skill, so Zero-G (rank 0) and Tactics (rank 3) can only have
    # come from rank bonuses — and must start at level 1, not 0.
    result = generate_character(NAVY_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    assert result.skills.get("Zero-G") == 1, "rank-0 bonus should grant Zero-G-1"
    assert result.skills.get("Tactics") == 1, "rank-3 bonus should grant Tactics-1"


# --- Extensibility (US3 preview) ---


def test_generate_character_accepts_any_career_without_navy_hardcoding() -> None:
    stub_career = dataclasses.replace(NAVY_CAREER, name="Scout")
    result = generate_character(stub_career, rolls=_rolls())
    assert isinstance(result, (Character, GenerationFailure))


# --- Stat boost helper ---


def test_apply_stat_boost_applies_boost_and_returns_true() -> None:
    characteristics = {"Strength": 7}
    assert _apply_stat_boost("+1 Str", characteristics) is True
    assert characteristics["Strength"] == 8


def test_apply_stat_boost_returns_false_for_plain_skill_name() -> None:
    characteristics = {"Strength": 7}
    assert _apply_stat_boost("Melee Combat", characteristics) is False
    assert characteristics["Strength"] == 7


def test_apply_stat_boost_returns_true_for_unknown_abbreviation_without_applying() -> None:
    characteristics = {"Strength": 7}
    assert _apply_stat_boost("+1 Xyz", characteristics) is True
    assert characteristics == {"Strength": 7}


# --- Characteristic cap at 33 ---


def test_apply_skill_entry_caps_stat_at_33() -> None:
    characteristics = {"Strength": 33}
    _apply_skill_entry("+1 Str", characteristics, {})
    assert characteristics["Strength"] == 33


def test_apply_material_benefit_caps_stat_at_33() -> None:
    characteristics = {"Strength": 33}
    _apply_material_benefit("+1 Str", characteristics, {})
    assert characteristics["Strength"] == 33


# --- T008: roll_until_qualified ---


def test_roll_until_qualified_returns_qualifying_characteristics() -> None:
    # First set of six characteristics is all 2s (Intelligence 2 < 6, fails);
    # the second is all 8s and qualifies.
    rolls = _rolls(two_d6={RollName.CHARACTERISTIC: [2] * 6 + [8] * 6})
    chars = roll_until_qualified(SCOUT_CAREER, rolls)
    assert chars[SCOUT_CAREER.qualification_stat] >= SCOUT_CAREER.qualification_target


def test_roll_until_qualified_loops_until_qualified() -> None:
    # Three failing sets of characteristics (Intelligence 3 < 6), then a passing
    # one. Every stat coming back as 8 — the fourth block — is only possible if
    # the loop discarded the first three.
    rolls = _rolls(two_d6={RollName.CHARACTERISTIC: [3] * 18 + [8] * 6})
    chars = roll_until_qualified(SCOUT_CAREER, rolls)
    assert chars["Intelligence"] >= 6
    assert set(chars.values()) == {8}


# --- T009: generate_character new params ---


def test_preset_characteristics_missing_stat_raises() -> None:
    incomplete = {
        "Strength": 9,
        "Dexterity": 9,
        "Endurance": 9,
        "Intelligence": 9,
        # Education and Social Standing intentionally omitted
    }
    with pytest.raises(ValueError, match="missing required stats"):
        generate_character(NAVY_CAREER, preset_characteristics=incomplete)


def test_preset_characteristics_are_used_not_rolled() -> None:
    # The scripted CHARACTERISTIC roll is 10; the preset says 9, and the preset wins.
    preset = {
        "Strength": 9,
        "Dexterity": 9,
        "Endurance": 9,
        "Intelligence": 9,
        "Education": 9,
        "Social Standing": 9,
    }
    result = generate_character(
        NAVY_CAREER,
        rolls=_rolls(),
        preset_characteristics=preset,
        bypass_qualification=True,
    )
    assert isinstance(result, Character)
    assert result.characteristics["Intelligence"] == 9


def test_bypass_qualification_skips_enlistment() -> None:
    # Qualification would fail, but bypass_qualification must skip the check
    # entirely. Survival then also fails, which resolves via the mishap table
    # rather than a GenerationFailure.
    result = generate_character(
        NAVY_CAREER,
        rolls=_rolls(checks={RollName.QUALIFICATION: False, RollName.SURVIVAL: False}),
        bypass_qualification=True,
    )
    assert isinstance(result, Character)


def test_hard_max_terms_prevents_forced_8th_term() -> None:
    # A natural 12 at term 7 would normally force term 8; hard_max_terms forbids it.
    result = generate_character(
        NAVY_CAREER,
        rolls=_rolls(two_d6={RollName.REENLISTMENT: 12}),
        bypass_qualification=True,
        hard_max_terms=True,
    )
    assert isinstance(result, Character)
    assert result.terms_served == 7


def test_drafted_param_sets_character_drafted_true() -> None:
    result = generate_character(
        NAVY_CAREER,
        rolls=_rolls(),
        bypass_qualification=True,
        drafted=True,
    )
    assert isinstance(result, Character)
    assert result.drafted is True


def test_drafted_defaults_to_false_in_generate_character() -> None:
    result = generate_character(NAVY_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    assert result.drafted is False


# --- T010: generate_career_character with Scout ---


def test_generate_career_character_returns_character() -> None:
    result = generate_career_character(SCOUT_CAREER, rolls=_rolls())
    assert isinstance(result, Character)


def test_generate_career_character_intelligence_at_least_6() -> None:
    result = generate_career_character(SCOUT_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    assert result.characteristics["Intelligence"] >= 6


def test_generate_career_character_piloting_at_level_1() -> None:
    # rank-0 bonus grants Piloting+1 before basic training; basic training skips setting it to 0
    result = generate_career_character(SCOUT_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    assert result.skills.get("Piloting", 0) >= 1


def test_generate_career_character_two_skill_rolls_per_term() -> None:
    # Scout has no commission/advancement → always 2 skill rolls per term
    result = generate_career_character(SCOUT_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    for i, term in enumerate(result.terms):
        non_bt = term.skills_gained if i > 0 else term.skills_gained[6:]
        assert len(non_bt) == 2, f"Term {i + 1} expected 2 skill rolls, got {len(non_bt)}"


def test_generate_career_character_material_roll_5_gives_explorers_society() -> None:
    # rank 0 -> material_dm=0, so idx = clamp(roll + 0 - 1) = roll - 1. A material
    # roll of 5 lands on idx 4 -> SCOUT_CAREER.material_benefits[4] = "Explorers'
    # Society", confirming row 5 is reachable with no rank DM.
    # terms_served=4 + rank-0 bonus (0) = 4 rolls: 3 cash (the cap), 1 material.
    result = _muster_out(
        career=SCOUT_CAREER,
        terms_served=4,
        rank=0,
        skills={},
        characteristics={},
        rolls=_rolls(d6={RollName.CASH_BENEFIT: 5, RollName.MATERIAL_BENEFIT: 5}),
    )
    assert len(result) == 4
    material_benefits = [b for b in result if b.kind == "material"]
    assert any(b.material_name == "Explorers' Society" for b in material_benefits)


# --- T010a: Education < 8 restricts Scout skill rolls to 3 tables ---


def test_education_below_8_excludes_advanced_education_skills() -> None:
    # Education 7 (< 8) leaves only 3 skill tables — no Advanced Education.
    # Navigation and Tactics live only in that table, so they must never appear.
    result = generate_career_character(
        SCOUT_CAREER, rolls=_rolls(two_d6={RollName.CHARACTERISTIC: 7})
    )
    assert isinstance(result, Character)
    exclusively_advanced = {"Navigation", "Tactics"}
    for skill in exclusively_advanced:
        assert (
            skill not in result.skills
        ), f"{skill!r} must not appear when Edu<8 (advanced education excluded)"


def test_education_8_or_above_can_access_advanced_education() -> None:
    # Education 10 (>= 8) opens the 4th table, index 3: advanced_education, whose
    # 4th entry is "Medicine".
    result = generate_career_character(
        SCOUT_CAREER,
        rolls=_rolls(
            choices={RollName.SKILL_TABLE: 3},
            d6={RollName.SKILL_ENTRY: 4},
        ),
    )
    assert isinstance(result, Character)
    assert "Medicine" in result.skills


# --- T010b: single-term Scout muster out ---


def test_single_term_scout_muster_out() -> None:
    # Re-enlistment of 4 misses Scout's target of 6, so the career ends after one
    # term: 1 term + rank-0 bonus (0) = a single benefit roll.
    result = generate_career_character(
        SCOUT_CAREER,
        rolls=_rolls(two_d6={RollName.CHARACTERISTIC: 8, RollName.REENLISTMENT: 4}),
    )
    assert isinstance(result, Character)
    assert result.terms_served == 1
    assert result.skills.get("Piloting", 0) >= 1
    term = result.terms[0]
    assert len(term.skills_gained) == 8  # 6 basic training + 2 skill rolls
    assert len(term.skills_gained[6:]) == 2
    assert len(result.benefits) == 1


# --- T015: draft_character ---


def test_draft_character_roll_5_gives_scout() -> None:
    # DRAFT_TABLE[4] = "scout"; a draft roll of 5 -> index 4.
    result = draft_character(rolls=_rolls(d6={RollName.DRAFT: 5}))
    assert isinstance(result, Character)
    assert result.drafted is True
    assert result.career == "Scout"


def test_draft_character_roll_1_gives_aerospace() -> None:
    # DRAFT_TABLE[0] = "aerospace system defense"; a draft roll of 1 -> index 0.
    result = draft_character(rolls=_rolls(d6={RollName.DRAFT: 1}))
    assert isinstance(result, Character)
    assert result.drafted is True
    assert result.career == "Aerospace System Defense"


def test_draft_character_sets_drafted_true() -> None:
    result = draft_character(rolls=_rolls(d6={RollName.DRAFT: 3}))
    assert isinstance(result, Character)
    assert result.drafted is True


def test_draft_character_roll_2_gives_marine() -> None:
    # DRAFT_TABLE[1] = "marine"; a draft roll of 2 -> index 1.
    result = draft_character(rolls=_rolls(d6={RollName.DRAFT: 2}))
    assert isinstance(result, Character)
    assert result.drafted is True
    assert result.career == "Marine"


# --- T016: draft_character with unimplemented career ---


def test_draft_character_unimplemented_career_returns_failure() -> None:
    from unittest.mock import patch

    # Patch DRAFT_TABLE in generator so index 0 is "smuggler" (not in CAREER_REGISTRY)
    with patch("cetools.engine.generator.DRAFT_TABLE", ("smuggler",) + ("navy",) * 5):
        result = draft_character(rolls=_rolls(d6={RollName.DRAFT: 1}))
    assert isinstance(result, GenerationFailure)
    assert "smuggler" in result.reason


# --- T017: benefits/pension/debt matrix after 5+ completed terms (US3) ---

_SCOUT_PRESET = {
    "Strength": 10,
    "Dexterity": 10,
    "Endurance": 10,
    "Intelligence": 10,
    "Education": 10,
    "Social Standing": 10,
}


def _generate_scout_mishap_after_five_terms(mishap: int, injury: int | None = None) -> Character:
    # Five terms survived, then the sixth ends in the given mishap.
    d6 = {RollName.MISHAP: mishap}
    if injury is not None:
        d6[RollName.INJURY] = injury
    result = generate_character(
        SCOUT_CAREER,
        rolls=_rolls(checks={RollName.SURVIVAL: [True] * 5 + [False]}, d6=d6),
        preset_characteristics=_SCOUT_PRESET,
        bypass_qualification=True,
    )
    assert isinstance(result, Character)
    return result


def test_mishap_outcome_1_preserves_benefits_and_pension_after_five_terms() -> None:
    # Mishap 1 takes two injury rolls; both land on row 6, "no permanent effect".
    result = _generate_scout_mishap_after_five_terms(mishap=1, injury=6)
    assert result.terms_served == 5
    assert len(result.benefits) == 5
    assert result.pension is not None
    assert result.debt == 0


def test_mishap_outcome_2_preserves_benefits_and_pension_after_five_terms() -> None:
    result = _generate_scout_mishap_after_five_terms(mishap=2)
    assert result.terms_served == 5
    assert len(result.benefits) == 5
    assert result.pension is not None
    assert result.debt == 0


def test_mishap_outcome_3_preserves_benefits_and_pension_with_legal_debt() -> None:
    result = _generate_scout_mishap_after_five_terms(mishap=3)
    assert result.terms_served == 5
    assert len(result.benefits) == 5
    assert result.pension is not None
    assert result.debt == 10_000


def test_mishap_outcome_4_forfeits_benefits_and_pension_after_five_terms() -> None:
    result = _generate_scout_mishap_after_five_terms(mishap=4)
    assert result.terms_served == 5
    assert result.benefits == []
    assert result.pension is None


def test_mishap_outcome_5_forfeits_benefits_and_pension_after_five_terms() -> None:
    result = _generate_scout_mishap_after_five_terms(mishap=5)
    assert result.terms_served == 5
    assert result.benefits == []
    assert result.pension is None


def test_mishap_outcome_6_preserves_benefits_and_pension_after_five_terms() -> None:
    # Mishap 6 takes a single injury roll; row 6 is "no permanent effect".
    result = _generate_scout_mishap_after_five_terms(mishap=6, injury=6)
    assert result.terms_served == 5
    assert len(result.benefits) == 5
    assert result.pension is not None
    assert result.debt == 0


# --- T019: mishap during a character's very first term (edge case) ---


def _generate_scout_first_term_mishap(mishap: int, injury: int | None = None) -> Character:
    d6 = {RollName.MISHAP: mishap}
    if injury is not None:
        d6[RollName.INJURY] = injury
    result = generate_character(
        SCOUT_CAREER,
        rolls=_rolls(checks={RollName.SURVIVAL: False}, d6=d6),
        preset_characteristics=_SCOUT_PRESET,
        bypass_qualification=True,
    )
    assert isinstance(result, Character)
    return result


@pytest.mark.parametrize(
    ("mishap", "injury"),
    [(1, 6), (2, None), (3, None), (4, None), (5, None), (6, 6)],
    ids=["outcome1", "outcome2", "outcome3", "outcome4", "outcome5", "outcome6"],
)
def test_first_term_mishap_yields_no_benefits_or_pension(mishap: int, injury: int | None) -> None:
    result = _generate_scout_first_term_mishap(mishap=mishap, injury=injury)
    assert result.terms_served == 0
    assert result.benefits == []
    assert result.pension is None


# --- T011: two skill rolls per term recorded in term history ---


def test_two_skill_rolls_per_term_in_term_history() -> None:
    result = generate_career_character(SCOUT_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    assert result.terms_served >= 2
    # Term 1: 6 basic training entries + 2 skill roll entries
    assert len(result.terms[0].skills_gained) == 8
    # All subsequent terms: exactly 2 skill roll entries each
    for term in result.terms[1:]:
        assert len(term.skills_gained) == 2


# --- Background skills: _draw_distinct ---


def test_draw_distinct_returns_requested_count_of_distinct_items() -> None:
    # Every draw takes index 0, the head of what remains.
    result = _draw_distinct(("A", "B", "C", "D"), 3, _rolls())
    assert result == ["A", "B", "C"]
    assert len(set(result)) == 3


def test_draw_distinct_respects_exclude() -> None:
    result = _draw_distinct(("A", "B", "C"), 2, _rolls(), exclude=("A",))
    assert result == ["B", "C"]
    assert "A" not in result


def test_draw_distinct_truncates_when_over_requested() -> None:
    # Only 2 items available but 5 requested → returns just the 2.
    result = _draw_distinct(("A", "B"), 5, _rolls())
    assert result == ["A", "B"]


def test_draw_distinct_uses_the_choice_to_index() -> None:
    # Index 2 each draw: [A,B,C,D] -> C; then [A,B,D] -> D.
    result = _draw_distinct(
        ("A", "B", "C", "D"), 2, _rolls(choices={RollName.BACKGROUND_SKILL: 2})
    )
    assert result == ["C", "D"]


def test_draw_distinct_can_reach_pool_tail() -> None:
    # Regression: indexing a pool larger than 6 with a fixed d6 left the tail
    # unreachable (Zero-G at index 9 could never be drawn). A choice is sized to
    # the pool, not to a die, so the last element is reachable.
    result = _draw_distinct(_HOMEWORLD_SKILLS, 1, _rolls(choices={RollName.BACKGROUND_SKILL: -1}))
    assert result == ["Zero-G"]


# --- Background skills: _grant_background_skills ---


def test_background_skill_count_matches_three_plus_education_dm() -> None:
    # count = 3 + characteristic_modifier(Education).
    cases = {2: 1, 4: 2, 7: 3, 10: 4, 12: 5, 15: 6}
    for education, expected in cases.items():
        skills: dict[str, int] = {}
        _grant_background_skills({"Education": education}, skills, _rolls())
        assert len(skills) == expected, f"Education {education} should grant {expected} skills"


def test_background_skills_are_all_level_zero() -> None:
    skills: dict[str, int] = {}
    _grant_background_skills({"Education": 12}, skills, _rolls())
    assert all(level == 0 for level in skills.values())


def test_background_low_education_draws_only_homeworld_skills() -> None:
    # count 1 (Edu 2) and count 2 (Edu 4) → every skill comes from the homeworld pool.
    for education in (2, 4):
        skills: dict[str, int] = {}
        _grant_background_skills({"Education": education}, skills, _rolls())
        assert set(skills) <= set(_HOMEWORLD_SKILLS)


def test_background_full_draw_is_deterministic_and_distinct() -> None:
    # Edu 12 → count 5. Every draw takes index 0.
    # Homeworld: Animals, Broker. Education (excluding those): Admin, Advocate, Carousing.
    skills: dict[str, int] = {}
    _grant_background_skills({"Education": 12}, skills, _rolls())
    assert set(skills) == {"Animals", "Broker", "Admin", "Advocate", "Carousing"}


def test_background_skills_reproducible_across_identical_scripts() -> None:
    first: dict[str, int] = {}
    second: dict[str, int] = {}
    choices = {RollName.BACKGROUND_SKILL: [1, 3, 0, 2]}
    _grant_background_skills({"Education": 10}, first, _rolls(choices=choices))
    _grant_background_skills({"Education": 10}, second, _rolls(choices=dict(choices)))
    assert first == second


def test_generate_character_grants_background_skills() -> None:
    # Preset Education 10 → 4 background skills, each drawn at index 0:
    # homeworld Animals, Broker; education Admin, Advocate. None of these are
    # Scout service, rank, or skill-roll outputs under this script, so they can
    # only have come from background granting.
    preset = {
        "Strength": 10,
        "Dexterity": 10,
        "Endurance": 10,
        "Intelligence": 10,
        "Education": 10,
        "Social Standing": 10,
    }
    result = generate_character(
        SCOUT_CAREER,
        rolls=_rolls(),
        preset_characteristics=preset,
        bypass_qualification=True,
    )
    assert isinstance(result, Character)
    for skill in ("Animals", "Broker", "Admin", "Advocate"):
        assert skill in result.skills
    assert result.skills["Broker"] == 0


def test_generate_character_none_qualification_skips_enlistment_failure() -> None:
    no_qual = dataclasses.replace(
        NAVY_CAREER, name="Drifter", qualification_stat=None, qualification_target=None
    )
    # The qualification check would fail, but a career with no qualification must
    # never run it — so no enlistment failure.
    result = generate_character(no_qual, rolls=_rolls(checks={RollName.QUALIFICATION: False}))
    assert isinstance(result, Character)


def test_generate_character_concrete_qualification_still_gates() -> None:
    result = generate_character(NAVY_CAREER, rolls=_rolls(checks={RollName.QUALIFICATION: False}))
    assert isinstance(result, GenerationFailure)
    assert "enlistment failed" in result.reason


def test_roll_until_qualified_none_qualification_returns_immediately() -> None:
    no_qual = dataclasses.replace(
        NAVY_CAREER, name="Drifter", qualification_stat=None, qualification_target=None
    )
    # Every stat rolls a 1 — Navy would loop forever; no-qual returns at once.
    result = roll_until_qualified(no_qual, rolls=_rolls(two_d6={RollName.CHARACTERISTIC: 1}))
    assert set(result.keys()) == set(STAT_NAMES)


def test_muster_out_ship_shares_rolls_quantity() -> None:
    ship_career = dataclasses.replace(
        NAVY_CAREER,
        material_benefits=(
            "Low Passage",
            "+1 Int",
            "Weapon",
            "Mid Passage",
            "+1 Soc",
            "High Passage",
            "1D6 Ship Shares",
        ),
    )
    characteristics = {stat: 7 for stat in STAT_NAMES}
    # rank 5 -> material_dm=1 and +2 bonus muster rolls; terms=2 -> 4 total rolls
    # (3 cash, the cap, then 1 material). The material roll of 6 lands on idx 6 ->
    # "1D6 Ship Shares", whose quantity is then rolled separately.
    benefits = _muster_out(
        ship_career,
        2,
        5,
        {},
        characteristics,
        _rolls(
            d6={
                RollName.CASH_BENEFIT: 1,
                RollName.MATERIAL_BENEFIT: 6,
                RollName.SHIP_SHARES: 3,
            }
        ),
    )
    material = [b for b in benefits if b.kind == "material"]
    assert len(material) == 1
    assert material[0].material_name == "Ship Shares"
    assert material[0].material_quantity == 3
    # ship shares do not touch characteristics
    assert all(value == 7 for value in characteristics.values())


def test_muster_out_zero_cash_benefit() -> None:
    from cetools.engine.careers.barbarian import BARBARIAN_CAREER

    characteristics = {stat: 7 for stat in STAT_NAMES}
    # rank 0, terms=1 -> 1 roll (cash). A cash roll of 1 with no Gambling DM
    # -> idx 0 -> cash_benefits[0] == 0.
    benefits = _muster_out(
        BARBARIAN_CAREER, 1, 0, {}, characteristics, _rolls(d6={RollName.CASH_BENEFIT: 1})
    )
    cash = [b for b in benefits if b.kind == "cash"]
    assert len(cash) == 1
    assert cash[0].cash_amount == 0


def test_muster_out_hunter_ship_shares() -> None:
    from cetools.engine.careers.hunter import HUNTER_CAREER

    characteristics = {stat: 7 for stat in STAT_NAMES}
    # rank 0 -> material_dm=0; terms=4 -> 4 rolls (3 cash, the cap, then 1
    # material). The material roll of 5 lands on idx 4 -> "1D6 Ship Shares".
    benefits = _muster_out(
        HUNTER_CAREER,
        4,
        0,
        {},
        characteristics,
        _rolls(
            d6={
                RollName.CASH_BENEFIT: 1,
                RollName.MATERIAL_BENEFIT: 5,
                RollName.SHIP_SHARES: 3,
            }
        ),
    )
    material = [b for b in benefits if b.kind == "material"]
    assert len(material) == 1
    assert material[0].material_name == "Ship Shares"
    assert material[0].material_quantity == 3


def test_generate_career_character_drifter_no_qualification() -> None:
    from cetools.engine.careers.drifter import DRIFTER_CAREER

    result = generate_career_character(DRIFTER_CAREER, rolls=_rolls())
    assert isinstance(result, Character)
    assert result.career == "Drifter"


def test_muster_out_belter_ship_shares() -> None:
    from cetools.engine.careers.belter import BELTER_CAREER

    characteristics = {stat: 7 for stat in STAT_NAMES}
    benefits = _muster_out(
        BELTER_CAREER,
        4,
        0,
        {},
        characteristics,
        _rolls(
            d6={
                RollName.CASH_BENEFIT: 1,
                RollName.MATERIAL_BENEFIT: 5,
                RollName.SHIP_SHARES: 3,
            }
        ),
    )
    material = [b for b in benefits if b.kind == "material"]
    assert len(material) == 1
    assert material[0].material_name == "Ship Shares"
    assert material[0].material_quantity == 3


# --- Psionics ---


def test_generated_character_has_psionics() -> None:
    # The gate passes and the Psi roll is 11, so Psi = max(0, 11 - terms_served).
    # terms_served is on the result, so the relationship holds without predicting
    # the whole generation.
    result = generate_career_character(
        NAVY_CAREER,
        _rolls(
            checks={RollName.PSI_GATE: True},
            two_d6={RollName.PSI_STRENGTH: 11},
        ),
    )
    assert isinstance(result, Character)
    assert isinstance(result.talents, dict)
    assert result.psi_strength == max(0, 11 - result.terms_served)


# --- T018: random_career_character ---


def test_random_career_character_selects_career_by_first_roll() -> None:
    # Careers are offered in name order; index 8 is Drifter (which has no
    # qualification, so generation completes on the defaults).
    result = random_career_character(_rolls(choices={RollName.CAREER: 8}))
    assert isinstance(result, Character)
    assert result.career == "Drifter"


def test_random_career_character_varies_with_first_roll() -> None:
    drifter = random_career_character(_rolls(choices={RollName.CAREER: 8}))
    aerospace = random_career_character(_rolls(choices={RollName.CAREER: 0}))
    assert aerospace.career == "Aerospace System Defense"
    assert drifter.career != aerospace.career


def test_random_career_character_passes_drafted_through() -> None:
    result = random_career_character(_rolls(choices={RollName.CAREER: 8}), drafted=True)
    assert isinstance(result, Character)
    assert result.drafted is True
