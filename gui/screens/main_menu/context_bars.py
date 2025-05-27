from functools import partial
from queue import Queue
from typing import TYPE_CHECKING, List, Union

import pygameextra as pe
from rm_api.helpers import threaded
from rm_api.models import Document, DocumentCollection

import gui.events as ev
from gui.cloud_action_helper import import_files_to_cloud
from gui.defaults import Defaults
from gui.file_prompts import import_prompt
from gui.i10n import t
from gui.pp_helpers import ContextBar
from gui.pp_helpers.popups import ConfirmPopup
from gui.screens.main_menu.context_menus import DeleteContextMenu, ImportContextMenu
from gui.screens.name_field_screen import NameFieldScreen

if TYPE_CHECKING:
    from rm_api import API


class MainMenuContextBar(ContextBar):
    ONLINE_ACTIONS = ()
    INCLUDE_MENU = True
    ALIGN = 'center'

    def __init__(self, parent):
        if self.INCLUDE_MENU:
            # noinspection PyTypeChecker
            self.BUTTONS = (
                {
                    "text": "menu.top.menu",
                    "icon": "burger",
                    "action": 'open_menu'
                }, *self.BUTTONS
            )
        self.popups = Queue()
        if parent.api.offline_mode:
            for button in self.BUTTONS:
                if button['action'] in self.ONLINE_ACTIONS:
                    button['disabled'] = True
        super().__init__(parent)
        if self.api.offline_mode:
            self.offline_error_text = pe.Text(
                t("menu.top.offline"),
                Defaults.MAIN_MENU_BAR_FONT, parent.ratios.main_menu_bar_size,
                colors=Defaults.TEXT_ERROR_COLOR
            )
            self.update_offline_error_text()

    def update_offline_error_text(self):
        self.offline_error_text.rect.bottomright = (
            self.width - self.ratios.main_menu_button_margin, self.ratios.main_menu_top_height)

    def handle_scales(self):
        super().handle_scales()
        if self.api.offline_mode:
            self.update_offline_error_text()

    def pre_loop(self):
        super().pre_loop()
        pe.draw.rect(Defaults.SELECTED if self.INVERT else Defaults.BACKGROUND,
                     (0, 0, self.width, self.ratios.main_menu_top_height))

    def post_loop(self):
        super().post_loop()
        if self.api.offline_mode:
            self.offline_error_text.display()
        if len(self.popups.queue) > 0:
            self.popups.queue[0]()
            if self.popups.queue[0].closed:
                self.popups.get()
        if self.INVERT:
            self.main_menu.resync_icon_inverted.display(self.main_menu.resync_rect.topleft)
        else:
            self.main_menu.resync_icon.display(self.main_menu.resync_rect.topleft)
        pe.button.rect(
            self.ratios.pad_button_rect(self.main_menu.resync_rect),
            Defaults.TRANSPARENT_COLOR,
            Defaults.BUTTON_ACTIVE_COLOR_INVERTED if self.INVERT else Defaults.BUTTON_ACTIVE_COLOR,
            action=self.main_menu.refresh, name='main_menu.refresh',
            disabled=(Defaults.BUTTON_DISABLED_COLOR if self.INVERT else Defaults.BUTTON_DISABLED_LIGHT_COLOR)
            if self.main_menu.loading or self.api.sync_notifiers != 0 else False
        )

    def handle_new_context_menu(self, context_menu_getter, index):
        super().handle_new_context_menu(
            lambda ideal_position: context_menu_getter((ideal_position[0], self.ratios.main_menu_top_height)), index
        )

    def finalize_button_rect(self, buttons, width, height):
        width += (len(self.BUTTONS) - (2 if self.INCLUDE_MENU else 1)) * self.ratios.main_menu_bar_padding
        max_width = self.main_menu.resync_rect.left - self.ratios.main_menu_button_margin
        if self.INCLUDE_MENU:
            width -= buttons[0].area.width
        if self.ALIGN == 'center':
            x = self.width / 2
            x -= width / 2
        elif self.ALIGN == 'left':
            x = self.ratios.main_menu_button_margin
        elif self.ALIGN == 'right':
            x = max_width - width - self.ratios.main_menu_button_margin
        if self.INCLUDE_MENU:
            margin = (self.ratios.main_menu_top_height - buttons[0].area.height) / 2
            buttons[0].area.left = margin
            buttons[0].area.top = margin
        for button in buttons[1 if self.INCLUDE_MENU else 0:]:
            button.area.left = x
            x = button.area.right + self.ratios.main_menu_bar_padding

    def open_menu(self):
        self.main_menu.hamburger()


