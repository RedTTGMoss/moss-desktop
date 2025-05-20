import sys
import threading
import time
import webbrowser
from typing import TYPE_CHECKING, List

import pygameextra as pe
from pyperclip import paste as pyperclip_paste
from rm_api import DEFAULT_REMARKABLE_URI, DEFAULT_REMARKABLE_DISCOVERY_URI
from rm_api.auth import FailedToGetToken, MissingTabletLink

from gui.defaults import Defaults
from gui.events import ResizeEvent
from gui.gui import APP_NAME
from gui.pp_helpers.popups import ConfirmPopup
from gui.rendering import render_button_using_text
from gui.screens.loader import Loader
from gui.screens.mixins import ButtonReadyMixin
from gui.screens.name_field_screen import NameFieldScreen

if TYPE_CHECKING:
    from gui.gui import GUI


class CloudPopup(ConfirmPopup):
    CLOSE_TEXT = "Use remarkable cloud"
    BUTTON_TEXTS = {
        **ConfirmPopup.BUTTON_TEXTS,
        'confirm': "Use custom cloud",
    }


class MissingTabletPopup(ConfirmPopup):
    CLOSE_TEXT = "Link as a desktop (will need to link your tablet first)"
    BUTTON_TEXTS = {
        **ConfirmPopup.BUTTON_TEXTS,
        'confirm': "Link as a tablet",
    }


