import threading

from pylibrm_lines import SceneTree, FailedToBuildTree
from pylibrm_lines.renderer import Renderer
import pygameextra as pe
from rm_lines import DocumentSizeTracker

from gui.defaults import Defaults
from gui.screens.viewer.renderers.notebook.expanded_notebook import ExpandedNotebook
from gui.screens.viewer.renderers.shared_model import AbstractRenderer
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from gui import GUI
    from rm_api import Document
    from gui.screens.viewer.viewer import DocumentRenderer


# noinspection PyPep8Naming
class LIB_rM_Lines_SizeTracker(DocumentSizeTracker):
    def __init__(self, renderer: 'Renderer' = None):
        super().__init__()
        self.renderer = renderer

        self.reset_information()

    def reset_information(self):
        self.track_top = 0
        self.track_left = 0
        self.track_bottom = 0
        self.track_right = 0
        for layer in self.renderer.layers:
            self.calculate_info_for_layer(layer.uuid)

    def calculate_info_for_layer(self, layer_id: str):
        layer = self.renderer.get_layer_by_uuid(layer_id)
        if not layer:
            return
        size_tracker = layer.size_tracker
        self.track_top = min(self.track_top, size_tracker.top)
        self.track_left = min(self.track_left, size_tracker.left)
        self.track_bottom = max(self.track_bottom, size_tracker.bottom)
        self.track_right = max(self.track_right, size_tracker.right)


# noinspection PyPep8Naming
class LIB_rM_Lines_ExpandedNotebook(ExpandedNotebook):
    def __init__(self, renderer: 'Renderer'):
        super().__init__(LIB_rM_Lines_SizeTracker(renderer))
        self.renderer = renderer

    def get_frame_from_initial(self, frame_x, frame_y, final_width: int = None, final_height: int = None) -> pe.Sprite:
        print(f"frame: {frame_x}x{frame_y} {final_width}x{final_height}")

    def update_scales(self, frames, scale: float):
        pass


# noinspection PyPep8Naming
class Notebook_LIB_rM_Lines_Renderer(AbstractRenderer):
    tree: Optional[SceneTree]
    renderer: Optional[Renderer]

    FAILED_TO_BUILD_TREE_ERROR = 'viewer.errors.failed_to_build_tree'

    def __init__(self, document_renderer: 'DocumentRenderer'):
        super().__init__(document_renderer)
        self.tree = None
        self.renderer = None
        self.rm_render_rect = None
        self.error = None
        self.current_page_uuid = None

    def _load(self, page_uuid: str):
        try:
            self.tree = SceneTree.from_document(self.document, page_uuid)
        except FailedToBuildTree:
            self.error = self.FAILED_TO_BUILD_TREE_ERROR
            return
        self.renderer = Renderer(self.tree)
        self.expanded_notebook = LIB_rM_Lines_ExpandedNotebook(self.renderer)
        self.document_renderer.loading -= 1

    def load(self):
        self.check_and_load_page(self.document.content.c_pages.last_opened.value)
        self.document_renderer.loading -= 1  # check_and_load_page adds an extra loading

    def check_and_load_page(self, page_uuid: str):
        self.current_page_uuid = page_uuid
        self.document_renderer.loading += 1
        threading.Thread(target=self._load, args=(page_uuid,), daemon=True).start()

    def handle_event(self, event):
        pass

    def render(self, page_uuid: str):
        if (self.tree and self.tree.page_uuid != page_uuid) or self.current_page_uuid != page_uuid:
            self.check_and_load_page(page_uuid)
            return
        if self.error:
            return

        frames = self.expanded_notebook.get_frames(
            -self.document_renderer.center_x, -self.document_renderer.center_y,
            *self.size, self.document_renderer.zoom
        )

        expected_frame_sizes = self.get_expected_frame_sizes()

        rotate_icon = self.gui.icons['rotate']

        for (frame_x, frame_y), frame_task in frames.items():
            rect = pe.Rect(0, 0, *expected_frame_sizes[0])
            icon_rect = pe.Rect(0, 0, *rotate_icon.size)
            rect.center = self.document_renderer.center
            rect.move_ip(
                frame_x * expected_frame_sizes[0][0],
                frame_y * expected_frame_sizes[0][1]
            )
            icon_rect.center = rect.center

            rotate_icon.display(icon_rect.topleft)
            pe.draw.rect(Defaults.LINE_GRAY, rect, self.gui.ratios.line)

    def close(self):
        del self.tree
