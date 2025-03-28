from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rm_api import Document
from rm_api.defaults import RM_SCREEN_SIZE, FileTypes


class DocumentSizeTracker(ABC):
    def __init__(
            self,
            document_center_x=0, document_center_y=0,
            document_cap_top=0, document_cap_bottom=0, document_cap_left=0, document_cap_right=0,
            frame_width=RM_SCREEN_SIZE[0], frame_height=RM_SCREEN_SIZE[1],
            offset_x=0, offset_y=0,
            reverse_frame_size=False
    ):
        self.document_center_x = document_center_x
        self.document_center_y = document_center_y
        self.document_cap_top = document_cap_top
        self.document_cap_bottom = document_cap_bottom
        self.document_cap_left = document_cap_left
        self.document_cap_right = document_cap_right
        self._track_top = 0
        self.track_bottom = frame_height
        self._track_left = 0
        self.track_right = frame_width
        self._frame_width = frame_width
        self._reverse_frame_size = reverse_frame_size
        self._frame_height = frame_height
        self.offset_x = offset_x
        self.offset_y = offset_y

    @property
    def frame_width(self):
        if self._reverse_frame_size:
            return self._frame_height
        return self._frame_width

    @property
    def frame_height(self):
        if self._reverse_frame_size:
            return self._frame_width
        return self._frame_height

    @property
    def track_top(self):
        return self._track_top

    @property
    def track_left(self):
        return self._track_left

    @property
    def track_width(self):
        return self.track_right - self.track_left

    @property
    def track_height(self):
        return self.track_bottom - self.track_top

    @frame_width.setter
    def frame_width(self, value):
        self.track_right = self.track_left + value
        self._frame_width = value

    @frame_height.setter
    def frame_height(self, value):
        self.track_bottom = self.track_top + value
        self._frame_height = value

    @track_top.setter
    def track_top(self, value):
        diff = value - self._track_top
        self._track_top = value
        self.track_bottom += diff

    @track_left.setter
    def track_left(self, value):
        diff = value - self._track_left
        self._track_left = value
        self.track_right += diff * 2

    def x(self, x):
        aligned_x = x + self.frame_width / 2
        if aligned_x > self.track_right:
            self.track_right = aligned_x
        if aligned_x < self.track_left:
            self.track_left = aligned_x

        return x

    def y(self, y):
        if y > self.track_bottom:
            self.track_bottom = y
        if y < self.track_top:
            self.track_top = y
        return y

    @property
    def format_kwargs(self):
        final = {
            'height': self.track_height,
            'width': self.track_width,
            'x_shift': self.frame_width / 2,
            'viewbox': f'{self.track_left} {self.track_top} {self.track_width} {self.track_height}',
            'template_rotate': 90 if self._reverse_frame_size else 0,
            'template_transform_y': RM_SCREEN_SIZE[0] if self._reverse_frame_size else 0,
            'template_transform_x': RM_SCREEN_SIZE[1] - RM_SCREEN_SIZE[0] if self._reverse_frame_size else 0
        }

        return final

    def __str__(self):
        return (f'DocumentSizeTracker('
                f'{self.track_left}->{self.track_right}, '
                f'{self.track_top}->{self.track_bottom}, '
                f'{self.track_width}, {self.track_height})')

    def __repr__(self):
        return str(self)

    @staticmethod
    def create_from_document(document: 'Document') -> 'DocumentSizeTracker':
        if document.content.file_type == FileTypes.PDF:
            return PDFSizeTracker(document)
        else:
            return NotebookSizeTracker(document)

    def validate_visible_portion(self, left: int, top: int, w: int, h: int):
        right = left + w
        bottom = top + h

        if right <= self.track_left or left >= self.track_right:
            return False

        if bottom <= self.track_top or top >= self.track_bottom:
            return False

        return True


class NotebookSizeTracker(DocumentSizeTracker):
    def __init__(self, document: 'Document'):
        super().__init__(reverse_frame_size=document.content.is_landscape)


class PDFSizeTracker(NotebookSizeTracker):
    def __init__(self, document: 'Document'):
        super().__init__(document)
        self._offset_x = self._frame_width * 0.2

    @property
    def frame_width(self):
        return super().frame_width() * 1.4

    @property
    def frame_height(self):
        return super().frame_height() * 1.4
