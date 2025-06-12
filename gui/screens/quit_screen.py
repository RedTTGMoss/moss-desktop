from typing import TYPE_CHECKING

import pygameextra as pe

from gui.defaults import Defaults
from gui.gui import APP_NAME
from gui.screens.mixins import LogoMixin
from gui.i10n import t

if TYPE_CHECKING:
    from gui.gui import GUI


class QuitScreen(pe.ChildContext, LogoMixin):
    LAYER = pe.AFTER_LOOP_LAYER

    def __init__(self, parent: "GUI"):
        super().__init__(parent)
        Defaults.BACKGROUND = (200, 190, 190)
        Defaults.TEXT_COLOR = [(30, 10, 10), None]
        self.initialize_logo_and_line()
        self.quit_text = pe.Text(
            t("quit.quitting"),
            Defaults.CUSTOM_FONT, self.ratios.pixel(20), colors=Defaults.TEXT_COLOR)
        self.love_text = pe.Text(
            t("quit.thanks"),
            Defaults.CUSTOM_FONT_BOLD, self.ratios.pixel(20), colors=Defaults.TEXT_COLOR
        )
        self.quit_text.rect.midtop = self.line_rect.midbottom
        self.love_text.rect.midtop = self.quit_text.rect.midbottom
        self.love_text.rect.top += self.ratios.pixel(20)

        self.icon = parent.icons.get('heart')
        if self.icon:
            self.icon_rect = pe.Rect(0, 0, *self.icon.size)
            self.icon_rect.midleft = self.love_text.rect.midright
            self.icon_rect.left += self.ratios.pixel(10)

    def close(self):
        self.close_screen()

    def loop(self):
        self.logo.display()
        self.quit_text.display()
        self.love_text.display()
        if self.icon:
            self.icon.display(self.icon_rect.topleft)
