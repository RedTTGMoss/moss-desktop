import json
import os
import shutil
from functools import lru_cache
from traceback import print_exc
from typing import TYPE_CHECKING, Tuple

import pygameextra as pe
import pyperclip
import rm_api.models as models
from colorama import Fore, Style
from rm_api.storage.v3 import get_file_contents, get_file, make_files_request
from rm_lines import rm_bytes_to_svg

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
        {
            "text": "Extract files",
            "icon": "export",
            "action": 'extract_files'
        },
        {
            "text": "Extract as json",
            "icon": "export",
            "action": 'extract_json',
        },
        {
            "text": "Render pages",
            "icon": "pencil",
            "action": 'render_pages'
        },
        {
            "text": "Render important",
            "icon": "star",
            "action": 'render_important'
        },
        {
            "text": "Copy UUID",
            "icon": "copy",
            "action": 'copy_uuid'
        },
        {
            "text": "Print debug info",
            "icon": "info",
            "action": 'debug_info'
        }
    )

    ratios: 'Ratios'

    def __init__(self, parent: 'GUI', document: 'Document', position: Tuple[int, int] = (0, 0)):
        self.document = document
        super().__init__(parent.main_menu, (0, 0))
        self.check_position(position)

    def check_position(self, position):
        self.left, self.top = tuple(p + o for p, o in zip(position, pe.display.display_reference.pos or (0, 0)))
        if self.rect.left != self.left or self.rect.top != self.top:
            self.initialized = False

    @classmethod
    def create(cls, parent: 'GUI', document: 'Document', position):
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
        return str(os.path.join(Defaults.SYNC_EXPORTS_FILE_PATH, str(self.document.parent),
                                self.document.uuid))

    @property
    @lru_cache
    def important_extract_location(self):
        return os.path.join(Defaults.SYNC_EXPORTS_FILE_PATH, 'important')

    def clean_extract_location(self, location=None):
        location = location or self.extract_location
        if os.path.isdir(location):
            shutil.rmtree(location, ignore_errors=True)
        os.makedirs(location, exist_ok=True)
        with open(os.path.join(location, f'$ {self.clean_filename(self.document.metadata.visible_name)}'),
                  'w') as f:
            _, lines = get_file(self.api, self.api.get_root()['hash'], use_cache=False, raw=True)
            for line in lines:
                file = models.File.from_line(line)
                if file.uuid == self.document.uuid:
                    f.write(line)
                    f.write('\n')
                    f.write(
                        make_files_request(self.api, "GET", file.hash, use_cache=False, binary=True).decode()
                    )

    def clean_file_uuid(self, file):
        return file.uuid.replace(f'{self.document.uuid}/', '')

    @staticmethod
    def clean_filename(filename):
        return "".join(c for c in filename if c.isalpha() or c.isdigit() or c == ' ').rstrip()

    def extract_files(self):
        self.clean_extract_location()

        for file in self.document.files:
            # Fetch the file
            try:
                data: bytes = get_file_contents(self.api, file.hash, binary=True, use_cache=False)
            except:
                print(f"{Fore.RED}Could not fetch file with UUID={file.uuid} HASH={file.hash}{Fore.RESET}")
                if file.uuid in self.document.content_data:
                    data = self.document.content_data[file.uuid]
                else:
                    continue
            file_path = os.path.join(self.extract_location, self.clean_file_uuid(file))

            is_json = file.uuid.rsplit('.')[-1] in ("content", "metadata")

            if self.config.add_ext_to_raw_exports and is_json:
                file_path += '.json'

            # Save the file
            with open(file_path, 'wb') as f:
                if self.config.format_raw_exports and is_json:
                    data = json.dumps(json.loads(data), indent=4, sort_keys=True).encode()
                f.write(data)

    def extract_json(self):
        self.clean_extract_location()
        with open(os.path.join(
                self.extract_location,
                f'{self.clean_filename(self.document.metadata.visible_name)}.json'
        ), 'w') as f:
            f.write(json.dumps(self.document.__dict__, indent=4, sort_keys=True))

    def render_pages(self, important: bool = False):
        if important:
            location = self.important_extract_location
        else:
            location = self.extract_location
        self.clean_extract_location(location)
        i = 0
        files = [file for file in self.document.files if file.uuid.endswith('.rm')]
        try:
            files.sort(key=lambda file: self.document.content.c_pages.get_index_from_uuid(
                file.uuid.split('/')[-1].split('.')[0]))
        except Exception as e:
            print_exc()
            pass

        for file in files:
            data: bytes = get_file_contents(self.api, file.hash, binary=True, use_cache=False)
            file_path = os.path.join(location, f'{i:>03} {self.clean_file_uuid(file)}.svg')

            # Render and save
            try:
                svg: str = rm_bytes_to_svg(data, self.document)[0]
                with open(file_path, 'w') as f:
                    f.write(svg)
            except Exception as e:
                print_exc()
            i += 1

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
