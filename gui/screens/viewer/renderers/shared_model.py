import threading
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rm_api.models import Document
    from gui import GUI
    from gui.screens.viewer.viewer import DocumentRenderer


class AbstractRenderer(ABC):
    def __init__(self, document_renderer: 'DocumentRenderer'):
        self.document_renderer = document_renderer
        self.gui: 'GUI' = document_renderer.parent_context
        self.document: 'Document' = document_renderer.document

    @property
    def error(self):
        return self.document_renderer.error

    @error.setter
    def error(self, value):
        self.document_renderer.error = value

    @property
    def size(self):
        return self.document_renderer.size

    @property
    def width(self):
        return self.document_renderer.width

    @property
    def height(self):
        return self.document_renderer.height

    @abstractmethod
    def load(self):
        ...

    @abstractmethod
    def handle_event(self, event):
        ...

    @abstractmethod
    def render(self, page_uuid: str):
        ...

    @abstractmethod
    def close(self):
        ...

    def get_enhance_scale(self):
        # Return an enhancement scale for when the page is zoomed in
        # Will at most return between 1 and 4.5
        scale = max(2, min(9, self.document_renderer.zoom // 0.5)) * 0.5
        return scale / self.document_renderer.config.scale

    def get_expected_frame_sizes(self):
        expected_frame_sizes = tuple(
            # Calculate frame size for both zoom levels to determine the zoom scaling offset
            (
                self.frame_width * zoom *
                self.gui.ratios.rm_scaled(self.frame_width),
                self.frame_height * zoom *
                self.gui.ratios.rm_scaled(self.frame_width)
            )
            for zoom in (self.document_renderer.zoom, self.document_renderer.zoom + 1)
        )
        self.document_renderer.zoom_scaling_offset = tuple(
            # Half the change when changing zooming by 1 unit
            (expected_frame_sizes[0][_] - expected_frame_sizes[1][_]) / 2
            for _ in range(2)
        )
        self.document_renderer.zoom_reference_size = expected_frame_sizes[0]
        return expected_frame_sizes

    @property
    def frame_width(self):
        return self.expanded_notebook.frame_width

    @property
    def frame_height(self):
        return self.expanded_notebook.frame_height


class LoadTask:
    def __init__(self, function, *args, **kwargs):
        self.loaded = False
        self.sprite = None
        self.function = function
        self.args = args
        self.kwargs = kwargs
        threading.Thread(target=self.load, daemon=True).start()

    def load(self):
        self.sprite = self.function(*self.args, **self.kwargs)
        self.loaded = True
