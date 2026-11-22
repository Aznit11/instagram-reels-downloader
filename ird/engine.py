"""Download engine: metadata, queueing, parallel downloads and cancellation.

The engine talks to the system ``yt-dlp`` executable. It never touches GTK:
the UI polls :meth:`DownloadManager.snapshot` from the main loop.
"""

from __future__ import annotations

import json
import logging
import os
import re
import signal
import subprocess
import threading
import time
import urllib.request
import uuid
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from . import util
from .config import Library, Settings

log = logging.getLogger(__name__)

# yt-dlp arguments per quality preset.
FORMAT_ARGS: dict[str, list[str]] = {
    "best": ["-f", "bv*+ba/b", "--merge-output-format", "mp4"],
    "1080": ["-f", "bv*[height<=1080]+ba/b[height<=1080]/b", "--merge-output-format", "mp4"],
    "720": ["-f", "bv*[height<=720]+ba/b[height<=720]/b", "--merge-output-format", "mp4"],
    "480": ["-f", "bv*[height<=480]+ba/b[height<=480]/b", "--merge-output-format", "mp4"],
    "audio": ["-f", "ba/b", "-x", "--audio-format", "mp3", "--audio-quality", "0"],
}

TERMINAL_STATUSES = {"done", "error", "cancelled", "duplicate"}
ACTIVE_STATUSES = {"preparing", "queued", "downloading", "processing", "cancelling"}

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_PROGRESS_PREFIX = "IRD_PROGRESS|"
_FILE_PREFIX = "IRD_FILE|"


class ExtractError(Exception):
    """A user-facing error while talking to yt-dlp."""


@dataclass
class Job:
    id: str
    url: str
    quality: str
    title: str = ""
    uploader: str = ""
    video_id: str = ""
    thumbnail_path: str = ""
    duration: float = 0.0
    status: str = "preparing"
    progress: float = 0.0
    downloaded: int = 0
    total: int = 0
    speed: float = 0.0
    eta: int = 0
    filename: str = ""
    size: int = 0
    error: str = ""
    added_at: float = field(default_factory=time.time)
    finished_at: float = 0.0
    cancel_event: threading.Event = field(default_factory=threading.Event, repr=False)
    proc: subprocess.Popen | None = field(default=None, repr=False)

    def snapshot(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "url": self.url,
            "quality": self.quality,
            "title": self.title or util.short_url(self.url),
            "uploader": self.uploader,
            "video_id": self.video_id,
            "thumbnail_path": self.thumbnail_path,
            "duration": self.duration,
            "status": self.status,
            "progress": self.progress,
            "downloaded": self.downloaded,
            "total": self.total,
            "speed": self.speed,
            "eta": self.eta,
            "filename": self.filename,
            "size": self.size,
            "error": self.error,
            "added_at": self.added_at,
            "finished_at": self.finished_at,
        }


class _Limiter:
    """A resizable concurrency limiter with cancellation support."""

    def __init__(self, limit: int) -> None:
        self._limit = max(1, int(limit))
        self._active = 0
        self._condition = threading.Condition()

    def set_limit(self, limit: int) -> None:
        with self._condition:
            self._limit = max(1, int(limit))
            self._condition.notify_all()

    def acquire(self, cancel_event: threading.Event) -> bool:
        with self._condition:
            while self._active >= self._limit:
                if cancel_event.is_set():
                    return False
                self._condition.wait(0.2)
            if cancel_event.is_set():
                return False
            self._active += 1
            return True

    def release(self) -> None:
        with self._condition:
            self._active = max(0, self._active - 1)
            self._condition.notify()


