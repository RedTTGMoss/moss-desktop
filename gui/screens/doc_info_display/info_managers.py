from typing import Any

from rm_api import Document

from .shared_model import DocInfoManager, DocInfoState, RenderInfo
from ...defaults import Defaults
from ...preview_handler import PreviewHandler


class rMDocInfoManager(DocInfoManager):
    @classmethod
    def get_collection_state_info(cls, state: DocInfoState) -> dict:
        return {
            **cls.get_general_state_info(state),
            'has_items': state.document.has_items
        }

    @classmethod
    def get_document_state_info(cls, state: DocInfoState) -> dict:
        result = {
            **cls.get_general_state_info(state),
            'provision': state.document.provision,
            'content_hash': state.document.file_uuid_map[f'{state.document.uuid}.content'].hash,
            'metadata_hash': state.document.file_uuid_map[f'{state.document.uuid}.metadata'].hash,
            'files_available': state.document.files_available,
        }

        if state.document.downloading:
            result['download_done'] = state.document.download_done

        return result

    @classmethod
    def get_general_state_info(cls, state: DocInfoState) -> dict:
        return {
            'uuid': state.document.uuid,
            'name': state.document.metadata.visible_name,
            'last_modified': state.document.metadata.last_modified,
            'hovered': state.button.hovered,
            'rect_size': state.rect.size,
            'preview_cache': PreviewHandler.CACHED_PREVIEW.get(state.document.uuid)
        }

    @classmethod
    def get_document_render_info(cls, state: DocInfoState) -> RenderInfo:
        return RenderInfo(
            title='', subtitle='',
            preview=PreviewHandler.get_preview(state.document, state.rect.size if state.rect else Defaults.PREVIEW_SIZE),
        )

    @classmethod
    def get_collection_render_info(cls, state: DocInfoState) -> RenderInfo:
        return RenderInfo(
            title='', subtitle='',
            icon='folder' if state.document.has_items else 'folder_empty',
        )

    @classmethod
    def is_document(cls, item: Any) -> bool:
        return isinstance(item, Document)