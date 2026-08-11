from abc import ABC
from functools import lru_cache

from gui.screens.viewer.renderers.shared_model import AbstractRenderer


# noinspection PyPep8Naming
class PDF_AbstractRenderer(AbstractRenderer, ABC):
    def __init__(self, document_renderer):
        super().__init__(document_renderer)
        self.current_page = self.document_renderer.current_page_index

    @property
    @lru_cache
    def pdf_raw(self):
        try:
            return self.document.content_data[f"{self.document.uuid}.pdf"]
        except KeyError:
            self.error = "PDF file missing"
            return None
