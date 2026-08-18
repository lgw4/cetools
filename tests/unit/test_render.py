import json

import pytest

from cetools.dice import ThrowResult
from cetools.errors import CetoolsError, ValidationProblem
from cetools.provenance import Disposition, FileProvenance, Provenance
from cetools.render import as_dict, as_json, as_text
from cetools.rules import ValidationReport
from cetools.tasks import CheckResult, Modifier

_PACKAGED = Provenance(version="2026.08.1", files=(), ignored=())
_OVERRIDDEN_WITH_IGNORED = Provenance(
    version="2026.08.1",
    files=(
        FileProvenance(
            file="navy.toml",
            disposition=Disposition.REPLACED,
            fingerprint="sha256:" + "3b1f" + "c0" * 30,
        ),
        FileProvenance(
            file="scouts.toml",
            disposition=Disposition.ADDED,
            fingerprint="sha256:" + "9ad4" + "71" * 30,
        ),
    ),
    ignored=("notes.md",),
)
_PACKAGED_WITH_IGNORED = Provenance(version="2026.08.1", files=(), ignored=("notes.md",))
_OVERRIDDEN_WITH_LONGER_IGNORED_PATH = Provenance(
    version="2026.08.1",
    files=(
        FileProvenance(
            file="navy.toml",
            disposition=Disposition.REPLACED,
            fingerprint="sha256:" + "3b1f" + "c0" * 30,
        ),
    ),
    ignored=("deep/subdir/notes.md",),
)


def test_as_text_throw_with_modifier_matches_contract_example():
    result = ThrowResult(
        notation="2d6+1",
        faces=(1, 5),
        modifier=1,
        total=7,
        seed=14333185781139156525,
    )
    assert as_text(result) == (
        "2d6+1 = 7\n"
        "  Dice:     1, 5 (sum 6)\n"
        "  Modifier: +1\n"
        "  Seed:     14333185781139156525\n"
    )


def test_as_text_throw_without_modifier_omits_sum_and_modifier_line():
    result = ThrowResult(
        notation="1d6",
        faces=(1,),
        modifier=0,
        total=1,
        seed=14333185781139156525,
    )
    assert as_text(result) == ("1d6 = 1\n" "  Dice: 1\n" "  Seed: 14333185781139156525\n")


def test_as_text_throw_negative_modifier_is_signed():
    result = ThrowResult(
        notation="2d6-1",
        faces=(1, 5),
        modifier=-1,
        total=5,
        seed=1,
    )
    text = as_text(result)
    assert "Modifier: -1" in text


def test_as_text_throw_ends_with_trailing_newline():
    result = ThrowResult(
        notation="1d6",
        faces=(1,),
        modifier=0,
        total=1,
        seed=1,
    )
    assert as_text(result).endswith("\n")
    assert not as_text(result).endswith("\n\n")


def test_as_text_check_matches_contract_difficult_example():
    result = CheckResult(
        faces=(1, 5),
        dice_total=6,
        modifiers=(
            Modifier(label="Difficulty (Difficult)", value=-2),
            Modifier(label="Characteristic 9", value=1),
            Modifier(label="Skill 2", value=2),
            Modifier(label="cover", value=-2),
        ),
        total=5,
        target=8,
        success=False,
        seed=14333185781139156525,
        provenance=_PACKAGED,
    )
    assert as_text(result) == (
        "Check: FAILURE\n"
        "  Dice:  1, 5 (sum 6)\n"
        "  Modifiers:\n"
        "    Difficulty (Difficult) -2\n"
        "    Characteristic 9       +1\n"
        "    Skill 2                +2\n"
        "    cover                  -2\n"
        "  Total: 5 vs target 8\n"
        "  Seed:  14333185781139156525\n"
        "  Rules: packaged (cetools 2026.08.1)\n"
    )


def test_as_text_check_success_header():
    result = CheckResult(
        faces=(6, 6),
        dice_total=12,
        modifiers=(Modifier(label="Difficulty (Average)", value=0),),
        total=12,
        target=8,
        success=True,
        seed=1,
        provenance=_PACKAGED,
    )
    assert as_text(result).startswith("Check: SUCCESS\n")


def test_as_text_check_modifier_values_are_signed_including_zero():
    result = CheckResult(
        faces=(2, 5),
        dice_total=7,
        modifiers=(
            Modifier(label="Difficulty (Average)", value=0),
            Modifier(label="Unskilled", value=-3),
        ),
        total=4,
        target=8,
        success=False,
        seed=1,
        provenance=_PACKAGED,
    )
    text = as_text(result)
    assert "Difficulty (Average) +0" in text
    assert "Unskilled            -3" in text


