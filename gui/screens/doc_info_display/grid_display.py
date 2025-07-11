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
        rect.inflate_ip(self.gui.ratios.main_menu_folder_margin_x, self.gui.ratios.main_menu_folder_margin_y)
        state.rect = rect
        surface = pe.Surface(state.rect.size)
        invert_key = '_inverted' if state.render_info.selected else ''

        text: Optional[pe.Text] = getattr(state.render_info, f't_title_folder{invert_key}')
        star_icon = self.gui.icons['star' + invert_key]
        tag_icon = self.gui.icons['tag' + invert_key]

        icon_position = (  # Calculate the offset where the folder icon will be displayed
            self.gui.ratios.main_menu_folder_margin_x // 2,
            self.gui.ratios.main_menu_folder_margin_y // 2
        )
        text_left_margin = icon.width + self.gui.ratios.main_menu_folder_padding  # Margin between icon and text

        # Calculate the available width for the text, accounting for icons and margins
        available_width = surface.width - (
                icon_position[0] + text_left_margin + self.gui.ratios.main_menu_folder_padding  # Base margin
                + (star_icon.width + self.gui.ratios.main_menu_folder_padding
                   if state.current_state['pinned'] else 0)  # If pinned, add star icon width + margin
                + (tag_icon.width + self.gui.ratios.main_menu_folder_padding
                   if state.current_state['tags'] else 0)  # If tags, add tag icon width + margin
        )
        state.set_trim_text_size('t_title_folder', available_width)

        if text:  # Position the text relative to the icon
            text.rect.midleft = icon_position
            text.rect.x += text_left_margin
            text.rect.y += icon.height // 1.5

        with surface:
            if state.render_info.selected:
                pe.fill.full(Defaults.SELECTED)
            icon.display(icon_position)
            if text:  # Display the text if it exists and handle the icons too
                text.display()

                # Position the icons if applicable
                icon_rect = pe.Rect(*text.rect.topright, *star_icon.size)
                icon_rect.x += self.gui.ratios.main_menu_folder_padding
                icon_rect.centery = surface.height // 2  # Center vertically

                if state.current_state['pinned']:
                    star_icon.display(icon_rect.topleft)
                    icon_rect.x += star_icon.width + self.gui.ratios.main_menu_folder_padding

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
        preview_rect = pe.Rect(0, 0, self.viewer.document_width, self.viewer.document_height)

        if state.render_info.selected:
            preview_rect.inflate_ip(tuple(-0.1 * x for x in preview_rect.size))

        preview, edge_rounding = self.render_document_preview(state,
                                                              preview_rect.size)  # Get the preview for the document
        invert_key = '_inverted' if state.render_info.selected else ''
        text = getattr(state.render_info, f't_title{invert_key}')  # Get the title text for the document
        sub_text = getattr(state.render_info, f't_description{invert_key}')  # Get the description text for the document
        star_icon = self.gui.icons['star' + invert_key]

        bottom = self.viewer.document_height

        if text:
            text.rect.top = self.viewer.document_height + self.gui.ratios.main_menu_document_title_height_margin
            text.rect.left = 0

            if sub_text:
                sub_text.rect.top = text.rect.bottom + self.gui.ratios.main_menu_document_title_padding
                sub_text.rect.left = 0
                bottom = sub_text.rect.bottom
            else:
                bottom = text.rect.bottom

        state.set_trim_text_size('t_title', surface.width - (
            star_icon.width + self.gui.ratios.main_menu_document_padding if state.current_state['pinned'] else 0))

        with surface:
            if state.render_info.selected:
                pe.fill.full(Defaults.SELECTED)
            elif state.button.hovered:
                pe.draw.rect(Defaults.BUTTON_ACTIVE_COLOR, (0, 0, surface.width, bottom), edge_rounding=edge_rounding,
                             edge_rounding_bottomleft=0)

            pe.display.blit(preview, preview_rect.topleft)

            # Handle drawing the tag texts on top of the preview area
            y = preview_rect.bottom - self.gui.ratios.main_menu_document_padding
            available_width = preview_rect.width - self.gui.ratios.main_menu_document_padding * 2
            tags_end = preview_rect.top if self.gui.config.doc_view_more_tags else preview_rect.centery
            for i, tag in enumerate(tag_names := [tag.name for tag in state.current_state['tags']], start=1):
                tag_text = getattr(state.render_info, f't_tag_{tag}')

                if not tag_text:
                    continue

                # Align the tag and display it
                tag_text.rect.x = preview_rect.left + self.gui.ratios.main_menu_document_padding
                tag_text.rect.bottom = y
                self.display_tag(tag_text)

                # Adjust the y position for the next tag
                y -= tag_text.rect.height + self.gui.ratios.main_menu_document_padding

                # Ensure the next tag can fit in the designated space safely
                if y-tag_text.rect.height-self.gui.ratios.main_menu_document_padding <= tags_end:
                    state.extra_tags_count = len(state.current_state['tags']) - i  # Remaining tags if any
                    break
            else:
                state.extra_tags_count = 0  # No extra tags, reset the count
            if state.extra_tags_count > 0:
                available_width /= 2
                extra_tags_text = getattr(state.render_info, 't_extra_tags')
                if extra_tags_text:
                    extra_tags_text.rect.bottomright = preview_rect.bottomright
                    extra_tags_text.rect.move_ip(-self.gui.ratios.main_menu_document_padding,
                                                 -self.gui.ratios.main_menu_document_padding)
                    self.display_tag(extra_tags_text)
                    state.set_trim_text_size('t_extra_tags', available_width)
            for tag in tag_names:
                state.set_trim_text_size(f't_tag_{tag}', available_width)

            if text:
                text.display()
                icon_rect = pe.Rect(0, 0, *star_icon.size)
                icon_rect.centery = text.rect.centery
                icon_rect.left = text.rect.right + self.gui.ratios.main_menu_document_padding
                star_icon.display(icon_rect.topleft)
            if sub_text:
                sub_text.display()

            # Debug updates to this surface
            # w = (time.time() * 100) % surface.width
            # pe.draw.line(pe.colors.red, (w, 0), (w, surface.height), 2)

            # with pe.mouse.Offset(state.button.area.topleft, reverse=True):
        return surface
