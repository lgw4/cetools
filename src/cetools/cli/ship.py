from pathlib import Path
from typing import Annotated

import typer

from cetools.engine.ships import build_ship, dump_design, load_design, render_sheet

app = typer.Typer()


@app.command("build")
def build(
    file: Annotated[Path, typer.Argument(help="Path to a TOML ship design file.")],
    toml: Annotated[
        bool, typer.Option("--toml", help="Emit round-trippable TOML instead of a sheet.")
    ] = False,
    out: Annotated[
        Path | None, typer.Option("--out", help="Write output to a file instead of stdout.")
    ] = None,
) -> None:
    """Build a ship from a TOML design file and print its sheet."""
    if out is not None and not toml:
        typer.echo("--out requires --toml", err=True)
        raise typer.Exit(1)

    try:
        design = load_design(file)
        ship = build_ship(design)
    except OSError:
        typer.echo(f"cannot read design file: {file}", err=True)
        raise typer.Exit(1)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)

    output = dump_design(ship.design) if toml else render_sheet(ship)

    if out is not None:
        out.write_text(output)
    else:
        typer.echo(output)
