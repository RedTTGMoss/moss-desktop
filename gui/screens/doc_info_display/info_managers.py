from .shared_model import DocRenderInfoManager, DocInfoState, RenderInfo


class rMDocInfoManager(DocRenderInfoManager):
    @classmethod
    def get_document_render_info(cls, state: DocInfoState) -> RenderInfo:
        return RenderInfo(
            title='', subtitle='',
        )

    @classmethod
    def get_collection_render_info(cls, state: DocInfoState) -> RenderInfo:
        return RenderInfo(
            title='', subtitle='',
            icon='folder' if state.document.has_items else 'folder_empty',
        )