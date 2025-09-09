# CETools: Tools for use with the _Cepheus Engine SRD_ tabletop roleplaying game

CETools is a suite of command-line utilities designed for players and referees of the Cepheus Engine tabletop roleplaying game. This project provides tools for character creation, NPC generation, dice rolling, world building, encounter generation, and SRD lookup.

## Features

- Character and NPC generation
- Dice roll parser with support for Cepheus-style notation (including D66)
- World and subsector generation
- Encounter generation and balancing
- SRD lookup and reference

## Installation

Requires Python 3.13 or later.

```bash
# Using uv (recommended)
uv pip install git+https://github.com/lgw4/cetools.git

# Using pip
pip install git+https://github.com/lgw4/cetools.git
```

## Quick Start

```bash
# Generate a character (when installed)
cetools character create --template traveller

# Or, during development, run via uv and python3
uv run python3 -m cetools.cli.__main__ character create --template traveller --export json

# Roll dice
cetools roll 2d6+3

# Generate a subsector
cetools world subsector create --seed 42 --export json

# Look up an SRD term
cetools srlookup "jump drive"
```

## Development Setup

1. Clone the repository
1. Set up a virtual environment with uv:

```bash
uv venv
source .venv/bin/activate  # On Unix/macOS
```

1. Install development dependencies:

```bash
uv pip install -e ".[dev]"
```

1. Run tests:

```bash
pytest
```

## License

See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

<!-- This file contains GitHub Copilot generated content. -->
