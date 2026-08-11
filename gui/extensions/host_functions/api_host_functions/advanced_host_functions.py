from typing import List, Annotated

import rm_api
from extism import Json
from rm_api import Document, FileSyncProgress
from rm_api.notifications.models import Notification, DocumentSyncProgress

from .shared_types import TRM_RootInfo, TRM_FileList
from .wrappers import (
    many_document_wrapper,
    document_wrapper,
    file_sync_progress_wrapper,
    event_wrapper,
)
from .. import definitions as d


@d.host_fn()
def moss_api_get_root() -> Annotated[TRM_RootInfo, Json]:
    return d.api.get_root()


@d.host_fn()
@document_wrapper()
def moss_api_upload(item: Document, callback: str, unload: bool) -> int:
    callback_function, task_id = d.extension_manager.callback(callback)
    d.api.upload(item, callback_function, unload or False)
    return task_id


@d.host_fn()
@many_document_wrapper()
def moss_api_upload_many_documents(
    items: List[Document], callback: str, unload: bool
) -> int:
    callback_function, task_id = d.extension_manager.callback(callback)
    d.api.upload_many_documents(items, callback_function, unload or False)
    return task_id


@d.host_fn()
@document_wrapper()
def moss_api_delete(item: Document, callback: str, unload: bool) -> int:
    callback_function, task_id = d.extension_manager.callback(callback)
    d.api.delete(item, callback_function, unload or False)
    return task_id


@d.host_fn()
@many_document_wrapper()
def moss_api_delete_many_documents(
    items: List[Document], callback: str, unload: bool
) -> int:
    callback_function, task_id = d.extension_manager.callback(callback)
    d.api.delete_many_documents(items, callback_function, unload or False)
    return task_id


@d.host_fn()
def moss_api_new_file_sync_progress() -> int:
    new = FileSyncProgress()
    d.extension_manager.file_sync_progress_objects[id(new)] = new
    return id(new)


@d.host_fn()
@file_sync_progress_wrapper("file_sync_progress_accessor")
def moss_api_new_document_sync_progress(
    item: FileSyncProgress, document_uuid: str
) -> int:
    new = DocumentSyncProgress(document_uuid, item)
    d.extension_manager.document_sync_progress_objects[id(new)] = new
    return id(new)


@d.host_fn()
@event_wrapper()
def moss_api_spread_event(item: Notification):
    d.api.spread_event(item)


@d.host_fn()
def moss_api_get_file(file_hash: str, use_cache: bool) -> Annotated[TRM_FileList, Json]:
    files = rm_api.get_file(d.api, file_hash, use_cache)
    return {"version": files._version, "files": files.files}


# @d.host_fn()
# def moss_api_put_file(file: Annotated[TRM_File, Json], data: str, sync_event: Annotated[AccessorInstance, Json]):
#     document_sync_event, _ = document_sync_progress_inferred(Box(sync_event))
#     rm_api.put_file(
#         d.api, File, base64.decode(data), document_sync_event
#     )

# @d.host_fn()
# def moss_api_get_file_contents():
#     ...
#
#
# @d.host_fn()
# def moss_api_check_file_exists():
#     ...
#
#
# @d.host_fn()
# def moss_api_update_root():
#     ...
