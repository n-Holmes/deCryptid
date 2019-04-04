"""Deduction logic and classes for maintaining/updating game state."""


from itertools import combinations

from gameboard import ANIMALS, STRUCTURES, TERRAINS
import hextools


class Game:
    """Class to store the game state and perform deductions with.

    Args:
        board: hextools.HexGrid object populated by gameboard.Hex objects.
            Contains all of the setup information
        player_count: Integer number of players (3, 4 or 5).
    """

    def __init__(self, board, player_count):
        if not isinstance(board, hextools.HexGrid):
            raise TypeError("board must be an instance of hextools.HexGrid.")
        if not isinstance(player_count, int):
            raise TypeError("player_count must be an int.")
        if player_count not in (3, 4, 5):
            raise ValueError("player_count must be be between 3 and 5.")

        self.board = board
        self.players = 

        self.terrains = {terrain: set() for terrain in TERRAINS.values()}
        self.animals = {animal: set() for animal in ANIMALS.values()}
        self.structures = {struct: set() for struct, color in STRUCTURES}
        self.colors = {color: set() for struct, color in STRUCTURES}

        self.clues = {}
        self._get_clues()

    def _get_clues(self):
        """Assemble the name and region for each possible clue."""
        tile_set = set()
        for pos, tile in self.board:
            pos = hextools.cubic(*pos)
            tile_set.add(pos)

            self.terrains[tile.terrain].add(pos)

            if tile.structure is not None:
                struct, color = tile.structure
                self.structures[struct].add(pos)
                self.colors[color].add(pos)

            if tile.animal is not None:
                self.animals[tile.animal].add(pos)

        # Pair of terrains
        for trn_1, trn_2 in combinations(self.terrains, 2):
            clue = f'on {trn_1} or {trn_2}'
            self.clues[clue] = self.terrains[trn_1] | self.terrains[trn_2]

        # Within 1 of a terrain
        for terrain, region in self.terrains.items():
            clue = f'within one space of {terrain}'
            self.clues[clue] = hextools.expand(region, 1)

        # Within 1 of animals
        clue = 'within one space of either animal territory'
        region = set()
        for animal, region in self.animals.items():
            region |= region
        self.clues[clue] = hextools.expand(region, 1)

        # Within 2 of structure type
        for struct, region in self.structures.items():
            clue = f'within two spaces of a {struct}'
            self.clues[clue] = hextools.expand(region, 2)

        # Within 2 of animal type
        for animal, region in self.animals.items():
            clue = f'within two spaces of {animal} territory'
            self.clues[clue] = hextools.expand(region, 2)

        # Within 3 of structure color
        for color, region in self.colors.items():
            # May not be any black structures (basic game)
            if not region:
                continue

            clue = f'within three spaces of a {color} structure'
            self.clues[clue] = hextools.expand(region, 3)

        # Restrict all clues to the board
        for clue in self.clues:
            self.clues[clue] = self.clues[clue] & tile_set

        # Negative clues if playing in advanced mode
        if self.colors['black']:
            positives = list(self.clues.items())
            for clue, tiles in positives:
                negation = 'not ' + clue
                self.clues[negation] = tile_set - tiles


class Player:
    """Stores information on the clues given by a player."""
    def __init__(self, positives=None, negatives=None):
        
