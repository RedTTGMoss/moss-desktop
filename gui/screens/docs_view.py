from abc import abstractmethod, ABC
from math import ceil
from typing import TYPE_CHECKING, Dict

import pygameextra as pe

from gui.defaults import Defaults
from gui.helpers import dynamic_text
from gui.literals import MAIN_MENU_MODES
from gui.rendering import render_document, render_collection
from gui.screens.scrollable_view import ScrollableView
from rm_api import DocumentCollection, Document

if TYPE_CHECKING:
    from gui import GUI


class DocumentTreeViewer(ScrollableView, ABC):
    def __init__(self, gui: 'GUI', area):
        self.AREA = area
        self.texts: Dict[str, pe.Text] = {}
        self.selected_documents = set()
        self.selected_document_collections = set()
        self.x_padding_collections = 0
        self.x_padding_documents = 0
        self.last_width = None
        self._scale = self.gui.config.doc_view_scale
        super().__init__(gui)

    def handle_texts(self):
        document_collections: Dict[str, DocumentCollection] = dict(self.document_collections)
        documents: Dict[str, Document] = dict(self.documents)

        # Preparing the document collection texts
        font_details = (Defaults.FOLDER_TITLE_FONT, self.gui.ratios.document_tree_view_folder_title_size)
        item_counts = set()
        for uuid, document_collection in document_collections.items():
            item_counts.add(document_collection.get_item_count(self.gui.api))
            if self.texts.get(uuid) is None or self.texts[
                uuid + '_full'
            ].text != document_collection.metadata.visible_name:
                width_reduction = self.gui.ratios.main_menu_document_padding
                if document_collection.metadata.pinned:
                    width_reduction += self.gui.icons['star'].width + self.gui.ratios.main_menu_folder_padding
                if document_collection.tags and self.mode == 'grid':
                    width_reduction += self.gui.icons['tag'].width + self.gui.ratios.main_menu_folder_padding
                shortened_text = dynamic_text(document_collection.metadata.visible_name, *font_details,
                                              (self.document_width if self.mode == 'grid' else self.width)
                                              - width_reduction
                                              )
                self.texts[uuid] = pe.Text(shortened_text, *font_details, (0, 0), Defaults.TEXT_COLOR)
                self.texts[uuid + '_inverted'] = pe.Text(shortened_text, *font_details, (0, 0),
                                                         Defaults.TEXT_COLOR_H)
                self.texts[uuid + '_full'] = pe.Text(document_collection.metadata.visible_name,
                                                     *font_details, (0, 0), Defaults.TEXT_COLOR)

        # Preparing the document texts
        font_details = (Defaults.DOCUMENT_SUBTITLE_FONT, self.gui.ratios.document_tree_view_document_title_size)
        page_counts = set()
        page_of_counts = set()
        pages_read = set()
        for uuid, document in documents.items():
            if document.content.file_type == 'notebook':
                page_counts.add(document.get_page_count())
            elif document.content.file_type == 'pdf':
                page_of_counts.add((document.metadata.last_opened_page + 1, document.get_page_count()))
            elif document.content.file_type == 'epub':
                pages_read.add(document.get_read())
            if self.texts.get(uuid) is None or self.texts[uuid + '_full'].text != document.metadata.visible_name:
                shortened_text = dynamic_text(document.metadata.visible_name, *font_details,
                                              self.document_width if self.mode == 'grid' else self.width)
                self.texts[uuid] = pe.Text(shortened_text, *font_details, (0, 0),
                                           Defaults.DOCUMENT_TITLE_COLOR)
                self.texts[uuid + '_inverted'] = pe.Text(shortened_text, *font_details
                                                         , (0, 0),
                                                         Defaults.DOCUMENT_TITLE_COLOR_INVERTED)
                self.texts[uuid + '_full'] = pe.Text(document.metadata.visible_name, *font_details, (0, 0),
                                                     Defaults.DOCUMENT_TITLE_COLOR)

        # Handle small texts
        font_details = (Defaults.DOCUMENT_SUBTITLE_FONT, self.gui.ratios.document_tree_view_small_info_size)
        for item_count in item_counts:
            self.texts[f'item_count_{item_count}'] = pe.Text(f'{item_count} items', *font_details,
                                                             (0, 0), Defaults.TEXT_COLOR)
            self.texts[f'item_count_{item_count}_inverted'] = pe.Text(f'{item_count} items', *font_details,
                                                                      (0, 0), Defaults.TEXT_COLOR_H)

        for page_count in page_counts:
            self.texts[f'page_count_{page_count}'] = pe.Text(f'{page_count} pages', *font_details,
                                                             (0, 0), Defaults.TEXT_COLOR)
            self.texts[f'page_count_{page_count}_inverted'] = pe.Text(f'{page_count} pages', *font_details,
                                                                      (0, 0), Defaults.TEXT_COLOR_H)

        for page_of, pages in page_of_counts:
            self.texts[f'page_of_{page_of}_{pages}'] = pe.Text(f'Page {page_of} of {pages}', *font_details,
                                                               (0, 0), Defaults.TEXT_COLOR)
            self.texts[f'page_of_{page_of}_{pages}_inverted'] = pe.Text(f'Page {page_of} of {pages}', *font_details,
                                                                        (0, 0), Defaults.TEXT_COLOR_H)

        for page_read in pages_read:
            self.texts[f'page_read_{page_read}'] = pe.Text(f'{page_read}% read', *font_details,
                                                           (0, 0), Defaults.TEXT_COLOR)
            self.texts[f'page_read_{page_read}_inverted'] = pe.Text(f'{page_read}% read', *font_details,
                                                                    (0, 0), Defaults.TEXT_COLOR_H)

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
        y += (self.document_height + self.gui.ratios.main_menu_document_height_distance) * documents_rows

        if len(self.documents) > 0:
            y -= self.gui.ratios.main_menu_document_title_height_margin * 2

        self.bottom = y + self.gui.ratios.bottom_bar_height

        super().pre_loop()

    def loop(self):
        top = self.top
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
            render_collection(self.gui, document_collection, self.texts,
                              self.gui.main_menu.set_parent, x, y, document_collection_width,
                              self.select_document_collection,
                              document_collection.uuid in self.selected_document_collections)

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
        full_document_height = self.document_height + self.gui.ratios.main_menu_document_height_distance
        for i, document in enumerate(self.gui.main_menu.get_sorted_documents(self.documents.values())):
            if y + full_document_height > 0:
                # Render the document
                rect = pe.Rect(
                    x, y,
                    self.document_width,
                    self.document_height
                )
                if document.uuid in self.gui.main_menu.document_sync_operations:
                    document_sync_operation = self.gui.main_menu.document_sync_operations[document.uuid]
                    if document_sync_operation.finished:
                        del self.gui.main_menu.document_sync_operations[document.uuid]
                        document_sync_operation = None
                else:
                    document_sync_operation = None
                render_document(self.gui, rect, self.texts, document, document_sync_operation,
                                self.scale, self.select_document, document.uuid in self.selected_documents)

            x += self.document_width + self.gui.ratios.main_menu_document_padding
            if x + self.document_width > self.width and i + 1 < len(self.documents):
                x = self.x_padding_documents
                y += full_document_height
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

    @property
    def document_width(self):
        return self.gui.ratios.main_menu_document_width * self.scale

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
            self.texts.clear()
            self.handle_texts()

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale = value
        self.gui.config.doc_view_scale = value
        self.gui.dirty_config = True
