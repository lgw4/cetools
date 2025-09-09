"""Command-line interface for Cepheus Engine tools."""

import typer

# Create the main application
app = typer.Typer(
    name="cetools",
    help="Tools for use with the Cepheus Engine SRD tabletop role-playing game",
    add_completion=False,
)

# Create subcommands for organized command structure
character_app = typer.Typer(
    name="character",
    help="Character generation and management commands",
    add_completion=False,
)

npc_app = typer.Typer(
    name="npc",
    help="NPC generation commands",
    add_completion=False,
)

encounter_app = typer.Typer(
    name="encounter",
    help="Encounter generation and balancing commands",
    add_completion=False,
)

world_app = typer.Typer(
    name="world",
    help="World and subsector generation commands",
    add_completion=False,
)

# Add subcommands to main app
app.add_typer(character_app, name="character")
app.add_typer(npc_app, name="npc")
app.add_typer(encounter_app, name="encounter")
app.add_typer(world_app, name="world")


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


@app.command()
def roll(
    expression: str = typer.Argument(..., help="Dice expression to roll (e.g., 2d6+3, d66)"),
    seed: int = typer.Option(None, "--seed", help="Random seed for reproducible results"),
    advantage: bool = typer.Option(False, "--adv", help="Roll with advantage"),
    disadvantage: bool = typer.Option(False, "--dis", help="Roll with disadvantage"),
):
    """Parse dice expressions and output detailed roll breakdown."""
    try:
        from cetools.core import DiceExpressionError, roll_dice

        result = roll_dice(expression, seed=seed, advantage=advantage, disadvantage=disadvantage)

        # Display the roll result
        typer.echo(f"Rolling {expression}")
        if seed is not None:
            typer.echo(f"Seed: {seed}")
        if advantage:
            typer.echo("Rolling with advantage")
        if disadvantage:
            typer.echo("Rolling with disadvantage")

        typer.echo(f"Result: {result.breakdown}")

        # Show D66 composed value if applicable
        if result.d66_composed is not None:
            typer.echo(f"D66 Value: {result.d66_composed}")

    except DiceExpressionError as ex:
        typer.echo(f"Error: {ex}", err=True)
        raise typer.Exit(2)
    except Exception as ex:
        typer.echo(f"Unexpected error: {ex}", err=True)
        raise typer.Exit(10)


@app.command()
def srlookup(
    term: str = typer.Argument(..., help="Term to search for in the SRD"),
    format_type: str = typer.Option("text", "--format", help="Output format (text or json)"),
):
    """Search local SRD index for game terms and output references."""
    # Implementation placeholder - will be implemented in later phases
    typer.echo(f"Looking up '{term}' in SRD...")
    typer.echo(f"Output format: {format_type}")
    typer.echo("SRD lookup functionality not yet implemented")


# Character commands
@character_app.command("create")
def character_create(
    template: str = typer.Option("traveller", "--template", help="Character template to use"),
    name: str = typer.Option(None, "--name", help="Character name"),
    export_format: str = typer.Option(None, "--export", help="Export format (json, yaml, csv)"),
):
    """Create a PC or NPC from SRD rules and templates."""
    # Implementation placeholder - will be implemented in later phases
    typer.echo(f"Creating character with template '{template}'...")
    if name:
        typer.echo(f"Character name: {name}")
    if export_format:
        typer.echo(f"Export format: {export_format}")
    typer.echo("Character creation functionality not yet implemented")


# NPC commands
@npc_app.command("gen")
def npc_generate(
    level: int = typer.Option(None, "--level", help="NPC level/experience"),
    template: str = typer.Option(None, "--template", help="NPC template to use"),
    export_format: str = typer.Option(None, "--export", help="Export format (json, yaml, csv)"),
):
    """Generate NPC stats, gear, and a short description."""
    # Implementation placeholder - will be implemented in later phases
    typer.echo("Generating NPC...")
    if level is not None:
        typer.echo(f"Level: {level}")
    if template:
        typer.echo(f"Template: {template}")
    if export_format:
        typer.echo(f"Export format: {export_format}")
    typer.echo("NPC generation functionality not yet implemented")


