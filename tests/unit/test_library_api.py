"""Every capability this feature adds, reached through `import cetools`
alone, with the command line never invoked (SC-013, FR-043).

Individual behaviors already have focused coverage elsewhere; this file's
job is programmatic reachability, not re-deriving that detail.
"""

import json
from importlib import resources

import pytest

import cetools


def _navy_source() -> str:
    return (
        resources.files("cetools.data.careers").joinpath("navy.toml").read_text(encoding="utf-8")
    )


def test_load_rules_and_validate_rules_agree_on_the_packaged_set():
    rules = cetools.load_rules()
    report = cetools.validate_rules()
    assert isinstance(rules, cetools.RulesData)
    assert isinstance(report, cetools.ValidationReport)
    assert report.valid
    assert report.problems == ()


def test_rules_data_exposes_every_component():
    rules = cetools.load_rules()
    assert isinstance(rules.task_parameters, cetools.TaskParameters)
    assert isinstance(rules.characteristics, cetools.CharacteristicRegistry)
    assert isinstance(rules.skills, cetools.SkillRegistry)
    assert isinstance(rules.benefits, cetools.BenefitRegistry)
    assert isinstance(rules.careers["navy"], cetools.CareerDefinition)
    assert isinstance(rules.provenance, cetools.Provenance)
    assert rules.provenance.is_packaged
    assert "INT" in rules.characteristics
    assert "Low Passage" in rules.benefits
    resolution = rules.skills.resolve(cetools.SkillReference(name="Piloting", specialty=None))
    assert resolution is cetools.SkillResolution.VALID


def test_career_definition_exposes_throws_tables_ladders_and_mustering_out():
    navy = cetools.load_rules().careers["navy"]
    assert isinstance(navy.throws["survival"], cetools.Throw)
    assert isinstance(navy.tables["service"], cetools.SkillTable)
    assert isinstance(navy.ladders[0], cetools.RankLadder)
    assert isinstance(navy.ladders[0].ranks[0], cetools.Rank)
    assert isinstance(navy.mustering_out, cetools.MusteringOut)


def test_parse_entry_covers_all_four_notation_forms():
    assert cetools.parse_entry("INT 4+", cetools.EntryContext.GATE) == cetools.CharacteristicCheck(
        characteristic="INT", target=4
    )
    assert cetools.parse_entry(
        "STR +1", cetools.EntryContext.SKILL_TABLE
    ) == cetools.CharacteristicAdjustment(characteristic="STR", amount=1)
    assert cetools.parse_entry(
        "Piloting 2", cetools.EntryContext.SKILL_TABLE
    ) == cetools.SkillGrant(skill=cetools.SkillReference(name="Piloting", specialty=None), level=2)
    assert cetools.parse_entry(
        "Melee Combat", cetools.EntryContext.SKILL_TABLE
    ) == cetools.SkillReference(name="Melee Combat", specialty=None)
    assert cetools.parse_entry(
        "Low Passage", cetools.EntryContext.BENEFIT_TABLE
    ) == cetools.BenefitItem(name="Low Passage")


def test_parse_entry_reports_a_malformed_entry_as_a_notation_problem():
    """The failure path of `parse_entry`, named through the package.

    `parse_entry` returns rather than raises (plan.md: validation is a
    function, not a control flow), so a library-only caller has to be able
    to name the type it gets back.
    """
    malformed = cetools.parse_entry("Piloting +", cetools.EntryContext.SKILL_TABLE)
    assert isinstance(malformed, cetools.NotationProblem)
    assert malformed.found == "Piloting +"
    assert malformed.expected

    inadmissible = cetools.parse_entry("Piloting 2", cetools.EntryContext.BENEFIT_TABLE)
    assert isinstance(inadmissible, cetools.NotationProblem)
    assert inadmissible.found == "Piloting 2"


def test_skill_resolution_covers_all_four_outcomes():
    """Every outcome of `SkillRegistry.resolve`, compared against the
    exported enum rather than against a member's name.
    """
    skills = cetools.load_rules().skills

    def resolve(name: str, specialty: str | None) -> cetools.SkillResolution:
        return skills.resolve(cetools.SkillReference(name=name, specialty=specialty))

    assert resolve("Gun Combat", "Slug Rifle") is cetools.SkillResolution.VALID
    assert resolve("Gun Combat", None) is cetools.SkillResolution.VALID
    assert resolve("Vac Suit", None) is cetools.SkillResolution.UNRECOGNIZED_SKILL
    assert resolve("Piloting", "Small Craft") is cetools.SkillResolution.SPECIALTY_NOT_ALLOWED
    assert resolve("Gun Combat", "Boomerang") is cetools.SkillResolution.UNRECOGNIZED_SPECIALTY


def test_an_invalid_override_load_raises_with_located_problems(tmp_path):
    broken = tmp_path / "characteristics.toml"
    broken.write_text('schema = "characteristics"\nschema-version = 1\n', encoding="utf-8")
    with pytest.raises(cetools.RulesDataError) as excinfo:
        cetools.load_rules(tmp_path)
    assert excinfo.value.problems
    assert all(isinstance(p, cetools.ValidationProblem) for p in excinfo.value.problems)


def test_the_same_invalid_override_reports_rather_than_raises_through_validate(tmp_path):
    broken = tmp_path / "characteristics.toml"
    broken.write_text('schema = "characteristics"\nschema-version = 1\n', encoding="utf-8")
    report = cetools.validate_rules(tmp_path)
    assert not report.valid
    assert report.problems


def test_an_override_reaches_a_check_result_with_overridden_provenance(tmp_path):
    navy = _navy_source()
    (tmp_path / "navy.toml").write_text(
        navy.replace("target = 5", "target = 9", 1), encoding="utf-8"
    )
    rules = cetools.load_rules(tmp_path)
    assert rules.careers["navy"].throws["survival"].target == 9
    assert not rules.provenance.is_packaged

    result = cetools.check(cetools.Roller("session-alpha"), rules=rules)
    assert isinstance(result, cetools.CheckResult)
    assert result.provenance is rules.provenance
    assert result.provenance.files[0].disposition is cetools.Disposition.REPLACED
    assert result.provenance.files[0].fingerprint.startswith("sha256:")


def test_check_result_and_validation_report_render_in_every_format():
    result = cetools.check(cetools.Roller("session-alpha"))
    assert "Rules:" in cetools.as_text(result)
    assert cetools.as_dict(result)["provenance"]["source"] == "packaged"
    assert json.loads(cetools.as_json(result))["provenance"]["source"] == "packaged"

    report = cetools.validate_rules()
    assert "Rules data is valid." in cetools.as_text(report)
    assert cetools.as_dict(report)["valid"] is True
    assert json.loads(cetools.as_json(report))["valid"] is True
