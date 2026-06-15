from functools import partial
from typing import Any, Union

import humanize
from rm_api import Document, DocumentCollection

from .shared_model import DocInfoManager, DocInfoState, RenderInfo
from ...i10n import t
from ...preview_handler import PreviewHandler
from ...rendering import open_document


class rMDocInfoManager(DocInfoManager):
    @classmethod
    def get_collection_state_info(cls, state: DocInfoState) -> dict:
        document: DocumentCollection = state.document
        return {
            **cls.get_general_state_info(state),
            'item_count': document.get_item_count(state.gui.api),
            'selected': state.document.uuid in state.manager.viewer.selected_document_collections,
            'tags': document.tags,
            **{f't_tag_{tag.name}': tag.name for tag in document.tags}
        }

    @classmethod
    def get_document_state_info(cls, state: DocInfoState) -> dict:
        document: Document = state.document

        # Check and fetch the sync operation if it exists
        if document.uuid in state.gui.main_menu.document_sync_operations:
            sync_operation = state.gui.main_menu.document_sync_operations[document.uuid]
            if sync_operation.finished:
                del state.gui.main_menu.document_sync_operations[document.uuid]
                sync_operation = None
            else:
                sync_operation = sync_operation
        elif document.downloading:
            sync_operation = document.download_progress
        else:
            sync_operation = None

        result = {
            **cls.get_general_state_info(state),
            'provision': document.provision,
            'content_hash': document.file_uuid_map[f'{document.uuid}.content'].hash,
            'metadata_hash': document.file_uuid_map[f'{document.uuid}.metadata'].hash,
            'files_available': document.files_available,
            'tags': document.content.tags,
            **{f't_tag_{tag.name}': tag.name for tag in document.content.tags},
            't_size': f'{humanize.naturalsize(document.content.size_in_bytes, binary=True)}',
            'selected': state.document.uuid in state.manager.viewer.selected_documents,
        }

        if sync_operation:  # Register the sync operation on the state
            result['done'] = sync_operation.done
            result['total'] = sync_operation.total

            result['sync_operation'] = sync_operation

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
        result = {
            **cls.get_required_state_info(state),
            'uuid': document.uuid,
            'last_modified': document.metadata.last_modified,
            'preview_cache': PreviewHandler.CACHED_PREVIEW.get(document.uuid),
            'pinned': document.metadata.pinned
        }

        # Optimize title text based on state type
        if state.is_document:
            result['t_title'] = document.metadata.visible_name
            del result['t_title_folder']
        else:
            result['t_title_folder'] = document.metadata.visible_name
            del result['t_title']
        return result

    @classmethod
    def get_document_render_info(cls, state: DocInfoState) -> RenderInfo:
        return RenderInfo(
            state=state,
            preview=PreviewHandler.get_preview(state.document) if not state.document.provision else None,
            selected=state.current_state['selected'],
            progress=state.current_state.get('sync_operation'),
        )

    @classmethod
    def get_collection_render_info(cls, state: DocInfoState) -> RenderInfo:
        return RenderInfo(
            state=state,
            icon='folder' if state.document.has_items else 'folder_empty',
            selected=state.current_state['selected'],
        )

    @classmethod
    def is_document(cls, item: Any) -> bool:
        return isinstance(item, Document)

    @classmethod
    def handle_item_open(cls, state: DocInfoState):
        if state.is_document:
            state.document.ensure_download_and_callback(
                partial(
                    PreviewHandler.clear_for,
                    state.document.uuid,
                    partial(open_document, state.gui, state.document.uuid)
                )
            )
        else:
            state.manager.viewer.open_document_collection(state.document.uuid)

    @classmethod
    def handle_item_context(cls, state: DocInfoState):
        if state.is_document:
            state.manager.viewer.select_document(state.document.uuid)
        else:
            state.manager.viewer.select_document_collection(state.document.uuid)
