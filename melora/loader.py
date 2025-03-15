import importlib
import os.path
import threading
from traceback import print_exc
from typing import TYPE_CHECKING

import pygameextra as pe
from box import BoxKeyError

from gui.defaults import Defaults
from gui.screens.mixins import LogoMixin
from melora.common import INJECTOR_COLOR
from melora.extension_base import ExtensionBase

if TYPE_CHECKING:
    from injector import Injector


class InjectorLoader(pe.ChildContext, LogoMixin):
    LAYER = pe.AFTER_LOOP_LAYER
    progress: float

    def __init__(self, injector: 'Injector'):
        self.done = 0
        self.total = 0
        self.injector = injector
        self.gui = injector.parent_context
        super().__init__(injector.parent_context)
        self.initialize_logo_and_line()
        self.logo.color, self.logo.background = INJECTOR_COLOR, None
        self.logo.init()
        self.extensions_dir = os.path.join(Defaults.SCRIPT_DIR, 'extensions')
        threading.Thread(target=self.load).start()

    def _load(self):
        if not os.path.exists(self.extensions_dir):
            os.mkdir(self.extensions_dir)
        files = [
            final_path
            for path in os.listdir(self.extensions_dir)
            if path.endswith('.py') and os.path.isfile(final_path := os.path.join(self.extensions_dir, path))
        ]
        self.total = len(files)
        for file in files:
            self.load_extension(file)
            self.done += 1
        self.injector.injected = True
        self.close_screen()

    def load_extension(self, file):
        module_name = os.path.splitext(file)[0]
        file_path = os.path.join(self.extensions_dir, file)
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        extension_class: ExtensionBase = getattr(module, 'Extension')
        if not self.enabled(extension_class.ID):
            return
        extension_instance = extension_class(self.injector)
        self.injector.extensions[extension_instance.ID] = extension_instance
        extension_instance.load()

    def enabled(self, extension_id: str):
        try:
            switches = self.gui.config.melora_extensions
        except BoxKeyError:
            self.gui.config.melora_extensions = {}
            return self.enabled(extension_id)
        enabled = switches.get(extension_id)
        if not enabled:
            switches[extension_id] = False
            self.gui.dirty_config = True
        return enabled

    def load(self):
        try:
            self._load()
        except:
            print_exc()

    def pre_loop(self):
        pe.fill.full(pe.colors.verydarkgray)

    @property
    def progress(self):
        if not self.total:
            return 0
        return self.done / self.total

    def loop(self):
        self.logo.display()

        pe.draw.rect(Defaults.LINE_GRAY, self.line_rect)
        progress_line = self.line_rect.copy()
        progress_line.width *= self.progress
        pe.draw.rect(INJECTOR_COLOR, progress_line)
        pe.draw.rect(pe.colors.black, self.line_rect, 1)
