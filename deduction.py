"""Deduction logic and classes for maintaining/updating game state."""


from itertools import combinations
import random

from gameboard import ANIMALS, STRUCTURES, TERRAINS
import hextools


class Game:
    """Class to store the game state and perform deductions with.

    Args:
        board: hextools.HexGrid object populated by gameboard.Hex objects.
            Contains all of the setup information
        player_count: Integer number of players (3, 4 or 5).
    """

    def __init__(self, board, player_count, known_clues=None):
        if not isinstance(board, hextools.HexGrid):
            raise TypeError("board must be an instance of hextools.HexGrid.")
        if not isinstance(player_count, int):
            raise TypeError("player_count must be an int.")
        if player_count not in (3, 4, 5):
            raise ValueError("player_count must be be between 3 and 5.")

        self.board = board
        self.tile_set = {hextools.cubic(*pos) for pos, tile in self.board}

        self.terrains = {terrain: set() for terrain in TERRAINS.values()}
        self.animals = {animal: set() for animal in ANIMALS.values()}
        self.structures = {struct: set() for struct, color in STRUCTURES}
        self.colors = {color: set() for struct, color in STRUCTURES}

        self.clues = {}
        self._get_clues()

        if known_clues is None:
            self.players = [Player(self, i) for i in range(player_count)]
        else:
            self.players = [
                Player(self, i, known_clue=known_clues[i])
                for i in range(player_count)
            ]

    def _get_clues(self):
        """Assemble the name and region for each possible clue."""
        for pos, tile in self.board:
            pos = hextools.cubic(*pos)

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
            clue = f'within one space of a {terrain}'
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
            self.clues[clue] = self.clues[clue] & self.tile_set

        # Negative clues if playing in advanced mode
        if self.colors['black']:
            positives = list(self.clues.items())
            for clue, tiles in positives:
                negation = 'not ' + clue
                self.clues[negation] = self.tile_set - tiles


class Player:
    """Stores information on the clues given by a player.

    Args:
        game: The Game object to associate the Player with.
        player_number: Integer - which player this is.
        positives: Positions marked positive by the player.
        negatives: Positions marked negative by the player.
        known_clue: Storage for the case that the clue is known.

    """

    # pylint: disable=too-many-arguments
    def __init__(self, game, player_number, positives=None,
                 negatives=None, known_clue=None):
        self.game = game
        self.clues = game.clues.copy()
        self.number = player_number

        if known_clue is not None and known_clue not in self.clues:
            print('known', known_clue)
            for clue in self.clues:
                print(clue)
            raise ValueError("known_clue must be an element of clues")
        self.known_clue = known_clue

        if positives is None:
            self.positives = set()
        else:
            self.positives = set(positives)

        if negatives is None:
            self.negatives = set()
        else:
            self.negatives = set(negatives)

        self.restrict_clues()

    def restrict_clues(self):
        """Restrict clue set to match positives and negatives.
        Ignores known_clue as storing publicly available knowledge is useful.
        """
        removals = []
        for clue, region in self.clues.items():
            if self.negatives & region or self.positives - region:
                removals.append(clue)

        for clue in removals:
            self.clues.pop(clue)

        if len(self.clues) == 1:
            self.known_clue = list(self.clues)[0]

    def add_clue(self, position, clue_type):
        """Update the player state given a new clue.

        Args:
            position: The position that the clue was given at.
            clue_type: Boolean, True for a positive clue, False for negative.
        """
        if clue_type:
            self.positives.add(position)
        else:
            self.negatives.add(position)

        self.restrict_clues()

    def play_random(self, clue_type=False):
        """Play a random, correct piece of the specified type.
        If the player's clue is not known this should cause an error.

        Args:
            clue_type: Boolean to determine whether the played piece
                should be positive or negative.

        Raises:
            UnknownClueError: If the player's clue is not known, then
                we cannot know where it can legally play.
            NoLegalPlayError: If there are no legal positions to play in.
        """
        if self.known_clue is None:
            raise UnknownClueError('Cannot play without known clue.')

        region = self.clues[self.known_clue]
        if not clue_type:
            region = self.game.tile_set - region

        possible_tiles = [
            tile
            for tile in region
            if False not in self.game.board.gethex(tile).players
            # Negative clue locks space
            and tile not in self.positives | self.negatives
        ]
        if not possible_tiles:
            raise NoLegalPlayError

        play = random.choice(possible_tiles)
        self.game.board.gethex(play).players[self.number] = clue_type

        if clue_type:
            self.positives.add(play)
        else:
            self.negatives.add(play)

        self.restrict_clues()


class UnknownClueError(Exception):
    pass


class NoLegalPlayError(Exception):
    pass
