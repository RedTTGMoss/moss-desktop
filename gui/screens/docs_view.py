from abc import abstractmethod, ABC
from math import ceil
from typing import TYPE_CHECKING, Dict

import pygameextra as pe
from rm_api import DocumentCollection, Document

from gui.defaults import Defaults
from gui.helpers import dynamic_text
from gui.literals import MAIN_MENU_MODES
from gui.rendering import render_document, render_collection
from gui.screens.doc_info_display.grid_display import GridDocInfoDisplay
from gui.screens.doc_info_display.info_managers import rMDocInfoManager
from gui.screens.scrollable_view import ScrollableView

if TYPE_CHECKING:
    from gui import GUI
    from gui.screens.doc_info_display.shared_model import DocInfoState


class DocumentTreeViewer(ScrollableView, ABC):
    def __init__(self, gui: 'GUI', area):
        self.AREA = area
        self.texts: Dict[str, pe.Text] = {}
        self._text_information: Dict[str, str] = {}
        self.selected_documents = set()
        self.selected_document_collections = set()
        self.x_padding_collections = 0
        self.x_padding_documents = 0
        self.last_width = None
        self.need_to_handle_texts = False
        self._scale = self.gui.config.doc_view_scale
        self.manager = GridDocInfoDisplay(gui, rMDocInfoManager, self)
        super().__init__(gui)

    @property
    def text_information(self) -> Dict[str, str]:
        return self._text_information

    @text_information.setter
    def text_information(self, value: Dict[str, str]):
        self._text_information = value
        self.need_to_handle_texts = True

    def handle_texts(self, expected_uuid: str = None):
        # document_collections: Dict[str, DocumentCollection] = dict(self.document_collections)
        # documents: Dict[str, Document] = dict(self.documents)

        # Preparing the document collection texts
        folder_font_details = (Defaults.FOLDER_TITLE_FONT, self.gui.ratios.document_tree_view_title_size)
        document_font_details = (Defaults.DOCUMENT_SUBTITLE_FONT, self.gui.ratios.document_tree_view_title_size)
        small_font_details = (Defaults.DOCUMENT_SUBTITLE_FONT, self.gui.ratios.document_tree_view_small_info_size)

        font_map = {  # Mapping text keys to their respective font details
            't_title': document_font_details,
            't_title_folder': folder_font_details,
            't_description': small_font_details,
            't_tags_extra': small_font_details,  # TODO: Maybe implement another font for this?
            't_filesize': small_font_details,
        }

        self.texts.clear()  # Clear existing texts to avoid build-up

        for key, value in self.text_information.items():
            state_uuid, text_key = key.split('|')  # Get the text key to determine the font
            if expected_uuid and state_uuid != expected_uuid:
                continue
            font = font_map.get(text_key, document_font_details)
            state: 'DocInfoState' = self.manager.get_state(state_uuid)
            state.dirty()
            size_constraint = state.trim_text_sizes.get(text_key, None)

            if size_constraint:
                trimmed_text = dynamic_text(value, *font, size_constraint)
            else:
                trimmed_text = value

            if trimmed_text != value:
                self.texts[key] = pe.Text(trimmed_text, *font, colors=Defaults.TEXT_COLOR)
                self.texts[f'{key}_inverted'] = pe.Text(trimmed_text, *font, colors=Defaults.TEXT_COLOR_H)
                self.texts[f'{key}_full'] = pe.Text(
                    dynamic_text(value, *font, state.gui.width * 0.5, True),
                    *font, colors=Defaults.TEXT_COLOR
                )
            else:
                self.texts[key] = pe.Text(value, *font, colors=Defaults.TEXT_COLOR)
                self.texts[f'{key}_inverted'] = pe.Text(value, *font, colors=Defaults.TEXT_COLOR_H)



    @property
    @abstractmethod
    def documents(self):
        return {}

    @property
    @abstractmethod
    def document_collections(self):
        return {}

    @property
    @abstractmethod
    def mode(self) -> MAIN_MENU_MODES:
        return 'list'

    def pre_loop(self):
        area_of_widths = self.width / (
                self.document_width + self.gui.ratios.main_menu_document_padding
        ) - self.gui.ratios.main_menu_document_padding / self.width
        area_of_widths = max(1, int(area_of_widths))

        width = area_of_widths * self.document_width
        width += self.gui.ratios.main_menu_document_padding * (area_of_widths - 1)

        padding = (self.width - width) / 2

        collections_rows = 1
        documents_rows = 1

        if len(self.document_collections) == 0:
            collections_rows = 0
        if len(self.document_collections) < area_of_widths:
            self.x_padding_collections = self.gui.ratios.main_menu_x_padding
        else:
            self.x_padding_collections = padding
            if self.mode == 'grid' or self.mode == 'folder':
                collections_rows = ceil(len(self.document_collections) / area_of_widths)
            else:
                collections_rows = len(self.document_collections)

        if len(self.documents) == 0:
            documents_rows = 0
        if len(self.documents) < area_of_widths:
            self.x_padding_documents = self.gui.ratios.main_menu_x_padding
        else:
            self.x_padding_documents = padding
            documents_rows = ceil(len(self.documents) / area_of_widths)

        if len(self.document_collections) > 0:
            # Collections
            y = self.gui.ratios.main_menu_top_padding / 2
            y += self.gui.ratios.main_menu_folder_height_distance * collections_rows
        else:
            y = 0

        # Documents
        y += (self.full_document_height + self.gui.ratios.main_menu_document_height_distance) * documents_rows

        if len(self.documents) > 0:
            y -= self.gui.ratios.main_menu_document_title_height_margin * 2

        self.bottom = y + self.gui.ratios.bottom_bar_height

        if self.need_to_handle_texts:
            self.handle_texts()
            self.need_to_handle_texts = False

        super().pre_loop()

    def loop(self):
        top = self.top
        area = pe.Rect(*self.AREA)
        if self.mode == 'grid':
            collections_x = self.x_padding_collections
        else:
            collections_x = self.gui.ratios.main_menu_x_padding

        x = collections_x

        y = self.gui.ratios.main_menu_top_padding / 2
        y += top

        # Rendering the folders
        document_collection_width = \
            self.document_width if self.mode == 'grid' else self.width - self.gui.ratios.main_menu_x_padding * 2
        for i, document_collection in enumerate(
                self.gui.main_menu.get_sorted_document_collections(self.document_collections.values())):
            # TODO: remove the debugging code
            if self.gui.ctrl_hold:
                render_collection(self.gui, document_collection, self.texts,
                                  self.open_document_collection, x, y, document_collection_width,
                                  self.select_document_collection,
                                  document_collection.uuid in self.selected_document_collections)
            self.manager.handle(document_collection, area, x, y)

            if self.mode == 'grid':
                x += self.document_width + self.gui.ratios.main_menu_document_padding
                if x + self.document_width > self.width and i + 1 < len(self.document_collections):
                    x = collections_x
                    y += self.gui.ratios.main_menu_folder_height_distance
            else:
                y += self.gui.ratios.main_menu_folder_height_distance
                if (self.mode == 'list' and len(self.documents) > 0) or i < len(self.document_collections) - 1:
                    line_y = y - self.gui.ratios.main_menu_folder_margin_y / 2
                    pe.draw.line(Defaults.LINE_GRAY,
                                 (collections_x, line_y), (self.width - collections_x, line_y),
                                 self.gui.ratios.line)

        # Resetting the x and y for the documents
        if len(self.document_collections) > 0:
            y += self.gui.ratios.main_menu_folder_height_last_distance
        else:
            y = top

        x = self.x_padding_documents

        # Rendering the documents
        for i, document in enumerate(self.gui.main_menu.get_sorted_documents(self.documents.values())):
            if y + self.full_document_height > 0:
                # Render the document
                rect = pe.Rect(
                    x, y,
                    self.document_width,
                    self.full_document_height
                )
                if document.uuid in self.gui.main_menu.document_sync_operations:
                    document_sync_operation = self.gui.main_menu.document_sync_operations[document.uuid]
                    if document_sync_operation.finished:
                        del self.gui.main_menu.document_sync_operations[document.uuid]
                        document_sync_operation = None
                elif document.downloading:
                    document_sync_operation = document.download_progress
                else:
                    document_sync_operation = None
                # TODO: remove the debugging code
                if self.gui.ctrl_hold:
                    render_document(self.gui, rect, self.texts, document, document_sync_operation,
                                    self.scale, self.select_document, document.uuid in self.selected_documents)
                self.manager.handle(document, area, x, y)

            x += self.document_width + self.gui.ratios.main_menu_document_padding
            if x + self.document_width > self.width and i + 1 < len(self.documents):
                x = self.x_padding_documents
                y += self.full_document_height
            if y > self.height:
                break

    def select_document(self, document_uuid: str):
        if document_uuid in self.selected_documents:
            self.selected_documents.remove(document_uuid)
        else:
            self.selected_documents.add(document_uuid)

    def select_document_collection(self, document_collection_uuid: str):
        if document_collection_uuid in self.selected_document_collections:
            self.selected_document_collections.remove(document_collection_uuid)
        else:
            self.selected_document_collections.add(document_collection_uuid)

    def open_document_collection(self, document_collection_uuid: str):
        self.gui.main_menu.set_parent(document_collection_uuid)

    @property
    def document_width(self):
        return self.gui.ratios.main_menu_document_width * self.scale

    @property
    def full_document_height(self):
        return self.document_height + self.gui.ratios.main_menu_document_height_distance

    @property
    def document_height(self):
        return self.gui.ratios.main_menu_document_height * self.scale

    def handle_event(self, event):
        super().handle_event(event)
        if not self.gui.ctrl_hold:
            return

        # Handle scrolling to change the scale
        if event.type == pe.pygame.MOUSEWHEEL:
            if event.y > 0:
                self.scale += 0.1
            else:
                self.scale -= 0.1
            self.scale = max(0.5, min(2.08, self.scale))
            self.handle_texts()

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale = value
        self.gui.config.doc_view_scale = value
        self.gui.dirty_config = True
