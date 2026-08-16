import re
from importlib.metadata import version
from typing import List, Optional

import typer

from cetools.dice import Roller, throw
from cetools.errors import CetoolsError, RulesDataError
from cetools.render import _problem_line, as_json, as_text
from cetools.rules import load_rules, validate_rules
from cetools.tasks import Modifier
from cetools.tasks import check as check_task

app = typer.Typer(add_completion=False)

_DM_VALUE = re.compile(r"^[+-]?[0-9]+$")


def _parse_dm(raw: str) -> Modifier:
    if "=" not in raw:
        raise typer.BadParameter(f"--dm must be label=value, got {raw!r}")
    label, _, value = raw.rpartition("=")
    label = label.strip()
    if not label:
        raise typer.BadParameter(f"--dm label must be non-empty, got {raw!r}")
    if not _DM_VALUE.match(value):
        raise typer.BadParameter(f"--dm value must be an integer, got {raw!r}")
    return Modifier(label=label, value=int(value))


def _version_callback(show_version: bool) -> None:
    if show_version:
        typer.echo(version("cetools"))
        raise typer.Exit()


@app.callback()
def _cetools(
    version_flag: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the package version and exit.",
    ),
) -> None:
    pass


@app.command()
def roll(
    notation: str = typer.Argument(
        ..., metavar="NOTATION", help="Dice notation, e.g. 2d6+1, d66."
    ),
    seed: Optional[str] = typer.Option(None, "--seed", help="Integer or arbitrary text."),
    json_output: bool = typer.Option(
        False, "--json", help="Emit machine-readable output instead of text."
    ),
) -> None:
    try:
        result = throw(Roller(seed), notation)
    except CetoolsError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    typer.echo(as_json(result) if json_output else as_text(result), nl=False)


@app.command()
def check(
    difficulty: Optional[str] = typer.Option(
        None,
        "--difficulty",
        help="Difficulty name from the ladder. Default: the zero-modifier rung.",
    ),
    characteristic: Optional[int] = typer.Option(
        None, "--characteristic", help="Characteristic score. Omitted: no characteristic modifier."
    ),
    skill: Optional[int] = typer.Option(
        None, "--skill", help="Skill level. Omitted: untrained (unskilled penalty applies)."
    ),
    dm: List[str] = typer.Option(
        [], "--dm", help='Repeatable labeled situational modifier, "label=value".'
    ),
    seed: Optional[str] = typer.Option(None, "--seed", help="Integer or arbitrary text."),
    json_output: bool = typer.Option(
        False, "--json", help="Emit machine-readable output instead of text."
    ),
) -> None:
    modifiers = tuple(_parse_dm(raw) for raw in dm)
    try:
        rules = load_rules()
        result = check_task(
            Roller(seed),
            difficulty=difficulty,
            characteristic=characteristic,
            skill=skill,
            modifiers=modifiers,
            rules=rules,
        )
    except CetoolsError as exc:
        if isinstance(exc, RulesDataError) and exc.problems:
            for problem in exc.problems:
                typer.echo(_problem_line(problem), err=True)
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(code=1)
    typer.echo(as_json(result) if json_output else as_text(result), nl=False)


@app.command()
def validate(
    json_output: bool = typer.Option(
        False, "--json", help="Emit machine-readable output instead of text."
    ),
) -> None:
    report = validate_rules()
    typer.echo(as_json(report) if json_output else as_text(report), nl=False)
    if not report.valid:
        raise typer.Exit(code=1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
