from typing import Any
from typing import TypedDict, List, Optional, Tuple

import pygameextra as pe


class TContextButton(TypedDict):
    text: str
    icon: str
    context_icon: Optional[str]
    action: Optional[str]
    context_menu: Optional[str]


class TContextMenu(TypedDict):
    key: str
    buttons: List[TContextButton]
    pre_loop: Optional[str]
    post_loop: Optional[str]
    invert: bool


class TColor(TypedDict):
    r: int
    g: int
    b: int
    a: Optional[int]


class TRect(TypedDict):
    x: int
    y: int
    width: int
    height: int


class TPygameExtraRectEdgeRounding(TypedDict):
    edge_rounding: Optional[int]
    edge_rounding_topright: Optional[int]
    edge_rounding_topleft: Optional[int]
    edge_rounding_bottomright: Optional[int]
    edge_rounding_bottomleft: Optional[int]


class TPygameExtraRect(TypedDict):
    color: TColor
    rect: TRect
    width: int
    edge_rounding: Optional[TPygameExtraRectEdgeRounding]


class TTextColors(TypedDict):
    foreground: TColor
    background: Optional[TColor]


class TScreen(TypedDict):
    key: str
    screen_pre_loop: Optional[str]
    screen_loop: str
    screen_post_loop: Optional[str]
    event_hook: Optional[str]


def rect_to_pe_rect(rect: TRect) -> pe.Rect:
    return pe.Rect(rect["x"], rect["y"], rect["width"], rect["height"])


def rect_from_pe_rect(rect: pe.Rect) -> TRect:
    return {"x": rect.x, "y": rect.y, "width": rect.width, "height": rect.height}


def color_from_tuple(
    color: Tuple[int, ...], allow_turn_to_none: bool = False
) -> Optional[TColor]:
    return (
        None
        if allow_turn_to_none and color is None or (len(color) == 4 and color[3] == 0)
        else {
            "r": color[0],
            "g": color[1],
            "b": color[2],
            **(
                {"a": color[3] if color[3] < 255 else None}
                if len(color) == 4
                else {"a": None}
            ),
        }
    )


def color_to_tuple(color: Optional[TColor]) -> Optional[Tuple[int, ...]]:
    if not color:
        return None
    return (
        (
            color["r"],
            color["g"],
            color["b"],
        )
        if color.get("a") is None or color["a"] == 255
        else (color["r"], color["g"], color["b"], color["a"])
    )


def context_button_clean(button: TContextButton, append: str = "") -> TContextButton:
    return {
        key: (
            (f"{append}{value}" if key in ("action", "context_menu") else value)
            if value
            else None
        )
        for key, value in button.items()
        if value or key == "action" and not value
    }


def text_colors_to_tuple(
    colors: TTextColors,
) -> Tuple[Tuple[int, ...], Optional[Tuple[int, ...]]]:
    return color_to_tuple(colors["foreground"]), color_to_tuple(colors["background"])


class TValue(TypedDict):
    value: Any
