from typing import TYPE_CHECKING

import pygameextra as pe

from gui import APP_NAME
from gui.defaults import Defaults
from gui.events import ResizeEvent
from gui.gui import ConfigDict
from gui.i10n import t
from gui.rendering import render_button_using_text
from gui.screens.mixins import TitledMixin, ButtonReadyMixin

if TYPE_CHECKING:
    from gui import GUI

def translation_pair(key: str) -> tuple[str, str]:
    """Returns the title and description for a popup based on the given key."""
    return (
        f'popups.{key}.title',
        f'popups.{key}.description'
    )

class Popup(pe.ChildContext, ButtonReadyMixin, TitledMixin):
    LAYER = pe.AFTER_LOOP_LAYER
    COLOR = (*Defaults.TRANSPARENT_COLOR[:3], 175)
    TITLE_COLORS = Defaults.TEXT_COLOR_H
    CLOSE_TEXT = "popups.confirm.close"
    BUTTON_TEXTS = {
        'close': "",
    }

    def __init__(self, parent: "GUI", title: str, description: str, **kwargs):
        super().__init__(parent)
        self.handle_title(title, **kwargs)
        self.BUTTON_TEXTS['close'] = self.CLOSE_TEXT
        self.handle_texts(**kwargs)
        self.description = pe.Text(t(description, None, **kwargs), Defaults.DEBUG_FONT, self.ratios.popup_description_size,
                                   colors=self.TITLE_COLORS)
        self.description.rect.left = self.title.rect.left
        self.description.rect.top = self.title.rect.bottom + self.ratios.popup_description_padding
        self.closed = False
        self.HOOK_ID = f'popup_{id(self)}_resize'
        self.api.add_hook(self.HOOK_ID, self.resize_check_hook)

    def close(self):
        self.closed = True
        self.api.remove_hook(self.HOOK_ID)

    def resize_check_hook(self, event):
        if isinstance(event, ResizeEvent):
            self.handle_texts()

    def loop(self):
        if self.closed:
            return
        pe.button.rect((0, 0, *self.size), self.COLOR, self.COLOR, name=f'popup_{id(self)}_background')
        self.title.display()
        self.description.display()
        render_button_using_text(self.parent_context, self.texts['close'], outline=self.ratios.outline,
                                 inactive_color=Defaults.BACKGROUND,
                                 active_color=Defaults.BUTTON_ACTIVE_COLOR_INVERTED,
                                 action=self.close, name=f'popup_{id(self)}_close', text_infront=True)


class ConfirmPopup(Popup):
    CLOSE_TEXT = "popups.confirms.close"
    BUTTON_TEXTS = {
        'confirm': "popups.confirms.confirm",
        'close': "",
    }

    def __init__(self, parent: "GUI", title: str, description: str, confirm_action=None, cancel_action=None):
        super().__init__(parent, title, description)
        self.confirm_action = confirm_action
        self.cancel_action = cancel_action

    def _close(self):
        super().close()

    def close(self):
        if self.cancel_action:
            self.cancel_action()
        self._close()

    def ok(self):
        if self.confirm_action:
            self.confirm_action()
        self._close()

    def loop(self):
        super().loop()

        render_button_using_text(self.parent_context, self.texts['confirm'], outline=self.ratios.outline,
                                 inactive_color=Defaults.BACKGROUND,
                                 active_color=Defaults.BUTTON_ACTIVE_COLOR_INVERTED,
                                 action=self.ok, name=f'popup_{id(self)}_confirm', text_infront=True)


class InstallPopup(ConfirmPopup):
    BUTTON_TEXTS = {
        'confirm': "popups.installs.confirm",
        'close': "",
    }


class GUIConfirmPopup(ConfirmPopup):
    LAYER = pe.AFTER_POST_LAYER
    TYPE: str = None


class GUISyncLockedPopup(GUIConfirmPopup):
    TYPE = "sync_locked"

    def __init__(self, parent: "GUI"):
        super().__init__(
            parent,
            "Sync in progress",
            f"There is still a sync in progress. If you close {APP_NAME} now you may infer data loss!\n"
            "It is recommended to wait until the sync is finished.\n\n"
            f"Are you sure you want to force close {APP_NAME} without waiting for the sync to finish?\n"
            f"Note: {APP_NAME} will proceed to close after the sync is finished.",
            confirm_action=parent.soft_quit
        )


class SwitchToLibRmLines(GUIConfirmPopup):
    TYPE = "switch_to_lib_rm_lines"
    BUTTON_TEXTS = {
        'confirm': "popups.switch_to_librm_lines.confirm",
        'close': "",
    }
    CLOSE_TEXT = "popups.switch_to_librm_lines.close"

    config: "ConfigDict"

    def __init__(self, parent: "GUI", document_viewer: "DocumentViewer"):
        self.document_viewer = document_viewer
        super().__init__(
            parent,
            *translation_pair('confirms.switch_to_librm_lines'),
            confirm_action=self.switch_to_lib_rm_lines,
            cancel_action=self.initialise_svg_renderer
        )

    def switch_to_lib_rm_lines(self):
        self.config.guides.switch_to_librm_lines = True
        self.config.notebook_render_mode = 'librm_lines_renderer'
        self.parent_context.dirty_config = True
        self.document_viewer.init_renderer()

    def initialise_svg_renderer(self):
        self.config.guides.switch_to_librm_lines = True
        self.parent_context.dirty_config = True
        self.document_viewer.init_renderer()

    def handle_event(self, e):  # Required for DocumentViewer
        pass


class WarningPopup(Popup):
    CLOSE_TEXT = "popups.warnings.close"