import hashlib
import json
import os
from functools import lru_cache
from typing import TYPE_CHECKING, List, Tuple, Optional

import pygameextra as pe
import pyperclip

from gui.cloud_action_helper import import_notebook_pages_to_cloud
from gui.defaults import Defaults
from gui.extensions.host_functions import ACTION_APPEND
from gui.extensions.shared_types import rect_from_pe_rect
from gui.file_prompts import notebook_prompt, import_debug
from gui.pp_helpers import ContextMenu, DocumentDebugPopup
from gui.preview_handler import PreviewHandler
from gui.screens.name_field_screen import NameFieldScreen
from gui.screens.viewer import DocumentViewer
from gui.i18n import t, i18n
from rm_api import make_hash
from rm_api.models import Document, DocumentCollection, Content, Metadata
from rm_api.notifications.models import DocumentSyncProgress
from rm_api.storage.common import FileHandle

if TYPE_CHECKING:
    from gui.extensions.extension_manager import ExtensionManager


class ImportContextMenu(ContextMenu):
    BUTTONS = (
        {
            "text": t("menu.import.pdf_epub"),
            "icon": "import",
            "action": 'import_action'
        },
        {
            "text": t("menu.import.notebook"),
            "icon": "notebook_add",
            "action": 'notebook_import'
        }
    )

    def import_action(self):
        self.main_menu.bar.import_action()
        self.close()

    def _notebook_import(self, title: str):
        notebook_prompt(lambda file_paths: import_notebook_pages_to_cloud(self.main_menu, file_paths, title))

    def notebook_import(self):
        NameFieldScreen(self.main_menu.parent_context, "Import Notebook", "", self._notebook_import, None, )
        self.close()


class DeleteContextMenu(ContextMenu):
    BUTTONS = (
        {
            "text": t("menu.delete.confirm"),
            "icon": "trashcan_delete",
            "action": 'delete_confirm'
        },
    )
    INVERT = True

    def delete_confirm(self):
        self.main_menu.bar.delete_confirm()
        self.close()


