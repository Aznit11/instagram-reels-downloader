# Maintainer: Aznit11 <admin@movies-hood.com>
pkgname=instagram-reels-downloader
pkgver=2.0.0
pkgrel=1
pkgdesc="Fast, modern GTK4 application for downloading Instagram reels"
arch=('any')
url="https://github.com/Aznit11/instagram-reels-downloader"
license=('MIT')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita>=1.5' 'yt-dlp' 'ffmpeg')
makedepends=('python-build' 'python-installer' 'python-wheel' 'python-setuptools')
source=("${pkgname}::git+https://github.com/Aznit11/${pkgname}.git#tag=v${pkgver}")
sha256sums=('SKIP')

build() {
  cd "${pkgname}"
  python -m build --wheel --no-isolation
}

package() {
  cd "${pkgname}"
  python -m installer --destdir="${pkgdir}" dist/*.whl
  install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
  install -Dm644 README.md "${pkgdir}/usr/share/doc/${pkgname}/README.md"
}
