from abc import abstractmethod, ABC
from dataclasses import dataclass
from pprint import pformat

from rm_api import Document, DocumentCollection, DocumentSyncProgress

import pygameextra as pe
from typing import TYPE_CHECKING, Union, Optional, Type, Any, Tuple, Dict

from gui.defaults import Defaults
from gui.pp_helpers import FullTextPopup
from gui.rendering import render_full_text

if TYPE_CHECKING:
    from gui import GUI
    from gui.screens.docs_view import DocumentTreeViewer


class DocInfoState:
    """Represents an item in its current static state."""

    def __init__(self, document: Any, manager: 'DocInfoDisplay'):
        self.gui: 'GUI' = manager.gui
        self.document = document
        self.render_info: Optional[RenderInfo] = None
        self.manager = manager
        self.scale = 0
        self._rect = pe.Rect(0, 0, 10, 10)
        self.trim_text_sizes = {}
        self.extra_tags_count = 0
        self.texts = {}
        self.button = pe.Button(
            self.rect,
            None, None,
            action_set=pe.button.ButtonActionSet(
                hover_draw=pe.button.ButtonAction(
                    action=self.manager.update,
                    kwargs={
                        'state': self,
                        'force_update': True
                    }
                ),
                hover=None,
                l_click=pe.button.ButtonAction(
                    action=self.manager.info_class.handle_item_open,
                    args=self
                ),
                r_click=pe.button.ButtonAction(
                    action=self.manager.info_class.handle_item_context,
                    args=self
                )
            ),
            name=f'doc_info_area_<{document.uuid}>',
        )
        self.frame: Optional[pe.Surface] = None
        self._current_state = None

    def set_trim_text_size(self, key: str, size: int):
        if self.trim_text_sizes.get(key, 0) == size:
            return
        self.trim_text_sizes[key] = size
        if self.render_info and (text := getattr(self.render_info, key, None)) is not None:  # Find the text object
            if text.rect.width > size:  # Check if the text is larger the trim size
                self.manager.viewer.need_to_handle_texts = True  # Mark that we need to handle trimming the text
            if text.text != self.current_state.get(key, text.text):
                self.manager.viewer.need_to_handle_texts = True  # Mark that we need to handle untrimming the text

    @property
    def current_state(self):
        if not self._current_state:
            self.current_state = self.get_state()
        return self._current_state

    @current_state.setter
    def current_state(self, value: dict):
        # Update texts if applicable
        self._current_state = value
        for key, value in [(key, value) for key, value in value.items() if key.startswith('t_')]:
            identifiable_key = f'{self.document.uuid}|{key}'
            current_text = self.manager.viewer.text_information.get(identifiable_key)
            if current_text is not None and current_text == value:
                continue
            self.manager.viewer.text_information[identifiable_key] = value
            self.manager.viewer.need_to_handle_texts = True

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, value: pe.Rect):
        self._rect = value

    @property
    def is_document(self):
        return self.manager.info_class.is_document(self.document)

    def needs_refresh(self):
        return not self.frame or self.current_state != self.get_state()

    def get_state(self):
        if self.is_document:
            return self.manager.info_class.get_document_state_info(self)
        else:
            return self.manager.info_class.get_collection_state_info(self)

    def dirty(self):
        self.current_state['dirty'] = True


@dataclass
class RenderInfo:
    """
    Represents generic information about the item to be rendered.
    This is shared between different items.
    """
    state: DocInfoState
    preview: Optional[pe.Sprite] = None
    icon: Optional[str] = None
    progress: Optional[DocumentSyncProgress] = None
    selected: bool = False

    def __getattr__(self, item):
        if item.startswith('t_'):
            return self.state.manager.viewer.texts.get(f'{self.state.document.uuid}|{item}')
        return super().__getattr__(item)


