"""Core, GUI-free tests: URL parsing, settings, library and error messages."""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from ird import util
from ird.config import Library, Settings
from ird.engine import DownloadManager, Job


class UrlTests(unittest.TestCase):
    def test_extracts_reel_and_post_urls(self):
        text = (
            "watch https://www.instagram.com/reel/ABC123/?igsh=xyz and "
            "https://instagram.com/p/DEF456/ also https://instagr.am/reel/GHI789"
        )
        urls = util.extract_urls(text)
        self.assertEqual(len(urls), 3)
        self.assertIn("https://instagram.com/p/DEF456/", urls)

    def test_deduplicates_with_or_without_trailing_slash(self):
        urls = util.extract_urls(
            "https://www.instagram.com/reel/ABC123/ "
            "https://www.instagram.com/reel/ABC123"
        )
        self.assertEqual(len(urls), 1)

    def test_supports_username_and_share_links(self):
        for url, code in (
            ("https://www.instagram.com/some.user/reel/ABC123/", "ABC123"),
            ("https://www.instagram.com/share/reel/BAFxyz", "BAFxyz"),
            ("https://www.instagram.com/tv/ABC123/", "ABC123"),
        ):
            urls = util.extract_urls(url)
            self.assertEqual(len(urls), 1, url)
            self.assertTrue(urls[0].rstrip("/").endswith(code), urls[0])

    def test_rejects_non_instagram_links(self):
        self.assertFalse(util.is_instagram_url("https://youtube.com/shorts/abc"))
        self.assertFalse(util.extract_urls("just some text"))

    def test_short_url(self):
        self.assertEqual(
            util.short_url("https://www.instagram.com/reel/ABC123/?igsh=x"),
            "Reel ABC123",
        )


class FormattingTests(unittest.TestCase):
    def test_sizes_and_times(self):
        self.assertEqual(util.human_size(0), "—")
        self.assertEqual(util.human_size(1536), "1.5 KB")
        self.assertEqual(util.human_duration(83), "1:23")
        self.assertEqual(util.human_duration(3723), "1:02:03")


class SettingsTests(unittest.TestCase):
    def test_round_trip_and_sanitizing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            settings = Settings(_path=path)
            settings.quality = "720"
            settings.concurrency = 99
            settings.theme = "dark"
            settings.save()

            loaded = Settings.load(path)
            self.assertEqual(loaded.quality, "720")
            self.assertEqual(loaded.concurrency, 6)
            self.assertEqual(loaded.theme, "dark")

    def test_invalid_values_fall_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            path.write_text(
                json.dumps(
                    {"quality": "8k", "theme": "neon", "cookies_mode": "telepathy"}
                ),
                encoding="utf-8",
            )
            loaded = Settings.load(path)
            self.assertEqual(loaded.quality, "best")
            self.assertEqual(loaded.theme, "system")
            self.assertEqual(loaded.cookies_mode, "none")


class LibraryTests(unittest.TestCase):
    def test_add_find_remove_and_persist(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            downloaded = tmp_path / "video.mp4"
            downloaded.write_bytes(b"x" * 32)
            path = tmp_path / "library.json"
            library = Library(path)

            entry = library.add(
                {
                    "video_id": "abc",
                    "title": "A reel",
                    "path": str(downloaded),
                    "size": 32,
                }
            )
            self.assertIsNotNone(library.find("abc"))
            self.assertEqual(library.all()[0]["title"], "A reel")

            reloaded = Library(path)
            self.assertEqual(reloaded.find("abc")["entry_id"], entry["entry_id"])
            self.assertTrue(reloaded.remove(entry["entry_id"]))
            self.assertIsNone(reloaded.find("abc"))

    def test_missing_file_is_not_a_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            library = Library(Path(tmp) / "library.json")
            library.add(
                {
                    "video_id": "gone",
                    "title": "Deleted",
                    "path": str(Path(tmp) / "missing.mp4"),
                }
            )
            self.assertIsNone(library.find("gone"))
            self.assertIsNotNone(library.find("gone", require_exists=False))


class EngineHelperTests(unittest.TestCase):
    def test_friendly_errors(self):
        cookie = DownloadManager._friendly_error(
            "ERROR: [Instagram] login required to view this post"
        )
        self.assertIn("cookies", cookie.lower())

        missing = DownloadManager._friendly_error(
            "ERROR: [Instagram] Requested content is not available"
        )
        self.assertIn("unavailable", missing.lower())

        generic = DownloadManager._friendly_error("ERROR: something odd happened")
        self.assertEqual(generic, "something odd happened")

    def test_progress_parsing(self):
        job = Job(id="1", url="https://example.com", quality="best")
        job.status = "downloading"
        manager = DownloadManager.__new__(DownloadManager)
        manager._lock = __import__("threading").RLock()
        DownloadManager._parse_progress(
            manager, job, "500|1000|NA|250.0|2"
        )
        self.assertEqual(job.downloaded, 500)
        self.assertEqual(job.total, 1000)
        self.assertAlmostEqual(job.progress, 0.5)
        self.assertEqual(job.speed, 250.0)
        self.assertEqual(job.eta, 2)


if __name__ == "__main__":
    unittest.main()