# Encounter commands
@encounter_app.command("balance")
def encounter_balance(
    party: str = typer.Option(..., "--party", help="Party composition file or JSON"),
    difficulty: str = typer.Option("avg", "--difficulty", help="Difficulty (easy, avg, hard)"),
):
    """Suggest encounters based on party composition."""
    # Implementation placeholder - will be implemented in later phases
    typer.echo(f"Balancing encounter for party: {party}")
    typer.echo(f"Difficulty: {difficulty}")
    typer.echo("Encounter balancing functionality not yet implemented")


# Animal encounter sub-app
animal_encounter_app = typer.Typer(
    name="animal",
    help="Animal encounter generation commands",
    add_completion=False,
)

encounter_app.add_typer(animal_encounter_app, name="animal")


@animal_encounter_app.command("gen")
def animal_encounter_generate(
    world: str = typer.Option(None, "--world", help="World or environment type"),
    challenge: str = typer.Option(None, "--challenge", help="Challenge rating"),
    export_format: str = typer.Option(None, "--export", help="Export format (json, yaml, csv)"),
):
    """Generate animal encounters appropriate to a world or subsector."""
    # Implementation placeholder - will be implemented in later phases
    typer.echo("Generating animal encounter...")
    if world:
        typer.echo(f"World/Environment: {world}")
    if challenge:
        typer.echo(f"Challenge: {challenge}")
    if export_format:
        typer.echo(f"Export format: {export_format}")
    typer.echo("Animal encounter generation functionality not yet implemented")


# Patron encounter sub-app
patron_encounter_app = typer.Typer(
    name="patron",
    help="Patron encounter generation commands",
    add_completion=False,
)

encounter_app.add_typer(patron_encounter_app, name="patron")


@patron_encounter_app.command("gen")
def patron_encounter_generate(
    tone: str = typer.Option("neutral", "--tone", help="Patron tone (friendly, neutral, hostile)"),
    level: int = typer.Option(None, "--level", help="Patron level/influence"),
    export_format: str = typer.Option(None, "--export", help="Export format (json, yaml, csv)"),
):
    """Generate patron NPCs or patron-encounters."""
    # Implementation placeholder - will be implemented in later phases
    typer.echo("Generating patron encounter...")
    typer.echo(f"Tone: {tone}")
    if level is not None:
        typer.echo(f"Level: {level}")
    if export_format:
        typer.echo(f"Export format: {export_format}")
    typer.echo("Patron encounter generation functionality not yet implemented")


# World commands
@world_app.command("create")
def world_create(
    seed: int = typer.Option(None, "--seed", help="Random seed for reproducible results"),
    export_format: str = typer.Option(None, "--export", help="Export format (json, yaml)"),
):
    """Create a world (star system, world data)."""
    # Implementation placeholder - will be implemented in later phases
    typer.echo("Creating world...")
    if seed is not None:
        typer.echo(f"Using seed: {seed}")
    if export_format:
        typer.echo(f"Export format: {export_format}")
    typer.echo("World creation functionality not yet implemented")


# Subsector sub-app
subsector_app = typer.Typer(
    name="subsector",
    help="Subsector generation commands",
    add_completion=False,
)

world_app.add_typer(subsector_app, name="subsector")


@subsector_app.command("create")
def subsector_create(
    seed: int = typer.Option(None, "--seed", help="Random seed for reproducible results"),
    export_format: str = typer.Option(None, "--export", help="Export format (json, yaml)"),
):
    """Create a subsector suitable for campaign placement."""
    # Implementation placeholder - will be implemented in later phases
    typer.echo("Creating subsector...")
    if seed is not None:
        typer.echo(f"Using seed: {seed}")
    if export_format:
        typer.echo(f"Export format: {export_format}")
    typer.echo("Subsector creation functionality not yet implemented")


if __name__ == "__main__":
    app()

# This file contains GitHub Copilot generated content.
