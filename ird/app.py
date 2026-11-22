"""Application object, global actions and entry point."""

from __future__ import annotations

import logging
import sys
from importlib.resources import files
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, Gtk  # noqa: E402

from . import __app_icon__, __app_id__, __app_name__, __version__, util
from .config import Library, Settings
from .engine import DownloadManager
from .ui.window import MainWindow

log = logging.getLogger(__name__)

_THEME_SCHEMES = {
    "system": Adw.ColorScheme.DEFAULT,
    "light": Adw.ColorScheme.FORCE_LIGHT,
    "dark": Adw.ColorScheme.FORCE_DARK,
}


class Application(Adw.Application):
    def __init__(self) -> None:
        super().__init__(
            application_id=__app_id__,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )
        self.settings = Settings.load()
        self.library = Library()
        self.manager = DownloadManager(self.settings, self.library)
        self.window: MainWindow | None = None
        self.pending_urls: list[str] = []
        self.connect("startup", self._on_startup)
        self.connect("activate", self._on_activate)
        self.connect("command-line", self._on_command_line)
        self.connect("shutdown", self._on_shutdown)

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def _on_startup(self, *_args) -> None:
        self._apply_theme()
        self._load_css()
        self._install_icon_paths()
        self._install_actions()
        self._install_accels()
        try:
            Path(self.settings.download_dir).expanduser().mkdir(
                parents=True, exist_ok=True
            )
        except OSError:
            pass

    def _on_activate(self, *_args) -> None:
        if self.window is None:
            self.window = MainWindow(
                self,
                self.settings,
                self.library,
                self.manager,
                self.pending_urls,
            )
            self.pending_urls = []
        self.window.present()
        self.window.url_entry.grab_focus()

    def _on_command_line(self, _application, command_line) -> int:
        arguments = command_line.get_arguments()
        urls = util.extract_urls(" ".join(arguments[1:]))
        if urls:
            if self.window is not None:
                self.window.enqueue_urls(urls)
            else:
                self.pending_urls.extend(urls)
        self.activate()
        return 0

    def _on_shutdown(self, *_args) -> None:
        self.manager.shutdown()

    # ------------------------------------------------------------------ #
    # Theme, CSS, icons
    # ------------------------------------------------------------------ #

    def apply_theme(self) -> None:
        scheme = _THEME_SCHEMES.get(self.settings.theme, Adw.ColorScheme.DEFAULT)
        Adw.StyleManager.get_default().set_color_scheme(scheme)

    _apply_theme = apply_theme

    def _load_css(self) -> None:
        display = Gdk.Display.get_default()
        if display is None:
            return
        try:
            css = files("ird").joinpath("style.css").read_text(encoding="utf-8")
        except (OSError, ModuleNotFoundError):
            log.warning("style.css could not be loaded")
            return
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_display(
            display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _install_icon_paths(self) -> None:
        display = Gdk.Display.get_default()
        if display is None:
            return
        theme = Gtk.IconTheme.get_for_display(display)
        package_root = Path(__file__).resolve().parent
        for candidate in (package_root, package_root.parent):
            try:
                theme.add_search_path(str(candidate))
            except Exception:
                pass
        try:
            Gtk.Window.set_default_icon_name(__app_icon__)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def _install_actions(self) -> None:
        actions = {
            "preferences": self._present_preferences,
            "shortcuts": self._present_shortcuts,
            "about": self._present_about,
            "quit": self._request_quit,
        }
        for name, callback in actions.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            self.add_action(action)

    def _install_accels(self) -> None:
        accels = {
            "app.preferences": ["<Control>comma"],
            "app.shortcuts": ["<Control>question"],
            "app.quit": ["<Control>q"],
            "win.download": ["<Control>Return"],
            "win.focus-url": ["<Control>l"],
            "win.open-folder": ["<Control>o"],
            "win.clear-finished": ["<Control>Delete"],
        }
        for action, values in accels.items():
            self.set_accels_for_action(action, values)

    def _present_preferences(self, *_args) -> None:
        if self.window is not None:
            self.window.present_preferences()

    def _request_quit(self, *_args) -> None:
        if self.window is not None:
            self.window.close()
        else:
            self.quit()

    def _present_shortcuts(self, *_args) -> None:
        dialog = Adw.PreferencesDialog()
        dialog.set_title("Keyboard Shortcuts")
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup()

        shortcuts = [
            ("Download links", "Ctrl+Enter"),
            ("Focus the link field", "Ctrl+L"),
            ("Paste from clipboard", "Ctrl+V"),
            ("Open downloads folder", "Ctrl+O"),
            ("Clear finished downloads", "Ctrl+Delete"),
            ("Preferences", "Ctrl+,"),
            ("This shortcut sheet", "Ctrl+?"),
            ("Quit", "Ctrl+Q"),
        ]
        for title, accel in shortcuts:
            row = Adw.ActionRow(title=title)
            label = Gtk.Label(label=accel)
            label.add_css_class("shortcut-label")
            row.add_suffix(label)
            group.add(row)
        page.add(group)
        dialog.add(page)
        dialog.present(self.window)

    def _present_about(self, *_args) -> None:
        about = Adw.AboutWindow(transient_for=self.window)
        about.set_application_name(__app_name__)
        about.set_application_icon(__app_icon__)
        about.set_version(__version__)
        about.set_developer_name("Aznit11")
        about.set_comments(
            "A fast, native downloader for Instagram reels, built with GTK 4 and libadwaita."
        )
        about.set_website("https://github.com/Aznit11/instagram-reels-downloader")
        about.set_issue_url(
            "https://github.com/Aznit11/instagram-reels-downloader/issues"
        )
        about.set_license_type(Gtk.License.MIT_X11)
        about.set_developers(["Aznit11"])
        try:
            about.add_credit_section("Built with", ["GTK 4", "libadwaita", "yt-dlp"])
        except Exception:
            pass
        about.present()


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
    args = list(sys.argv if argv is None else argv)
    app = Application()
    return app.run(args)
