from pylibrm_lines import SceneTree
from pylibrm_lines.renderer import Renderer

from gui.screens.viewer.renderers.shared_model import AbstractRenderer
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from gui import GUI
    from rm_api import Document
    from gui.screens.viewer.viewer import DocumentRenderer


# noinspection PyPep8Naming
class Notebook_LIB_rM_Lines_Renderer(AbstractRenderer):
    tree: Optional[SceneTree]
    renderer: Optional[Renderer]

    def __init__(self, document_renderer: 'DocumentRenderer'):
        super().__init__(document_renderer)
        self.tree = None
        self.renderer = None

    def load(self):
        self.tree = SceneTree.from_document(self.document, self.document_renderer.page_uuid)
        self.renderer = Renderer(self.tree)
        self.document_renderer.loading -= 1

    def handle_event(self, event):
        pass

    def render(self, page_uuid: str):
        pass

    def close(self):
        # pylibrm_lines needs to implement the methods to destroy the renderer and scene tree
        return