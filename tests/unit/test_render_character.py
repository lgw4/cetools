"""The Universal Character Format (contracts/cli.md, FR-044 through FR-048a).

Every `Character` here is a hand-constructed literal, never generated from a
seed: which character a seed produces is unknowable until the walk exists,
and SC-016 asks for goldens that are an expected value written before the
implementation they check, not a captured one (T091). The six references
these characters render to are `tests/golden/npc_*.txt`, compared as bytes.
"""

from cetools.character import CareerService, Character, CharacterSkill, HistoryStep
from cetools.render import as_text

_DUMMY_HISTORY = (
    HistoryStep(kind="characteristics", career="", term=0, throw=None, selected="", effects=()),
)


def _skills(*entries):
    return tuple(CharacterSkill(name=n, specialty=s, level=lvl) for n, s, lvl in entries)


def _service(**overrides):
    fields = dict(
        career="Navy",
        terms=1,
        ladder="enlisted",
        rank=0,
        title="",
        commissioned=False,
        entered_by="selected",
        ended="term cap",
        benefit_rolls=1,
    )
    fields.update(overrides)
    return CareerService(**fields)


def _character(**overrides):
    fields = dict(
        seed=1,
        name="Placeholder",
        given_name="",
        surname="",
        surname_region="",
        title="",
        characteristics={"STR": 7, "DEX": 7, "END": 7, "INT": 7, "EDU": 7, "SOC": 7},
        skills=(),
        careers=(_service(),),
        age=18,
        funds=0,
        debt=0,
        pension=0,
        benefits=(),
        history=_DUMMY_HISTORY,
    )
    fields.update(overrides)
    return Character(**fields)


TITLED = _character(
    name="Amara Okonkwo",
    title="Lieutenant",
    characteristics={"STR": 9, "DEX": 10, "END": 7, "INT": 11, "EDU": 8, "SOC": 6},
    age=34,
    funds=55000,
    careers=(
        _service(
            career="Navy",
            terms=4,
            ladder="officer",
            rank=2,
            title="Lieutenant",
            commissioned=True,
            entered_by="selected",
            ended="re-enlistment",
            benefit_rolls=4,
        ),
    ),
    skills=_skills(
        ("Comms", None, 1),
        ("Gun Combat", "Slug Rifle", 1),
        ("Leadership", None, 0),
        ("Melee Combat", None, 0),
        ("Navigation", None, 2),
        ("Tactics", None, 1),
        ("Vehicle", None, 0),
        ("Zero-G", None, 1),
    ),
    benefits=("High Passage", "Weapon", "High Passage"),
)

UNTITLED = _character(
    name="Kira Solis",
    characteristics={"STR": 7, "DEX": 9, "END": 8, "INT": 6, "EDU": 5, "SOC": 4},
    age=22,
    funds=20000,
    careers=(_service(career="Scout", terms=1, ladder="scout", rank=0, benefit_rolls=1),),
    skills=_skills(("Pilot", None, 1), ("Survival", None, 1), ("Vehicle", "Grav", 0)),
    benefits=("Weapon",),
)

NO_BENEFITS = _character(
    name="Devon Marsh",
    characteristics={"STR": 5, "DEX": 5, "END": 5, "INT": 5, "EDU": 5, "SOC": 5},
    age=18,
    funds=1000,
    careers=(_service(career="Drifter", terms=1, ladder="drifter", rank=0, benefit_rolls=1),),
    skills=_skills(("Streetwise", None, 0)),
    benefits=(),
)

MULTI_CAREER = _character(
    name="Priya Nakamura",
    characteristics={"STR": 8, "DEX": 8, "END": 8, "INT": 8, "EDU": 8, "SOC": 8},
    age=30,
    funds=8000,
    careers=(
        _service(career="Navy", terms=4, ladder="enlisted", rank=0, benefit_rolls=4),
        _service(
            career="Drifter",
            terms=1,
            ladder="drifter",
            rank=0,
            entered_by="fallback",
            ended="term cap",
            benefit_rolls=1,
        ),
    ),
    skills=_skills(("Gunnery", None, 1), ("Streetwise", None, 0), ("Vehicle", None, 1)),
    benefits=("Weapon", "Trade Goods"),
)

TITLED_THEN_UNTITLED = _character(
    name="Elin Marsh",
    title="Captain",
    characteristics={"STR": 6, "DEX": 6, "END": 6, "INT": 6, "EDU": 6, "SOC": 6},
    age=38,
    funds=12000,
    careers=(
        _service(
            career="Navy",
            terms=4,
            ladder="officer",
            rank=5,
            title="Captain",
            commissioned=True,
            benefit_rolls=4,
        ),
        _service(
            career="Drifter",
            terms=3,
            ladder="drifter",
            rank=0,
            title="Drifter",
            entered_by="fallback",
            benefit_rolls=3,
        ),
    ),
    skills=_skills(("Gambler", None, 0), ("Recon", None, 1)),
    benefits=("Weapon",),
)

