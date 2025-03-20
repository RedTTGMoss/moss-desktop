from functools import lru_cache
from typing import Optional, Any

import pygameextra as pe

from rm_api.defaults import RM_SCREEN_SIZE, ZoomModes
from . import PDF_AbstractRenderer
from ..shared_model import LoadTask

# noinspection PyBroadException
try:
    import pymupdf
except Exception:
    pymupdf = None

# DPI / typographic measurement unit
PDF_SCALING = 227.54 / 72


# noinspection PyPep8Naming
class PDF_PyMuPDF_Viewer(PDF_AbstractRenderer):
    pdf: Optional[Any]

    def __init__(self, document_renderer):
        super().__init__(document_renderer)
        self.pdf = None
        self.extra_scale = {}
        self.previous_page = None

    def load(self):
        if self.pdf_raw:
            self.pdf = pymupdf.open(stream=self.pdf_raw, filetype='pdf')
        self.document_renderer.loading -= 1

    def render(self, page_uuid: str):
        if not self.pdf:
            return
        page = self.document.content.c_pages.get_page_from_uuid(page_uuid)
        if not page.redirect:
            return

        # Calculate the scale and remarkable scale of the page
        acceptable_width = RM_SCREEN_SIZE[0] * self.gui.ratios.rm_scaled(RM_SCREEN_SIZE[0])
        base_scale = self.document_renderer.zoom * self.gui.ratios.rm_scaled(RM_SCREEN_SIZE[0])

        page_index = page.redirect.value
        pdf_zoom_enhance = self.get_enhance_scale()
        task = self.task_get_page(page_index, pdf_zoom_enhance, acceptable_width)

        if not (task.loaded and self.document_renderer.zoom_ready):
            pdf_zoom_enhance = 1
            sprite = self.get_page(page_index, 1, acceptable_width)
        else:
            sprite = task.sprite

        # Scale the PDF to the screen
        scale = (base_scale * PDF_SCALING) / (pdf_zoom_enhance + self.extra_scale.get(page_index, 0))

        # Set the scale of the sprite
        sprite.scale = (scale, scale)

        if task.loaded and self.previous_page != page_uuid and self.extra_scale.get(page_index, None) is not None:
            # Automatically zoom the PDF to the width of the screen
            best_zoom = tuple(screen / pdf for screen, pdf in zip(self.gui.maintain_aspect_size, sprite.size))
            if self.document_renderer.document.content.zoom.zoom_mode == ZoomModes.BestFit:
                self.document_renderer.base_zoom *= min(*best_zoom)
            elif self.document_renderer.document.content.zoom.zoom_mode == ZoomModes.FitToWidth:
                self.document_renderer.base_zoom *= best_zoom[0]
            elif self.document_renderer.document.content.zoom.zoom_mode == ZoomModes.FitToHeight:
                self.document_renderer.base_zoom *= best_zoom[1]
            self.document_renderer.align_top()
            self.previous_page = page_uuid
            return
        elif not task.loaded and self.previous_page is None:
            return

        rect = pe.Rect(0, 0, *sprite.size)
        rect.center = self.document_renderer.center
        # Align the PDF to the top
        rect.top = rect.centery - (RM_SCREEN_SIZE[1] // 2) * base_scale

        screen_rect = pe.Rect(0, 0, *self.size)

        # Clip the visible area of the PDF
        clipped_area = screen_rect.clip(rect)

        # Remove the rect position from the clip
        clipped_area.move_ip(-rect.left, -rect.top)
        # Move the rect by the clipped area offset
        rect.move_ip(clipped_area.left, clipped_area.top)

        # Finally render the PDF
        sprite.display(rect.topleft, clipped_area)

    @lru_cache()
    def get_page(self, page, scale: float = 1, acceptable_width: int = None) -> pe.Sprite:
        pdf_page: pymupdf.Page = self.pdf[page]

        if acceptable_width:
            self.extra_scale[page] = acceptable_width / pdf_page.mediabox_size.x

        scale += self.extra_scale.get(page, 0)

        # Scale up the PDF if required
        matrix = pymupdf.Matrix(scale, scale)

        # noinspection PyUnresolvedReferences
        pix = pdf_page.get_pixmap(matrix=matrix)
        mode = "RGBA" if pix.alpha else "RGB"
        # noinspection PyTypeChecker
        sprite = pe.Sprite(sprite_reference=pe.pygame.image.frombuffer(pix.samples, (pix.width, pix.height), mode))
        return sprite

    @lru_cache()
    def task_get_page(self, page, scale: float = 1, acceptable_width: int = None) -> LoadTask:
        return LoadTask(self.get_page, page, scale, acceptable_width)

    def close(self):
        pass

    def handle_event(self, event):
        pass
