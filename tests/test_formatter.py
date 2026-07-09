from cetools.engine.models import Benefit, Character, MishapOutcome
from cetools.formatter import format_character


def _base_characteristics() -> dict[str, int]:
    return {
        "Strength": 7,
        "Dexterity": 10,
        "Endurance": 6,
        "Intelligence": 11,
        "Education": 8,
        "Social Standing": 5,
    }


def _make_full_character(mishap: MishapOutcome | None = None, debt: int = 0) -> Character:
    """Matches contracts/ucf-output.md's "fully-populated character" example."""
    return Character(
        characteristics=_base_characteristics(),
        upp="7A6B85",
        age=46,
        career="Navy",
        rank=6,
        rank_title="Commodore",
        terms_served=7,
        name="Bruce Ayala",
        skills={"Engineering": 2, "Gunnery": 1, "Navigation": 2, "Tactics": 1, "Zero-G": 1},
        benefits=[
            Benefit(kind="cash", cash_amount=50000),
            Benefit(kind="cash", cash_amount=20000),
            Benefit(kind="cash", cash_amount=10000),
            Benefit(kind="material", material_name="High Passage"),
            Benefit(kind="material", material_name="Explorers' Society"),
        ],
        pension=14000,
        terms=[],
        drafted=False,
        mishap=mishap,
        debt=debt,
    )


def _make_empty_character(mishap: MishapOutcome | None = None, debt: int = 0) -> Character:
    """Matches contracts/ucf-output.md's zero-cash/zero-material/zero-skills example."""
    return Character(
        characteristics=_base_characteristics(),
        upp="5A5555",
        age=22,
        career="Navy",
        rank=0,
        rank_title="Starman",
        terms_served=1,
        name="Alex Kade",
        skills={},
        benefits=[],
        pension=None,
        terms=[],
        drafted=True,
        mishap=mishap,
        debt=debt,
    )


def test_full_character_matches_contract_example() -> None:
    output = format_character(_make_full_character())
    assert output == (
        "Commodore Bruce Ayala\t7A6B85\tAge 46\n"
        "Navy (7 terms)\tCr80,000\n"
        "Engineering-2, Gunnery-1, Navigation-2, Tactics-1, Zero-G-1\n"
        "High Passage, Explorers' Society"
    )


def test_empty_character_matches_contract_example() -> None:
    output = format_character(_make_empty_character())
    assert output == ("Starman Alex Kade\t5A5555\tAge 22\n" "Navy (1 terms)\tCr0\n")


def test_line1_includes_rank_title_with_trailing_space() -> None:
    output = format_character(_make_full_character())
    line1 = output.split("\n")[0]
    assert line1 == "Commodore Bruce Ayala\t7A6B85\tAge 46"


def test_line1_omits_rank_title_when_empty() -> None:
    character = _make_full_character()
    character.rank_title = ""
    output = format_character(character)
    line1 = output.split("\n")[0]
    assert line1 == "Bruce Ayala\t7A6B85\tAge 46"


def test_line2_format() -> None:
    output = format_character(_make_full_character())
    line2 = output.split("\n")[1]
    assert line2 == "Navy (7 terms)\tCr80,000"


def test_funds_zero_when_no_cash_benefits() -> None:
    output = format_character(_make_empty_character())
    line2 = output.split("\n")[1]
    assert line2 == "Navy (1 terms)\tCr0"


def test_skill_line_sorted_alphabetically() -> None:
    character = _make_full_character()
    character.skills = {"Zero-G": 1, "Gunnery": 2}
    output = format_character(character)
    line3 = output.split("\n")[2]
    assert line3 == "Gunnery-2, Zero-G-1"


def test_skill_line_present_but_empty_when_no_skills() -> None:
    output = format_character(_make_empty_character())
    lines = output.split("\n")
    assert len(lines) == 3
    assert lines[2] == ""


def test_equipment_line_present_only_when_material_benefits_exist() -> None:
    output = format_character(_make_full_character())
    lines = output.split("\n")
    assert len(lines) == 4
    assert lines[3] == "High Passage, Explorers' Society"


def test_equipment_line_omitted_entirely_when_no_material_benefits() -> None:
    character = _make_full_character()
    character.benefits = [b for b in character.benefits if b.kind != "material"]
    output = format_character(character)
    lines = output.split("\n")
    assert len(lines) == 3


def test_no_blank_separator_lines() -> None:
    output = format_character(_make_full_character())
    assert "\n\n" not in output


