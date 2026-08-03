"""Check the docs against the code.

Documentation drifts faster than code, and nothing else tests it. Every check here
exists because the thing it catches actually happened:

1. `models.boost()` survived in CONTRIBUTING.md after a rename, and
   CAREER_REGISTRY / is_military_career survived a rewrite that deleted them.
2. Every README example called entry points that no longer existed, and one
   printed a whole dataclass where it meant to print a name.
3. CONTRIBUTING.md's module map silently omitted ranks.py the day it was added.
4. Spaced em-dashes accumulated against the project's punctuation rule.
5. The README's `cetools ship build` console block kept `Jump-1 Maneuver-1 Power-1` on the
   drives line after the code started printing `Drives: Jump-1 (A)  Maneuver-1 (A)  Power-1
   (A), 4t power plant`; nothing ran non-Python console examples to catch it.
6. British spellings accumulated in docstrings and comments while the tables, enums
   and prompts stayed American, so the same concept was spelled two ways depending
   on whether it was code or the prose above it.

Run: uv run python scripts/check_docs.py
"""

from __future__ import annotations

import contextlib
import importlib
import inspect
import io
import pkgutil
import re
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The docs we maintain.
DOCS = ("README.md", "CONTRIBUTING.md", "AGENTS.md")
PROSE = [ROOT / doc for doc in DOCS]
SOURCES = sorted((ROOT / "src").rglob("*.py"))
TESTS = sorted((ROOT / "tests").rglob("*.py"))
ENGINE = ROOT / "src" / "cetools" / "engine"
GLOSSARY = ROOT / "CONTEXT.md"

# Every Markdown file the repo owns, for the checks that apply to prose wherever
# it lives rather than to the three documents `check_symbols` reads. A dotted
# path component means a tool owns the file (`.venv`, `.pytest_cache`), so it is
# not ours to spell-check.
MARKDOWN = sorted(
    path
    for path in ROOT.rglob("*.md")
    if not any(part.startswith(".") for part in path.relative_to(ROOT).parts)
)

# The only command `check_readme_ship_console_examples` will run. See its docstring.
SHIP_CONSOLE_PREFIX = "uv run cetools ship"

# Backticked things that are prose, tooling, or SRD notation rather than cetools code.
NOT_CODE = {
    # tooling, files, git
    "uv",
    "uvx",
    "pytest",
    "black",
    "isort",
    "flake8",
    "pre-commit",
    "python",
    "bash",
    "text",
    "console",
    "markdown",
    "main",
    "HEAD",
    "cetools",
    "src",
    "tests",
    "docs",
    "scripts",
    "gh",
    # triage label vocabulary
    "wontfix",
    # SRD notation and pseudo-hex digits
    "Psi",
    "Edu",
    "Soc",
    "Str",
    "Dex",
    "End",
    "Int",
    "A",
    "B",
    "I",
    "O",
    # keywords a referee types at an interactive prompt, not names in the package
    "none",
    "revise",
    # standard-library methods used in prose
    "lower",
    "strip",
    "items",
    "keys",
    "values",
    "get",
}

# British spellings this project does not use, mapped to the American form.
# Keys are *stems*, not whole words, so a derived form is caught by the same
# entry: "catalogu" covers catalogue, catalogued and cataloguing, and "armour"
# covers armoured and unarmoured. This file is not itself scanned (the scan
# covers MARKDOWN, SOURCES and TESTS), so the keys below are not a violation of
# the rule they enforce.
#
# A stem has to be unambiguous before it is added here. "specialis" looks like a
# fine stem for "specialise" and would flag every one of this package's
# `specialist_skills`, which is already American. When in doubt, spell out the
# whole British form rather than reaching for a shorter stem.
BRITISH_SPELLINGS = {
    "armour": "armor",
    "behaviour": "behavior",
    "catalogu": "catalog",
    "fuelled": "fueled",
    "honour": "honor",
    "labelled": "labeled",
    "manoeuvre": "maneuver",
    "modelled": "modeled",
    "normalis": "normaliz",
    "recognis": "recogniz",
}

failures: list[str] = []


def public_names() -> set[str]:
    """Every public name cetools defines: modules, module-level names, and the
    attributes of its classes (a dataclass field is a name the docs can cite)."""
    names: set[str] = set()
    package = importlib.import_module("cetools")
    for info in pkgutil.walk_packages(package.__path__, "cetools."):
        try:
            module = importlib.import_module(info.name)
        except Exception as exc:  # pragma: no cover
            failures.append(f"cannot import {info.name}: {exc}")
            continue
        names.add(info.name.rsplit(".", 1)[-1])
        for attr, value in vars(module).items():
            if attr.startswith("_"):
                continue
            names.add(attr)
            if inspect.isclass(value):
                names.update(a for a in dir(value) if not a.startswith("_"))
                names.update(getattr(value, "__annotations__", {}))
    return names


def check_symbols(known: set[str]) -> None:
    """Every backticked identifier in the prose must exist in the package."""
    token = re.compile(r"`([A-Za-z_][A-Za-z0-9_.]*(?:\(\))?)`")
    for path in PROSE:
        if not path.exists():
            continue
        rel = path.relative_to(ROOT)
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for raw in token.findall(line):
                name = raw.removesuffix("()")
                if name in NOT_CODE or name.endswith((".md", ".toml", ".lock")):
                    continue
                if name.endswith(".py"):
                    if not list(ROOT.rglob(name)):
                        failures.append(f"{rel}:{lineno}: no such file `{name}`")
                    continue
                leaf = name.rsplit(".", 1)[-1]
                if leaf and leaf not in known and leaf not in NOT_CODE:
                    failures.append(f"{rel}:{lineno}: `{raw}` is not defined anywhere in cetools")


