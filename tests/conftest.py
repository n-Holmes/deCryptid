import pytest

import gameboard


@pytest.fixture
def board():
    boardstring = '1r42635'
    structures = ((4, -1), (3, 7), (10, 2), (0, 3),
                  (9, -4), (5, 1), (0, 4), (2, 4))
    clues = ['not within one space of a mountain',
             'not within one space of a desert',
             'on water or desert',
             'not within three spaces of a blue structure']
    solution = (9, 8)

    game = gameboard.assemble_board(boardstring, structures)
    return game


@pytest.fixture
def board_basic():
    boardstring = '31r254r6r'
    structures = ((4, 2), (4, 1), (9, -3), (7, 5), (4, -2), (1, 6))
    clues = ['within two spaces of a shack',
             'within three spaces of a white structure',
             'on water or forest',
             'within three spaces of a green structure']
    solution = (6, -1)

    game = gameboard.assemble_board(boardstring, structures)
    return game
