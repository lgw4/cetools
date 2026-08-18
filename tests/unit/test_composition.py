"""Composition: how an override location combines with the packaged data set,
at library level and before any command exists (FR-028, FR-029, FR-032,
FR-032a, FR-032b).
"""

import os
import shutil
from pathlib import Path

import pytest

from cetools.errors import RulesDataError
from cetools.provenance import Disposition
from cetools.rules import load_rules, validate_rules

NAVY = Path(__file__).resolve().parents[2] / "src" / "cetools" / "data" / "careers" / "navy.toml"


def test_a_basename_matching_a_packaged_file_replaces_it(tmp_path):
    override = tmp_path / "navy.toml"
    override.write_text(
        NAVY.read_text(encoding="utf-8").replace("target = 5", "target = 9"), encoding="utf-8"
    )
    rules = load_rules(override)
    assert rules.careers["navy"].throws["survival"].target == 9
    assert len(rules.provenance.files) == 1
    assert rules.provenance.files[0].file == "navy.toml"
    assert rules.provenance.files[0].disposition is Disposition.REPLACED


def test_a_basename_matching_nothing_is_admitted_as_an_addition(tmp_path):
    override = tmp_path / "scouts.toml"
    text = NAVY.read_text(encoding="utf-8").replace('name = "Navy"', 'name = "Scouts"')
    override.write_text(text, encoding="utf-8")
    rules = load_rules(override)
    assert "navy" in rules.careers
    assert "scouts" in rules.careers
    assert rules.provenance.files[0].disposition is Disposition.ADDED


def test_a_non_toml_file_is_recorded_as_ignored_without_failing_the_load(tmp_path):
    (tmp_path / "notes.md").write_text("just some notes", encoding="utf-8")
    report = validate_rules(tmp_path)
    assert report.valid
    assert report.provenance.ignored == ("notes.md",)


def test_a_dot_prefixed_file_is_passed_over_silently(tmp_path):
    (tmp_path / ".DS_Store").write_text("binary junk", encoding="utf-8")
    report = validate_rules(tmp_path)
    assert report.valid
    assert report.provenance.ignored == ()
    assert report.provenance.is_packaged


def test_a_dot_prefixed_file_named_as_the_location_itself_composes(tmp_path):
    # T101. FR-032b's carve-out is drawn at authorship — "a file the author
    # did not write is not a mistake the author needs told about" — and a path
    # typed on the command line is not such a file. Passing it over made
    # `cetools validate override/.navy.toml` report `Rules data is valid.`,
    # `Rules: packaged`, and exit 0 having composed nothing, which is verbatim
    # the mistyped-path-that-appears-to-succeed failure FR-028 exists to
    # remove and is how a `/dev/null` location was settled (FR-040a).
    hidden = tmp_path / ".scouts.toml"
    hidden.write_text(
        NAVY.read_text(encoding="utf-8").replace('name = "Navy"', 'name = "Scouts"'),
        encoding="utf-8",
    )
    report = validate_rules(hidden)
    assert report.valid, report.problems
    assert not report.provenance.is_packaged
    assert [(fp.file, fp.disposition) for fp in report.provenance.files] == [
        (".scouts.toml", Disposition.ADDED)
    ]
    assert load_rules(hidden).careers[".scouts"].name == "Scouts"


def test_a_dot_prefixed_non_toml_file_named_as_the_location_is_reported_ignored(tmp_path):
    # The other half of the same decision: a directly named location that
    # cannot be rules data is named rather than passed over, so nothing an
    # author typed produces a run that succeeds having done nothing.
    junk = tmp_path / ".DS_Store"
    junk.write_text("binary junk", encoding="utf-8")
    report = validate_rules(junk)
    assert report.valid
    assert report.provenance.ignored == (".DS_Store",)


def test_a_dot_prefixed_file_found_by_walking_a_directory_is_still_passed_over(tmp_path):
    # The control case for the decision above: the carve-out still applies to
    # everything the walk finds, so a `.DS_Store` beside a house rule neither
    # fails the load nor clutters the report.
    (tmp_path / ".DS_Store").write_text("binary junk", encoding="utf-8")
    (tmp_path / ".navy.toml").write_bytes(NAVY.read_bytes())
    report = validate_rules(tmp_path)
    assert report.valid
    assert report.provenance.ignored == ()
    assert report.provenance.is_packaged


def test_a_dot_prefixed_file_with_a_wrong_extension_still_appears_nowhere(tmp_path):
    (tmp_path / ".hidden.yaml").write_text("junk", encoding="utf-8")
    report = validate_rules(tmp_path)
    assert report.valid
    assert report.provenance.ignored == ()


def test_an_override_holding_only_ignored_files_still_composes_as_packaged(tmp_path):
    (tmp_path / "notes.md").write_text("just some notes", encoding="utf-8")
    report = validate_rules(tmp_path)
    assert report.valid
    assert report.provenance.is_packaged
    assert report.provenance.ignored == ("notes.md",)


