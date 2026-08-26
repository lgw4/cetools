"""The Universal Character Format (contracts/cli.md, FR-044 through FR-048a).

Every `Character` here is a hand-constructed literal, never generated from a
seed: which character a seed produces is unknowable until the walk exists,
and SC-016 asks for goldens that are an expected value written before the
implementation they check, not a captured one (T091). The six references
these characters render to are `tests/golden/npc_*.txt`, compared as bytes.
"""

import dataclasses

from cetools.character import (
    CareerService,
    Character,
    CharacterBatch,
    CharacterSkill,
    HistoryStep,
    StepEffect,
    StepThrow,
)
from cetools.provenance import Provenance
from cetools.render import as_text
from cetools.rules import load_rules
from cetools.tasks import Modifier

_PACKAGED_CHARACTERISTICS = load_rules().characteristics

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
    fields.setdefault(
        "characteristic_symbols",
        tuple(_PACKAGED_CHARACTERISTICS.symbol(v) for v in fields["characteristics"].values()),
    )
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
    skills=_skills(("Piloting", None, 1), ("Survival", None, 1), ("Aircraft", "Grav Vehicle", 0)),
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
    benefits=("Weapon", "Mid Passage"),
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
            # Untitled, not "Drifter" (T171): a later career that *does*
            # name a title for the rank held would supply it, so a service
            # carrying one here is not the "left them untitled" shape
            # SC-009 asks this reference to cover at all.
            title="",
            entered_by="fallback",
            benefit_rolls=3,
        ),
    ),
    skills=_skills(("Gambling", None, 0), ("Recon", None, 1)),
    benefits=("Weapon",),
)

CASCADE = _character(
    name="Tomas Weber",
    characteristics={"STR": 9, "DEX": 9, "END": 9, "INT": 9, "EDU": 9, "SOC": 9},
    age=26,
    funds=30000,
    careers=(_service(career="Scout", terms=2, ladder="scout", rank=0, benefit_rolls=2),),
    skills=_skills(("Aircraft", "Winged Aircraft", 1), ("Piloting", None, 1)),
    benefits=("Ship Share",),
)


_FULL_HISTORY = (
    HistoryStep(
        kind="characteristics",
        career="",
        term=0,
        throw=None,
        selected="",
        effects=(
            StepEffect(kind="characteristic", subject="STR", amount=8),
            StepEffect(kind="characteristic", subject="DEX", amount=7),
            StepEffect(kind="characteristic", subject="END", amount=9),
            StepEffect(kind="characteristic", subject="INT", amount=6),
            StepEffect(kind="characteristic", subject="EDU", amount=5),
            StepEffect(kind="characteristic", subject="SOC", amount=4),
        ),
    ),
    HistoryStep(
        kind="qualification",
        career="Navy",
        term=1,
        throw=StepThrow(
            faces=(2, 5),
            modifiers=(Modifier(label="Characteristic 6", value=1),),
            total=8,
            target=6,
            success=True,
        ),
        selected="",
        effects=(),
    ),
    HistoryStep(
        kind="career-entered", career="Navy", term=1, throw=None, selected="selected", effects=()
    ),
    HistoryStep(
        kind="mishap",
        career="Navy",
        term=2,
        throw=StepThrow(faces=(3, 2), modifiers=(), total=5, target=0, success=True),
        selected="Injury",
        effects=(),
    ),
    HistoryStep(
        kind="mishap",
        career="Navy",
        term=2,
        throw=None,
        selected="",
        effects=(StepEffect(kind="debt", subject="", amount=1200),),
    ),
    HistoryStep(
        kind="pension",
        career="Navy",
        term=0,
        throw=None,
        selected="",
        effects=(StepEffect(kind="pension", subject="", amount=10000),),
    ),
)

