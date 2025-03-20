from functools import lru_cache
from typing import Tuple

import pygameextra as pe

from gui.defaults import Defaults


def hex_parser(hex_color: str):
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def defaults_parser(defaults: str):
    return getattr(Defaults, defaults)


def pe_parser(pe_color: str):
    return getattr(pe.colors, pe_color)


def get_single_color(color: str):
    parser, value = color.split(':')

    return {
        'hex': hex_parser,
        'defaults': defaults_parser,
        'pe': pe_parser
    }[parser](value)


@lru_cache()
def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(color_a, color_b, t):
    return tuple(
        lerp(a, b, t)
        for a, b in zip(color_a, color_b)
    )


def invert_color(color: Tuple[int, ...]) -> Tuple[int, ...]:
    return tuple(
        255 - c if i < 3 else c
        for i, c in enumerate(color)
    )


def ease_out_quad(t):
    return 1 - (1 - t) ** 2


def ease_in_quad(t):
    return t ** 2
