"""The ship-name catalog and its provenance types.

Two invariants a future contributor must not disturb without reading this
docstring first.

First, **the draw stays last.** `generate_ship_name` is called as the final
`Rolls` draw on every `generate_ship` path, after every other decision a seed
makes. `RandomRolls` wraps a single `random.Random` stream, so a draw inserted
anywhere but the end shifts every later draw and changes the hull, drives and
armament a seed produces.
`test_sc008_ship_name_is_the_final_draw_and_is_drawn_exactly_once_on_both_paths`
in `tests/test_ship_generator.py` pins this directly, and
`tests/data/baseline/designs.json` is a re-pinned seed-to-ship anchor for future
features, failing loudly, naming the seed, if a future change ever moves the
name draw off the end of a path.

Second, **two different mappings, two different stability guarantees**.
The seed-to-*ship* mapping, every field but `name`, is a
compatibility surface, protected by that same baseline test. The
seed-to-*name* mapping is not: `SHIP_NAMES` is an ordered tuple and selection
is an index into it, so adding, removing or reordering an entry changes which
name a given seed draws. That is expected and permitted. A contributor
withdrawing a mis-sourced entry needs no baseline update and no
test edit, only a data-only change to this file.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from cetools.engine.rolls import RandomRolls, RollName, Rolls


class Tradition(StrEnum):
    """Where a catalog name comes from.

    A name is assigned to the *earliest* tradition it belongs to and
    cataloged exactly once: a mythological name later claimed by a
    written- or screen-SF vessel stays under `MYTHOLOGY_FOLKLORE`.
    """

    MYTHOLOGY_FOLKLORE = "mythology_folklore"
    WRITTEN_SF = "written_sf"
    SCREEN_SF = "screen_sf"


class BasisKind(StrEnum):
    """Why a fiction-tradition name is safe to catalog, recorded on its entry:
    it belongs to a real vessel, is an ordinary word, or is a public-domain
    borrowing.

    Exactly one kind is recorded per entry, even when a name would qualify
    under more than one: the field is evidence the constraint
    holds, not an exhaustive provenance record.
    """

    ORDINARY_WORD = "ordinary_word"
    REAL_VESSEL = "real_vessel"
    PUBLIC_DOMAIN_WORK = "public_domain_work"


@dataclass(frozen=True)
class ShipName:
    """One catalog entry: a bare proper name plus its provenance.

    `basis_kind` and `basis_reference` are set together, and only for
    `WRITTEN_SF` and `SCREEN_SF` entries (V1-V3): the tradition itself is
    `MYTHOLOGY_FOLKLORE`'s warrant, so it carries neither.
    """

    name: str
    tradition: Tradition
    basis_kind: BasisKind | None = None
    basis_reference: str = ""


SHIP_NAMES: tuple[ShipName, ...] = (
    # -- Mythology and folklore: no basis, the tradition is its own warrant.
    # -- Grouped loosely by source culture for readability; the grouping
    # -- carries no meaning.
    ShipName(name="Beowulf", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    # Greek and Roman
    ShipName(name="Achilles", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Perseus", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Hyperion", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Nemesis", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Bellerophon", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Agamemnon", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Pegasus", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Prometheus", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Icarus", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Atlas", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Ajax", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Odysseus", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Orion", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Andromeda", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Cassandra", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Theseus", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Narcissus", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Atlantis", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Erebus", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Aurora", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    # Norse
    ShipName(name="Valkyrie", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Sleipnir", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Fenrir", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Yggdrasil", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Baldur", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Heimdall", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Mimir", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Skadi", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Huginn", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Muninn", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    # Germanic and Anglo-Saxon legend
    ShipName(name="Grendel", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Hrothgar", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Wayland", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Sigurd", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    # Arthurian
    ShipName(name="Excalibur", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Gawain", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Merlin", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Avalon", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Camelot", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Percival", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Galahad", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Pendragon", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    # Celtic
    ShipName(name="Cu Chulainn", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Brigid", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Danu", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Lugh", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Rhiannon", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Taliesin", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Oisin", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Niamh", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    # Mesopotamian
    ShipName(name="Gilgamesh", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Marduk", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Ishtar", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Tiamat", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Anzu", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Ereshkigal", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Enkidu", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    # Japanese
    ShipName(name="Amaterasu", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Susanoo", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Raijin", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Fujin", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Kaguya", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Yamato", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    # Chinese
    ShipName(name="Qilin", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Pangu", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Nuwa", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Chang'e", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Zhulong", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Taotie", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    # West African
    ShipName(name="Anansi", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Oshun", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Ogun", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Shango", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Yemoja", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    # Mesoamerican
    ShipName(name="Quetzalcoatl", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Kukulkan", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Xolotl", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Itzamna", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    ShipName(name="Ixchel", tradition=Tradition.MYTHOLOGY_FOLKLORE),
    # -- Written science fiction: every entry earns
    # -- its place on a real vessel, an ordinary word or a public-domain
    # -- borrowing, each checked for accuracy. A name mythology
    # -- already claims (Pegasus, Prometheus, Erebus, ...) stays there
    # -- even where a written-SF vessel later bore it.
    # --
    # -- `basis_*` records why a name is safe to catalog, not
    # -- where it comes from. Where an entry's *tradition* was queried and
    # -- confirmed, a comment above it names the source
    # -- vessel, since no field carries that and no test can check it.
    ShipName(
        name="Endeavour",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Endeavour, 1764",
    ),
    ShipName(
        name="Nautilus",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="Nautilus, Robert Fulton's submarine, 1800",
    ),
    ShipName(
        name="Albatross",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="albatross: a large seabird",
    ),
    ShipName(
        name="Rocinante",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.PUBLIC_DOMAIN_WORK,
        basis_reference="Rocinante, Cervantes, Don Quixote (1605)",
    ),
    ShipName(
        name="Canterbury",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Canterbury, 1915",
    ),
    ShipName(
        name="Razorback",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="razorback: a wild hog with a ridged back",
    ),
    ShipName(
        name="Behemoth",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.PUBLIC_DOMAIN_WORK,
        basis_reference="Behemoth, Book of Job, Hebrew Bible",
    ),
    ShipName(
        name="Skylark",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="skylark: a small songbird",
    ),
    ShipName(
        name="Fearless",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Fearless, 1934",
    ),
    ShipName(
        name="Invincible",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Invincible, 1907",
    ),
    ShipName(
        name="Peregrine",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="peregrine: a peregrine falcon",
    ),
    ShipName(
        name="Ariel",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.PUBLIC_DOMAIN_WORK,
        basis_reference="Ariel, Shakespeare, The Tempest (1611)",
    ),
    ShipName(
        name="Resolution",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Resolution, 1771",
    ),
    ShipName(
        name="Adventure",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Adventure, 1771",
    ),
    ShipName(
        name="Beagle",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Beagle, 1820",
    ),
    ShipName(
        name="Bounty",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Bounty, 1787",
    ),
    ShipName(
        name="Terror",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Terror, 1813",
    ),
    ShipName(
        name="Falcon",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="falcon: a bird of prey",
    ),
    ShipName(
        name="Wanderer",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="wanderer: one who travels without a fixed destination",
    ),
    ShipName(
        name="Pilgrim",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="pilgrim: one who journeys to a sacred place",
    ),
    ShipName(
        name="Envoy",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="envoy: a messenger or representative sent on a mission",
    ),
    ShipName(
        name="Nomad",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="nomad: a member of a people with no fixed residence",
    ),
    ShipName(
        name="Pequod",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.PUBLIC_DOMAIN_WORK,
        basis_reference="Pequod, Melville, Moby-Dick (1851)",
    ),
    ShipName(
        name="Zephyr",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="zephyr: a gentle breeze",
    ),
    # Lady Macbeth, Peter F. Hamilton, The Reality Dysfunction (1996)
    ShipName(
        name="Lady Macbeth",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.PUBLIC_DOMAIN_WORK,
        basis_reference="Lady Macbeth, Shakespeare, Macbeth (1606)",
    ),
    ShipName(
        name="Trident",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="trident: a three-pronged spear",
    ),
    # Halcyon, Alastair Reynolds, Halcyon Years (2026)
    ShipName(
        name="Halcyon",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="halcyon: calm and peaceful",
    ),
    ShipName(
        name="Leviathan",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="leviathan: something of immense size and power",
    ),
    ShipName(
        name="Victory",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Victory, 1765",
    ),
    ShipName(
        name="Dreadnought",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Dreadnought, 1906",
    ),
    ShipName(
        name="Intrepid",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="USS Intrepid, 1943",
    ),
    ShipName(
        name="Ark Royal",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Ark Royal, 1937",
    ),
    ShipName(
        name="Belfast",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Belfast, 1938",
    ),
    ShipName(
        name="Hood",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Hood, 1918",
    ),
    ShipName(
        name="Constellation",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="USS Constellation, 1797",
    ),
    ShipName(
        name="Perseverance",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="perseverance: continued effort despite difficulty",
    ),
    ShipName(
        name="Nimrod",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="Nimrod, Shackleton's Antarctic expedition ship, 1907",
    ),
    ShipName(
        name="Discovery",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="RRS Discovery, Scott's Antarctic research ship, 1901",
    ),
    ShipName(
        name="Odyssey",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="odyssey: a long and eventful journey",
    ),
    ShipName(
        name="Sirocco",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="sirocco: a hot Mediterranean wind",
    ),
    # Rockhopper, Alastair Reynolds, Pushing Ice (2005)
    ShipName(
        name="Rockhopper",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="rockhopper: a crested penguin",
    ),
    # Vanguard, Robert A. Heinlein, "Universe" (1941), collected as Orphans of
    # the Sky (1963) -- one of the earliest generation ships in written SF, and
    # so the earliest tradition the name belongs to, screen use of it
    # notwithstanding.
    ShipName(
        name="Vanguard",
        tradition=Tradition.WRITTEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="vanguard: the foremost part of an advancing group",
    ),
    # -- Science fiction film and television: the
    # -- pool leans on real-vessel and ordinary-word names for the same
    # -- reason as written SF; coined franchise names (Millennium Falcon,
    # -- Tantive IV, Executor) are excluded. Mythological names stay
    # -- under MYTHOLOGY_FOLKLORE however famous the ship that
    # -- later bore them.
    ShipName(
        name="Serenity",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="serenity: calm, untroubled state",
    ),
    ShipName(
        name="Enterprise",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="USS Enterprise (CV-6), 1936",
    ),
    ShipName(
        name="Constitution",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="USS Constitution, 1797",
    ),
    ShipName(
        name="Lexington",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="USS Lexington (CV-2), 1925",
    ),
    ShipName(
        name="Yorktown",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="USS Yorktown (CV-5), 1936",
    ),
    ShipName(
        name="Saratoga",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="USS Saratoga (CV-3), 1925",
    ),
    ShipName(
        name="Hornet",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="USS Hornet (CV-8), 1940",
    ),
    ShipName(
        name="Repulse",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Repulse, 1916",
    ),
    ShipName(
        name="Potemkin",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="Potemkin, Imperial Russian Navy battleship, 1900",
    ),
    ShipName(
        name="Farragut",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="USS Farragut (DD-348), 1934",
    ),
    ShipName(
        name="Voyager",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="voyager: one who travels on a long journey",
    ),
    ShipName(
        name="Sovereign",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="sovereign: possessing supreme authority",
    ),
    ShipName(
        name="Ambassador",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="ambassador: an official envoy",
    ),
    ShipName(
        name="Nebula",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="nebula: a cloud of interstellar gas and dust",
    ),
    ShipName(
        name="Galaxy",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="galaxy: a system of stars",
    ),
    ShipName(
        name="Nostromo",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.PUBLIC_DOMAIN_WORK,
        basis_reference="Nostromo, Joseph Conrad (1904)",
    ),
    ShipName(
        name="Liberator",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="liberator: one who sets free",
    ),
    ShipName(
        name="Swordfish",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="swordfish: a large fish with a sword-like bill",
    ),
    ShipName(
        name="Bebop",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="bebop: a style of jazz music",
    ),
    ShipName(
        name="Excelsior",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="excelsior: ever upward",
    ),
    ShipName(
        name="Bismarck",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="Bismarck, German battleship, 1939",
    ),
    ShipName(
        name="Valiant",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Valiant, 1914",
    ),
    ShipName(
        name="Vengeance",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Vengeance, 1944",
    ),
    ShipName(
        name="Dauntless",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="dauntless: showing fearlessness and determination",
    ),
    ShipName(
        name="Sentinel",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="sentinel: a soldier or guard who keeps watch",
    ),
    ShipName(
        name="Covenant",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="covenant: a formal, binding agreement",
    ),
    ShipName(
        name="Horizon",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="horizon: the line at which the earth and sky appear to meet",
    ),
    # USS Exeter, Star Trek, "The Omega Glory" (1968) -- named on screen for
    # the Royal Navy cruiser by D. C. Fontana and Robert Justman's own memos
    ShipName(
        name="Exeter",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Exeter, 1929",
    ),
    ShipName(
        name="Event Horizon",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="event horizon: the boundary beyond which nothing escapes a black hole",
    ),
    # USS Essex, Star Trek: The Next Generation, "Power Play" (1992)
    ShipName(
        name="Essex",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="USS Essex, 1799",
    ),
    ShipName(
        name="Destiny",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="destiny: the events that will necessarily happen to a person or thing",
    ),
    ShipName(
        name="Defiant",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="defiant: boldly resistant or challenging",
    ),
    ShipName(
        name="Sulaco",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.PUBLIC_DOMAIN_WORK,
        basis_reference="Sulaco, Conrad, Nostromo (1904)",
    ),
    ShipName(
        name="Pathfinder",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="pathfinder: one who discovers a new route through unknown territory",
    ),
    ShipName(
        name="Columbia",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="Space Shuttle Columbia, 1981",
    ),
    ShipName(
        name="White Star",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="White Star, Pilkington & Wilson clipper ship, 1854",
    ),
    ShipName(
        name="Reliant",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.ORDINARY_WORD,
        basis_reference="reliant: depending on or trusting in someone or something",
    ),
    ShipName(
        name="Formidable",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Formidable, 1898",
    ),
    ShipName(
        name="Temeraire",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Temeraire, 1798",
    ),
    ShipName(
        name="Warrior",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="HMS Warrior, 1860",
    ),
    ShipName(
        name="Arizona",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="USS Arizona, 1915",
    ),
    # Endurance, Interstellar (2014) -- the ranger's mothership. The basis below
    # is Shackleton's ship, which the film's name honors; the tradition is the
    # film, no written-SF vessel of the name having been found.
    ShipName(
        name="Endurance",
        tradition=Tradition.SCREEN_SF,
        basis_kind=BasisKind.REAL_VESSEL,
        basis_reference="Endurance, Shackleton's Antarctic expedition ship, 1912",
    ),
)


def generate_ship_name(rolls: Rolls | None = None) -> str:
    """A random catalog name, drawn through the `Rolls` seam.

    Must stay the last `Rolls` draw on every `generate_ship` path (module
    docstring, above)."""
    rolls = rolls or RandomRolls()
    return rolls.choose(SHIP_NAMES, RollName.SHIP_NAME).name
