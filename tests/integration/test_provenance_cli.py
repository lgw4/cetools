"""The overridden provenance text block, through `check` and `validate` alike:
the file column padded to the longest basename, the disposition column padded
to the longest disposition, effective files first sorted by name then ignored
files sorted by name, an ignored line ending at the disposition, and an
override holding only ignored files still reading `packaged` while listing
them (contracts/cli.md, FR-032a, FR-035).
"""

from pathlib import Path

from typer.testing import CliRunner

from cetools.cli import app

runner = CliRunner()

NAVY = (
    Path(__file__).resolve().parents[2] / "src" / "cetools" / "data" / "careers" / "navy.toml"
).read_text(encoding="utf-8")


def _mixed_override(tmp_path):
    """navy.toml replaced, scouts.toml added, notes.md ignored: three
    basenames of different lengths and every disposition in one location.
    """
    (tmp_path / "navy.toml").write_text(
        NAVY.replace("target = 5", "target = 9", 1), encoding="utf-8"
    )
    (tmp_path / "scouts.toml").write_text(
        NAVY.replace('name = "Navy"', 'name = "Scouts"'), encoding="utf-8"
    )
    (tmp_path / "notes.md").write_text("just some notes", encoding="utf-8")
    return tmp_path


def _rules_block(stdout: str) -> list[str]:
    lines = stdout.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip().startswith("Rules:"))
    return lines[start:]


def test_check_reports_the_mixed_provenance_block(tmp_path):
    _mixed_override(tmp_path)
    result = runner.invoke(app, ["check", "--rules-data", str(tmp_path), "--seed", "1"])
    assert result.exit_code == 0
    block = _rules_block(result.stdout)
    assert block[0].strip().startswith("Rules: overridden")
    assert block[1].strip().startswith("navy.toml")
    assert block[2].strip().startswith("scouts.toml")
    assert block[3].strip() == "notes.md      ignored"


def test_validate_reports_the_mixed_provenance_block(tmp_path):
    _mixed_override(tmp_path)
    result = runner.invoke(app, ["validate", str(tmp_path)])
    assert result.exit_code == 0
    block = _rules_block(result.stdout)
    assert block[0].strip().startswith("Rules: overridden")
    assert block[1].strip().startswith("navy.toml")
    assert block[2].strip().startswith("scouts.toml")
    assert block[3].strip() == "notes.md      ignored"


def test_file_column_is_padded_to_the_longest_basename(tmp_path):
    _mixed_override(tmp_path)
    result = runner.invoke(app, ["validate", str(tmp_path)])
    block = _rules_block(result.stdout)
    file_lines = [line for line in block[1:] if line.strip()]
    # "scouts.toml" (11 chars) is the longest basename present; every file
    # column, including the shorter "navy.toml" and "notes.md", pads to it.
    prefix_width = len("    ") + len("scouts.toml")
    for line in file_lines:
        assert line[prefix_width : prefix_width + 3] == "   "


def test_disposition_column_is_padded_to_the_longest_disposition(tmp_path):
    _mixed_override(tmp_path)
    result = runner.invoke(app, ["validate", str(tmp_path)])
    block = _rules_block(result.stdout)
    navy_line = next(line for line in block if "navy.toml" in line)
    scouts_line = next(line for line in block if "scouts.toml" in line)
    # "replaced" and "added" both pad to "replaced"'s width (8) before the
    # fingerprint column starts.
    navy_disposition = navy_line.split("navy.toml", 1)[1].strip().split("  ", 1)[0]
    scouts_disposition = scouts_line.split("scouts.toml", 1)[1].strip().split("  ", 1)[0]
    assert navy_disposition.rstrip() == "replaced"
    assert scouts_disposition.rstrip() == "added"
    fingerprint_column = navy_line.index("sha256:")
    assert scouts_line.index("sha256:") == fingerprint_column


def test_effective_files_are_listed_before_ignored_files_each_sorted_by_name(tmp_path):
    _mixed_override(tmp_path)
    result = runner.invoke(app, ["validate", str(tmp_path)])
    block = _rules_block(result.stdout)
    names_in_order = [line.strip().split()[0] for line in block[1:] if line.strip()]
    assert names_in_order == ["navy.toml", "scouts.toml", "notes.md"]


def test_an_ignored_line_ends_at_the_disposition(tmp_path):
    _mixed_override(tmp_path)
    result = runner.invoke(app, ["validate", str(tmp_path)])
    block = _rules_block(result.stdout)
    ignored_line = next(line for line in block if "notes.md" in line)
    assert ignored_line.strip().endswith("ignored")
    assert "sha256:" not in ignored_line


def test_an_override_holding_only_ignored_files_still_reads_packaged_and_lists_them(tmp_path):
    (tmp_path / "notes.md").write_text("just some notes", encoding="utf-8")
    result = runner.invoke(app, ["validate", str(tmp_path)])
    assert result.exit_code == 0
    block = _rules_block(result.stdout)
    assert block[0].strip().startswith("Rules: packaged")
    assert block[1].strip() == "notes.md   ignored"
