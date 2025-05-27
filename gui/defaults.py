import __main__
import locale
import os.path
from pprint import pformat
from typing import TYPE_CHECKING

import pygameextra as pe
from colorama import Fore
from rm_lines.inker.writing_tools import remarkable_palette

from gui import USER_DATA_DIR


def get_asset_path():
    # Check if we are running in a Nuitka bundle
    if '__compiled__' in globals():
        if pe.settings.config.debug:
            print("Running as a Nuitka bundle")
        base_asset_dir = os.path.dirname(__main__.__file__)
        # noinspection PyUnresolvedReferences
        script_dir = __compiled__.containing_dir
    else:
        if pe.settings.config.debug:
            print("Running in development")
        pe.settings.indev = True
        base_asset_dir = os.path.abspath(".")
        script_dir = os.path.abspath(os.path.dirname(__main__.__file__))

    if pe.settings.config.debug:
        print(f"Base asset dir: {base_asset_dir}")
        print(f"Script dir: {script_dir}")
    return base_asset_dir, script_dir


class DefaultsMeta(type):
    def __setattr__(self, key, value):
        if key == 'BACKGROUND':
            remarkable_palette[2] = list(value[:3])
        if key == 'SELECTED':
            remarkable_palette[0] = list(value[:3])
        if key == 'LINE_GRAY':
            remarkable_palette[1] = list(value[:3])
            remarkable_palette[8] = remarkable_palette[1]
        super().__setattr__(key, value)


