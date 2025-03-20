from abc import ABC
from typing import Tuple, TYPE_CHECKING

import pygameextra as pe

from gui.defaults import Defaults
from gui.pp_helpers.context_bar import ContextBar

if TYPE_CHECKING:
    from gui.screens.main_menu import MainMenu


class ContextMenu(ContextBar, ABC):
    ENABLE_OUTLINE = True
    CONTEXT_MENU_OPEN_DIRECTION = 'right'
    CLOSE_AFTER_ACTION: bool = False

    def __init__(self, parent: 'MainMenu', topleft: Tuple[int, int]):
        self.left, self.top = topleft
        self.is_closed = False
        self.waiting_for_let_go = True
        self.rect = pe.Rect(0, 0, 10, 10)

        super().__init__(parent)

    def pre_loop(self):
        pe.draw.rect(Defaults.SELECTED if self.INVERT else Defaults.BACKGROUND, self.rect)
        pe.button.action(self.rect, name=f'context_menu<{id(self)}>.blank_space')
        if self.ENABLE_OUTLINE:
            pe.draw.rect(Defaults.LINE_GRAY, self.rect, self.ratios.line)
        super().pre_loop()

    def close(self):
        if self.context_menu_count > 0:
            return
        self.is_closed = True

    def handle_context_menu_closed(self, button, button_meta):
        if button_meta['_context_menu'].CLOSE_AFTER_ACTION:
            super().handle_context_menu_closed(button, button_meta)
            return self.close()
        super().handle_context_menu_closed(button, button_meta)

    def handle_action(self, action, data):
        super().handle_action(action, data)
        if self.CLOSE_AFTER_ACTION:
            self.close()

    def post_loop(self):
        super().post_loop()
        if self.waiting_for_let_go:
            if not any(pe.mouse.clicked()):
                self.waiting_for_let_go = False
        elif any(pe.mouse.clicked()) and not self.rect.collidepoint(pe.mouse.pos()):
            self.close()

    def finalize_button_rect(self, buttons, width, height):
        x = self.left
        max_height = 0
        total_width = 0
        buttons_handled = 0
        while len(buttons) - buttons_handled > 0:
            column = []
            height = 0
            for button in buttons[buttons_handled:]:
                if height + button.area.height >= self.height:
                    break
                height += button.area.height
                column.append(button)

            max_width = max(button.area.width for button in column)

            y = self.top
            for button in column:
                button.area.topleft = x, y
                button.area.width = max_width
                y += button.area.height
            x += max_width

            total_width += max_width
            max_height = max(max_height, y - self.top)
            buttons_handled += len(column)

        self.rect = pe.Rect(self.left, self.top, total_width, max_height)
        self.rect.clamp_ip(pe.Rect(0, 0, self.width, self.height))
        if self.left != self.rect.left or self.top != self.rect.top:
            self.left, self.top = self.rect.topleft
            self.finalize_button_rect(buttons, width, height)

    def __call__(self):
        try:
            self.extension_manager.opened_context_menus.append(getattr(self, 'KEY', self.__class__.__name__))
        except AttributeError:
            pass
        super().__call__()

    def draw_with_offset(self, x_offset: int = 0, y_offset: int = 0):
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.parent_hooking()
