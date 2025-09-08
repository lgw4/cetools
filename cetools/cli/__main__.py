"""Command-line interface for Cepheus Engine tools."""

import typer

app = typer.Typer(
    name="cetools",
    help="Tools for use with the Cepheus Engine SRD tabletop role-playing game",
    add_completion=False,
)


@app.callback()
def callback():
    """
    Cepheus Engine Tools - Utilities for the Cepheus Engine tabletop RPG.
    """
    pass


@app.command()
def version():
    """Show the version of CETools."""
    from cetools import __version__

    typer.echo(f"CETools version {__version__}")


if __name__ == "__main__":
    app()

# This file contains GitHub Copilot generated content.