class TopBar(MainMenuContextBar):
    ADD_FOLDER = {
        "text": "menu.top.create.folder",
        "icon": "folder_add",
        "action": 'create_collection'
    }
    BUTTONS = (
        {
            "text": "menu.top.create.notebook",
            "icon": "notebook_add",
            "action": 'create_notebook'
        }, dict(ADD_FOLDER), {
            "text": "menu.top.import",
            "icon": "import",
            "action": 'import_action',
            "context_menu": 'import_context',
            "context_icon": "small_chevron_down"
        },
        # {
        #     "text": "Export",
        #     "icon": "export",
        #     "action": None,
        #     "disabled": True
        # }
    )
    ONLINE_ACTIONS = ['create_notebook', 'create_collection', 'import_action']
    api: 'API'

    def create_notebook(self):
        self.api.spread_event(ev.CreateNotebookInit)
        NameFieldScreen(self.parent_context, "New Notebook", "", self._create_notebook,
                        partial(self.api.spread_event, ev.CreateNotebookCancelled),
                        submit_text='Create notebook')

    def create_collection(self):
        self.api.spread_event(ev.CreateCollectionInit)
        NameFieldScreen(self.parent_context, "New Folder", "", self._create_collection,
                        partial(self.api.spread_event, ev.CreateCollectionCancelled),
                        submit_text='Create folder')

    @threaded
    def _create_notebook(self, title):
        doc = Document.new_notebook(self.api, title, self.main_menu.navigation_parent)
        self.api.spread_event(ev.CreateNotebookConfirmed(title, doc.uuid))
        self.api.upload(doc)

    @threaded
    def _create_collection(self, title):
        col = DocumentCollection.create(self.api, title, self.main_menu.navigation_parent)
        self.api.spread_event(ev.CreateCollectionConfirmed(title, col.uuid))
        self.api.upload(col)

    def import_action(self):
        import_prompt(lambda file_paths: import_files_to_cloud(self.parent_context, file_paths))

    def import_context(self, ideal_position):
        return ImportContextMenu(self.main_menu, ideal_position)


