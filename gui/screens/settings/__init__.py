from typing import TYPE_CHECKING, Dict

import pygameextra as pe

from .settings_menu import SettingsSidebarChain, BackButton, parse_menu_xml
from .settings_view import SettingsView
from ...defaults import Defaults
from ...events import ResizeEvent

if TYPE_CHECKING:
    from gui import GUI
    from gui.aspect_ratio import Ratios
    from rm_api import API
    from gui.extensions.extension_manager import ExtensionManager


class Settings(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER
    MENUS = [
        {
            "text": f"settings.moss.title",
            "icon": "moss",
            "action": "moss",
            "data": "xml_settings",
        }
    ]

    # definitions from GUI
    api: "API"
    extension_manager: "ExtensionManager"
    parent_context: "GUI"
    icons: Dict[str, pe.Image]
    ratios: "Ratios"

    def __init__(self, parent: "GUI"):
        super().__init__(parent)

        self.MENUS = [
            *self.MENUS,
            *list(self.extension_manager.extension_menus.values()),
        ]

        self.sidebar = SettingsSidebarChain(self)
        self.xml_interactor = SettingsView(
            self, parse_menu_xml(self.data.get(f"xml_settings/default"))[0], self
        )

        if len(self.sidebar.stack[0].BUTTONS) == 1:
            # If there is only one button in the sidebar, we open the moss settings directly
            self.sidebar.stack[0].open_sub("xml_settings")  # Open the default settings
            del self.sidebar.stack[0]  # Remove the empty menu from the stack
            self.sidebar.transitioning = False  # Reset the transitioning state
            self.sidebar.stack[-1].open_sub(
                "xml_settings/moss"
            )  # Open the moss settings

        self.back_button = BackButton(self)
        self.api.add_hook("settings_resize_check", self.handle_resize_event)

    def handle_resize_event(self, event):
        if isinstance(event, ResizeEvent):
            self.sidebar.handle_resize()
            self.xml_interactor.handle_resize()

    def loop(self):
        # Display the back button
        self.back_button()
        self.sidebar()
        self.xml_interactor()

    def post_loop(self):
        # Draw a separator line between the sidebar and the settings menu
        pe.draw.line(
            Defaults.OUTLINE_COLOR,
            (0, self.ratios.main_menu_top_height),
            (self.ratios.main_menu_side_bar_width, self.ratios.main_menu_top_height),
            w=self.ratios.line,
        )

        # Outline the end of the Side bar
        pe.draw.line(
            Defaults.OUTLINE_COLOR,
            (self.ratios.main_menu_side_bar_width, 0),
            (self.ratios.main_menu_side_bar_width, self.height),
            w=self.ratios.line,
        )

    def close(self):
        self.close_screen()

    def get(self, value, file=None):
        if file:
            return self.extension_manager.configs[file].get(value)
        return self.config.get(value)

    def set(self, key, value, file, value_type):
        if file:
            self.extension_manager.configs[file][key] = value
            if file not in self.extension_manager.dirty_configs:
                self.extension_manager.dirty_configs.append(file)
            return
        self.config[key] = value
        self.parent_context.dirty_config = True
