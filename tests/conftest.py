import pytest

import gameboard
import deduction


@pytest.fixture
def board_advanced():
    """Returns a valid advanced Cryptid board."""
    boardstring = "1r42635"
    structures = ((4, -1), (3, 7), (10, 2), (0, 3), (9, -4), (5, 1), (0, 4), (2, 4))
    clues = ["not,mountain", "not,desert", "water,desert", "not,blue"]
    solution = (9, 8)

    board = gameboard.assemble_board(boardstring, structures)
    return board


@pytest.fixture
def board_basic():
    """Returns a valid basic Cryptid board."""
    boardstring = "31r254r6r"
    structures = ((4, 2), (4, 1), (9, -3), (7, 5), (4, -2), (1, 6))
    clues = ["shack", "white", "water,forest", "green"]
    solution = (6, -1)

    board = gameboard.assemble_board(boardstring, structures)
    return board


@pytest.fixture
def board_known():
    """Returns a valid advanced Cryptid board with the clues for each player."""
    boardstring = "1r42635"
    structures = ((4, -1), (3, 7), (10, 2), (0, 3), (9, -4), (5, 1), (0, 4), (2, 4))
    clues = ["not,mountain", "not,desert", "water,desert", "not,blue"]
    solution = (9, 4)

    board = gameboard.assemble_board(boardstring, structures)
    return board, clues, solution


@pytest.fixture
def game_with_plays(board_known):
    """Creates a deduction.Game object with initial negative plays."""

    board, clues, _ = board_known
    game = deduction.Game(board, 4, known_clues=clues)

    for _ in range(2):
        for player in game.players:
            player.play(False, "random")

    return game
