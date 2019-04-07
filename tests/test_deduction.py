"""Test functions for deductive logic component."""

import pytest

import deduction


@pytest.mark.deduce
def test_clue_count_advanced(board):
    """Check for correct clue count on advanced board.
    Given an advanced board,
    When setting up a Game object,
    Then 48 clues should be generated.
    """
    game = deduction.Game(board, 4)
    assert(len(game.clues)) == 48


@pytest.mark.deduce
def test_clue_count_basic(board_basic):
    """Check for correct clue count on basic board.
    Given a basic board,
    When setting up a Game object,
    Then 23 clues should be generated.
    """
    game = deduction.Game(board_basic, 4)
    assert(len(game.clues)) == 23


@pytest.mark.deduce
def test_random_plays(board_known):
    """Check that players can play pieces randomly
    Given a board where all Players know their clues,
    Have all players take turns playing two random false pieces.
    """
    board, clues = board_known
    game = deduction.Game(board, 4, known_clues=clues)

    for player in game.players:
        assert(player.known_clue is not None)

    # Make random plays
    for _ in range(2):
        for player in game.players:
            player.play_random()

    assert(len([play for play in player.negatives for player in game.players])) == 8
