import os.path
import threading
from traceback import print_exc
from typing import Dict, Tuple, List, Optional

import pygameextra as pe
from rm_api import Document
from rm_api.models import Page
from rm_api.storage.common import FileHandle
from rm_api.storage.v3 import get_file_contents, check_file_exists, CacheMiss

from gui.defaults import Defaults
from gui.screens.viewer.renderers.notebook.rm_lines_svg_inker import Notebook_rM_Lines_Renderer

try:
    import pymupdf
except ImportError:
    pymupdf = None


class PreviewHandler:
    # Document id : (page id, sprite)
    # Sprite just allows for easy resizing
    CACHED_PREVIEW: Dict[str, Tuple[str, Optional[pe.Sprite]]] = {}
    PREVIEW_LOAD_TASKS: List[str] = []
    PYGAME_THREAD_LOCK = threading.Lock()
    TASK_LOCK = threading.Lock()

    @classmethod
    def get_preview(cls, document: Document, size: Tuple[int, int]) -> Optional[pe.Sprite]:
        size = tuple(min(given, max) for given, max in zip(size, Defaults.PREVIEW_SIZE))
        try:
            sprite = cls._get_preview(document)
        except:
            print_exc()
            sprite = None
        if sprite is None:
            return None
        sprite.resize = size
        return sprite

    @classmethod
    def _get_preview(cls, document: Document) -> Optional[pe.Sprite]:
        try:
            if document.content.cover_page_number == -1:
                page_id = document.content.c_pages.last_opened.value
            else:
                page_id = document.content.c_pages.pages[0].id
        except:
            page_id = 'index-error'
        document_id = document.uuid
        loading_task = f'{document_id}.{page_id}'
        location = os.path.join(Defaults.THUMB_FILE_PATH, f'{loading_task}.png')
        if preview := cls.CACHED_PREVIEW.get(document_id):
            if preview[0] == page_id:
                if os.path.isdir(Defaults.THUMB_FILE_PATH):
                    if not document.provision and preview[1] and not os.path.exists(location):
                        preview[1].get_finished_surface().save_to_file(location)
                return preview[1]
        # If the preview is not cached, load it
        if os.path.exists(location):
            with PreviewHandler.PYGAME_THREAD_LOCK:
                sprite = pe.Sprite(location)
            cls.CACHED_PREVIEW[document_id] = (page_id, sprite)
            return cls._get_preview(document)

        # Prevent multiple of the same task
        if loading_task in cls.PREVIEW_LOAD_TASKS:
            return None

        # Create a new loading task
        cls.PREVIEW_LOAD_TASKS.append(loading_task)
        threading.Thread(target=cls.handle_loading_task, args=(loading_task, document, page_id), daemon=True).start()

    @classmethod
    def handle_loading_task(cls, loading_task, document: Document, page_id: str):
        try:
            with cls.TASK_LOCK:
                cls._handle_loading_task(document, page_id)
        except:
            print_exc()
            cls.CACHED_PREVIEW[document.uuid] = (page_id, None)
        finally:
            cls.PREVIEW_LOAD_TASKS.remove(loading_task)

    @classmethod
    def _handle_loading_task(cls, document: Document, page_id: str):
        file = document.files_available.get(file_uuid := f'{document.uuid}/{page_id}.rm')

        base_img: pe.Surface = None

        if document.content.file_type in ('pdf', 'epub'):
            if page_id == 'index-error':
                page = Page.new_pdf_redirect(0, 'index-error', 'index-error')
            else:
                page = document.content.c_pages.get_page_from_uuid(page_id)

            if page and page.redirect:
                pdf_file = document.files_available.get(f'{document.uuid}.pdf')
                try:
                    document.load_files_from_cache()
                except CacheMiss:
                    cls.CACHED_PREVIEW[document.uuid] = (page_id, None)
                    return

                if pdf_file and (stream := document.content_data.get(pdf_file.uuid)) and pymupdf:
                    if isinstance(stream, FileHandle):
                        pdf = pymupdf.open(stream.file_path, filetype='pdf')
                    else:
                        pdf = pymupdf.open(
                            stream=stream,
                            filetype='pdf'
                        )

                    pdf_page = pdf[page.redirect.value]

                    scale_x = Defaults.PREVIEW_SIZE[0] / pdf_page.rect.width
                    scale_y = Defaults.PREVIEW_SIZE[1] / pdf_page.rect.height
                    matrix = pymupdf.Matrix(scale_x, scale_y)

                    # noinspection PyUnresolvedReferences
                    pix = pdf_page.get_pixmap(matrix=matrix)
                    mode = "RGBA" if pix.alpha else "RGB"
                    # noinspection PyTypeChecker
                    with PreviewHandler.PYGAME_THREAD_LOCK:
                        base_img = pe.Surface(
                            surface=pe.pygame.image.frombuffer(pix.samples, (pix.width, pix.height), mode))

        if not document.provision:
            document.unload_files()

        file_hash = None
        if not file:
            if pe.settings.config.download_last_opened_page_to_make_preview:
                for file in document.files:
                    if file.uuid == file_uuid:
                        file_hash = file.hash
                        break
        else:
            file_hash = file.hash
        if file_hash and check_file_exists(document.api, file_hash):
            rm_bytes = get_file_contents(document.api, file_hash, binary=True)
            if not rm_bytes:
                raise Exception('Page content unavailable to construct preview')
            notebook = Notebook_rM_Lines_Renderer.generate_expanded_notebook_from_rm(
                document, rm_bytes,
                use_lock=cls.PYGAME_THREAD_LOCK,
            )
            if notebook is None:
                raise Exception('Failed to create expanded notebook to render preview')
            image = notebook.get_frame_from_initial(0, 0, *Defaults.PREVIEW_SIZE)
        else:
            image = None

        if base_img:
            if image:
                base_img.stamp(image.reference)
                image.reference = base_img
            else:
                image = pe.Sprite(base_img)

        cls.CACHED_PREVIEW[document.uuid] = (page_id, image)

    @classmethod
    def clear_for(cls, document_uuid: str, callback=None):
        cls.CACHED_PREVIEW.pop(document_uuid, None)
        if callback:
            callback()