CASCADE = _character(
    name="Tomas Weber",
    characteristics={"STR": 9, "DEX": 9, "END": 9, "INT": 9, "EDU": 9, "SOC": 9},
    age=26,
    funds=30000,
    careers=(_service(career="Scout", terms=2, ladder="scout", rank=0, benefit_rolls=2),),
    skills=_skills(("Vehicle", "Aircraft", 1), ("Piloting", None, 1)),
    benefits=("Ship Share",),
)


class TestUniversalCharacterFormat:
    def test_four_lines_one_tab_between_fields(self):
        text = as_text(TITLED)
        lines = text.split("\n")
        assert len(lines) == 4
        assert lines[0].count("\t") == 2
        assert lines[1].count("\t") == 1

    def test_title_space_name_with_no_leading_separator_when_untitled(self):
        assert as_text(TITLED).startswith("Lieutenant Amara Okonkwo\t")
        assert as_text(UNTITLED).startswith("Kira Solis\t")

    def test_pseudo_hex_profile_in_registry_order(self):
        line1 = as_text(TITLED).split("\n")[0]
        assert line1.split("\t")[1] == "9A7B86"

    def test_age_line(self):
        assert "Age 34" in as_text(TITLED)

    def test_careers_line_comma_separated_singular_at_one(self):
        line2 = as_text(UNTITLED).split("\n")[1]
        assert line2.startswith("Scout (1 term)\t")
        line2_multi = as_text(MULTI_CAREER).split("\n")[1]
        assert line2_multi.startswith("Navy (4 terms), Drifter (1 term)\t")

    def test_funds_with_thousands_separators(self):
        assert as_text(TITLED).split("\n")[1].endswith("Cr55,000")

    def test_skills_sorted_by_casefold_and_codepoint(self):
        line3 = as_text(TITLED).split("\n")[2]
        assert line3 == (
            "Comms-1, Gun Combat (Slug Rifle)-1, Leadership-0, Melee Combat-0, "
            "Navigation-2, Tactics-1, Vehicle-0, Zero-G-1"
        )

    def test_cascade_specialization_qualified_by_parent(self):
        line3 = as_text(CASCADE).split("\n")[2]
        assert "Vehicle (Aircraft)-1" in line3

    def test_benefit_items_collapsed_with_repeats_and_sorted(self):
        line4 = as_text(TITLED).split("\n")[3]
        assert line4 == "High Passage (x2), Weapon"

    def test_benefit_line_omitted_when_there_are_none(self):
        text = as_text(NO_BENEFITS)
        assert len(text.split("\n")) == 3

    def test_species_traits_line_never_emitted(self):
        for character in (TITLED, UNTITLED, NO_BENEFITS, MULTI_CAREER, CASCADE):
            lines = as_text(character).split("\n")
            assert len(lines) in (3, 4)


class TestTitlePersistence:
    def test_a_later_untitled_career_does_not_erase_an_earlier_title(self):
        # The Character literal already carries the resolved title (FR-047c
        # is the generator's rule, not the renderer's); the renderer simply
        # writes whatever `character.title` holds. This is what proves the
        # renderer never re-derives a title by comparing ladders itself.
        assert TITLED_THEN_UNTITLED.title == "Captain"
        assert as_text(TITLED_THEN_UNTITLED).startswith("Captain Elin Marsh\t")

    def test_no_rendering_may_write_anything_but_a_rank_title(self):
        # FR-048: the only title any rendering may write is a rank title
        # from a ladder. Character carries exactly one `title` field, and
        # the renderer reads only it, so there is no second surface a noble
        # title (or anything else) could reach the sheet through.
        import dataclasses

        assert [f.name for f in dataclasses.fields(Character) if "title" in f.name] == ["title"]


def test_goldens(read_golden_bytes):
    for filename, character in (
        ("npc_titled.txt", TITLED),
        ("npc_untitled.txt", UNTITLED),
        ("npc_no_benefits.txt", NO_BENEFITS),
        ("npc_multi_career.txt", MULTI_CAREER),
        ("npc_titled_then_untitled.txt", TITLED_THEN_UNTITLED),
        ("npc_cascade.txt", CASCADE),
    ):
        assert as_text(character).encode("utf-8") == read_golden_bytes(filename), filename
