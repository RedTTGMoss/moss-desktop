from functools import lru_cache
from typing import TYPE_CHECKING, Dict, Tuple, Optional

import pygameextra as pe

from gui.defaults import Defaults
from gui.pp_helpers import FullTextPopup, DocumentDebugPopup
from gui.preview_handler import PreviewHandler
from gui.screens.viewer import DocumentViewer
from gui.screens.viewer.viewer import CannotRenderDocument
from gui.sync_stages import SYNC_STAGE_ICONS
from rm_api import DocumentSyncProgress, STAGE_SYNC

if TYPE_CHECKING:
    from gui import GUI
    from rm_api.models import DocumentCollection
    from rm_api.models import Document
    from queue import Queue


def render_full_collection_title(gui: 'GUI', texts, collection_uuid: str, rect):
    pe.draw.rect(Defaults.OUTLINE_COLOR, rect, gui.ratios.outline)
    text = texts[collection_uuid]
    text_full = texts[collection_uuid + '_full']
    if text.text != text_full.text:
        FullTextPopup.create(gui, text_full, text)()


def render_full_text(gui: 'GUI', text: pe.Text):
    FullTextPopup.create(gui, text, text)()


def render_collection(gui: 'GUI', collection: 'DocumentCollection', texts: Dict[str, pe.Text], callback, x, y, width,
                      select_collection=None, selected=False):
    icon_key = 'folder' if collection.has_items else 'folder_empty'
    invert_icon_key = ('_inverted' if selected else '')
    if selected:
        icon_key += '_inverted'
    icon = gui.icons[icon_key]

    try:
        text = texts[collection.uuid + invert_icon_key]
    except KeyError:
        return
    text.rect.midleft = (x, y)
    text.rect.x += icon.width + gui.ratios.main_menu_folder_padding
    text.rect.y += icon.height // 1.5

    extra_x = text.rect.right + gui.ratios.main_menu_folder_padding
    star_icon = gui.icons['star' + invert_icon_key]
    tag_icon = gui.icons['tag' + invert_icon_key]

    rect = pe.rect.Rect(
        x, y,
        width -
        gui.ratios.main_menu_folder_padding,
        icon.height
    )
    rect.inflate_ip(gui.ratios.main_menu_folder_margin_x, gui.ratios.main_menu_folder_margin_y)
    if selected:
        pe.draw.rect(Defaults.SELECTED, rect.inflate(gui.ratios.main_menu_x_padding * 0.75, 0))

    icon.display((x, y))
    text.display()

    # Draw the star icon
    if collection.metadata.pinned:
        star_icon.display((extra_x, text.rect.centery - star_icon.width // 2))
        extra_x += star_icon.width + gui.ratios.main_menu_folder_padding
    if collection.tags:
        tag_icon.display((extra_x, text.rect.centery - tag_icon.width // 2))
        extra_x += tag_icon.width + gui.ratios.main_menu_folder_padding

    render_button_using_text(
        gui, text,
        Defaults.TRANSPARENT_COLOR, Defaults.TRANSPARENT_COLOR,
        name=collection.uuid + '_title_hover',
        action=None,
        data=None,
        action_set={
            'l_click': {
                'action': callback,
                'args': collection.uuid
            },
            'r_click': {
                'action': select_collection,
                'args': collection.uuid
            },
            'hover_draw': {
                'action': render_full_collection_title,
                'args': (gui, texts, collection.uuid, rect)
            }
        },
        rect=rect
    )
    # pe.button.rect(
    #     rect,
    #     Defaults.TRANSPARENT_COLOR, Defaults.TRANSPARENT_COLOR,
    #     action=callback, data=collection.uuid,
    #     hover_draw_action=pe.draw.rect,
    #     hover_draw_data=(Defaults.LINE_GRAY, rect, gui.ratios.pixel(3))
    # )


def render_full_document_title(gui: 'GUI', texts, document_uuid: str):
    text = texts[document_uuid]
    text_full = texts[document_uuid + '_full']
    if text.text != text_full.text:
        FullTextPopup.create(gui, text_full, text)()


def open_document(gui: 'GUI', document_uuid: str):
    if document_uuid in DocumentViewer.PROBLEMATIC_DOCUMENTS:
        return
    document = gui.api.documents.get(document_uuid)
    if not document or document.provision:
        return
    try:
        gui.add_screen(DocumentViewer(gui, document_uuid))
    except CannotRenderDocument:
        pass


def open_document_debug_menu(gui: 'GUI', document: 'Document', position):
    DocumentDebugPopup.create(gui, document, position)()


def render_document(gui: 'GUI', rect: pe.Rect, texts, document: 'Document',
                    document_sync_operation: DocumentSyncProgress = None, scale=1, select_document=None,
                    selected: bool = False):
    # Prepare edge rounding and all the texts
    edge_rounding = int(gui.ratios.main_menu_document_rounding * rect.width)
    inverse_key = '_inverted' if selected else ''
    title_text = texts.get(document.uuid + inverse_key)
    if not title_text:
        return
    sub_text: Optional[pe.Text]
    if document.content.file_type == 'notebook':
        page_count = document.get_page_count()
        if page_count < 0:
            sub_text = texts.get('page_info_unknown')
        else:
            sub_text = texts.get(f'page_count_{page_count}{inverse_key}')
    elif document.content.file_type == 'pdf':
        page_count = document.get_page_count()
        if page_count < 0:
            sub_text = texts.get('page_info_unknown')
        else:
            sub_text = texts.get(
                f'page_of_{document.metadata.last_opened_page + 1}_{page_count}{inverse_key}')
    elif document.content.file_type == 'epub':
        read_percent = document.get_read()
        if read_percent < 0:
            sub_text = texts.get('page_info_unknown')
        else:
            sub_text = texts.get(f'page_read_{read_percent}{inverse_key}')
    else:
        sub_text = None

    # Position the texts
    title_text.rect.topleft = rect.bottomleft
    title_text.rect.top += gui.ratios.main_menu_document_title_height_margin
    if sub_text:
        sub_text.rect.left = title_text.rect.left
        sub_text.rect.top = title_text.rect.bottom + gui.ratios.main_menu_document_title_padding

    # Prepare the action set if the document is clicked
    action = document.ensure_download_and_callback
    data = lambda: PreviewHandler.clear_for(document.uuid, lambda: open_document(gui, document.uuid))
    action_set = {
        'l_click': {
            'action': action,
            'args': data
        },
        'r_click': {
            'action': select_document,
            'args': document.uuid
        }
    }
    disabled = document.downloading

    # Start downloading the document if it's not available and not downloading
    # If the config specifies to download everything, download everything
    # In this case it will only download it when it shows up on the screen
    if gui.config.download_everything and not document.available and not document.downloading:
        document.ensure_download_and_callback(lambda: PreviewHandler.clear_for(document.uuid))

    # Draw black outline if selected
    if selected:
        selection_rect = rect.inflate(gui.ratios.main_menu_x_padding, gui.ratios.main_menu_x_padding)
        selection_rect.height += title_text.rect.height + gui.ratios.main_menu_x_padding + gui.ratios.line * 2
        pe.draw.rect(Defaults.SELECTED, selection_rect)

    # Draw a background behind the document
    pe.draw.rect(Defaults.DOCUMENT_BACKGROUND, rect)

    # Render the title text
    render_button_using_text(
        gui, title_text,
        Defaults.TRANSPARENT_COLOR, Defaults.TRANSPARENT_COLOR,
        name=document.uuid + '_title_hover',
        action=None,
        data=None,
        action_set={
            **action_set,
            'hover_draw': {
                'action': render_full_document_title,
                'args': (gui, texts, document.uuid)
            }
        },
        disabled=document.provision or disabled
    )

    # Render the sub text if it exists
    if sub_text:
        sub_text.display()

    # Render the notebook icon if there is no preview
    preview = PreviewHandler.get_preview(document, rect.size)
    if not preview:
        notebook_large: pe.Image = gui.icons['notebook_large'].copy()
        notebook_large.resize(tuple(v * scale for v in notebook_large.size))
        notebook_large_rect = pe.Rect(0, 0, *notebook_large.size)
        notebook_large_rect.center = rect.center
        notebook_large.display(notebook_large_rect.topleft)
    else:
        preview.display(rect.topleft)

    # Render the availability cloud icon
    is_problematic = not document.content.usable or document.uuid in DocumentViewer.PROBLEMATIC_DOCUMENTS
    if is_problematic or not document.available:
        if document.downloading:
            cloud_icon: pe.Image = gui.icons['cloud_download']
        elif is_problematic:
            cloud_icon: pe.Image = gui.icons['warning_circle']
        else:
            cloud_icon: pe.Image = gui.icons['cloud']
        cloud_icon_rect = pe.Rect(0, 0, *cloud_icon.size)

        # Add padding
        cloud_icon_padded_rect = cloud_icon_rect.inflate(gui.ratios.main_menu_document_cloud_padding,
                                                         gui.ratios.main_menu_document_cloud_padding)

        cloud_icon_padded_rect.scale_by_ip(1, .75)  # The icon itself is square, but the padded box is not
        cloud_icon_padded_rect.bottomright = rect.bottomright

        cloud_icon_rect.center = cloud_icon_padded_rect.center

        pe.draw.rect(Defaults.DOCUMENT_BACKGROUND,
                     cloud_icon_padded_rect)  # Give the cloud icon a white background with padding
        cloud_icon.display(cloud_icon_rect.topleft)

    # Render the passive outline
    pe.draw.rect(
        Defaults.DOCUMENT_GRAY,
        rect, gui.ratios.pixel(2),
        edge_rounding_topright=edge_rounding,
        edge_rounding_bottomright=edge_rounding
    )
    # Render the passive spine
    spine_rect = rect.scale_by(0.07, 1)
    spine_rect.left = rect.left
    pe.draw.rect(
        Defaults.DOCUMENT_GRAY,
        spine_rect
    )

    # Render the button
    pe.button.action(
        rect,
        name=document.uuid,
        action_set={
            **action_set,
            'hover_draw': {
                'action': pe.draw.rect,
                'args': (Defaults.BUTTON_ACTIVE_COLOR, rect.copy()),
                'kwargs': {'edge_rounding_topright': edge_rounding, 'edge_rounding_bottomright': edge_rounding}
            }
        },
        disabled=document.provision or disabled
    )

    if gui.config.debug:
        popup_exists = DocumentDebugPopup.EXISTING.get(id(document)) is not None
        debug_text = gui.main_menu.texts['debug']

        # Inflate a rect around the debug text
        inflated_rect = debug_text.rect.inflate(gui.ratios.pixel(20), gui.ratios.pixel(20))
        inflated_rect.topright = rect.topright
        debug_text.rect.center = inflated_rect.center

        if not popup_exists:
            def draw_debug_background():
                # Draw the original_background
                pe.draw.rect(Defaults.BUTTON_ACTIVE_COLOR, rect)
                # Draw a background for the debug button
                pe.draw.rect(Defaults.LINE_GRAY, inflated_rect)

            pe.button.action(
                inflated_rect,
                hover_draw_action=draw_debug_background,
                name=document.uuid + '_debug',
                action=open_document_debug_menu,
                data=(gui, document, inflated_rect.topleft)
            )
            debug_text.display()
        else:
            open_document_debug_menu(gui, document, inflated_rect.topleft)

    if document.provision and document_sync_operation:
        progress_rect = rect.copy()
        progress_rect.width -= gui.ratios.document_sync_progress_margin * 2
        progress_rect.height = gui.ratios.document_sync_progress_height
        progress_rect.midbottom = rect.midbottom
        progress_rect.bottom -= gui.ratios.document_sync_progress_margin

        pe.draw.rect(
            Defaults.BACKGROUND,
            progress_rect.inflate(gui.ratios.document_sync_progress_outline * 2,
                                  gui.ratios.document_sync_progress_outline * 2),
            edge_rounding=gui.ratios.document_sync_progress_rounding + gui.ratios.document_sync_progress_outline
        )
        pe.draw.rect(Defaults.BUTTON_DISABLED_COLOR, progress_rect,
                     edge_rounding=gui.ratios.document_sync_progress_rounding)
        # left = progress_rect.left
        if document_sync_operation and document_sync_operation.total > 0:
            progress_rect.width *= document_sync_operation.done / document_sync_operation.total
        pe.draw.rect(Defaults.SELECTED, progress_rect, edge_rounding=gui.ratios.document_sync_progress_rounding)


def render_button_using_text(
        gui: 'GUI', text: pe.Text,
        inactive_color: Tuple[int, ...] = None, active_color: Tuple[int, ...] = None,
        *args,
        name: str = None, action=None, data=None,
        rect: pe.Rect = None,
        outline: int = None,
        text_infront: bool = False,
        outline_color: Tuple[int, ...] = None,
        **kwargs
):
    if not outline_color:
        outline_color = Defaults.OUTLINE_COLOR
    if not inactive_color:
        inactive_color = Defaults.TRANSPARENT_COLOR
    if not active_color:
        active_color = Defaults.BUTTON_ACTIVE_COLOR
    if not text_infront:
        text.display()
    if not rect:
        rect = gui.ratios.pad_button_rect(text.rect)
    pe.button.rect(
        rect,
        inactive_color, active_color,
        *args,
        name=name,
        action=action,
        data=data,
        **kwargs
    )
    if outline is not None and outline > 0:
        pe.draw.rect(outline_color, rect, outline)
    if text_infront:
        text.display()
    return rect


def render_header(gui: 'GUI', texts: Dict[str, pe.Text], callback, path_queue: 'Queue'):
    menu_location = gui.main_menu.menu_location

    render_button_using_text(gui, texts[menu_location], action=callback, name='main_menu.header')

    x = texts[menu_location].rect.right + gui.ratios.main_menu_path_padding
    y = texts[menu_location].rect.centery

    width = 0
    skips = 0

    # Calculate the width of the path
    for item in path_queue.queue:
        text_key = f'path_{item}'
        width += gui.icons['chevron_right'].width + texts[text_key].rect.width

    # Calculate the number of items to skip in the path, this results in the > > you see in the beginning
    while width > gui.width - (x + 200):
        skips += 1
        if len(path_queue.queue) - skips <= 0:
            # window is too small to render the path
            return
        width -= texts[f'path_{path_queue.queue[-skips]}'].rect.width

    # Draw the path
    for i, item in enumerate(reversed(path_queue.queue)):
        text_key = f'path_{item}'

        # Draw the arrow
        if i >= skips or i < 1:  # Making sure to render the arrow only for the first skip, making sure to avoid > > > >
            gui.icons['chevron_right'].display((x, y - gui.icons['chevron_right'].height // 2))

            x += gui.icons['chevron_right'].width
            if i == 0:
                x += gui.ratios.main_menu_path_first_padding

        # Draw the text only if it's not skipped
        if i >= skips:
            texts[text_key].rect.midleft = (x, y)
            render_button_using_text(gui, texts[text_key], action=callback, data=item, name=f'main_menu.path={item}')
            x += texts[text_key].rect.width


@lru_cache
def get_bottom_bar_rect(gui: 'GUI'):
    return pe.Rect(0, gui.height - gui.ratios.bottom_bar_height, gui.width, gui.ratios.bottom_bar_height)


def draw_bottom_bar(gui: 'GUI'):
    # The entire lower bar
    pe.draw.rect(
        Defaults.SELECTED,
        get_bottom_bar_rect(gui)
    )


def draw_bottom_loading_bar(
        gui: 'GUI',
        current: int, total: int,
        previous_t: float = 0,
        finish: bool = False, stage: int = STAGE_SYNC
):
    draw_bottom_bar(gui)
    bottom_bar_rect = get_bottom_bar_rect(gui)
    loading_bar_rect = pe.Rect(0, 0, gui.ratios.bottom_loading_bar_width, gui.ratios.bottom_loading_bar_height)
    loading_bar_rect.midright = bottom_bar_rect.midright
    loading_bar_rect.x -= gui.ratios.bottom_loading_bar_padding

    # Draw the loading bar background
    pe.draw.rect(Defaults.BUTTON_DISABLED_LIGHT_COLOR, loading_bar_rect, 0,
                 edge_rounding=gui.ratios.bottom_loading_bar_rounding)

    t = (current / total) if total else 0
    if t == 0 or t == 1:
        smooth_t = t
    elif abs(t - previous_t) > 0.01:
        smooth_t = previous_t + (t - previous_t) * pe.settings.game_context.delta_time * 10
    else:
        smooth_t = t
    smooth_t = min(1, max(0, smooth_t))

    if total > 0:
        loading_bar_rect.width = int(loading_bar_rect.width * smooth_t)

    pe.draw.rect(Defaults.BACKGROUND, loading_bar_rect, 0, edge_rounding=gui.ratios.bottom_loading_bar_rounding)

    # Make and show text of current / total
    if not finish:
        prepend_text = gui.main_menu.texts.get(
            f'rm_api_stage_{stage or STAGE_SYNC}',
            gui.main_menu.texts[f'rm_api_stage_{STAGE_SYNC}']
        )

        icon_key = f'{SYNC_STAGE_ICONS.get(stage or STAGE_SYNC, SYNC_STAGE_ICONS[STAGE_SYNC])}'
        base_icon: pe.Image = gui.icons[icon_key]
        base_icon_rect = pe.Rect(0, 0, *base_icon.size)

        if icon_key == 'rotate_inverted':
            icon = pe.Image(
                pe.pygame.transform.rotate(
                    base_icon.surface.surface, 360 - gui.main_menu.rotate_angle  # Make it rotate clockwise
                )
            )
            icon_rect = pe.Rect(0, 0, *icon.size)
        else:
            icon = base_icon
            icon_rect = base_icon_rect

        text = pe.Text(f"{current} / {total}", Defaults.MAIN_MENU_PROGRESS_FONT, gui.ratios.bottom_bar_size,
                       colors=Defaults.TEXT_COLOR_H)

        # Position the texts and icon
        text.rect.midright = loading_bar_rect.midleft
        text.rect.right -= gui.ratios.bottom_loading_bar_padding

        base_icon_rect.midright = text.rect.midleft
        base_icon_rect.right -= gui.ratios.bottom_loading_bar_padding

        prepend_text.rect.midright = base_icon_rect.midleft
        prepend_text.rect.right -= gui.ratios.bottom_loading_bar_padding

        icon_rect.center = base_icon_rect.center

        text.display()
        prepend_text.display()
        icon.display(icon_rect.topleft)
    else:
        icon: pe.Image = gui.icons['cloud_synced_inverted']
        icon_rect = pe.Rect(0, 0, *icon.size)
        icon_rect.midright = loading_bar_rect.midleft
        icon_rect.right -= gui.ratios.bottom_loading_bar_padding
        icon.display(icon_rect.topleft)

    return smooth_t
