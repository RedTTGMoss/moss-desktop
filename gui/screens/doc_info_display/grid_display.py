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
        preview_rect = (0, 0, self.viewer.document_width, self.viewer.document_height)
        state.preview_size = preview_rect[2:]
        edge_rounding = int(state.gui.ratios.main_menu_document_rounding * self.viewer.scale)
        preview_masked = pe.Surface((self.viewer.document_width, self.viewer.document_height))

        with surface:
            with pe.mouse.Offset(state.button.area.topleft, reverse=True):
                if state.render_info.preview:
                    mask = pe.Surface((self.viewer.document_width, self.viewer.document_height))
                    with mask:
                        pe.draw.rect(  # Draw a filled rounded area for a preview mask
                            pe.colors.white,
                            preview_rect,
                            edge_rounding_topright=edge_rounding,
                            edge_rounding_bottomright=edge_rounding
                        )

                    # Blit and cut out the preview to the masked area
                    preview_masked.surface.blit(state.render_info.preview.get_finished_surface().surface, (0, 0))
                    preview_masked.surface.blit(mask.surface, (0, 0), special_flags=pe.BLEND_RGBA_MULT)

                with preview_masked:
                    pe.draw.rect(  # Draw the notebook spine
                        Defaults.DOCUMENT_GRAY,
                        (0, 0, pe.display.get_width() * 0.07, pe.display.get_height())
                    )

                    pe.draw.rect(  # Draw the rounded outline around the preview
                        Defaults.SELECTED if state.button.hovered else Defaults.DOCUMENT_GRAY,
                        preview_rect, state.gui.ratios.outline if state.button.hovered else state.gui.ratios.line,
                        edge_rounding_topright=edge_rounding,
                        edge_rounding_bottomright=edge_rounding
                    )
                pe.display.blit(preview_masked)

        return surface
