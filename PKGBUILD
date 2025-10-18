# Maintainer: Your Name <your.email@example.com>
pkgname=instagram-reels-downloader
pkgver=1.0.0
pkgrel=1
pkgdesc="A beautiful native GTK application for downloading Instagram reels with one click"
arch=('any')
url="https://github.com/yourusername/instagram-reels-downloader"
license=('MIT')
depends=('python' 'python-gobject' 'gtk3' 'python-pip')
makedepends=('python-setuptools')
source=("${pkgname}-${pkgver}.tar.gz::https://github.com/yourusername/${pkgname}/archive/v${pkgver}.tar.gz")
sha256sums=('SKIP')  # Replace with actual checksum after uploading to GitHub

prepare() {
    cd "${srcdir}/${pkgname}-${pkgver}"
}

build() {
    cd "${srcdir}/${pkgname}-${pkgver}"
    python setup.py build
}

package() {
    cd "${srcdir}/${pkgname}-${pkgver}"
    
    # Install Python application
    python setup.py install --root="${pkgdir}" --optimize=1 --skip-build
    
    # Install desktop file
    install -Dm644 instagram-reels-downloader.desktop \
        "${pkgdir}/usr/share/applications/instagram-reels-downloader.desktop"
    
    # Install icon
    install -Dm644 icon.png \
        "${pkgdir}/usr/share/pixmaps/instagram-reels-downloader.png"
    
    # Install documentation
    install -Dm644 README-NATIVE.md \
        "${pkgdir}/usr/share/doc/${pkgname}/README.md"
    
    # Install license
    install -Dm644 LICENSE \
        "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}
