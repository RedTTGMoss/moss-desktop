from typing import Any, Union

import humanize
from rm_api import Document, DocumentCollection

from .shared_model import DocInfoManager, DocInfoState, RenderInfo
from ...defaults import Defaults
from ...i10n import t
from ...preview_handler import PreviewHandler


class rMDocInfoManager(DocInfoManager):
    @classmethod
    def get_collection_state_info(cls, state: DocInfoState) -> dict:
        document: DocumentCollection = state.document
        return {
            **cls.get_general_state_info(state),
            'item_count': document.get_item_count(state.gui.api)
        }

    @classmethod
    def get_document_state_info(cls, state: DocInfoState) -> dict:
        document: Document = state.document
        result = {
            **cls.get_general_state_info(state),
            'provision': document.provision,
            'content_hash': document.file_uuid_map[f'{document.uuid}.content'].hash,
            'metadata_hash': document.file_uuid_map[f'{document.uuid}.metadata'].hash,
            'files_available': document.files_available,
            'tags': document.content.tags,
            't_size': f'{humanize.naturalsize(document.content.size_in_bytes, binary=True)}',
        }

        if document.content.file_type == 'notebook':
            result['t_description'] = t('doc_display.sub.page_count', page_count=document.get_page_count())
        elif document.content.file_type == 'pdf':
            result['t_description'] = t('doc_display.sub.page_of', page=document.metadata.last_opened_page + 1,
                                        total=document.get_page_count())
        elif document.content.file_type == 'epub':
            result['t_description'] = t('doc_display.sub.pages_read', read_percent=document.get_read())

        if state.document.downloading:
            result['download_done'] = state.document.download_done

        return result

    @classmethod
    def get_general_state_info(cls, state: DocInfoState) -> dict:
        document: Union[Document, DocumentCollection] = state.document
        return {
            **cls.get_required_state_info(state),
            'uuid': document.uuid,
            't_title': document.metadata.visible_name,
            'last_modified': document.metadata.last_modified,
            'preview_cache': PreviewHandler.CACHED_PREVIEW.get(document.uuid),
            'pinned': document.metadata.pinned
        }

    @classmethod
    def get_document_render_info(cls, state: DocInfoState) -> RenderInfo:
        return RenderInfo(
            preview=PreviewHandler.get_preview(state.document,
                                               state.preview_size if state.preview_size else Defaults.PREVIEW_SIZE),
        )

    @classmethod
    def get_collection_render_info(cls, state: DocInfoState) -> RenderInfo:
        return RenderInfo(
            icon='folder' if state.document.has_items else 'folder_empty',
        )

    @classmethod
    def is_document(cls, item: Any) -> bool:
        return isinstance(item, Document)

    @classmethod
    def handle_item_open(cls, state: DocInfoState):
        if state.is_document:
            pass
        else:
            state.manager.viewer.open_document_collection(state.document.uuid)

    @classmethod
    def handle_item_context(cls, state: DocInfoState):
        pass