def test_output_never_more_than_4_lines_without_mishap() -> None:
    for character in (_make_full_character(), _make_empty_character()):
        output = format_character(character)
        assert len(output.split("\n")) <= 4


def test_output_gains_one_line_when_mishap_present() -> None:
    mishap = MishapOutcome(
        roll=2,
        discharge_type="honorable",
        imprisoned=False,
        injury_reductions={},
        injury_crisis=False,
    )
    full_output = format_character(_make_full_character(mishap=mishap))
    assert len(full_output.split("\n")) == 5

    empty_output = format_character(_make_empty_character(mishap=mishap))
    assert len(empty_output.split("\n")) == 4


def test_no_legacy_section_headers_or_drafted_label() -> None:
    for character in (_make_full_character(), _make_empty_character()):
        output = format_character(character)
        assert "UPP:" not in output
        assert "Characteristics:" not in output
        assert "Mustering-Out Benefits:" not in output
        assert "Retirement Pension:" not in output
        assert "(Drafted)" not in output


def test_format_character_returns_string() -> None:
    result = format_character(_make_full_character())
    assert isinstance(result, str)
    assert len(result) > 0


# --- User Story 3: funds and equipment at a glance ---


def test_us3_multiple_cash_benefits_sum_to_single_total() -> None:
    """Acceptance scenario 1: several cash benefits combine into one Cr<amount> total."""
    character = _make_empty_character()
    character.benefits = [
        Benefit(kind="cash", cash_amount=50000),
        Benefit(kind="cash", cash_amount=20000),
        Benefit(kind="cash", cash_amount=10000),
    ]
    output = format_character(character)
    line2 = output.split("\n")[1]
    assert line2 == "Navy (1 terms)\tCr80,000"


def test_us3_zero_cash_benefits_shows_cr0_not_omitted() -> None:
    """Acceptance scenario 2: no cash benefits renders "Cr0" rather than dropping the figure."""
    character = _make_full_character()
    character.benefits = [b for b in character.benefits if b.kind != "cash"]
    output = format_character(character)
    line2 = output.split("\n")[1]
    assert line2 == "Navy (7 terms)\tCr0"


def test_us3_material_benefits_listed_by_name_in_order() -> None:
    """Acceptance scenario 3: each material benefit is named, comma-separated, in list order."""
    character = _make_empty_character()
    character.benefits = [
        Benefit(kind="material", material_name="Weapon"),
        Benefit(kind="material", material_name="Travellers' Aid Society"),
        Benefit(kind="material", material_name="Ship Share"),
    ]
    output = format_character(character)
    lines = output.split("\n")
    assert lines[-1] == "Weapon, Travellers' Aid Society, Ship Share"


def test_material_benefits_sum_boosts_and_group_items() -> None:
    """Stat boosts are summed and listed first; material items keep singles-then-
    repeats ordering, each group ordered by first occurrence."""
    character = _make_empty_character()
    character.benefits = [
        Benefit(kind="material", material_name="Weapon"),
        Benefit(kind="material", material_name="+1 Edu"),
        Benefit(kind="material", material_name="High Passage"),
        Benefit(kind="material", material_name="Weapon"),
        Benefit(kind="material", material_name="+1 Soc"),
        Benefit(kind="material", material_name="Weapon"),
    ]
    output = format_character(character)
    lines = output.split("\n")
    assert lines[-1] == "+1 Edu, +1 Soc, High Passage, Weapon (x3)"


def test_repeated_stat_boost_sums_into_single_entry() -> None:
    """Two "+1 Soc" rolls render as "+2 Soc", not "+1 Soc x 2"."""
    character = _make_empty_character()
    character.benefits = [
        Benefit(kind="material", material_name="+1 Soc"),
        Benefit(kind="material", material_name="+1 Soc"),
    ]
    output = format_character(character)
    assert output.split("\n")[-1] == "+2 Soc"


def test_single_stat_boost_renders_as_plus_one() -> None:
    """A stat boost rolled once stays "+1 Edu" (no "x 1")."""
    character = _make_empty_character()
    character.benefits = [Benefit(kind="material", material_name="+1 Edu")]
    output = format_character(character)
    assert output.split("\n")[-1] == "+1 Edu"


def test_triple_stat_boost_sums_to_plus_three() -> None:
    character = _make_empty_character()
    character.benefits = [
        Benefit(kind="material", material_name="+1 Str"),
        Benefit(kind="material", material_name="+1 Str"),
        Benefit(kind="material", material_name="+1 Str"),
    ]
    output = format_character(character)
    assert output.split("\n")[-1] == "+3 Str"


