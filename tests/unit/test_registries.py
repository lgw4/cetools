import pytest

from cetools.errors import RulesDataError, TaskError, ValidationProblem
from cetools.notation import SkillReference
from cetools.registries import (
    Band,
    BenefitRegistry,
    CharacteristicRegistry,
    SkillRegistry,
    SkillResolution,
    parse_benefits,
    parse_characteristics,
    parse_skills,
)

# A valid `[modifier-dms]` table, reused across `TestCharacteristicRegistry`
# so each test can isolate the field it means to break (003-npc-generator
# FR-039). Twelve bands, matching the shipped file.
VALID_MODIFIER_DMS = {
    "0-2": -2,
    "3-5": -1,
    "6-8": 0,
    "9-11": 1,
    "12-14": 2,
    "15-17": 3,
    "18-20": 4,
    "21-23": 5,
    "24-26": 6,
    "27-29": 7,
    "30-32": 8,
    "33+": 9,
}


class TestCharacteristicRegistry:
    def test_parses_valid_file(self):
        data = {
            "schema": "characteristics",
            "schema-version": 2,
            "characteristics": {"STR": "Strength", "INT": "Intellect"},
            "modifier-dms": VALID_MODIFIER_DMS,
        }
        registry, problems = parse_characteristics(data, "characteristics.toml")
        assert problems == ()
        assert isinstance(registry, CharacteristicRegistry)
        assert registry.names["STR"] == "Strength"
        assert registry.names["INT"] == "Intellect"
        assert len(registry.bands) == 12
        assert registry.characteristic_dm(7) == 0

    def test_contains_delegates_to_names(self):
        registry = CharacteristicRegistry(names={"STR": "Strength"})
        assert "STR" in registry
        assert "str" not in registry  # case sensitive

    def test_missing_characteristics_table_is_a_problem(self):
        data = {
            "schema": "characteristics",
            "schema-version": 2,
            "modifier-dms": VALID_MODIFIER_DMS,
        }
        registry, problems = parse_characteristics(data, "characteristics.toml")
        assert registry is None
        assert len(problems) == 1
        assert problems[0].file == "characteristics.toml"
        assert problems[0].location == "characteristics"

    def test_empty_characteristics_table_is_a_problem(self):
        data = {
            "schema": "characteristics",
            "schema-version": 2,
            "characteristics": {},
            "modifier-dms": VALID_MODIFIER_DMS,
        }
        registry, problems = parse_characteristics(data, "characteristics.toml")
        assert registry is None
        assert len(problems) == 1

    def test_non_string_label_is_a_type_problem(self):
        data = {
            "schema": "characteristics",
            "schema-version": 2,
            "characteristics": {"STR": 5},
            "modifier-dms": VALID_MODIFIER_DMS,
        }
        registry, problems = parse_characteristics(data, "characteristics.toml")
        assert registry is None
        assert problems[0].location == "characteristics.STR"

    def test_every_non_string_label_is_reported_not_only_the_first(self):
        # The standard T076 held `parse_skills` to, asserted at the sibling it
        # was compared against: changing this loop's `continue` to `break` left
        # the whole suite green, so the asymmetry that justified the fix could
        # regress here unnoticed (FR-021, SC-003).
        data = {
            "schema": "characteristics",
            "schema-version": 2,
            "characteristics": {"STR": 5, "DEX": 7, "END": 9},
            "modifier-dms": VALID_MODIFIER_DMS,
        }
        registry, problems = parse_characteristics(data, "characteristics.toml")
        assert registry is None
        assert [p.location for p in problems] == [
            "characteristics.STR",
            "characteristics.DEX",
            "characteristics.END",
        ]

    def test_unrecognized_top_level_key_is_a_problem(self):
        data = {
            "schema": "characteristics",
            "schema-version": 2,
            "characteristics": {"STR": "Strength"},
            "modifier-dms": VALID_MODIFIER_DMS,
            "extra": "nope",
        }
        registry, problems = parse_characteristics(data, "characteristics.toml")
        assert registry is None
        assert any(p.location == "extra" for p in problems)

    def test_two_unrecognized_top_level_keys_are_both_reported(self):
        # `_unrecognized_key_problems` is shared by all three registry
        # parsers; truncating `extra = sorted(set(data) - allowed)` to its
        # first element would leave a file with two misspelled top-level
        # keys reporting only one, hiding the mistake FR-020 exists for
        # (FR-021, SC-003).
        data = {
            "schema": "characteristics",
            "schema-version": 2,
            "characteristics": {"STR": "Strength"},
            "modifier-dms": VALID_MODIFIER_DMS,
            "extra": "nope",
            "other": "also nope",
        }
        registry, problems = parse_characteristics(data, "characteristics.toml")
        assert registry is None
        assert {p.location for p in problems} >= {"extra", "other"}


