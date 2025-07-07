from abc import abstractmethod, ABC
from dataclasses import dataclass

from rm_api import Document, DocumentCollection, DocumentSyncProgress

import pygameextra as pe
from typing import TYPE_CHECKING, Union, Optional, Type

from gui.defaults import Defaults

if TYPE_CHECKING:
    from gui import GUI
    from gui.screens.docs_view import DocumentTreeViewer


class DocInfoState:
    """Represents an item in it's current static state."""

    def __init__(self, document: Union[Document, DocumentCollection], manager: 'DocInfoDisplay'):
        self.gui = manager.gui
        self.document = document
        self.current_state = self.get_state()
        self.manager = manager
        self.scale = 0
        self._rect = pe.Rect(0, 0, 10, 10)
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
                l_click=None,
                r_click=None
            ),
            name=f'doc_info_area_<{document.uuid}>',
        )
        self.frame: Optional[pe.Surface] = None

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, value: pe.Rect):
        self._rect = value
        self.button.area = value  # Update the button area to match the rect

    @property
    def is_document(self):
        return isinstance(self.document, Document)

    def needs_refresh(self):
        return not self.frame or self.current_state != self.get_state()

    def get_state(self):
        if self.is_document:
            state = self._get_document_state()
        else:
            state = self._get_collection_state()
        return {
            **state,
            'uuid': self.document.uuid,
            'name': self.document.metadata.visible_name,
            'last_modified': self.document.metadata.last_modified,
        }

    def _get_document_state(self):
        state = {
            'provision': self.document.provision,
            'content_hash': self.document.file_uuid_map[f'{self.document.uuid}.content'].hash,
            'metadata_hash': self.document.file_uuid_map[f'{self.document.uuid}.metadata'].hash,
        }

        if self.document.downloading:
            state['download_done'] = self.document.download_done

        return state

    def _get_collection_state(self):
        return {
            'has_items': self.document.has_items
        }


@dataclass
class RenderInfo:
    """
    Represents generic information about the item to be rendered.
    This is shared between different items.
    """
    title: str
    subtitle: str
    preview: Optional[pe.Sprite] = None
    icon: Optional[str] = None
    progress: Optional[DocumentSyncProgress] = None
    selected: bool = False


class DocRenderInfoManager(ABC):
    """Abstract base class for managing render information for documents and collections."""

    @classmethod
    @abstractmethod
    def get_document_render_info(cls, state: DocInfoState) -> RenderInfo:
        ...

    @classmethod
    @abstractmethod
    def get_collection_render_info(cls, state: DocInfoState) -> RenderInfo:
        ...


class DocInfoDisplay(ABC):
    """Represents the handler for rendering the static item information into a visual frame."""
    __cache = {}

    def __init__(self, gui: 'GUI', render_info_manager_class: Type[DocRenderInfoManager],
                 doc_tree_view: 'DocumentTreeViewer'):
        self.gui = gui
        self.render_info_manager_class = render_info_manager_class
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

    def update(self, state: DocInfoState, area: pe.Rect = None, force_update: bool = False):
        if not area:
            area = pe.Rect(*self.viewer.AREA)
        if state.needs_refresh() or state.scale != self.viewer.scale or force_update:
            state.render_info = self.get_render_info(state)
            state.scale = self.viewer.scale
        elif not force_update:
            return
        if state.is_document:
            state.frame = self.render_document(state, area)
        else:
            state.frame = self.render_collection(state, area)
        if state.frame is not None:
            state.rect.size = state.frame.size  # Update the area of the button to match the rendered size

    def render(self, state: DocInfoState, area: pe.Rect, offset_x: int, offset_y: int):
        """
        Renders the item frame if available.
        """
        state.rect.left = offset_x
        state.rect.top = offset_y
        if not state.frame:
            pe.draw.rect(Defaults.BACKGROUND_ERROR, state.rect, 0,
                         edge_rounding=self.gui.ratios.error_edge_rounding)
        else:
            pe.display.blit(state.frame, state.rect.topleft)  # Clip the frame to an area
        pe.settings.game_context.buttons.append(state.button)
        state.button.area = state.rect.clip(pe.Rect(0, 0, *area.size))
        pe.button.check_hover(state.button)

    @abstractmethod
    def render_document(self, state: DocInfoState, area: pe.Rect) -> pe.Surface:
        ...

    @abstractmethod
    def render_collection(self, state: DocInfoState, area: pe.Rect) -> pe.Surface:
        ...

    def get_render_info(self, state: DocInfoState) -> RenderInfo:
        if state.is_document:
            return self.render_info_manager_class.get_document_render_info(state)
        else:
            return self.render_info_manager_class.get_collection_render_info(state)
