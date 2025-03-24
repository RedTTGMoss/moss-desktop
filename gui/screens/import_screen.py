import threading
from datetime import timedelta
from typing import Dict, TYPE_CHECKING, List

import pygameextra as pe

from gui.aspect_ratio import Ratios
from gui.cloud_action_helper import surfaces_to_pdf
from gui.defaults import Defaults
from gui.events import ResizeEvent
from gui.preview_handler import PreviewHandler
from gui.rendering import render_button_using_text, render_full_text
from gui.screens.docs_view import DocumentTreeViewer
from gui.screens.mixins import ButtonReadyMixin, TitledMixin
from gui.screens.viewer import DocumentViewer
from rm_api import Document

if TYPE_CHECKING:
    from gui import GUI
    from rm_api import API


class ImportScreenDocView(DocumentTreeViewer):
    BACKGROUND = pe.colors.red
    import_screen: 'ImportScreen'

    def __init__(self, gui: 'GUI', import_screen: 'ImportScreen'):
        self.gui = gui
        self.import_screen = import_screen
        pos, size = self.area_within_import_screen
        super().__init__(gui, (*pos, *size))

    def update_size(self):
        pos, size = self.area_within_import_screen
        self.position = pos
        self.resize(size)

    @property
    def area_within_import_screen(self):
        return (pos := (
            0,
            self.import_screen.title_bottom,
        )), (
            self.gui.width,
            self.gui.height - pos[1] - self.gui.ratios.import_screen_button_margin
        )

    @property
    def documents(self):
        return {
            **{document.uuid: document for document in self.import_screen.documents_to_upload},
            **{dummy_document.uuid: dummy_document for dummy_document in self.import_screen.dummy_documents}
        }

    @property
    def document_collections(self):
        return {}

    @property
    def mode(self):
        return self.gui.config.main_menu_view_mode


class ImportScreen(pe.ChildContext, ButtonReadyMixin, TitledMixin):
    LAYER = pe.AFTER_LOOP_LAYER

    # definitions from GUI
    api: 'API'
    parent_context: 'GUI'
    icons: Dict[str, pe.Image]
    ratios: 'Ratios'
    import_screen: 'ImportScreen'

    documents_to_upload: List['Document']
    dummy_documents: List['Document']

    EVENT_HOOK_NAME = 'import_screen_resize_check<{0}>'

    BUTTON_TEXTS = {
        **ButtonReadyMixin.BUTTON_TEXTS,
        'full': "Full Sync",
        'light': "Light Sync",
        'info_text': "Syncs a dummy so that you can archive it,\nbefore syncing the full document"
    }
    TITLE = "Import Documents"

    def __init__(self, parent: 'GUI'):
        self.documents_to_upload = []
        self.dummy_documents = []
        self.expected_documents = 0
        self.folder = parent.main_menu.navigation_parent
        self.uploading_light = False
        super().__init__(parent)
        parent.import_screen = self
        self.handle_title()
        self.handle_texts()

        self.doc_view = ImportScreenDocView(self.parent_context, self)
        self.api.add_hook(self.EVENT_HOOK_NAME.format(id(self)), self.resize_check_hook)

    def resize_check_hook(self, event):
        if isinstance(event, ResizeEvent):
            self.calculate_texts()
            self.doc_view.update_size()

    def add_item(self, document: 'Document'):
        assert isinstance(document, Document)
        self.documents_to_upload.append(document)
        document.provision = True  # Ensure that the document is in provisioning mode
        self.doc_view.handle_texts()
        if len(self.dummy_documents) > 0:  # Delete the predefined dummy document
            DocumentViewer.PROBLEMATIC_DOCUMENTS.remove(self.dummy_documents[0].uuid)
            del self.dummy_documents[0]

    def predefine_item(self, items: int = 1):
        self.expected_documents += items
        for _ in range(items):
            # This makes a dummy document that will be placed first and will have a problematic marker
            self.dummy_documents.append(Document.new_notebook(self.api, ''))
            self.dummy_documents[-1].provision = True
            self.dummy_documents[-1].metadata.last_modified += timedelta(weeks=10).total_seconds()
            DocumentViewer.PROBLEMATIC_DOCUMENTS.add(self.dummy_documents[-1].uuid)

    def loop(self):
        self.title.display()

        self.doc_view()

        not_ready = self.uploading_light or len(self.documents_to_upload) < self.expected_documents

        render_button_using_text(self.parent_context, self.texts['cancel'], outline=self.ratios.outline,
                                 action=self.close, name='import_screen.cancel',
                                 disabled=(0, 0, 0, 50) if not_ready else False)
        render_button_using_text(self.parent_context, self.texts['full'], outline=self.ratios.outline,
                                 action=self.full_import, name='import_screen.full_sync',
                                 disabled=(0, 0, 0, 50) if not_ready else False)
        light_import_rect = render_button_using_text(self.parent_context, self.texts['light'],
                                                     outline=self.ratios.outline,
                                                     action=self.light_import, name='import_screen.light_sync',
                                                     disabled=(0, 0, 0, 50) if not_ready else False)
        info_icon = self.icons['info']
        info_rect = pe.Rect(0, 0, *info_icon.size)
        info_rect.center = light_import_rect.topright
        pe.button.rect(
            info_rect,
            self.BACKGROUND, self.BACKGROUND,
            hover_draw_action=render_full_text,
            hover_draw_data=(self.parent_context, self.texts['info_text']),
            name='import_screen.light_sync > info_button'
        )
        info_icon.display(info_rect.topleft)

    def close(self):
        self.parent_context.import_screen = None
        self.api.remove_hook(self.EVENT_HOOK_NAME.format(id(self)))
        self.close_screen()

    def full_import(self):
        threading.Thread(
            target=self.api.upload_many_documents,
            args=(self.documents_to_upload,),
            daemon=True
        ).start()
        self.close()

    def light_import(self):
        if self.uploading_light:
            return
        self.uploading_light = True
        threading.Thread(
            target=self._light_import,
            daemon=True
        ).start()

    def _light_import(self):
        self.api.upload_many_documents(self.convert_light())
        self.uploading_light = False

    def convert_light(self):
        light_documents = []

        for document in self.documents_to_upload:
            preview = PreviewHandler.get_preview(document, Defaults.PREVIEW_SIZE)
            if document.content.file_type == "pdf":
                light_documents.append(document.replace_pdf(surfaces_to_pdf([
                    preview.get_finished_surface()
                ]) if preview else self.data['light_pdf']))

        return light_documents

    def handle_event(self, e):
        self.doc_view.handle_event(e)
