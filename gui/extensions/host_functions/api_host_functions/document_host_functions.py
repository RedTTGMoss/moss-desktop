from functools import partial
from typing import Annotated

from box import Box
from extism import Json

from rm_api import Document
from .accessor_handlers import AccessorTypes, AccessorInstanceBox
from .shared_types import DocumentNewNotebook, DocumentNewPDF, DocumentNewEPUB
from .wrappers import document_wrapper
from .. import definitions as d


@d.host_fn()
def moss_api_document_new_notebook(value: Annotated[DocumentNewNotebook, Json]) -> str:
    _ = Box(value)
    document = Document.new_notebook(
        d.api,
        _.name,
        _.parent,
        _.accessor["uuid"],
        _.page_count,
        d.get_data_from_box(_, "notebook", True),
        d.extension_manager.metadata_objects[_.metadata_id] if _.metadata_id else None,
        d.extension_manager.content_objects[_.content_id] if _.content_id else None,
    )
    if (accessor_type := _.accessor["type"]) == AccessorTypes.APIDocument.value:
        d.api.documents[document.uuid] = document
    elif accessor_type == AccessorTypes.StandaloneDocument.value:
        d.extension_manager.document_objects[document.uuid] = document
    else:
        raise d.InvalidAccessor()
    return document.uuid


@d.host_fn()
def moss_api_document_new_pdf(value: Annotated[DocumentNewPDF, Json]) -> str:
    _ = Box(value)
    document = Document.new_pdf(
        d.api, _.name, d.get_data_from_box(_, "pdf"), _.parent, _.accessor["uuid"]
    )
    if (accessor_type := _.accessor["type"]) == AccessorTypes.APIDocument.value:
        d.api.documents[document.uuid] = document
    elif accessor_type == AccessorTypes.StandaloneDocument.value:
        d.extension_manager.document_objects[document.uuid] = document
    else:
        raise d.InvalidAccessor()
    return document.uuid


@d.host_fn()
def moss_api_document_new_epub(value: Annotated[DocumentNewEPUB, Json]) -> str:
    _ = Box(value)
    document = Document.new_epub(
        d.api, _.name, d.get_data_from_box(_, "epub"), _.parent, _.accessor["uuid"]
    )
    if (accessor_type := _.accessor["type"]) == AccessorTypes.APIDocument.value:
        d.api.documents[document.uuid] = document
    elif accessor_type == AccessorTypes.StandaloneDocument.value:
        d.extension_manager.document_objects[document.uuid] = document
    else:
        raise d.InvalidAccessor()
    return document.uuid


@d.host_fn()
@document_wrapper()
def moss_api_document_duplicate(item: Document, accessor: AccessorInstanceBox) -> str:
    new_document = item.duplicate()
    if accessor.type == AccessorTypes.APIDocument.value:
        d.api.documents[new_document.uuid] = new_document
    elif accessor.type == AccessorTypes.StandaloneDocument.value:
        d.extension_manager.document_objects[new_document.uuid] = new_document
    else:
        raise d.InvalidAccessor()
    return new_document.uuid


@d.host_fn()
@document_wrapper()
def moss_api_document_randomize_uuids(
    item: Document, accessor: AccessorInstanceBox
) -> str:
    if accessor.type == AccessorTypes.APIDocument.value:
        d.api.documents.pop(item.uuid)
        item.randomize_uuids()
        d.api.documents[item.uuid] = item
    elif accessor.type == AccessorTypes.StandaloneDocument.value:
        d.extension_manager.document_objects.pop(item.uuid)
        item.randomize_uuids()
        d.extension_manager.document_objects[item.uuid] = item
    else:
        raise d.InvalidAccessor()
    return item.uuid


@d.host_fn()
@document_wrapper()
def moss_api_document_unload_files(item: Document):
    item.unload_files()


@d.host_fn()
@document_wrapper()
def moss_api_document_load_files_from_cache(item: Document):
    item.load_files_from_cache()


@d.host_fn()
@document_wrapper()
def moss_api_document_ensure_download_and_callback(item: Document, callback: str):
    action = d.extension_manager.action(callback)
    item.ensure_download_and_callback(partial(action, _arg=item.uuid))


@d.host_fn()
@document_wrapper()
def moss_api_document_ensure_download(item: Document):
    item.ensure_download()


@d.host_fn()
@document_wrapper()
def moss_api_document_export(item: Document):
    item.export()
