from enum import Enum
from typing import Annotated
from typing import Any, Optional, List, TypedDict

from box import Box

from rm_api.defaults import ZoomModes, FileTypes, Orientations, DocumentTypes


class AccessorTypes(Enum):
    # Document API SUB
    APIDocumentMetadata = "api_document_metadata"
    APIDocumentContent = "api_document_content"

    # Collection API SUB
    APICollectionMetadata = "api_collection_metadata"

    # API
    APIDocument = "api_document"
    APICollection = "api_collection"

    # Document Standalone SUB
    StandaloneDocumentMetadata = "document_metadata"
    StandaloneDocumentContent = "document_content"

    # Collection Standalone SUB
    StandaloneCollectionMetadata = "collection_metadata"

    # Standalone
    StandaloneDocument = "document"
    StandaloneCollection = "collection"

    StandaloneMetadata = "metadata"
    StandaloneContent = "content"

    # Sync operations
    FileSyncProgress = "file_sync_progress"
    DocumentSyncProgress = "document_sync_progress"

    SyncStage = "sync_stage"

    # Events
    EventMossFatal = "moss_fatal"
    EventApiFatal = "api_fatal"


class AccessorInstance(TypedDict):
    type: AccessorTypes
    uuid: Optional[str]
    id: Optional[str]


class AccessorInstanceBox(Box):
    type: str
    uuid: Optional[str]
    id: Optional[str]


class DocumentNewNotebook(TypedDict):
    name: str
    parent: Optional[str]
    page_count: int
    notebook_file: Optional[List[str]]
    notebook_data: Optional[List[bytes]]
    metadata_id: Optional[str]
    content_id: Optional[str]

    accessor: AccessorInstance


class DocumentNewPDF(TypedDict):
    name: str
    pdf_file: Optional[str]
    pdf_data: Optional[bytes]
    parent: Optional[str]

    accessor: AccessorInstance


class DocumentNewEPUB(TypedDict):
    name: str
    epub_file: Optional[str]
    epub_data: Optional[bytes]
    parent: Optional[str]

    accessor: AccessorInstance


class MetadataNew(TypedDict):
    name: str
    parent: Optional[str]
    document_type: Optional[Annotated[DocumentTypes, str]]


class API_SyncProgresBase(TypedDict):
    done: int
    total: int
    stage: int
    finished: bool


class API_FileSyncProgress(API_SyncProgresBase):
    pass


class API_SyncStage(TypedDict):
    text: str
    icon: str


class API_DocumentSyncProgress(API_SyncProgresBase):
    document_uuid: str
    file_sync_operation: API_FileSyncProgress
    total_tasks: int
    finished_tasks: int
    _tasks_was_set_once: bool


class TRM_File(TypedDict):
    content_count: int
    hash: str
    rm_filename: str
    size: int
    uuid: str


class TRM_TimestampedValue(TypedDict):
    timestamp: str
    value: Optional[Any]


class TRM_Tag(TypedDict):
    name: str
    timestamp: int


class TRM_Page(TypedDict):
    id: str
    index: TRM_TimestampedValue
    template: TRM_TimestampedValue
    redirect: Optional[TRM_TimestampedValue]
    scroll_time: Optional[TRM_TimestampedValue]
    vertical_scroll: Optional[TRM_TimestampedValue]


class TRM_CPagesUUID(TypedDict):
    first: str
    second: int


class TRM_CPages(TypedDict):
    pages: List[TRM_Page]
    original: TRM_TimestampedValue
    last_opened: TRM_TimestampedValue
    uuids: List[TRM_CPagesUUID]


class TRM_Zoom(TypedDict):  # RAW
    zoomMode: ZoomModes
    customZoomCenterX: int
    customZoomCenterY: int
    customZoomPageHeight: int
    customZoomPageWidth: int
    customZoomScale: float


class TRM_Content(TypedDict):
    hash: str
    c_pages: TRM_CPages
    cover_page_number: int
    file_type: FileTypes
    version: int
    usable: bool
    zoom: TRM_Zoom
    orientation: Orientations
    tags: List[TRM_Tag]
    size_in_bytes: int
    dummy_document: bool


class TRM_MetadataBase(TypedDict):
    hash: str
    type: DocumentTypes
    parent: Optional[str]
    created_time: int
    last_modified: int
    visible_name: str
    metadata_modified: bool
    modified: bool
    synced: bool
    version: Optional[int]


class TRM_MetadataDocument(TRM_MetadataBase):
    last_opened: int
    last_opened_page: int


class TRM_DocumentCollection(TypedDict):
    tags: List[TRM_Tag]
    metadata: TRM_MetadataBase
    uuid: str
    has_items: bool


class TRM_Document(TypedDict):
    files: List[TRM_File]
    content: TRM_Content
    metadata: TRM_MetadataDocument
    uuid: str
    server_hash: Optional[str]
    files_available: List[str]
    downloading: bool
    provision: bool
    available: bool


class TRM_RootInfo(TypedDict):
    generation: int
    hash: str


class TRM_FileList(TypedDict):
    version: int
    files: List[TRM_File]


class T_PutFile:
    file: TRM_File
    content_data: Optional[str]
    content_file: Optional[bytes]
    document_sync_event: AccessorInstance
