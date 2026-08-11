from typing import TYPE_CHECKING

from gui.screens.docs_view import DocumentTreeViewer

if TYPE_CHECKING:
    from gui import GUI


class MainMenuDocView(DocumentTreeViewer):
    main_menu: "MainMenu"

    def __init__(self, gui: "GUI"):
        self.gui = gui
        pos, size = self.area_within_main_menu
        super().__init__(gui, (*pos, *size))

    def update_size(self):
        pos, size = self.area_within_main_menu
        self.position = pos
        self.resize(size)

    @property
    def area_within_main_menu(self):
        return (
            pos := (
                0,
                self.gui.main_menu.texts["my_files"].rect.bottom
                + self.gui.ratios.main_menu_top_padding,
            )
        ), (self.gui.width, self.gui.height - pos[1])

    @property
    def documents(self):
        return self.gui.main_menu.documents

    @property
    def document_collections(self):
        return self.gui.main_menu.document_collections

    @property
    def mode(self):
        return self.gui.config.main_menu_view_mode
