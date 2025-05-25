import time
from typing import TYPE_CHECKING, List, Tuple, Optional

import pygameextra as pe
from lxml import etree
from lxml.etree import Element

from gui.i18n import t
from gui.pp_helpers import ContextMenu
from gui.screens.scrollable_view import ScrollableView
from .settings_view import SettingsView
from ...extensions.shared_types import TContextButton

if TYPE_CHECKING:
    from . import Settings


def parse_menu_xml(data: bytes):
    tree: Element = etree.fromstring(data)
    root_tag = tree.tag
    if root_tag == 'menu':
        menu_items = []
        for item in tree.findall('item'):
            menu_item = {
                'text': item.findtext('text'),
                'icon': item.findtext('icon'),
                'action': item.findtext('action') or 'moss',
                'data': item.findtext('data')
            }
            menu_items.append(menu_item)
        return menu_items, root_tag
    elif root_tag == 'view':
        return tree, root_tag


class BackButton(ContextMenu):
    ENABLE_OUTLINE = False

    BUTTONS = (
        {
            'text': t("menu.settings.back"),
            'icon': 'chevron_left',
            'action': 'back'
        },
    )

    def __init__(self, settings: 'Settings'):
        self.settings = settings
        super().__init__(settings, (0, 0))

    def back(self):
        self.settings.sidebar.transitioning = True
        self.settings.sidebar.transitioning_back = True
        self.settings.sidebar.transitioning_time = time.time()

    def finalize_button_rect(self, buttons, width, height):
        # Rescale and position the buttons
        y = self.top
        for button in buttons:
            button.area.width = self.ratios.main_menu_side_bar_width
            button.area.height = self.ratios.main_menu_top_height
            button.area.left = self.left

            button.area.top = y
            y += button.area.height

        self.rect = pe.Rect(self.left, self.top, self.ratios.main_menu_side_bar_width, self.ratios.main_menu_top_height)


def generate_missing_menu(data, menu_id):
    return data.get('xml_missing_menu_template').decode().format(menu_id).encode()


class SettingsContextMenu(ContextMenu):
    ENABLE_OUTLINE = False

    def __init__(self, settings: 'Settings', menu: List[TContextButton]):
        self.settings = settings
        # noinspection PyTypeChecker
        self.BUTTONS = [
            {
                **item,
                'inverted_id': item['data']
            } for item in menu
        ]
        # Add space for the back button and initialize the buttons
        super().__init__(settings, (0, 0))

    def finalize_button_rect(self, buttons, width, height):
        # Rescale and position the buttons
        y = self.top
        for button in buttons:
            button.area.width = self.ratios.main_menu_side_bar_width
            button.area.height = self.ratios.main_menu_top_height
            button.area.left = self.left

            button.area.top = y
            y += button.area.height

            # button.display_reference = self.settings.sidebar.surface

        self.rect = pe.Rect(self.left, self.top, self.ratios.main_menu_side_bar_width, y)

    def open_sub(self, item):
        if self.settings.sidebar.transitioning:  # Prevent accidental double menu clicks
            return
        menu = self.data.get(item)
        if menu:
            xml, root_tag = parse_menu_xml(menu)
        else:
            xml, root_tag = parse_menu_xml(generate_missing_menu(self.data, item))
        if root_tag == 'menu':
            self.settings.sidebar.transitioning = True
            self.settings.sidebar.transitioning_time = time.time()
            self.settings.sidebar.append(
                SettingsContextMenu(self.settings, xml)
            )
        else:
            self.currently_inverted = item
            self.settings.xml_interactor = SettingsView(self.settings, xml, self.settings)

    @property
    def currently_inverted(self):
        return self.settings.sidebar.currently_inverted

    @currently_inverted.setter
    def currently_inverted(self, value):
        self.settings.sidebar.currently_inverted = value

    def __getattr__(self, item):
        if item == 'moss':
            return self.open_sub
        return super().__getattr__(item)


class SettingsSidebarChain(ScrollableView):
    LAYER = pe.BEFORE_LOOP_LAYER
    TRANSITION_TIME = 0.2

    def __init__(self, settings: 'Settings'):
        self.stack: List[ContextMenu] = []
        self.settings = settings

        self.transitioning = False
        self.transitioning_back = False
        self.transitioning_time: Optional[float] = None

        self.currently_inverted = None

        self.AREA = (
            0, self.settings.ratios.main_menu_top_height,
            self.settings.ratios.main_menu_side_bar_width,
            self.settings.height - self.settings.ratios.main_menu_top_height
        )

        super().__init__(settings.parent_context)

        self.append(SettingsContextMenu(settings, self.settings.MENUS))

    def get_surface(self, context_menu: ContextMenu, position: Tuple[int, int] = (0, 0)):
        context_menu.check_hover = self.in_focus
        surface = pe.Surface(context_menu.rect.size)
        with surface:
            context_menu.draw_with_offset(*position)
        return surface

    def append(self, context_menu: ContextMenu):
        self.stack.append(context_menu)
        context_menu.handle_scales()

    def loop(self):
        # Get the current and previous context menus
        previous = self.stack[-2] if len(self.stack) > 1 else None
        current = self.stack[-1]

        if not self.transitioning:
            # Display the current context menu by default
            pos = (0, self.top)
            surface = self.get_surface(current, pos)
            self.bottom = surface.height
            pe.display.blit(surface)
        elif self.transitioning_back and not previous:
            # If we are on the main menu and back is pressed just exit the settings
            self.settings.close()
        else:
            # Calculate the transition progress
            delta = time.time() - self.transitioning_time
            t = min(1, delta / self.TRANSITION_TIME)
            if self.transitioning_back:
                t = 1 - t

            # Handle the end of the transition
            if t >= 1 or self.transitioning_back and t <= 0:
                self.transitioning = False
                self.transitioning_time = None
                self.reset_top()
                if self.transitioning_back:
                    self.stack.pop()
                    self.transitioning_back = False

            # Calculate the positions of the two context menus
            pos1 = (-self.settings.ratios.main_menu_side_bar_width * t, 0 if self.transitioning_back else self.top)
            pos2 = (
                self.settings.ratios.main_menu_side_bar_width - self.settings.ratios.main_menu_side_bar_width * t,
                self.top if self.transitioning_back else 0)

            # Prepare both context menus
            surface1 = self.get_surface(previous, pos1)
            surface2 = self.get_surface(current, pos2)

            # Add a fading transition effect
            surface1.set_alpha(255 - 255 * t)
            surface2.set_alpha(255 * t)

            # Display both context menus
            pe.display.blit(surface1, (pos1[0], 0))
            pe.display.blit(surface2, (pos2[0], 0))

    def handle_resize(self):
        self.resize((
            self.settings.ratios.main_menu_side_bar_width,
            self.settings.height - self.settings.ratios.main_menu_top_height
        ))

    def handle_event(self, event):
        super().handle_event(event)
        if pe.event.key_DOWN(pe.K_ESCAPE) or pe.event.key_DOWN(pe.KSCAN_ESCAPE):
            # Go back through the settings when pressing the escape button
            self.settings.back_button.back()