class CodeScreen(ButtonReadyMixin, pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER
    CODE_LENGTH = 8
    BACKSPACE_DELETE_DELAY = 0.3  # Initial backspace delay
    BACKSPACE_DELETE_SPEED = 0.05  # After initial backspace delay
    EVENT_HOOK_NAME = 'code_screen_resize_check'

    BUTTON_TEXTS = {
        'change': "I wanna change my cloud",
    }

    parent_context: 'GUI'
    screens: List[pe.ChildContext]

    website_info: pe.Text

    def __init__(self, parent: 'GUI'):
        super().__init__(parent)
        self.underscore = pe.Text(
            "_",
            Defaults.CODE_FONT, self.ratios.loader_logo_text_size,
            colors=Defaults.CODE_COLOR
        )
        self.underscore_red = pe.Text(
            "_",
            Defaults.CODE_FONT, self.ratios.loader_logo_text_size,
            colors=(Defaults.RED, None)
        )
        self.logo = pe.Text(
            APP_NAME,
            Defaults.LOGO_FONT, self.ratios.loader_logo_text_size,
            self.logo_position,
            Defaults.TEXT_COLOR_T
        )
        self.code_info = pe.Text(
            "Input your connect code",
            Defaults.LOGO_FONT, self.ratios.code_screen_info_size,
            colors=Defaults.TEXT_COLOR_T
        )
        self.get_website_info()
        self.loader = Loader(self.parent_context)
        self.loader.load_one('tablet')
        self.loader.load_one('desktop')
        self.loader.load_one('share')
        self.update_code_text_positions()
        self.api.add_hook(self.EVENT_HOOK_NAME, self.resize_check_hook)
        self.remarkable = False  # Wether to authenticate as a tablet or desktop
        self.code = []
        self.code_text = []
        self.code_failed = False
        self.checking_code = False
        self.hold_backspace = False
        self.hold_backspace_timer = None
        self.warning: CloudPopup = None
        self.handle_texts()

    def get_website_info(self):
        self.website_info = pe.Text(
            self.config.uri.replace('https://', '').replace('http://', ''),
            Defaults.LOGO_FONT, self.ratios.code_screen_info_size,
            colors=Defaults.TEXT_COLOR_LINK if self.connecting_to_real_remarkable() else Defaults.TEXT_COLOR_T
        )

    @property
    def logo_position(self):
        return (
            self.width // 2,
            self.height // 2 - (self.underscore.rect.height + self.ratios.code_screen_header_padding // 2)
        )

    def update_code_text_positions(self):
        self.code_info.rect.midtop = self.logo.rect.midbottom
        self.code_info.rect.top += self.ratios.code_screen_header_padding // 2
        self.website_info.rect.centerx = self.code_info.rect.centerx
        self.underscore.rect.top = self.logo.rect.bottom + self.ratios.code_screen_header_padding
        self.underscore_red.rect.top = self.underscore.rect.top
        self.website_info.rect.bottom = self.underscore.rect.bottom + self.ratios.code_screen_header_padding

    def resize_check_hook(self, event):
        if isinstance(event, ResizeEvent):
            self.logo.rect.center = self.logo_position
            self.update_code_text_positions()
            self.handle_texts()

    def add_character(self, char: str):
        if len(self.code) == self.CODE_LENGTH:
            return
        self.code.append(char)
        self.code_text.append(pe.Text(
            char,
            Defaults.CODE_FONT, self.ratios.loader_logo_text_size,
            colors=Defaults.TEXT_COLOR_CODE
        ))
        if len(self.code) == self.CODE_LENGTH:
            self.check_code()

    def handle_event(self, event):
        if event.type == pe.pygame.KEYDOWN:
            mods = pe.pygame.key.get_mods()
            system_mod = mods & pe.KMOD_META if sys.platform == 'darwin' else mods & pe.KMOD_CTRL
            if system_mod and event.key == pe.pygame.K_v:
                for char in pyperclip_paste():
                    if char.isalnum():
                        self.add_character(char)

            if event.key == pe.pygame.K_BACKSPACE and len(self.code) > 0:
                del self.code[-1]
                del self.code_text[-1]
                self.code_failed = False
                self.hold_backspace = True
                self.hold_backspace_timer = time.time() + self.BACKSPACE_DELETE_DELAY
            elif len(self.code) == self.CODE_LENGTH:
                pass
            elif event.unicode.isalnum():
                self.add_character(event.unicode)
        elif event.type == pe.pygame.KEYUP:
            if event.key == pe.pygame.K_BACKSPACE:
                self.hold_backspace = False

    def check_code(self):
        self.checking_code = True
        threading.Thread(target=self.check_code_thread, daemon=True).start()

    def check_code_thread(self):
        try:
            self.api.get_token("".join(self.code), self.remarkable)
            self.add_screen(self.loader)
            self.api.remove_hook(self.EVENT_HOOK_NAME)
            del self.screens[0]
        except MissingTabletLink:
            self.warning = MissingTabletPopup(
                self.parent_context,
                "Your tablet is not linked yet.",
                f"{APP_NAME} typically identifies as a desktop app.\n"
                "However it can identify as a tablet to pass this check\n"
                "Would you like to identify as a tablet. You have to get a new pair code.\n"
                f"Alternatively, link your tablet before using {APP_NAME} and then pair as a desktop app.",
                self.switch_link_mode, None)
        except FailedToGetToken:
            self.code_failed = True
        self.checking_code = False

    def switch_link_mode(self):
        self.remarkable = not self.remarkable
        self.clear()

    def clear(self):
        self.code.clear()
        self.code_text.clear()

    def pre_loop(self):
        if self.warning and self.warning.closed:
            self.warning = None
        elif self.warning:
            self.warning()

        # Handling backspace
        if self.hold_backspace and time.time() - self.hold_backspace_timer > self.BACKSPACE_DELETE_SPEED and len(
                self.code) > 0:
            self.hold_backspace_timer = time.time()
            del self.code[-1]
            del self.code_text[-1]

    def connecting_to_real_remarkable(self):
        return 'remarkable.com' in self.config.uri

    def loop(self):
        self.logo.display()
        self.code_info.display()
        self.website_info.display()
        if self.connecting_to_real_remarkable():
            link_icon = self.icons['tablet'] if self.remarkable else self.icons['desktop']
            share_rect = pe.Rect(
                self.website_info.rect.right,
                self.website_info.rect.top,
                *self.icons['share'].size
            )
            self.icons['share'].display(share_rect.topleft)
            pe.button.rect(
                self.ratios.pad_button_rect(self.website_info.rect),
                Defaults.TRANSPARENT_COLOR, Defaults.BUTTON_ACTIVE_COLOR,
                action=webbrowser.open,
                data=("https://my.remarkable.com/#desktop", 0, True),
                name='code_screen.webopen<rm>'
            )
            share_rect.left = share_rect.right + self.ratios.code_screen_spacing * 3
            link_icon.display(share_rect.topleft)
            pe.button.rect(
                link_button_rect := self.ratios.pad_button_rect(share_rect),
                Defaults.TRANSPARENT_COLOR, Defaults.BUTTON_ACTIVE_COLOR,
                action=self.switch_link_mode,
                name='code_screen.switch_link_mode'
            )
            pe.draw.rect(Defaults.OUTLINE_COLOR, link_button_rect, self.ratios.outline)
        else:
            if self.remarkable:
                self.remarkable = False
            pe.button.rect(
                self.ratios.pad_button_rect(self.website_info.rect),
                Defaults.TRANSPARENT_COLOR, Defaults.BUTTON_ACTIVE_COLOR,
                action=webbrowser.open,
                data=(self.config.uri, 0, True),
                name='code_screen.webopen<custom>'
            )

        x = self.width // 2 - self.underscore.rect.width * (self.CODE_LENGTH / 2)
        x -= self.ratios.code_screen_spacing * (self.CODE_LENGTH - 1) / 2

        underscore = self.underscore_red if self.code_failed else self.underscore

        for i in range(self.CODE_LENGTH):
            underscore.rect.left = x
            underscore.display()
            if i < len(self.code):
                self.code_text[i].rect.midbottom = underscore.rect.midbottom
                self.code_text[i].display()
            x += underscore.rect.width + self.ratios.code_screen_spacing

    def change_cloud(self):
        self.warning = CloudPopup(
            self.parent_context,
            "Using custom cloud",
            "Moss supports custom clouds like rmfakecloud by ddvk.\n"
            "We have even communicated with ddvk for improved compatibility.\n"
            "You can input the address of your cloud on the next screen\n"
            "or use the remarkable cloud.", self.open_cloud_input, self.use_rm_cloud
        )

    def open_cloud_input(self):
        NameFieldScreen(self.parent_context, "Input your cloud address", '', self._change_cloud, self.use_rm_cloud,
                        submit_text="Set cloud address", cancel_text="Use remarkable cloud")

    def use_rm_cloud(self):
        self.set_cloud(DEFAULT_REMARKABLE_URI, DEFAULT_REMARKABLE_DISCOVERY_URI)

    def _change_cloud(self, cloud):
        self.set_cloud(cloud, cloud)

    def set_cloud(self, uri, discovery_uri):
        self.api.uri = uri
        self.api.discovery_uri = discovery_uri

        self.config.uri = uri
        self.config.discovery_uri = discovery_uri

        self.parent_context.dirty_config = True
        self.get_website_info()
        self.update_code_text_positions()
        self.api.reconnect()

    def post_loop(self):
        if not self.warning:
            render_button_using_text(self.parent_context, self.texts['change'], action=self.change_cloud,
                                     name='code_screen.change_cloud', outline=True)

        if not self.checking_code:
            return

        # Make a frozen paper effect
        pe.fill.transparency(pe.colors.white, 150)
