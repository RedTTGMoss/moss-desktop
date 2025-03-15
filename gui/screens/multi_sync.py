from typing import TYPE_CHECKING, Dict

import pygameextra as pe

from gui.defaults import Defaults
from gui.screens.mixins import LogoMixin

if TYPE_CHECKING:
    from gui.gui import GUI
    from rm_api import API


class MultiSync(pe.ChildContext, LogoMixin):
    LAYER = pe.AFTER_LOOP_LAYER
    icons: Dict[str, pe.Image]
    api: 'API'
    logo: pe.Text
    line_rect: pe.Rect
    EVENT_HOOK = 'multi_sync_resize_check'

    def __init__(self, parent: 'GUI'):
        super().__init__(parent)
        self.initialize_logo_and_line()
        self.api.add_hook(self.EVENT_HOOK, self.resize_check_hook)
        self.progress = {}

    def update_progress_done(self, key, done: int):
        current = self.progress.get(key, [0, 0])
        current[0] = done
        self.progress[key] = current

    def update_progress_total(self, key, total: int):
        current = self.progress.get(key, [0, 0])
        current[1] = total
        self.progress[key] = current

    def _update_total_progress(self):
        self.progress['total'] = (
            sum(p[0] for p in self.progress.values()),
            sum(p[1] for p in self.progress.values())
        )

    def pre_loop(self):
        self._update_total_progress()

    def loop(self):
        self.logo.display()

        # Define the end of the progress bar's black outline to be hidden
        total_cutter = self.big_line_rect.scale_by(self._('total'), 0)
        total_cutter.right = self.big_line_rect.right

        # Calculate all progress keys rects
        progress_rects = {
            key: self.big_line_rect.scale_by(self._(key), 0).inflate(-10, -10)
            for key in self.progress.keys()
        }

        for progress_key in sorted(self.progress.keys(), key=lambda key: Defaults.PROGRESS_ORDER.index(key)):
            if progress_key == 'total':
                continue
            pe.draw.rect(Defaults.PROGRESS_COLOR[progress_key], progress_rects[progress_key], 0)

        pe.draw.rect(pe.colors.black, self.big_line_rect, 1)
        pe.draw.rect(self.BACKGROUND, total_cutter, 1)

    def _(self, key) -> float:
        """Calculates the percentage between 0 and 1 of the progress"""
        current = self.progress.get(key, (0, 0))
        if current[0] <= 0:
            return 0
        return min(1, current[1] / current[0])  # total / done

    def close(self):
        self.document_renderer.close()
        self.api.remove_hook(self.EVENT_HOOK)
        del self.close_screen()
