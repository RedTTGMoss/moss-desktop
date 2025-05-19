import os
import sys
import threading
from typing import TYPE_CHECKING, List, Union, Dict

if sys.platform == 'linux':
    from .filedialogs.linux import cfd
elif sys.platform == 'win32':
    from .filedialogs.windows import cfd
else:
    from .filedialogs.macos import cfd

import pygameextra as pe

from gui.defaults import Defaults
from gui.i18n import t

if TYPE_CHECKING:
    from rm_api.models import Document
    from gui.gui import ConfigDict

tk_lock = False


# noinspection PyTypeHints
def get_config() -> 'ConfigDict':
    pe.settings.game_context.config: 'ConfigDict'
    return pe.settings.game_context.config


def get_types(types_text: str, filetypes: Union[Dict[str, Union[List[str], str]], List[str], str]) -> Dict[
    str, List[str]]:
    if isinstance(filetypes, dict):
        filetypes_list = []
        for types in filetypes.values():
            if isinstance(types, list):
                filetypes_list.extend(types)
            else:
                filetypes_list.append(types)
    elif isinstance(filetypes, str):
        filetypes_list = [filetypes]
    else:
        filetypes_list = filetypes
    return {f'{types_text} ({", ".join(filetype[1:] for filetype in filetypes_list)})': filetypes_list}


def open_file(title: str, types_text: str, filetypes):
    def decorator(func):
        def wrapper(*args, **kwargs):
            def prompt_file():
                config = get_config()
                initialdir = config.last_prompt_directory if config.last_prompt_directory and os.path.isdir(
                    config.last_prompt_directory) else None
                file_names = cfd.open_multiple(title, initialdir, get_types(types_text, filetypes))

                if not file_names:
                    return

                if os.path.isdir(directory := os.path.dirname(file_names[0])):
                    config.last_prompt_directory = directory
                    pe.settings.game_context.dirty_config = True

                return func(file_names, *args, **kwargs)

            threading.Thread(target=prompt_file).start()

        return wrapper

    return decorator


def save_file(title: str, filetypes):
    def decorator(func):
        def wrapper(document: 'Document', *args, **kwargs):
            def prompt_file():
                file_name = cfd.save_file(title, document.metadata.visible_name)

                return func(file_name, document, *args, **kwargs) if file_name else None

            threading.Thread(target=prompt_file).start()

        return wrapper

    return decorator


@open_file(t("prompts.import.file"), "Moss import types", Defaults.IMPORT_TYPES)
def import_prompt(file_path, callback):
    callback(file_path)


@open_file("Import debug", "All types", Defaults.ALL_TYPES)
def import_debug(file_path, callback):
    callback(file_path)


@open_file(t("prompts.import.notebook"), "RM lines", '.rm')
def notebook_prompt(file_path, callback):
    callback(file_path)


@save_file(t("prompts.export.pdf"), Defaults.EXPORT_TYPES)
def export_prompt(file_path, document: 'Document', callback):
    # TODO: formats need work
    callback(file_path)
