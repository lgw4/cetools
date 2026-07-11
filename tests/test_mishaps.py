from collections import Counter

from cetools.engine.dice import RandomDiceRoller
from cetools.engine.mishaps import (
    INJURY_TABLE,
    SURVIVAL_MISHAPS_TABLE,
    InjuryEntry,
    MishapEntry,
    resolve_survival_mishap,
)
from conftest import SequenceRoller

# --- T004: table shape ---


def test_survival_mishaps_table_has_six_entries() -> None:
    assert len(SURVIVAL_MISHAPS_TABLE) == 6


def test_injury_table_has_six_entries() -> None:
    assert len(INJURY_TABLE) == 6


def test_survival_mishaps_table_rows_match_data_model() -> None:
    expected = {
        1: ("none", False, 0, 2),
        2: ("honorable", False, 0, 0),
        3: ("honorable", False, 10_000, 0),
        4: ("dishonorable", False, 0, 0),
        5: ("dishonorable", True, 0, 0),
        6: ("medical", False, 0, 1),
    }
    for roll, (discharge_type, imprisoned, debt, injury_rolls) in expected.items():
        entry = SURVIVAL_MISHAPS_TABLE[roll - 1]
        assert isinstance(entry, MishapEntry)
        assert entry.discharge_type == discharge_type
        assert entry.imprisoned == imprisoned
        assert entry.debt == debt
        assert entry.injury_rolls == injury_rolls


def test_injury_table_rows_match_data_model() -> None:
    expected = {
        1: (("Strength", "Dexterity", "Endurance"), 1, 0, 2),
        2: (("Strength", "Dexterity", "Endurance"), 1, 0, 0),
        3: (("Strength", "Dexterity"), 0, 2, 0),
        4: (("Strength", "Dexterity", "Endurance"), 0, 2, 0),
        5: (("Strength", "Dexterity", "Endurance"), 0, 1, 0),
        6: ((), 0, 0, 0),
    }
    for roll, (candidate_stats, primary_dice, primary_fixed, secondary_amount) in expected.items():
        entry = INJURY_TABLE[roll - 1]
        assert isinstance(entry, InjuryEntry)
        assert entry.candidate_stats == candidate_stats
        assert entry.primary_dice == primary_dice
        assert entry.primary_fixed == primary_fixed
        assert entry.secondary_amount == secondary_amount


# --- T005: non-injury outcomes ---


def test_mishap_roll_2_is_honorable_discharge_no_debt() -> None:
    characteristics = {"Strength": 8, "Dexterity": 8, "Endurance": 8}
    before = dict(characteristics)
    roller = SequenceRoller([2], default=6)
    outcome, debt = resolve_survival_mishap(roller, characteristics)
    assert outcome.roll == 2
    assert outcome.discharge_type == "honorable"
    assert outcome.imprisoned is False
    assert outcome.injury_reductions == {}
    assert outcome.injury_crisis is False
    assert debt == 0
    assert characteristics == before


def test_mishap_roll_3_is_honorable_discharge_with_legal_debt() -> None:
    characteristics = {"Strength": 8, "Dexterity": 8, "Endurance": 8}
    before = dict(characteristics)
    roller = SequenceRoller([3], default=6)
    outcome, debt = resolve_survival_mishap(roller, characteristics)
    assert outcome.roll == 3
    assert outcome.discharge_type == "honorable"
    assert outcome.imprisoned is False
    assert outcome.injury_reductions == {}
    assert outcome.injury_crisis is False
    assert debt == 10_000
    assert characteristics == before


def test_mishap_roll_4_is_dishonorable_discharge_not_imprisoned() -> None:
    characteristics = {"Strength": 8, "Dexterity": 8, "Endurance": 8}
    roller = SequenceRoller([4], default=6)
    outcome, debt = resolve_survival_mishap(roller, characteristics)
    assert outcome.roll == 4
    assert outcome.discharge_type == "dishonorable"
    assert outcome.imprisoned is False
    assert debt == 0


