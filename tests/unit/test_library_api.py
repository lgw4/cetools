"""Every capability this feature adds, reached through `import cetools`
alone, with the command line never invoked (SC-013, FR-043).

Individual behaviors already have focused coverage elsewhere; this file's
job is programmatic reachability, not re-deriving that detail.
"""

import json
import re
from importlib import resources
from pathlib import Path

import pytest

import cetools

_SPECS = Path(__file__).resolve().parents[2] / "specs"
_FENCE = re.compile(r"```python\n(.*?)```", re.DOTALL)


def _first_python_block(contract: Path, heading: str) -> str:
    section = contract.read_text(encoding="utf-8").split(f"\n## {heading}\n", 1)
    assert len(section) == 2, f"{contract.name} has no '## {heading}' section"
    match = _FENCE.search(section[1].split("\n## ", 1)[0])
    assert match is not None, f"'{heading}' in {contract.name} carries no python block"
    return match.group(1)


def _names(block: str) -> set[str]:
    """Every bare identifier a contract block lists, comments stripped.

    Reads both the `from cetools import (...)` form and the bare-name form the
    removed-surface block uses, so the two sections are compared the same way.
    """
    # Comments first: the removed-surface block explains itself with
    # `# replaced by load_rules(...)`, whose parentheses would otherwise be
    # taken for the import list's and leave the set holding `...`.
    body = "\n".join(line.split("#", 1)[0] for line in block.splitlines())
    if "(" in body:
        body = body.split("(", 1)[1].rsplit(")", 1)[0]
    found = {part.strip() for part in body.replace("\n", ",").split(",") if part.strip()}
    found.discard("from cetools import")
    return found


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


class TestPublicSurfaceMatchesTheContract:
    """`__all__` compared against the contracts as a *set*, in both
    directions. Nothing did that — `rg __all__ tests/` returned nothing — so
    two clauses of contracts/library-api.md survived being broken with the
    suite green: restoring a working `load_task_parameters`, which the
    contract lists under **Public surface removed** and FR-044 requires
    replaced rather than kept alongside, and dropping `FileProvenance`, which
    every test reaches through `cetools.provenance` instead. Comparing the set
    closes both, and every future one (FR-043, SC-013).
    """

    _ADDED = _names(
        _first_python_block(
            _SPECS / "002-rules-data-loading" / "contracts" / "library-api.md",
            "Public surface added",
        )
    )
    _REMOVED = _names(
        _first_python_block(
            _SPECS / "002-rules-data-loading" / "contracts" / "library-api.md",
            "Public surface removed",
        )
    )
    _INHERITED = _names(
        _first_python_block(
            _SPECS / "001-dice-task-engine" / "contracts" / "library-api.md",
            "Public surface (`cetools/__init__.py`)",
        )
    )
    # A third contract (T076): `003-npc-generator` adds the generation
    # surface. Its "Public surface added" block is the `from cetools import
    # (...)` form the other two contracts use; "Public surface removed" is
    # the literal word `nothing`, which `_names` reads as an empty set.
    _ADDED_003 = _names(
        _first_python_block(
            _SPECS / "003-npc-generator" / "contracts" / "library-api.md",
            "Public surface added",
        )
    )
    _REMOVED_003 = _names(
        _first_python_block(
            _SPECS / "003-npc-generator" / "contracts" / "library-api.md",
            "Public surface removed",
        )
    )

    def test_the_contracts_parsed_into_something(self):
        # A heading rename or a reformatted block would otherwise leave every
        # assertion below comparing the empty set against itself.
        assert len(self._INHERITED) > 10
        assert len(self._ADDED) > 20
        assert self._REMOVED == {"load_task_parameters"}
        assert len(self._ADDED_003) > 20
        assert self._REMOVED_003 == set()

    def test_all_is_exactly_the_inherited_surface_less_what_was_removed_plus_what_was_added(self):
        expected = (self._INHERITED - self._REMOVED) | self._ADDED
        expected = (expected - self._REMOVED_003) | self._ADDED_003
        assert set(cetools.__all__) == expected

    def test_all_has_no_duplicates(self):
        assert len(cetools.__all__) == len(set(cetools.__all__))

    def test_every_name_in_all_is_actually_importable(self):
        for name in cetools.__all__:
            assert hasattr(cetools, name), name

    def test_the_removed_surface_is_gone_from_the_module_as_well_as_from_all(self):
        for name in self._REMOVED:
            assert not hasattr(cetools, name), name
