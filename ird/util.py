"""Small shared helpers: URLs, formatting, XDG paths, opening files."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Iterable

from . import __app_icon__, __app_name__

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #

APP_SLUG = "instagram-reels-downloader"


def _xdg_dir(env_var: str, fallback: Path) -> Path:
    value = os.environ.get(env_var)
    return Path(value).expanduser() if value else fallback


def config_dir() -> Path:
    path = _xdg_dir("XDG_CONFIG_HOME", Path.home() / ".config") / APP_SLUG
    path.mkdir(parents=True, exist_ok=True)
    return path


def cache_dir() -> Path:
    path = _xdg_dir("XDG_CACHE_HOME", Path.home() / ".cache") / APP_SLUG
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_download_dir() -> Path:
    return Path.home() / "Downloads" / "Instagram_Reels"


# --------------------------------------------------------------------------- #
# Instagram URLs
# --------------------------------------------------------------------------- #

_URL_PATTERN = (
    r"https?://(?:www\.)?(?:instagram\.com|instagr\.am)/"
    r"(?:[A-Za-z0-9_.]+/)?(?:reel|reels|p|tv|share)/[A-Za-z0-9_-]+/?"
    r"(?:[?#][^\s\"'<>]*)?"
)
_URL_RE = re.compile(_URL_PATTERN, re.IGNORECASE)


def extract_urls(text: str | None) -> list[str]:
    """Return every Instagram URL in *text*, deduplicated, in order."""
    if not text:
        return []
    seen: set[str] = set()
    urls: list[str] = []
    for match in _URL_RE.finditer(text):
        url = match.group(0).strip().rstrip(".,;:!?)]}\"'")
        key = url.rstrip("/")
        if key and key not in seen:
            seen.add(key)
            urls.append(url)
    return urls


def is_instagram_url(text: str | None) -> bool:
    if not text:
        return False
    return _URL_RE.fullmatch(text.strip()) is not None


def short_url(url: str) -> str:
    code = url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]
    return f"Reel {code}" if code else url


# --------------------------------------------------------------------------- #
# Formatting
# --------------------------------------------------------------------------- #


def human_size(num: float | int | None) -> str:
    if not num or num <= 0:
        return "—"
    size = float(num)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            if unit == "B":
                return f"{size:.0f} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return "—"


def human_speed(bytes_per_second: float | int | None) -> str:
    if not bytes_per_second or bytes_per_second <= 0:
        return ""
    return f"{human_size(bytes_per_second)}/s"


def human_duration(seconds: float | int | None) -> str:
    if not seconds or seconds <= 0:
        return ""
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def relative_time(timestamp: float | int | None) -> str:
    if not timestamp:
        return ""
    delta = max(0, time.time() - float(timestamp))
    if delta < 60:
        return "just now"
    if delta < 3600:
        return f"{int(delta // 60)} min ago"
    if delta < 86400:
        return f"{int(delta // 3600)} h ago"
    if delta < 86400 * 7:
        return f"{int(delta // 86400)} d ago"
    return time.strftime("%b %d, %Y", time.localtime(timestamp))


# --------------------------------------------------------------------------- #
# yt-dlp discovery
# --------------------------------------------------------------------------- #


def which_ytdlp() -> str | None:
    """Locate a yt-dlp executable (works for system, pip and venv installs)."""
    override = os.environ.get("YT_DLP")
    if override and Path(override).is_file():
        return override
    found = shutil.which("yt-dlp")
    if found:
        return found
    # pip --user installs sometimes land outside PATH when launched from a
    # desktop entry.
    candidate = Path.home() / ".local" / "bin" / "yt-dlp"
    return str(candidate) if candidate.is_file() else None


# --------------------------------------------------------------------------- #
# Files and integrations
# --------------------------------------------------------------------------- #


def open_path(path: str | Path | None) -> bool:
    """Open a file or folder with the user's default application."""
    if not path:
        return False
    target = Path(path).expanduser()
    if not target.exists():
        return False
    try:
        from gi.repository import Gio

        Gio.AppInfo.launch_default_for_uri(target.resolve().as_uri(), None)
        return True
    except Exception:
        return False


def open_uri(uri: str) -> bool:
    try:
        from gi.repository import Gio

        Gio.AppInfo.launch_default_for_uri(uri, None)
        return True
    except Exception:
        return False


def read_text_file(path: str | Path, limit: int = 256_000) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read(limit)
    except OSError:
        return ""


def atomic_write_json(path: str | Path, data) -> bool:
    """Write JSON atomically so a crash cannot truncate settings/history."""
    target = Path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, target)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        return True
    except OSError:
        return False


_notify = None


def notify(summary_text: str, body_text: str = "") -> bool:
    """Send a desktop notification through libnotify when available."""
    global _notify
    if _notify is None:
        try:
            import gi

            gi.require_version("Notify", "0.7")
            from gi.repository import Notify

            if not Notify.is_initted():
                Notify.init(__app_name__)
            _notify = Notify
        except Exception:
            _notify = False
    if _notify is False:
        return False
    try:
        notification = _notify.Notification.new(summary_text, body_text, __app_icon__)
        notification.show()
        return True
    except Exception:
        return False


def join_unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