class TopBarSelectOne(MainMenuContextBar):
    BUTTONS = (
        {
            "text": "menu.top.deselect",
            "icon": "x_medium",
            "action": "deselect"
        }, {
            "text": "menu.common.rename",
            "icon": "text_edit",
            "action": "rename"
        }, {
            "text": "menu.common.favorite",
            "icon": "star",
            "action": "favorite"
        }, {
            "text": "menu.common.duplicate",
            "icon": "duplicate",
            "action": "duplicate"
        }, {
            "text": "menu.common.trash",
            "icon": "trashcan",
            "action": "trash",
            "context_menu": 'delete_context',
            "context_icon": "small_chevron_down"
        }, {
            "text": "menu.common.move",
            "icon": "move",
            "action": "move"
        },
    )
    ONLINE_ACTIONS = ('rename', 'favorite', 'duplicate', 'trash', 'move')
    DELETE_MESSAGE = "Are you sure you want to delete this item?"
    INVERT = True
    INCLUDE_MENU = False
    ALIGN = 'left'

    def __init__(self, parent):
        super().__init__(parent)
        self.is_favorite = False

    def delete_confirm(self):
        self.api.spread_event(ev.UserDeleteInit(self.both_as_items))
        self.popups.put(ConfirmPopup(self.parent_context, "Delete", self.DELETE_MESSAGE, self.delete, partial(
            self.api.spread_event, ev.UserDeleteCancelled()
        )))

    @threaded
    def delete(self):
        items = self.both_as_items
        sub_items = []
        for item in items:
            if isinstance(item, DocumentCollection):
                sub_items.extend(item.recurse(self.api))
        self.deselect()
        self.api.spread_event(ev.UserDeleteConfirmed(items + sub_items))
        self.api.delete_many_documents(items + sub_items)

    def move(self):
        self.main_menu.move_mode = True

    @threaded
    def duplicate(self, here: bool = False):
        items_to_upload: List[Union[Document, DocumentCollection]] = []
        for document_uuid in reversed(tuple(self.documents)):
            document = self.api.documents[document_uuid]
            items_to_upload.append(document.duplicate())
            if here:
                items_to_upload[-1].parent = self.main_menu.navigation_parent
            items_to_upload[-1].metadata.visible_name += " copy"

        for document_collection_uuid in reversed(tuple(self.document_collections)):
            document_collection = self.api.document_collections[document_collection_uuid]
            items, collection = document_collection.duplicate(self.api)
            items_to_upload.extend(items)
            items_to_upload.append(collection)
            if here:
                items_to_upload[-1].parent = self.main_menu.navigation_parent
            items_to_upload[-1].metadata.visible_name += " copy"
        self.deselect()
        self.api.spread_event(ev.UserDuplicateConfirmed(self.both_as_items, items_to_upload))
        self.api.upload_many_documents(items_to_upload)

    def deselect(self):
        self.documents.clear()
        self.document_collections.clear()

    @property
    def documents(self):
        return self.main_menu.doc_view.selected_documents

    @property
    def document_collections(self):
        return self.main_menu.doc_view.selected_document_collections

    @property
    def both(self):
        return tuple(self.documents) + tuple(self.document_collections)

    @property
    def both_as_items(self):
        return [self.get_item(uuid) for uuid in self.both]

    def post_loop(self):
        super().post_loop()
        self.is_favorite = all(map(lambda x: self.get_item(x).metadata.pinned, self.both))
        for button in self.BUTTONS:
            if 'star' in button['icon']:
                button['icon'] = 'star_empty' if self.is_favorite else 'star'
                break

    @threaded
    def favorite(self):
        items_to_upload = []
        for document_uuid in self.documents:
            document = self.api.documents[document_uuid]
            items_to_upload.append(document)
            document.metadata.pinned = not self.is_favorite
        for document_collection_uuid in self.document_collections:
            document_collection = self.api.document_collections[document_collection_uuid]
            items_to_upload.append(document_collection)
            document_collection.metadata.pinned = not self.is_favorite
        self.deselect()
        self.api.spread_event(ev.UserFavoritesConfirmed(items_to_upload))
        self.api.upload_many_documents(items_to_upload)

    def rename(self):
        is_notebook = isinstance(self.single_item, Document)
        self.api.spread_event(
            partial(ev.RenameNotebookInit if is_notebook else ev.RenameCollectionInit, self.single_item.uuid))
        NameFieldScreen(self.parent_context, "Rename", self.single_item.metadata.visible_name, self._rename,
                        partial(self.api.spread_event,
                                partial(ev.RenameNotebookCancelled if is_notebook else ev.RenameCollectionCancelled,
                                        self.single_item.uuid)),
                        submit_text='Finish rename')

    @threaded
    def _rename(self, new_name: str):
        self.api.spread_event(
            partial(
                ev.RenameNotebookConfirmed if isinstance(self.single_item, Document) else ev.RenameCollectionConfirmed,
                self.single_item.uuid, new_name, self.single_item.metadata.visible_name
            )
        )
        self.single_item.metadata.visible_name = new_name
        self.api.upload(self.single_item)

    @property
    def single_item(self) -> Union[Document, DocumentCollection]:
        if len(self.documents) > 0:
            return self.api.documents[next(iter(self.documents))]
        else:
            return self.api.document_collections[next(iter(self.document_collections))]

    def get_item(self, uuid: str) -> Union[Document, DocumentCollection]:
        if uuid in self.documents:
            return self.api.documents[uuid]
        else:
            return self.api.document_collections[uuid]

    @threaded
    def move_to(self, parent: str):
        items_to_upload = []
        for document_uuid in self.documents:
            document = self.api.documents[document_uuid]
            items_to_upload.append(document)
            document.parent = parent
        for document_collection_uuid in self.document_collections:
            document_collection = self.api.document_collections[document_collection_uuid]
            items_to_upload.append(document_collection)
            document_collection.parent = parent
        self.deselect()
        self.api.spread_event(ev.MoveConfirmed(items_to_upload, parent))
        self.api.upload_many_documents(items_to_upload)

    def trash(self):
        self.move_to('trash')

    def delete_context(self, ideal_position):
        return DeleteContextMenu(self.main_menu, ideal_position)


