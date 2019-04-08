"""Tests for drawing a board to an image"""

import pytest

import gameboard
import draw
import hextools


@pytest.mark.drawing
def test_draw(board_advanced, board_basic):
    """Test the drawing of static board objects.
    Requires manual viewing
    """
    draw.draw_board(board_advanced, 100, 'testmap.png')
    draw.draw_board(board_basic, 56, 'testmap2.png')


@pytest.mark.drawing
def test_draw_with_clues(game_with_plays):
    """Test the drawing of a board with plays."""
    draw.draw_board(game_with_plays.board, 100, 'testclues.png')
