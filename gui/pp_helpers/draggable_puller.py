from typing import TYPE_CHECKING

import pygameextra as pe

if TYPE_CHECKING:
    from gui import GUI


class DraggablePuller(pe.ChildContext):
    LAYER = pe.BEFORE_POST_LAYER

    def __init__(
        self,
        parent: "GUI",
        rect,
        detect_x: int = None,
        detect_y: int = None,
        callback_x=None,
        callback_y=None,
        draw_callback_x=None,
        draw_callback_y=None,
    ):
        self.rect = rect
        self.draggable = pe.Draggable(self.rect.topleft, self.rect.size)
        self.detect_x = detect_x
        self.detect_y = detect_y
        self.callback_x = callback_x
        self.callback_y = callback_y
        self.draw_callback_x = draw_callback_x
        self.draw_callback_y = draw_callback_y
        super().__init__(parent)

    def loop(self):
        dragging, pos = self.draggable.check()

        # Uncomment the following line to see the draggable area
        # pe.draw.rect(pe.colors.red, (*pos, *self.draggable.area), 1)

        move_amount = tuple(
            original - current for original, current in zip(self.rect.topleft, pos)
        )
        if move_amount[0] == 0 and move_amount[1] == 0:
            return
        if self.detect_x is not None and self.callback_x is not None:
            if 0 < self.detect_x < move_amount[0]:
                if not dragging:
                    self.callback_x()
                elif self.draw_callback_x is not None:
                    self.draw_callback_x()
            elif 0 > self.detect_x > move_amount[0]:
                if not dragging:
                    self.callback_x()
                elif self.draw_callback_x is not None:
                    self.draw_callback_x()
        if self.detect_y is not None and self.callback_y is not None:
            if 0 < self.detect_y < move_amount[1]:
                if not dragging:
                    self.callback_y()
                elif self.draw_callback_y is not None:
                    self.draw_callback_y()
            elif 0 > self.detect_y > move_amount[1]:
                if not dragging:
                    self.callback_y()
                elif self.draw_callback_y is not None:
                    self.draw_callback_y()

        if not dragging:
            self.draggable.pos = self.rect.topleft
