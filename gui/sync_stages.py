from typing import Dict

from rm_api.sync_stages import *

from gui.literals import SYNC_STAGE_ICON_TYPES

SYNC_STAGE_TEXTS = {
    STAGE_START: "sync.stages.start",
    STAGE_GET_ROOT: "sync.stages.get_root",
    STAGE_EXPORT_DOCUMENTS: "sync.stages.export_documents",
    STAGE_DIFF_CHECK_DOCUMENTS: "sync.stages.diff_check_documents",
    STAGE_PREPARE_DATA: "sync.stages.prepare_data",
    STAGE_COMPILE_DATA: "sync.stages.compile_data",
    STAGE_PREPARE_ROOT: "sync.stages.prepare_root",
    STAGE_PREPARE_OPERATIONS: "sync.stages.prepare_operations",
    STAGE_UPLOAD: "sync.stages.upload",
    STAGE_UPDATE_ROOT: "sync.stages.update_root",
    STAGE_SYNC: "sync.stages.sync",
    DOWNLOAD_CONTENT: "sync.stages.download_content",
}

SYNC_STAGE_ICONS: Dict[int, SYNC_STAGE_ICON_TYPES] = {
    STAGE_START: "pencil_inverted",
    STAGE_GET_ROOT: "import_inverted",
    STAGE_EXPORT_DOCUMENTS: "export_inverted",
    STAGE_DIFF_CHECK_DOCUMENTS: "rotate_inverted",
    STAGE_PREPARE_DATA: "export_inverted",
    STAGE_COMPILE_DATA: "pencil_inverted",
    STAGE_PREPARE_ROOT: "filter_inverted",
    STAGE_PREPARE_OPERATIONS: "pencil_inverted",
    STAGE_UPLOAD: "rotate_inverted",
    STAGE_UPDATE_ROOT: "pencil_inverted",
    STAGE_SYNC: "rotate_inverted",
    DOWNLOAD_CONTENT: "cloud_download_inverted",
}
