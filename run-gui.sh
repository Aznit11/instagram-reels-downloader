#!/usr/bin/env bash
# Launch the native GTK4 app from a source checkout.
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required." >&2
  exit 1
fi

if ! python3 -c 'import gi; gi.require_version("Gtk", "4.0"); gi.require_version("Adw", "1")' >/dev/null 2>&1; then
  cat >&2 <<'EOF'
GTK4 and libadwaita Python bindings are missing.

Arch Linux:
  sudo pacman -S gtk4 libadwaita python-gobject

Debian / Ubuntu:
  sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1

Fedora:
  sudo dnf install python3-gobject gtk4 libadwaita
EOF
  exit 1
fi

if ! command -v yt-dlp >/dev/null 2>&1; then
  echo "Warning: yt-dlp was not found. Install it (sudo pacman -S yt-dlp) before downloading." >&2
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Warning: ffmpeg was not found. Video and audio merging may fail." >&2
fi

exec python3 -m ird "$@"
