import __main__
import os.path

from gui import USER_DATA_DIR
from rm_lines.inker.writing_tools import remarkable_palette

try:
    from cefpython3 import cefpython as cef
except Exception:
    cef = None
import pygameextra as pe


def get_asset_path():
    # Check if we are running in a Nuitka bundle
    if '__compiled__' in globals():
        if pe.settings.config.debug:
            print("Running as a Nuitka bundle")
        base_asset_dir = os.path.dirname(__main__.__file__)
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
    BASE_ASSET_DIR, SCRIPT_DIR = get_asset_path()
    ASSET_DIR = os.path.join(BASE_ASSET_DIR, 'assets')
    INSTALLED = os.path.exists(os.path.join(BASE_ASSET_DIR, 'installed'))

    XML_DIR = os.path.join(ASSET_DIR, 'xml')
    ICON_DIR = os.path.join(ASSET_DIR, 'icons')
    IMAGES_DIR = os.path.join(ASSET_DIR, 'images')
    DATA_DIR = os.path.join(ASSET_DIR, 'data')
    FONT_DIR = os.path.join(ASSET_DIR, 'fonts')

    if INSTALLED:
        SCRIPT_DIR = USER_DATA_DIR
    TOKEN_FILE_PATH = os.path.join(SCRIPT_DIR, 'token')
    CONFIG_FILE_PATH = pe.settings.config_file_path  # The GUI handles the path for this
    SYNC_FILE_PATH = os.path.join(SCRIPT_DIR, 'sync')
    THUMB_FILE_PATH = os.path.join(SCRIPT_DIR, 'thumbnails')
    LOG_FILE = os.path.join(SCRIPT_DIR, 'moss.log')

    CONTENT_DIR = os.path.join(SCRIPT_DIR, 'content')
    TEMP_DIR = os.path.join(CONTENT_DIR, '.temporary')
    EXTENSIONS_DIR = os.path.join(CONTENT_DIR, 'extensions')
    OPTIONS_DIR = os.path.join(CONTENT_DIR, 'options')

    CUSTOM_FONT = os.path.join(FONT_DIR, 'Imperator.ttf')
    CUSTOM_FONT_BOLD = os.path.join(FONT_DIR, 'Imperator Bold.ttf')
    MONO_FONT = os.path.join(FONT_DIR, 'JetBrainsMono-Bold.ttf')
    ROBOTO_REGULAR_FONT = os.path.join(FONT_DIR, 'Roboto-Regular.ttf')
    ROBOTO_MEDIUM_FONT = os.path.join(FONT_DIR, 'Roboto-Medium.ttf')
    TITLE_FONT = os.path.join(FONT_DIR, 'PTM75F.ttf')

    PATH_FONT = ROBOTO_REGULAR_FONT
    FOLDER_TITLE_FONT = TITLE_FONT
    DOCUMENT_TITLE_FONT = TITLE_FONT
    DOCUMENT_ERROR_FONT = ROBOTO_MEDIUM_FONT
    INSTALLER_FONT = ROBOTO_REGULAR_FONT
    BUTTON_FONT = ROBOTO_REGULAR_FONT

    LOGO_FONT = CUSTOM_FONT_BOLD
    MAIN_MENU_FONT = CUSTOM_FONT_BOLD
    MAIN_MENU_BAR_FONT = ROBOTO_MEDIUM_FONT
    MAIN_MENU_PROGRESS_FONT = MONO_FONT
    CODE_FONT = MONO_FONT
    DEBUG_FONT = MONO_FONT
    GUIDES_FONT = ROBOTO_REGULAR_FONT

    XML_TITLE_FONT = ROBOTO_MEDIUM_FONT
    XML_SUBTITLE_FONT = ROBOTO_REGULAR_FONT
    XML_TEXT_FONT = TITLE_FONT
    XML_SUBTEXT_FONT = MONO_FONT
    XML_OPTION_FONT = MONO_FONT
    XML_FULL_TEXT_FONT = TITLE_FONT

    BACKGROUND = pe.colors.white

    TEXT_COLOR = (pe.colors.black, BACKGROUND)
    SELECTED = (10, 10, 10)
    TEXT_ERROR_COLOR = (pe.colors.red, None)
    TEXT_COLOR_CODE = (pe.colors.darkaqua, None)
    TEXT_COLOR_LINK = (pe.colors.darkblue, None)
    DOCUMENT_TITLE_COLOR = ((20, 20, 20), BACKGROUND)
    DOCUMENT_TITLE_COLOR_INVERTED = ((235, 235, 235), SELECTED)
    DOCUMENT_SUBTITLE_COLOR = ((100, 100, 100), BACKGROUND)
    TEXT_COLOR_T = (TEXT_COLOR[0], None)
    TEXT_COLOR_H = (BACKGROUND, None)
    CODE_COLOR = ((120, 120, 120), None)
    LINE_GRAY = (88, 88, 88)
    LINE_GRAY_LIGHT = (167, 167, 167)
    DOCUMENT_GRAY = (184, 184, 184)
    DOCUMENT_BACKGROUND = BACKGROUND
    TRANSPARENT_COLOR = (0, 0, 0, 0)
    BUTTON_ACTIVE_COLOR = (0, 0, 0, 25)
    BUTTON_ACTIVE_COLOR_INVERTED = (255, 255, 255, 50)
    BUTTON_DISABLED_COLOR = (0, 0, 0, 100)
    BUTTON_DISABLED_LIGHT_COLOR = (*BACKGROUND, 150)

    PREVIEW_SIZE = (312, 416)

    # Colors
    OUTLINE_COLOR = pe.colors.black
    RED = (255, 50, 50)

    # Key bindings
    NAVIGATION_KEYS = {
        "next": [pe.K_RIGHT],
        "previous": [pe.K_LEFT],
    }

    APP_ICON = os.path.join(ICON_DIR, 'moss.png')
    ICO_APP_ICON = os.path.join(ICON_DIR, 'moss.ico')

    IMPORT_TYPES = ['.rm', '.pdf', '.epub']
    ALL_TYPES = [*IMPORT_TYPES, '.content', '.metadata', '.json']

    PROGRESS_ORDER = [
        "total",
    ]
    PROGRESS_COLOR = {
        "total": pe.colors.white,  # This should never get used!!!
    }


if pe.settings.config.debug:
    print("\nDefaults:")
    for key, value in Defaults.__dict__.items():
        if not key.startswith("__"):
            print(f"{key}: {value}")
    print("^ Defaults ^\n")
