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
