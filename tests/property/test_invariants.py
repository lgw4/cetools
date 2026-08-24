import string

from hypothesis import given, settings
from hypothesis import strategies as st

from cetools.dice import Roller, d66, throw_dice
from cetools.generator import generate_character
from cetools.notation import (
    BenefitItem,
    CharacteristicAdjustment,
    CharacteristicCheck,
    EntryContext,
    SkillGrant,
    SkillReference,
    parse_entry,
)
from cetools.rules import load_rules
from cetools.tasks import Modifier, check

# Deliberately unbounded on both sides: 001-dice-task-engine FR-002 puts no
# upper bound on the magnitude of an integer seed and permits a negative sign,
# so a strategy clamped to `0..2**64-1` would never exercise either half of what
# the requirement allows.
seeds = st.one_of(
    st.integers(min_value=-(2**200), max_value=2**200), st.text(min_size=1, max_size=20)
)
counts = st.integers(min_value=1, max_value=20)
sides = st.integers(min_value=1, max_value=100)
modifiers = st.integers(min_value=-10, max_value=10)

_PARAMETERS = load_rules().task_parameters

difficulty_names = st.sampled_from(list(_PARAMETERS.difficulty_dms))
characteristics = st.none() | st.integers(min_value=0, max_value=50)
skills = st.none() | st.integers(min_value=0, max_value=10)
situational_modifiers = st.lists(
    st.builds(Modifier, label=st.text(min_size=1, max_size=10), value=st.integers(-5, 5)),
    max_size=3,
).map(tuple)


@given(seed=seeds, count=counts, sides_=sides, modifier=modifiers)
def test_throw_faces_are_within_range_and_correct_count(seed, count, sides_, modifier):
    result = throw_dice(Roller(seed), count, sides_, modifier)
    assert len(result.faces) == count
    assert all(1 <= face <= sides_ for face in result.faces)


@given(seed=seeds, count=counts, sides_=sides, modifier=modifiers)
def test_throw_total_equals_sum_of_faces_plus_modifier(seed, count, sides_, modifier):
    result = throw_dice(Roller(seed), count, sides_, modifier)
    assert result.total == sum(result.faces) + modifier


@given(seed=seeds, count=counts, sides_=sides, modifier=modifiers)
def test_same_seed_and_arguments_yield_equal_result(seed, count, sides_, modifier):
    first = throw_dice(Roller(seed), count, sides_, modifier)
    second = throw_dice(Roller(seed), count, sides_, modifier)
    assert first == second


@given(seed=seeds)
def test_d66_digits_are_within_range_and_total_is_composed(seed):
    result = d66(Roller(seed))
    assert len(result.faces) == 2
    assert all(1 <= face <= 6 for face in result.faces)
    assert result.total == result.faces[0] * 10 + result.faces[1]


@given(
    seed=seeds,
    difficulty=difficulty_names,
    characteristic=characteristics,
    skill=skills,
    situational=situational_modifiers,
)
def test_check_total_equals_dice_total_plus_sum_of_modifiers(
    seed, difficulty, characteristic, skill, situational
):
    result = check(
        Roller(seed),
        difficulty=difficulty,
        characteristic=characteristic,
        skill=skill,
        modifiers=situational,
    )
    assert result.total == result.dice_total + sum(m.value for m in result.modifiers)


@given(
    seed=seeds,
    difficulty=difficulty_names,
    characteristic=characteristics,
    skill=skills,
    situational=situational_modifiers,
)
def test_same_seed_and_arguments_yield_equal_check(
    seed, difficulty, characteristic, skill, situational
):
    # 001-dice-task-engine FR-006 binds programmatic invocation as well as
    # command invocation, and the throw side of that was already covered; this
    # is the check side.
    def resolve():
        return check(
            Roller(seed),
            difficulty=difficulty,
            characteristic=characteristic,
            skill=skill,
            modifiers=situational,
        )

    assert resolve() == resolve()


@given(
    seed=seeds,
    difficulty=difficulty_names,
    characteristic=characteristics,
    skill=skills,
    situational=situational_modifiers,
)
def test_check_success_equals_total_at_least_target(
    seed, difficulty, characteristic, skill, situational
):
    result = check(
        Roller(seed),
        difficulty=difficulty,
        characteristic=characteristic,
        skill=skill,
        modifiers=situational,
    )
    assert result.success == (result.total >= result.target)


# --- notation round trip (plan.md Testing, contracts/notation.md) ---
#
# `_words` excludes digits, signs, and parentheses so a generated name never
# collides with a suffix token or a specialty delimiter; contracts/notation.md
# reserves those to the grammar's suffix and specialty positions, not the name.
# A hyphen is admitted inside a word, for names like `Zero-G`, but a word that
# is nothing but a hyphen is excluded: as the trailing token it is the bare
# sign the grammar reports as malformed, not part of a name.
_words = st.text(alphabet=string.ascii_letters + "'-/", min_size=1, max_size=8).filter(
    lambda word: word != "-"
)
names = st.lists(_words, min_size=1, max_size=3).map(" ".join)
uints = st.integers(min_value=0, max_value=999)
signs = st.sampled_from(["+", "-"])


@given(name=names, target=uints)
def test_check_entry_round_trips(name, target):
    rendered = f"{name} {target}+"
    assert parse_entry(rendered, EntryContext.GATE) == CharacteristicCheck(
        characteristic=name, target=target
    )


@given(name=names, sign=signs, amount=uints)
def test_adjustment_entry_round_trips(name, sign, amount):
    rendered = f"{name} {sign}{amount}"
    signed = amount if sign == "+" else -amount
    assert parse_entry(rendered, EntryContext.SKILL_TABLE) == CharacteristicAdjustment(
        characteristic=name, amount=signed
    )


@given(name=names, specialty=st.none() | names, level=uints)
def test_grant_entry_round_trips(name, specialty, level):
    written_name = f"{name} ({specialty})" if specialty is not None else name
    rendered = f"{written_name} {level}"
    assert parse_entry(rendered, EntryContext.SKILL_TABLE) == SkillGrant(
        skill=SkillReference(name=name, specialty=specialty), level=level
    )


@given(name=names, specialty=st.none() | names)
def test_bare_skill_reference_round_trips(name, specialty):
    rendered = f"{name} ({specialty})" if specialty is not None else name
    assert parse_entry(rendered, EntryContext.SKILL_TABLE) == SkillReference(
        name=name, specialty=specialty
    )


@given(name=names)
def test_bare_benefit_item_round_trips(name):
    assert parse_entry(name, EntryContext.BENEFIT_TABLE) == BenefitItem(name=name)


# --- the walk (003-npc-generator T110): always alive, always internally
# consistent, over Hypothesis-drawn seeds rather than a fixed sample ---

_RULES = load_rules()


@settings(max_examples=50, deadline=None)
@given(seed=seeds)
def test_the_walk_always_produces_a_living_named_consistent_character(seed):
    character = generate_character(Roller(seed), _RULES)
    assert character.name
    assert character.careers
    assert character.funds >= 0
    assert character.debt >= 0
    floor = _RULES.characteristics.floor()
    for code, score in character.characteristics.items():
        assert score >= floor
        _RULES.characteristics.symbol(score)  # raises if out of the declared range
    assert character.history
