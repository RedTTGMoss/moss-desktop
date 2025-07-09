import time

import pygameextra as pe

from .shared_model import DocInfoDisplay, DocInfoState
from ...defaults import Defaults


class GridDocInfoDisplay(DocInfoDisplay):
    def render_collection(self, state: DocInfoState, area: pe.Rect) -> pe.Surface:
        icon: pe.Sprite = self.gui.icons[
            (state.render_info.icon or 'folder') + ('_inverted' if state.render_info.selected else '')]
        rect = pe.Rect(
            0, 0, self.viewer.document_width, icon.height
        )
        rect.inflate_ip(state.gui.ratios.main_menu_folder_margin_x, state.gui.ratios.main_menu_folder_margin_y)
        state.rect = rect
        surface = pe.Surface(state.rect.size)

        icon_position = (
            state.gui.ratios.main_menu_folder_margin_x // 2,
            state.gui.ratios.main_menu_folder_margin_y // 2
        )
        with surface:
            icon.display(icon_position)
            if state.button.hovered:
                pe.draw.rect(Defaults.OUTLINE_COLOR, (0, 0, *surface.size), self.gui.ratios.outline)
        return surface

    def render_document(self, state: DocInfoState, area: pe.Rect) -> pe.Surface:
        surface = pe.Surface((self.viewer.document_width, self.viewer.full_document_height))
        state.preview_size = preview_size = (self.viewer.document_width, self.viewer.document_height)
        preview = self.render_document_preview(state, preview_size)

        with surface:
            if state.button.hovered:
                pe.draw.rect(Defaults.BUTTON_ACTIVE_COLOR, (0, 0, *surface.size))

            pe.display.blit(preview)

            # with pe.mouse.Offset(state.button.area.topleft, reverse=True):

        return surface