class Defaults(metaclass=DefaultsMeta):
    # Figure out where Moss is located and check if it is installed
    BASE_ASSET_DIR, SCRIPT_DIR = get_asset_path()
    ASSET_DIR = os.path.join(BASE_ASSET_DIR, 'assets')
    INSTALLED = os.path.exists(os.path.join(BASE_ASSET_DIR, 'installed'))

    # Get asset directories
    XML_DIR = os.path.join(ASSET_DIR, 'xml')
    ICON_DIR = os.path.join(ASSET_DIR, 'icons')
    IMAGES_DIR = os.path.join(ASSET_DIR, 'images')
    DATA_DIR = os.path.join(ASSET_DIR, 'data')
    FONT_DIR = os.path.join(ASSET_DIR, 'fonts')
    TRANSLATIONS_DIR = os.path.join(ASSET_DIR, 'translations')

    if INSTALLED:
        SCRIPT_DIR = USER_DATA_DIR

    # Get API storage file paths
    TOKEN_FILE_PATH = os.path.join(SCRIPT_DIR, 'token')
    CONFIG_FILE_PATH = pe.settings.config_file_path  # The GUI handles the path for this
    SYNC_FILE_PATH = os.path.join(SCRIPT_DIR, 'sync')
    THUMB_FILE_PATH = os.path.join(SCRIPT_DIR, 'thumbnails')
    LOG_FILE = os.path.join(SCRIPT_DIR, 'moss.log')

    # Get user data directories
    CONTENT_DIR = os.path.join(SCRIPT_DIR, 'content')
    TEMP_DIR = os.path.join(CONTENT_DIR, '.temporary')
    EXTENSIONS_DIR = os.path.join(CONTENT_DIR, 'extensions')
    OPTIONS_DIR = os.path.join(CONTENT_DIR, 'options')

    # Get font paths
    CUSTOM_FONT = None
    CUSTOM_FONT_BOLD = None
    MONO_FONT = None
    ROBOTO_REGULAR_FONT = None
    ROBOTO_MEDIUM_FONT = None
    TITLE_FONT = None
    SUBTITLE_FONT = None

    # Main fonts
    PATH_FONT = None
    FOLDER_TITLE_FONT = None
    DOCUMENT_TITLE_FONT = None
    DOCUMENT_SUBTITLE_FONT = None
    DOCUMENT_ERROR_FONT = None
    INSTALLER_FONT = None
    BUTTON_FONT = None

    # Unique fonts
    LOGO_FONT = None
    MAIN_MENU_FONT = None
    MAIN_MENU_BAR_FONT = None
    MAIN_MENU_PROGRESS_FONT = None
    CODE_FONT = None
    DEBUG_FONT = None
    GUIDES_FONT = None

    # Settings fonts
    XML_TITLE_FONT = None
    XML_SUBTITLE_FONT = None
    XML_TEXT_FONT = None
    XML_SUBTEXT_FONT = None
    XML_OPTION_FONT = None

    # The main colors
    BACKGROUND = pe.colors.white
    SELECTED = (10, 10, 10)

    # Main text colors
    TEXT_COLOR = (pe.colors.black, BACKGROUND)
    TEXT_COLOR_T = (TEXT_COLOR[0], None)
    TEXT_COLOR_H = (BACKGROUND, None)
    TEXT_ERROR_COLOR = (pe.colors.red, None)
    TEXT_COLOR_CODE = (pe.colors.darkaqua, None)
    TEXT_COLOR_LINK = (pe.colors.darkblue, None)

    # Unique text colors
    DOCUMENT_TITLE_COLOR = ((20, 20, 20), BACKGROUND)
    DOCUMENT_TITLE_COLOR_INVERTED = ((235, 235, 235), SELECTED)
    DOCUMENT_SUBTITLE_COLOR = ((100, 100, 100), BACKGROUND)
    CODE_COLOR = ((120, 120, 120), None)

    # UI colors
    OUTLINE_COLOR = pe.colors.black
    LINE_GRAY = (88, 88, 88)
    LINE_GRAY_LIGHT = (167, 167, 167)
    DOCUMENT_GRAY = (184, 184, 184)
    DOCUMENT_BACKGROUND = BACKGROUND
    BUTTON_ACTIVE_COLOR_INVERTED = (255, 255, 255, 50)
    BUTTON_DISABLED_COLOR = (0, 0, 0, 100)
    BUTTON_DISABLED_LIGHT_COLOR = (*BACKGROUND, 150)
    BUTTON_ACTIVE_COLOR = (0, 0, 0, 25)

    # General colors
    RED = (255, 50, 50)
    ORANGE = (255, 155, 0)
    TRANSPARENT_COLOR = (0, 0, 0, 0)

    # Define a thumbnail preview size for documents
    PREVIEW_SIZE = (312, 416)

    # Key bindings
    NAVIGATION_KEYS = {
        "next": [pe.K_RIGHT],
        "previous": [pe.K_LEFT],
    }

    # Get the icon paths
    APP_ICON = os.path.join(ICON_DIR, 'moss.png')
    ICO_APP_ICON = os.path.join(ICON_DIR, 'moss.ico')

    # File select data
    RM_TYPES_RAW = ['*.pdf', '*.epub']
    RM_TYPES = {
        "PDF & EPUB": RM_TYPES_RAW,
    }
    IMPORT_TYPES = {  # All import
        "Moss doc format": '*.mossdoc',
        "RM doc format": '*.rmdoc',
        **RM_TYPES
    }
    EXPORT_TYPES = {  # Export
        "Moss doc type": '*.mossdoc',
        "RM doc type": '*.rmdoc',
        "Render to PDF": '*.pdf'
    }
    ALL_TYPES = [  # Debug import
        *RM_TYPES_RAW, '*.content', '*.metadata', '*.json'
    ]

    # TODO: Explain this for multisync operations not yet added
    PROGRESS_ORDER = [
        "total",
    ]
    PROGRESS_COLOR = {
        "total": pe.colors.white,  # This should never get used!!!
    }

    @classmethod
    def init(cls, config):
        # TODO: Get system default local, and use system fonts by default
        if config.language == "zh":
            zh_font = os.path.join(cls.FONT_DIR, 'NotoSansSC-VariableFont_wght.ttf')
            cls.CUSTOM_FONT = zh_font
            cls.CUSTOM_FONT_BOLD = zh_font
            cls.MONO_FONT = zh_font
            cls.ROBOTO_REGULAR_FONT = zh_font
            cls.ROBOTO_MEDIUM_FONT = zh_font
            cls.TITLE_FONT = zh_font
            cls.SUBTITLE_FONT = zh_font
        else:
            if config.language == "en":
                cls.CUSTOM_FONT = os.path.join(cls.FONT_DIR, 'Imperator.ttf')
                cls.CUSTOM_FONT_BOLD = os.path.join(cls.FONT_DIR, 'Imperator Bold.ttf')
            else:
                cls.CUSTOM_FONT = os.path.join(cls.FONT_DIR, 'Roboto-Regular.ttf')
                cls.CUSTOM_FONT_BOLD = os.path.join(cls.FONT_DIR, 'Roboto-Medium.ttf')
            cls.MONO_FONT = os.path.join(cls.FONT_DIR, 'JetBrainsMono-Bold.ttf')
            cls.ROBOTO_REGULAR_FONT = os.path.join(cls.FONT_DIR, 'Roboto-Regular.ttf')
            cls.ROBOTO_MEDIUM_FONT = os.path.join(cls.FONT_DIR, 'Roboto-Medium.ttf')
            cls.TITLE_FONT = os.path.join(cls.FONT_DIR, 'PTM75F.ttf')
            cls.SUBTITLE_FONT = os.path.join(cls.FONT_DIR, 'PTM55F.ttf')

        # Main fonts
        cls.PATH_FONT = cls.ROBOTO_REGULAR_FONT
        cls.FOLDER_TITLE_FONT = cls.TITLE_FONT
        cls.DOCUMENT_TITLE_FONT = cls.TITLE_FONT
        cls.DOCUMENT_SUBTITLE_FONT = cls.SUBTITLE_FONT
        cls.DOCUMENT_ERROR_FONT = cls.ROBOTO_MEDIUM_FONT
        cls.INSTALLER_FONT = cls.ROBOTO_REGULAR_FONT
        cls.BUTTON_FONT = cls.ROBOTO_REGULAR_FONT

        # Unique fonts
        cls.LOGO_FONT = cls.CUSTOM_FONT_BOLD
        cls.MAIN_MENU_FONT = cls.CUSTOM_FONT_BOLD
        cls.MAIN_MENU_BAR_FONT = cls.ROBOTO_MEDIUM_FONT
        cls.MAIN_MENU_PROGRESS_FONT = cls.MONO_FONT
        cls.CODE_FONT = cls.MONO_FONT
        cls.DEBUG_FONT = cls.MONO_FONT
        cls.GUIDES_FONT = cls.ROBOTO_REGULAR_FONT

        # Settings fonts
        cls.XML_TITLE_FONT = cls.ROBOTO_MEDIUM_FONT
        cls.XML_SUBTITLE_FONT = cls.ROBOTO_MEDIUM_FONT
        cls.XML_TEXT_FONT = cls.TITLE_FONT
        cls.XML_SUBTEXT_FONT = cls.MONO_FONT
        cls.XML_OPTION_FONT = cls.TITLE_FONT

        # If in debug mode just display the defaults in the terminal for easy reference
        if pe.settings.config.debug:
            print(f"\n{Fore.MAGENTA}Defaults:{Fore.RESET}")
            for key, value in Defaults.__dict__.items():
                if not key.startswith("__"):
                    print(f"{Fore.YELLOW}{key}: {Fore.CYAN}{pformat(value)}{Fore.RESET}")
            print(f"{Fore.MAGENTA}^ Defaults ^{Fore.RESET}\n")