FULL = _character(
    name="Jonah Vance",
    title="Sergeant",
    characteristics={"STR": 8, "DEX": 7, "END": 9, "INT": 6, "EDU": 5, "SOC": 4},
    age=26,
    funds=4000,
    debt=1200,
    pension=10000,
    careers=(
        _service(
            career="Navy",
            terms=2,
            ladder="enlisted",
            rank=0,
            title="",
            commissioned=False,
            entered_by="selected",
            ended="term cap",
            benefit_rolls=2,
        ),
    ),
    skills=_skills(("Gunnery", None, 1)),
    benefits=("Weapon",),
    history=_FULL_HISTORY,
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

    def test_skills_sorted_by_label_not_by_label_and_level(self):
        # `"Gun Combat"` is a prefix of `"Gun Combat (Slug Rifle)"`, so the
        # shorter label sorts first (contracts/cli.md: sorted "over the
        # rendered name-and-specialty"). Appending "-{level}" before sorting
        # would compare "gun combat (slug rifle)-0" against "gun combat-1"
        # instead, where the space in "(Slug..." (0x20) sorts before the
        # hyphen in "-1" (0x2D) and reverses the order (T154).
        character = _character(
            skills=_skills(
                ("Gun Combat", None, 1),
                ("Gun Combat", "Slug Rifle", 0),
            ),
        )
        line3 = as_text(character).split("\n")[2]
        assert line3 == "Gun Combat-1, Gun Combat (Slug Rifle)-0"

    def test_cascade_specialization_qualified_by_parent(self):
        line3 = as_text(CASCADE).split("\n")[2]
        assert "Aircraft (Winged Aircraft)-1" in line3

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

    def test_a_top_level_skill_and_its_own_name_as_a_specialty_render_distinctly(self):
        # FR-016a, D6, research R8: the skill book keys on (name, specialty),
        # so `Survival` and `Animals (Survival)` are different keys and
        # neither merges into nor aliases the other. The background-skills
        # education list grants all four `Sciences` specialties bare, so the
        # `Life Sciences` / `Sciences (Life Sciences)` pair is the case every
        # character can actually draw, not an override-only curiosity.
        character = _character(
            skills=_skills(
                ("Survival", None, 1),
                ("Animals", "Survival", 0),
                ("Life Sciences", None, 0),
                ("Sciences", "Life Sciences", 1),
            )
        )
        line3 = as_text(character).split("\n")[2]
        assert "Survival-1" in line3
        assert "Animals (Survival)-0" in line3
        assert "Life Sciences-0" in line3
        assert "Sciences (Life Sciences)-1" in line3
        assert line3.count("Survival") == 2
        assert line3.count("Sciences (Life Sciences)") == 1

    def test_profile_renders_the_characters_own_symbols_not_the_packaged_ones(self):
        # T159: `as_text`'s signature carries no rules parameter
        # (contracts/library-api.md), so the only seam that lets an
        # overridden pseudo-hex table reach the render is the character
        # itself. A character carrying symbols that disagree with the
        # packaged table must still render exactly what it carries.
        character = _character(
            characteristics={"STR": 9, "DEX": 10, "END": 7, "INT": 11, "EDU": 8, "SOC": 6},
            characteristic_symbols=("!", "!", "!", "!", "!", "!"),
        )
        line1 = as_text(character).split("\n")[0]
        assert line1.split("\t")[1] == "!!!!!!"


class TestTitlePersistence:
    def test_a_later_untitled_career_does_not_erase_an_earlier_title(self):
        # The Character literal already carries the resolved title (FR-047c
        # is the generator's rule, not the renderer's); the renderer simply
        # writes whatever `character.title` holds. This is what proves the
        # renderer never re-derives a title by comparing ladders itself.
        assert TITLED_THEN_UNTITLED.title == "Captain"
        assert as_text(TITLED_THEN_UNTITLED).startswith("Captain Elin Marsh\t")

    def test_the_fixture_actually_represents_a_later_career_left_untitled(self):
        # The scenario this golden claims to cover, restated as a check on
        # the fixture itself: its second `CareerService` must carry no
        # title, or nothing here proves an earlier title survives rather
        # than merely getting overwritten by an identical later one (T171).
        assert TITLED_THEN_UNTITLED.careers[1].title == ""

    def test_no_shipped_ladder_rank_leaves_a_character_untitled(self):
        # FR-047c's "an earlier title survives" branch
        # (`generator.py`'s `if title: self.title = title`) is asserted
        # only against TITLED_THEN_UNTITLED's hand-built literal, because
        # every rank of every shipped ladder declares a title: ordinary
        # generation can never reach it. An override could supply what the
        # shipped data cannot, which is why the branch — and this golden —
        # still earn their place (T171).
        rules = load_rules()
        for career in rules.careers.values():
            for ladder in career.ladders:
                for rank_row in ladder.ranks:
                    assert rank_row.title, (
                        f"{career.name}'s {ladder.name!r} ladder rank {rank_row.rank} "
                        "declares no title"
                    )

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


class TestFullerSheet:
    """`--full` (contracts/cli.md FR-049): the Universal Character Format,
    a blank line, then what the format has nowhere to put.
    """

    def test_starts_with_the_universal_character_format_then_a_blank_line(self):
        text = as_text(FULL, full=True)
        base_lines = as_text(FULL).split("\n")
        full_lines = text.split("\n")
        assert full_lines[: len(base_lines)] == base_lines
        assert full_lines[len(base_lines)] == ""

    def test_debt_and_pension_both_carry_the_currency_prefix_and_thousands_separator(self):
        text = as_text(FULL, full=True)
        assert "  Debt:    Cr1,200" in text
        assert "  Pension: Cr10,000" in text

    def test_a_zero_pension_reads_none_rather_than_cr0(self):
        character = _character(pension=0)
        text = as_text(character, full=True)
        assert "  Pension: none" in text

    def test_history_heading_and_one_line_per_step(self):
        text = as_text(FULL, full=True)
        assert "  History:" in text
        lines = text.split("\n")
        heading = lines.index("  History:")
        history_lines = lines[heading + 1 :]
        assert len(history_lines) == len(FULL.history)

    def test_each_history_line_is_composed_from_the_steps_named_parts(self):
        lines = as_text(FULL, full=True).split("\n")
        heading = lines.index("  History:")
        history_lines = lines[heading + 1 :]
        # "qualification": a throw with an itemized modifier, a total that
        # differs from the raw dice sum, and a target and outcome.
        qualification = next(line for line in history_lines if "qualification" in line)
        assert "2, 5 (sum 7)" in qualification
        assert "Characteristic 6 +1" in qualification
        assert "= 8 vs 6  SUCCESS" in qualification
        # "career-entered": selected only, no throw and no effects.
        entered = next(line for line in history_lines if "career-entered" in line)
        assert entered.endswith("selected")
        # A mishap effect carries the debt amount, composed from its kind,
        # subject, and amount rather than a stored line.
        debt_line = next(line for line in history_lines if "Cr1,200 debt" in line)
        assert debt_line

    def test_columns_padded_to_the_longest_value_present(self):
        lines = as_text(FULL, full=True).split("\n")
        heading = lines.index("  History:")
        history_lines = lines[heading + 1 :]
        kind_width = max(len(step.kind) for step in FULL.history)
        for line in history_lines:
            # Every kind column starts at the same offset, so the character
            # immediately after it — whatever comes next — lines up too.
            assert line[4 : 4 + kind_width].rstrip() in {step.kind for step in FULL.history}

    def test_no_field_of_a_history_step_holds_a_line_composed_from_its_other_parts(self):
        # FR-030a is checkable from the record's shape: `HistoryStep` carries
        # only `kind`, `career`, `term`, `throw`, `selected`, and `effects` —
        # no field meant to hold prose composed elsewhere, unlike
        # `MishapRow.description`, which is a source-material label rather
        # than a rendering of a step.
        assert [f.name for f in dataclasses.fields(HistoryStep)] == [
            "kind",
            "career",
            "term",
            "throw",
            "selected",
            "effects",
        ]


def test_full_golden(read_golden_bytes):
    assert as_text(FULL, full=True).encode("utf-8") == read_golden_bytes("npc_full.txt")


BATCH = CharacterBatch(
    seed=1,
    provenance=Provenance(version="0.0.0", files=(), ignored=()),
    characters=(TITLED, UNTITLED, NO_BENEFITS),
)


def test_batch_golden(read_golden_bytes):
    """SC-011: consecutive sheets separated by exactly one blank line and
    nothing else, a derivation checkable without a captured expectation
    (T126).
    """
    assert as_text(BATCH).encode("utf-8") == read_golden_bytes("npc_batch.txt")
