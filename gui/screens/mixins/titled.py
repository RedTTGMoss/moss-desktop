from typing import TYPE_CHECKING

import pygameextra as pe

from gui.defaults import Defaults
from gui.i10n import t

if TYPE_CHECKING:
    from gui.aspect_ratio import Ratios


class TitledMixin:
    TITLE = "Title"
    ratios: 'Ratios'
    TITLE_COLORS = None
    title: pe.Text

    @property
    def title_colors(self):
        return self.TITLE_COLORS or Defaults.TEXT_COLOR

    def handle_title(self, title: str = None, **kwargs):
        self.title = pe.Text(t(title, kwargs=kwargs) or self.TITLE, Defaults.MAIN_MENU_FONT, self.ratios.titled_mixin_title_size,
                             colors=self.title_colors)

        self.title.rect.topleft = (
            self.ratios.titled_mixin_title_padding,
            self.ratios.titled_mixin_title_padding
        )

    @property
    def title_bottom(self):
        return self.title.rect.bottom + self.ratios.main_menu_top_padding
