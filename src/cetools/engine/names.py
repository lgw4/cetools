from cetools.engine.dice import DiceRoller

FIRST_NAMES: tuple[str, ...] = (
    "Alex",
    "Sam",
    "Jordan",
    "Taylor",
    "Morgan",
    "Casey",
    "Riley",
    "Avery",
    "Quinn",
    "Reese",
    "Skyler",
    "Drew",
)

LAST_NAMES: tuple[str, ...] = (
    "Voss",
    "Kade",
    "Renn",
    "Solis",
    "Marlowe",
    "Okafor",
    "Brennan",
    "Achebe",
    "Reyes",
    "Whitfield",
    "Nakamura",
    "Delgado",
)


def generate_name(roller: DiceRoller) -> str:
    first = FIRST_NAMES[roller.roll(len(FIRST_NAMES)) - 1]
    last = LAST_NAMES[roller.roll(len(LAST_NAMES)) - 1]
    return f"{first} {last}"
