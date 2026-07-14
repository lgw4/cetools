from cetools.engine.rolls import RollName, ScriptedRolls

# Fake rollers used to live here (ConstantRoller, SmartRoller, SequenceRoller).
# They scripted raw die sequences positionally, so a test had to know the exact
# order and arity of every roll the engine made. Tests now script rolls by name
# through cetools.engine.rolls.ScriptedRolls instead.


def scripted(**overrides) -> ScriptedRolls:
    """A career where nothing goes wrong.

    Every check passes, every table roll lands on row 1, every choice takes the
    head of the list, every 2D6 is 10. Psionics is opted out (the gate fails) so
    that tests about careers are not perturbed by psionic rolls.

    Override any of it by name—a test says only what it is actually about.
    """
    checks = {RollName.PSI_GATE: False}
    checks.update(overrides.pop("checks", {}))
    params = dict(default_check=True, default_two_d6=10, default_d6=1, default_choice=0)
    params.update(overrides)
    return ScriptedRolls(checks=checks, **params)
