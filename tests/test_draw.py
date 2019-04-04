"""Tests for drawing a board to an image"""

import pytest

import gameboard
import draw
import hextools


@pytest.mark.drawing
def test_draw(board, board_basic):
    draw.draw_board(board, 100, 'testmap.png')
    draw.draw_board(board_basic, 56, 'testmap2.png')
