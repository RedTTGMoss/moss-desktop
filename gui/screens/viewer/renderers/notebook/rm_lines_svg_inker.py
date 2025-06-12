import re
import threading
from functools import lru_cache
from io import BytesIO
from traceback import print_exc
from typing import Dict, Tuple, Union, TYPE_CHECKING

import pygameextra as pe
from pygameextra import settings

from gui.defaults import Defaults
from gui.screens.viewer.renderers.notebook.expanded_notebook import ExpandedNotebook
from gui.screens.viewer.renderers.shared_model import AbstractRenderer
from rm_api import Document
from rm_lines import rm_bytes_to_svg
from rm_lines.inker.document_size_tracker import NotebookSizeTracker

if TYPE_CHECKING:
    pass


class rM_Lines_ExpandedNotebook(ExpandedNotebook):
    WIDTH_PATTERN = r'width="([\d.]+)"'
    HEIGHT_PATTERN = r'height="([\d.]+)"'
    VIEWPORT_PATTERN = r'viewBox="([\d.-]+) ([\d.-]+) ([\d.]+) ([\d.]+)"'

    def __init__(self, svg: str, track_xy: NotebookSizeTracker,
                 use_lock: threading.Lock = None):
        super().__init__(track_xy)
        self.svg = svg
        self.width_match = re.search(self.WIDTH_PATTERN, self.svg)
        self.height_match = re.search(self.HEIGHT_PATTERN, self.svg)
        self.viewbox_match = re.search(self.VIEWPORT_PATTERN, self.svg)
        self.use_lock = use_lock

    @lru_cache()
    def get_frame_from_initial(self, frame_x, frame_y, final_width: int = None, final_height: int = None,
                               scale: float = None) -> pe.Sprite:
        # Replace the svg viewport with a viewport to capture the frame

        width = float(self.width_match.group(1))
        height = float(self.height_match.group(1))
        x = float(self.viewbox_match.group(1))
        y = float(self.viewbox_match.group(2))
        w = float(self.viewbox_match.group(3))
        h = float(self.viewbox_match.group(4))

        final_width = final_width or self.frame_width
        final_height = final_height or self.frame_height

        # Replace values in the SVG content
        svg_content = re.sub(self.WIDTH_PATTERN, f'width="{final_width}"', self.svg)
        svg_content = re.sub(self.HEIGHT_PATTERN, f'height="{final_height}"', svg_content)
        svg_content = re.sub(self.VIEWPORT_PATTERN,
                             f'viewBox="'
                             f'{frame_x * self.frame_width - self.track_xy.offset_x} '
                             f'{frame_y * self.frame_height - self.track_xy.offset_y} '
                             f'{self.frame_width} '
                             f'{self.frame_height}"',
                             svg_content)

        encoded_svg_content = svg_content.encode()
        # if self.use_lock:
        #     with self.use_lock:
        #         return pe.Image(BytesIO(encoded_svg_content), (final_width, final_height))
        # else:
        # TODO: Instead of rendering each page render the SVG once and then slice it
        #  or use something else to render SVGs
        return pe.Sprite(BytesIO(encoded_svg_content), (final_width, final_height))

    def update_scales(self, frames, scale: float):
        for frame in frames.values():
            if not frame.loaded:
                continue
            frame.sprite.scale = (scale, scale)

