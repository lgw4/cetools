from cetools.engine.background import HOMEWORLD_SKILLS, background_skills, draw_distinct
from cetools.engine.rolls import RollName
from conftest import scripted

# --- draw_distinct ---


def test_draw_distinct_returns_requested_count_of_distinct_items() -> None:
    # Every draw takes index 0, the head of what remains.
    result = draw_distinct(("A", "B", "C", "D"), 3, scripted())
    assert result == ["A", "B", "C"]
    assert len(set(result)) == 3


def test_draw_distinct_respects_exclude() -> None:
    result = draw_distinct(("A", "B", "C"), 2, scripted(), exclude=("A",))
    assert result == ["B", "C"]
    assert "A" not in result


def test_draw_distinct_truncates_when_over_requested() -> None:
    # Only 2 items available but 5 requested → returns just the 2.
    result = draw_distinct(("A", "B"), 5, scripted())
    assert result == ["A", "B"]


def test_draw_distinct_uses_the_choice_to_index() -> None:
    # Index 2 each draw: [A,B,C,D] -> C; then [A,B,D] -> D.
    result = draw_distinct(
        ("A", "B", "C", "D"), 2, scripted(choices={RollName.BACKGROUND_SKILL: 2})
    )
    assert result == ["C", "D"]


def test_draw_distinct_can_reach_pool_tail() -> None:
    # Regression: indexing a pool larger than 6 with a fixed d6 left the tail
    # unreachable (Zero-G at index 9 could never be drawn). A choice is sized to
    # the pool, not to a die, so the last element is reachable.
    result = draw_distinct(HOMEWORLD_SKILLS, 1, scripted(choices={RollName.BACKGROUND_SKILL: -1}))
    assert result == ["Zero-G"]


# --- background_skills ---


def test_background_skill_count_matches_three_plus_education_dm() -> None:
    # count = 3 + characteristic_modifier(Education).
    cases = {2: 1, 4: 2, 7: 3, 10: 4, 12: 5, 15: 6}
    for education, expected in cases.items():
        skills = background_skills({"Education": education}, scripted())
        assert len(skills) == expected, f"Education {education} should grant {expected} skills"


def test_background_skills_are_all_level_zero() -> None:
    skills = background_skills({"Education": 12}, scripted())
    assert all(level == 0 for level in skills.values())


def test_background_low_education_draws_only_homeworld_skills() -> None:
    # count 1 (Edu 2) and count 2 (Edu 4) → every skill comes from the homeworld pool.
    for education in (2, 4):
        skills = background_skills({"Education": education}, scripted())
        assert set(skills) <= set(HOMEWORLD_SKILLS)


def test_background_full_draw_is_deterministic_and_distinct() -> None:
    # Edu 12 → count 5. Every draw takes index 0.
    # Homeworld: Animals, Broker. Education (excluding those): Admin, Advocate, Carousing.
    skills = background_skills({"Education": 12}, scripted())
    assert set(skills) == {"Animals", "Broker", "Admin", "Advocate", "Carousing"}


def test_background_skills_reproducible_across_identical_scripts() -> None:
    choices = {RollName.BACKGROUND_SKILL: [1, 3, 0, 2]}
    first = background_skills({"Education": 10}, scripted(choices=choices))
    second = background_skills({"Education": 10}, scripted(choices=dict(choices)))
    assert first == second


def test_background_skills_does_not_mutate_characteristics() -> None:
    characteristics = {"Education": 12}
    background_skills(characteristics, scripted())
    assert characteristics == {"Education": 12}
