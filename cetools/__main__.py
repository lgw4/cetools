"""Entry point for running CETools as a module (python -m cetools).

Delegates to the CLI implementation in `cetools.cli.__main__` so tests and
developer workflows can run the CLI without an installed console script.

This file contains GitHub Copilot generated content.
"""

from cetools.cli.__main__ import app


def main():
    app()


if __name__ == "__main__":
    main()
