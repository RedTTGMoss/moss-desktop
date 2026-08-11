import json
import os
import shutil
import time
from concurrent.futures import as_completed, ThreadPoolExecutor
from functools import lru_cache, partial
from typing import TYPE_CHECKING, Tuple

import pygameextra as pe
import pyperclip
from colorama import Fore, Style
from pylibrm_lines import SceneTree, FailedToBuildTree
from rm_api import DownloadOperation, ROOT_DOC_SCHEMA
from rm_api.storage.v3 import get_file_contents, get_file, make_files_request

from gui.defaults import Defaults
from gui.pp_helpers.context_menu import ContextMenu

if TYPE_CHECKING:
    from rm_api.models import Document
    from gui.aspect_ratio import Ratios
    from gui import GUI


class DocumentDebugPopup(ContextMenu):
    EXISTING = {}
    CLOSE_AFTER_ACTION = True
    BUTTONS = (
        {"text": "Extract files", "icon": "export", "action": "extract_files"},
        {
            "text": "Test download",
            "icon": "export",
            "action": "test_download",
        },
        {"text": "Render pages", "icon": "pencil", "action": "render_pages"},
        {"text": "Render important", "icon": "star", "action": "render_important"},
        {"text": "Copy UUID", "icon": "copy", "action": "copy_uuid"},
        {"text": "Print debug info", "icon": "info", "action": "debug_info"},
    )

    ratios: "Ratios"

    def __init__(
        self, parent: "GUI", document: "Document", position: Tuple[int, int] = (0, 0)
    ):
        self.document = document
        super().__init__(parent.main_menu, (0, 0))
        self.check_position(position)

    def check_position(self, position):
        self.left, self.top = tuple(
            p + o for p, o in zip(position, pe.display.display_reference.pos or (0, 0))
        )
        if self.rect.left != self.left or self.rect.top != self.top:
            self.initialized = False

    @classmethod
    def create(cls, parent: "GUI", document: "Document", position):
        key = id(document)
        if cls.EXISTING.get(key) is None:
            cls.EXISTING.clear()
            cls.EXISTING[key] = cls(parent, document, position)
            return cls.EXISTING[key]
        if not cls.EXISTING[key].is_closed:
            cls.EXISTING[key].check_position(position)
            return cls.EXISTING[key]
        else:
            cls.EXISTING.clear()
            return cls.create(parent, document, position)

    def close(self):
        self.EXISTING.clear()
        super().close()

    def parent_hooking(self):
        return super().parent_hooking()

    @property
    @lru_cache
    def extract_location(self) -> str:
        return str(
            os.path.join(
                Defaults.SYNC_EXPORTS_FILE_PATH,
                str(self.document.parent),
                self.document.uuid,
            )
        )

    @property
    @lru_cache
    def important_extract_location(self):
        return os.path.join(Defaults.SYNC_EXPORTS_FILE_PATH, "important")

    def clean_extract_location(self, location=None):
        location = location or self.extract_location
        if os.path.isdir(location):
            shutil.rmtree(location, ignore_errors=True)
        os.makedirs(location, exist_ok=True)
        with open(
            os.path.join(
                location,
                f"$ {self.clean_filename(self.document.metadata.visible_name)}",
            ),
            "w",
        ) as f:
            files = get_file(
                self.api,
                self.api.get_root()["hash"],
                ROOT_DOC_SCHEMA,
                use_cache=False,
                raw=True,
            )
            for file in files.files:
                op = DownloadOperation(self.document)
                if file.uuid == self.document.uuid:
                    f.write(file.to_line())
                    f.write("\n")
                    f.write(
                        make_files_request(
                            self.api,
                            "GET",
                            file.hash,
                            file.rm_filename,
                            use_cache=False,
                            binary=True,
                            operation=op,
                        ).decode()
                    )

    @staticmethod
    def clean_filename(filename):
        return "".join(
            c for c in filename if c.isalpha() or c.isdigit() or c == " "
        ).rstrip()

    def extract_files(self):
        self.clean_extract_location()

        for file in self.document.files:
            # Fetch the file
            try:
                data: bytes = get_file_contents(
                    self.api, file.hash, file.rm_filename, binary=True, use_cache=False
                )
            except:
                print(
                    f"{Fore.RED}Could not fetch file with UUID={file.uuid} HASH={file.hash}{Fore.RESET}"
                )
                if file.uuid in self.document.content_data:
                    data = self.document.content_data[file.uuid]
                else:
                    continue
            file_path = os.path.join(self.extract_location, file.uuid)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            is_json = file.uuid.rsplit(".")[-1] in ("content", "metadata")

            if self.config.add_ext_to_raw_exports and is_json:
                file_path += ".json"

            # Save the file
            with open(file_path, "wb") as f:
                if self.config.format_raw_exports and is_json:
                    data = json.dumps(
                        json.loads(data), indent=4, sort_keys=True
                    ).encode()
                f.write(data)

        print(
            f"{Fore.GREEN}Extracted {len(self.document.files)} files to '{self.extract_location}'!{Fore.RESET}"
        )

    def test_download(self):
        self.document.ensure_download_and_callback(self.test_download_finished)

    def test_download_finished(self):
        print(
            f"{Fore.GREEN}Document '{self.document.metadata.visible_name}' downloaded successfully!{Fore.RESET}"
        )
        self.debug_info()

    def render_pages(self, important: bool = False):
        self.document.ensure_download_and_callback(
            partial(self.render_pages_after_download, important)
        )

    def _render_page(self, location: str, i: int, page) -> bool:
        file_path = os.path.join(location, f"{i:03} {page.index.value}.png")

        try:
            print(f"{Fore.CYAN}Rendering page {i}{Fore.RESET}")
            tree = SceneTree.from_document(self.document, page.id)
            try:
                tree.renderer.to_image_file(file_path)
            finally:
                del tree
            return True
        except (FailedToBuildTree, FileNotFoundError):
            return False

    def render_pages_after_download(self, important: bool = False):
        if important:
            location = self.important_extract_location
        else:
            location = self.extract_location
        self.clean_extract_location(location)

        start = time.time()
        failed = 0

        pages = list(enumerate(self.document.content.c_pages.pages))

        with ThreadPoolExecutor(max_workers=min(8, len(pages) or 1)) as executor:
            futures = [
                executor.submit(self._render_page, location, i, page)
                for i, page in pages
            ]

            for future in as_completed(futures):
                if not future.result():
                    failed += 1

        took = time.time() - start

        print(
            f"{Fore.GREEN}Rendered {len(self.document.content.c_pages.pages) - failed}/{len(self.document.content.c_pages.pages)} pages in {took:.2f} seconds!{Fore.RESET}"
        )

    def render_important(self):
        self.render_pages(True)

    def copy_uuid(self):
        pyperclip.copy(self.document.uuid)

    def debug_info(self):
        print(
            f"{Fore.LIGHTBLACK_EX}"
            f"{Style.BRIGHT}DEBUG INFO FOR '{self.document.metadata.visible_name}'"
            f"{Style.RESET_ALL}\n"
            f"{Fore.LIGHTCYAN_EX}Content data: {Fore.YELLOW}{list(self.document.content_data.keys())}\n"
            f"{Fore.LIGHTCYAN_EX}Files: {Fore.YELLOW}{[file.uuid for file in self.document.files]}\n"
            f"{Fore.LIGHTCYAN_EX}"
            f"Files available: {Fore.YELLOW}{list(self.document.files_available.keys())}\n"
            f"{Fore.LIGHTCYAN_EX}"
            f"Content files: {Fore.YELLOW}{self.document.content_files}\n"
            f"{Fore.LIGHTCYAN_EX}Provision: {Fore.YELLOW}{self.document.provision}\n"
            f"{Fore.LIGHTCYAN_EX}Available: {Fore.YELLOW}{self.document.available}\n"
            f"{Fore.LIGHTCYAN_EX}Content usable: {Fore.YELLOW}{self.document.content.usable}\n"
        )