def test_as_text_check_dice_line_always_carries_sum():
    result = CheckResult(
        faces=(2, 5),
        dice_total=7,
        modifiers=(Modifier(label="Difficulty (Average)", value=0),),
        total=7,
        target=8,
        success=False,
        seed=1,
        provenance=_PACKAGED,
    )
    assert "Dice:  2, 5 (sum 7)" in as_text(result)


def test_as_text_check_ends_with_trailing_newline():
    result = CheckResult(
        faces=(2, 5),
        dice_total=7,
        modifiers=(Modifier(label="Difficulty (Average)", value=0),),
        total=7,
        target=8,
        success=False,
        seed=1,
        provenance=_PACKAGED,
    )
    text = as_text(result)
    assert text.endswith("\n")
    assert not text.endswith("\n\n")


def test_as_text_check_with_no_modifiers_renders_an_empty_modifier_list():
    # `check` always applies at least a difficulty and a skill-or-unskilled row,
    # so the CLI cannot reach this. `CheckResult` and `as_text` are both public,
    # though, so a library caller can construct one, and a heading with no rows
    # under it is not malformed — it is simply a check with nothing applied.
    result = CheckResult(
        faces=(2, 5),
        dice_total=7,
        modifiers=(),
        total=7,
        target=8,
        success=False,
        seed=1,
        provenance=_PACKAGED,
    )
    assert as_text(result) == (
        "Check: FAILURE\n"
        "  Dice:  2, 5 (sum 7)\n"
        "  Modifiers:\n"
        "  Total: 7 vs target 8\n"
        "  Seed:  1\n"
        "  Rules: packaged (cetools 2026.08.1)\n"
    )


# --- provenance block: packaged, overridden, ignored-only ---


def _check_with(provenance):
    return CheckResult(
        faces=(2, 5),
        dice_total=7,
        modifiers=(Modifier(label="Difficulty (Average)", value=0),),
        total=7,
        target=8,
        success=False,
        seed=1,
        provenance=provenance,
    )


def test_as_text_provenance_block_reports_packaged():
    text = as_text(_check_with(_PACKAGED))
    assert text.endswith("  Rules: packaged (cetools 2026.08.1)\n")


def test_as_text_provenance_block_reports_overridden_with_files_first_then_ignored():
    text = as_text(_check_with(_OVERRIDDEN_WITH_IGNORED))
    lines = text.splitlines()
    rules_index = lines.index("  Rules: overridden (cetools 2026.08.1)")
    assert lines[rules_index + 1].startswith("    navy.toml")
    assert "replaced" in lines[rules_index + 1]
    assert lines[rules_index + 2].startswith("    scouts.toml")
    assert "added" in lines[rules_index + 2]
    assert lines[rules_index + 3] == "    notes.md      ignored"


def test_as_text_provenance_block_columns_are_padded_to_the_longest_present():
    text = as_text(_check_with(_OVERRIDDEN_WITH_IGNORED))
    lines = text.splitlines()
    rules_index = lines.index("  Rules: overridden (cetools 2026.08.1)")
    provenance_lines = lines[rules_index + 1 :]
    # "scouts.toml" (11 chars) is the longest basename; "replaced" (8 chars)
    # is the longest disposition. Both shorter entries pad out to match.
    assert provenance_lines[0].startswith("    navy.toml     replaced  ")
    assert provenance_lines[1].startswith("    scouts.toml   added     ")
    assert provenance_lines[2] == "    notes.md      ignored"


def test_as_text_provenance_block_pads_to_the_longest_name_even_when_it_is_ignored():
    # The file column is padded to the longest name across BOTH lists — a
    # composition key for an effective file or a path within the override
    # for an ignored one (contracts/cli.md) — not to the longest effective
    # file alone. Changing `[fp.file for fp in provenance.files] + list(
    # provenance.ignored)` to use `or` in place of `+` would silently drop
    # the ignored list from the width calculation whenever any file took
    # effect, which no existing fixture catches: "scouts.toml" (11 chars) is
    # already the longest name in `_OVERRIDDEN_WITH_IGNORED`, so `or` would
    # coincidentally compute the same width there.
    text = as_text(_check_with(_OVERRIDDEN_WITH_LONGER_IGNORED_PATH))
    lines = text.splitlines()
    rules_index = lines.index("  Rules: overridden (cetools 2026.08.1)")
    provenance_lines = lines[rules_index + 1 :]
    width = len("deep/subdir/notes.md")
    assert len("navy.toml") < width
    assert provenance_lines[0].startswith(f"    {'navy.toml'.ljust(width)}   replaced  ")
    assert provenance_lines[1] == f"    {'deep/subdir/notes.md'.ljust(width)}   ignored"


