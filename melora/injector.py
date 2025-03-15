from typing import TYPE_CHECKING

import pygameextra as pe

from gui import GUI
from rm_api import DocumentCollection, Metadata, make_uuid
from rm_api.defaults import DocumentTypes

if TYPE_CHECKING:
    from .menu import InjectorMenu


class Injector(pe.ChildContext):
    LAYER = pe.AFTER_LOOP_LAYER
    parent_context: GUI
    MIN_HOVER_T = 0.3
    MAX_HOVER_T = 2

    menu: 'InjectorMenu'
    gui: GUI

    def __init__(self, parent: GUI):
        self.injected = False
        self.last_area = None
        self.extensions = {}
        self.gui = parent
        super().__init__(parent)
        from .menu import InjectorMenu
        self.menu = InjectorMenu(self)

    def loop(self):
        if not self.injected:
            from .loader import InjectorLoader
            if self.parent_context.main_menu is None:
                return
            if isinstance(self.parent_context.current_screen, InjectorLoader):
                return
            self.parent_context.screens.put(InjectorLoader(self))
            return

    def create_temp_collection(self, name: str):
        uuid = make_uuid()
        self.api.document_collections[uuid] = DocumentCollection(
            [],
            Metadata.new(name, self.gui.main_menu.navigation_parent, DocumentTypes.Collection.value), uuid
        )
        self.gui.main_menu.set_parent(uuid)
        return uuid

    def post_loop(self):
        self.menu()

    def handle_event(self, e):
        self.menu.handle_event(e)

    def run_pp_helpers(self):
        self()

    @property
    def t(self):
        return (self.hover_t - self.MIN_HOVER_T) / (self.MAX_HOVER_T - self.MIN_HOVER_T)