class TestCharacteristicRegistryModifierBands:
    """`[modifier-dms]` parsing, moved here from the previous feature's
    `tasks.toml` reader when the bands moved to the characteristics registry
    (003-npc-generator FR-039, T009).
    """

    def _parsed(self, modifier_dms):
        data = {
            "schema": "characteristics",
            "schema-version": 2,
            "characteristics": {"STR": "Strength"},
            "modifier-dms": modifier_dms,
        }
        registry, problems = parse_characteristics(data, "characteristics.toml")
        assert not problems, problems
        assert registry is not None
        return registry

    def _problems(self, modifier_dms):
        data = {
            "schema": "characteristics",
            "schema-version": 2,
            "characteristics": {"STR": "Strength"},
            "modifier-dms": modifier_dms,
        }
        registry, problems = parse_characteristics(data, "characteristics.toml")
        assert registry is None
        return problems

    def test_all_twelve_bands_parse_sorted_by_minimum(self):
        registry = self._parsed(VALID_MODIFIER_DMS)
        assert len(registry.bands) == 12
        assert registry.bands[0] == Band(minimum=0, maximum=2, dm=-2)
        assert registry.bands[-1] == Band(minimum=33, maximum=None, dm=9)

    def test_bands_sort_by_minimum_regardless_of_file_order(self):
        # `Band`'s own docstring states the unbounded band "sorts last" as an
        # invariant `characteristic_dm`'s linear first-match scan depends on;
        # nothing forbids overlapping bands, so file order — not declaration
        # order — must decide which of two overlapping bands a shadowed score
        # resolves to (FR-026, plan.md trap list).
        registry = self._parsed({"5-15": 5, "0-10": -2, "33+": 9})
        assert [band.minimum for band in registry.bands] == [0, 5, 33]
        assert registry.characteristic_dm(7) == -2

    def test_missing_modifier_dms_table_is_a_problem(self):
        data = {"schema": "characteristics", "schema-version": 2, "characteristics": {"STR": "S"}}
        registry, problems = parse_characteristics(data, "characteristics.toml")
        assert registry is None
        assert any(p.location == "modifier-dms" and p.found == "missing" for p in problems)

    def test_empty_modifier_dms_table_is_a_problem(self):
        problems = self._problems({})
        assert any(p.location == "modifier-dms" and p.found == "an empty table" for p in problems)

    def test_several_unbounded_bands_reports_a_problem(self):
        modifier_dms = dict(VALID_MODIFIER_DMS)
        del modifier_dms["30-32"]
        modifier_dms["30+"] = 8
        problems = self._problems(modifier_dms)
        assert any(p.location == "modifier-dms" for p in problems)

    def test_malformed_band_key_reports_a_problem(self):
        modifier_dms = dict(VALID_MODIFIER_DMS)
        del modifier_dms["0-2"]
        modifier_dms["low"] = -2
        problems = self._problems(modifier_dms)
        assert any(p.location == "modifier-dms.low" for p in problems)

    def test_boolean_modifier_dm_value_is_a_type_problem(self):
        modifier_dms = dict(VALID_MODIFIER_DMS)
        modifier_dms["9-11"] = True
        problems = self._problems(modifier_dms)
        matching = [p for p in problems if p.location == "modifier-dms.9-11"]
        assert len(matching) == 1
        assert matching[0].found == "a boolean"

    def test_removed_band_leaves_a_gap_that_raises(self):
        modifier_dms = dict(VALID_MODIFIER_DMS)
        del modifier_dms["15-17"]
        registry = self._parsed(modifier_dms)
        assert len(registry.bands) == 11
        for score in (15, 16, 17):
            with pytest.raises(RulesDataError, match="no characteristic band covers"):
                registry.characteristic_dm(score)
        assert registry.characteristic_dm(14) == 2
        assert registry.characteristic_dm(18) == 4

    def test_negative_score_raises_task_error(self):
        registry = self._parsed(VALID_MODIFIER_DMS)
        with pytest.raises(TaskError):
            registry.characteristic_dm(-1)


