from cetools.errors import ValidationProblem
from cetools.notation import SkillReference
from cetools.registries import (
    BenefitRegistry,
    CharacteristicRegistry,
    SkillRegistry,
    SkillResolution,
    parse_benefits,
    parse_characteristics,
    parse_skills,
)


class TestCharacteristicRegistry:
    def test_parses_valid_file(self):
        data = {
            "schema": "characteristics",
            "schema-version": 1,
            "characteristics": {"STR": "Strength", "INT": "Intellect"},
        }
        registry, problems = parse_characteristics(data, "characteristics.toml")
        assert problems == ()
        assert isinstance(registry, CharacteristicRegistry)
        assert registry.names["STR"] == "Strength"
        assert registry.names["INT"] == "Intellect"

    def test_contains_delegates_to_names(self):
        registry = CharacteristicRegistry(names={"STR": "Strength"})
        assert "STR" in registry
        assert "str" not in registry  # case sensitive

    def test_missing_characteristics_table_is_a_problem(self):
        data = {"schema": "characteristics", "schema-version": 1}
        registry, problems = parse_characteristics(data, "characteristics.toml")
        assert registry is None
        assert len(problems) == 1
        assert problems[0].file == "characteristics.toml"
        assert problems[0].location == "characteristics"

    def test_empty_characteristics_table_is_a_problem(self):
        data = {"schema": "characteristics", "schema-version": 1, "characteristics": {}}
        registry, problems = parse_characteristics(data, "characteristics.toml")
        assert registry is None
        assert len(problems) == 1

    def test_non_string_label_is_a_type_problem(self):
        data = {
            "schema": "characteristics",
            "schema-version": 1,
            "characteristics": {"STR": 5},
        }
        registry, problems = parse_characteristics(data, "characteristics.toml")
        assert registry is None
        assert problems[0].location == "characteristics.STR"

    def test_unrecognized_top_level_key_is_a_problem(self):
        data = {
            "schema": "characteristics",
            "schema-version": 1,
            "characteristics": {"STR": "Strength"},
            "extra": "nope",
        }
        registry, problems = parse_characteristics(data, "characteristics.toml")
        assert registry is None
        assert any(p.location == "extra" for p in problems)


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
