import hashlib
import re
import secrets

_DIGIT_STRING = re.compile(r"^[+-]?[0-9]+$")


def _fold(text: str) -> int:
    """Fold text to 64 bits with blake2b over its UTF-8 bytes, big-endian.

    The one place the digest is computed, so a text seed and a folded
    negative seed can never drift apart (research.md R1).
    """
    return int.from_bytes(hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest(), "big")


def resolve_seed(seed: int | str | None) -> int:
    """Resolve a caller-supplied seed to the integer a `Roller` is built from.

    `None` draws 64 bits from `secrets`. An `int` is used as given. A string
    of digits (optionally signed) is read as that integer, so a seed echoed
    back by a previous run round-trips exactly. Any other string is folded
    with a blake2b-64 digest over its UTF-8 bytes, never handed to
    `random.Random` directly (see research.md R1, R2).
    """
    if seed is None:
        return secrets.randbits(64)
    if isinstance(seed, int):
        return seed
    if _DIGIT_STRING.match(seed):
        return int(seed)
    return _fold(seed)


def rng_seed(resolved: int) -> int:
    """Map a resolved seed onto the value `random.Random` is seeded with.

    `random.Random` seeds an exact integer from its *absolute value*, so
    `-5` and `5` would otherwise be the same stream and half the seed space
    would be unreachable. FR-002 forbids reducing a seed "into a narrower
    range", so the sign has to survive the hand-off.

    Only the negative branch is folded, through the same blake2b digest a
    text seed takes, keyed on the signed decimal form. Non-negative seeds
    pass through untouched, which is what keeps every published value in
    contracts/cli.md and every golden file byte-identical; a symmetric
    remap such as zigzag encoding would have moved all of them.

    The seed a result *reports* is always the resolved integer, sign and
    all, so the round trip is unaffected: the reported `-5` resolves back
    to `-5` and folds to the same stream again.
    """
    if resolved >= 0:
        return resolved
    return _fold(str(resolved))
