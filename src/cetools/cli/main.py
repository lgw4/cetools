import typer

app = typer.Typer()


@app.callback()
def main() -> None:
    """Cepheus Engine character generation tools."""
