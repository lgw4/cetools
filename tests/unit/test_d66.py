from cetools.dice import Roller, d66, parse_notation


def test_d66_session_alpha_matches_published_table():
    result = d66(Roller("session-alpha"))
    assert result.faces == (1, 5)
    assert result.total == 15
    assert result.modifier == 0
    assert result.notation == "d66"


def test_parse_notation_d66_returns_none():
    assert parse_notation("d66") is None


def test_parse_notation_1d66_returns_general_grammar_tuple():
    assert parse_notation("1d66") == (1, 66, 0)


def test_parse_notation_d66_is_case_insensitive():
    assert parse_notation("D66") is None
    assert parse_notation("d66") is None


def test_seeded_sample_of_d66_covers_all_36_values_with_valid_digits():
    roller = Roller("session-alpha")
    values = {d66(roller).total for _ in range(1000)}
    assert values == {10 * tens + units for tens in range(1, 7) for units in range(1, 7)}
