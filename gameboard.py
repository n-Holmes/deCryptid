"""Classes for assembling actual Cryptid boards."""  # pylint: disable=no-member

from collections import namedtuple

import hextools

# TODO: Make a Clue class for sanity when comparing.
TERRAINS = {"F": "forest", "D": "desert", "W": "water", "S": "swamp", "M": "mountain"}

ANIMALS = {"b": "bear", "c": "cougar"}

Structure = namedtuple("Structure", ["name", "color"])
STRUCTURES = [
    Structure(name, color)
    for color in ("green", "white", "blue", "black")
    for name in ("standing stone", "shack")
]


class Hex:  # pylint: disable=too-few-public-methods
    """Holder class for information on a hexagon.
    Chosen over namedtuple for mutability.

    Args:
        terrainS: A terrain string.
        animal: An animal string or None.
        structure: A Structure namedtuple or None.
        players: A 5-entry array to store player's clues.
    """

    __slots__ = ["terrain", "animal", "structure", "players"]

    def __init__(self, terrain, animal=None, structure=None, players=None):
        if len(terrain) == 1:
            self.terrain = TERRAINS[terrain]
        else:
            self.terrain = terrain

        self.animal = animal
        self.structure = structure

        if players is None:
            self.players = [None] * 5
        else:
            self.players = players

    def __str__(self):
        parts = [f"Hex: {self.terrain}"]
        if self.animal is not None:
            parts.append(f"{self.animal} territory")
        if self.structure is not None:
            parts.append(f"{self.Structure.color} {self.structure.name}")
        if self.players is not None:
            for i, truth in enumerate(self.players, 1):
                if truth is not None:
                    parts.append(f"player {i}: {truth}")

        return "".join(parts)

    def play(self, player, truth):
        """Play a single marker"""
        self.players[player - 1] = truth

    def plays(self, players):
        """Set the values of all plays.

        Args:
            players: A sequence of True, False or None values containing the
                truth value of all players. Length may be less than five to
                make lower player-count games simpler.
        """
        for i, truth in enumerate(players):
            self.players[i] = truth


def _static_boards(func):
    """Decorator to allow for single initialization of the board strings."""
    setattr(
        func,
        "boards",
        [
            "WSSWSSWWDWDDbFFDbFFF",
            "ScSSFcSMFcFMFDMFDMFDD",
            "SScMcSScMFFMFMMFWWWWW",
            "DDDDDDMMDMWFMWFMWcFc",
            "SSDSDDSDWMWWMMWbMMbWb",
            "DbMbMDMWSSWSSWSFWFFF",
        ],
    )
    return func


@_static_boards
def _get_board(index):
    board_string = _get_board.boards[index - 1]
    hex_list = []

    for char in board_string:
        if char.isupper():
            hex_list.append(Hex(char))
        else:
            hex_list[-1].animal = ANIMALS[char]

    return hextools.HexGrid(6, 3, hex_list, True)


def assemble_board(arrangement, structures):
    """Assemble a Cryptid board.

    Args:
        arrangement: A string containing the order of the boards along with
            which of them have been rotated. Matches pattern ([1-6]r?){6}
        structures: A dict of coordinate, Structure pairs giving the locations
            of each of the structures.
    """

    boards = []
    for char in arrangement:
        if char == "r":
            boards[-1].rotate()
        else:
            boards.append(_get_board(int(char)))

    for i in (0, 2, 4):
        boards[i].extend(boards[i + 1])

    main_board = boards[0]
    main_board.extend(boards[2], 1)
    main_board.extend(boards[4], 1)

    for pos, struct in zip(structures, STRUCTURES):
        tile = main_board.gethex(pos)
        tile.structure = struct

    return main_board
