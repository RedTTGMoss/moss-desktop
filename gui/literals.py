from typing import Literal

MAIN_MENU_MODES = Literal['grid', 'list', 'compressed', 'folder']
MAIN_MENU_LOCATIONS = Literal['my_files', 'trash']
PDF_RENDER_MODES = Literal['cef', 'pymupdf', 'none', 'retry']  # CEF is deprecated
NOTEBOOK_RENDER_MODES = Literal[
    'rm_lines_svg_inker_OLD', 'librm_lines_renderer', 'retry']  # rm_lines_svg_inker is deprecated
CONTEXT_BAR_DIRECTIONS = Literal['down', 'right']
DOCUMENT_VIEWER_MODES = Literal['free', 'read']
SYNC_STAGE_ICON_TYPES = Literal[
    'rotate_inverted', 'export_inverted', 'import_inverted', 'pencil_inverted', 'filter_inverted']
