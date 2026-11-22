"""Main application window."""

from __future__ import annotations

import logging
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, GLib, Gtk, Pango  # noqa: E402

from .. import __app_icon__, __app_name__, util
from ..config import (
    QUALITY_LABELS,
    QUALITY_ORDER,
    Library,
    Settings,
)
from ..engine import ACTIVE_STATUSES, DownloadManager
from . import widgets

log = logging.getLogger(__name__)


class DownloadRow(Gtk.ListBoxRow):
    """One row in the download queue."""

    def __init__(self, job_id: str, callbacks: dict) -> None:
        super().__init__()
        self.set_activatable(False)
        self.set_selectable(False)
        self.job_id = job_id
        self._callbacks = callbacks
        self._job: dict = {}
        self._meta_text = ""
        self._status_text = ""
        self._thumb_path = ""
        self._status_class = ""

        self.add_css_class("queue-row")

        outer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        outer.set_margin_top(10)
        outer.set_margin_bottom(10)
        outer.set_margin_start(12)
        outer.set_margin_end(8)

        self._thumb = widgets.thumbnail_box("", 56)
        outer.append(self._thumb)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        info.set_hexpand(True)
        info.set_valign(Gtk.Align.CENTER)

        self._title = Gtk.Label()
        self._title.set_xalign(0)
        self._title.set_ellipsize(Pango.EllipsizeMode.END)
        self._title.set_single_line_mode(True)
        self._title.add_css_class("row-title")
        info.append(self._title)

        self._meta = Gtk.Label()
        self._meta.set_xalign(0)
        self._meta.set_ellipsize(Pango.EllipsizeMode.END)
        self._meta.set_single_line_mode(True)
        self._meta.add_css_class("dim-label")
        self._meta.add_css_class("caption")
        info.append(self._meta)

        self._status = Gtk.Label()
        self._status.set_xalign(0)
        self._status.set_ellipsize(Pango.EllipsizeMode.END)
        self._status.set_single_line_mode(True)
        self._status.add_css_class("caption")
        info.append(self._status)

        self._progress = Gtk.ProgressBar()
        self._progress.set_show_text(False)
        self._progress.add_css_class("download-progress")
        self._progress.set_visible(False)
        info.append(self._progress)

        outer.append(info)

        trailing = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        trailing.set_valign(Gtk.Align.CENTER)

        self._spinner = Adw.Spinner()
        self._spinner.set_size_request(18, 18)
        self._spinner.set_visible(False)
        trailing.append(self._spinner)

        self._cancel_btn = widgets.flat_icon_button(
            "process-stop-symbolic",
            "Cancel download",
            lambda: self._callbacks["cancel"](self.job_id),
        )
        trailing.append(self._cancel_btn)

        self._open_btn = widgets.flat_icon_button(
            "folder-open-symbolic",
            "Open file",
            lambda: self._callbacks["open"](self._job),
        )
        trailing.append(self._open_btn)

        self._retry_btn = widgets.flat_icon_button(
            "view-refresh-symbolic",
            "Retry download",
            lambda: self._callbacks["retry"](self.job_id),
        )
        trailing.append(self._retry_btn)

        self._remove_btn = widgets.flat_icon_button(
            "window-close-symbolic",
            "Remove from list",
            lambda: self._callbacks["remove"](self.job_id),
        )
        trailing.append(self._remove_btn)

        outer.append(trailing)
        self.set_child(outer)

    def update(self, job: dict) -> None:
        self._job = job
        title = job.get("title") or util.short_url(job.get("url", ""))
        if title != self._title.get_label():
            self._title.set_label(title)
            self.set_tooltip_text(title)

        status = job.get("status", "")
        progress = float(job.get("progress") or 0.0)
        downloaded = int(job.get("downloaded") or 0)
        total = int(job.get("total") or 0)
        speed = float(job.get("speed") or 0.0)
        eta = int(job.get("eta") or 0)

        meta_parts: list[str] = []
        if job.get("uploader"):
            meta_parts.append(str(job["uploader"]))
        if job.get("duration"):
            meta_parts.append(util.human_duration(job["duration"]))
        quality_label = QUALITY_LABELS.get(job.get("quality", ""), "")
        if quality_label:
            meta_parts.append(quality_label)
        meta_text = " · ".join(meta_parts)
        if meta_text != self._meta_text:
            self._meta_text = meta_text
            self._meta.set_label(meta_text)
            self._meta.set_visible(bool(meta_text))

        status_text = ""
        status_class = ""
        if status == "preparing":
            status_text = "Fetching video info…"
        elif status == "queued":
            status_text = "Waiting for a download slot…"
        elif status == "downloading":
            if total:
                status_text = f"{util.human_size(downloaded)} of {util.human_size(total)}"
            elif downloaded:
                status_text = f"{util.human_size(downloaded)} downloaded…"
            else:
                status_text = "Starting download…"
            if speed:
                status_text += f" · {util.human_speed(speed)}"
            if eta:
                status_text += f" · {util.human_duration(eta)} left"
        elif status == "processing":
            status_text = "Finishing up…"
        elif status == "cancelling":
            status_text = "Cancelling…"
        elif status == "done":
            status_text = f"Downloaded · {util.human_size(job.get('size'))}"
            status_class = "success-text"
        elif status == "duplicate":
            status_text = "Already in your library"
            status_class = "accent-text"
        elif status == "cancelled":
            status_text = "Cancelled"
            status_class = "dim-label"
        elif status == "error":
            status_text = job.get("error") or "Download failed"
            status_class = "error-text"
            self._status.set_tooltip_text(status_text)

        if status_text != self._status_text:
            self._status_text = status_text
            self._status.set_label(status_text)
            self._status.set_visible(bool(status_text))
        if status_class != self._status_class:
            for css_class in ("success-text", "accent-text", "error-text", "dim-label"):
                self._status.remove_css_class(css_class)
            if status_class:
                self._status.add_css_class(status_class)
            self._status_class = status_class

        active = status in ACTIVE_STATUSES and status != "cancelling"
        self._spinner.set_visible(active)
        self._cancel_btn.set_visible(status in ACTIVE_STATUSES)
        self._cancel_btn.set_sensitive(status != "cancelling")
        self._open_btn.set_visible(status in {"done", "duplicate"})
        self._retry_btn.set_visible(status in {"error", "cancelled"})
        self._remove_btn.set_visible(status not in ACTIVE_STATUSES)

        if status == "downloading":
            self._progress.set_visible(True)
            if total > 0:
                self._progress.set_fraction(max(0.0, min(1.0, progress)))
            else:
                self._progress.pulse()
        else:
            self._progress.set_visible(False)

        thumb_path = job.get("thumbnail_path") or ""
        if thumb_path != self._thumb_path:
            self._thumb_path = thumb_path
            widgets.fill_thumbnail(self._thumb, thumb_path, 56)


