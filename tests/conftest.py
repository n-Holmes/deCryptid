import pytest

import gameboard


@pytest.fixture
def board():
    boardstring = '1r42635'
    structures = ((4, 1), (3, 8), (10, 7), (0, 3),
                  (9, 0), (5, 3), (0, 4), (2, 5))
    clues = ['not1Mountain', 'not1Desert', 'Water|Desert', 'not3Blue']
    solution = (9, 8)

    game = gameboard.assemble_board(boardstring, structures)
    return game


@pytest.fixture
def board_basic():
    boardstring = '5246r31'
    structures = ((1, 0), (10, 6), (5, 1), (6, 4), (2, 0), (3, 2))
    clues = ['within two of bear', 'on water or mountain',
             'on desert or mountain', 'within one of forest']
    solution = None

    game = gameboard.assemble_board(boardstring, structures)
    return game
