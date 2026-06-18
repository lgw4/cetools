from cetools.engine.models import Benefit, Character
from cetools.formatter import format_character


def _make_character(pension: int | None = 14000) -> Character:
    return Character(
        characteristics={
            "Strength": 7,
            "Dexterity": 10,
            "Endurance": 6,
            "Intelligence": 11,
            "Education": 8,
            "Social Standing": 5,
        },
        upp="7A6B85",
        age=46,
        career="Navy",
        rank=6,
        rank_title="Commodore",
        terms_served=7,
        skills={"Engineering": 2, "Gunnery": 1, "Navigation": 2, "Tactics": 1, "Zero-G": 1},
        benefits=[
            Benefit(kind="cash", cash_amount=50000),
            Benefit(kind="cash", cash_amount=20000),
            Benefit(kind="cash", cash_amount=10000),
            Benefit(kind="material", material_name="High Passage"),
            Benefit(kind="material", material_name="+1 Edu"),
            Benefit(kind="material", material_name="Explorer's Society"),
            Benefit(kind="material", material_name="Mid Passage"),
        ],
        pension=pension,
        terms=[],
    )


def test_output_contains_upp():
    output = format_character(_make_character())
    assert "UPP:" in output
    assert "7A6B85" in output


def test_no_i_or_o_in_upp():
    output = format_character(_make_character())
    upp_line = next(line for line in output.splitlines() if "UPP:" in line)
    upp_value = upp_line.split("UPP:")[-1].strip()
    assert "I" not in upp_value
    assert "O" not in upp_value


def test_output_contains_career_name():
    output = format_character(_make_character())
    assert "Navy" in output


def test_output_contains_rank_title():
    output = format_character(_make_character())
    assert "Commodore" in output


def test_output_contains_terms():
    output = format_character(_make_character())
    assert "7" in output


def test_output_contains_age():
    output = format_character(_make_character())
    assert "46" in output


def test_output_contains_all_characteristic_names():
    output = format_character(_make_character())
    for name in (
        "Strength",
        "Dexterity",
        "Endurance",
        "Intelligence",
        "Education",
        "Social Standing",
    ):
        assert name in output


def test_characteristic_over_9_shows_pseudohex():
    output = format_character(_make_character())
    # Dexterity=10 → A, Intelligence=11 → B
    assert "A" in output
    assert "B" in output


def test_output_contains_skill_list_with_levels():
    output = format_character(_make_character())
    assert "Engineering" in output
    assert "2" in output
    assert "Gunnery" in output
    assert "1" in output


def test_output_contains_benefits_section():
    output = format_character(_make_character())
    # cash amounts in Cr format
    assert "Cr50,000" in output or "50000" in output
    # material names
    assert "High Passage" in output
    assert "Explorer's Society" in output


def test_pension_line_present_when_not_none():
    output = format_character(_make_character(pension=14000))
    assert "14,000" in output or "14000" in output
    assert "pension" in output.lower() or "Pension" in output


def test_no_pension_line_when_none():
    output = format_character(_make_character(pension=None))
    assert "Pension" not in output
    assert "pension" not in output


def test_format_character_returns_string():
    result = format_character(_make_character())
    assert isinstance(result, str)
    assert len(result) > 0


def test_characteristics_printed_in_upp_order() -> None:
    output = format_character(_make_character())
    stat_names = (
        "Strength",
        "Dexterity",
        "Endurance",
        "Intelligence",
        "Education",
        "Social Standing",
    )
    stat_lines = [ln.strip() for ln in output.splitlines() if any(n in ln for n in stat_names)]
    names_found = [ln.split(":")[0] for ln in stat_lines]
    assert names_found == list(stat_names)