def test_an_existing_but_empty_location_composes_as_packaged(tmp_path):
    report = validate_rules(tmp_path)
    assert report.valid
    assert report.provenance.is_packaged
    assert report.provenance.files == ()
    assert report.provenance.ignored == ()


def test_a_location_that_does_not_exist_is_a_usage_error_naming_it(tmp_path):
    missing = tmp_path / "nope"
    with pytest.raises(RulesDataError, match="nope"):
        validate_rules(missing)


def test_a_location_that_is_neither_a_file_nor_a_directory_is_a_usage_error_naming_it(tmp_path):
    # The same silent failure FR-028 removes for a mistyped path: a location
    # that cannot hold rules data must not compose to the packaged set while
    # appearing to have put the author's house rules in force.
    fifo = tmp_path / "pipe"
    os.mkfifo(fifo)
    with pytest.raises(RulesDataError, match="pipe"):
        validate_rules(fifo)


def test_a_broken_symlink_in_an_override_is_reported_rather_than_passed_over(tmp_path):
    (tmp_path / "navy.toml").symlink_to(tmp_path / "nowhere.toml")
    report = validate_rules(tmp_path)
    assert not report.valid
    navy_problems = [p for p in report.problems if p.file == "navy.toml"]
    assert len(navy_problems) == 1
    assert navy_problems[0].location == ""
    assert "read" in navy_problems[0].found


def test_a_file_behind_a_symlinked_directory_is_collected(tmp_path):
    # `Path.rglob` defaults to `recurse_symlinks=False`, so a whole subtree
    # reached through a symlinked directory composed nothing while the run
    # reported `packaged` and exited 0 — the author's house rules entirely
    # out of force while the run appears to succeed, which is verbatim the
    # failure FR-028 exists to remove.
    real = tmp_path / "real"
    real.mkdir()
    shutil.copy(NAVY, real / "navy.toml")
    override = tmp_path / "override"
    override.mkdir()
    (override / "linked").symlink_to(real, target_is_directory=True)
    report = validate_rules(override)
    assert report.valid, report.problems
    assert [fp.file for fp in report.provenance.files] == ["navy.toml"]


def test_a_directory_reached_twice_is_walked_once(tmp_path):
    # The `seen` set is what stops a symlink pointing at its own ancestor from
    # walking until the kernel runs out of path — a regression there hangs
    # rather than fails, which is no signal at all. Its other job is
    # observable: a link beside the directory it points at yielded every file
    # beneath it twice, and two override files sharing a basename is a
    # problem, so this fails rather than hangs if the guard goes. It also pins
    # the identity check running *before* `iterdir`, not after it (T111).
    real = tmp_path / "real"
    real.mkdir()
    shutil.copy(NAVY, real / "navy.toml")
    (tmp_path / "alias").symlink_to(real, target_is_directory=True)
    report = validate_rules(tmp_path)
    assert report.valid, report.problems
    assert [fp.file for fp in report.provenance.files] == ["navy.toml"]


def test_a_symlink_cycle_terminates(tmp_path):
    inner = tmp_path / "inner"
    inner.mkdir()
    shutil.copy(NAVY, inner / "navy.toml")
    (inner / "up").symlink_to(tmp_path, target_is_directory=True)
    report = validate_rules(tmp_path)
    assert report.valid, report.problems
    assert [fp.file for fp in report.provenance.files] == ["navy.toml"]


def test_provenance_files_arrive_sorted_by_composition_key(tmp_path):
    # data-model.md guarantees `Provenance.files` is sorted by `file`. The line
    # that appeared to provide it was dead — the list is built from
    # `sorted(candidates.items())` — so removing the sort that actually does
    # would have looked safe. Written into the override in reverse order, at
    # differing depths, so an implementation relying on directory order fails.
    deep = tmp_path / "z" / "deeper"
    deep.mkdir(parents=True)
    shutil.copy(NAVY, deep / "navy.toml")
    for stem in ("scouts", "army", "marines"):
        (tmp_path / f"{stem}.toml").write_text(
            NAVY.read_text(encoding="utf-8").replace('name = "Navy"', f'name = "{stem}"'),
            encoding="utf-8",
        )
    report = validate_rules(tmp_path)
    assert report.valid, report.problems
    names = [fp.file for fp in report.provenance.files]
    assert names == sorted(names)
    assert names == ["army.toml", "marines.toml", "navy.toml", "scouts.toml"]


