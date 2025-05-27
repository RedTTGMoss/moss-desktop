import os
import random
import threading
import time
from traceback import print_exc
from typing import TYPE_CHECKING, Union, Dict

import pygameextra as pe
from rm_api.notifications.models import SyncCompleted, NewDocuments

from gui import APP_NAME
from gui.defaults import Defaults
from gui.helpers import invert_icon
from gui.screens.main_menu import MainMenu
from gui.screens.mixins import LogoMixin

if TYPE_CHECKING:
    from gui.gui import GUI
    from rm_api import API
    from gui.i10n import I10nManager
    from gui.extensions import ExtensionManager


class ReusedIcon:
    def __init__(self, key: str, scale: float):
        self.key = key
        self.scale = scale


class InvertedIcon:
    def __init__(self, item: 'AcceptedLoadTypes'):
        self.item = item


class ResizedIcon:
    def __init__(self, item: str, scale: float):
        self.item = item
        self.scale = scale


class TreatAsData:
    def __init__(self, item: str):
        self.item = item


AcceptedLoadTypes = Union[str, ReusedIcon, ResizedIcon, InvertedIcon, TreatAsData]


class Loader(pe.ChildContext, LogoMixin):
    TO_LOAD = {
        # Icons and Images
        'moss': os.path.join(Defaults.ICON_DIR, 'moss.svg'),
        'tablet': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'tablet.svg')),
        'desktop': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'desktop.svg')),
        'folder': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'folder.svg')),
        'folder_add': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'folder_add.svg')),
        'folder_empty': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'folder_empty.svg')),
        'star': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'star.svg')),
        'star_empty': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'star_empty.svg')),
        'tag': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'tag.svg')),
        'chevron_down': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'chevron_down.svg')),
        'chevron_right': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'chevron_right.svg')),
        'chevron_left': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'chevron_left.svg')),
        'small_chevron_down': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'small_chevron_down.svg')),
        'small_chevron_right': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'small_chevron_right.svg')),
        'cloud': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'cloud.svg')),
        'cloud_download': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'cloud_download.svg')),
        'cloud_synced': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'cloud_synced.svg')),
        'checkmark': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'checkmark.svg')),
        'warning_circle': os.path.join(Defaults.ICON_DIR, 'warning_circle.svg'),
        'notebook_large': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'notebook_large.svg')),
        'notebook': InvertedIcon(ReusedIcon('notebook_large', 0.333)),
        'notebook_add': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'notebook_add.svg')),
        'share': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'share.svg')),
        'export': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'export.svg')),
        'copy': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'copy.svg')),
        'import': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'import.svg')),
        'info': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'information_circle.svg')),
        'glasses': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'glasses.svg')),
        'free_mode': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'free_mode.svg')),
        'rotate': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'rotate.svg')),
        'puzzle': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'puzzle.svg')),
        'burger': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'burger.svg')),
        'filter': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'filter.svg')),
        'context_menu': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'context_menu.svg')),
        'pencil': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'pencil.svg')),
        'my_files': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'my_files.svg')),
        'trashcan': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'trashcan.svg')),
        'trashcan_delete': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'trashcan_delete.svg')),
        'cog': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'cog.svg')),
        'heart': os.path.join(Defaults.ICON_DIR, 'heart.svg'),
        'language': os.path.join(Defaults.ICON_DIR, 'language.svg'),
        'compass': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'compass.svg')),
        'duplicate': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'duplicate.svg')),
        'text_edit': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'text_edit.svg')),
        'move': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'move.svg')),
        'x_medium': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'x_medium.svg')),
        'x_small': InvertedIcon(os.path.join(Defaults.ICON_DIR, 'x_small.svg')),
        # 'screenshot': 'Screenshot_20241023_162027.png',

        # Data files
        'light_pdf': os.path.join(Defaults.DATA_DIR, 'light.pdf'),

        # Templates
        # TODO: Soon to be obsolete data, or add check before loading?
        **{
            f"templates/{template.rsplit('.', 1)[0]}":
                TreatAsData(os.path.join(Defaults.DATA_DIR, 'templates', template))
            for template in os.listdir(os.path.join(Defaults.DATA_DIR, 'templates'))
        },

        # Settings
        'xml_settings': os.path.join(Defaults.XML_DIR, 'settings', 'settings_menu.xml'),
        'xml_missing_menu_template': os.path.join(Defaults.XML_DIR, 'missing_menu_template.xml'),
        **{
            f"xml_settings/{settings_sub_menu.rsplit('.', 1)[0]}":
                TreatAsData(os.path.join(Defaults.XML_DIR, 'settings', 'sub_menus', settings_sub_menu))
            for settings_sub_menu in os.listdir(os.path.join(Defaults.XML_DIR, 'settings', 'sub_menus'))
        },

    }

    LAYER = pe.AFTER_LOOP_LAYER
    icons: Dict[str, pe.Image]
    api: 'API'
    i10n: 'I10nManager'
    extension_manager: 'ExtensionManager'
    logo: pe.Text
    line_rect: pe.Rect

    def __init__(self, parent: 'GUI'):
        super().__init__(parent)
        self.api.add_hook('loader_resize_check', self.resize_check_hook)
        self.items_loaded = 0
        self.files_loaded = 0
        self.loading_feedback = 0  # Used by main menu to know if enough changes have been made since last checked
        self.loading_complete_marker = 0  # A timestamp of last sync completion
        self.files_to_load: Union[int, None] = None
        self.last_progress = 0
        self.current_progress = 0
        self.initialized = False
        self.to_load = len(self.TO_LOAD)
        parent.loader = self
        # noinspection PyBroadException
        try:
            with open(os.path.join(Defaults.DATA_DIR, 'messages.txt'), 'r') as f:
                messages = f.readlines()
                self.motivational_message = random.choice(messages)
        except:
            self.motivational_message = ""
        finally:
            self.motivational_message = self.motivational_message.replace('%APP_NAME%', APP_NAME)
        self.motivational_text = None
        self.initialize_logo_and_line()

    def start_syncing(self):
        threading.Thread(target=self.get_documents, daemon=True).start()

    def load_one(self, key: str, item: AcceptedLoadTypes = None):
        if not item:
            item = self.TO_LOAD[key]
        if isinstance(item, ReusedIcon):
            self.icons[key] = self.icons[item.key].copy()
            self.icons[key].resize(tuple(v * item.scale for v in self.icons[key].size))
        elif isinstance(item, ResizedIcon):
            self.load_image(key, item.item, item.scale)
        elif isinstance(item, InvertedIcon):
            self.load_one(key, item.item)
            key_inverted = f'{key}_inverted'
            invert_icon(self, key, key_inverted)
        elif isinstance(item, TreatAsData):
            self.load_data(key, item.item)
        elif not isinstance(item, str):
            return
        elif item.endswith('.svg'):
            self.load_svg(key, item)
        elif item.endswith('.png'):
            self.load_image(key, item)
        else:
            self.load_data(key, item)

    def _load(self):
        for key, item in self.TO_LOAD.items():
            self.load_one(key, item)
            self.items_loaded += 1

        # Load additional languages
        for lang_file in os.listdir(Defaults.TRANSLATIONS_DIR):
            if not lang_file.endswith('.json'):
                continue
            lang = lang_file[:-5]
            self.i10n.load_translations(lang)

        # Begin loading extensions
        threading.Thread(target=self.load_extensions, daemon=True).start()

        # Wait for extensions to load
        while not (
                self.extension_manager.gathered_extensions and
                self.extension_manager.extensions_loaded == self.extension_manager.extension_count
        ):
            pass

        # Load extension data
        self.to_load += len(self.extension_manager.extra_items)
        for key, item in self.extension_manager.extra_items.items():
            if item.endswith('.svg'):
                self.load_image(key, item, 0.5)
            elif item.endswith('.png'):
                self.load_image(key, item)
            else:
                self.load_data(key, item)
            self.items_loaded += 1

    def load(self):
        try:
            self._load()
        except:
            print_exc()

    def load_extensions(self):
        try:
            self.extension_manager.load()
        except AttributeError:
            pass
        except:
            print_exc()

    def get_documents(self):
        def progress(loaded, to_load):
            self.files_loaded = loaded
            self.files_to_load = to_load

        self.loading_feedback = 0
        self.loading_complete_marker = 0
        self.api.get_documents(progress)
        if self.config.last_root != self.api.last_root:
            self.config.last_root = self.api.last_root
            self.parent_context.dirty_config = True
        self.files_to_load = None
        if not self.current_progress:
            self.current_progress = 1
        self.api.spread_event(NewDocuments())

        self.loading_complete_marker = time.time()

    def load_image(self, key, file, multiplier: float = 1):
        self.icons[key] = pe.Image(file)
        self.icons[key].resize(tuple(self.ratios.pixel(v * multiplier) for v in self.icons[key].size))

    def load_svg(self, key, file):
        # SVGs are 40px, but we use 1000px height, so they are 23px
        # 23 / 40 = 0.575
        # but, I find 0.5 to better match
        self.load_image(key, file, 0.5)

    def load_data(self, key, file):
        with open(file, 'rb') as f:
            self.data[key] = f.read()

    @property
    def extensions_loaded(self):
        try:
            return self.extension_manager.extensions_loaded
        except AttributeError:
            return 0

    @property
    def extension_count(self):
        try:
            return self.extension_manager.extension_count
        except AttributeError:
            return 0

    def progress(self):
        if self.files_to_load is None and self.config.wait_for_everything_to_load and not self.current_progress:
            # Before we know the file count, just return 0 progress
            return 0
        try:
            base_division_a = (
                    self.extensions_loaded +
                    self.items_loaded
            )
            base_division_b = (
                    self.extension_count +
                    self.to_load
            )
            if not self.config.wait_for_everything_to_load:
                self.current_progress = base_division_a / base_division_b
            else:
                self.current_progress = (
                                                base_division_a +
                                                self.files_loaded
                                        ) / (
                                                base_division_b +
                                                (self.files_to_load or self.files_loaded)
                                        )
        except ZeroDivisionError:
            self.current_progress = 0
        self.last_progress = self.last_progress + (self.current_progress - self.last_progress) / (self.FPS * .1)
        if not self.config.wait_for_everything_to_load and self.current_progress == 1 and self.last_progress < 0.9:
            self.last_progress = 0.9
        return self.last_progress

    def loop(self):
        self.logo.display()
        self.motivational_text.display()
        progress = self.progress()
        if progress:
            pe.draw.rect(Defaults.LINE_GRAY, self.line_rect, self.ratios.loader_loading_bar_thickness,
                         edge_rounding=self.ratios.loader_loading_bar_rounding)
            progress_rect = self.line_rect.copy()
            progress_rect.width *= progress
            pe.draw.rect(Defaults.SELECTED, progress_rect, 0, edge_rounding=self.ratios.loader_loading_bar_rounding)
            if self.config.debug:
                if self.extension_count:
                    extensions_rect = self.line_rect.copy()
                    extensions_rect.width *= (
                            self.extensions_loaded / self.extension_count)
                    pe.draw.rect(Defaults.TEXT_ERROR_COLOR[0], extensions_rect,
                                 self.ratios.loader_loading_bar_thickness * 3,
                                 edge_rounding=self.ratios.loader_loading_bar_rounding)
                icons_rect = self.line_rect.copy()
                icons_rect.width *= (self.items_loaded / len(self.TO_LOAD))
                pe.draw.rect(Defaults.LINE_GRAY_LIGHT, icons_rect, self.ratios.loader_loading_bar_thickness * 2,
                             edge_rounding=self.ratios.loader_loading_bar_rounding)

    def post_loop(self):
        if self.current_progress == 1 and self.last_progress >= .98:
            self.add_screen(MainMenu(self.parent_context))  # Open the main menu
            self.api.connect_to_notifications()  # Connect to the reMarkable websocket
            self.api.add_hook('loader', self.loader_hook)  # Add api event hook for loader
            try:
                self.extension_manager.extra_items.clear()  # Allow extensions to finally loop
            except AttributeError:
                pass

    def loader_hook(self, event):
        if isinstance(event, SyncCompleted):
            self.start_syncing()

    def pre_loop(self):
        if not self.initialized:
            threading.Thread(target=self.load, daemon=True).start()
            self.start_syncing()
            self.initialized = True

    def initialize_logo_and_line(self):
        self.motivational_text = pe.Text(
            self.motivational_message,
            Defaults.CUSTOM_FONT,
            self.ratios.loader_motivational_text_size,
            colors=Defaults.TEXT_COLOR
        )
        super().initialize_logo_and_line()
        self.motivational_text.color = Defaults.TEXT_COLOR
        self.motivational_text.rect.midtop = self.line_rect.midbottom
        self.motivational_text.rect.top += self.ratios.loader_loading_bar_padding
