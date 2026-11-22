"""Preferences dialog (libadwaita)."""

from __future__ import annotations

from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402

from ..config import (
    BROWSERS,
    COOKIE_MODES,
    COOKIE_MODE_LABELS,
    QUALITY_LABELS,
    QUALITY_ORDER,
    THEME_KEYS,
    THEME_LABELS,
    Settings,
)


class PreferencesDialog(Adw.PreferencesDialog):
    def __init__(self, window, settings: Settings, controller) -> None:
        super().__init__()
        self._window = window
        self._settings = settings
        self._controller = controller
        self.set_title("Preferences")
        self.set_search_enabled(True)
        try:
            self.set_content_width(640)
            self.set_content_height(640)
        except Exception:
            pass

        self._build_downloads_page()
        self._build_account_page()
        self._build_appearance_page()
        self._build_behavior_page()
        self._build_library_page()

    # ------------------------------------------------------------------ #
    # Pages
    # ------------------------------------------------------------------ #

    def _build_downloads_page(self) -> None:
        page = Adw.PreferencesPage(
            title="Downloads", icon_name="folder-download-symbolic"
        )
        group = Adw.PreferencesGroup(title="Destination")

        self.folder_row = Adw.ActionRow(
            title="Download folder", subtitle=self._settings.download_dir
        )
        self.folder_row.set_subtitle_lines(2)
        browse = Gtk.Button(label="Browse…")
        browse.add_css_class("flat")
        browse.set_valign(Gtk.Align.CENTER)
        browse.connect("clicked", self._choose_folder)
        self.folder_row.add_suffix(browse)
        group.add(self.folder_row)
        self.folder_row.set_activatable_widget(browse)
        page.add(group)

        quality_group = Adw.PreferencesGroup(title="Quality")
        self.quality_row = Adw.ComboRow(title="Default quality")
        self.quality_row.set_model(
            Gtk.StringList.new([QUALITY_LABELS[key] for key in QUALITY_ORDER])
        )
        self.quality_row.set_selected(self._index(QUALITY_ORDER, self._settings.quality))
        self.quality_row.connect("notify::selected", self._on_quality_changed)
        quality_group.add(self.quality_row)

        self.concurrency_row = Adw.SpinRow.new_with_range(1, 6, 1)
        self.concurrency_row.set_title("Simultaneous downloads")
        self.concurrency_row.set_subtitle("Higher values download more reels at once.")
        self.concurrency_row.set_value(self._settings.concurrency)
        self.concurrency_row.connect("notify::value", self._on_concurrency_changed)
        page.add(quality_group)

        performance_group = Adw.PreferencesGroup(title="Performance")
        performance_group.add(self.concurrency_row)
        page.add(performance_group)

        self.add(page)

    def _build_account_page(self) -> None:
        page = Adw.PreferencesPage(
            title="Account", icon_name="dialog-password-symbolic"
        )
        group = Adw.PreferencesGroup(
            title="Instagram cookies",
            description=(
                "Instagram often requires a logged-in session. Importing cookies from "
                "your browser lets you download reels you can already see."
            ),
        )

        self.cookie_mode_row = Adw.ComboRow(title="Authentication")
        self.cookie_mode_row.set_model(
            Gtk.StringList.new([COOKIE_MODE_LABELS[mode] for mode in COOKIE_MODES])
        )
        self.cookie_mode_row.set_selected(
            self._index(COOKIE_MODES, self._settings.cookies_mode)
        )
        self.cookie_mode_row.connect("notify::selected", self._on_cookie_mode_changed)
        group.add(self.cookie_mode_row)

        self.browser_row = Adw.ComboRow(title="Browser")
        self.browser_row.set_model(
            Gtk.StringList.new([browser.capitalize() for browser in BROWSERS])
        )
        self.browser_row.set_selected(
            self._index(BROWSERS, self._settings.cookies_browser)
        )
        self.browser_row.connect("notify::selected", self._on_browser_changed)
        group.add(self.browser_row)

        self.cookie_file_row = Adw.ActionRow(
            title="Cookies file",
            subtitle=self._settings.cookies_file or "No file selected",
        )
        self.cookie_file_row.set_subtitle_lines(2)
        pick_button = Gtk.Button(label="Choose…")
        pick_button.add_css_class("flat")
        pick_button.set_valign(Gtk.Align.CENTER)
        pick_button.connect("clicked", self._choose_cookies_file)
        self.cookie_file_row.add_suffix(pick_button)
        self.cookie_file_row.set_activatable_widget(pick_button)
        group.add(self.cookie_file_row)

        self._update_cookie_rows()
        page.add(group)

        tip = Adw.PreferencesGroup()
        tip_row = Adw.ActionRow(
            title="Tip",
            subtitle=(
                "Firefox works most reliably. Close private windows and stay logged in "
                "to instagram.com in the selected browser."
            ),
        )
        tip_row.set_subtitle_lines(3)
        tip.add(tip_row)
        page.add(tip)

        self.add(page)

    def _build_appearance_page(self) -> None:
        page = Adw.PreferencesPage(
            title="Appearance", icon_name="applications-graphics-symbolic"
        )
        group = Adw.PreferencesGroup(title="Theme")
        self.theme_row = Adw.ComboRow(title="Color scheme")
        self.theme_row.set_model(
            Gtk.StringList.new([THEME_LABELS[key] for key in THEME_KEYS])
        )
        self.theme_row.set_selected(self._index(THEME_KEYS, self._settings.theme))
        self.theme_row.connect("notify::selected", self._on_theme_changed)
        group.add(self.theme_row)
        page.add(group)
        self.add(page)

    def _build_behavior_page(self) -> None:
        page = Adw.PreferencesPage(
            title="Behavior", icon_name="preferences-system-symbolic"
        )
        group = Adw.PreferencesGroup(title="After a download")

        self.notifications_row = self._switch_row(
            "Desktop notifications",
            "Show a notification when a reel finishes while the window is in the background.",
            self._settings.notifications,
            self._on_notifications_changed,
        )
        group.add(self.notifications_row)

        self.clipboard_row = self._switch_row(
            "Clipboard suggestions",
            "Offer to paste a reel link found on the clipboard when the window is focused.",
            self._settings.clipboard_hint,
            self._on_clipboard_changed,
        )
        group.add(self.clipboard_row)

        self.metadata_row = self._switch_row(
            "Embed metadata",
            "Write the title, uploader and description into the media file.",
            self._settings.embed_metadata,
            self._on_metadata_changed,
        )
        group.add(self.metadata_row)

        self.thumbnail_row = self._switch_row(
            "Embed thumbnail",
            "Embed the cover image into video files (slightly slower).",
            self._settings.embed_thumbnail,
            self._on_thumbnail_changed,
        )
        group.add(self.thumbnail_row)
        page.add(group)
        self.add(page)

    def _build_library_page(self) -> None:
        page = Adw.PreferencesPage(title="Library", icon_name="document-open-recent-symbolic")
        group = Adw.PreferencesGroup(title="Download history")
        row = Adw.ActionRow(
            title="Clear download history",
            subtitle="Files on disk are kept. This only clears the library view.",
        )
        clear_button = Gtk.Button(label="Clear")
        clear_button.add_css_class("destructive-action")
        clear_button.set_valign(Gtk.Align.CENTER)
        clear_button.connect("clicked", lambda *_: self._controller.confirm_clear_history())
        row.add_suffix(clear_button)
        row.set_activatable_widget(clear_button)
        group.add(row)
        page.add(group)
        self.add(page)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _index(values, value) -> int:
        try:
            return values.index(value)
        except ValueError:
            return 0

    @staticmethod
    def _switch_row(title: str, subtitle: str, active: bool, callback) -> Adw.SwitchRow:
        row = Adw.SwitchRow(title=title, subtitle=subtitle)
        row.set_active(active)
        row.connect("notify::active", callback)
        return row

    def _save(self) -> None:
        self._settings.save()
        try:
            self._controller.apply_settings()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Callbacks
    # ------------------------------------------------------------------ #

    def _choose_folder(self, *_args) -> None:
        dialog = Gtk.FileDialog(title="Choose a download folder")
        try:
            dialog.set_initial_folder(
                Gio.File.new_for_path(str(Path(self._settings.download_dir).expanduser()))
            )
        except Exception:
            pass
        dialog.select_folder(self.get_root(), None, self._on_folder_selected)

    def _on_folder_selected(self, dialog, result) -> None:
        try:
            folder = dialog.select_folder_finish(result)
        except GLib.Error:
            return
        if not folder:
            return
        path = folder.get_path()
        if path:
            self._settings.download_dir = path
            self.folder_row.set_subtitle(path)
            self._save()

    def _choose_cookies_file(self, *_args) -> None:
        dialog = Gtk.FileDialog(title="Choose a cookies.txt file")
        try:
            dialog.set_initial_folder(Gio.File.new_for_path(str(Path.home())))
        except Exception:
            pass
        dialog.open(self.get_root(), None, self._on_cookies_file_selected)

    def _on_cookies_file_selected(self, dialog, result) -> None:
        try:
            file = dialog.open_finish(result)
        except GLib.Error:
            return
        if file and file.get_path():
            self._settings.cookies_file = file.get_path()
            self.cookie_file_row.set_subtitle(file.get_path())
            self._settings.cookies_mode = "file"
            self.cookie_mode_row.set_selected(self._index(COOKIE_MODES, "file"))
            self._update_cookie_rows()
            self._save()

    def _on_quality_changed(self, row, _pspec) -> None:
        index = row.get_selected()
        if 0 <= index < len(QUALITY_ORDER):
            self._settings.quality = QUALITY_ORDER[index]
            self._save()

    def _on_concurrency_changed(self, row, _pspec) -> None:
        value = int(round(row.get_value()))
        if value != self._settings.concurrency:
            self._settings.concurrency = max(1, min(6, value))
            self._save()

    def _on_cookie_mode_changed(self, row, _pspec) -> None:
        index = row.get_selected()
        if 0 <= index < len(COOKIE_MODES):
            self._settings.cookies_mode = COOKIE_MODES[index]
            self._update_cookie_rows()
            self._save()

    def _on_browser_changed(self, row, _pspec) -> None:
        index = row.get_selected()
        if 0 <= index < len(BROWSERS):
            self._settings.cookies_browser = BROWSERS[index]
            self._save()

    def _on_theme_changed(self, row, _pspec) -> None:
        index = row.get_selected()
        if 0 <= index < len(THEME_KEYS):
            self._settings.theme = THEME_KEYS[index]
            self._save()
            self._controller.apply_theme()

    def _on_notifications_changed(self, row, _pspec) -> None:
        self._settings.notifications = row.get_active()
        self._save()

    def _on_clipboard_changed(self, row, _pspec) -> None:
        self._settings.clipboard_hint = row.get_active()
        self._save()

    def _on_metadata_changed(self, row, _pspec) -> None:
        self._settings.embed_metadata = row.get_active()
        self._save()

    def _on_thumbnail_changed(self, row, _pspec) -> None:
        self._settings.embed_thumbnail = row.get_active()
        self._save()

    def _update_cookie_rows(self) -> None:
        mode = self._settings.cookies_mode
        self.browser_row.set_visible(mode == "browser")
        self.cookie_file_row.set_visible(mode == "file")
