"""Guard `.github/workflows/release.yaml` against
specs/005-release-publishing/contracts/release-workflow.md.

No YAML parser is installed and none is added for a single file (Principle
VI); this reads the workflow as text and matches with anchored regexes, the
way `tests/guards/test_python_support.py` already reads `ci.yaml`.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yaml"


def _text() -> str:
    assert WORKFLOW.is_file(), f"{WORKFLOW} does not exist"
    return WORKFLOW.read_text(encoding="utf-8")


# --- prohibitions --------------------------------------------------------


def test_triggers_only_on_a_v_tagged_push():
    text = _text()
    match = re.search(r"^on:\n(.*?)^\S", text, re.MULTILINE | re.DOTALL)
    trigger_block = match.group(1) if match else text
    assert re.search(r"push:\s*\n\s*tags:\s*\n\s*-\s*'v\*'", trigger_block), trigger_block
    assert "workflow_dispatch" not in trigger_block
    assert "schedule" not in trigger_block
    assert "release:" not in trigger_block


def test_grants_exactly_the_three_required_permissions():
    text = _text()
    match = re.search(r"^permissions:\n((?:[ \t]+\S.*\n)+)", text, re.MULTILINE)
    assert match, "no top-level permissions block"
    block = match.group(1)
    granted = dict(re.findall(r"(\w[\w-]*):\s*(\w+)", block))
    assert granted == {
        "contents": "write",
        "id-token": "write",
        "attestations": "write",
    }, granted


def test_no_step_tolerates_its_own_failure():
    assert "continue-on-error" not in _text()


def test_never_edits_or_uploads_to_an_existing_release():
    text = _text()
    for forbidden in (
        "gh release edit",
        "gh release upload",
        "--clobber",
        "--draft",
        "--generate-notes",
    ):
        assert forbidden not in text, f"{forbidden!r} must not appear in {WORKFLOW}"


# --- required steps --------------------------------------------------------


def test_checks_out_the_pushed_tag_not_a_branch_tip():
    text = _text()
    assert "actions/checkout@" in text
    # The checkout step must not pin `ref:` to a branch; the default checks
    # out whatever triggered the run, which for a `push: tags:` trigger is
    # the tag itself.
    checkout_block_match = re.search(r"actions/checkout@\S+\n((?:\s{4,}.*\n)*)", text)
    block = checkout_block_match.group(1) if checkout_block_match else ""
    assert "ref:" not in block or "GITHUB_REF_NAME" in block or "refs/heads" not in block


def test_invokes_the_preflight_script():
    text = _text()
    assert re.search(
        r"scripts/release-preflight\.sh[^\n]*GITHUB_REF_NAME[^\n]*pyproject\.toml"
        r"[^\n]*CHANGELOG\.md",
        text,
    ), "release-preflight.sh must be invoked with the ref name, pyproject.toml, CHANGELOG.md"


def test_runs_pytest_with_no_narrowing():
    text = _text()
    match = re.search(r"run:\s*uv run pytest([^\n]*)", text)
    assert match, "no `uv run pytest` step"
    trailing = match.group(1)
    for forbidden in (" -m", " --deselect", " -k", " tests/"):
        assert forbidden not in trailing, f"pytest invocation narrows the run: {trailing!r}"


def test_assembles_notes_from_the_changelog_extractor_then_the_footer():
    text = _text()
    extractor_match = re.search(r"scripts/changelog-section\.sh", text)
    footer_match = re.search(r"\.github/release-footer\.md", text)
    assert extractor_match, "release notes are not assembled from changelog-section.sh"
    assert footer_match, "release notes do not append .github/release-footer.md"
    assert (
        extractor_match.start() < footer_match.start()
    ), "the footer must be appended after the changelog section body, not before"


def test_publishes_with_gh_release_create_and_verify_tag():
    text = _text()
    assert "gh release create" in text
    assert "--verify-tag" in text
