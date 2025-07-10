from abc import abstractmethod, ABC
from dataclasses import dataclass
from pprint import pformat

from rm_api import Document, DocumentCollection, DocumentSyncProgress

import pygameextra as pe
from typing import TYPE_CHECKING, Union, Optional, Type, Any, Tuple

from gui.defaults import Defaults

if TYPE_CHECKING:
    from gui import GUI
    from gui.screens.docs_view import DocumentTreeViewer


class DocInfoState:
    """Represents an item in its current static state."""

    def __init__(self, document: Any, manager: 'DocInfoDisplay'):
        self.gui = manager.gui
        self.document = document
        self.render_info: Optional[RenderInfo] = None
        self.manager = manager
        self.scale = 0
        self._rect = pe.Rect(0, 0, 10, 10)
        self.preview_size: Optional[Tuple[int, int]] = None
        self.small_text_sizes = {}
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
        self.current_state = self.get_state()

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


@dataclass
class RenderInfo:
    """
    Represents generic information about the item to be rendered.
    This is shared between different items.
    """
    preview: Optional[pe.Sprite] = None
    icon: Optional[str] = None
    progress: Optional[DocumentSyncProgress] = None
    selected: bool = False


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
            't_title': 'Title',  # The title of the document or collection
            't_description': 'Description',  # The subtext aka page count, read progress or item count
            # If the tags are too many this text is shown to indicate extra tags that are not displayed
            't_tags_extra': '+0',
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
    __cache = {}

    def __init__(self, gui: 'GUI', info_class: Type[DocInfoManager],
                 doc_tree_view: 'DocumentTreeViewer'):
        self.gui = gui
        self.info_class = info_class
        self.viewer = doc_tree_view

    def handle(self, item: Union[Document, DocumentCollection], area: pe.Rect, offset_x: int, offset_y: int):
        """
        Handles the item state and frame rendering.
        """
        state = self.__cache.get(item.uuid)
        if not state:
            state = DocInfoState(item, self)
            self.__cache[item.uuid] = state
        self.update(state, area, state.button.hovered)
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
        rect = state.rect.move(offset_x, offset_y)
        if not state.frame:
            pe.draw.rect(Defaults.BACKGROUND_ERROR, rect, 0,
                         edge_rounding=self.gui.ratios.error_edge_rounding)
        else:
            pe.display.blit(state.frame, rect.topleft)  # Clip the frame to an area
        pe.settings.game_context.buttons.append(state.button)
        state.button.area = rect.clip(pe.Rect(0, 0, *area.size))
        pe.button.check_hover(state.button)

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

    def render_document_preview(self, state: DocInfoState, size: Tuple[int, int]) -> Optional[pe.Sprite]:
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

        return preview_masked