class DownloadManager:
    META_TTL = 3600
    META_ERROR_TTL = 45
    META_CACHE_MAX = 120

    def __init__(self, settings: Settings, library: Library) -> None:
        self._settings = settings
        self._library = library
        self._lock = threading.RLock()
        self._jobs: dict[str, Job] = {}
        self._order: list[str] = []
        self._previews: dict[str, dict] = {}
        self._meta_cache: dict[str, tuple[float, dict]] = {}
        self._meta_sem = threading.BoundedSemaphore(2)
        self._meta_procs: set[subprocess.Popen] = set()
        self._limiter = _Limiter(settings.concurrency)
        self._meta_exec = ThreadPoolExecutor(max_workers=3, thread_name_prefix="ird-meta")
        self._dl_exec = ThreadPoolExecutor(max_workers=8, thread_name_prefix="ird-download")
        self._closed = False

    # ------------------------------------------------------------------ #
    # Queue control
    # ------------------------------------------------------------------ #

    def add(self, urls: list[str], quality: str | None = None) -> list[str]:
        quality = quality if quality in FORMAT_ARGS else self._settings.quality
        if quality not in FORMAT_ARGS:
            quality = "best"
        added: list[str] = []
        for raw_url in urls:
            url = (raw_url or "").strip()
            if not url.startswith(("http://", "https://")):
                continue
            with self._lock:
                if self._closed:
                    return added
                if any(
                    job.url == url and job.status not in TERMINAL_STATUSES
                    for job in self._jobs.values()
                ):
                    continue
                job = Job(id=uuid.uuid4().hex[:12], url=url, quality=quality)
                self._jobs[job.id] = job
                self._order.append(job.id)
                added.append(job.id)
        for job_id in added:
            try:
                self._dl_exec.submit(self._download_worker, self._jobs[job_id])
            except RuntimeError:  # executor already shut down
                break
        return added

    def cancel(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.status in TERMINAL_STATUSES:
                return
            job.cancel_event.set()
            job.status = "cancelling"
            proc = job.proc
        self._terminate(proc)

    def retry(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.status not in TERMINAL_STATUSES:
                return
            job.status = "preparing"
            job.progress = 0.0
            job.downloaded = 0
            job.total = 0
            job.speed = 0.0
            job.eta = 0
            job.error = ""
            job.finished_at = 0.0
            job.cancel_event = threading.Event()
        try:
            self._dl_exec.submit(self._download_worker, job)
        except RuntimeError:
            pass

    def remove(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            if job.status not in TERMINAL_STATUSES:
                job.cancel_event.set()
                proc = job.proc
            else:
                proc = None
            self._jobs.pop(job_id, None)
            if job_id in self._order:
                self._order.remove(job_id)
        self._terminate(proc)

    def clear_finished(self) -> None:
        with self._lock:
            for job_id in list(self._order):
                job = self._jobs.get(job_id)
                if job and job.status in TERMINAL_STATUSES:
                    self._jobs.pop(job_id, None)
                    self._order.remove(job_id)

    def active_count(self) -> int:
        with self._lock:
            return sum(1 for job in self._jobs.values() if job.status in ACTIVE_STATUSES)

    def snapshot(self) -> list[dict[str, Any]]:
        with self._lock:
            result: list[dict[str, Any]] = []
            for job_id in self._order:
                job = self._jobs.get(job_id)
                if job is not None:
                    result.append(job.snapshot())
            return result

    def set_concurrency(self, limit: int) -> None:
        self._limiter.set_limit(limit)

    def shutdown(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            jobs = list(self._jobs.values())
            meta_procs = list(self._meta_procs)
        for job in jobs:
            job.cancel_event.set()
            if job.proc is not None:
                self._terminate(job.proc)
        for proc in meta_procs:
            self._terminate(proc)
        self._dl_exec.shutdown(wait=False, cancel_futures=True)
        self._meta_exec.shutdown(wait=False, cancel_futures=True)

    # ------------------------------------------------------------------ #
    # Preview metadata
    # ------------------------------------------------------------------ #

    def request_preview(self, url: str) -> None:
        url = (url or "").strip()
        if not url or self._closed:
            return
        now = time.time()
        with self._lock:
            state = self._previews.get(url)
            if state:
                if state.get("status") == "loading":
                    return
                age = now - state.get("ts", 0)
                if state.get("status") == "ready" and age < self.META_TTL:
                    return
                if state.get("status") == "error" and age < self.META_ERROR_TTL:
                    return
            self._previews[url] = {"status": "loading", "ts": now}
        try:
            self._meta_exec.submit(self._preview_worker, url)
        except RuntimeError:
            pass

    def preview(self, url: str) -> dict | None:
        url = (url or "").strip()
        with self._lock:
            state = self._previews.get(url)
            return dict(state) if state else None

    def is_downloaded(self, video_id: str) -> dict | None:
        return self._library.find(video_id)

    def _preview_worker(self, url: str) -> None:
        if self._closed:
            return
        try:
            meta = self._extract_meta(url)
        except ExtractError as error:
            state = {"status": "error", "error": str(error), "ts": time.time()}
        except Exception as error:  # defensive: never kill the worker pool
            state = {"status": "error", "error": str(error)[:280], "ts": time.time()}
        else:
            state = {"status": "ready", "meta": meta, "ts": time.time()}
        with self._lock:
            self._previews[url] = state

    # ------------------------------------------------------------------ #
    # Download worker
    # ------------------------------------------------------------------ #

    def _download_worker(self, job: Job) -> None:
        if self._closed:
            return
        if job.cancel_event.is_set():
            self._finish(job, "cancelled")
            return
        try:
            meta = self._extract_meta(job.url)
        except ExtractError as error:
            self._finish(job, "error", error=str(error))
            return
        except Exception as error:  # defensive
            self._finish(job, "error", error=str(error)[:280])
            return

        with self._lock:
            job.video_id = meta["id"]
            job.title = meta["title"]
            job.uploader = meta["uploader"]
            job.duration = meta["duration"]
            job.thumbnail_path = meta.get("thumb_path", "")
            job.status = "queued"
            self._previews[job.url] = {
                "status": "ready",
                "meta": meta,
                "ts": time.time(),
            }

        if job.cancel_event.is_set():
            self._finish(job, "cancelled")
            return

        existing = self._library.find(meta["id"])
        if existing:
            self._finish(
                job,
                "duplicate",
                filename=existing.get("path", ""),
                size=int(existing.get("size") or 0),
                progress=1.0,
            )
            return

        if not self._limiter.acquire(job.cancel_event):
            self._finish(job, "cancelled")
            return
        try:
            if job.cancel_event.is_set():
                self._finish(job, "cancelled")
                return
            with self._lock:
                job.status = "downloading"
            cmd = self._download_cmd(job)
            returncode, filepath, tail = self._run_download(job, cmd)
        except ExtractError as error:
            self._finish(job, "error", error=str(error))
            return
        except Exception as error:  # defensive
            self._finish(job, "error", error=str(error)[:280])
            return
        finally:
            self._limiter.release()

        if job.cancel_event.is_set():
            self._finish(job, "cancelled")
            return

        if returncode != 0:
            log.warning(
                "yt-dlp failed for %s (exit %s): %s",
                job.url,
                returncode,
                " | ".join(tail[-4:]),
            )
            error_text = self._friendly_error("\n".join(tail))
            self._finish(job, "error", error=error_text)
            return

        with self._lock:
            job.status = "processing"

        path = Path(filepath) if filepath else None
        if path is None or not path.exists():
            path = self._find_output(meta["id"])
        if path is None or not path.exists():
            self._finish(job, "error", error="Download finished but the file could not be found.")
            return

        try:
            size = path.stat().st_size
        except OSError:
            size = 0

        try:
            self._library.add(
                {
                    "video_id": meta["id"],
                    "url": job.url,
                    "title": job.title,
                    "uploader": job.uploader,
                    "path": str(path),
                    "size": size,
                    "duration": job.duration,
                    "quality": job.quality,
                    "timestamp": time.time(),
                    "thumbnail": job.thumbnail_path,
                }
            )
        except Exception:
            pass

        self._finish(job, "done", filename=str(path), size=size, progress=1.0)

    def _finish(self, job: Job, status: str, **fields: Any) -> None:
        with self._lock:
            job.status = status
            job.finished_at = time.time()
            for key, value in fields.items():
                setattr(job, key, value)
            if status == "done":
                job.progress = 1.0
                if job.total and not job.downloaded:
                    job.downloaded = job.total

    def _download_cmd(self, job: Job) -> list[str]:
        settings = self._settings
        ytdlp = util.which_ytdlp()
        if not ytdlp:
            raise ExtractError(
                "yt-dlp is not installed. Install it with your package manager "
                "(for example: sudo pacman -S yt-dlp)."
            )
        output_dir = Path(settings.download_dir).expanduser()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise ExtractError(f"Cannot create the download folder: {error}") from error

        template = str(
            output_dir
            / "%(uploader,channel,creator,id)s - %(title).100B [%(id)s].%(ext)s"
        )
        cmd = [
            ytdlp,
            "--ignore-config",
            "--no-playlist",
            "--no-colors",
            "--newline",
            "--progress",
            "--progress-template",
            _PROGRESS_PREFIX
            + "%(progress.downloaded_bytes)s|%(progress.total_bytes)s|"
            + "%(progress.total_bytes_estimate)s|%(progress.speed)s|%(progress.eta)s",
            "--print",
            "after_move:" + _FILE_PREFIX + "%(filepath)s",
            "--no-simulate",
            "--no-overwrites",
            "--socket-timeout",
            "25",
            "--retries",
            "3",
            "--fragment-retries",
            "3",
            "--concurrent-fragments",
            "4",
            "-o",
            template,
        ]
        cmd += FORMAT_ARGS[job.quality]
        if settings.embed_metadata:
            cmd.append("--embed-metadata")
        if settings.embed_thumbnail and job.quality != "audio":
            cmd.append("--embed-thumbnail")
        cmd += self._cookie_args(settings)
        cmd.append(job.url)
        return cmd

    def _run_download(self, job: Job, cmd: list[str]) -> tuple[int, str, list[str]]:
        env = os.environ.copy()
        env.setdefault("PYTHONIOENCODING", "utf-8")
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                start_new_session=True,
                env=env,
            )
        except FileNotFoundError as error:
            raise ExtractError("yt-dlp could not be started.") from error

        with self._lock:
            job.proc = proc

        filepath = ""
        tail: deque[str] = deque(maxlen=14)
        try:
            assert proc.stdout is not None
            for raw_line in proc.stdout:
                line = raw_line.rstrip("\r\n")
                if not line:
                    continue
                if line.startswith(_PROGRESS_PREFIX):
                    self._parse_progress(job, line[len(_PROGRESS_PREFIX) :])
                elif line.startswith(_FILE_PREFIX):
                    filepath = line[len(_FILE_PREFIX) :].strip()
                else:
                    tail.append(line)
            returncode = proc.wait()
        finally:
            if proc.poll() is None:
                proc.kill()
            with self._lock:
                job.proc = None
        return returncode, filepath, list(tail)

    def _parse_progress(self, job: Job, payload: str) -> None:
        parts = payload.split("|")
        if len(parts) < 5:
            return

        def number(value: str) -> float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        downloaded = number(parts[0])
        total = number(parts[1]) or number(parts[2])
        speed = number(parts[3])
        eta = int(number(parts[4]))
        with self._lock:
            job.downloaded = int(downloaded)
            job.total = int(total)
            job.speed = speed
            job.eta = eta
            if job.total > 0:
                job.progress = max(0.0, min(1.0, downloaded / job.total))
            if job.status in {"queued", "processing"}:
                job.status = "downloading"

    # ------------------------------------------------------------------ #
    # Metadata
    # ------------------------------------------------------------------ #

    def _extract_meta(self, url: str) -> dict:
        now = time.time()
        with self._lock:
            cached = self._meta_cache.get(url)
            if cached and now - cached[0] < self.META_TTL:
                return dict(cached[1])

        ytdlp = util.which_ytdlp()
        if not ytdlp:
            raise ExtractError(
                "yt-dlp is not installed. Install it with your package manager "
                "(for example: sudo pacman -S yt-dlp)."
            )

        cmd = [
            ytdlp,
            "--ignore-config",
            "--no-playlist",
            "--no-warnings",
            "--no-check-formats",
            "--socket-timeout",
            "20",
            "--retries",
            "2",
            "-J",
        ]
        cmd += self._cookie_args(self._settings)
        cmd.append(url)

        try:
            with self._meta_sem:
                if self._closed:
                    raise ExtractError("Cancelled.")
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    start_new_session=True,
                )
                with self._lock:
                    self._meta_procs.add(proc)
                try:
                    try:
                        stdout, stderr = proc.communicate(timeout=90)
                    except subprocess.TimeoutExpired as error:
                        self._terminate(proc)
                        proc.communicate()
                        raise ExtractError(
                            "Timed out while contacting Instagram. Check your connection and retry."
                        ) from error
                finally:
                    with self._lock:
                        self._meta_procs.discard(proc)
        except FileNotFoundError as error:
            raise ExtractError("yt-dlp could not be started.") from error

        if proc.returncode != 0:
            log.warning(
                "yt-dlp metadata failed for %s (exit %s): %s",
                url,
                proc.returncode,
                (stderr or stdout or "").strip()[-500:],
            )
            raise ExtractError(self._friendly_error(stderr or stdout))

        try:
            data = json.loads(stdout)
        except (ValueError, TypeError) as error:
            raise ExtractError("Could not read the video information returned by yt-dlp.") from error

        if not isinstance(data, dict):
            raise ExtractError("Unexpected response from yt-dlp.")

        if data.get("_type") == "playlist":
            entries = [entry for entry in (data.get("entries") or []) if entry]
            if not entries:
                raise ExtractError("No downloadable video was found at that link.")
            parent = data
            data = dict(entries[0])
            for key in ("uploader", "channel", "creator", "thumbnail", "description"):
                if not data.get(key) and parent.get(key):
                    data[key] = parent[key]

        video_id = str(data.get("id") or "").strip()
        if not video_id:
            raise ExtractError("This link does not contain a downloadable video.")

        title = (
            data.get("title")
            or data.get("description")
            or data.get("fulltitle")
            or "Instagram reel"
        )
        title = " ".join(str(title).split())
        if title.lower().startswith("video by") and data.get("description"):
            caption = str(data["description"]).strip().splitlines()
            for line in caption:
                cleaned = " ".join(line.split())
                if cleaned and not cleaned.startswith("#"):
                    title = cleaned
                    break
        if len(title) > 200:
            title = title[:200].rstrip() + "…"
        uploader = (
            data.get("uploader")
            or data.get("channel")
            or data.get("creator")
            or data.get("uploader_id")
            or ""
        )
        thumb_url = data.get("thumbnail") or ""
        if not thumb_url:
            thumbnails = data.get("thumbnails") or []
            if thumbnails and isinstance(thumbnails[-1], dict):
                thumb_url = thumbnails[-1].get("url") or ""

        meta = {
            "id": video_id,
            "title": title,
            "uploader": str(uploader),
            "duration": float(data.get("duration") or 0),
            "thumbnail": thumb_url,
            "thumb_path": self._fetch_thumbnail(video_id, thumb_url),
            "webpage_url": data.get("webpage_url") or url,
            "description": str(data.get("description") or ""),
        }

        with self._lock:
            if len(self._meta_cache) >= self.META_CACHE_MAX:
                oldest = min(self._meta_cache, key=lambda key: self._meta_cache[key][0])
                self._meta_cache.pop(oldest, None)
            self._meta_cache[url] = (time.time(), dict(meta))
        return meta

    def _fetch_thumbnail(self, video_id: str, thumb_url: str) -> str:
        if not video_id or not thumb_url:
            return ""
        suffix = Path(urlsplit(thumb_url).path).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            suffix = ".jpg"
        folder = util.cache_dir() / "thumbnails"
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"{video_id}{suffix}"
        try:
            if target.exists() and target.stat().st_size > 0:
                return str(target)
        except OSError:
            pass
        try:
            request = urllib.request.Request(
                thumb_url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
                    )
                },
            )
            with urllib.request.urlopen(request, timeout=12) as response:
                payload = response.read(8 * 1024 * 1024 + 1)
            if not payload or len(payload) > 8 * 1024 * 1024:
                return ""
            temp = target.with_suffix(target.suffix + ".part")
            temp.write_bytes(payload)
            os.replace(temp, target)
            return str(target)
        except Exception:
            return ""

    def _find_output(self, video_id: str) -> Path | None:
        folder = Path(self._settings.download_dir).expanduser()
        try:
            candidates = [
                item
                for item in folder.iterdir()
                if item.is_file()
                and f"[{video_id}]" in item.name
                and not item.name.endswith((".part", ".ytdl"))
            ]
        except OSError:
            return None
        if not candidates:
            return None
        try:
            return max(candidates, key=lambda item: item.stat().st_mtime)
        except OSError:
            return None

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _cookie_args(settings: Settings) -> list[str]:
        if settings.cookies_mode == "browser" and settings.cookies_browser:
            return ["--cookies-from-browser", settings.cookies_browser]
        if settings.cookies_mode == "file" and settings.cookies_file:
            path = Path(settings.cookies_file).expanduser()
            if path.is_file():
                return ["--cookies", str(path)]
        return []

    @staticmethod
    def _friendly_error(text: str) -> str:
        clean = _ANSI_RE.sub("", text or "")
        lines = [line.strip() for line in clean.splitlines() if line.strip()]
        errors = [
            line
            for line in lines
            if line.upper().startswith("ERROR")
            or line.lower().startswith("error:")
            or "error:" in line.lower()
        ]
        raw = errors[-1] if errors else (lines[-1] if lines else "Download failed.")
        lowered = raw.lower()
        if "cookies database" in lowered or (
            "could not find" in lowered and "cookies" in lowered
        ):
            return (
                "Could not read cookies from the selected browser. Close the browser "
                "(including private windows), make sure you are logged in to "
                "instagram.com, then retry."
            )
        if "ffmpeg" in lowered and ("not found" in lowered or "not installed" in lowered):
            return "ffmpeg is required to merge video and audio. Install it and retry."
        if "429" in lowered or "too many requests" in lowered:
            return (
                "Instagram rate-limited this request. Wait a few minutes, or enable "
                "cookies in Preferences, then retry."
            )
        if any(
            token in lowered
            for token in (
                "login",
                "cookies",
                "rate-limit",
                "rate limit",
                "empty media response",
                "checkpoint",
                "challenge",
                "blocked",
                "consent",
            )
        ):
            return (
                "Instagram blocked this request. Enable cookies in Preferences "
                "(log in to Instagram in your browser), then retry."
            )
        if "private" in lowered:
            return "This post is private. Enable cookies for an account that follows it."
        if "not available" in lowered or "unavailable" in lowered:
            return "This content is unavailable (removed, private, or region-locked)."
        if "unsupported url" in lowered:
            return "That link is not a supported Instagram reel."
        if "timed out" in lowered or "timeout" in lowered:
            return "The connection timed out. Check your internet connection and retry."
        if "unable to extract" in lowered:
            return (
                "Instagram returned an unexpected response. Update yt-dlp and try "
                "again; cookies may also help."
            )
        if "unable to download" in lowered and "http error" in lowered:
            return "Instagram refused the download. Try again, or enable cookies in Preferences."
        raw = re.sub(r"^(?:ERROR|error):\s*", "", raw)
        return raw[:280]

    @staticmethod
    def _terminate(proc: subprocess.Popen | None) -> None:
        if proc is None or proc.poll() is not None:
            return
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            try:
                proc.terminate()
            except Exception:
                return
