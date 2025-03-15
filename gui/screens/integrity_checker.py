import os.path
import subprocess
import zipfile
from functools import partial
from queue import Queue
from typing import TYPE_CHECKING

import pygameextra as pe

from gui.events import ResizeEvent
from gui.gui import APP_NAME, Defaults
from gui.pp_helpers.popups import WarningPopup, InstallPopup
from gui.screens.mixins import LogoMixin

if TYPE_CHECKING:
    from gui.gui import GUI


class GitCheckException(Exception):
    pass


class IntegrityChecker(pe.ChildContext, LogoMixin):
    LAYER = pe.AFTER_LOOP_LAYER

    def __init__(self, parent: "GUI"):
        self.checked = False
        if os.path.exists('requirements.txt'):
            with open('requirements.txt'):
                self.versions = {
                    package: version
                    for package, version in
                    map(lambda line: str.split(line, '==') if '==' in line else (None, None),
                        open('requirements.txt').read().splitlines())
                }
        else:
            self.versions = None
        super().__init__(parent)
        self.warnings = Queue()
        self.initialize_logo_and_line()
        self.api.add_hook('version_checker_resize_check', self.resize_check_hook)

    def resize_check_hook(self, event):
        if isinstance(event, ResizeEvent):
            self.initialize_logo_and_line()

    def events(self):
        pass

    def check(self):
        self.checked = True
        if self.versions is not None:
            # Ensure PygameExtra is up to date
            if pe.__version__ != self.versions['pygameextra']:
                self.warnings.put(WarningPopup(
                    self.parent_context,
                    "PygameExtra is outdated",
                    f"You are running from source.\n"
                    f"The main package that {APP_NAME} uses is outdated!\n"
                    f"Please update PygameExtra to {self.versions['pygameextra']}\n"
                    "This should resolve any issues you may experience\n\n"
                    "Do not report issues unless you have updated PygameExtra!"
                ))
        if os.path.exists('.git'):
            # Check for new commit
            try:
                branch = subprocess.check_output(
                    ["git", "branch", "--show-current"],
                    stderr=subprocess.DEVNULL
                ).strip().decode("utf-8")

                if not branch:
                    raise GitCheckException("No branch found")

                # Fetch remote changes
                subprocess.run(["git", "fetch"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # Compare local and remote branch
                status = subprocess.check_output(["git", "status", "-sb"]).strip().decode('utf-8')
                if '[behind' in status:
                    self.warnings.put(WarningPopup(
                        self.parent_context,
                        "New commits available!",
                        "There are new commits available for this branch.\n"
                        "Please pull the changes to stay up to date.\n\n"
                        "Do not report issues unless you have pulled the changes!"
                    ))
                elif '[ahead' in status and not self.config.debug:
                    self.warnings.put(WarningPopup(
                        self.parent_context,
                        "You've created new commits!",
                        "Can't wait for you to share them!\n"
                        "Disable this message by enabling debug.\n\n"
                        "Do not report issues unless you have pushed these changes!"
                    ))
            except (FileNotFoundError, GitCheckException):
                self.warnings.put(WarningPopup(
                    self.parent_context,
                    "Failed to check for updates.",
                    "Failed to check for updates, please check manually for any new commits."
                ))
        for extension_name in os.listdir(Defaults.EXTENSIONS_DIR):
            if extension_name.endswith('.zip'):
                extension_directory = os.path.join(Defaults.EXTENSIONS_DIR, extension_name[:-4])
                self.warnings.put(InstallPopup(
                    self.parent_context, "Install extension from zip?",
                    f"Moss has found a zip file in the extensions directory.\n"
                    "Please make sure you trust this extension before installing it!\n\n"
                    f"Would you like to install and enable {extension_name}?",
                    partial(
                        self.extract_zip,
                        os.path.join(Defaults.EXTENSIONS_DIR, extension_name),
                        extension_directory
                    )
                ))

    def extract_zip(self, zip_path: str, extension_directory: str):
        extension_name = os.path.basename(extension_directory)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extension_directory)
        self.config.extensions[extension_name] = True
        os.remove(zip_path)

    def close(self):
        self.api.remove_hook('version_checker_resize_check')
        self.close_screen()

    def loop(self):
        self.logo.display()
        if not self.checked:
            self.check()
        if len(self.warnings.queue) > 0:
            self.warnings.queue[0]()
            if self.warnings.queue[0].closed:
                self.warnings.get()
        else:
            self.close()
