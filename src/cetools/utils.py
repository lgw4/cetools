import random

PSEUDO_HEX = {
    0: "0",
    1: "1",
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    9: "9",
    10: "A",
    11: "B",
    12: "C",
    13: "D",
    14: "E",
    15: "F",
    16: "G",
    17: "H",
    18: "J",
    19: "K",
    20: "L",
    21: "M",
    22: "N",
    23: "P",
    24: "Q",
    25: "R",
    26: "S",
    27: "T",
    28: "U",
    29: "V",
    30: "W",
    31: "X",
    32: "Y",
    33: "Z",
}

RAND = random.SystemRandom()


def roll_d6() -> int:
    """Simulate rolling one six-sided die."""
    return RAND.randint(1, 6)


def roll_nd6(num: int = 2) -> int:
    """Return the sum of num simulated die rolls."""
    return sum([roll_d6() for _ in range(num)])


def roll_d66() -> int:
    """
    Return an integer representation of two single die rolls as units
    and tens digits.
    """
    return int(f"{roll_d6()}{roll_d6()}")
