import io
import json
import os
import shutil
import zipfile
from typing import TYPE_CHECKING, List

import pygameextra as pe
from PIL import Image
from rm_api import Document, Metadata, Content, File
from rm_api.defaults import DocumentTypes
from rm_api.storage.common import FileHandle

if TYPE_CHECKING:
    from gui import GUI


def import_pdf_to_cloud(gui: 'GUI', file_path):
    pdf_data = FileHandle(file_path)

    parent = gui.main_menu.navigation_parent
    name = os.path.basename(file_path).rsplit('.', 1)[0]  # remove .pdf from the end

    document = Document.new_pdf(gui.api, name, pdf_data, parent)

    document.check()

    gui.import_screen.add_item(document)


def import_epub_to_cloud(gui: 'GUI', file_path):
    epub_data = FileHandle(file_path)

    parent = gui.main_menu.navigation_parent
    name = os.path.basename(file_path).rsplit('.', 1)[0]  # remove .pdf from the end

    document = Document.new_epub(gui.api, name, epub_data, parent)

    document.check()

    gui.import_screen.add_item(document)


def import_rmdoc_to_cloud(gui: 'GUI', file_path):
    files = {}
    file_uuid = None
    with (zipfile.ZipFile(file_path, 'r') as zip_ref):
        # Extract the contents to a temporary directory
        temp_dir = os.path.join(os.path.dirname(file_path), 'temp_rmdoc')
        zip_ref.extractall(temp_dir)

        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            if os.path.isdir(item_path):
                for sub_item in os.listdir(item_path):
                    sub_item_path = os.path.join(item_path, sub_item)
                    files[f"{item}/{sub_item}"] = sub_item_path
            else:
                files[item] = item_path
        for _, file in files.items():
            if _.endswith('.metadata'):
                file_uuid = _.rsplit('.', 1)[0]
            handle = FileHandle(file)
            new_location = os.path.join(gui.api.sync_file_path, handle.hash())
            shutil.move(file, new_location)
            files[_] = new_location
            handle.close()

        shutil.rmtree(temp_dir)

    content = None
    metadata = None
    content_hash = None
    file_content: List[File] = []

    for uuid, file in files.items():
        handle = FileHandle(file)
        if uuid == f'{file_uuid}.content':
            content = json.loads(handle.read())
            content_hash = handle.hash()
            file_content.append(File(content_hash, uuid, 0, handle.file_size))
        elif uuid == f'{file_uuid}.metadata':

            metadata = Metadata(json.loads(handle.read()), handle.hash())
            file_content.append(File(handle.hash(), uuid, 0, handle.file_size))

            if metadata.type == DocumentTypes.Collection.value:
                handle.close()
                return  # Collections are not supported for import yet
        else:
            file_content.append(File(handle.hash(), uuid, 0, handle.file_size))
        handle.close()

    if not content or not metadata:
        return  # Invalid .rmdoc file

    document = Document(gui.api,
                        Content(content, metadata, content_hash, gui.api.debug),
                        metadata, file_content, file_uuid, None)
    document.load_files_from_cache()
    document.parent = gui.main_menu.navigation_parent
    document.randomize_uuids()

    document.check()

    gui.import_screen.add_item(document)


def import_files_to_cloud(gui: 'GUI', files):
    files = tuple(
        file for file in files if file.endswith('.pdf') or file.endswith('.epub') or file.endswith('.rmdoc')
    )

    gui.import_screen.predefine_item(len(files))

    for file in files:
        if file.endswith('.pdf'):
            import_pdf_to_cloud(gui, file)
        if file.endswith('.epub'):
            import_epub_to_cloud(gui, file)
        if file.endswith('.rmdoc'):
            import_rmdoc_to_cloud(gui, file)


def import_notebook_pages_to_cloud(gui: 'GUI', files: List[str], title: str):
    parent = gui.main_menu.navigation_parent

    gui.import_screen.predefine_item(1)
    document = Document.new_notebook(gui.api, title, parent, page_count=len(files), notebook_data=[
        FileHandle(file) for file in files
    ])

    document.check()

    gui.import_screen.add_item(document)


def surfaces_to_pdf(surfaces: List[pe.Surface]):
    pdf_bytes = io.BytesIO()
    images = []

    for surface in (surface.surface for surface in surfaces):
        surface: pe.pygame.Surface
        # Convert the pygame surface to a raw image
        raw_image = pe.pygame.image.tobytes(surface, "RGB")
        width, height = surface.get_size()

        # Create a PIL Image for PDF inclusion
        image = Image.frombytes("RGB", (width, height), raw_image)

        images.append(image)

    images[0].save(
        pdf_bytes,
        "PDF",
        save_all=True,
        resolution=100.0,
        append_images=images[1:]
    )

    return pdf_bytes.getvalue()
