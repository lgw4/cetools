class ConstantRoller:
    """Returns the same value for all dice rolls."""

    def __init__(self, value: int):
        self._value = value

    def roll(self, sides: int, count: int = 1) -> int:
        return self._value


class SmartRoller:
    """Returns one value for 2-dice rolls (checks) and another for 1-die rolls (tables)."""

    def __init__(self, two_dice_value: int, one_die_value: int):
        self._two = two_dice_value
        self._one = one_die_value

    def roll(self, sides: int, count: int = 1) -> int:
        return self._two if count >= 2 else self._one


class SequenceRoller:
    """Returns values from a sequence, then falls back to a default."""

    def __init__(self, values: list[int], default: int = 6):
        self._values = list(values)
        self._pos = 0
        self._default = default

    def roll(self, sides: int, count: int = 1) -> int:
        if self._pos < len(self._values):
            val = self._values[self._pos]
            self._pos += 1
            return val
        return self._default