class DebugContextMenu(ContextMenu):
    DEBUG_FOLDER = 'debug'
    DEBUG_PREVIEW = 'debug_preview'
    DEBUG_PREVIEW_PAGE_INDEX = 'debug'
    CLOSE_AFTER_ACTION = True
    PREVIEW_COLORS = (
        (255, 255, 255),
        (200, 200, 200),
        (150, 150, 150),
        (100, 100, 100),
        (50, 50, 50),
        (20, 20, 20),
        (0, 0, 0),
        (255, 0, 0),
        (200, 0, 0),
        (150, 0, 0),
        (100, 0, 0),
        (50, 0, 0),
        (20, 0, 0),
        (0, 255, 0),
        (0, 200, 0),
        (0, 150, 0),
        (0, 100, 0),
        (0, 50, 0),
        (0, 20, 0),
        (0, 0, 255),
        (0, 0, 200),
        (0, 0, 150),
        (0, 0, 100),
        (0, 0, 50),
        (0, 0, 20),
        (255, 255, 0),
        (200, 200, 0),
        (150, 150, 0),
        (100, 100, 0),
        (50, 50, 0),
        (20, 20, 0),
        (0, 255, 255),
        (0, 200, 200),
        (0, 150, 150),
        (0, 100, 100),
        (0, 50, 50),
        (0, 20, 20),
        (255, 0, 255),
        (200, 0, 200),
        (150, 0, 150),
        (100, 0, 100),
        (50, 0, 50),
        (20, 0, 20),

    )
    BUTTONS = (
        {
            "text": t("menu.debug.global"),
            "icon": "cog",
            "action": None
        },
        {
            "text": t("menu.debug.test_doc"),
            "icon": "notebook",
            "action": "test_doc_view"
        },
        {
            "text": t("menu.debug.import_dir"),
            "icon": "import",
            "action": "import_from_directory"
        },
        {
            "text": t("menu.debug.export_json"),
            "icon": "export",
            "action": "export_directory_json"
        },
        {
            "text": t("menu.debug.hot_reload"),
            "icon": "rotate",
            "action": "hot_reload"
        },
        {
            "text": t("menu.debug.copy_uuid"),
            "icon": "copy",
            "action": "copy_uuid"
        },
        {
            "text": t("menu.debug.export_stats"),
            "icon": "export",
            "action": "export_statistics"
        }
    )

    def hot_reload(self):
        self.reload()

    def test_doc_view(self):
        if not PreviewHandler.CACHED_PREVIEW.get(self.DEBUG_PREVIEW):
            surface = pe.Surface((len(self.PREVIEW_COLORS) * 10, 100))
            with surface:
                for i, color in enumerate(self.PREVIEW_COLORS):
                    pe.draw.rect(color, (i * 10, 0, 10, surface.height))
            PreviewHandler.CACHED_PREVIEW[self.DEBUG_PREVIEW] = (self.DEBUG_PREVIEW_PAGE_INDEX, pe.Image(surface))

        for document in list(self.api.documents.values()):
            if document.parent == self.DEBUG_FOLDER:
                self.api.documents.pop(document.uuid)
        for document_collection in list(self.api.document_collections.values()):
            if document_collection.parent == self.DEBUG_FOLDER:
                self.api.document_collections.pop(document_collection.uuid)

        self.apply(DocumentCollection.create(self.api, "Folder", self.DEBUG_FOLDER))
        self.apply(folder_with_tag := DocumentCollection.create(self.api, "Folder /w tag", self.DEBUG_FOLDER))
        self.apply(folder_with_star := DocumentCollection.create(self.api, "Folder /w star", self.DEBUG_FOLDER))
        self.apply(Document.new_notebook(self.api, "Normal notebook", self.DEBUG_FOLDER))
        self.apply(notebook_with_tag := Document.new_notebook(self.api, "Notebook /w tag", self.DEBUG_FOLDER))
        self.apply(notebook_with_star := Document.new_notebook(self.api, "Notebook /w star", self.DEBUG_FOLDER))
        self.apply(problematic_notebook := Document.new_notebook(self.api, "Problematic notebook", self.DEBUG_FOLDER))
        self.apply(syncing_notebook := Document.new_notebook(self.api, "Syncing notebook", self.DEBUG_FOLDER))

        # Document collections
        folder_with_tag.tags.append('Test tag')

        folder_with_star.metadata.pinned = True

        # Notebooks
        DocumentViewer.PROBLEMATIC_DOCUMENTS.add(problematic_notebook.uuid)

        notebook_with_tag.content.tags.append('Test tag')
        notebook_with_star.metadata.pinned = True

        progress = DocumentSyncProgress(syncing_notebook.uuid)
        progress.total = 2
        progress.done = 1
        self.api.spread_event(progress)

        # Set the navigation parent
        self.main_menu.navigation_parent = self.DEBUG_FOLDER

    def copy_uuid(self):
        pyperclip.copy(self.main_menu.navigation_parent)

    def apply(self, item):
        if isinstance(item, DocumentCollection):
            self.api.document_collections[item.uuid] = item
        elif isinstance(item, Document):
            self.api.documents[item.uuid] = item
            item.provision = True
            item.content.c_pages.pages[0].id = self.DEBUG_PREVIEW_PAGE_INDEX
            PreviewHandler.CACHED_PREVIEW[item.uuid] = PreviewHandler.CACHED_PREVIEW[self.DEBUG_PREVIEW]

    def import_from_directory(self):
        import_debug(self._import_from_directory)

    def _import_from_directory(self, file_paths: List[str]):
        content = None
        metadata = None
        rm_files = []
        document_uuid = None
        for file_path in file_paths:
            if file_path.endswith('.rm'):
                rm_files.append(file_path)
            elif file_path.endswith('.content.json') or file_path.endswith('.content'):
                with open(file_path, 'r') as f:
                    raw_content = json.load(f)
                    content = Content(raw_content, metadata, make_hash(raw_content), True)
            elif file_path.endswith('.metadata.json') or file_path.endswith('.metadata'):
                with open(file_path, 'r') as f:
                    raw_metadata = json.load(f)
                    metadata = Metadata(raw_metadata, make_hash(raw_metadata))
                    metadata.parent = self.main_menu.navigation_parent
                    if content:
                        content._metadata = metadata
                document_uuid = os.path.basename(file_path).split('.')[0]
        document = Document.new_notebook(
            self.api, "Import debug", None, page_count=len(rm_files), notebook_data=[
                FileHandle(file) for file in rm_files
            ], document_uuid=document_uuid, content=content, metadata=metadata
        )

        document.check()
        document.randomize_uuids()

        self.import_screen.add_item(document)

    def export_directory_json(self):
        if not self.main_menu.navigation_parent:
            return
        debug = DocumentDebugPopup(
            self.parent_context,
            self.api.document_collections[self.main_menu.navigation_parent]
        )
        debug.extract_json()

    def export_statistics(self):
        self.parent_context.extension_manager.export_statistical_data()


