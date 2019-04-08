import cmath

import numpy as np
from PIL import Image, ImageDraw

from hextools import AOTRANSFORM

_R3 = 3 ** 0.5  # Square root of 3 precomputed for convenience
_BLACK = '#000000'

COLORS = {
    'water': '#1e7dbb',
    'swamp': '#3a173e',
    'desert': '#fecd0d',
    'mountains': '#9a9899',
    'forest': '#199239',
    'blue': '#3232e8',
    'green': '#009a00',
    'white': '#ffffff',
    'black': '#000000',
    'red': '#b82222',
    'p1': '#6b4cd1',
    'p2': '#cf2537',
    'p3': '#f5a044',
    'p4': '#44b6f4',
    'p5': '#55db53', # Chose a new color here to avoid player similarity
}


def draw_hex_grid(grid, scale, color_func, path, final_func=None):
    """Draws a HexGrid object to an image.

    Args:
        grid: HexGrid object to draw.
        scale: Side length of hexagons in pixels.
        color_func: Function from entries of grid to colors.
        path: Filepath to save image to.
        final_func: Function to draw any details other than the hexagons.
    """
    dim = grid.dimensions
    grid_dim = (
        int(2 * scale * (0.25 + 0.75 * dim[0])),
        int(_R3 * scale * (0.5 + dim[1])) + 1,
    )

    image = Image.new("RGB", grid_dim)

    drawer = ImageDraw.Draw(image)
    for pos, tile in grid:
        center = scale * (_R3 * np.dot(AOTRANSFORM, pos[:2]) +
                          [1, _R3 / 2])
        draw_poly(drawer,
                  center=center,
                  sides=6,
                  scale=scale,
                  color=color_func(tile),
                  border=COLORS['white']
                  )

        if final_func is not None:
            final_func(drawer, center, scale, tile)

    image.save(path)


def draw_poly(drawer, center, sides, scale, color=None, border=None, rotation=0):
    """Draw a regular polygon.

    Args:
        drawer: PIL.ImageDraw.Draw object.
        center: Center of the polygon.
        sides: Integer number of sides.
        scale: Side length of the polygon.
        color: Pillow ImageColor compatible color of the polygon.
            Unfilled if None 
        border: Color for the border. If None, no border is drawn.
        rotation: Rotation of the resulting polygon, in radians. If rotation
            is 0, the polygon will have a flat side on top.
    """
    if color is None and border is None:
        raise ValueError("There must be a value for color or border.")

    center = center[0] + center[1] * 1j

    # Repeat the first coordinate at the end to make border drawing simpler.
    corners = [
        center + cmath.rect(scale, 2 * k * cmath.pi / sides + rotation)
        for k in range(sides + 1)
    ]
    corners = [(z.real, z.imag) for z in corners]

    if color is not None:
        drawer.polygon(corners[:sides], fill=color)

    if border is not None:
        for i in range(sides):
            drawer.line(
                (corners[i], corners[i + 1]), fill=border, width=(scale // 10)
            )


def draw_components(drawer, center, scale, tile):
    """Draw Cryptid components in a hex.

    Args:
        drawer: PIL.ImageDraw.Draw object.
        center: Center of the board hexagon.
        scale: Side length of the hexagon.
        tile: gameboard.Hex object representing board hexagon.
    """
    # Draw any animal territories on the tile
    if tile.animal is not None:
        animal_color = {'bear': 'black', 'cougar': 'red'}[tile.animal]
        draw_poly(drawer,
                  center=center,
                  sides=6,
                  scale=int(0.8 * scale),
                  border=COLORS[animal_color],
                  )

    # Draw any structure on the tile
    if tile.structure is not None:
        struct, color = tile.structure
        border = 'white' if color == 'black' else 'black'

        if struct == 'shack':
            struct_center = [center[0], center[1] + 0.45 * scale]
            draw_poly(drawer,
                      center=struct_center,
                      sides=3,
                      scale=int(0.5 * scale),
                      color=COLORS[color],
                      border=COLORS[border],
                      rotation=cmath.pi / 6,
                      )
        else:
            struct_center = [center[0], center[1] + 0.35 * scale]
            draw_poly(drawer,
                      center=struct_center,
                      sides=8,
                      scale=int(0.4 * scale),
                      color=COLORS[color],
                      border=COLORS[border],
                      rotation=cmath.pi / 8,
                      )

    player_count = len(tile.players) - tile.players.count(None)
    if player_count:
        draw_width = 0.4 * scale * (player_count - 1)
        used_count = 0
        for player, truth in enumerate(tile.players):
            if truth is not None:
                x, y = center
                x += used_count * 0.4 * scale - draw_width / 2
                y -= 0.15 * scale

                used_count += 1

                if truth:
                    draw_poly(drawer,
                              center=(x, y),
                              sides=20,
                              scale=int(0.3 * scale),
                              color=COLORS[f'p{player + 1}'],
                              #border=COLORS['black'],
                              )
                else:
                    draw_poly(drawer,
                              center=(x, y),
                              sides=4,
                              scale=int(0.3 * scale),
                              color=COLORS[f'p{player + 1}'],
                              #border=COLORS['black'],
                              rotation=cmath.pi / 4,
                              )



def draw_board(grid, scale, path):
    """Draws a cryptid board."""
    def color_map(tile):
        return COLORS[tile.terrain]
    draw_hex_grid(grid, scale, color_map, path, draw_components)