@pytest.mark.skipif(
    hasattr(os, "geteuid") and os.geteuid() == 0,
    reason="root lists a mode-000 directory regardless of its mode",
)
def test_a_subdirectory_that_cannot_be_listed_is_reported_rather_than_passed_over(tmp_path):
    # `rglob` swallows the `OSError`, so an unlistable subtree was the one
    # traversal failure that got exactly the treatment `_collect_entry`'s
    # comment rejects for a single unreadable file (FR-020a, FR-022).
    closed = tmp_path / "closed"
    closed.mkdir()
    shutil.copy(NAVY, closed / "navy.toml")
    closed.chmod(0o000)
    try:
        report = validate_rules(tmp_path)
    finally:
        closed.chmod(0o700)
    assert not report.valid
    assert any("closed" in p.file and p.location == "" for p in report.problems)


@pytest.mark.skipif(
    hasattr(os, "geteuid") and os.geteuid() == 0,
    reason="root lists a mode-000 directory regardless of its mode",
)
def test_an_override_root_that_cannot_be_listed_is_reported(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    shutil.copy(NAVY, root / "navy.toml")
    root.chmod(0o000)
    try:
        report = validate_rules(root)
    finally:
        root.chmod(0o700)
    assert not report.valid
    assert any(p.location == "" and "listed" in p.found for p in report.problems)


def test_a_dot_prefixed_directory_is_passed_over_with_everything_under_it(tmp_path):
    # FR-032b draws its line at authorship, and a git checkout is the obvious
    # way to share a rule set: `.git/HEAD` and `.git/config` were written by
    # no author, and a report full of them is a report that stops being read.
    git = tmp_path / ".git"
    git.mkdir()
    (git / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (git / "config").write_text("[core]\n", encoding="utf-8")
    (git / "hooks").mkdir()
    (git / "hooks" / "applypatch-msg.sample").write_text("#!/bin/sh\n", encoding="utf-8")
    report = validate_rules(tmp_path)
    assert report.valid
    assert report.provenance.ignored == ()
    assert report.provenance.is_packaged


def test_a_toml_file_under_a_dot_prefixed_directory_does_not_compose(tmp_path):
    # The other half: following the letter of FR-032b let `.hidden/navy.toml`
    # replace the packaged Navy career and be reported as `replaced`.
    hidden = tmp_path / ".hidden"
    hidden.mkdir()
    shutil.copy(NAVY, hidden / "navy.toml")
    report = validate_rules(tmp_path)
    assert report.valid
    assert report.provenance.files == ()
    assert report.provenance.is_packaged


def test_every_ignored_file_is_named_not_every_distinct_basename(tmp_path):
    # FR-035 requires any file FR-032a marks ignored to be named,
    # unconditionally, and FR-032a's whole bargain is that admitting an
    # unrecognized filename is paid for by reporting it. Accumulating
    # basenames in a set reported one of two author-written files under the
    # other's name, which is not reporting it.
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "notes.md").write_text("first", encoding="utf-8")
    (tmp_path / "b" / "notes.md").write_text("second", encoding="utf-8")
    report = validate_rules(tmp_path)
    assert report.valid
    assert report.provenance.ignored == ("a/notes.md", "b/notes.md")


def test_two_override_files_sharing_a_basename_is_a_problem_naming_both(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    shutil.copy(NAVY, tmp_path / "a" / "navy.toml")
    shutil.copy(NAVY, tmp_path / "b" / "navy.toml")
    report = validate_rules(tmp_path)
    assert not report.valid
    combined = " ".join(f"{p.file} {p.found} {p.expected}" for p in report.problems)
    assert "a/navy.toml" in combined or "a" + "\\" + "navy.toml" in combined
    assert "b/navy.toml" in combined or "b" + "\\" + "navy.toml" in combined


def test_a_replacement_at_any_depth_within_the_override_is_positioned_by_basename(tmp_path):
    nested = tmp_path / "some" / "nested" / "path"
    nested.mkdir(parents=True)
    override = nested / "navy.toml"
    override.write_text(
        NAVY.read_text(encoding="utf-8").replace("target = 5", "target = 1"), encoding="utf-8"
    )
    rules = load_rules(override.parent)
    assert rules.careers["navy"].throws["survival"].target == 1
    assert rules.provenance.files[0].disposition is Disposition.REPLACED


def test_a_single_file_override_composes_exactly_as_a_directory_holding_it_alone(tmp_path):
    (tmp_path / "navy.toml").write_bytes(NAVY.read_bytes())
    directory_result = validate_rules(tmp_path)
    file_result = validate_rules(tmp_path / "navy.toml")
    assert directory_result.valid == file_result.valid
    # The content is byte-identical to the packaged file, and the spec's Edge
    # Case requires it to be recorded as overridden all the same, "because
    # provenance describes where content came from, not whether it differs".
    # Comparing the two tuples alone holds vacuously if both are empty, so an
    # implementation that compared content and composed this as packaged would
    # satisfy it (FR-035).
    assert [(fp.file, fp.disposition) for fp in directory_result.provenance.files] == [
        ("navy.toml", Disposition.REPLACED)
    ]
    assert directory_result.provenance.files == file_result.provenance.files
