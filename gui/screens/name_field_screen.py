from typing import TYPE_CHECKING

import pygameextra as pe

from gui.defaults import Defaults
from gui.events import ResizeEvent
from gui.i10n import t
from gui.rendering import render_button_using_text
from gui.screens.mixins import TitledMixin, ButtonReadyMixin

if TYPE_CHECKING:
    from gui import GUI


class CustomInputBox(pe.InputBox):
    def __init__(self, gui: 'GUI', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gui = gui
        self._padding = gui.ratios.field_screen_input_padding

    def display(self):
        pe.draw.line(
            Defaults.LINE_GRAY,
            (self.area.left + self._padding, self.area.bottom),
            (self.area.right - self._padding, self.area.bottom),
            self.gui.ratios.line
        )
        super().display()

    def draw_cursor(self, active_blink: bool):
        if not active_blink:
            return
        pe.draw.line(Defaults.LINE_GRAY, (self.cursor_x, self.text.rect.top), (self.cursor_x, self.text.rect.bottom),
                     self.gui.ratios.line)

    def draw_selection(self):
        selection_rect = self.selected_text.rect.copy()
        selection_rect.height += (self.area.bottom - selection_rect.bottom) * 2
        selection_rect.bottom = self.area.bottom
        pe.draw.rect(self.selected_text.background, selection_rect, 0)
        self.selected_text.display()


class NameFieldScreen(pe.ChildContext, ButtonReadyMixin, TitledMixin):
    LAYER = pe.AFTER_LOOP_LAYER

    field: pe.InputBox

    parent_context: 'GUI'

    BUTTON_TEXTS = {
        **ButtonReadyMixin.BUTTON_TEXTS,
    }

    EVENT_HOOK_NAME = 'name_field_screen_resize_check<{0}>'

    def __init__(self, gui: 'GUI', title, text='', on_submit=None, on_cancel=None, empty_ok: bool = False,
                 submit_text: str = None, cancel_text: str = None):
        self.title = title
        self.empty_ok = empty_ok
        self.on_submit = on_submit
        self.on_cancel = on_cancel
        super().__init__(gui)

        self.BUTTON_TEXTS['ok_button'] = submit_text or t("name_field.submit")
        self.BUTTON_TEXTS['cancel'] = cancel_text or t("name_field.cancel")

        self.handle_title(title)
        self.handle_texts()

        self.field = CustomInputBox(
            gui,
            (0, self.title_bottom, self.width, gui.ratios.field_screen_input_height),
            Defaults.DOCUMENT_TITLE_FONT,
            text, gui.ratios.field_screen_input_size,
            text_colors=Defaults.DOCUMENT_TITLE_COLOR,
            selected_colors=Defaults.DOCUMENT_TITLE_COLOR_INVERTED,
            return_action=self.ok,
        )
        self.field.focus()

        gui.add_screen(self)
        self.api.add_hook(self.EVENT_HOOK_NAME.format(id(self)), self.resize_check_hook)

    @property
    def text(self):
        return self.field.value

    def close(self, cancelled=True):
        self.api.remove_hook(self.EVENT_HOOK_NAME.format(id(self)))
        if self.on_cancel and cancelled:
            self.on_cancel()
        self.close_screen()

    def ok(self):
        if not self.empty_ok and not self.text:
            return
        if self.on_submit:
            self.on_submit(self.text)
        self.close(False)

    def resize_check_hook(self, event):
        if isinstance(event, ResizeEvent):
            self.field.area.width = self.width
            self.calculate_texts()

    def loop(self):
        self.title.display()
        self.field.display()

        render_button_using_text(self.parent_context, self.texts['cancel'], outline=self.ratios.outline,
                                 action=self.close, name='name_field_screen.cancel')

        render_button_using_text(self.parent_context, self.texts['ok_button'], outline=self.ratios.outline,
                                 action=self.ok, name='name_field_screen.ok_button',
                                 disabled=False if self.empty_ok or self.text else (0, 0, 0, 50))

    def post_loop(self):
        if not self.field.focused and not pe.mouse.clicked()[0]:
            self.field.focus()
