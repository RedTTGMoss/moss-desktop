from typing import TYPE_CHECKING

import pygameextra as pe

from gui.defaults import Defaults
from gui.i10n import t

if TYPE_CHECKING:
    from gui.aspect_ratio import Ratios


class ButtonReadyMixin:
    BUTTON_TEXTS = {
        'cancel': "Cancel",
    }
    ratios: 'Ratios'
    texts: dict[str, pe.Text]
    width: int
    height: int

    def handle_texts(self, **kwargs):
        self.texts = {
            key: pe.Text(
                t(text, None, **kwargs),
                Defaults.BUTTON_FONT, self.ratios.import_screen_button_size,
                colors=Defaults.TEXT_COLOR_T)
            for key, text in self.BUTTON_TEXTS.items()
        }
        self.calculate_texts()

    def calculate_texts(self):
        right = self.width - self.ratios.import_screen_button_margin
        for text in self.texts.values():
            text.rect.height = max(text.rect.height, self.ratios.import_screen_button_size)
            text.rect.centery = self.height - self.ratios.import_screen_button_margin
            text.rect.right = right
            text.position = text.rect.center
            right = text.rect.left - self.ratios.import_screen_button_margin
