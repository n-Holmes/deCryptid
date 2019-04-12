"""Deduction logic and classes for maintaining/updating game state."""

from collections import defaultdict
import itertools
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

        feature_names = []
        feature_names.extend(TERRAINS.values())
        feature_names.extend(ANIMALS.values())
        feature_names.extend(struct for struct, color in STRUCTURES)
        feature_names.extend(color for struct, color in STRUCTURES)

        self.features = {name: set() for name in feature_names}

        self.clues = {}
        self._get_clues()

        if known_clues is None:
            self.players = [Player(self, i) for i in range(player_count)]
        else:
            self.players = [
                Player(self, i, known_clue=known_clues[i]) for i in range(player_count)
            ]

    def _get_clues(self):
        """Assemble the name and region for each possible clue."""
        for pos, tile in self.board:
            pos = hextools.cubic(*pos)

            self.features[tile.terrain].add(pos)

            if tile.structure is not None:
                struct, color = tile.structure
                self.features[struct].add(pos)
                self.features[color].add(pos)

            if tile.animal is not None:
                self.features[tile.animal].add(pos)

        for feature, region in self.features.items():
            if region:
                self._add_clue(region, feature)

        self._add_clue(self.features["bear"] | self.features["cougar"], "bear,cougar")

        # terrain pairs
        for first, second in itertools.combinations(TERRAINS.values(), 2):
            self._add_clue(
                self.features[first] | self.features[second], f"{first},{second}"
            )

        # Restrict all clues to the board
        for clue in self.clues:
            self.clues[clue] = self.clues[clue] & self.tile_set

        # Negative clues if playing in advanced mode
        if self.features["black"]:
            positives = list(self.clues.items())
            for clue, tiles in positives:
                negation = Clue(",".join(clue.features), negate=True)
                self.clues[negation] = self.tile_set - tiles

    def _add_clue(self, region, features):
        clue = Clue(features)
        self.clues[clue] = hextools.expand(region, clue.radius)

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
            raise IncompatibleCluesError

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
                raise ValueError(f"Clue for player {player} is not known.")

            clue_sets[player] = {self.players[player].known_clue}

        # TODO: Clean up this code.  Multiple nested try-except blocks
        #   seems like a bad idea
        solutions = []
        for clue_list in itertools.product(*clue_sets):
            try:
                # There must be a unique solution to the clue set
                solution = self.solve(clue_list)
                # All clues must be determinative on the solution
                for sub_list in itertools.combinations(clue_list, len(clue_list) - 1):
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
        known_clue: Clue object or string representing the known clue of the
            player.
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self, game, player_number, positives=None, negatives=None, known_clue=None
    ):
        self.game = game
        self.clues = game.clues.copy()
        self.number = player_number

        if known_clue is not None:
            if isinstance(known_clue, str):
                known_clue = Clue(known_clue)
            if known_clue not in self.clues:
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

    def play(self, play_type, choice="random"):
        """Play a correct piece of the specified type.
        If the player's clue is not known this should cause an error.

        Args:
            play_type: Boolean to determine whether the played piece
                should be positive or negative.
            choice: A string specifying how to choose where to play.
                Options are 'random', 'cluecount'.

        Raises:
            UnknownClueError: If the player's clue is not known, then
                we cannot know where it can legally play.
            NoLegalPlayError: If there are no legal positions to play in.
        """
        if self.known_clue is None:
            raise UnknownClueError("Cannot play without known clue.")

        region = self.clues[self.known_clue]
        if not play_type:
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

        play_func = {"random": self._play_random, "cluecount": self._play_clue_count}[
            choice
        ]
        play = play_func(possible_tiles, play_type)

        self.game.board.gethex(play).players[self.number] = play_type
        if play_type:
            self.positives.add(play)
        else:
            self.negatives.add(play)

        self.restrict_clues()

    def _play_random(self, possible_tiles, play_type):
        """Make a random play."""

        return random.choice(possible_tiles)

    def _play_clue_count(self, possible_tiles, play_type):
        """Make a play attempting to maximize the number of remaining
        possible clues."""

        clues_remaining = defaultdict(int)
        for tile in possible_tiles:
            for region in self.clues.values():
                if play_type == (tile in region):
                    clues_remaining[tile] += 1

        return max(clues_remaining, key=lambda t: clues_remaining[t])


class Clue:
    """Class to store a Player's clue.

    Args:
        features: A comma separated string of features contained in the clue.
            If the first element of features is 'not', will force negation.
        negate: A boolean.  If true, the clue is a negation. 'not' in features
            overrides this
    """

    def __init__(self, features, negate=False):
        self.features = features.split(",")
        if self.features[0] == "not":
            self.features = self.features[1:]
            self.negate = True
        else:
            self.negate = negate

        self.features = tuple(sorted(self.features))

        if self.features[0] in ANIMALS.values():
            if len(self.features) == 2:
                self.radius = 1
            else:
                self.radius = 2
        elif self.features[0] in TERRAINS.values():
            if len(self.features) == 2:
                self.radius = 0
            else:
                self.radius = 1
        elif self.features[0][0] == "s":  # Standing Stone or Shack
            self.radius = 2
        else:
            self.radius = 3

    def __eq__(self, other):
        return self.features == other.features and self.negate == other.negate

    def __hash__(self):
        return hash((*self.features, self.negate))

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(features={self.features},"
            f" negate={self.negate}"
        )


class IncompatibleCluesError(Exception):
    pass


class UnknownClueError(Exception):
    pass


class NoLegalPlayError(Exception):
    pass
