"""Persistent settings and the downloaded-reel library."""

from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass, field, fields
from pathlib import Path

from . import util

QUALITY_KEYS = ("best", "1080", "720", "480", "audio")
QUALITY_LABELS = {
    "best": "Best available",
    "1080": "1080p",
    "720": "720p",
    "480": "480p",
    "audio": "Audio only (MP3)",
}
QUALITY_ORDER = ["best", "1080", "720", "480", "audio"]

THEME_KEYS = ("system", "light", "dark")
THEME_LABELS = {"system": "Follow system", "light": "Light", "dark": "Dark"}

COOKIE_MODES = ("none", "browser", "file")
COOKIE_MODE_LABELS = {
    "none": "Don't use cookies",
    "browser": "Import from a web browser",
    "file": "Use a cookies.txt file",
}

BROWSERS = ("firefox", "chrome", "chromium", "brave", "edge", "vivaldi", "opera")


@dataclass
class Settings:
    download_dir: str = field(default_factory=lambda: str(util.default_download_dir()))
    quality: str = "best"
    concurrency: int = 3
    theme: str = "system"
    cookies_mode: str = "none"
    cookies_browser: str = "firefox"
    cookies_file: str = ""
    notifications: bool = True
    clipboard_hint: bool = True
    embed_metadata: bool = True
    embed_thumbnail: bool = False

    # Not persisted; used by the app.
    _path: Path | None = field(default=None, repr=False, compare=False)

    @classmethod
    def load(cls, path: Path | None = None) -> "Settings":
        target = path or (util.config_dir() / "settings.json")
        settings = cls(_path=target)
        try:
            raw = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return settings
        if not isinstance(raw, dict):
            return settings
        for item in fields(cls):
            if item.name.startswith("_") or item.name not in raw:
                continue
            value = raw[item.name]
            if item.name == "concurrency":
                try:
                    value = max(1, min(6, int(value)))
                except (TypeError, ValueError):
                    continue
            elif item.name in {"notifications", "clipboard_hint", "embed_metadata", "embed_thumbnail"}:
                value = bool(value)
            elif not isinstance(value, str):
                continue
            setattr(settings, item.name, value)
        settings._sanitize()
        return settings

    def _sanitize(self) -> None:
        if self.quality not in QUALITY_KEYS:
            self.quality = "best"
        if self.theme not in THEME_KEYS:
            self.theme = "system"
        if self.cookies_mode not in COOKIE_MODES:
            self.cookies_mode = "none"
        if self.cookies_browser not in BROWSERS:
            self.cookies_browser = "firefox"
        if not self.download_dir or not str(self.download_dir).strip():
            self.download_dir = str(util.default_download_dir())
        self.download_dir = str(Path(self.download_dir).expanduser())
        self.concurrency = max(1, min(6, int(self.concurrency)))

    def save(self) -> bool:
        data = {item.name: getattr(self, item.name) for item in fields(self) if not item.name.startswith("_")}
        return util.atomic_write_json(self._path or (util.config_dir() / "settings.json"), data)

    def as_dict(self) -> dict:
        return {item.name: getattr(self, item.name) for item in fields(self) if not item.name.startswith("_")}


class Library:
    """Thread-safe record of downloaded reels, also used for duplicate checks."""

    MAX_ENTRIES = 1000

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (util.config_dir() / "library.json")
        self._lock = threading.RLock()
        self._entries: list[dict] = []
        self._by_video: dict[str, dict] = {}
        self.version = 0
        self._load()

    # -- persistence ------------------------------------------------------- #

    def _load(self) -> None:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        entries = raw.get("entries") if isinstance(raw, dict) else raw
        if not isinstance(entries, list):
            return
        cleaned: list[dict] = []
        for entry in entries:
            if not isinstance(entry, dict) or not entry.get("video_id"):
                continue
            entry.setdefault("entry_id", uuid.uuid4().hex)
            entry.setdefault("title", "")
            entry.setdefault("uploader", "")
            entry.setdefault("path", "")
            entry.setdefault("size", 0)
            entry.setdefault("duration", 0)
            entry.setdefault("quality", "best")
            entry.setdefault("timestamp", 0)
            entry.setdefault("thumbnail", "")
            entry.setdefault("url", "")
            cleaned.append(entry)
        with self._lock:
            self._entries = cleaned[: self.MAX_ENTRIES]
            self._reindex()

    def _save(self) -> None:
        # Caller holds the lock.
        util.atomic_write_json(self._path, {"version": 1, "entries": self._entries})

    def _reindex(self) -> None:
        self._by_video = {entry["video_id"]: entry for entry in self._entries}

    # -- public API -------------------------------------------------------- #

    def all(self) -> list[dict]:
        with self._lock:
            return [dict(entry) for entry in self._entries]

    def find(self, video_id: str, require_exists: bool = True) -> dict | None:
        if not video_id:
            return None
        with self._lock:
            entry = self._by_video.get(video_id)
            if not entry:
                return None
            if require_exists and not Path(entry.get("path") or "").exists():
                return None
            return dict(entry)

    def add(self, entry: dict) -> dict:
        video_id = str(entry.get("video_id") or "").strip()
        if not video_id:
            raise ValueError("entry needs a video_id")
        entry = dict(entry)
        entry.setdefault("entry_id", uuid.uuid4().hex)
        entry.setdefault("timestamp", time.time())
        with self._lock:
            existing = self._by_video.get(video_id)
            if existing:
                entry["entry_id"] = existing.get("entry_id", entry["entry_id"])
            self._entries = [item for item in self._entries if item.get("video_id") != video_id]
            self._entries.insert(0, entry)
            del self._entries[self.MAX_ENTRIES :]
            self._reindex()
            self.version += 1
            self._save()
            return dict(entry)

    def remove(self, entry_id: str) -> bool:
        with self._lock:
            before = len(self._entries)
            self._entries = [item for item in self._entries if item.get("entry_id") != entry_id]
            if len(self._entries) == before:
                return False
            self._reindex()
            self.version += 1
            self._save()
            return True

    def clear(self) -> None:
        with self._lock:
            if not self._entries:
                return
            self._entries = []
            self._by_video = {}
            self.version += 1
            self._save()
