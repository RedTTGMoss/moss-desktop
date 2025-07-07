import time

import pygameextra as pe

from .shared_model import DocInfoDisplay, DocInfoState


class GridDocInfoDisplay(DocInfoDisplay):
    def render_collection(self, state: DocInfoState, area: pe.Rect) -> pe.Surface:
        surface = pe.Surface((self.viewer.document_width, self.viewer.document_height))
        with surface:
            pe.fill.transparency(pe.colors.lightaqua, 50)
            pe.draw.rect(pe.colors.red, (0, 0, 10, 10))
        return surface

    def render_document(self, state: DocInfoState, area: pe.Rect) -> pe.Surface:
        surface = pe.Surface((self.viewer.document_width, self.viewer.document_height))
        with surface:
            with pe.mouse.Offset(state.button.area.topleft, reverse=True):
                pe.fill.transparency(pe.colors.lightaqua, 50)
                if state.gui.config.debug:
                    # Draw a line across the surface to indicate that the rendering is active
                    pe.draw.line(pe.colors.red, (0, 0), (surface.width, surface.height), 2)
                    pe.draw.line(pe.colors.red, (surface.width, 0), (0, surface.height), 2)
                    pe.draw.rect(pe.colors.green, ((time.time() * surface.width) % surface.width - 5, 0, 2, surface.height))

        return surface