class TestSkillRegistry:
    def test_parses_valid_file(self):
        data = {
            "schema": "skills",
            "schema-version": 1,
            "skills": {"Admin": [], "Blade": ["Cutlass", "Dagger"]},
        }
        registry, problems = parse_skills(data, "skills.toml")
        assert problems == ()
        assert isinstance(registry, SkillRegistry)
        assert registry.skills["Blade"] == ("Cutlass", "Dagger")
        assert registry.skills["Admin"] == ()

    def test_missing_skills_table_is_a_problem(self):
        data = {"schema": "skills", "schema-version": 1}
        registry, problems = parse_skills(data, "skills.toml")
        assert registry is None
        assert problems[0].location == "skills"

    def test_empty_skills_table_is_a_problem(self):
        data = {"schema": "skills", "schema-version": 1, "skills": {}}
        registry, problems = parse_skills(data, "skills.toml")
        assert registry is None

    def test_non_list_specialties_is_a_type_problem(self):
        data = {"schema": "skills", "schema-version": 1, "skills": {"Pilot": "none"}}
        registry, problems = parse_skills(data, "skills.toml")
        assert registry is None
        assert problems[0].location == "skills.Pilot"

    def test_non_string_specialty_is_a_type_problem(self):
        data = {"schema": "skills", "schema-version": 1, "skills": {"Blade": ["Cutlass", 5]}}
        registry, problems = parse_skills(data, "skills.toml")
        assert registry is None
        assert problems[0].location == "skills.Blade[1]"

    def test_every_non_string_specialty_is_reported_not_only_the_first(self):
        # FR-021 collects everything and SC-003 requires the number of runs
        # needed to find every problem in a file to be one. Reporting the
        # first offending element alone made this the one field where fixing
        # the reported mistake revealed the next one on the following run,
        # while `parse_benefits` and `parse_characteristics` both loop.
        data = {
            "schema": "skills",
            "schema-version": 1,
            "skills": {"Blade": ["Cutlass", 5, 7, 9]},
        }
        registry, problems = parse_skills(data, "skills.toml")
        assert registry is None
        assert [p.location for p in problems] == [
            "skills.Blade[1]",
            "skills.Blade[2]",
            "skills.Blade[3]",
        ]

    def test_unrecognized_top_level_key_is_a_problem(self):
        data = {
            "schema": "skills",
            "schema-version": 1,
            "skills": {"Admin": []},
            "extra": "nope",
        }
        registry, problems = parse_skills(data, "skills.toml")
        assert registry is None
        assert any(p.location == "extra" for p in problems)

    def test_a_skill_name_spelling_a_specialty_is_a_problem(self):
        # T100's mirror case. A key such as `Gun Combat (Slug Rifle)` was
        # accepted and could then be referenced by nothing: any career writing
        # that very text parses it into a base and a specialty and resolves
        # `UNRECOGNIZED_SKILL` against `Gun Combat`. Specialties are declared
        # in the array (FR-011), so a name that also spells one is a mistake
        # rather than an unreachable entry (FR-006, FR-013).
        data = {
            "schema": "skills",
            "schema-version": 1,
            "skills": {"Gun Combat (Slug Rifle)": []},
        }
        registry, problems = parse_skills(data, "skills.toml")
        assert registry is None
        assert len(problems) == 1
        assert problems[0].location == "skills.Gun Combat (Slug Rifle)"
        assert problems[0].found == "Gun Combat (Slug Rifle)"
        assert "no parentheses" in problems[0].expected

    def test_an_unbalanced_parenthesis_in_a_skill_name_is_caught_too(self):
        data = {"schema": "skills", "schema-version": 1, "skills": {"Blade (": []}}
        registry, problems = parse_skills(data, "skills.toml")
        assert registry is None
        assert [p.location for p in problems] == ["skills.Blade ("]