def test_as_text_provenance_block_an_override_with_only_ignored_files_still_reads_packaged():
    text = as_text(_check_with(_PACKAGED_WITH_IGNORED))
    lines = text.splitlines()
    rules_index = lines.index("  Rules: packaged (cetools 2026.08.1)")
    # A single ignored file pads to its own width; nothing else is present.
    assert lines[rules_index + 1] == "    notes.md   ignored"


def test_as_dict_check_provenance_packaged_shape():
    payload = as_dict(_check_with(_PACKAGED))
    assert payload["provenance"] == {
        "source": "packaged",
        "version": "2026.08.1",
        "files": [],
        "ignored": [],
    }


def test_as_dict_check_provenance_overridden_shape():
    payload = as_dict(_check_with(_OVERRIDDEN_WITH_IGNORED))
    assert payload["provenance"] == {
        "source": "overridden",
        "version": "2026.08.1",
        "files": [
            {
                "file": "navy.toml",
                "disposition": "replaced",
                "fingerprint": "sha256:3b1f" + "c0" * 30,
            },
            {
                "file": "scouts.toml",
                "disposition": "added",
                "fingerprint": "sha256:9ad4" + "71" * 30,
            },
        ],
        "ignored": ["notes.md"],
    }


def test_as_dict_throw_matches_json_contract_shape():
    result = ThrowResult(
        notation="2d6+1",
        faces=(1, 5),
        modifier=1,
        total=7,
        seed=14333185781139156525,
    )
    assert as_dict(result) == {
        "kind": "roll",
        "notation": "2d6+1",
        "faces": [1, 5],
        "modifier": 1,
        "total": 7,
        "seed": "14333185781139156525",
    }


def test_as_dict_check_matches_json_contract_shape():
    result = CheckResult(
        faces=(1, 5),
        dice_total=6,
        modifiers=(
            Modifier(label="Difficulty (Difficult)", value=-2),
            Modifier(label="cover", value=-2),
        ),
        total=1,
        target=8,
        success=False,
        seed=14333185781139156525,
        provenance=_PACKAGED,
    )
    assert as_dict(result) == {
        "kind": "check",
        "faces": [1, 5],
        "dice_total": 6,
        "modifiers": [
            {"label": "Difficulty (Difficult)", "value": -2},
            {"label": "cover", "value": -2},
        ],
        "total": 1,
        "target": 8,
        "success": False,
        "seed": "14333185781139156525",
        "provenance": {
            "source": "packaged",
            "version": "2026.08.1",
            "files": [],
            "ignored": [],
        },
    }


def test_as_json_throw_uses_indent_two_and_unescaped_unicode():
    result = ThrowResult(notation="1d6", faces=(1,), modifier=0, total=1, seed=1)
    text = as_json(result)
    assert text == json.dumps(as_dict(result), indent=2, ensure_ascii=False) + "\n"


def test_as_json_check_uses_indent_two_and_unescaped_unicode():
    result = CheckResult(
        faces=(2, 5),
        dice_total=7,
        modifiers=(Modifier(label="Difficulty (Average)", value=0),),
        total=7,
        target=8,
        success=False,
        seed=1,
        provenance=_PACKAGED,
    )
    text = as_json(result)
    assert text == json.dumps(as_dict(result), indent=2, ensure_ascii=False) + "\n"


def test_as_json_ends_with_trailing_newline():
    result = ThrowResult(notation="1d6", faces=(1,), modifier=0, total=1, seed=1)
    assert as_json(result).endswith("\n")
    assert json.loads(as_json(result)) == as_dict(result)


# --- ValidationReport rendering (contracts/cli.md, contracts/json-output.md) ---

_WHOLE_FILE_PROBLEM = ValidationProblem(
    file="navy.toml",
    location="",
    found="invalid TOML at line 12, column 3",
    expected="a well-formed TOML document",
)

# Already in (file, location) order, as `validate_rules` guarantees.
_SORTED_PROBLEMS = (
    ValidationProblem(
        file="navy.toml",
        location="mustering-out.chash",
        found="an unrecognized key 'chash'",
        expected="one of: benefits, cash",
    ),
    ValidationProblem(
        file="navy.toml",
        location="tables.service.entries[2]",
        found="unrecognized skill name 'Vac Suit'",
        expected="a name in the skills registry",
    ),
    ValidationProblem(
        file="navy.toml",
        location="throws.survival.target",
        found="a string",
        expected="an integer",
    ),
    ValidationProblem(
        file="skills.toml",
        location="skills",
        found="no entries",
        expected="at least one",
    ),
)