class MainWindow(Adw.ApplicationWindow):
    def __init__(
        self,
        application: Adw.Application,
        settings: Settings,
        library: Library,
        manager: DownloadManager,
        pending_urls: list[str] | None = None,
    ) -> None:
        super().__init__(application=application)
        self.settings = settings
        self.library = library
        self.engine = manager
        self._pending_urls = pending_urls or []
        self._rows: dict[str, DownloadRow] = {}
        self._history_map: dict[Gtk.ListBoxRow, dict] = {}
        self._history_version = -1
        self._tick_source: int | None = None
        self._preview_timer: int | None = None
        self._preview_url = ""
        self._preview_meta: dict | None = None
        self._preview_thumb = ""
        self._hint_text = ""
        self._hint_kind = ""
        self._seen_status: dict[str, str] = {}
        self._closing = False
        self._clipboard = Gdk.Display.get_default().get_clipboard()

        self.set_title(__app_name__)
        self.set_default_size(940, 780)
        self.set_size_request(560, 580)

        self._build_ui()
        self._install_actions()
        self._connect_signals()
        self._install_dnd()

        self._tick_source = GLib.timeout_add(120, self._tick)
        self._refresh_history()
        self._sync_queue(self.engine.snapshot())

        if self._pending_urls:
            self._enqueue(self._pending_urls)
            self._pending_urls = []

        self.url_entry.grab_focus()

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        self.overlay = Adw.ToastOverlay()
        self.set_content(self.overlay)

        self.toolbar_view = Adw.ToolbarView()
        self.overlay.set_child(self.toolbar_view)

        self.header = Adw.HeaderBar()
        self.view_stack = Adw.ViewStack()
        self.switcher_title = Adw.ViewSwitcherTitle(
            title=__app_name__, stack=self.view_stack
        )
        self.header.set_title_widget(self.switcher_title)
        self.toolbar_view.add_top_bar(self.header)

        menu = Gio.Menu()
        menu.append("Preferences", "app.preferences")
        menu.append("Keyboard Shortcuts", "app.shortcuts")
        menu.append("Open Downloads Folder", "win.open-folder")
        menu.append("About Instagram Reels Downloader", "app.about")
        self.menu_button = Gtk.MenuButton(
            icon_name="open-menu-symbolic", menu_model=menu
        )
        self.menu_button.add_css_class("flat")
        self.menu_button.set_tooltip_text("Main menu")
        self.header.pack_end(self.menu_button)

        queue_page = self.view_stack.add_titled(
            self._build_queue_page(), "queue", "Downloads"
        )
        history_page = self.view_stack.add_titled(
            self._build_history_page(), "history", "History"
        )
        queue_page.set_icon_name("folder-download-symbolic")
        history_page.set_icon_name("document-open-recent-symbolic")
        self.toolbar_view.set_content(self.view_stack)

    def _build_queue_page(self) -> Gtk.Widget:
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)

        clamp = Adw.Clamp(maximum_size=800, tightening_threshold=680)
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        page.set_margin_top(22)
        page.set_margin_bottom(32)
        page.set_margin_start(20)
        page.set_margin_end(20)
        clamp.set_child(page)
        scroller.set_child(clamp)
        self.queue_page = page

        self.ytdlp_banner = Adw.Banner(
            title="yt-dlp is not installed — downloads will not work.",
            button_label="Install guide",
            revealed=util.which_ytdlp() is None,
        )
        self.ytdlp_banner.connect(
            "button-clicked",
            lambda *_: util.open_uri("https://github.com/yt-dlp/yt-dlp#installation"),
        )
        page.append(self.ytdlp_banner)

        # Hero / input card -------------------------------------------------
        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        hero.add_css_class("card")
        hero.add_css_class("hero-card")

        heading = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        logo = widgets.icon_image(__app_icon__, 38, "video-x-generic-symbolic")
        logo.set_valign(Gtk.Align.CENTER)
        heading.append(logo)

        titles = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title = Gtk.Label(label="Save a reel in seconds")
        title.set_xalign(0)
        title.add_css_class("hero-title")
        subtitle = Gtk.Label(label="Paste a link, choose a quality, done.")
        subtitle.set_xalign(0)
        subtitle.add_css_class("dim-label")
        titles.append(title)
        titles.append(subtitle)
        heading.append(titles)
        hero.append(heading)

        entry_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.url_entry = Gtk.Entry()
        self.url_entry.set_hexpand(True)
        self.url_entry.set_placeholder_text("https://www.instagram.com/reel/…")
        self.url_entry.set_input_purpose(Gtk.InputPurpose.URL)
        self.url_entry.add_css_class("url-entry")
        entry_row.append(self.url_entry)

        self.paste_button = widgets.flat_icon_button(
            "edit-paste-symbolic", "Paste from clipboard", self._paste_from_clipboard
        )
        self.paste_button.set_valign(Gtk.Align.CENTER)
        entry_row.append(self.paste_button)
        hero.append(entry_row)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.quality_dropdown = Gtk.DropDown.new_from_strings(
            [QUALITY_LABELS[key] for key in QUALITY_ORDER]
        )
        self.quality_dropdown.set_tooltip_text("Download quality")
        self.quality_dropdown.set_size_request(170, -1)
        try:
            selected = QUALITY_ORDER.index(self.settings.quality)
        except ValueError:
            selected = 0
        self.quality_dropdown.set_selected(selected)
        actions.append(self.quality_dropdown)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        actions.append(spacer)

        self.download_button = widgets.icon_label_button(
            "folder-download-symbolic", "Download", ("suggested-action", "pill")
        )
        self.download_button.set_tooltip_text("Add to download queue (Ctrl+Enter)")
        self.download_button.set_size_request(150, -1)
        actions.append(self.download_button)
        hero.append(actions)

        self.hint_label = Gtk.Label()
        self.hint_label.set_xalign(0)
        self.hint_label.set_wrap(True)
        self.hint_label.set_visible(False)
        hero.append(self.hint_label)

        page.append(hero)

        # Preview card ------------------------------------------------------
        self.preview_revealer = Gtk.Revealer(
            transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN,
            transition_duration=220,
        )
        preview = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        preview.add_css_class("card")
        preview.add_css_class("preview-card")

        self.preview_thumb = widgets.thumbnail_box("", 104, "video-x-generic-symbolic")
        preview.append(self.preview_thumb)

        preview_info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        preview_info.set_valign(Gtk.Align.CENTER)
        preview_info.set_hexpand(True)
        self.preview_title = Gtk.Label()
        self.preview_title.set_xalign(0)
        self.preview_title.set_wrap(True)
        self.preview_title.set_lines(2)
        self.preview_title.set_ellipsize(Pango.EllipsizeMode.END)
        self.preview_title.add_css_class("preview-title")
        preview_info.append(self.preview_title)

        self.preview_meta = Gtk.Label()
        self.preview_meta.set_xalign(0)
        self.preview_meta.set_ellipsize(Pango.EllipsizeMode.END)
        self.preview_meta.set_single_line_mode(True)
        self.preview_meta.add_css_class("dim-label")
        preview_info.append(self.preview_meta)

        self.preview_badge = Gtk.Label()
        self.preview_badge.set_xalign(0)
        self.preview_badge.add_css_class("warning-text")
        self.preview_badge.set_visible(False)
        preview_info.append(self.preview_badge)
        preview.append(preview_info)

        self.preview_spinner = Adw.Spinner()
        self.preview_spinner.set_size_request(20, 20)
        self.preview_spinner.set_valign(Gtk.Align.CENTER)
        self.preview_spinner.set_visible(False)
        preview.append(self.preview_spinner)

        self.preview_revealer.set_child(preview)
        page.append(self.preview_revealer)

        # Queue -------------------------------------------------------------
        queue_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        queue_title = Gtk.Label(label="Downloads")
        queue_title.set_xalign(0)
        queue_title.add_css_class("section-title")
        queue_header.append(queue_title)

        self.queue_count = Gtk.Label()
        self.queue_count.set_xalign(0)
        self.queue_count.add_css_class("dim-label")
        self.queue_count.add_css_class("caption")
        queue_header.append(self.queue_count)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        queue_header.append(spacer)

        self.clear_finished_btn = Gtk.Button()
        self.clear_finished_btn.set_icon_name("edit-clear-all-symbolic")
        self.clear_finished_btn.add_css_class("flat")
        self.clear_finished_btn.set_tooltip_text("Clear finished downloads")
        self.clear_finished_btn.set_visible(False)
        queue_header.append(self.clear_finished_btn)
        page.append(queue_header)

        self.queue_list = Gtk.ListBox()
        self.queue_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.queue_list.set_show_separators(False)
        self.queue_list.add_css_class("queue")
        self.queue_list.set_valign(Gtk.Align.START)

        self.queue_empty = self._empty_page(
            "folder-download-symbolic",
            "No downloads yet",
            "Paste an Instagram reel link above to start.",
        )
        self.queue_stack = Gtk.Stack(
            transition_type=Gtk.StackTransitionType.CROSSFADE,
            transition_duration=200,
        )
        self.queue_stack.add_named(self.queue_empty, "empty")
        self.queue_stack.add_named(self.queue_list, "list")
        self.queue_stack.set_visible_child_name("empty")
        page.append(self.queue_stack)

        bottom_space = Gtk.Box()
        bottom_space.set_size_request(-1, 8)
        page.append(bottom_space)
        return scroller

    def _build_history_page(self) -> Gtk.Widget:
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)

        clamp = Adw.Clamp(maximum_size=800, tightening_threshold=680)
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        page.set_margin_top(22)
        page.set_margin_bottom(32)
        page.set_margin_start(20)
        page.set_margin_end(20)
        clamp.set_child(page)
        scroller.set_child(clamp)
        self.history_page = page

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title = Gtk.Label(label="Library")
        title.set_xalign(0)
        title.add_css_class("section-title")
        header.append(title)

        self.history_count = Gtk.Label()
        self.history_count.set_xalign(0)
        self.history_count.add_css_class("dim-label")
        self.history_count.add_css_class("caption")
        header.append(self.history_count)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header.append(spacer)

        self.clear_history_btn = Gtk.Button()
        self.clear_history_btn.set_icon_name("user-trash-symbolic")
        self.clear_history_btn.add_css_class("flat")
        self.clear_history_btn.set_tooltip_text("Clear download history")
        self.clear_history_btn.set_visible(False)
        header.append(self.clear_history_btn)
        page.append(header)

        self.history_search = Gtk.SearchEntry()
        self.history_search.set_placeholder_text("Search your library…")
        self.history_search.connect("search-changed", lambda *_: self._refresh_history())
        page.append(self.history_search)

        self.history_list = Gtk.ListBox()
        self.history_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.history_list.set_show_separators(False)
        self.history_list.add_css_class("queue")
        self.history_list.set_valign(Gtk.Align.START)
        self.history_list.set_activate_on_single_click(True)

        self.history_empty = self._empty_page(
            "document-open-recent-symbolic",
            "Your library is empty",
            "Downloaded reels will appear here.",
        )
        self.history_stack = Gtk.Stack(
            transition_type=Gtk.StackTransitionType.CROSSFADE,
            transition_duration=200,
        )
        self.history_stack.add_named(self.history_empty, "empty")
        self.history_stack.add_named(self.history_list, "list")
        self.history_stack.set_visible_child_name("empty")
        page.append(self.history_stack)
        return scroller

    @staticmethod
    def _empty_page(icon_name: str, title: str, description: str) -> Adw.StatusPage:
        page = Adw.StatusPage(
            icon_name=icon_name, title=title, description=description
        )
        page.add_css_class("compact-status")
        return page

    # ------------------------------------------------------------------ #
    # Signals and actions
    # ------------------------------------------------------------------ #

    def _connect_signals(self) -> None:
        self.url_entry.connect("changed", self._on_entry_changed)
        self.url_entry.connect("activate", lambda *_: self._start_download())
        self.download_button.connect("clicked", lambda *_: self._start_download())
        self.quality_dropdown.connect("notify::selected", self._on_quality_changed)
        self.clear_finished_btn.connect("clicked", lambda *_: self._on_clear_finished())
        self.clear_history_btn.connect("clicked", lambda *_: self._confirm_clear_history())
        self.history_list.connect("row-activated", self._on_history_row_activated)
        self.connect("close-request", self._on_close_request)
        self.connect("notify::is-active", self._on_active_changed)
        self.connect("destroy", lambda *_: self._cleanup())

    def _install_actions(self) -> None:
        actions = {
            "download": (self._start_download, None),
            "focus-url": (self._focus_url, None),
            "open-folder": (self._open_download_folder, None),
            "clear-finished": (self._on_clear_finished, None),
            "history-open": (self._on_history_open, "s"),
            "history-folder": (self._on_history_folder, "s"),
            "history-copy": (self._on_history_copy, "s"),
            "history-remove": (self._on_history_remove, "s"),
            "history-delete": (self._on_history_delete, "s"),
        }
        for name, (callback, param_type) in actions.items():
            action = Gio.SimpleAction.new(
                name, GLib.VariantType.new(param_type) if param_type else None
            )
            action.connect("activate", callback)
            self.add_action(action)

    def _install_dnd(self) -> None:
        text_target = Gtk.DropTarget.new(str, Gdk.DragAction.COPY)
        text_target.connect("enter", self._on_drop_enter)
        text_target.connect("leave", self._on_drop_leave)
        text_target.connect("drop", self._on_drop_text)
        self.overlay.add_controller(text_target)

        try:
            file_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
            file_target.connect("enter", self._on_drop_enter)
            file_target.connect("leave", self._on_drop_leave)
            file_target.connect("drop", self._on_drop_files)
            self.overlay.add_controller(file_target)
        except TypeError:
            log.debug("Gdk.FileList drop target unavailable")

    def _on_drop_enter(self, *_args):
        self.overlay.add_css_class("drop-active")
        return Gdk.DragAction.COPY

    def _on_drop_leave(self, *_args):
        self.overlay.remove_css_class("drop-active")

    def _on_drop_text(self, _target, value, _x, _y) -> bool:
        self.overlay.remove_css_class("drop-active")
        urls = util.extract_urls(value)
        if urls:
            self._enqueue(urls)
            return True
        self._toast("That drop did not contain an Instagram reel link.")
        return False

    def _on_drop_files(self, _target, file_list, _x, _y) -> bool:
        self.overlay.remove_css_class("drop-active")
        urls: list[str] = []
        try:
            files = file_list.get_files()
        except AttributeError:
            files = []
        for gfile in files:
            uri = gfile.get_uri() or ""
            if uri.startswith(("http://", "https://")):
                urls.extend(util.extract_urls(uri))
            elif uri.endswith(".txt") and gfile.get_path():
                urls.extend(util.extract_urls(util.read_text_file(gfile.get_path())))
        if urls:
            self._enqueue(urls)
            return True
        return False

    # ------------------------------------------------------------------ #
    # Input handling
    # ------------------------------------------------------------------ #

    def _focus_url(self, *_args) -> None:
        self.url_entry.grab_focus()
        self.url_entry.select_region(0, -1)

    def _paste_from_clipboard(self) -> None:
        self._clipboard.read_text_async(None, self._on_paste_text)

    def _on_paste_text(self, clipboard, result) -> None:
        try:
            text = clipboard.read_text_finish(result)
        except GLib.Error:
            text = None
        if text:
            self.url_entry.set_text(text.strip()[:4096])
            self.url_entry.set_position(-1)
        else:
            self._toast("Clipboard is empty.")

    def _on_clipboard_hint_text(self, clipboard, result) -> None:
        if not self.settings.clipboard_hint or self.url_entry.get_text().strip():
            return
        try:
            text = clipboard.read_text_finish(result)
        except GLib.Error:
            return
        urls = util.extract_urls(text or "")
        if urls and not self.url_entry.get_text().strip():
            self._set_hint(
                f"📋 {len(urls)} reel link(s) in the clipboard — press the paste button or Ctrl+V.",
                "accent",
            )

    def _on_active_changed(self, *_args) -> None:
        if not self.get_property("is-active"):
            return
        if self.settings.clipboard_hint and not self.url_entry.get_text().strip():
            self._clipboard.read_text_async(None, self._on_clipboard_hint_text)

    def _on_entry_changed(self, *_args) -> None:
        self._cancel_preview_timer()
        text = self.url_entry.get_text().strip()
        if not text:
            self._preview_url = ""
            self._preview_meta = None
            self.preview_spinner.set_visible(False)
            self.preview_revealer.set_reveal_child(False)
            self._set_hint("", "")
            return

        urls = util.extract_urls(text)
        if not urls:
            self._preview_url = ""
            self._preview_meta = None
            self.preview_spinner.set_visible(False)
            self.preview_revealer.set_reveal_child(False)
            self._set_hint("That does not look like an Instagram reel link.", "error")
            return

        if len(urls) > 1:
            self._preview_url = ""
            self._preview_meta = None
            self.preview_spinner.set_visible(False)
            self.preview_revealer.set_reveal_child(False)
            self._set_hint(
                f"{len(urls)} links detected — all of them will be queued.", "accent"
            )
            return

        url = urls[0]
        if url != self._preview_url:
            self._preview_url = url
            self._preview_meta = None
            self._preview_thumb = ""
            self.preview_spinner.set_visible(False)
            self.preview_revealer.set_reveal_child(False)
            self._set_hint("", "")
            self._preview_timer = GLib.timeout_add(450, self._request_preview)
        else:
            self._set_hint("", "")

    def _request_preview(self) -> bool:
        self._preview_timer = None
        url = self._preview_url
        if url and url in self.url_entry.get_text():
            self.engine.request_preview(url)
            state = self.engine.preview(url)
            if not state or state.get("status") == "loading":
                if self._preview_meta is None:
                    self._show_preview_loading()
        return False

    def _show_preview_loading(self) -> None:
        self.preview_title.set_text("Fetching video info…")
        self.preview_meta.set_text("Reading the post from Instagram")
        self.preview_badge.set_visible(False)
        self.preview_spinner.set_visible(True)
        widgets.fill_thumbnail(self.preview_thumb, "", 104)
        self.preview_revealer.set_reveal_child(True)

    def _cancel_preview_timer(self) -> None:
        if self._preview_timer is not None:
            GLib.source_remove(self._preview_timer)
            self._preview_timer = None

    def _set_hint(self, text: str, kind: str) -> None:
        if text == self._hint_text and kind == self._hint_kind:
            return
        self._hint_text = text
        self._hint_kind = kind
        self.hint_label.set_text(text)
        self.hint_label.set_visible(bool(text))
        for css_class in ("error-text", "accent-text", "dim-label"):
            self.hint_label.remove_css_class(css_class)
        if kind == "error":
            self.hint_label.add_css_class("error-text")
        elif kind == "accent":
            self.hint_label.add_css_class("accent-text")
        else:
            self.hint_label.add_css_class("dim-label")

    def _on_quality_changed(self, dropdown, _pspec) -> None:
        index = dropdown.get_selected()
        if 0 <= index < len(QUALITY_ORDER):
            key = QUALITY_ORDER[index]
            if key != self.settings.quality:
                self.settings.quality = key
                self.settings.save()

    # ------------------------------------------------------------------ #
    # Download actions
    # ------------------------------------------------------------------ #

    def _start_download(self, *_args) -> None:
        urls = util.extract_urls(self.url_entry.get_text())
        if not urls:
            self._set_hint("Paste an Instagram reel link first.", "error")
            self._toast("No Instagram reel link found.")
            self.url_entry.grab_focus()
            return
        quality = QUALITY_ORDER[self.quality_dropdown.get_selected()]
        added = self.engine.add(urls, quality)
        if not added:
            self._toast("Those links are already in the queue.")
            return
        self.url_entry.set_text("")
        self._preview_url = ""
        self._preview_meta = None
        self.preview_revealer.set_reveal_child(False)
        self._set_hint("", "")
        noun = "download" if len(added) == 1 else "downloads"
        self._toast(f"Added {len(added)} {noun} to the queue.")
        self.url_entry.grab_focus()

    def _enqueue(self, urls: list[str]) -> None:
        urls = [url for url in util.join_unique(urls) if url]
        if not urls:
            return
        quality = QUALITY_ORDER[self.quality_dropdown.get_selected()]
        added = self.engine.add(urls, quality)
        if added:
            noun = "download" if len(added) == 1 else "downloads"
            self._toast(f"Added {len(added)} {noun} to the queue.")
        else:
            self._toast("Those links are already in the queue.")

    def enqueue_urls(self, urls: list[str]) -> None:
        """Add links from the command line or a desktop drop."""
        self._enqueue(urls)
        self.present()

    def _on_clear_finished(self, *_args) -> None:
        self.engine.clear_finished()
        self._toast("Cleared finished downloads.")

    def _open_job(self, job: dict) -> None:
        path = job.get("filename")
        if path and Path(path).exists():
            if not util.open_path(path):
                self._toast("Could not open the file.")
            return
        self._open_download_folder()

    def _open_download_folder(self, *_args) -> None:
        folder = Path(self.settings.download_dir).expanduser()
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        if not util.open_path(folder):
            self._toast("Could not open the downloads folder.")

    # ------------------------------------------------------------------ #
    # History
    # ------------------------------------------------------------------ #

    def _refresh_history(self) -> None:
        entries = self.library.all()
        query = self.history_search.get_text().strip().lower()
        if not entries and query:
            self.history_search.set_text("")
            query = ""
        if query:
            visible = [
                entry
                for entry in entries
                if query
                in " ".join(
                    (
                        str(entry.get("title") or ""),
                        str(entry.get("uploader") or ""),
                        str(entry.get("url") or ""),
                    )
                ).lower()
            ]
        else:
            visible = entries
        self._history_version = self.library.version

        row = self.history_list.get_row_at_index(0)
        while row is not None:
            self.history_list.remove(row)
            row = self.history_list.get_row_at_index(0)
        self._history_map.clear()

        for entry in visible[:200]:
            list_row = self._build_history_row(entry)
            self._history_map[list_row] = entry
            self.history_list.append(list_row)

        if query and entries:
            count_text = f"{len(visible)} of {len(entries)} reels"
        else:
            count_text = f"{len(entries)} saved reel{'s' if len(entries) != 1 else ''}"
        self.history_count.set_text(count_text)
        if not entries:
            self.history_empty.set_title("Your library is empty")
            self.history_empty.set_description("Downloaded reels will appear here.")
        elif not visible:
            self.history_empty.set_title("No matches")
            self.history_empty.set_description("Try a different title, creator or link.")
        self.history_stack.set_visible_child_name("list" if visible else "empty")
        self.clear_history_btn.set_visible(bool(entries))
        self.history_search.set_visible(bool(entries))

    def _build_history_row(self, entry: dict) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow()
        row.set_activatable(True)
        row.add_css_class("queue-row")

        outer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        outer.set_margin_top(9)
        outer.set_margin_bottom(9)
        outer.set_margin_start(12)
        outer.set_margin_end(8)

        path = entry.get("path") or ""
        exists = bool(path) and Path(path).exists()
        thumb = widgets.thumbnail_box(
            entry.get("thumbnail") if exists else "",
            48,
            "video-x-generic-symbolic",
        )
        outer.append(thumb)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info.set_hexpand(True)
        info.set_valign(Gtk.Align.CENTER)

        title = Gtk.Label(label=entry.get("title") or "Instagram reel")
        title.set_xalign(0)
        title.set_ellipsize(Pango.EllipsizeMode.END)
        title.set_single_line_mode(True)
        title.add_css_class("row-title")
        info.append(title)

        parts = [entry.get("uploader") or "Instagram"]
        if entry.get("timestamp"):
            parts.append(util.relative_time(entry["timestamp"]))
        if entry.get("size"):
            parts.append(util.human_size(entry["size"]))
        if not exists:
            parts.append("file missing")
        subtitle = Gtk.Label(label=" · ".join(parts))
        subtitle.set_xalign(0)
        subtitle.set_ellipsize(Pango.EllipsizeMode.END)
        subtitle.set_single_line_mode(True)
        subtitle.add_css_class("dim-label")
        subtitle.add_css_class("caption")
        info.append(subtitle)
        outer.append(info)

        trailing = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        trailing.set_valign(Gtk.Align.CENTER)

        open_btn = widgets.flat_icon_button(
            "folder-open-symbolic",
            "Open reel",
            lambda: self._open_history_entry(entry),
        )
        trailing.append(open_btn)

        menu = Gio.Menu()
        entry_id = entry.get("entry_id", "")
        menu.append("Open file", f"win.history-open::{entry_id}")
        menu.append("Show in folder", f"win.history-folder::{entry_id}")
        menu.append("Copy link", f"win.history-copy::{entry_id}")
        menu.append("Remove from library", f"win.history-remove::{entry_id}")
        menu.append("Delete file…", f"win.history-delete::{entry_id}")
        menu_button = Gtk.MenuButton(icon_name="view-more-symbolic", menu_model=menu)
        menu_button.add_css_class("flat")
        menu_button.add_css_class("circular")
        menu_button.set_tooltip_text("More actions")
        trailing.append(menu_button)
        outer.append(trailing)

        row.set_child(outer)
        return row

    def _entry_by_id(self, entry_id: str) -> dict | None:
        for entry in self.library.all():
            if entry.get("entry_id") == entry_id:
                return entry
        return None

    def _open_history_entry(self, entry: dict) -> None:
        path = entry.get("path") or ""
        if path and Path(path).exists():
            if not util.open_path(path):
                self._toast("Could not open the file.")
        else:
            self._toast("File not found — it may have been moved or deleted.")

    def _on_history_row_activated(self, _listbox, row) -> None:
        entry = self._history_map.get(row)
        if entry:
            self._open_history_entry(entry)

    def _on_history_open(self, _action, param) -> None:
        entry = self._entry_by_id(param.get_string())
        if entry:
            self._open_history_entry(entry)

    def _on_history_folder(self, _action, param) -> None:
        entry = self._entry_by_id(param.get_string())
        if not entry:
            return
        path = Path(entry.get("path") or "")
        if path.exists():
            if not util.open_path(path.parent):
                self._toast("Could not open the folder.")
        else:
            self._toast("File not found.")

    def _on_history_copy(self, _action, param) -> None:
        entry = self._entry_by_id(param.get_string())
        if not entry:
            return
        self._clipboard.set(entry.get("url") or "")
        self._toast("Link copied to the clipboard.")

    def _on_history_remove(self, _action, param) -> None:
        entry_id = param.get_string()
        if self.library.remove(entry_id):
            self._refresh_history()
            self._toast("Removed from the library.")

    def _on_history_delete(self, _action, param) -> None:
        entry = self._entry_by_id(param.get_string())
        if not entry:
            return
        path = entry.get("path") or ""
        title = entry.get("title") or "this reel"

        def delete_file() -> None:
            try:
                if path:
                    Path(path).unlink(missing_ok=True)
            except OSError as error:
                self._toast(f"Could not delete the file: {error}")
                return
            self.library.remove(entry.get("entry_id", ""))
            self._refresh_history()
            self._toast("File deleted.")

        widgets.confirm(
            self,
            "Delete this file?",
            f"“{title}” will be removed from disk. This cannot be undone.",
            "Delete",
            destructive=True,
            callback=delete_file,
        )

    def _confirm_clear_history(self) -> None:
        def clear() -> None:
            self.library.clear()
            self._refresh_history()
            self._toast("Library cleared.")

        widgets.confirm(
            self,
            "Clear the library?",
            "This removes the download history. Files on disk are kept.",
            "Clear",
            destructive=True,
            callback=clear,
        )

    # ------------------------------------------------------------------ #
    # Preferences and settings
    # ------------------------------------------------------------------ #

    def present_preferences(self) -> None:
        from .preferences import PreferencesDialog

        dialog = PreferencesDialog(self, self.settings, self)
        dialog.present(self)

    def confirm_clear_history(self) -> None:
        self._confirm_clear_history()

    def apply_theme(self) -> None:
        application = self.get_application()
        if application is not None:
            application.apply_theme()

    def apply_settings(self) -> None:
        self.engine.set_concurrency(self.settings.concurrency)
        self.ytdlp_banner.set_revealed(util.which_ytdlp() is None)
        try:
            index = QUALITY_ORDER.index(self.settings.quality)
            if self.quality_dropdown.get_selected() != index:
                self.quality_dropdown.set_selected(index)
        except ValueError:
            pass
        try:
            Path(self.settings.download_dir).expanduser().mkdir(
                parents=True, exist_ok=True
            )
        except OSError:
            pass

    # ------------------------------------------------------------------ #
    # Poll loop
    # ------------------------------------------------------------------ #

    def _tick(self) -> bool:
        if self._closing:
            return False
        snapshot = self.engine.snapshot()
        self._sync_queue(snapshot)
        self._sync_preview()
        self._handle_completions(snapshot)
        if self.library.version != self._history_version:
            self._refresh_history()
        return True

    def _sync_queue(self, snapshot: list[dict]) -> None:
        by_id = {job["id"]: job for job in snapshot}
        for job in snapshot:
            row = self._rows.get(job["id"])
            if row is None:
                row = DownloadRow(
                    job["id"],
                    {
                        "cancel": self.engine.cancel,
                        "retry": self.engine.retry,
                        "remove": self.engine.remove,
                        "open": self._open_job,
                    },
                )
                self._rows[job["id"]] = row
                self.queue_list.prepend(row)
            row.update(job)

        for job_id in list(self._rows):
            if job_id not in by_id:
                self.queue_list.remove(self._rows.pop(job_id))

        active = sum(1 for job in snapshot if job["status"] in ACTIVE_STATUSES)
        finished = sum(
            1 for job in snapshot if job["status"] in {"done", "duplicate", "error", "cancelled"}
        )
        if active and finished:
            count_text = f"{active} active · {finished} finished"
        elif active:
            count_text = f"{active} active"
        elif finished:
            count_text = f"{finished} finished"
        else:
            count_text = ""
        if self.queue_count.get_label() != count_text:
            self.queue_count.set_label(count_text)
        self.queue_stack.set_visible_child_name("list" if snapshot else "empty")
        self.clear_finished_btn.set_visible(finished > 0)
        if not snapshot:
            for job_id in self._seen_status:
                if job_id not in by_id:
                    self._seen_status.pop(job_id, None)

    def _sync_preview(self) -> None:
        url = self._preview_url
        if not url or url not in self.url_entry.get_text():
            return
        state = self.engine.preview(url)
        if not state:
            return

        if state.get("status") == "ready":
            meta = state.get("meta") or {}
            if meta == self._preview_meta:
                return
            self._preview_meta = meta
            self.preview_spinner.set_visible(False)
            self.preview_title.set_text(meta.get("title") or "Instagram reel")
            parts = []
            if meta.get("uploader"):
                parts.append(str(meta["uploader"]))
            if meta.get("duration"):
                parts.append(util.human_duration(meta["duration"]))
            self.preview_meta.set_text(" · ".join(parts))
            thumb = meta.get("thumb_path") or ""
            if thumb != self._preview_thumb:
                self._preview_thumb = thumb
                widgets.fill_thumbnail(self.preview_thumb, thumb, 104)
            existing = self.engine.is_downloaded(meta.get("id") or "")
            if existing:
                self.preview_badge.set_text(
                    f"Already downloaded {util.relative_time(existing.get('timestamp'))}"
                )
                self.preview_badge.set_visible(True)
            else:
                self.preview_badge.set_visible(False)
            self.preview_revealer.set_reveal_child(True)
        elif state.get("status") == "error":
            self.preview_spinner.set_visible(False)
            self.preview_revealer.set_reveal_child(False)
            if not self._hint_text:
                self._set_hint(state.get("error") or "Could not load that reel.", "error")

    def _handle_completions(self, snapshot: list[dict]) -> None:
        completed: list[dict] = []
        failed: list[dict] = []
        for job in snapshot:
            previous = self._seen_status.get(job["id"])
            current = job["status"]
            if current == "done" and previous != "done":
                completed.append(job)
            elif current == "error" and previous != "error":
                failed.append(job)
            self._seen_status[job["id"]] = current

        for job_id in list(self._seen_status):
            if not any(job["id"] == job_id for job in snapshot):
                self._seen_status.pop(job_id, None)

        if completed:
            if len(completed) == 1:
                job = completed[0]
                toast = Adw.Toast.new(f"Downloaded: {job['title']}")
                toast.set_button_label("Open")
                path = job.get("filename")
                toast.connect("button-clicked", lambda *_: self._open_job(job))
                toast.set_timeout(5)
                self.overlay.add_toast(toast)
                if self.settings.notifications and not self.get_property("is-active"):
                    util.notify("Reel downloaded", job["title"])
            else:
                toast = Adw.Toast.new(f"{len(completed)} downloads finished")
                toast.set_button_label("Open folder")
                toast.connect("button-clicked", lambda *_: self._open_download_folder())
                toast.set_timeout(5)
                self.overlay.add_toast(toast)
                if self.settings.notifications and not self.get_property("is-active"):
                    util.notify("Downloads finished", f"{len(completed)} reels saved")

        if failed:
            job = failed[0]
            toast = Adw.Toast.new(f"Download failed: {job.get('error') or 'unknown error'}")
            toast.set_timeout(6)
            self.overlay.add_toast(toast)

    # ------------------------------------------------------------------ #
    # Closing
    # ------------------------------------------------------------------ #

    def _on_close_request(self, *_args) -> bool:
        if self._closing:
            self._cleanup()
            return False
        if self.engine.active_count() > 0:
            def quit_anyway() -> None:
                self._closing = True
                self._cleanup()
                self.close()

            widgets.confirm(
                self,
                "Quit while downloading?",
                "Active downloads will be cancelled. Partially downloaded files are kept.",
                "Quit",
                destructive=True,
                callback=quit_anyway,
            )
            return True
        self._closing = True
        self._cleanup()
        return False

    def _cleanup(self) -> None:
        if self._tick_source is not None:
            GLib.source_remove(self._tick_source)
            self._tick_source = None
        self._cancel_preview_timer()
        self.engine.shutdown()

    def _toast(self, text: str, timeout: int = 4) -> None:
        toast = Adw.Toast.new(text)
        toast.set_timeout(timeout)
        self.overlay.add_toast(toast)