class CustomExtensionsMenu(ContextMenu):
    extension_manager: 'ExtensionManager'
    DEFAULT_BUTTONS = (
        {
            "text": "No extension menus",
            "icon": "puzzle",
            "action": None
        },
    )
    NO_EXTENSION_MANAGER = (
        {
            "text": "Extension manager failed to load",
            "icon": "puzzle",
            "action": None
        },
    )

    def __init__(self, parent: 'MainMenu', midright: Tuple[int, int]):
        self.previously_hashed_buttons = None
        super().__init__(parent, midright)
        self.midright = midright
        self.initialized_position = False

    def finalize_button_rect(self, buttons, width, height):
        super().finalize_button_rect(buttons, width, height)
        if not self.initialized_position:
            self.rect.midleft = self.midright
            self.left, self.top = self.rect.topleft
            self.initialized_position = True
            super().finalize_button_rect(buttons, width, height)

    @lru_cache
    def get_actions(self) -> List[Tuple[Optional[str], Optional[str], str]]:
        return [
            (
                button.get('action'),
                button.get('context_menu'),
                button['_extension']
            )
            for button in self.extension_manager.extension_buttons
        ]

    def __getattr__(self, item):
        if item.startswith(ACTION_APPEND):
            for action, context_menu, extension in self.get_actions():
                if item == action:
                    return self.extension_manager.action(action[len(ACTION_APPEND):], extension)
                if item == context_menu:
                    function = self.extension_manager.action(context_menu[len(ACTION_APPEND):], extension)
                    return lambda ideal_position: function(
                        **rect_from_pe_rect(pe.Rect(*ideal_position, 0, 0))
                    )
        return super().__getattr__(item)

    @property
    def BUTTONS(self):
        try:
            buttons = self.extension_manager.extension_buttons or self.DEFAULT_BUTTONS
        except AttributeError:
            buttons = self.NO_EXTENSION_MANAGER
        current_hash = hashlib.sha1()
        for button in buttons:
            current_hash.update(id(button).to_bytes(8, 'big'))
        if current_hash.digest() != self.previously_hashed_buttons:
            self.previously_hashed_buttons = current_hash.digest()
            self.handle_scales()
            self.get_actions.clear_cache()
        return buttons

    def handle_scales(self):
        super().handle_scales()
        self.initialized_position = False