class TopBarTrash(MainMenuContextBar):
    BUTTONS = (
        {
            "text": "menu.top.empty_trash",
            "icon": "trashcan_delete",
            "action": 'delete_confirm'
        },
    )
    ONLINE_ACTIONS = ('delete_confirm',)
    ALIGN = 'right'

    @property
    def bin_items(self):
        return [
            item for item in self.api.documents.values() if item.parent == 'trash'
        ]

    @threaded
    def delete(self):
        items = self.bin_items

        for collection in self.api.document_collections.values():
            if collection.parent != 'trash':
                continue
            items.extend(collection.recurse(self.api))
            items.append(collection)

        self.api.spread_event(ev.UserDeleteConfirmed(items))
        self.api.delete_many_documents(items)

    def delete_confirm(self):
        self.api.spread_event(ev.UserDeleteInit(self.bin_items))
        self.popups.put(ConfirmPopup(self.parent_context,
                                     "Delete permanently?",
                                     "Are you sure you want to clear the trash?\n"
                                     "This action is irreversible.",
                                     self.delete, partial(self.api.spread_event, ev.UserDeleteCancelled())))


class TopBarSelectMulti(TopBarSelectOne):
    BUTTONS = (
        {
            "text": "menu.top.deselect",
            "icon": "x_medium",
            "action": "deselect"
        }, {
            "text": "menu.common.favorite",
            "icon": "star",
            "action": "favorite"
        }, {
            "text": "menu.common.duplicate",
            "icon": "duplicate",
            "action": "duplicate"
        }, {
            "text": "menu.common.trash",
            "icon": "trashcan",
            "action": "trash",
            "context_menu": 'delete_context',
            "context_icon": "small_chevron_down"
        }, {
            "text": "menu.common.move",
            "icon": "move",
            "action": "move"
        },
    )
    DELETE_MESSAGE = "Are you sure you want to delete these items?"


class TopBarSelectMove(TopBarSelectOne):
    BUTTONS = (
        {
            "text": "menu.cancel_move",
            "icon": "x_medium",
            "action": "cancel"
        }, {
            "text": "menu.top.deselect",
            "icon": "x_medium",
            "action": "deselect"
        }, dict(TopBar.ADD_FOLDER), {
            "text": "menu.move_here",
            "icon": "move",
            "action": "finalize_move"
        }, {
            "text": "menu.duplicate_here",
            "icon": "duplicate",
            "action": "duplicate_here"
        },
    )

    def cancel(self):
        self.main_menu.move_mode = False

    def finalize_move(self):
        self.move_to(self.main_menu.navigation_parent)

    def duplicate_here(self):
        super().duplicate(here=True)

    # noinspection PyProtectedMember
    def create_collection(self):
        self.main_menu._bar.create_collection()
