from importlib.metadata import version
from typing import Optional

import typer

from cetools.dice import Roller, throw
from cetools.errors import CetoolsError
from cetools.render import as_text

app = typer.Typer(add_completion=False)


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
    typer.echo(as_text(result), nl=False)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
