import os
import shutil
import subprocess
import sys
import threading
from typing import TYPE_CHECKING, Dict

import pygameextra as pe

from gui.events import ResizeEvent
from gui.screens.mixins import LogoMixin

if os.name == 'nt':
    import winshell

from gui import APP_NAME, INSTALL_DIR, USER_DATA_DIR
from gui.defaults import Defaults

if TYPE_CHECKING:
    from gui import GUI
    from rm_api import API


class Installer(pe.ChildContext, LogoMixin):
    LAYER = pe.AFTER_LOOP_LAYER
    icons: Dict[str, pe.Image]
    api: 'API'

    logo: pe.Text
    line_rect: pe.Rect
    cancel_button_rect: pe.Rect
    install_button_rect: pe.Rect
    EVENT_HOOK_NAME = 'installer_resize_check'

    def __init__(self, parent: 'GUI'):
        self.installing = False
        super().__init__(parent)
        # Initialize the texts
        (
            self.cancel_text,
            self.install_text,
            self.reinstall_text,
            self.launch_text
        ) = tuple(
            pe.Text(
                text,
                Defaults.INSTALLER_FONT, self.ratios.installer_buttons_size,
                colors=Defaults.TEXT_COLOR_T
            ) for text in (
                "Cancel",
                "Install",
                "Reinstall",
                "Launch"
            )
        )
        self.calculate_texts()
        self.api.add_hook(self.EVENT_HOOK_NAME, self.resize_check_hook)
        self.total = 0
        self.progress = 0
        self.just_installed = False

    def resize_check_hook(self, event):
        if isinstance(event, ResizeEvent):
            self.calculate_texts()

    def calculate_texts(self):
        super().initialize_logo_and_line()
        buttons_rect = pe.Rect(0, 0, self.ratios.installer_buttons_width, self.ratios.installer_buttons_height)
        buttons_rect.midtop = self.line_rect.midtop
        self.cancel_button_rect = buttons_rect.scale_by(.5, 1)
        self.cancel_button_rect.width -= self.ratios.installer_buttons_padding // 2
        self.cancel_button_rect.left = buttons_rect.left
        self.install_button_rect = self.cancel_button_rect.copy()
        self.install_button_rect.right = buttons_rect.right

    def draw_button_outline(self, rect):
        pe.draw.rect(Defaults.LINE_GRAY, rect, self.ratios.pixel(3))

    def loop(self):
        self.logo.display()
        if self.installing:
            pe.draw.rect(pe.colors.black, self.line_rect, 1)
            progress_rect = self.line_rect.copy()
            progress_rect.width *= self.progress / self.total
            pe.draw.rect(pe.colors.black, progress_rect, 0)
        elif not self.just_installed:
            pe.button.rect(
                self.cancel_button_rect,
                Defaults.TRANSPARENT_COLOR, Defaults.BUTTON_ACTIVE_COLOR,
                action=self.cancel,
                text=self.cancel_text,
                name='installer.cancel'
            )
            can_install = self.check_can_install()
            pe.button.rect(
                self.install_button_rect,
                Defaults.TRANSPARENT_COLOR if can_install else Defaults.BUTTON_DISABLED_COLOR,
                Defaults.BUTTON_ACTIVE_COLOR,
                action=self.install,
                text=self.install_text if not Defaults.INSTALLED else self.reinstall_text,
                disabled=not can_install,
                name='installer.install'
            )
            self.draw_button_outline(self.cancel_button_rect)
            self.draw_button_outline(self.install_button_rect)
        else:
            pe.button.rect(
                self.install_button_rect,
                Defaults.TRANSPARENT_COLOR, Defaults.BUTTON_ACTIVE_COLOR,
                action=self.launch,
                text=self.launch_text,
                name='installer.launch'
            )
            self.draw_button_outline(self.install_button_rect)

    def cancel(self):
        self.api.remove_hook(self.EVENT_HOOK_NAME)
        self.close_screen()

    def install_thread(self):
        self.installing = True

        for root, dirs, files in (os.walk(self.from_directory) if not self.config.debug else ()):
            rel_path = os.path.relpath(root, self.from_directory)
            dest_path = os.path.join(self.to_directory, rel_path)
            os.makedirs(dest_path, exist_ok=True)

            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dest_path, file)

                print(f"COPY FROM: {src_file}\nTO: {dst_file}\n")
                try:
                    shutil.copy2(src_file, dst_file)
                except shutil.SameFileError:
                    pass
                self.progress += 1
        self.make_shortcut()
        self.add_to_path()
        self.add_to_start()
        print()
        self.copy_config()

        with open(os.path.join(self.to_directory, "installed"), 'w') as f:
            f.write("Installed")
            print("Installed!")
        self.installing = False

        self.just_installed = True
        Defaults.INSTALLED = True

    def make_shortcut(self):
        if os.name == 'nt':
            desktop = winshell.desktop()
            path = os.path.join(desktop, f"{APP_NAME}.lnk")
            self.make_link(path)
        elif os.name == 'posix':
            path = "/usr/share/applications"
            os.makedirs(path, exist_ok=True)
            path = os.path.join(path, f"{APP_NAME}.desktop")
            with open(path, 'w') as f:
                f.write(
                    "[Desktop Entry]"
                    f"Name={APP_NAME}"
                    f"Exec={os.path.join(INSTALL_DIR, 'moss.bin')}"
                    f"Path={INSTALL_DIR}"
                    f"Icon={os.path.join(INSTALL_DIR, 'assets', 'icons', 'moss.png')}"
                    "Type=Application"
                    "Categories=Utility;")

    def add_to_path(self):
        if os.name == 'nt':
            import winreg
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Environment")
            path = winreg.QueryValueEx(key, "PATH")[0]
            if not INSTALL_DIR in path:
                if path.endswith(";"):
                    path += INSTALL_DIR + ";"
                else:
                    path += f";{INSTALL_DIR}"
                winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, path)
            winreg.CloseKey(key)
        elif os.name == 'posix':
            try:
                os.symlink(os.path.join(INSTALL_DIR, "moss.bin"), "/usr/local/bin/moss")
            except FileExistsError:
                pass

    def make_link(self, path):
        print(f"Making a shortcut to moss: {path}")
        with winshell.shortcut(path) as link:
            link.path = os.path.join(INSTALL_DIR, "moss.exe")
            link.icon_location = (os.path.join(INSTALL_DIR, "assets", "icons", "moss.ico"), 0)
            link.description = APP_NAME
            link.working_directory = INSTALL_DIR

    def add_to_start(self):
        if os.name == 'nt':
            import winshell
            start = winshell.start_menu()
            # Also make a folder for it
            path = os.path.join(start, APP_NAME)
            os.makedirs(path, exist_ok=True)
            path = os.path.join(path, f"{APP_NAME}.lnk")
            self.make_link(path)

    def copy_config(self):
        os.makedirs(USER_DATA_DIR, exist_ok=True)

        if os.path.exists(Defaults.TOKEN_FILE_PATH) and not os.path.exists(to := os.path.join(USER_DATA_DIR, 'token')):
            print(f"COPY FROM: {Defaults.TOKEN_FILE_PATH}\nTO: {to}\n")
            try:
                shutil.copy2(Defaults.TOKEN_FILE_PATH, to)
            except shutil.SameFileError:
                pass
        if os.path.exists(Defaults.CONFIG_FILE_PATH) and not os.path.exists(
                to := os.path.join(USER_DATA_DIR, 'config.json')):
            print(f"COPY FROM: {Defaults.CONFIG_FILE_PATH}\nTO: {to}\n")
            try:
                shutil.copy2(Defaults.CONFIG_FILE_PATH, to)
            except shutil.SameFileError:
                pass

    def install(self):
        self.total = sum([len(files) for _, _, files in os.walk(self.from_directory)])
        threading.Thread(target=self.install_thread, daemon=False).start()

    def launch(self):
        # Launch and close the installer'
        if os.name == 'nt':
            subprocess.Popen(
                [os.path.join(INSTALL_DIR, "moss.exe")],
                cwd=INSTALL_DIR,
                # creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                start_new_session=True
            )
        elif os.name == 'posix':
            subprocess.Popen(
                [os.path.join(INSTALL_DIR, "moss.bin")],
                cwd=INSTALL_DIR,
                start_new_session=True
            )
        sys.exit()

    @staticmethod
    def check_can_install():
        if os.name == 'posix':
            # Check for sudo
            return os.getuid() == 0
        return True

    @property
    def from_directory(self):
        return Defaults.BASE_ASSET_DIR

    @property
    def to_directory(self):
        return INSTALL_DIR
