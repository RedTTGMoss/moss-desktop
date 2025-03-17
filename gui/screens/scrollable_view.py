from abc import ABC
from typing import TYPE_CHECKING

import pygameextra as pe

if TYPE_CHECKING:
    from gui import GUI


class ScrollableView(pe.Context, ABC):
    T = 20

    def __init__(self, gui: 'GUI'):
        self.gui = gui
        self.BACKGROUND = self.gui.BACKGROUND
        self._top = 0
        self.active_top = 0
        self.bottom = 0
        super().__init__()

    def handle_event(self, event):
        if self.in_focus and not self.gui.ctrl_hold and event.type == pe.MOUSEWHEEL:
            self.active_top += event.y * 50
            # active top is always a negative number

    @property
    def in_focus(self):
        rect = pe.Rect(*self.AREA)
        return rect.collidepoint(*pe.mouse.pos(False))

    @property
    def top(self):
        correct_top = min(0, max(self.active_top,
                                 (-self.bottom + self.height) - self.gui.ratios.main_menu_document_padding))
        self.active_top = int(
            (1 - self.T * self.gui.delta_time) * self.active_top + self.T * self.gui.delta_time * correct_top)
        if self.active_top - 5 < self._top < self.active_top + 5:
            return self._top
        self._top = int((1 - self.T * self.gui.delta_time) * self._top + self.T * self.gui.delta_time * self.active_top)

        return self._top

    def reset_top(self):
        self.active_top = 0
        self._top = 0

    @property
    def buttons(self):
        for button in self.gui.button_manager.buttons_with_names.values():
            if button.display_reference == self.surface:
                yield button

    def post_loop(self):
        for button in self.buttons:
            if isinstance(button.area, pe.Rect):
                button_rect = button.area
            else:
                button_rect = pe.Rect(*button.area)
            screen_rect = pe.Rect(0, 0, *self.size)
            if button_rect.right > screen_rect.right:
                button_rect.width = screen_rect.right - button_rect.left
            if button_rect.bottom > screen_rect.bottom:
                button_rect.height = screen_rect.bottom - button_rect.top
            if button_rect.left < screen_rect.left:
                button_rect.width -= screen_rect.left - button_rect.left
                button_rect.left = screen_rect.left
            if button_rect.top < screen_rect.top:
                button_rect.height -= screen_rect.top - button_rect.top
                button_rect.top = screen_rect.top
            if button_rect.width < 0:
                button_rect.width = 0
            if button_rect.height < 0:
                button_rect.height = 0
            if not isinstance(button.area, pe.Rect):
                button.area = button_rect
