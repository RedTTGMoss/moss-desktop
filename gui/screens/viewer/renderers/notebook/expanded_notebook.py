from abc import ABC, abstractmethod
from functools import lru_cache

import pygameextra as pe
from pygameextra import settings

from gui.screens.viewer.renderers.shared_model import LoadTask
from rm_lines.inker.document_size_tracker import NotebookSizeTracker


class ExpandedNotebook(ABC):
    def __init__(self, track_xy: NotebookSizeTracker):
        self.frame_width = track_xy.frame_width
        self.frame_height = track_xy.frame_height
        self.frame_size = (self.frame_width, self.frame_height)
        self.track_xy = track_xy
        if settings.config.debug:
            print(f'Expanded notebook debug, frame size: {track_xy.frame_width}, {track_xy.frame_height} {track_xy}')

    def get_frames(self, area_x: int, area_y: int, area_width: int, area_height: int, scale: float = 1):

        visible_frames = []

        scale *= settings.game_context.ratios.rm_scaled(self.frame_width)

        frame_width_scaled = self.frame_width * scale
        frame_height_scaled = self.frame_height * scale

        # Handle centering issue
        area_x += frame_width_scaled / 2
        area_y += frame_height_scaled / 2

        start_x = int(area_x // frame_width_scaled)
        end_x = int((area_x + area_width) // frame_width_scaled)
        start_y = int(area_y // frame_height_scaled)
        end_y = int((area_y + area_height) // frame_height_scaled)

        for frame_x in range(start_x, end_x + 1):
            for frame_y in range(start_y, end_y + 1):
                frame_left = frame_x * frame_width_scaled
                frame_right = frame_left + frame_width_scaled
                frame_top = frame_y * frame_height_scaled
                frame_bottom = frame_top + frame_height_scaled

                if (frame_right > area_x and frame_left < area_x + area_width and
                        frame_bottom > area_y and frame_top < area_y + area_height):
                    if self.track_xy.validate_visible_portion(
                            frame_x * self.frame_width - self.track_xy.offset_x,
                            frame_y * self.frame_height - self.track_xy.offset_y,
                            self.frame_width, self.frame_height
                    ):
                        visible_frames.append((frame_x, frame_y))

        frames = {}

        for frame in visible_frames:
            frames[frame] = self.task_frame_from_initial(*frame)
            if frames[frame].loaded:
                frames[frame].sprite.scale = (scale, scale)

        return frames

    @abstractmethod
    def get_frame_from_initial(self, frame_x, frame_y, final_width: int = None, final_height: int = None) -> pe.Sprite:
        ...

    @lru_cache()
    def task_frame_from_initial(self, frame_x, frame_y, final_width: int = None,
                                final_height: int = None) -> LoadTask:
        return LoadTask(self.get_frame_from_initial, frame_x, frame_y, final_width, final_height)