def test_mishap_roll_5_is_dishonorable_discharge_imprisoned() -> None:
    characteristics = {"Strength": 8, "Dexterity": 8, "Endurance": 8}
    roller = SequenceRoller([5], default=6)
    outcome, debt = resolve_survival_mishap(roller, characteristics)
    assert outcome.roll == 5
    assert outcome.discharge_type == "dishonorable"
    assert outcome.imprisoned is True
    assert debt == 0


# --- T005: injury outcomes (single injury roll, mishap roll 6) ---


def test_mishap_roll_6_injury_row_2_reduces_one_physical_stat_only() -> None:
    # mishap roll=6 -> 1 injury roll; injury roll=2 (all-3 candidates, primary_dice=1,
    # secondary_amount=0); candidate pick=1 -> Strength; 1D6 primary amount=3
    characteristics = {"Strength": 8, "Dexterity": 8, "Endurance": 8}
    roller = SequenceRoller([6, 2, 1, 3], default=6)
    outcome, debt = resolve_survival_mishap(roller, characteristics)
    assert outcome.roll == 6
    assert outcome.discharge_type == "medical"
    assert outcome.injury_reductions == {"Strength": 3}
    assert characteristics["Strength"] == 5
    assert characteristics["Dexterity"] == 8
    assert characteristics["Endurance"] == 8
    assert outcome.injury_crisis is False
    assert debt == 0


def test_mishap_roll_6_injury_row_1_reduces_secondary_stats_by_2() -> None:
    # injury roll=1 (all-3 candidates, primary_dice=1, secondary_amount=2);
    # candidate pick=1 -> Strength; 1D6 primary amount=3
    characteristics = {"Strength": 8, "Dexterity": 8, "Endurance": 8}
    roller = SequenceRoller([6, 1, 1, 3], default=6)
    outcome, debt = resolve_survival_mishap(roller, characteristics)
    assert outcome.injury_reductions == {"Strength": 3, "Dexterity": 2, "Endurance": 2}
    assert characteristics["Strength"] == 5
    assert characteristics["Dexterity"] == 6
    assert characteristics["Endurance"] == 6


def test_mishap_roll_6_injury_row_3_candidate_pick_excludes_endurance() -> None:
    # injury roll=3 (candidates=Strength/Dexterity only, primary_fixed=2, no roll for amount);
    # candidate pick roll(2)=2 -> Dexterity (never Endurance, since it's not a candidate)
    characteristics = {"Strength": 8, "Dexterity": 8, "Endurance": 8}
    roller = SequenceRoller([6, 3, 2], default=6)
    outcome, debt = resolve_survival_mishap(roller, characteristics)
    assert outcome.injury_reductions == {"Dexterity": 2}
    assert characteristics["Dexterity"] == 6
    assert characteristics["Strength"] == 8
    assert characteristics["Endurance"] == 8


# --- T006(a): roll twice, take the lower (more severe) result ---


def test_mishap_roll_1_applies_lower_of_two_injury_rolls() -> None:
    # mishap roll=1 -> 2 injury rolls: 5 then 2 -> min=2 -> row 2 applies, not row 5
    # candidate pick=1 -> Strength; 1D6 primary amount=4
    characteristics = {"Strength": 8, "Dexterity": 8, "Endurance": 8}
    roller = SequenceRoller([1, 5, 2, 1, 4], default=6)
    outcome, debt = resolve_survival_mishap(roller, characteristics)
    assert outcome.roll == 1
    assert outcome.discharge_type == "none"
    assert outcome.injury_reductions == {"Strength": 4}
    assert characteristics["Strength"] == 4
    assert characteristics["Dexterity"] == 8
    assert characteristics["Endurance"] == 8


# --- T006(b): injury crisis charges debt and restores the stat to 1 ---


def test_injury_crisis_restores_zeroed_stat_to_one_and_charges_debt() -> None:
    # injury roll=2 (primary_dice=1, secondary=0); candidate pick=1 -> Strength;
    # 1D6 primary amount=6 -> Strength 2 - 6 -> clamped to 0 -> crisis; crisis roll=3 -> Cr30,000
    characteristics = {"Strength": 2, "Dexterity": 8, "Endurance": 8}
    roller = SequenceRoller([6, 2, 1, 6, 3], default=6)
    outcome, debt = resolve_survival_mishap(roller, characteristics)
    assert characteristics["Strength"] == 1
    assert outcome.injury_crisis is True
    assert debt == 30_000


