"""A library to allow easy manipulation of hexagonal grids"""


import numpy as np

# Square root of 3
_ROOT3 = np.sqrt(3)

# Transformation matrices to switch between coordinates.
# Hexagonal to Rectangular
HRTRANSFORM = np.array([[.5, .5], [0, 1]])
# Rectangular to Hexagonal
RHTRANSFORM = np.array([[2, -1], [0, 1]])
# Axial to Orthonormal
AOTRANSFORM = np.array([[_ROOT3 / 2, 0], [0.5, 1]])
# Orthonormal to Axial
OATRANSFORM = np.array([[2 / _ROOT3, 0], [-1 / _ROOT3, 1]])
# Hexagonal to Array, needs floor dividing after
HSTRANSFORM = np.array([[0, 2], [2, -1]])


class GridMutationError(Exception):
    pass


class HexGrid:
    """A rectangular grid of hexagons.

    Args:
        rows: Integer number of rows.
        columns: Integer number of columns.
        content: Something to put as a value for each hexagon.
        iterate_content: Boolean, whether content should be treated as an
            iterable of elements for each hex or not.
        scale: The length of a hexagon's side in orthonormal coordinates.
    """

    def __init__(self, rows, columns, content=None,
                 iterate_content=False, scale=1):
        if not isinstance(rows, int) or not isinstance(columns, int):
            raise TypeError

        if iterate_content:
            if rows * columns > len(content):
                raise ValueError("content has too few values.")
            cont_iter = iter(content)
            self._data = [
                [next(cont_iter) for j in range(columns)]
                for i in range(rows)
            ]

        else:
            self._data = [
                [content for j in range(columns)]
                for i in range(rows)
            ]

        self.scale = scale

    def __iter__(self):
        for i, row in enumerate(self._data):
            for j, elem in enumerate(row):
                yield array_to_axial(i, j), elem

    def copy(self):
        """Return a copy of self."""
        rows, cols = self.dimensions
        content = sum(self._data, [])
        return HexGrid(rows, cols, content, True, self.scale)

    def gethex(self, pos):  # pylint: disable=invalid-name
        """Get the contents of the hexagon at the given cubic coordinates.

        Args:
            pos: A pair (or triple) of integer cubic coordinates.

        Returns:
            The value stored for the given coordinates.
        """
        i, j = axial_to_array(*pos)
        return self._data[i][j]

    def sethex(self, pos, value):  # pylint: disable=invalid-name
        """Set the contents of the hexagon at the given cubic coordinates.

        Args:
            pos: A pair (or triple) of integer cubic coordinates.
            value: The value to set the hex to.
        """
        i, j = axial_to_array(*pos)
        self._data[i][j] = value

    @property
    def dimensions(self):
        """Return the dimensions of the grid."""
        return len(self._data), len(self._data[0])

    def nearest(self, x, y):  # pylint: disable=invalid-name
        """Given a set of orthonormal coordinates, find the nearest hex."""
        pixel = cubic(*np.dot(OATRANSFORM, [x, y]) / self.scale)
        rounded = [round(n) for n in pixel]
        diffs = [abs(p - r) for p, r in zip(pixel, rounded)]

        max_index = diffs.index(max(diffs))
        rounded[max_index] = sum(rounded) - rounded[max_index]

        return self.gethex(rounded)

    def flip_vertical(self, ignore_dimension=False):
        """Flip the grid in the vertical axis.

        Args:
            ignore_dimension: Boolean, suppresses the error when flipping a
                grid with even row count.

        Raises:
            GridMutationError: Reflecting would change connectivity of hexes.
        """

        if len(self._data) % 2 == 0 and not ignore_dimension:
            raise GridMutationError(
                "Reflections should have an odd number of rows.")

        self._data = self._data[::-1]

    def rotate(self, ignore_dimension=False):
        """Rotate the grid 180 degrees.

        Args:
            ignore_dimension: Boolean, suppresses the error when rotating a
                grid with odd row count.

        Raises:
            GridMutationError: Rotating would change connectivity of hexes.
        """

        if len(self._data) % 2 and not ignore_dimension:
            raise GridMutationError(
                "Rotations should have an even number of rows.")

        self._data = [row[::-1] for row in self._data[::-1]]

    def extend(self, other, axis=0):
        """Join another HexGrid to this one.

        Args:
            other: A HexGrid with compatible dimensions.
            axis: 0 for adding new rows, 1 for new columns.
        """
        if axis not in (0, 1):
            raise ValueError("axis must be 0 or 1.")

        if other.dimensions[1 - axis] != self.dimensions[1 - axis]:
            raise ValueError(
                "Dimensions of HexGrid objects must match in the non-stacking axis.")

        if axis == 0:
            self._data.extend(other._data)  # pylint: disable=protected-access
        else:
            for i, row in enumerate(self._data):
                row.extend(other._data[i])  # pylint: disable=protected-access


def array_to_axial(row, column):
    """Turn orthonormal array coordinates into axial hexagonal."""
    return row, column - (row >> 1)


def axial_to_array(u, v, w=None):  # pylint: disable=invalid-name, unused-argument
    """Get the array coordinate of a hexagon given in axial coordinates.
    Can take full cubic coordinates too."""
    return u, v + (u >> 1)


def cubic(u, v, w=None):  # pylint: disable=invalid-name, unused-argument
    """Get the full cubic coordinates of a hexagon, given the first two."""
    return u, v, -u - v


def distance(pos1, pos2, metric="grid"):
    """Get the distance between two pairs of cubic coordinates.

    Args:
        pos1, pos2: Pairs (or triples) of cubic coordinates.
        metric: A string giving the metric to calculate distance by.
            Current options are 'grid' which measures along hexagonal grid
            lines and 'direct', which calculates the Euclidean distance.

    Returns:
        Distance between positions as int if possible, otherwise float.
    """
    if metric == "grid":
        return _grid_dist(pos1, pos2)

    if metric == "direct":
        return _euclid_dist(pos1, pos2)

    raise ValueError('Value of metric must be either "grid" or "direct"')


def _grid_dist(pos1, pos2):
    pairs = zip(cubic(*pos1), cubic(*pos2))
    return max(abs(m - n) for m, n in pairs)


def _euclid_dist(pos1, pos2):
    du = pos2[0] - pos1[0]  # pylint: disable=invalid-name
    dv = pos2[1] - pos1[1]  # pylint: disable=invalid-name
    return np.sqrt(du ** 2 + dv ** 2 - du * dv)


def adjacent(cubic_pos):
    """Given a set of axial or cubic coordinates, get the adgacent hexagons."""
    full_cubic = list(cubic(*cubic_pos))
    for i in (0, 1, 2):
        for j in (0, 1, 2):
            if i != j:
                new_hex = full_cubic[:]
                new_hex[i] += 1
                new_hex[j] -= 1
                yield tuple(new_hex)


def expand(region, radius):
    """Grow a region to all hexes within radius.

    Args:
        region: Sequence of positions on the grid
        radius: Integer

    Returns:
        A set of cubic coordinate triples.
    """
    reg_set = {cubic(*pos) for pos in region}

    recent = reg_set.copy()
    for _ in range(radius):
        new_set = set()
        for pos in recent:
            new_set |= set(adjacent(pos))

        reg_set |= new_set
        recent = new_set - recent
        
    return reg_set
