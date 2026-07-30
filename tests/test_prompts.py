import pytest

from cetools.cli.prompts import key, numbers, offer, spell, split_values

# --- spell / key: the display <-> stored spelling round trip (FR-014, FR-015) ---


def test_spell_turns_underscore_into_space():
    assert spell("bonded_superdense") == "bonded superdense"


def test_spell_accepts_an_int():
    assert spell(100) == "100"


def test_key_lowercases():
    assert key("BONDED_SUPERDENSE") == "bonded_superdense"


def test_key_turns_space_into_underscore():
    assert key("bonded superdense") == "bonded_superdense"


def test_key_turns_hyphen_into_underscore():
    assert key("bonded-superdense") == "bonded_superdense"


def test_key_ignores_surrounding_whitespace():
    assert key("  pop up  ") == "pop_up"


def test_key_collapses_an_internal_whitespace_run_to_one_separator():
    assert key("self   sealing") == "self_sealing"


@pytest.mark.parametrize(
    "stored",
    ["reflec", "self_sealing", "stealth", "pop_up", "fixed", "bonded_superdense", "small_craft"],
)
def test_key_of_spell_round_trips(stored):
    assert key(spell(stored)) == stored


# --- numbers: evenly-spaced run collapsing (FR-005) ---


def test_numbers_collapses_a_run_of_three_or_more():
    assert numbers([1, 2, 3, 4, 5, 6]) == ["1-6"]


def test_numbers_collapses_a_two_element_run_only_when_the_step_is_one():
    assert numbers([1, 2]) == ["1-2"]


def test_numbers_enumerates_a_two_element_run_whose_step_is_not_one():
    assert numbers([1, 3]) == ["1", "3"]


def test_numbers_names_several_runs_in_ascending_order():
    values = (
        list(range(100, 1001, 100)) + list(range(1200, 2001, 200)) + list(range(3000, 5001, 1000))
    )
    assert numbers(values) == [
        "100-1000 by 100",
        "1200-2000 by 200",
        "3000-5000 by 1000",
    ]


def test_numbers_enumerates_a_value_in_no_run_in_its_place():
    assert numbers([1, 2, 3, 4, 100]) == ["1-4", "100"]


def test_numbers_of_a_single_value_enumerates_it():
    assert numbers([7]) == ["7"]


def test_numbers_of_empty_is_empty():
    assert numbers([]) == []


# --- split_values: the greedy longest-match scan (FR-015, FR-018) ---

_ARMOR_OPTION_KEYS = ("reflec", "self_sealing", "stealth")


def test_split_values_keeps_a_two_word_value_whole():
    assert split_values("reflec self sealing", _ARMOR_OPTION_KEYS) == ["reflec", "self_sealing"]


def test_split_values_treats_commas_and_whitespace_alike():
    assert split_values("reflec, self sealing", _ARMOR_OPTION_KEYS) == ["reflec", "self_sealing"]


def test_split_values_accepts_the_underscored_spelling():
    assert split_values("self_sealing reflec", _ARMOR_OPTION_KEYS) == ["self_sealing", "reflec"]


def test_split_values_accepts_the_hyphenated_and_any_case_spelling():
    assert split_values("reflec, Self-Sealing", _ARMOR_OPTION_KEYS) == ["reflec", "self_sealing"]


def test_split_values_raises_naming_a_word_run_that_matches_nothing():
    with pytest.raises(ValueError, match="bogus"):
        split_values("reflec bogus", _ARMOR_OPTION_KEYS)


def test_split_values_span_limit_is_derived_from_known_not_hard_coded():
    known = ("warp_core_stabilizer",)
    assert split_values("warp core stabilizer", known) == ["warp_core_stabilizer"]


# --- offer: the "question (values) [default]:" composition (FR-012) ---


def test_offer_composes_question_and_values():
    assert offer("Fitting", ["armory", "vault", "none"]) == "Fitting (armory, vault, none)"


def test_offer_returns_the_question_unchanged_when_no_values_and_no_note():
    assert offer("Purpose", []) == "Purpose"


def test_offer_emits_the_note_alone_when_values_are_empty():
    assert (
        offer("Power plant rating", [], note="a 10-ton hull can carry none, at least 6")
        == "Power plant rating (a 10-ton hull can carry none, at least 6)"
    )


def test_offer_appends_the_note_after_the_joined_values():
    assert (
        offer("Power plant rating", ["3-5"], note=", at least 3")
        == "Power plant rating (3-5, at least 3)"
    )
