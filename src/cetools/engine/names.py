from cetools.engine.rolls import RollName, Rolls

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


def generate_name(rolls: Rolls) -> str:
    first = rolls.choose(FIRST_NAMES, RollName.FIRST_NAME)
    last = rolls.choose(LAST_NAMES, RollName.LAST_NAME)
    return f"{first} {last}"