def test_boosts_and_items_full_example() -> None:
    """Reproduces the reported bug: "+1 Edu, +1 Soc x 2, Mid Passage, Weapon x 2"
    must render with Soc summed and boosts first."""
    character = _make_empty_character()
    character.benefits = [
        Benefit(kind="material", material_name="+1 Edu"),
        Benefit(kind="material", material_name="Mid Passage"),
        Benefit(kind="material", material_name="+1 Soc"),
        Benefit(kind="material", material_name="+1 Soc"),
        Benefit(kind="material", material_name="Weapon"),
        Benefit(kind="material", material_name="Weapon"),
    ]
    output = format_character(character)
    assert output.split("\n")[-1] == "+1 Edu, +2 Soc, Mid Passage, Weapon (x2)"


def test_material_benefits_multiple_repeated_names_ordered_by_first_occurrence() -> None:
    character = _make_empty_character()
    character.benefits = [
        Benefit(kind="material", material_name="High Passage"),
        Benefit(kind="material", material_name="Weapon"),
        Benefit(kind="material", material_name="High Passage"),
        Benefit(kind="material", material_name="Weapon"),
    ]
    output = format_character(character)
    lines = output.split("\n")
    assert lines[-1] == "High Passage (x2), Weapon (x2)"


# --- User Story 2: understand why a career ended early (Mishap line) ---


def test_no_mishap_line_when_mishap_is_none() -> None:
    output = format_character(_make_full_character())
    assert "Mishap:" not in output
    assert len(output.split("\n")) == 4


def test_mishap_line_honorable_discharge_no_debt_no_injury() -> None:
    mishap = MishapOutcome(
        roll=2,
        discharge_type="honorable",
        imprisoned=False,
        injury_reductions={},
        injury_crisis=False,
    )
    output = format_character(_make_empty_character(mishap=mishap))
    assert output.split("\n")[-1] == "Mishap: Honorably discharged"


def test_mishap_line_honorable_discharge_with_debt() -> None:
    mishap = MishapOutcome(
        roll=3,
        discharge_type="honorable",
        imprisoned=False,
        injury_reductions={},
        injury_crisis=False,
    )
    output = format_character(_make_empty_character(mishap=mishap, debt=10_000))
    assert output.split("\n")[-1] == "Mishap: Honorably discharged; Debt Cr10,000"


def test_mishap_line_dishonorable_discharge_not_imprisoned() -> None:
    mishap = MishapOutcome(
        roll=4,
        discharge_type="dishonorable",
        imprisoned=False,
        injury_reductions={},
        injury_crisis=False,
    )
    output = format_character(_make_empty_character(mishap=mishap))
    assert output.split("\n")[-1] == "Mishap: Dishonorably discharged"


def test_mishap_line_dishonorable_discharge_imprisoned() -> None:
    mishap = MishapOutcome(
        roll=5,
        discharge_type="dishonorable",
        imprisoned=True,
        injury_reductions={},
        injury_crisis=False,
    )
    output = format_character(_make_empty_character(mishap=mishap))
    assert output.split("\n")[-1] == "Mishap: Dishonorably discharged (imprisoned)"


def test_mishap_line_medical_discharge() -> None:
    mishap = MishapOutcome(
        roll=6,
        discharge_type="medical",
        imprisoned=False,
        injury_reductions={},
        injury_crisis=False,
    )
    output = format_character(_make_empty_character(mishap=mishap))
    assert output.split("\n")[-1] == "Mishap: Medically discharged"


def test_mishap_line_injured_in_action() -> None:
    mishap = MishapOutcome(
        roll=1,
        discharge_type="none",
        imprisoned=False,
        injury_reductions={},
        injury_crisis=False,
    )
    output = format_character(_make_empty_character(mishap=mishap))
    assert output.split("\n")[-1] == "Mishap: Injured in action"


def test_mishap_line_injury_clause_sorted_alphabetically() -> None:
    mishap = MishapOutcome(
        roll=1,
        discharge_type="none",
        imprisoned=False,
        injury_reductions={"Strength": 1, "Endurance": 2},
        injury_crisis=False,
    )
    output = format_character(_make_empty_character(mishap=mishap))
    assert output.split("\n")[-1] == (
        "Mishap: Injured in action, injured (Endurance -2, Strength -1)"
    )


