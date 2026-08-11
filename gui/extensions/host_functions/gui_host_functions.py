from typing import Type, Annotated

from box import Box
from extism import Json

from . import definitions as d
from ..shared_types import TContextMenu, context_button_clean
from ...helpers import invert_icon
from ...pp_helpers import ContextMenu


@d.host_fn()
def moss_gui_register_context_menu(menu: Annotated[TContextMenu, Json]):
    context_menu = Box(menu)

    class CustomContextMenu(ContextMenu):
        KEY = context_menu.key
        EXTENSION_NAME = d.extension_manager.current_extension
        BUTTONS = tuple(context_button_clean(button) for button in context_menu.buttons)
        ACTIONS = tuple(
            value
            for button in context_menu.buttons
            for key, value in button.items()
            if key == "action" and value is not None
        )
        PRE_LOOP = context_menu.get("pre_loop", None)
        POST_LOOP = context_menu.get("post_loop", None)
        INVERT = context_menu.get("invert", False)

        def pre_loop(self):
            if self.PRE_LOOP:
                d.extension_manager.action(self.PRE_LOOP, self.EXTENSION_NAME)()
            super().pre_loop()

        def post_loop(self):
            super().post_loop()
            if self.POST_LOOP:
                d.extension_manager.action(self.POST_LOOP, self.EXTENSION_NAME)()

        def __getattr__(self, item):
            if item in self.ACTIONS:
                return d.extension_manager.action(item, self.EXTENSION_NAME)
            return super().__getattr__(item)

    d.extension_manager.log(
        f"Registered context menu {d.extension_manager.current_extension}.{context_menu.key}"
    )

    d.extension_manager.context_menus[context_menu.key] = CustomContextMenu


@d.host_fn()
def moss_gui_open_context_menu(key: str, x: int, y: int):
    if not d.gui.main_menu:
        return
    context_menu_class: Type[ContextMenu] = d.extension_manager.context_menus[key]
    context_menu = context_menu_class(d.gui.main_menu, (x, y))
    d.gui.main_menu.context_menus[key] = context_menu


# Icons
@d.host_fn()
def moss_gui_invert_icon(key: str, result_key: str):
    invert_icon(d.gui, key, result_key)
