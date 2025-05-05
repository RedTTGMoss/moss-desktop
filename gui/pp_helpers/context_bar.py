from abc import ABC
from abc import abstractmethod
from functools import lru_cache
from typing import Tuple, Dict, List, Optional, TYPE_CHECKING

import pygameextra as pe

from gui.defaults import Defaults
from gui.literals import CONTEXT_BAR_DIRECTIONS

if TYPE_CHECKING:
    from gui.screens.main_menu import MainMenu


class ContextBar(pe.ChildContext, ABC):
    LAYER = pe.AFTER_LOOP_LAYER
    TEXT_COLOR = None
    TEXT_COLOR_INVERTED = None
    BUTTONS: Tuple[Dict[str, Optional[str]]] = ()
    INVERT = False
    CONTEXT_MENU_OPEN_DIRECTION: CONTEXT_BAR_DIRECTIONS = 'down'
    CONTEXT_MENU_OPEN_PADDING: int = 0

    # definitions from GUI
    icons: Dict[str, pe.Image]
    ratios: 'Ratios'

    # Scaled button texts
    texts: List[pe.Text]
    texts_inverted: List[pe.Text]

    @property
    def text_color(self):
        return self.TEXT_COLOR or Defaults.TEXT_COLOR_T

    @property
    def text_color_inverted(self):
        return self.TEXT_COLOR_INVERTED or Defaults.TEXT_COLOR_H

    def __init__(self, parent: 'MainMenu'):
        self.texts = []
        self.texts_inverted = []
        self.main_menu = parent
        self.initialized = False
        self.check_hover = True
        self.x_offset = 0
        self.y_offset = 0
        self.context_menu_count = 0
        super().__init__(parent.parent_context)

    @property
    @lru_cache()
    def buttons(self) -> List[pe.RectButton]:
        width, height = 0, 0
        buttons: List[pe.RectButton] = []
        for i, button in enumerate(self.BUTTONS):
            icon = self.icons[button['icon']]
            rect = pe.Rect(
                0, 0,
                self.texts[i].rect.width + icon.width * 1.5,
                self.ratios.main_menu_top_height
            )
            rect.inflate_ip(self.ratios.main_menu_x_padding, -self.ratios.main_menu_x_padding)
            disabled = button.get('disabled', False)
            buttons.append((
                pe.RectButton(
                    rect,
                    Defaults.TRANSPARENT_COLOR,
                    Defaults.BUTTON_ACTIVE_COLOR if button['action'] else Defaults.TRANSPARENT_COLOR,
                    action_set={
                        'l_click': {
                            'action': self.handle_action,
                            'args': (getattr(self, button['action']) if button['action'] else lambda: None,
                                     button.get('data', ())),
                        },
                        'r_click': {
                            'action': self.handle_new_context_menu,
                            'args': (getattr(self, context_menu), i)
                        } if (context_menu := button.get('context_menu')) else None,
                        'hover_draw': None,
                        'hover': None
                    },
                    disabled=(Defaults.BUTTON_DISABLED_COLOR if self.INVERT else Defaults.BUTTON_DISABLED_LIGHT_COLOR)
                    if disabled else False,
                    name=f'context_bar<{id(self)}>.button_{i}'
                )
            ))
            width += buttons[-1].area.width
            height += buttons[-1].area.height
        self.finalize_button_rect(buttons, width, height)

        return buttons

    def handle_action(self, action, data):
        self.quick_refresh()
        pe.button.Button.action_call({
            'action': action,
            'args': data
        })

    def handle_new_context_menu(self, context_menu_getter, index):
        if self.CONTEXT_MENU_OPEN_DIRECTION == 'down':
            ideal_position = self.buttons[index].area.bottomleft
            ideal_position = ideal_position[0], ideal_position[1] + self.CONTEXT_MENU_OPEN_PADDING
        elif self.CONTEXT_MENU_OPEN_DIRECTION == 'right':
            ideal_position = self.buttons[index].area.topright
            ideal_position = ideal_position[0] + self.CONTEXT_MENU_OPEN_PADDING, ideal_position[1]
        else:
            raise ValueError(f"Invalid CONTEXT_MENU_OPEN_DIRECTION '{self.CONTEXT_MENU_OPEN_DIRECTION}'")

        context_menu = context_menu_getter(ideal_position)
        if not context_menu:
            return
        if context_menu:
            context_menu()
            self.BUTTONS[index]['_context_menu'] = context_menu
            self.context_menu_count += 1

    def handle_context_menu_closed(self, button, button_meta):
        button_meta['_context_menu'] = None
        self.context_menu_count -= 1

    @abstractmethod
    def finalize_button_rect(self, buttons, width, height):
        ...

    @property
    def button_data_zipped(self):
        return zip(self.buttons, self.BUTTONS, self.texts, self.texts_inverted)

    def handle_scales(self):
        # Cache reset
        self.texts.clear()
        self.texts_inverted.clear()
        self.__class__.buttons.fget.cache_clear()

        # Handle texts so we know their size
        for button_meta in self.BUTTONS:
            self.texts.append(pe.Text(
                button_meta['text'], Defaults.MAIN_MENU_BAR_FONT, self.ratios.main_menu_bar_size,
                colors=self.text_color
            ))
            self.texts_inverted.append(pe.Text(
                button_meta['text'], Defaults.MAIN_MENU_BAR_FONT, self.ratios.main_menu_bar_size,
                colors=self.text_color_inverted
            ))

        # Process final text and icon positions inside button and padding
        for button, button_meta, button_text, button_text_inverted in self.button_data_zipped:
            # Position the icon with padding
            icon = self.icons[button_meta['icon']]
            icon_rect = pe.Rect(0, 0, *icon.size)

            icon_rect.midleft = button.area.midleft
            icon_rect.left += self.button_margin

            # Position the button text with padding
            button_text.rect.midleft = icon_rect.midright
            button_text.rect.left += self.button_padding
            button_text_inverted.rect.center = button_text.rect.center

            button_meta['icon_rect'] = icon_rect

            # Position the context icons with padding
            for icon_key in (
                    'context_menu', 'chevron_right', 'chevron_down', 'small_chevron_right', 'small_chevron_down'):
                context_icon = self.icons[icon_key]
                context_icon_rect = pe.Rect(0, 0, *context_icon.size)

                if 'right' in icon_key:
                    context_icon_rect.midright = button.area.midright
                else:
                    context_icon_rect.bottomright = button.area.bottomright
                    context_icon_rect.top -= self.button_margin / 2
                context_icon_rect.left -= self.button_margin / 2
                button_meta[f'{icon_key}_icon_rect'] = context_icon_rect

    @property
    def button_margin(self):
        return self.ratios.main_menu_button_margin

    @property
    def button_padding(self):
        return self.ratios.main_menu_button_padding

    @property
    def currently_inverted(self):
        return None

    def pre_loop(self):
        if not self.initialized:
            self.handle_scales()
            self.initialized = True

    def post_loop(self):
        self.x_offset = 0
        self.y_offset = 0

    def loop(self, x_offset: int = 0, y_offset: int = 0):
        x_offset = x_offset or self.x_offset
        y_offset = y_offset or self.y_offset
        for button, button_meta, button_text, button_text_inverted in self.button_data_zipped:
            if x_offset or y_offset:
                button.area.move_ip(x_offset, y_offset)
                button_meta['icon_rect'].move_ip(x_offset, y_offset)
                button_meta['context_menu_icon_rect'].move_ip(x_offset, y_offset)
                button_text.rect.move_ip(x_offset, y_offset)
                button_text_inverted.rect.move_ip(x_offset, y_offset)
            if inverted_id := button_meta.get('inverted_id'):
                is_inverted = (self.INVERT or inverted_id == self.currently_inverted)
            else:
                is_inverted = self.INVERT
            if is_inverted:
                pe.draw.rect(Defaults.SELECTED, button.area)
            pe.settings.game_context.buttons.append(button)
            if not button_meta['action']:
                button.active_resource = Defaults.TRANSPARENT_COLOR
            elif is_inverted:
                button.active_resource = Defaults.BUTTON_ACTIVE_COLOR_INVERTED
            else:
                button.active_resource = Defaults.BUTTON_ACTIVE_COLOR

            if self.check_hover:
                pe.button.check_hover(button)
            else:
                button.hovered = False
                button.render()

            if is_inverted:
                button_text_inverted.display()
            else:
                button_text.display()

            icon = self.icons[button_meta['icon']]
            if is_inverted:
                icon = self.icons.get(f'{button_meta["icon"]}_inverted', icon)
            icon.display(button_meta['icon_rect'].topleft)

            if context_icon_type := button_meta.get('context_icon'):
                if context_icon_type == 'context_menu':
                    context_icon = self.icons['context_menu'] if not is_inverted else self.icons[
                        'context_menu_inverted']
                    context_icon.display(button_meta['context_menu_icon_rect'].topleft)
                elif context_icon_type == 'chevron_right':
                    context_icon = self.icons['chevron_right'] if not is_inverted else self.icons[
                        'chevron_right_inverted']
                    context_icon.display(button_meta['chevron_right_icon_rect'].topleft)
                elif context_icon_type == 'chevron_down':
                    context_icon = self.icons['chevron_down'] if not is_inverted else self.icons[
                        'chevron_down_inverted']
                    context_icon.display(button_meta['chevron_down_icon_rect'].topleft)
                elif context_icon_type == 'small_chevron_right':
                    context_icon = self.icons['small_chevron_right'] if not is_inverted else self.icons[
                        'small_chevron_right_inverted']
                    context_icon.display(button_meta['small_chevron_right_icon_rect'].topleft)
                elif context_icon_type == 'small_chevron_down':
                    context_icon = self.icons['small_chevron_down'] if not is_inverted else self.icons[
                        'small_chevron_down_inverted']
                    context_icon.display(button_meta['small_chevron_down_icon_rect'].topleft)

            if button.disabled:
                pe.draw.rect(Defaults.BUTTON_DISABLED_COLOR if self.INVERT else Defaults.BUTTON_DISABLED_LIGHT_COLOR,
                             button.area)

            if context_menu := button_meta.get('_context_menu'):
                if context_menu.is_closed:
                    self.handle_context_menu_closed(button, button_meta)
                context_menu()

            if x_offset or y_offset:
                button.area.move_ip(-x_offset, -y_offset)
                button_meta['icon_rect'].move_ip(-x_offset, -y_offset)
                button_meta['context_menu_icon_rect'].move_ip(-x_offset, -y_offset)
                button_text.rect.move_ip(-x_offset, -y_offset)
                button_text_inverted.rect.move_ip(-x_offset, -y_offset)
