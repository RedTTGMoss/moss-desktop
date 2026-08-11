from functools import wraps
from typing import Annotated

import pygameextra as pe
from extism import Json

from . import definitions as d
from ..shared_types import (
    TTextColors,
    text_colors_to_tuple,
    TRect,
    rect_to_pe_rect,
    rect_from_pe_rect,
)


def text_wrap(fn):
    fn.__annotations__.pop("t")
    fn.__annotations__ = {"text_id": int, **fn.__annotations__}

    @wraps(fn)
    def wrapped(text_id: int, *args, **kwargs):
        return fn(d.extension_manager.texts[text_id], *args, **kwargs)

    return wrapped


@d.host_fn()
@d.transform_to_json
def moss_text_make(
    text: str, font: str, font_size: int, colors: Annotated[TTextColors, Json]
) -> int:
    text = pe.Text(text, font, font_size, colors=text_colors_to_tuple(colors))
    d.extension_manager.texts[id(text)] = text
    return id(text)


@d.host_fn()
@text_wrap
def moss_text_set_text(t: pe.Text, text: str) -> Annotated[TRect, Json]:
    t.text = text
    t.position = t.rect.center
    t.init()
    return rect_from_pe_rect(t.rect)


@d.host_fn()
@text_wrap
def moss_text_set_font(t: pe.Text, font: str, font_size: int) -> Annotated[TRect, Json]:
    t.font = pe.text.get_font(font, font_size)
    t.position = t.rect.center
    t.init()
    return rect_from_pe_rect(t.rect)


@d.host_fn()
@text_wrap
def moss_text_set_rect(t: pe.Text, rect: Annotated[TRect, Json]):
    t.rect = rect_to_pe_rect(rect)


@d.host_fn()
@text_wrap
def moss_text_get_rect(t: pe.Text) -> Annotated[TRect, Json]:
    return rect_from_pe_rect(t.rect)


@d.host_fn()
@text_wrap
def moss_text_display(t: pe.Text):
    t.display()
