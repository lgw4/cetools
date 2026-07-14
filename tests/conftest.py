# Fake rollers used to live here (ConstantRoller, SmartRoller, SequenceRoller).
# They scripted raw die sequences positionally, so a test had to know the exact
# order and arity of every roll the engine made. Tests now script rolls by name
# through cetools.engine.rolls.ScriptedRolls instead.
