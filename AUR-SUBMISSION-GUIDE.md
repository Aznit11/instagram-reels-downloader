# Publishing to the AUR

The repository ships a ready-to-use `PKGBUILD` and `.SRCINFO` for
`instagram-reels-downloader` 2.0.0.

## 1. Tag the release

The PKGBUILD pulls the `v2.0.0` git tag, so the tag must exist on GitHub:

```bash
git tag -a v2.0.0 -m "Instagram Reels Downloader 2.0.0"
git push origin main
git push origin v2.0.0
```

For a new version, update `pkgver` in `PKGBUILD` (and `pyproject.toml` /
`ird/__init__.py`), then regenerate `.SRCINFO`:

```bash
makepkg --printsrcinfo > .SRCINFO
```

## 2. Test the package locally

```bash
makepkg -si
instagram-reels-downloader
```

Check that the desktop entry and icon are installed:

```bash
/usr/share/applications/io.github.aznit11.InstagramReelsDownloader.desktop
/usr/share/icons/hicolor/scalable/apps/instagram-reels-downloader.svg
```

## 3. Push to the AUR

Create the AUR repository once (the AUR namespace is separate from GitHub):

```bash
git clone ssh://aur@aur.archlinux.org/instagram-reels-downloader.git aur-repo
cp PKGBUILD .SRCINFO aur-repo/
cd aur-repo
git add PKGBUILD .SRCINFO
git commit -m "Initial import: 2.0.0"
git push
```

If the package name is already taken, pick a different `pkgname` (for example
`instagram-reels-downloader-git`) and update `pkgname` and `.SRCINFO`.

## Notes

- Runtime dependencies are `python`, `python-gobject`, `gtk4`, `libadwaita`,
  `yt-dlp` and `ffmpeg`.
- The source uses the GitHub tag (`git+https://…#tag=v2.0.0`) with
  `sha256sums=('SKIP')`. VCS sources are allowed to use `SKIP`, but a release
  tarball with a real checksum is preferable once releases are published on
  GitHub.
- Keep `pkgver` in `PKGBUILD`, `pyproject.toml` and `ird/__init__.py` in sync.
