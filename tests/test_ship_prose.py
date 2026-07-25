"""Table-driven tests for the text primitives in `engine/ships/prose.py`.

Every case here is a rule from data-model.md section 5, testable without
building a `Ship`: that is the point of the module boundary (research.md
Part G).
"""

import pytest

from cetools.engine.ships.prose import (
    article,
    count,
    join,
    money,
    number,
    plural,
    signed,
    tonnage_article,
    tons,
)

# --- count: words zero-ten, digits above ten (FR-022) ---

COUNT_CASES = [
    (0, "zero"),
    (1, "one"),
    (2, "two"),
    (3, "three"),
    (4, "four"),
    (5, "five"),
    (6, "six"),
    (7, "seven"),
    (8, "eight"),
    (9, "nine"),
    (10, "ten"),
    (11, "11"),
    (12, "12"),
    (18, "18"),
    (25, "25"),
    (35, "35"),
    (120, "120"),
    (1096, "1096"),
]


@pytest.mark.parametrize("value,expected", COUNT_CASES)
def test_count_words_below_eleven_and_digits_above(value, expected):
    assert count(value) == expected


def test_count_never_emits_a_thousands_separator():
    assert count(1096) == "1096"
    assert count(12345) == "12345"


# --- tons: the count rule when whole, digits when fractional (FR-022b) ---

TONS_CASES = [
    (0, "zero"),
    (0.0, "zero"),
    (1, "one"),
    (1.0, "one"),
    (2, "two"),
    (5.0, "five"),
    (10.0, "ten"),
    (11.0, "11"),
    (22, "22"),
    (44.0, "44"),
    (84, "84"),
    (135.0, "135"),
    (0.5, "0.5"),
    (1.3, "1.3"),
    (6.2, "6.2"),
    (2.5, "2.5"),
    (10.5, "10.5"),
]


@pytest.mark.parametrize("value,expected", TONS_CASES)
def test_tons_uses_the_count_rule_when_whole_and_digits_when_fractional(value, expected):
    assert tons(value) == expected


def test_tons_never_emits_a_dangling_decimal_point():
    for value in (1.0, 12.0, 135.0, 0.0):
        assert not tons(value).endswith(".")


# --- number: digits always (FR-022a, FR-025) ---

NUMBER_CASES = [
    (0, "0"),
    (0.0, "0"),
    (1, "1"),
    (1.0, "1"),
    (2, "2"),
    (4, "4"),
    (8, "8"),
    (135.0, "135"),
    (0.5, "0.5"),
    (6.2, "6.2"),
    (1.3, "1.3"),
    (0.00125, "0.00125"),
    (597.87, "597.87"),
    (2768.145, "2768.145"),
    (1000000.0, "1000000"),
]


@pytest.mark.parametrize("value,expected", NUMBER_CASES)
def test_number_is_always_digits_with_trailing_zeros_stripped(value, expected):
    assert number(value) == expected


def test_number_never_uses_scientific_notation():
    for value in (1e7, 1.25e-3, 5_000_000.0):
        assert "e" not in number(value)
        assert "E" not in number(value)


def test_number_never_emits_a_dangling_decimal_point():
    for value in (1.0, 597.870, 1e7):
        assert not number(value).endswith(".")


def test_number_carries_no_thousands_separator():
    assert number(2768.145) == "2768.145"
    assert number(1146.915) == "1146.915"


def test_number_strips_the_float_accumulation_artefact():
    assert number(29.771999999999998) == "29.772"


# --- money: number plus thousands separators (FR-020, FR-025, FR-025a) ---

MONEY_CASES = [
    (0, "0"),
    (8, "8"),
    (29.772, "29.772"),
    (29.771999999999998, "29.772"),
    (33.219, "33.219"),
    (194.445, "194.445"),
    (597.870, "597.87"),
    (1146.915, "1,146.915"),
    (2768.145, "2,768.145"),
    (1000, "1,000"),
    (1000000.5, "1,000,000.5"),
    (0.00125, "0.00125"),
]


@pytest.mark.parametrize("value,expected", MONEY_CASES)
def test_money_renders_full_precision_with_thousands_separators(value, expected):
    assert money(value) == expected


def test_money_never_uses_scientific_notation():
    assert "e" not in money(1e7)
    assert money(1e7) == "10,000,000"


def test_money_never_emits_a_dangling_decimal_point():
    for value in (8, 597.870, 1000):
        assert not money(value).endswith(".")


# --- signed: an explicit sign at every magnitude (FR-009) ---

SIGNED_CASES = [(-4, "-4"), (-2, "-2"), (0, "+0"), (1, "+1"), (2, "+2"), (12, "+12")]


@pytest.mark.parametrize("value,expected", SIGNED_CASES)
def test_signed_always_carries_an_explicit_sign(value, expected):
    assert signed(value) == expected


def test_signed_zero_is_plus_zero_never_bare_zero():
    assert signed(0) == "+0"


