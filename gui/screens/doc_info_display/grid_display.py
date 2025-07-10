import time
from typing import Optional

import pygameextra as pe

from .shared_model import DocInfoDisplay, DocInfoState
from ...defaults import Defaults
from ...rendering import render_full_text


class GridDocInfoDisplay(DocInfoDisplay):
    def render_collection(self, state: 'DocInfoState', area: pe.Rect) -> pe.Surface:
        icon: pe.Sprite = self.gui.icons[
            (state.render_info.icon or 'folder') + ('_inverted' if state.render_info.selected else '')]
        rect = pe.Rect(
            0, 0, self.viewer.document_width, icon.height
        )
        rect.inflate_ip(state.gui.ratios.main_menu_folder_margin_x, state.gui.ratios.main_menu_folder_margin_y)
        state.rect = rect
        surface = pe.Surface(state.rect.size)
        invert_key = '_inverted' if state.render_info.selected else ''

        text: Optional[pe.Text] = getattr(state.render_info, f't_title_folder{invert_key}')
        star_icon = state.gui.icons['star' + invert_key]
        tag_icon = state.gui.icons['tag' + invert_key]

        icon_position = (  # Calculate the offset where the folder icon will be displayed
            state.gui.ratios.main_menu_folder_margin_x // 2,
            state.gui.ratios.main_menu_folder_margin_y // 2
        )
        text_left_margin = icon.width + state.gui.ratios.main_menu_folder_padding  # Margin between icon and text

        # Calculate the available width for the text, accounting for icons and margins
        available_width = surface.width - (
                icon_position[0] + text_left_margin + state.gui.ratios.main_menu_folder_padding  # Base margin
                + (star_icon.width + state.gui.ratios.main_menu_folder_padding
                   if state.current_state['pinned'] else 0)  # If pinned, add star icon width + margin
                + (tag_icon.width + state.gui.ratios.main_menu_folder_padding
                   if state.current_state['tags'] else 0)  # If tags, add tag icon width + margin
        )
        state.set_trim_text_size('t_title_folder', available_width)

        if text:  # Position the text relative to the icon
            text.rect.midleft = icon_position
            text.rect.x += text_left_margin
            text.rect.y += icon.height // 1.5

        with surface:
            icon.display(icon_position)
            if text:  # Display the text if it exists and handle the icons too
                text.display()

                # Position the icons if applicable
                icon_rect = pe.Rect(*text.rect.topright, *star_icon.size)
                icon_rect.x += state.gui.ratios.main_menu_folder_padding
                icon_rect.centery = surface.height // 2  # Center vertically

                if state.current_state['pinned']:
                    star_icon.display(icon_rect.topleft)
                    icon_rect.x += star_icon.width + state.gui.ratios.main_menu_folder_padding

                if state.current_state['tags']:
                    tag_icon.display(icon_rect.topleft)

            if state.button.hovered:  # Highlight the button if hovered
                pe.draw.rect(Defaults.OUTLINE_COLOR, (0, 0, *surface.size), self.gui.ratios.outline)

            # Debug updates to this surface
            # w = (time.time() * 100) % surface.width
            # pe.draw.line(pe.colors.red, (w, 0), (w, surface.height), 2)
        return surface

    def render_document(self, state: DocInfoState, area: pe.Rect) -> pe.Surface:
        surface = pe.Surface((self.viewer.document_width, self.viewer.full_document_height))
        state.preview_size = preview_size = (self.viewer.document_width, self.viewer.document_height)
        preview = self.render_document_preview(state, preview_size)  # Get the preview for the document
        text = state.render_info.t_title  # Get the title text for the document

        if text:
            text.rect.top = state.preview_size[1]
            text.rect.left = 0

        state.set_trim_text_size('t_title', surface.width)

        with surface:
            if state.button.hovered:
                pe.draw.rect(Defaults.BUTTON_ACTIVE_COLOR, (0, 0, *surface.size))

            pe.display.blit(preview)

            if text:
                text.display()

            # Debug updates to this surface
            # w = (time.time() * 100) % surface.width
            # pe.draw.line(pe.colors.red, (w, 0), (w, surface.height), 2)

            # with pe.mouse.Offset(state.button.area.topleft, reverse=True):
        return surface