class TestSkillRegistryResolution:
    def _registry(self):
        return SkillRegistry(skills={"Admin": (), "Blade": ("Cutlass", "Dagger", "Sword")})

    def test_unrecognized_skill_name(self):
        registry = self._registry()
        result = registry.resolve(SkillReference(name="Vac Suit"))
        assert result is SkillResolution.UNRECOGNIZED_SKILL

    def test_specialty_given_for_a_skill_that_has_none(self):
        registry = self._registry()
        result = registry.resolve(SkillReference(name="Admin", specialty="Legal"))
        assert result is SkillResolution.SPECIALTY_NOT_ALLOWED

    def test_unrecognized_specialty_for_a_skill_that_has_some(self):
        registry = self._registry()
        result = registry.resolve(SkillReference(name="Blade", specialty="Chainsaw"))
        assert result is SkillResolution.UNRECOGNIZED_SPECIALTY

    def test_valid_fully_specified(self):
        registry = self._registry()
        result = registry.resolve(SkillReference(name="Blade", specialty="Cutlass"))
        assert result is SkillResolution.VALID

    def test_valid_choice_owed_stays_distinguishable_from_fully_specified(self):
        registry = self._registry()
        choice_owed = SkillReference(name="Blade", specialty=None)
        fully_specified = SkillReference(name="Blade", specialty="Cutlass")

        assert registry.resolve(choice_owed) is SkillResolution.VALID
        assert registry.resolve(fully_specified) is SkillResolution.VALID
        # The registry says both are valid; the distinction survives on the
        # SkillReference itself, which the registry does not collapse.
        assert choice_owed.specialty is None
        assert fully_specified.specialty is not None

    def test_case_sensitive_skill_name(self):
        registry = self._registry()
        result = registry.resolve(SkillReference(name="blade", specialty=None))
        assert result is SkillResolution.UNRECOGNIZED_SKILL

    def test_case_sensitive_specialty(self):
        registry = self._registry()
        result = registry.resolve(SkillReference(name="Blade", specialty="cutlass"))
        assert result is SkillResolution.UNRECOGNIZED_SPECIALTY


class TestBenefitRegistry:
    def test_parses_valid_file(self):
        data = {
            "schema": "benefits",
            "schema-version": 1,
            "benefits": ["Low Passage", "Middle Passage"],
        }
        registry, problems = parse_benefits(data, "benefits.toml")
        assert problems == ()
        assert isinstance(registry, BenefitRegistry)
        assert registry.items == ("Low Passage", "Middle Passage")

    def test_contains_delegates_to_items(self):
        registry = BenefitRegistry(items=("Low Passage",))
        assert "Low Passage" in registry
        assert "low passage" not in registry  # case sensitive

    def test_missing_benefits_key_is_a_problem(self):
        data = {"schema": "benefits", "schema-version": 1}
        registry, problems = parse_benefits(data, "benefits.toml")
        assert registry is None
        assert problems[0].location == "benefits"

    def test_empty_benefits_array_is_a_problem(self):
        data = {"schema": "benefits", "schema-version": 1, "benefits": []}
        registry, problems = parse_benefits(data, "benefits.toml")
        assert registry is None

    def test_non_string_item_is_a_type_problem(self):
        data = {"schema": "benefits", "schema-version": 1, "benefits": ["Low Passage", 5]}
        registry, problems = parse_benefits(data, "benefits.toml")
        assert registry is None
        assert problems[0].location == "benefits[1]"

    def test_every_non_string_item_is_reported_not_only_the_first(self):
        # The other sibling T076's fix was measured against; `break` here left
        # the suite green too (FR-021, SC-003).
        data = {"schema": "benefits", "schema-version": 1, "benefits": [5, 7, 9]}
        registry, problems = parse_benefits(data, "benefits.toml")
        assert registry is None
        assert [p.location for p in problems] == ["benefits[0]", "benefits[1]", "benefits[2]"]

    def test_unrecognized_top_level_key_is_a_problem(self):
        data = {
            "schema": "benefits",
            "schema-version": 1,
            "benefits": ["Low Passage"],
            "extra": "nope",
        }
        registry, problems = parse_benefits(data, "benefits.toml")
        assert registry is None
        assert any(p.location == "extra" for p in problems)


class TestProblemsAreValidationProblems:
    def test_returned_problems_are_validation_problem_instances(self):
        data = {"schema": "benefits", "schema-version": 1}
        _, problems = parse_benefits(data, "benefits.toml")
        assert all(isinstance(p, ValidationProblem) for p in problems)
