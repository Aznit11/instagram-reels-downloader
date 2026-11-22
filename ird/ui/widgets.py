"""Reusable GTK widgets and small UI helpers."""

from __future__ import annotations

import math
from collections import OrderedDict

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")

from gi.repository import Adw, Gdk, GdkPixbuf, GLib, Gtk  # noqa: E402

_PIXBUF_CACHE: "OrderedDict[tuple[str, int], GdkPixbuf.Pixbuf]" = OrderedDict()
_PIXBUF_CACHE_MAX = 160


def load_texture(path: str | None) -> Gdk.Texture | None:
    if not path:
        return None
    try:
        return Gdk.Texture.new_from_filename(path)
    except (GLib.Error, ValueError):
        return None


def _square_pixbuf(path: str, size: int) -> GdkPixbuf.Pixbuf | None:
    key = (path, size)
    cached = _PIXBUF_CACHE.get(key)
    if cached is not None:
        _PIXBUF_CACHE.move_to_end(key)
        return cached
    try:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
        width, height = pixbuf.get_width(), pixbuf.get_height()
        if width <= 0 or height <= 0:
            return None
        scale = max(size / width, size / height)
        new_width = max(size, int(math.ceil(width * scale)))
        new_height = max(size, int(math.ceil(height * scale)))
        scaled = pixbuf.scale_simple(
            new_width, new_height, GdkPixbuf.InterpType.BILINEAR
        )
        if scaled is None:
            return None
        offset_x = max(0, (new_width - size) // 2)
        offset_y = max(0, (new_height - size) // 2)
        if new_width > size or new_height > size:
            scaled = scaled.new_subpixbuf(offset_x, offset_y, size, size)
    except (GLib.Error, ValueError, OSError):
        return None
    _PIXBUF_CACHE[key] = scaled
    if len(_PIXBUF_CACHE) > _PIXBUF_CACHE_MAX:
        _PIXBUF_CACHE.popitem(last=False)
    return scaled


def fill_thumbnail(
    box: Gtk.Box,
    path: str | None,
    size: int,
    icon_name: str = "video-x-generic-symbolic",
) -> None:
    child = box.get_first_child()
    while child is not None:
        box.remove(child)
        child = box.get_first_child()

    pixbuf = _square_pixbuf(path, size) if path else None
    if pixbuf is not None:
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.set_pixel_size(size)
        image.set_size_request(size, size)
        image.set_halign(Gtk.Align.CENTER)
        image.set_valign(Gtk.Align.CENTER)
        box.append(image)
        return

    image = Gtk.Image.new_from_icon_name(icon_name)
    image.set_pixel_size(max(16, int(size * 0.4)))
    image.set_halign(Gtk.Align.CENTER)
    image.set_valign(Gtk.Align.CENTER)
    image.set_hexpand(True)
    image.set_vexpand(True)
    image.add_css_class("dim-label")
    box.append(image)


def thumbnail_box(
    path: str | None,
    size: int,
    icon_name: str = "video-x-generic-symbolic",
) -> Gtk.Box:
    box = Gtk.Box()
    box.add_css_class("thumb")
    box.set_size_request(size, size)
    box.set_hexpand(False)
    box.set_hexpand_set(True)
    box.set_vexpand(False)
    box.set_vexpand_set(True)
    box.set_overflow(Gtk.Overflow.HIDDEN)
    box.set_valign(Gtk.Align.CENTER)
    fill_thumbnail(box, path, size, icon_name)
    return box


def flat_icon_button(
    icon_name: str,
    tooltip: str,
    callback=None,
    css_classes: tuple[str, ...] = (),
) -> Gtk.Button:
    button = Gtk.Button()
    button.set_icon_name(icon_name)
    button.set_tooltip_text(tooltip)
    button.add_css_class("flat")
    button.add_css_class("circular")
    for css_class in css_classes:
        button.add_css_class(css_class)
    if callback is not None:
        button.connect("clicked", lambda *_: callback())
    return button


def icon_label_button(icon_name: str, label: str, css_classes: tuple[str, ...] = ()) -> Gtk.Button:
    button = Gtk.Button()
    content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    content.append(Gtk.Image.new_from_icon_name(icon_name))
    content.append(Gtk.Label(label=label))
    button.set_child(content)
    for css_class in css_classes:
        button.add_css_class(css_class)
    return button


def icon_image(name: str, pixel_size: int, fallback: str = "video-x-generic-symbolic") -> Gtk.Image:
    display = Gdk.Display.get_default()
    if display is not None:
        theme = Gtk.IconTheme.get_for_display(display)
        if not theme.has_icon(name):
            name = fallback
    image = Gtk.Image.new_from_icon_name(name)
    image.set_pixel_size(pixel_size)
    return image


def confirm(
    parent: Gtk.Window,
    heading: str,
    body: str,
    confirm_label: str,
    destructive: bool = False,
    callback=None,
) -> None:
    dialog = Adw.AlertDialog(heading=heading, body=body)
    dialog.add_response("cancel", "Cancel")
    dialog.add_response("confirm", confirm_label)
    if destructive:
        dialog.set_response_appearance("confirm", Adw.ResponseAppearance.DESTRUCTIVE)
    dialog.set_default_response("cancel")
    dialog.set_close_response("cancel")

    def on_choice(dlg, result):
        try:
            response = dlg.choose_finish(result)
        except GLib.Error:
            return
        if response == "confirm" and callback is not None:
            callback()

    dialog.choose(parent, None, on_choice)
