import os
import threading
import tkinter as tk
from tkinter import filedialog
from typing import TYPE_CHECKING

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


def make_tk():
    global tk_lock
    root = tk.Tk()
    root.withdraw()
    if os.name == 'nt':
        root.iconbitmap(Defaults.ICO_APP_ICON)
    if os.name == 'posix':
        img = tk.PhotoImage(file=Defaults.APP_ICON)
        root.tk.call('wm', 'iconphoto', root._w, img)
    tk_lock = True
    return root


def open_file(title: str, types_text: str, *filetypes):
    def decorator(func):
        def wrapper(*args, **kwargs):
            def prompt_file():
                global tk_lock
                if tk_lock:
                    return
                root = make_tk()
                filetypes_with_default = [(types_text, filetypes)]
                config = get_config()
                file_names = filedialog.askopenfilenames(
                    parent=root,
                    title=title,

                    filetypes=filetypes_with_default,
                    initialdir=config.last_prompt_directory if config.last_prompt_directory and os.path.isdir(
                        config.last_prompt_directory) else None
                )
                root.destroy()
                tk_lock = False

                if not file_names:
                    return

                if os.path.isdir(directory := os.path.dirname(file_names[0])):
                    config.last_prompt_directory = directory
                    pe.settings.game_context.dirty_config = True

                return func(file_names, *args, **kwargs)

            threading.Thread(target=prompt_file).start()

        return wrapper

    return decorator


def save_file(title: str, *filetypes):
    def decorator(func):
        def wrapper(document: 'Document', *args, **kwargs):
            def prompt_file():
                root = make_tk()
                filetypes_with_default = [(f'{ext} files', f'*.{ext}') for ext in filetypes]
                file_name = filedialog.asksaveasfilename(
                    parent=root,
                    title=title,
                    defaultextension=filetypes[0],
                    initialfile=document.metadata.visible_name,
                    filetypes=filetypes_with_default
                )
                root.destroy()
                return func(file_name, document, *args, **kwargs) if file_name else None

            threading.Thread(target=prompt_file).start()

        return wrapper

    return decorator


@open_file(t("prompts.import.file"), "Moss import types", *Defaults.IMPORT_TYPES)
def import_prompt(file_path, callback):
    callback(file_path)


@open_file("Import debug", "All types", *Defaults.ALL_TYPES)
def import_debug(file_path, callback):
    callback(file_path)


@open_file(t("prompts.import.notebook"), "RM lines", '.rm')
def notebook_prompt(file_path, callback):
    callback(file_path)


@save_file(t("prompts.export.pdf"), '.pdf')
def export_prompt(file_path, document: 'Document', callback):
    # TODO: formats need work
    callback(file_path)
