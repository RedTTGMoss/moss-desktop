import time
from typing import TYPE_CHECKING, Optional

import pygameextra as pe

if TYPE_CHECKING:
    from gui import GUI


class FullTextPopup(pe.ChildContext):
    LAYER = pe.AFTER_POST_LAYER
    EXISTING = {}

    rect: pe.Rect

    def __init__(self, parent: "GUI", text: pe.Text, referral_text: pe.Text = None):
        self.text = text
        self.offset = pe.display.display_reference.pos or (0, 0)
        self.referral_text = referral_text

        self.used_at = time.time()
        super().__init__(parent)

    def align_in_screen(self):
        # Copy original text rect to the popup rect
        self.rect = self.text.rect.copy()

        # Set the position of the text
        if self.referral_text is not None:
            self.rect.center = self.referral_text.rect.center
        else:
            self.rect.midbottom = pe.mouse.pos()

        # Make sure the text is inside the screen
        screen_rect = pe.Rect(0, 0, *self.size)
        screen_rect.scale_by_ip(0.98, 0.98)
        self.rect.x += self.offset[0]
        self.rect.y += self.offset[1]
        self.rect.clamp_ip(screen_rect)

    def pre_loop(self):
        self.align_in_screen()
        outline_rect = self.rect.inflate(self.ratios.pixel(10), self.ratios.pixel(10))
        pe.draw.rect(pe.colors.white, outline_rect, 0)
        pe.draw.rect(pe.colors.black, outline_rect, self.ratios.pixel(2))

    def loop(self):
        pe.display.blit(self.text.obj, self.rect.topleft)

    def post_loop(self):
        self.used_at = time.time()

    @classmethod
    def create(cls, parent: "GUI", text: pe.Text, referral_text: pe.Text = None):
        if cls.EXISTING.get(id(text)) is None:
            cls.EXISTING[id(text)] = cls(parent, text, referral_text)
            return cls.EXISTING[id(text)]
        if time.time() - cls.EXISTING[id(text)].used_at < 0.05:
            cls.EXISTING[id(text)].align_in_screen()
            return cls.EXISTING[id(text)]
        else:
            del cls.EXISTING[id(text)]
            return cls.create(parent, text, referral_text)

    @classmethod
    def fetch(cls, text: pe.Text) -> Optional["FullTextPopup"]:
        return cls.EXISTING.get(id(text), None)
