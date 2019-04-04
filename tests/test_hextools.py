"""Tests for basic hexagonal algorithms in hextools.py"""

import pytest
from math import e, pi

import hextools

@pytest.mark.hextools
def test_empty_grid_creation():
    hexgrid = hextools.HexGrid(10, 15)
    assert hexgrid.dimensions == (10, 15)
    assert hexgrid.gethex((3, 2)) is None

@pytest.mark.hextools
def test_filled_grid_creation():
    hexgrid = hextools.HexGrid(3, 11, "Hello")
    assert hexgrid.gethex((1, 1)) == "Hello"

@pytest.mark.hextools
def test_coordinate_inverses():
    a, b = 2, 5
    assert hextools.array_to_axial(*hextools.axial_to_array(a, b)) == (a, b)
    assert hextools.axial_to_array(*hextools.array_to_axial(a, b)) == (a, b) 

@pytest.mark.hextools
def test_cubic_coordinates():
    assert hextools.cubic(0, 0) == (0, 0, 0)
    assert hextools.cubic(2, 5) == (2, 5, -7)
    assert hextools.cubic(-4, 3, 5) == (-4, 3, 1)

@pytest.mark.hextools
def test_grid_distance():
    pos1 = (0, 0, 0)
    pos2 = (5, 1, -6)
    pos3 = (3.5, -10.5, 7)

    assert hextools.distance(pos1, pos2, "grid") == 6
    assert hextools.distance(pos2, pos3) == 13

@pytest.mark.hextools
def test_euclid_distance():
    pos1 = (0, 0, 0)
    pos2 = (5, 1, -6)
    pos3 = (3.5, -10.5, 7)

    v_unit = e ** (2j * pi / 3)

    assert hextools.distance(pos1, pos2, "direct") == abs(5 + v_unit)
    assert hextools.distance(pos2, pos3, "direct") == abs(1.5 + 11.5 * v_unit)

@pytest.mark.hextools
def test_iteration():
    hexgrid = hextools.HexGrid(5, 4, 0)
    hexgrid.sethex((2, 1), 'word')

    assert hexgrid.dimensions == (5, 4)

    elements = {key:value for key, value in hexgrid}

    assert len(elements) == 20
    assert set(elements.values()) == {0, 'word'}