# noinspection PyPep8Naming
class Notebook_rM_Lines_Renderer(AbstractRenderer):
    """
    This is a fast renderer for rM lines in SVG format
    Using the RMC project with a few modifications for better inking

    This renderer is also used for debug rendering and previews
    """

    pages: Dict[str, Union[rM_Lines_ExpandedNotebook, None]]
    RENDER_ERROR = 'viewer.errors.rendering_error'
    expanded_notebook: rM_Lines_ExpandedNotebook

    def __init__(self, document_renderer):
        super().__init__(document_renderer)
        self.pages = {}
        self.expanded_notebook = None

    def _load(self, page_uuid: str):
        if content := self.document.content_data.get(file_uuid := f'{self.document.uuid}/{page_uuid}.rm'):
            template = self.document.content.c_pages.get_page_from_uuid(page_uuid).template.value
            self.pages[file_uuid] = self.generate_expanded_notebook_from_rm(self.document, content,
                                                                            size=self.size, template=template)
        self.document_renderer.loading -= 1

    def load(self):
        self.check_and_load_page(self.document.content.c_pages.last_opened.value)
        self.document_renderer.loading -= 1  # check_and_load_page adds an extra loading

    def handle_event(self, event):
        pass

    def render(self, page_uuid: str):
        page = self.document.content.c_pages.get_page_from_uuid(page_uuid)
        rm_file = f'{self.document.uuid}/{page.id}.rm'

        if rm_file in self.pages:
            if self.pages[rm_file] is None:
                self.error = self.RENDER_ERROR
                return
            self.expanded_notebook = self.pages[rm_file]

            # TODO: Check zoom and handle higher quality chunks of the page when zoomed in

            # TODO: Remove this old single frame code
            # initial_frame = expanded_notebook.get_frame_from_initial(
            #     0, 0
            # )
            # scale = self.gui.ratios.rm_scaled(expanded_notebook.frame_width) * self.document_renderer.zoom
            # initial_frame.scale = (scale, scale)
            # rect = pe.Rect(0, 0, *initial_frame.size)
            # rect.centerx = self.document_renderer.center_x
            # rect.centery = self.document_renderer.center_y
            #
            # # if not self.document_renderer.renderer:
            # #     # Draw notebook shadow
            # #     shadow_rect = rect.inflate(self.gui.ratios.document_viewer_notebook_shadow_size,
            # #                                self.gui.ratios.document_viewer_notebook_shadow_size)
            # #     pe.draw.rect(Defaults.LINE_GRAY, shadow_rect, self.gui.ratios.seperator,
            # #                  edge_rounding=self.gui.ratios.document_viewer_notebook_shadow_radius)
            #
            # initial_frame.display(rect.topleft)

            frames = self.expanded_notebook.get_frames(
                -self.document_renderer.center_x, -self.document_renderer.center_y,
                *self.size, self.document_renderer.zoom
            )

            expected_frame_sizes = self.get_expected_frame_sizes()

            rotate_icon = self.gui.icons['rotate']

            for (frame_x, frame_y), frame_task in frames.items():
                if frame_task.loaded:
                    frame = frame_task.sprite
                else:
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
                    continue

                rect = pe.Rect(0, 0, *frame.size)
                rect.center = self.document_renderer.center
                rect.move_ip(
                    frame_x * frame.size[0],
                    frame_y * frame.size[1]
                )
                frame.display(rect.topleft)
                if self.gui.config.debug_viewer:
                    pe.draw.rect(pe.colors.magenta, rect, self.gui.ratios.line)

            if self.error and self.error.text == self.RENDER_ERROR:
                self.error = None
        elif self.error and self.error.text == self.RENDER_ERROR:
            self.error = None
        elif rm_file in self.document.content_files:
            self.check_and_load_page(page_uuid)

    def check_and_load_page(self, page_uuid: str):
        self.document_renderer.loading += 1
        threading.Thread(target=self._load, args=(page_uuid,), daemon=True).start()

    @staticmethod
    def generate_expanded_notebook_from_rm(document: Document, content: bytes, size: Tuple[int, int] = None,
                                           use_lock: threading.Lock = None,
                                           template: str = None) -> rM_Lines_ExpandedNotebook:
        try:
            template_key = f'templates/{template}'
            template_data = settings.game_context.data.get(template_key, None)

            svg, track_xy = rm_bytes_to_svg(content, document, template_data.decode() if template_data else None)
            # with open('save.svg', 'w') as f:
            #     f.write(svg)
            expanded = rM_Lines_ExpandedNotebook(svg, track_xy, use_lock)
            expanded.get_frame_from_initial(0, 0, *(size if size else ()))
        except Exception as e:
            print_exc()
            return None
        else:
            return expanded

    def close(self):
        pass
