import time
from queue import Queue
from threading import Lock
from typing import TYPE_CHECKING, Dict, List, Union

import pygameextra as pe

from gui.defaults import Defaults
from gui.events import ResizeEvent
from gui.helpers import shorten_path
from gui.rendering import draw_bottom_loading_bar, get_bottom_bar_rect, render_header
from gui.screens.main_menu.context_bars import TopBar, TopBarSelectOne, TopBarSelectMulti, TopBarSelectMove, TopBarTrash
from gui.screens.main_menu.context_menus import SideBar
from gui.screens.main_menu.main_doc_view import MainMenuDocView
from gui.sync_stages import SYNC_STAGE_TEXTS
from rm_api.models import Document
from rm_api.notifications.models import SyncRefresh, FileSyncProgress, NewDocuments, DocumentSyncProgress

if TYPE_CHECKING:
    from gui import GUI
    from gui.aspect_ratio import Ratios
    from rm_api import API
    from gui.screens.loader import Loader


class MainMenu(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER

    # definitions from GUI
    api: 'API'
    parent_context: 'GUI'
    icons: Dict[str, pe.Image]
    ratios: 'Ratios'

    SORTING_FUNCTIONS = {
        'last_modified': lambda item: item.metadata.last_modified,
    }

    HEADER_TEXTS = {
        'my_files': "My files",
        'trash': "Trash",
        'favorites': "Favorites",
        'tags': "Tags",
        'notebooks': "Notebooks",
        'pdfs': "PDFs",
        'ebooks': "Ebooks",
    }

    SMALL_HEADER_TEXTS = {
        f'rm_api_stage_{stage}': stage_text
        for stage, stage_text in SYNC_STAGE_TEXTS.items()
    }

    MAINTAIN_TEXT_KEYS = (
        *HEADER_TEXTS.keys(),
        *SMALL_HEADER_TEXTS.keys(),
        'debug'
    )

    LOCATION_PARENT_MAPPING = {
        'my_files': None,
        'trash': 'trash',
    }

    file_sync_operation: Union[None, FileSyncProgress]

    resync_icon: pe.Image
    resync_icon_inverted: pe.Image
    resync_rect: pe.Rect
    hamburger_icon: pe.Image
    hamburger_rect: pe.Rect
    doc_view: MainMenuDocView

    def __init__(self, parent: 'GUI'):
        self.document_collections = {}
        self.documents = {}
        self.texts: Dict[str, pe.Text] = {}
        self.path_queue = Queue()
        self.call_lock = Lock()
        self.file_sync_operation = None
        self.previous_t = 0
        self.rotate_angle = 0
        # TODO: Maybe load from settings
        self.current_sorting_mode = 'last_modified'
        # reversed is equivalent to descending
        # obviously, non-reversed is ascending
        self.current_sorting_reverse = True
        self.move_mode = False
        super().__init__(parent)
        parent.main_menu = self  # Assign myself as the main menu
        # Update the location properly by setting it
        self.menu_location = self.menu_location

        # Initialize the top bars
        self._bar = TopBar(self)
        self._bar_one = TopBarSelectOne(self)
        self._bar_multi = TopBarSelectMulti(self)
        self._bar_move = TopBarSelectMove(self)
        self._bar_trash = TopBarTrash(self)

        if 'screenshot' in self.icons:
            self.icons['screenshot'].set_alpha(100)

        # Header texts
        for key, text in self.HEADER_TEXTS.items():
            self.texts[key] = pe.Text(text, Defaults.MAIN_MENU_FONT, self.ratios.main_menu_my_files_size,
                                      (0, 0), Defaults.TEXT_COLOR)
            self.texts[key].rect.topleft = (
                self.ratios.main_menu_x_padding, self.ratios.main_menu_top_height + self.ratios.main_menu_top_padding)
        for key, text in self.SMALL_HEADER_TEXTS.items():
            self.make_small_header_text(key, text)

        self.context_menus = {}

        # Document debug button text
        self.texts['debug'] = pe.Text(
            'DEBUG',
            Defaults.DEBUG_FONT,
            self.ratios.small_debug_text_size,
            colors=(Defaults.DOCUMENT_BACKGROUND, None)
        )

        self.doc_view = MainMenuDocView(parent)
        self.side_bar = SideBar(self, (0, 0))
        self.side_bar.is_closed = True
        self.get_items()

        self.document_sync_operations: Dict[str, DocumentSyncProgress] = {}

        self.resync_icon = self.icons['rotate']
        self.resync_icon_inverted = self.icons['rotate_inverted']
        self.rect_calculations()
        parent.api.add_hook("main_menu_cache_invalidator", self.api_event_hook)

    def make_small_header_text(self, key, text):
        self.texts[key] = pe.Text(text, Defaults.MAIN_MENU_BAR_FONT, self.ratios.main_menu_bar_size,
                                  (0, 0), Defaults.TEXT_COLOR_H)

    @property
    def bar(self):
        selected_items = len(self.doc_view.selected_documents) + len(self.doc_view.selected_document_collections)
        if selected_items > 0 and self.move_mode:
            return self._bar_move
        elif self.move_mode:
            self.move_mode = False
        elif selected_items == 1:
            return self._bar_one
        elif selected_items > 1:
            return self._bar_multi
        if self.menu_location == 'trash':
            return self._bar_trash
        return self._bar

    @property
    def navigation_parent(self):
        return self._navigation_parent

    @navigation_parent.setter
    def navigation_parent(self, uuid):
        self._navigation_parent = uuid
        if all((
                self.menu_location == 'my_files',
                self.config.save_last_opened_folder,
                self.config.last_opened_folder != uuid
        )):
            self.config.last_opened_folder = uuid
            self.parent_context.dirty_config = True
        self.get_items()
        self.quick_refresh()

    @property
    def view_mode(self):
        return self.config.main_menu_view_mode

    @view_mode.setter
    def view_mode(self, value):
        self.config.main_menu_view_mode = value
        self.parent_context.dirty_config = True

    @property
    def menu_location(self):
        return self.config.main_menu_menu_location

    @menu_location.setter
    def menu_location(self, value):
        if self.config.main_menu_menu_location != value:
            self.config.main_menu_menu_location = value
            self.parent_context.dirty_config = True
        if value == 'trash':
            self.navigation_parent = 'trash'
        elif value == 'my_files':
            self.navigation_parent = self.config.last_opened_folder

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.bar()

    def get_items(self):
        # Copy the document collections and documents incase they change
        document_collections = dict(self.api.document_collections)
        documents = dict(self.api.documents)

        # Filtering the document collections and documents with the current parent
        self.document_collections = {
            key: item for key, item in
            document_collections.items()
            if item.parent == self.navigation_parent
        }
        self.documents = {
            key: item for key, item in
            documents.items()
            if item.parent == self.navigation_parent
        }

        # Preparing the path queue and the path texts
        self.path_queue.queue.clear()
        if self.navigation_parent is not None:
            parent = self.navigation_parent
            while parent is not None:
                self.path_queue.put(parent)
                text_key = f'path_{parent}'

                # Render the path text
                if self.texts.get(text_key) is None:
                    try:
                        text = shorten_path(document_collections[parent].metadata.visible_name)
                    except:
                        del self.path_queue.queue[-1]
                        parent = None
                        continue
                    self.texts[text_key] = pe.Text(
                        text,
                        Defaults.PATH_FONT,
                        self.ratios.main_menu_path_size,
                        (0, 0), Defaults.TEXT_COLOR
                    )
                try:
                    parent = document_collections[parent].parent
                except KeyError:
                    parent = None
        self.doc_view.handle_texts()

    def pre_loop(self):
        if 'screenshot' in self.icons:
            self.icons['screenshot'].display()
        if not self.side_bar.is_closed:
            self.side_bar()

    def set_parent(self, uuid=None):  # This function is from before navigation_parent was a property
        self.navigation_parent = uuid or self.LOCATION_PARENT_MAPPING[self.menu_location]

    @staticmethod
    def get_sorted_document_collections(old_document_collections) -> sorted:
        return sorted(old_document_collections, key=lambda item: item.metadata.visible_name)

    def get_sorted_documents(self, original_documents_list: List['Document']) -> Union[List['Document'], reversed]:
        documents = sorted(original_documents_list, key=self.SORTING_FUNCTIONS[self.current_sorting_mode])
        if self.current_sorting_reverse:
            return reversed(documents)
        return documents

    def refresh(self):
        if self.api.sync_notifiers < 1:
            self.api.spread_event(SyncRefresh())

    def hamburger(self):
        self.side_bar.is_closed = False

    def loop(self):
        pe.draw.line(Defaults.LINE_GRAY, (0, self.ratios.main_menu_top_height),
                     (self.width, self.ratios.main_menu_top_height), self.ratios.line)

        render_header(self.parent_context, self.texts, self.set_parent, self.path_queue)

        self.doc_view()

    @property
    def loading(self):
        loader: 'Loader' = self.parent_context.screens[0]
        return loader.files_to_load is not None or \
            loader.loading_feedback or \
            self.file_sync_operation and not self.file_sync_operation.finished

    def post_loop(self):
        # Handle extra context menus
        context_menus_to_remove = []
        for key, context_menu in self.context_menus.items():
            context_menu()
            if context_menu.is_closed:
                context_menus_to_remove.append(key)
        for key in context_menus_to_remove:
            del self.context_menus[key]

        # Draw progress bar for file sync operations
        if self.file_sync_operation and not self.file_sync_operation.finished:
            self.previous_t = draw_bottom_loading_bar(
                self.parent_context, self.file_sync_operation.done,
                self.file_sync_operation.total, self.previous_t,
                stage=self.file_sync_operation.stage
            )
            self.update_sync_angle()
            return

        # Draw sync operation from loader
        loader: 'Loader' = self.parent_context.screens[0]  # The loader is always the first screen
        if loader.files_to_load is not None:
            self.previous_t = draw_bottom_loading_bar(self.parent_context, loader.files_loaded, loader.files_to_load,
                                                      self.previous_t)
            # Update the data if the loader has loaded more files
            if loader.loading_feedback + 3 < loader.files_loaded:  # Update menu every 3 files
                self.get_items()
                loader.loading_feedback = loader.files_loaded
            self.update_sync_angle()
        elif loader.loading_feedback:
            self.get_items()
            loader.loading_feedback = 0
            self.previous_t = 0
            draw_bottom_loading_bar(self.parent_context, 1, 1, finish=True)
        elif time.time() - loader.loading_complete_marker < 1:  # For 1 second after loading is complete
            draw_bottom_loading_bar(self.parent_context, 1, 1, finish=True)

    def _critical_event_hook(self, event):
        if isinstance(event, ResizeEvent):
            self.invalidate_cache()
            self._bar.handle_scales()
            self._bar_one.handle_scales()
            self._bar_multi.handle_scales()
            self._bar_move.handle_scales()
            self._bar_trash.handle_scales()
            self.side_bar.handle_scales()
            self.doc_view.update_size()
        elif isinstance(event, NewDocuments):
            self.get_items()

    def _non_critical_event_hook(self, event):
        if isinstance(event, FileSyncProgress):
            self.file_sync_operation = event
        elif isinstance(event, DocumentSyncProgress):
            self.document_sync_operations[event.document_uuid] = event

    def api_event_hook(self, event):
        self._non_critical_event_hook(event)
        with self.call_lock:
            self._critical_event_hook(event)

    def invalidate_cache(self):
        header_texts = {key: text for key, text in self.texts.items() if
                        key in self.MAINTAIN_TEXT_KEYS}
        self.texts.clear()
        self.texts.update(header_texts)
        self.get_items()
        self.rect_calculations()
        get_bottom_bar_rect.cache_clear()

    def rect_calculations(self):
        # Handle sync refresh button rect
        self.resync_rect = pe.Rect(0, 0, *self.resync_icon.size)
        padded = self.resync_rect.copy()
        padded.size = (self.ratios.main_menu_top_height,) * 2
        padded.topright = (self.width, 0)
        self.resync_rect.center = padded.center

    def handle_event(self, event):
        self.doc_view.handle_event(event)

    def update_sync_angle(self):
        self.rotate_angle += 360 * self.delta_time
        if self.rotate_angle >= 360:
            self.rotate_angle = 0