# --- T006(c): a single mishap zeroing two stats charges only one crisis debt ---


def test_injury_crisis_zeroing_two_stats_charges_only_one_debt() -> None:
    # injury roll=1 (primary_dice=1, secondary_amount=2); candidate pick=1 -> Strength
    # (so Dexterity/Endurance are the secondaries); both already low enough to be zeroed
    # by the -2 secondary reduction. crisis roll=1 -> Cr10,000 (charged once, not twice).
    characteristics = {"Strength": 8, "Dexterity": 1, "Endurance": 1}
    roller = SequenceRoller([6, 1, 1, 3, 1], default=6)
    outcome, debt = resolve_survival_mishap(roller, characteristics)
    assert characteristics["Dexterity"] == 1
    assert characteristics["Endurance"] == 1
    assert outcome.injury_crisis is True
    assert debt == 10_000


# --- Regression: a stat already at 0 before this mishap's injury (e.g. from prior
# aging) must not spuriously trigger a crisis or get "restored" ---


def test_injury_on_already_zero_stat_does_not_trigger_crisis() -> None:
    # Strength is already 0 (e.g. from prior _apply_aging) before this mishap's
    # injury; injury roll=2 (primary_dice=1, secondary=0); candidate pick=1 ->
    # Strength; 1D6 primary amount=3 -> Strength stays at 0 (not driven there by
    # this injury), so no crisis should fire and the stat is left as-is.
    characteristics = {"Strength": 0, "Dexterity": 8, "Endurance": 8}
    roller = SequenceRoller([6, 2, 1, 3], default=6)
    outcome, debt = resolve_survival_mishap(roller, characteristics)
    assert outcome.injury_reductions == {"Strength": 3}
    assert characteristics["Strength"] == 0
    assert outcome.injury_crisis is False
    assert debt == 0


# --- T006(d): mutates characteristics in place ---


def test_resolve_survival_mishap_mutates_characteristics_in_place() -> None:
    characteristics = {"Strength": 8, "Dexterity": 8, "Endurance": 8}
    roller = SequenceRoller([6, 2, 1, 3], default=6)
    same_dict = characteristics
    resolve_survival_mishap(roller, characteristics)
    assert characteristics is same_dict
    assert characteristics["Strength"] == 5


# --- T007: SC-004 statistical distribution ---


def test_mishap_roll_distribution_within_ten_percent_of_uniform() -> None:
    roller = RandomDiceRoller()
    results = []
    for _ in range(10_000):
        characteristics = {"Strength": 10, "Dexterity": 10, "Endurance": 10}
        results.append(resolve_survival_mishap(roller, characteristics))
    counts = Counter(outcome.roll for outcome, _debt in results)
    for roll in range(1, 7):
        assert 1500 <= counts[roll] <= 1834, f"roll {roll} count {counts[roll]} out of tolerance"


# --- Career military classification (guards against silent drift) ---


def test_exactly_the_expected_careers_are_military() -> None:
    from cetools.engine.careers.registry import (
        CAREER_REGISTRY,
        is_military_career,
    )

    expected_military = {
        "Aerospace System Defense",
        "Marine",
        "Maritime System Defense",
        "Navy",
        "Scout",
        "Surface System Defense",
    }
    actual_military = {
        career.name for career in CAREER_REGISTRY.values() if is_military_career(career.name)
    }
    assert actual_military == expected_military


def test_military_names_report_draft_keys_missing_from_registry() -> None:
    import pytest

    from cetools.engine.careers.registry import (
        CAREER_REGISTRY,
        _collect_military_career_names,
    )

    with pytest.raises(ValueError, match="ghost career"):
        _collect_military_career_names(("navy", "ghost career"), CAREER_REGISTRY)
