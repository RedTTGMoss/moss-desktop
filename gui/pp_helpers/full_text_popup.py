import time
from typing import TYPE_CHECKING

import pygameextra as pe

if TYPE_CHECKING:
    from gui import GUI


class FullTextPopup(pe.ChildContext):
    LAYER = pe.AFTER_POST_LAYER
    EXISTING = {}

    def __init__(self, parent: 'GUI', text: pe.Text, referral_text: pe.Text = None):
        self.text = text
        self.offset = pe.display.display_reference.pos

        # Set the position of the text
        if referral_text is not None:
            self.text.rect.center = referral_text.rect.center
        else:
            self.text.rect.midbottom = pe.mouse.pos()

        self.used_at = time.time()
        super().__init__(parent)
        self.align_in_screen()

    def align_in_screen(self):
        # Make sure the text is inside the screen
        screen_rect = pe.Rect(0, 0, *self.size)
        screen_rect.scale_by_ip(.98, .98)
        if self.offset:
            self.text.rect.x += self.offset[0]
            self.text.rect.y += self.offset[1]
            self.offset = None
        self.text.rect.clamp_ip(screen_rect)

    def pre_loop(self):
        outline_rect = self.text.rect.inflate(self.ratios.pixel(10), self.ratios.pixel(10))
        pe.draw.rect(pe.colors.white, outline_rect, 0)
        pe.draw.rect(pe.colors.black, outline_rect, self.ratios.pixel(2))

    def loop(self):
        self.text.display()

    def post_loop(self):
        self.used_at = time.time()

    @classmethod
    def create(cls, parent: 'GUI', text: pe.Text, referral_text: pe.Text = None):
        if cls.EXISTING.get(id(text)) is None:
            cls.EXISTING[id(text)] = cls(parent, text, referral_text)
            return cls.EXISTING[id(text)]
        if time.time() - cls.EXISTING[id(text)].used_at < .05:
            cls.EXISTING[id(text)].align_in_screen()
            return cls.EXISTING[id(text)]
        else:
            del cls.EXISTING[id(text)]
            return cls.create(parent, text, referral_text)
