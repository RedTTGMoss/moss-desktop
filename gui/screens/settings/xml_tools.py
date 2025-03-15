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
