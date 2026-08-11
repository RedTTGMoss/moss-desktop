from typing import TYPE_CHECKING

import pygameextra as pe

from gui import APP_NAME
from gui.defaults import Defaults
from gui.events import ResizeEvent

if TYPE_CHECKING:
    from gui.aspect_ratio import Ratios


class LogoMixin:
    logo: pe.Text
    line_rect: pe.Rect
    big_line_rect: pe.Rect
    ratios: "Ratios"
    width: int
    height: int

    def resize_check_hook(self, event):
        if isinstance(event, ResizeEvent):
            self.initialize_logo_and_line()

    def initialize_logo_and_line(self):
        self._logo = pe.Text(
            APP_NAME,
            Defaults.LOGO_FONT,
            self.ratios.loader_logo_text_size,
            pe.math.center(
                (
                    0,
                    0,
                    self.width,
                    self.height
                    - (
                        self.ratios.loader_loading_bar_height
                        + self.ratios.loader_loading_bar_padding
                    ),
                )
            ),
            Defaults.TEXT_COLOR,
        )
        self.line_rect = pe.Rect(
            0,
            0,
            self.ratios.loader_loading_bar_width,
            self.ratios.loader_loading_bar_height,
        )
        self.line_rect.midtop = self._logo.rect.midbottom
        self.line_rect.top += self.ratios.loader_loading_bar_padding

        self.big_line_rect = pe.Rect(
            0,
            0,
            self.ratios.loader_loading_bar_big_width,
            self.ratios.loader_loading_bar_big_height,
        )
        self.big_line_rect.midtop = self._logo.rect.midbottom
        self.big_line_rect.top += self.ratios.loader_loading_bar_padding

    @property
    def logo(self):
        if (
            self._logo.color != Defaults.TEXT_COLOR[0]
            or self._logo.background != Defaults.TEXT_COLOR[1]
        ):
            self.initialize_logo_and_line()
        return self._logo