def check_readme_examples() -> None:
    """Every Python example in the README must run.

    The examples are one narrative: later blocks build on earlier imports, so they
    share a namespace and run in order, exactly as a reader would follow them.
    """
    blocks = re.findall(
        r"```python\n(.*?)```", (ROOT / "README.md").read_text(encoding="utf-8"), re.S
    )
    if not blocks:
        failures.append("README.md: no Python examples found; did the fences change?")
        return

    namespace: dict = {"__name__": "__readme__"}
    for i, block in enumerate(blocks, 1):
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(block, f"README.md[example {i}]", "exec"), namespace)
        except Exception as exc:
            failures.append(f"README.md: example {i} fails to run: {type(exc).__name__}: {exc}")


def check_readme_ship_console_examples() -> None:
    """Every `cetools ship` console example in the README must match real output.

    `check_readme_examples` runs the Python blocks; a `console` block has no such
    check, so the drives line (`Jump-1 Maneuver-1 Power-1`) drifted silently after
    the drives-line format changed until someone ran the command by hand. This
    closes that gap for `cetools ship` invocations specifically.

    Only the exact `$ uv run cetools ship ` prefix is run. This check executes what
    the README says, so a looser match would let any future README edit run any
    command in CI; the prefix keeps the executed program pinned to this CLI.
    """
    prefix = "$ " + SHIP_CONSOLE_PREFIX + " "
    blocks = re.findall(
        r"```console\n(.*?)```", (ROOT / "README.md").read_text(encoding="utf-8"), re.S
    )
    for block in blocks:
        lines = block.splitlines()
        if not lines or not lines[0].startswith(prefix):
            if lines and lines[0].startswith("$ ") and "cetools ship" in lines[0]:
                failures.append(
                    f"README.md: `{lines[0][2:]}` is not checked; a `cetools ship` console "
                    f"block must invoke it as `{SHIP_CONSOLE_PREFIX} ...`"
                )
            continue
        command = SHIP_CONSOLE_PREFIX.split() + shlex.split(lines[0][len(prefix) :])
        expected = "\n".join(lines[1:]).rstrip("\n")
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        actual = result.stdout.rstrip("\n")
        if actual != expected:
            failures.append(
                f"README.md: `{lines[0][2:]}` output does not match the documented console block\n"
                f"    expected:\n{expected}\n    actual:\n{actual}"
            )


def check_module_map() -> None:
    """CONTRIBUTING.md's module map must name every engine module.

    Only the tree diagram counts: the prose elsewhere cites `tests/test_foo.py` as
    an example of the mirroring rule, and that is not a claim about a real file.
    """
    tree = [
        line
        for line in (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8").splitlines()
        if "──" in line
    ]
    listed = set(re.findall(r"([a-z_]+\.py)", "\n".join(tree)))
    actual = {p.name for p in ENGINE.glob("*.py") if p.name != "__init__.py"}
    for missing in sorted(actual - listed):
        failures.append(f"CONTRIBUTING.md: module map omits engine/{missing}")
    for extra in sorted(listed - actual):
        if not list(ROOT.rglob(extra)):
            failures.append(f"CONTRIBUTING.md: module map names {extra}, which does not exist")


def check_punctuation() -> None:
    """Em-dashes and en-dashes are tight: no leading or trailing spaces.

    Deliberately narrower than `check_spelling`, which sweeps every Markdown file
    the repo owns. `docs/agents/` is seeded from a skill's own templates and
    carries spaced dashes from them; adopting the punctuation rule there means
    editing generated scaffolding, which is a decision on its own rather than a
    consequence of this check.
    """
    for path in PROSE + SOURCES + [GLOSSARY]:
        if not path.exists():
            continue
        rel = path.relative_to(ROOT)
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r" [—–] ", line):
                failures.append(f"{rel}:{lineno}: spaced em/en-dash; tighten it or use a comma")


def check_spelling() -> None:
    """Spelling is American English, in prose as much as in identifiers.

    This project's docstrings are long and expository, so most of its prose lives
    in the source rather than in the docs, and that is where the British forms
    collected. Tests are scanned too: a test *name* is prose a reader greps for,
    and `catalogue_names` was a local variable before this check existed.

    Scans every Markdown file the repo owns rather than the three `check_symbols`
    reads, because a spelling can drift back anywhere prose lives—`docs/agents/`
    included, which is edited by hand even though a skill seeds it.
    """
    for path in MARKDOWN + SOURCES + TESTS:
        if not path.exists():
            continue
        rel = path.relative_to(ROOT)
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            lowered = line.lower()
            for british, american in BRITISH_SPELLINGS.items():
                if british in lowered:
                    failures.append(
                        f"{rel}:{lineno}: British spelling {british!r}; this project "
                        f"uses {american!r}"
                    )


def main() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    check_symbols(public_names())
    check_readme_examples()
    check_readme_ship_console_examples()
    check_module_map()
    check_punctuation()
    check_spelling()

    if failures:
        print(f"{len(failures)} docs problem(s):\n", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1

    print(
        "docs OK: symbols resolve, README examples run, `cetools ship` console blocks match, "
        "module map complete, dashes tight, spelling American"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