def test_mishap_line_crisis_clause_after_injury_clause() -> None:
    mishap = MishapOutcome(
        roll=1,
        discharge_type="none",
        imprisoned=False,
        injury_reductions={"Strength": 3},
        injury_crisis=True,
    )
    output = format_character(_make_empty_character(mishap=mishap))
    assert output.split("\n")[-1] == (
        "Mishap: Injured in action, injured (Strength -3), survived an injury crisis"
    )


def test_mishap_line_contract_example_dishonorable_imprisoned_no_injury() -> None:
    mishap = MishapOutcome(
        roll=5,
        discharge_type="dishonorable",
        imprisoned=True,
        injury_reductions={},
        injury_crisis=False,
    )
    output = format_character(_make_empty_character(mishap=mishap))
    assert output.split("\n")[-1] == "Mishap: Dishonorably discharged (imprisoned)"


def test_mishap_line_contract_example_honorable_with_debt() -> None:
    mishap = MishapOutcome(
        roll=3,
        discharge_type="honorable",
        imprisoned=False,
        injury_reductions={},
        injury_crisis=False,
    )
    output = format_character(_make_empty_character(mishap=mishap, debt=10_000))
    assert output.split("\n")[-1] == "Mishap: Honorably discharged; Debt Cr10,000"


def test_mishap_line_contract_example_injured_no_crisis() -> None:
    mishap = MishapOutcome(
        roll=1,
        discharge_type="none",
        imprisoned=False,
        injury_reductions={"Strength": 3},
        injury_crisis=False,
    )
    output = format_character(_make_empty_character(mishap=mishap))
    assert output.split("\n")[-1] == "Mishap: Injured in action, injured (Strength -3)"


def test_mishap_line_contract_example_medical_injury_crisis_debt() -> None:
    mishap = MishapOutcome(
        roll=6,
        discharge_type="medical",
        imprisoned=False,
        injury_reductions={"Dexterity": 6},
        injury_crisis=True,
    )
    output = format_character(_make_empty_character(mishap=mishap, debt=40_000))
    assert output.split("\n")[-1] == (
        "Mishap: Medically discharged, injured (Dexterity -6), "
        "survived an injury crisis; Debt Cr40,000"
    )


def test_ship_shares_quantities_summed() -> None:
    from cetools.formatter import _combine_material_benefits

    benefits = [
        Benefit(kind="material", material_name="Ship Shares", material_quantity=3),
        Benefit(kind="material", material_name="Ship Shares", material_quantity=4),
    ]
    assert _combine_material_benefits(benefits) == ["7 Ship Shares"]


def test_single_ship_share_renders_without_pluralization() -> None:
    from cetools.formatter import _combine_material_benefits

    benefits = [Benefit(kind="material", material_name="Ship Shares", material_quantity=1)]
    assert _combine_material_benefits(benefits) == ["1 Ship Shares"]


def test_ship_shares_coexist_with_boosts_and_items() -> None:
    from cetools.formatter import _combine_material_benefits

    benefits = [
        Benefit(kind="material", material_name="+1 Edu"),
        Benefit(kind="material", material_name="High Passage"),
        Benefit(kind="material", material_name="Ship Shares", material_quantity=2),
    ]
    assert _combine_material_benefits(benefits) == [
        "+1 Edu",
        "High Passage",
        "2 Ship Shares",
    ]


def test_psionic_character_renders_upp_suffix_and_psionics_line() -> None:
    char = _make_full_character()
    char.psi_strength = 6
    char.talents = {"Telepathy": 0, "Awareness": 0}
    lines = format_character(char).split("\n")
    # UPP token on line 0 carries the pseudo-hex suffix.
    assert f"{char.upp}-6" in lines[0]
    # Psionics line is alphabetical and sits immediately after the skills line.
    assert "Psionics: Awareness-0, Telepathy-0" in lines
    skills_index = 2
    assert lines[skills_index + 1] == "Psionics: Awareness-0, Telepathy-0"


def test_non_psionic_character_has_bare_upp_and_no_psionics_line() -> None:
    char = _make_empty_character()  # psi_strength defaults to 0, talents to {}
    output = format_character(char)
    assert f"\t{char.upp}\t" in output  # bare UPP, no hyphen suffix
    assert "Psionics:" not in output


def test_high_psi_renders_pseudohex_suffix() -> None:
    char = _make_full_character()
    char.psi_strength = 10
    char.talents = {"Telepathy": 0}
    assert f"{char.upp}-A" in format_character(char)