class DocInfoManager(ABC):
    """Abstract base class for managing render information for documents and collections."""

    @classmethod
    @abstractmethod
    def get_document_render_info(cls, state: DocInfoState) -> RenderInfo:
        ...

    @classmethod
    @abstractmethod
    def get_collection_render_info(cls, state: DocInfoState) -> RenderInfo:
        ...

    @classmethod
    @abstractmethod
    def get_document_state_info(cls, state: DocInfoState) -> dict:
        ...

    @classmethod
    @abstractmethod
    def get_collection_state_info(cls, state: DocInfoState) -> dict:
        ...

    @classmethod
    def get_required_state_info(cls, state: DocInfoState) -> dict:
        """
        Returns the required state information that is always present.
        This can be overridden to add more fields.
        """
        return {
            'hovered': state.button.hovered,
            'rect_size': state.rect.size,
            'pinned': False,
            'tags': [],

            # ONE OF THESE IS REQUIRED, NOT BOTH TITLES
            't_title': 'Title',  # The title of the document
            't_title_folder': 'Title Folder',  # The title of the collection

            't_description': 'Description',  # The subtext aka page count, read progress or item count
            # If the tags are too many this text is shown to indicate extra tags that are not displayed
            't_extra_tags': f'+{state.extra_tags_count}',
            't_filesize': '0 Bytes',  # The size of the document
        }

    @classmethod
    @abstractmethod
    def is_document(cls, item: Any) -> bool:
        ...

    @classmethod
    @abstractmethod
    def handle_item_open(cls, state: DocInfoState):
        ...

    @classmethod
    @abstractmethod
    def handle_item_context(cls, state: DocInfoState):
        ...