def test_as_text_validation_report_valid_summary():
    report = ValidationReport(provenance=_PACKAGED, file_count=5, problems=())
    assert as_text(report) == (
        "Rules data is valid.\n" "  Files: 5\n" "  Rules: packaged (cetools 2026.08.1)\n"
    )


def test_as_text_validation_report_one_problem_per_line():
    report = ValidationReport(provenance=_PACKAGED, file_count=5, problems=_SORTED_PROBLEMS)
    text = as_text(report)
    lines = text.splitlines()
    assert (
        lines[0] == "navy.toml:mustering-out.chash: found an unrecognized key 'chash'; "
        "expected one of: benefits, cash"
    )
    assert (
        lines[1] == "navy.toml:tables.service.entries[2]: "
        "found unrecognized skill name 'Vac Suit'; expected a name in the skills registry"
    )
    assert lines[2] == "navy.toml:throws.survival.target: found a string; expected an integer"
    assert lines[3] == "skills.toml:skills: found no entries; expected at least one"


def test_as_text_validation_report_problems_precede_a_blank_line_then_the_summary():
    report = ValidationReport(provenance=_PACKAGED, file_count=5, problems=_SORTED_PROBLEMS)
    lines = as_text(report).splitlines()
    assert lines[4] == ""
    assert lines[5] == "Rules data is invalid."
    assert lines[6] == "  Files:    5"
    assert lines[7] == "  Problems: 4"
    assert lines[8] == "  Rules:    packaged (cetools 2026.08.1)"


def test_as_text_validation_report_file_as_a_whole_drops_location():
    report = ValidationReport(provenance=_PACKAGED, file_count=5, problems=(_WHOLE_FILE_PROBLEM,))
    lines = as_text(report).splitlines()
    assert lines[0] == (
        "navy.toml: found invalid TOML at line 12, column 3; "
        "expected a well-formed TOML document"
    )


def test_as_text_validation_report_preserves_the_given_problem_order():
    # The loader guarantees (file, location) order; rendering must not resort.
    reversed_problems = tuple(reversed(_SORTED_PROBLEMS))
    report = ValidationReport(provenance=_PACKAGED, file_count=5, problems=reversed_problems)
    lines = as_text(report).splitlines()
    assert lines[0].startswith("skills.toml:skills:")
    assert lines[1].startswith("navy.toml:throws.survival.target:")


def test_as_text_validation_report_ends_with_trailing_newline():
    report = ValidationReport(provenance=_PACKAGED, file_count=5, problems=())
    text = as_text(report)
    assert text.endswith("\n")
    assert not text.endswith("\n\n")


def test_as_dict_validation_report_valid_shape():
    report = ValidationReport(provenance=_PACKAGED, file_count=5, problems=())
    assert as_dict(report) == {
        "kind": "validation",
        "valid": True,
        "file_count": 5,
        "provenance": {
            "source": "packaged",
            "version": "2026.08.1",
            "files": [],
            "ignored": [],
        },
        "problems": [],
    }


def test_as_dict_validation_report_invalid_shape_and_key_order():
    report = ValidationReport(provenance=_PACKAGED, file_count=5, problems=_SORTED_PROBLEMS)
    payload = as_dict(report)
    assert payload["valid"] is False
    assert list(payload) == ["kind", "valid", "file_count", "provenance", "problems"]
    assert payload["problems"][0] == {
        "file": "navy.toml",
        "location": "mustering-out.chash",
        "found": "an unrecognized key 'chash'",
        "expected": "one of: benefits, cash",
    }
    assert [p["location"] for p in payload["problems"]] == [p.location for p in _SORTED_PROBLEMS]


def test_as_dict_validation_report_whole_file_problem_location_is_empty_string_not_absent():
    report = ValidationReport(provenance=_PACKAGED, file_count=5, problems=(_WHOLE_FILE_PROBLEM,))
    payload = as_dict(report)
    assert "location" in payload["problems"][0]
    assert payload["problems"][0]["location"] == ""


def test_as_json_validation_report_round_trips_through_json():
    report = ValidationReport(provenance=_PACKAGED, file_count=5, problems=_SORTED_PROBLEMS)
    text = as_json(report)
    assert json.loads(text) == as_dict(report)


# --- singledispatch fallbacks: an unregistered type is a detected condition ---


@pytest.mark.parametrize("render", [as_text, as_dict, as_json])
def test_rendering_an_unregistered_type_raises_a_cetools_error(render):
    # `as_text`, `as_dict`, and `as_json` are all public, so a caller can reach
    # the fallback. 001-dice-task-engine FR-029 is unconditional and each
    # fallback is a condition the code explicitly detects, so the miss is
    # signaled through the base class every other library error descends from.
    with pytest.raises(CetoolsError, match="object"):
        render(object())
