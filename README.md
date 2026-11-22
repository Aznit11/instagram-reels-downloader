# 📹 Instagram Reels Downloader

<img src="instagram-reels-downloader.svg" width="96" align="right" alt="App icon">

A fast, native **GTK 4 + libadwaita** desktop app for saving Instagram reels — with a queue, live progress, previews, quality selection and a searchable library.

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Platform: Linux](https://img.shields.io/badge/Platform-Linux-orange.svg)
![GTK](https://img.shields.io/badge/GTK-4-success.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)

## ✨ What's new in 2.0

- **Modern GTK 4 / libadwaita UI** — follows your system accent color and light/dark theme, with smooth transitions and toasts.
- **Parallel download queue** — multiple reels at once (configurable), per-item progress, speed, ETA, cancel and retry.
- **Instant previews** — title, creator, cover image and “already downloaded” detection before you commit.
- **Background library** — every finished reel is recorded with a thumbnail; search it, open it, reveal it, copy its link or delete it from the History tab.
- **Quality control** — best available, 1080p, 720p, 480p, or audio-only MP3.
- **Cookies support** — import an Instagram session from Firefox, Chrome, Chromium, Brave, Edge, Vivaldi or Opera for login-walled posts.
- **Batch links and drag & drop** — paste several URLs at once, or drop links/text files onto the window.
- **Clipboard detection** — offers the reel link already sitting in your clipboard.
- **Desktop notifications** — optional, only while the window is in the background.
- **Smarter and faster** — no heavy yt-dlp import at startup, throttled UI updates, cached previews and thumbnails, duplicate skipping.
- **Keyboard-first** — `Ctrl+Enter` to download, `Ctrl+L` to focus the link field, `Ctrl+,` for preferences.

## 🚀 Install

### Arch Linux (AUR)

The repository ships a `PKGBUILD`; once the package is published to the AUR you can install it with:

```bash
yay -S instagram-reels-downloader
```

Or build the package locally right away:

```bash
git clone https://github.com/Aznit11/instagram-reels-downloader.git
cd instagram-reels-downloader
makepkg -si
```

### Any Linux distribution

Install the runtime dependencies first (GTK 4.10+ and libadwaita 1.5+):

| Distribution | Command |
| --- | --- |
| Arch | `sudo pacman -S python-gobject gtk4 libadwaita yt-dlp ffmpeg` |
| Debian / Ubuntu | `sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 yt-dlp ffmpeg` |
| Fedora | `sudo dnf install python3-gobject gtk4 libadwaita yt-dlp ffmpeg` |

Then install the app:

```bash
git clone https://github.com/Aznit11/instagram-reels-downloader.git
cd instagram-reels-downloader
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install .
instagram-reels-downloader
```

Or run straight from the checkout without installing:

```bash
./run-gui.sh
# equivalent to: python3 -m ird
```

You can also pass links on the command line, which works even when the app is
already running:

```bash
instagram-reels-downloader "https://www.instagram.com/reel/…/"
```

> `yt-dlp` must be on your `PATH`. Set `YT_DLP=/path/to/yt-dlp` to override it.

## 🎬 Usage

1. Copy a reel link (`https://www.instagram.com/reel/…`) or several links.
2. Paste it into the field, or drag a link onto the window.
3. Pick a quality (your choice is remembered).
4. Press **Download** (`Ctrl+Enter`). A preview card appears while the post is inspected.
5. Watch the queue; use the buttons on each row to cancel, retry, open the file or remove it.
6. Switch to **History** to browse everything you have saved.

Reels are saved to `~/Downloads/Instagram_Reels/` by default. Change it in **Preferences → Downloads**.

### Login-walled or private posts

Instagram increasingly asks for a session. Open **Preferences → Account** and either:

- choose **Import from a web browser**, pick the browser where you are logged in to instagram.com, or
- choose **Use a cookies.txt file** and select an exported Netscape cookies file.

Cookies are only used locally by yt-dlp; nothing is uploaded anywhere.

### Quality

| Choice | Result |
| --- | --- |
| Best available | Highest video + audio, merged to MP4 |
| 1080p / 720p / 480p | Caps the resolution, still merged to MP4 |
| Audio only (MP3) | Extracts the soundtrack at best VBR quality |

`ffmpeg` is required for merging and audio extraction.

## ⌨️ Shortcuts

| Action | Shortcut |
| --- | --- |
| Download links in the field | `Ctrl+Enter` |
| Focus the link field | `Ctrl+L` |
| Paste | `Ctrl+V` |
| Open downloads folder | `Ctrl+O` |
| Clear finished downloads | `Ctrl+Delete` |
| Preferences | `Ctrl+,` |
| Shortcut sheet | `Ctrl+?` |
| Quit | `Ctrl+Q` |

## ⚙️ How it works

- The GUI is pure Python + PyGObject; there is no web view.
- Downloads are handled by one `yt-dlp` process per job, so cancelling a job cleanly stops the transfer.
- A thread pool downloads several reels concurrently; progress is collected in a thread-safe snapshot that the GTK main loop polls at 120 ms.
- Settings, the download library and thumbnails live in XDG directories:
  - `~/.config/instagram-reels-downloader/settings.json`
  - `~/.config/instagram-reels-downloader/library.json`
  - `~/.cache/instagram-reels-downloader/thumbnails/`

## 🧱 Project layout

```
ird/
├── app.py          # Adw.Application, actions, theme and CSS
├── config.py       # settings + library persistence
├── engine.py       # yt-dlp queue, metadata, previews, cancellation
├── util.py         # URLs, formatting, XDG paths, notifications
├── style.css       # libadwaita-aware styling
└── ui/
    ├── window.py       # main window, queue and history
    ├── preferences.py  # preferences dialog
    └── widgets.py      # thumbnails and small widgets
instagram_downloader_gui.py  # legacy entry point → ird.app:main
```

## 🐛 Troubleshooting

**“No module named 'gi'”** — install PyGObject (`python-gobject` / `python3-gi`).

**“Gtk 4.0 not found” / “Adw 1 not found”** — install GTK 4 and libadwaita (`gtk4`, `libadwaita` / `gir1.2-gtk-4.0`, `gir1.2-adw-1`).

**Instagram blocked the request** — update yt-dlp (`sudo pacman -S yt-dlp` or `pip install -U yt-dlp`), then enable cookies in Preferences. Log in to instagram.com in the selected browser and close private windows.

**Downloads stay at 0%** — check that `ffmpeg` and `yt-dlp` are installed and that you can reach Instagram in a browser.

**Progress looks stuck after a network drop** — the job retries automatically a few times; cancel and retry if it does not recover.

**Running from source** — `./run-gui.sh` checks GTK/PyGObject and starts `python3 -m ird`.

## 🤝 Contributing

Issues and pull requests are welcome at
<https://github.com/Aznit11/instagram-reels-downloader>.

```bash
git clone https://github.com/Aznit11/instagram-reels-downloader.git
cd instagram-reels-downloader
python3 -m ird        # run from source
python3 -m build      # build a wheel
```

## 📝 License

MIT — see [LICENSE](LICENSE).

## ⚠️ Disclaimer

This tool is for personal use. Respect Instagram's terms of service and creators' rights; only download content you have permission to save.