class DocInfoDisplay(ABC):
    """Represents the handler for rendering the static item information into a visual frame."""
    __cache: Dict[str, DocInfoState] = {}

    def __init__(self, gui: 'GUI', info_class: Type[DocInfoManager],
                 doc_tree_view: 'DocumentTreeViewer'):
        self.gui: 'GUI' = gui
        self.info_class = info_class
        self.viewer = doc_tree_view

    def handle(self, item: Union[Document, DocumentCollection], area: pe.Rect, offset_x: Optional[int] = None,
               offset_y: Optional[int] = None):
        """
        Handles the item state and frame rendering.
        """
        state = self.__cache.get(item.uuid)
        if not state:  # If the state is not cached, create a new one
            state = DocInfoState(item, self)
            self.__cache[item.uuid] = state
        self.update(state, area, state.button.hovered)
        if offset_x and offset_y:
            self.render(state, area, offset_x, offset_y)

    def update(self, state: DocInfoState, area: pe.Rect = None, force_update: bool = False) -> bool:
        if not area:
            area = pe.Rect(*self.viewer.AREA)
        if state.needs_refresh() or state.scale != self.viewer.scale or force_update:
            state.current_state = state.get_state()
            state.render_info = self.get_render_info(state)
            state.scale = self.viewer.scale
        elif not force_update:
            return False
        if state.is_document:
            state.frame = self.render_document(state, area)
        else:
            state.frame = self.render_collection(state, area)
        if state.frame is not None:
            state.rect.size = state.frame.size  # Update the area of the button to match the rendered size
        return True

    def render(self, state: DocInfoState, area: pe.Rect, offset_x: int, offset_y: int):
        """
        Renders the item frame if available.
        """
        rect = state.rect.copy()
        rect.topleft = (offset_x, offset_y)
        if not state.frame:
            pe.draw.rect(Defaults.BACKGROUND_ERROR, rect, 0,
                         edge_rounding=self.gui.ratios.error_edge_rounding)
        else:
            pe.display.blit(state.frame, rect.topleft)  # Clip the frame to an area
            # Check if the title is long
            if state.button.hovered:
                if state.is_document:
                    title = state.render_info.t_title
                    full = state.render_info.t_title_full
                else:
                    title = state.render_info.t_title_folder
                    full = state.render_info.t_title_folder_full
                if title and full:
                    full.rect.topleft = title.rect.topleft
                    full.rect.move_ip(offset_x, offset_y)
                    render_full_text(state.gui, full)

        # Properly handle button contexting so everything works as expected
        self.gui.buttons_with_names[state.button.name] = state.button  # Register the button
        self.gui.buttons.append(state.button)  # Add the button to the buttons list
        pe.button.check_hover(state.button)

        # Clip the button area to the area of the viewer
        state.button.area = rect.clip(pe.Rect(0, 0, *area.size))

    @abstractmethod
    def render_document(self, state: DocInfoState, area: pe.Rect) -> pe.Surface:
        ...

    @abstractmethod
    def render_collection(self, state: DocInfoState, area: pe.Rect) -> pe.Surface:
        ...

    def get_render_info(self, state: DocInfoState) -> RenderInfo:
        if state.is_document:
            return self.info_class.get_document_render_info(state)
        else:
            return self.info_class.get_collection_render_info(state)

    def render_document_preview(self, state: DocInfoState, size: Tuple[int, int]) -> Tuple[Optional[pe.Sprite], int]:
        edge_rounding = int(state.gui.ratios.main_menu_document_rounding * self.viewer.scale)
        preview_masked = pe.Surface(size)
        preview_rect = (0, 0, *size)

        with preview_masked:
            pe.fill.full(Defaults.DOCUMENT_BACKGROUND)

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
            with preview_masked:
                state.render_info.preview.resize = size
                state.render_info.preview.display()
            preview_masked.surface.blit(mask.surface, (0, 0), special_flags=pe.BLEND_RGBA_MULT)

        with preview_masked:
            pe.draw.rect(  # Draw the notebook spine
                Defaults.DOCUMENT_GRAY,
                (0, 0, spine_width := size[0] * 0.07, size[1])
            )

            if state.button.hovered:
                pe.draw.line(Defaults.SELECTED, (spine_width, 0), (spine_width, size[1]), state.gui.ratios.outline)

            pe.draw.rect(  # Draw the rounded outline around the preview
                Defaults.SELECTED if state.button.hovered else Defaults.DOCUMENT_GRAY,
                preview_rect, state.gui.ratios.outline if state.button.hovered else state.gui.ratios.line,
                edge_rounding_topright=edge_rounding,
                edge_rounding_bottomright=edge_rounding
            )

        return preview_masked, edge_rounding

    def display_tag(self, tag_text):
        # Make rects that surround the tag text
        expanded_rect = self.gui.ratios.pad_button_rect(tag_text.rect, self.gui.ratios.main_menu_tag_padding)
        outline_rect = expanded_rect.inflate(self.gui.ratios.outline, self.gui.ratios.outline)

        # Draw the background and outline for the tag
        pe.draw.rect(Defaults.SELECTED, outline_rect, 0, edge_rounding=outline_rect.height)
        pe.draw.rect(Defaults.BACKGROUND, expanded_rect, 0, edge_rounding=expanded_rect.height)

        tag_text.display()  # Display the tag text

    def get_state(self, state_uuid) -> Optional[DocInfoState]:
        return self.__cache.get(state_uuid, None)

    @property
    def document_rect(self):
        return self._document_rect()

    @property
    def collection_rect(self):
        return self._collection_rect()
    @property
    def document_margin(self):
        return self._document_margin()

    @property
    def collection_margin(self):
        return self._collection_margin()

    @property
    def separation_distance(self):
        return self._separation_distance()

    @abstractmethod
    def _document_rect(self) -> pe.Rect:
        ...

    @abstractmethod
    def _collection_rect(self) -> pe.Rect:
        ...

    @abstractmethod
    def _document_margin(self) -> int:
        ...

    @abstractmethod
    def _collection_margin(self) -> int:
        ...

    @abstractmethod
    def _separation_distance(self) -> int:
        ...