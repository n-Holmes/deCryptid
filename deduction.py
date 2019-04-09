"""Deduction logic and classes for maintaining/updating game state."""


from itertools import combinations, product
import random

from gameboard import ANIMALS, STRUCTURES, TERRAINS
import hextools


class Game:
    """Class to store the game state and perform deductions with.

    Args:
        board: hextools.HexGrid object populated by gameboard.Hex objects.
            Contains all of the setup information
        player_count: Integer number of players (3, 4 or 5).
        known_clues: If Some clues are known by players, pass them in
            as an array.
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

        # Pairs of terrains
        for trn_1, trn_2 in combinations(self.terrains, 2):
            clue = f'on {trn_1} or {trn_2}'
            self.clues[clue] = self.terrains[trn_1] | self.terrains[trn_2]

        self.clues[
            'within one space of either animal territory'
        ] = hextools.expand(self.animals['bear'] | self.animals['cougar'], 1)

        for terrain, region in self.terrains.items():
            self._add_clue(region, expansion=1, name=terrain)

        for struct, region in self.structures.items():
            self._add_clue(region, expansion=2, name=struct)

        for animal, region in self.animals.items():
            self._add_clue(region, expansion=2, name=f'{animal} territory')

        for color, region in self.colors.items():
            # There may not be any black structures (basic game)
            if not region:
                continue
            self._add_clue(region, expansion=3, name=f'{color} structure')

        # Restrict all clues to the board
        for clue in self.clues:
            self.clues[clue] = self.clues[clue] & self.tile_set

        # Negative clues if playing in advanced mode
        if self.colors['black']:
            positives = list(self.clues.items())
            for clue, tiles in positives:
                negation = 'not ' + clue
                self.clues[negation] = self.tile_set - tiles

    def _add_clue(self, region, expansion, name):
        dist = {1: 'one space', 2: 'two spaces', 3: 'three spaces'}
        clue = f'within {dist[expansion]} of a {name}'
        self.clues[clue] = hextools.expand(region, expansion)

    def solve(self, clue_list):
        """Given a list of clue names, find the unique position on the board
        which satisfies all of them.

        Args:
            clue_list: A list of clue names.

        Returns:
            The cubic coordinates of a hex on the map satisfting all clues.

        Raises:
            ValueError: clue_list must contain unique clues.
            IncompatibleCluesError: If the list of clues does not specify
                a unique hex.
        """
        if len(set(clue_list)) != len(clue_list):
            raise ValueError("Clues must be different")

        region = set.intersection(*[self.clues[clue] for clue in clue_list])

        if len(region) != 1:
            raise IncompatibleCluesError(
                f'Clues: {", ".join(clue_list)} give region {region}.'
            )

        return region.pop()

    def solutions(self, *known_players):
        """Find all possible solutions and their frequencies.

        Args:
            known_player: None, or iterable containing player numbers whose
                clues are known (uses known_clue rather than clues).

        Returns:
            A list of possible solutions.
        """

        clue_sets = [player.clues for player in self.players]
        for player in known_players:
            if self.players[player].known_clue is None:
                raise ValueError(f'Clue for player {player} is not known.')

            clue_sets[player] = {self.players[player].known_clue}

        # TODO: Clean up this code.  Multiple nested try-except blocks
        #   seems like a bad idea
        solutions = []
        for clue_list in product(*clue_sets):
            try:
                # There must be a unique solution to the clue set
                solution = self.solve(clue_list)
                # All clues must be determinative on the solution
                for sub_list in combinations(clue_list, len(clue_list) - 1):
                    try:
                        self.solve(sub_list)
                        raise ValueError
                    except IncompatibleCluesError:
                        pass

                solutions.append(solution)
            except (ValueError, IncompatibleCluesError):
                pass

        return solutions



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


class IncompatibleCluesError(Exception):
    pass


class UnknownClueError(Exception):
    pass


class NoLegalPlayError(Exception):
    pass