# --- plural: the caller supplies both spellings (FR-023) ---


@pytest.mark.parametrize("n", [0, 2, 3, 11, 120])
def test_plural_uses_the_plural_form_for_every_count_but_one(n):
    assert plural(n, "stateroom", "staterooms") == "staterooms"


def test_plural_uses_the_singular_form_at_exactly_one():
    assert plural(1, "stateroom", "staterooms") == "stateroom"


def test_plural_never_derives_a_spelling_by_suffix():
    assert plural(4, "armory", "armories") == "armories"
    assert plural(1, "armory", "armories") == "armory"
    assert plural(2, "fuel scoops", "fuel scoops") == "fuel scoops"


# The description agrees a noun with a *tonnage* in three places -- fuel tankage,
# cargo capacity and hangar capacity -- and `Ship.jump_fuel`, `Ship.power_fuel`
# and `Ship.cargo_tons` are all floats, so `plural` is called with a float there
# as often as with an int. Both domains are pinned here (FR-023, FR-022b).
@pytest.mark.parametrize("value", [0.0, 0.5, 1.3, 2.0, 6.2, 22.0])
def test_plural_uses_the_plural_form_for_a_tonnage_that_is_not_one(value):
    assert plural(value, "ton", "tons") == "tons"


def test_plural_uses_the_singular_form_for_a_tonnage_of_exactly_one():
    assert plural(1.0, "ton", "tons") == "ton"


# --- join: commas and a final "and", no serial comma (FR-024) ---

JOIN_CASES = [
    ([], ""),
    (["a pilot"], "a pilot"),
    (["one pilot", "one navigator"], "one pilot and one navigator"),
    (
        ["one pilot", "one navigator", "one engineer"],
        "one pilot, one navigator and one engineer",
    ),
    (
        ["an armory", "four detention cells", "fuel scoops", "a vault"],
        "an armory, four detention cells, fuel scoops and a vault",
    ),
]


@pytest.mark.parametrize("items,expected", JOIN_CASES)
def test_join_uses_no_serial_comma(items, expected):
    assert join(items) == expected


def test_join_of_three_has_exactly_one_comma():
    assert join(["a", "b", "c"]).count(",") == 1


def test_join_accepts_a_tuple_as_well_as_a_list():
    assert join(("a", "b")) == "a and b"


# --- article: "an" before a vowel letter (FR-023a) ---

ARTICLE_CASES = [
    ("armory", "an"),
    ("engineer", "an"),
    ("intake", "an"),
    ("observation deck", "an"),
    ("upper hold", "an"),
    ("meson screen", "a"),
    ("nuclear damper", "a"),
    ("pulse laser", "a"),
    ("vault", "a"),
]


@pytest.mark.parametrize("word,expected", ARTICLE_CASES)
def test_article_picks_an_before_a_leading_vowel_letter(word, expected):
    assert article(word) == expected


# --- tonnage_article: "an" for a leading 8 (research.md Part C) ---

TONNAGE_ARTICLE_CASES = [
    (10, "a"),
    (40, "a"),
    (50, "a"),
    (100, "a"),
    (200, "a"),
    (300, "a"),
    (400, "a"),
    (500, "a"),
    (600, "a"),
    (700, "a"),
    (800, "an"),
    (80, "an"),
    (85, "an"),
    (900, "a"),
    (1000, "a"),
    (1800, "a"),
    (5000, "a"),
]


@pytest.mark.parametrize("value,expected", TONNAGE_ARTICLE_CASES)
def test_tonnage_article_is_an_only_for_a_leading_eight(value, expected):
    assert tonnage_article(value) == expected


def test_tonnage_article_covers_every_tabulated_hull_size():
    from cetools.engine.ships.tables import HULLS, SMALL_CRAFT_HULLS

    for hull_tons in (*HULLS, *SMALL_CRAFT_HULLS):
        assert tonnage_article(hull_tons) in ("a", "an")


# --- FR-022c: the three numeric helpers occupy disjoint domains ---


@pytest.mark.parametrize("value", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
def test_count_and_tons_agree_and_both_disagree_with_number_on_a_whole_value(value):
    # A slot rendered by the wrong helper must be detectable: `count` and `tons`
    # spell a small whole value as a word, `number` always as digits. Rendering
    # "2 tons allocated to fire control" instead of "two tons" is therefore a
    # visible difference, not a silent one (FR-022c).
    assert count(value) == tons(value)
    assert count(value).isalpha()
    assert number(value).isdigit()
    assert number(value) != count(value)


def test_no_helper_silently_accepts_the_domain_of_another():
    # `tons` is the only helper that switches on whole-vs-fractional; `count`
    # is integer-only and `number`/`money` are digits-only, at every magnitude.
    assert tons(2.5) == "2.5" and tons(2.0) == "two"
    assert number(2.0) == "2" and number(2.5) == "2.5"
    assert money(2.0) == "2" and money(2.5) == "2.5"
    assert count(2) == "two"
