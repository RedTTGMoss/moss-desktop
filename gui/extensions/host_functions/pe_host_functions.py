from typing import Annotated, Optional

import pygameextra as pe
from box import Box
from extism import Json

from . import definitions as d
from ..shared_types import color_to_tuple, rect_to_pe_rect, TPygameExtraRect, TScreen


@d.host_fn('_moss_pe_draw_rect')
def moss_pe_draw_rect(draw: Annotated[TPygameExtraRect, Json]):
    color, rect, width, edge_rounding = draw['color'], draw['rect'], draw['width'], draw['edge_rounding'] or {}
    pe.draw.rect(
        color_to_tuple(color), rect_to_pe_rect(rect), width,
        edge_rounding=edge_rounding.get('edge_rounding', -1) or -1,
        edge_rounding_topright=edge_rounding.get('edge_rounding_topright', -1) or -1,
        edge_rounding_topleft=edge_rounding.get('edge_rounding_topleft', -1) or -1,
        edge_rounding_bottomright=edge_rounding.get('edge_rounding_bottomright', -1) or -1,
        edge_rounding_bottomleft=edge_rounding.get('edge_rounding_bottomleft', -1) or -1
    )


@d.host_fn()
def moss_pe_register_screen(screen: Annotated[TScreen, Json]):
    screen = Box(screen)

    class CustomScreen(pe.ChildContext):
        KEY = screen.key
        LAYER = pe.AFTER_LOOP_LAYER
        EXTENSION_NAME = d.extension_manager.current_extension
        PRE_LOOP = screen.get('screen_pre_loop', None)
        LOOP = screen.screen_loop
        POST_LOOP = screen.get('screen_post_loop', None)
        EVENT_HOOK = screen.get('event_hook', None)

        def __init__(self, parent, initial_values: Optional[dict] = None):
            self.values = initial_values or {}
            self.event_hook_id = f'{self.EXTENSION_NAME}::{self.KEY}<{id(self)}>_API_HOOK'
            d.api.add_hook(self.event_hook_id, self.handle_hook)
            super().__init__(parent)

        @property
        def state(self):
            return d.extension_manager.raw_state

        def pre_loop(self):
            if self.PRE_LOOP:
                d.extension_manager.action(self.PRE_LOOP, self.EXTENSION_NAME)()

        def loop(self):
            d.extension_manager.action(self.LOOP, self.EXTENSION_NAME)()

        def post_loop(self):
            if self.POST_LOOP:
                d.extension_manager.action(self.POST_LOOP, self.EXTENSION_NAME)()

        def handle_hook(self, event):
            if self.EVENT_HOOK:
                d.extension_manager.action(self.EVENT_HOOK, self.EXTENSION_NAME)(event=event.__class__.__name__)

        def close(self):
            d.api.remove_hook(self.event_hook_id)
            self.close_screen()

    CustomScreen.__name__ = screen.key

    d.extension_manager.log(f"Registered screen {d.extension_manager.current_extension}.{screen.key}")

    d.extension_manager.screens[screen.key] = CustomScreen


@d.host_fn(name='_moss_pe_open_screen')
def moss_pe_open_screen(key: str, initial_values: Annotated[dict, Json]) -> int:
    screen_class = d.extension_manager.screens[key]
    screen = screen_class(d.gui, initial_values)
    d.gui.screens.put(screen)
    return id(screen)


@d.host_fn(signature=([], []))
def moss_pe_close_screen(*args):
    current_screen = d.gui.current_screen
    if close_function := getattr(current_screen, "close", None):
        close_function()
    else:
        raise ReferenceError("The current screen has no close procedure")


@d.host_fn()
@d.unpack
def moss_pe_set_screen_value(key: str, value: Annotated[dict, Json]):
    screen = d.gui.current_screen
    screen.values[key] = value


@d.host_fn()
@d.transform_to_json
def moss_pe_get_screen_value(key: str):
    screen = d.gui.current_screen
    if key == 'id':
        return id(screen)
    try:
        print(screen, key, getattr(screen, key))
        return getattr(screen, key)
    except AttributeError:
        return screen.values[key]
