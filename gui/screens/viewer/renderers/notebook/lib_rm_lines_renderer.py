import threading

from pylibrm_lines import SceneTree, FailedToBuildTree
from pylibrm_lines.renderer import Renderer
import pygameextra as pe
from rm_lines import DocumentSizeTracker

from gui.defaults import Defaults
from gui.screens.viewer.renderers.notebook.expanded_notebook import ExpandedNotebook
from gui.screens.viewer.renderers.shared_model import AbstractRenderer
from typing import TYPE_CHECKING, Optional, List, Tuple

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


class LIB_rM_Lines_ChunkTask:
    def __init__(self, renderer: 'Renderer', agent: 'LIB_rM_Lines_ChunkingAgent', chunk_rect: pe.Rect):
        self.renderer = renderer
        self.agent = agent
        self.chunk_rect = chunk_rect

        # We undo the scaling of chunk_rect to match the agent's scale
        # We also adjust to add the base_rect offset which is in rm size
        self.rm_area = pe.Rect(
            chunk_rect.x / agent.scale + agent.base_rect.x,
            chunk_rect.y / agent.scale + agent.base_rect.y,
            chunk_rect.width / agent.scale,
            chunk_rect.height / agent.scale
        )
        self.loaded = False
        self.scale = agent.scale
        self.image: pe.Image = None
        threading.Thread(target=self.load, daemon=True).start()

    def load(self):
        # We need to load the data now from the renderer
        scaled_area = self.rm_area.copy()

        with self.agent.lock:
            raw = self.renderer.get_frame_raw(
                *scaled_area.topleft,
                *scaled_area.size,
                *self.chunk_rect.size
                # TODO: Potentially enable the user to pick if they want antialiasing
            )
        self.image = pe.Image(pe.pygame.image.frombytes(raw, self.chunk_rect.size, 'RGBA'))
        self.loaded = True

    @staticmethod
    def generate_hash(agent: 'LIB_rM_Lines_ChunkingAgent', chunk_rect: pe.Rect) -> int:
        return hash(
            f"{agent.base_rect.topleft}-{agent.base_rect.size}-"
            f"{agent.scale}-{chunk_rect.topleft}-{chunk_rect.size}"
        )


# noinspection PyPep8Naming
class LIB_rM_Lines_ChunkingAgent:
    CHUNK_SIZE = 100

    def __init__(self, renderer: 'Renderer', base_rect: pe.Rect, lock: threading.Lock):
        self.renderer = renderer
        self.base_rect = base_rect  # As scaled to the document as base size
        self.scale = 1  # Assuming no scale yet
        self.lock = lock
        self.cache = {}  # A hashmap to cache chunks

    def get_chunks(self, rect: pe.Rect):
        chunk_rects: List[pe.Rect] = []
        x_offset = 0
        y_offset = 0
        while y_offset < rect.height:
            while x_offset < rect.width:
                chunk_rect = pe.Rect(
                    x_offset,
                    y_offset,
                    self.CHUNK_SIZE,
                    self.CHUNK_SIZE
                )
                chunk_rects.append(chunk_rect)
                x_offset += self.CHUNK_SIZE
            x_offset = 0
            y_offset += self.CHUNK_SIZE

        screen_rect = pe.Rect(0, 0, *pe.display.get_size())

        chunks: List[LIB_rM_Lines_ChunkTask] = []
        for chunk_rect in chunk_rects:
            aligned_chunk_rect = chunk_rect.move(rect.topleft)
            if not aligned_chunk_rect.colliderect(screen_rect):
                continue
            hash_of_chunk = LIB_rM_Lines_ChunkTask.generate_hash(self, chunk_rect)
            if hash_of_chunk in self.cache:
                chunks.append(self.cache[hash_of_chunk])
                continue
            chunk = LIB_rM_Lines_ChunkTask(
                self.renderer,
                self, chunk_rect
            )
            self.cache[hash_of_chunk] = chunk
            chunks.append(chunk)
        return chunks


# noinspection PyPep8Naming
class LIB_rM_Lines_ExpandedNotebook(ExpandedNotebook):
    def __init__(self, renderer: 'Renderer'):
        super().__init__(LIB_rM_Lines_SizeTracker(renderer))
        self.renderer = renderer
        self.lock = threading.Lock()

    def get_frame_from_initial(self, frame_x, frame_y, final_width: int = None,
                               final_height: int = None) -> LIB_rM_Lines_ChunkingAgent:
        final_width = final_width or self.frame_width
        final_height = final_height or self.frame_height
        return LIB_rM_Lines_ChunkingAgent(
            self.renderer,
            pe.Rect(
                frame_x * self.frame_width,
                frame_y * self.frame_height,
                final_width,
                final_height
            ), self.lock
        )

    def update_scales(self, frames, scale: float):
        for frame in frames.values():
            if not frame.loaded:
                continue
            frame.sprite.scale = scale


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

            if self.gui.config.debug_viewer:
                pe.draw.rect(Defaults.LINE_GRAY, rect, self.gui.ratios.line)

            if frame_task.loaded:
                frame: LIB_rM_Lines_ChunkingAgent = frame_task.sprite

            chunks = frame.get_chunks(rect)
            for chunk in chunks:
                aligned_chunk_rect = chunk.chunk_rect.move(rect.topleft)
                if not chunk.loaded:
                    pe.draw.rect(Defaults.BUTTON_DISABLED_LIGHT_COLOR, aligned_chunk_rect)
                else:
                    chunk.image.display(aligned_chunk_rect.topleft)
                if self.gui.config.debug_viewer:
                    pe.draw.rect(pe.colors.red, aligned_chunk_rect, self.gui.ratios.line)

    def close(self):
        del self.tree