class SideBar(ContextMenu):
    ENABLE_OUTLINE = False
    TOP_BUTTONS = 5
    BUTTONS = (
        {
            "text": t("menu.sidebar.my_files"),
            "icon": "my_files",
            "action": "set_location",
            "data": "my_files",
            "inverted_id": "my_files"
        },
        {
            "text": t("menu.sidebar.filter"),
            "icon": "filter",
            "action": None,
            "inverted_id": "filter",
            "disabled": True,
            "context_icon": "chevron_right",
        },
        {
            "text": t("menu.sidebar.favorites"),
            "icon": "star",
            "action": None,
            "inverted_id": "favorites",
            "disabled": True
        },
        {
            "text": t("menu.sidebar.tags"),
            "icon": "tag",
            "action": None,
            "inverted_id": "tags",
            "disabled": True
        },
        {
            "text": t("menu.sidebar.extensions"),
            "icon": "puzzle",
            "action": "custom_extensions_menu",
            "inverted_id": "extensions",
            "context_icon": "chevron_right"
        },
        {
            "text": t("menu.sidebar.trash"),
            "icon": "trashcan",
            "action": "set_location",
            "data": "trash",
            "inverted_id": "trash"
        },
        {
            "text": t("menu.sidebar.language"),
            "icon": "language",
            "action": "language_menu",
            "context_icon": "chevron_right"
        },  
        {
            "text": t("menu.sidebar.made_by"),
            "icon": "heart",
            "action": None
        },
        {
            "text": t("menu.sidebar.settings"),
            "icon": "cog",
            "action": "settings",
            "disabled": False
        }
    )

    extensions_button_midright: Optional[Tuple[int, int]]

    def __init__(self, context, *args, **kwargs):
        if context.config.debug:
            self.BUTTONS = (*self.BUTTONS, {
                "text": t("menu.sidebar.debug"),
                "icon": "cog",
                "action": "debug",
                "context_icon": "chevron_right",
            })
        elif context.extension_manager.extension_count == 0:
            self.BUTTONS = (
                *self.BUTTONS[:4],
                *self.BUTTONS[5:]
            )
            self.TOP_BUTTONS = 4
        super().__init__(context, *args, **kwargs)
        self.extensions_button_midright = None
        self.CONTEXT_MENU_OPEN_PADDING = self.ratios.seperator - self.ratios.line

    def pre_loop(self):
        super().pre_loop()
        pe.draw.line(Defaults.LINE_GRAY, self.rect.topright, self.rect.bottomright, self.ratios.seperator)

    def set_location(self, menu_location: str):
        self.main_menu.menu_location = menu_location
        self.close()

    def settings(self):
        from gui.screens.settings import Settings
        self.add_screen(Settings(self.parent_context))
        self.close()

    def debug(self):
        self.handle_new_context_menu(self.debug_context_menu, len(self.BUTTONS) - 1)

    def debug_context_menu(self, ideal_position):
        return DebugContextMenu(self.main_menu, ideal_position)

    def finalize_button_rect(self, buttons, width, height):
        # Rescale the buttons
        for button in buttons:
            button.area.width = self.ratios.main_menu_side_bar_width
            button.area.height = self.ratios.main_menu_top_height
            button.area.left = self.left

        # Position the top buttons
        y = self.top
        for button in buttons[:self.TOP_BUTTONS]:
            button.area.top = y
            y += button.area.height

        self.extensions_button_midright = button.area.midright

        # Position the bottom buttons
        y = self.height
        for button in reversed(buttons[self.TOP_BUTTONS:]):
            button.area.bottom = y
            y -= button.area.height
        self.rect = pe.Rect(self.left, self.top, self.ratios.main_menu_side_bar_width, self.height)

    def custom_extensions_menu(self):
        self.handle_new_context_menu(self._custom_extensions_menu, 4)

    def _custom_extensions_menu(self, ideal_position):
        return CustomExtensionsMenu(self.main_menu, self.extensions_button_midright)

    @property
    def button_margin(self):
        return self.main_menu.bar.buttons[0].area.left + self.main_menu.bar.button_padding

    @property
    def currently_inverted(self):
        return self.main_menu.menu_location
    
    def language_menu(self):
        self.handle_new_context_menu(self._language_menu, 6)  # 6 是语言按钮的索引

    def _language_menu(self, ideal_position):
        return LanguageMenu(self.main_menu, ideal_position)
    

class LanguageMenu(ContextMenu):
    BUTTONS = [
        {
            "text": lang,
            "action": "set_language",
            "icon": "language",
            "data": lang
        }
        for lang in i18n.get_available_languages()
    ]

    def __init__(self, parent: 'MainMenu', ideal_position: Tuple[int, int]):
        super().__init__(parent, ideal_position)

    def set_language(self, lang):
        if self.main_menu.parent_context.set_language(lang):
            self.close()
        else:
            print(f"Failed to set language to {lang}")

