from abc import abstractmethod, ABC
from typing import TYPE_CHECKING, Dict

import pygameextra as pe
from math import ceil

from gui.defaults import Defaults
from gui.helpers import dynamic_text
from gui.literals import MAIN_MENU_MODES
from gui.screens.doc_info_display.grid_display import GridDocInfoDisplay
from gui.screens.doc_info_display.info_managers import rMDocInfoManager
from gui.screens.scrollable_view import ScrollableView

if TYPE_CHECKING:
    from gui import GUI
    from gui.screens.doc_info_display.shared_model import DocInfoState


class DocumentTreeViewer(ScrollableView, ABC):
    def __init__(self, gui: "GUI", area):
        self.AREA = area
        self.texts: Dict[str, pe.Text] = {}
        self._text_information: Dict[str, str] = {}
        self.selected_documents = set()
        self.selected_document_collections = set()
        self.x_padding_collections = 0
        self.x_padding_documents = 0
        self.collection_columns_fittable = 1
        self.document_columns_fittable = 1
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
        folder_font_details = (
            Defaults.FOLDER_TITLE_FONT,
            self.gui.ratios.document_tree_view_title_size,
        )
        document_font_details = (
            Defaults.DOCUMENT_SUBTITLE_FONT,
            self.gui.ratios.document_tree_view_title_size,
        )
        small_font_details = (
            Defaults.DOCUMENT_SUBTITLE_FONT,
            self.gui.ratios.document_tree_view_small_info_size,
        )

        font_map = {  # Mapping text keys to their respective font details
            "t_title": document_font_details,
            "t_title_folder": folder_font_details,
            "t_description": small_font_details,
            "t_extra_tags": small_font_details,  # TODO: Maybe implement another font for this?
            "t_filesize": small_font_details,
            "t_tag": small_font_details,
        }

        self.texts.clear()  # Clear existing texts to avoid build-up

        for key, value in self.text_information.items():
            state_uuid, text_key = key.split(
                "|"
            )  # Get the text key to determine the font
            if expected_uuid and state_uuid != expected_uuid:
                continue
            font = font_map.get(
                "t_tag" if "t_tag_" in text_key else text_key, small_font_details
            )
            state: "DocInfoState" = self.manager.get_state(state_uuid)
            state.dirty()
            size_constraint = state.trim_text_sizes.get(text_key, None)

            if size_constraint:
                trimmed_text = dynamic_text(value, *font, size_constraint)
            else:
                trimmed_text = value

            if trimmed_text != value:
                self.texts[key] = pe.Text(
                    trimmed_text, *font, colors=Defaults.TEXT_COLOR_T
                )
                self.texts[f"{key}_inverted"] = pe.Text(
                    trimmed_text, *font, colors=Defaults.TEXT_COLOR_H
                )
                self.texts[f"{key}_full"] = pe.Text(
                    dynamic_text(value, *font, state.gui.width * 0.5, True),
                    *font,
                    colors=Defaults.TEXT_COLOR,
                )
            else:
                self.texts[key] = pe.Text(value, *font, colors=Defaults.TEXT_COLOR_T)
                self.texts[f"{key}_inverted"] = pe.Text(
                    value, *font, colors=Defaults.TEXT_COLOR_H
                )

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
        return "list"

    def pre_loop(self):
        # Get the sizes from the manager
        collection_size = self.manager.collection_rect.size
        document_size = self.manager.document_rect.size

        # Figure out the columns, if we should add padding or not
        self.collection_columns_fittable = max(
            1,
            int(
                self.width  # Divide the width by the size of one collection
                / (collection_size[0] + self.manager.collection_margin)
            ),
        )
        self.document_columns_fittable = max(
            1,
            int(
                self.width  # Do the same for document columns
                / (document_size[0] + self.manager.document_margin)
            ),
        )

        # Calculate x padding for collections based on length
        # noinspection DuplicatedCode
        if len(self.document_collections) < self.collection_columns_fittable:
            self.x_padding_collections = self.gui.ratios.main_menu_x_padding
        else:
            width = self.collection_columns_fittable * collection_size[
                0
            ] + self.gui.ratios.main_menu_folder_margin * (
                self.collection_columns_fittable - 1
            )
            self.x_padding_collections = (self.width - width) / 2

        # Calculate x padding for documents based on length
        # noinspection DuplicatedCode
        if len(self.documents) < self.document_columns_fittable:
            self.x_padding_documents = self.gui.ratios.main_menu_x_padding
        else:
            width = self.document_columns_fittable * document_size[
                0
            ] + self.gui.ratios.main_menu_document_margin * (
                self.document_columns_fittable - 1
            )
            self.x_padding_documents = (self.width - width) / 2

        # Finally calculate row count for final height determination of the scrollable view
        if len(self.document_collections) > 0:
            collection_rows = ceil(
                len(self.document_collections) / self.collection_columns_fittable
            )
        else:
            collection_rows = 0

        if len(self.documents) > 0:
            document_rows = ceil(len(self.documents) / self.document_columns_fittable)
        else:
            document_rows = 0

        # Calculate the height of the scrollable view
        y = (collection_size[1] + self.manager.collection_margin) * collection_rows
        y += (document_size[1] + self.manager.document_margin) * document_rows

        if len(self.document_collections) > 0:  # Add the separation distance
            y += self.manager.separation_distance

        # Add the padding of the bottom bar for better scroll experience
        self.bottom = y + self.gui.ratios.bottom_bar_height

        # As a final pre_loop, handle texts if flagged for handling
        if self.need_to_handle_texts:
            self.handle_texts()
            self.need_to_handle_texts = False

        super().pre_loop()

    def loop(self):
        top = self.top
        area = pe.Rect(*self.AREA)

        # Get the sizes from the manager
        collection_size = self.manager.collection_rect.size
        document_size = self.manager.document_rect.size

        x = self.x_padding_collections

        y = self.gui.ratios.main_menu_top_padding / 2
        y += top

        # Rendering the folders
        for i, document_collection in enumerate(
            self.gui.main_menu.get_sorted_document_collections(
                self.document_collections.values()
            )
        ):
            self.manager.handle(
                document_collection, area, x, y
            )  # Render the collection

            if (
                i % self.collection_columns_fittable
                == self.collection_columns_fittable - 1
                and i < len(self.document_collections) - 1
            ):  # Also skip this operation for the last collection
                # If we reached the end of the row, reset x and increase y
                x = self.x_padding_collections
                y += collection_size[1] + self.manager.collection_margin
            else:
                # Otherwise, just increase x
                x += collection_size[0] + self.manager.collection_margin

        # Resetting the x and y for the documents
        x = self.x_padding_documents
        if len(self.document_collections) > 0:
            y += collection_size[1] + self.manager.separation_distance
        else:
            y = top

        # Rendering the documents
        for i, document in enumerate(
            self.gui.main_menu.get_sorted_documents(self.documents.values())
        ):
            self.manager.handle(document, area, x, y)  # Render the document

            if (
                i % self.document_columns_fittable == self.document_columns_fittable - 1
                and i < len(self.documents) - 1
            ):  # Also skip this operation for the last document
                # If we reached the end of the row, reset x and increase y
                x = self.x_padding_documents
                y += document_size[1] + self.manager.document_margin
            else:
                # Otherwise, just increase x
                x += document_size[0] + self.manager.document_margin

    def select_document(self, document_uuid: str):
        print(
            f"Toggling selection for document {document_uuid} {self.manager.__class__.__name__} {self.__class__.__name__}"
        )
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
