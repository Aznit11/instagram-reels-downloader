# 📋 Publishing Checklist

Before publishing your Instagram Reels Downloader to the public, complete these steps:

## ✅ Pre-Publishing Checklist

### 1. Code Quality
- [ ] Test the app thoroughly with various Instagram URLs
- [ ] Handle all error cases gracefully
- [ ] Ensure download progress works correctly
- [ ] Test folder selection functionality
- [ ] Verify app works on fresh installation

### 2. Clean Up Project
- [ ] Delete web interface files (see FILES-TO-DELETE.txt)
- [ ] Remove venv/ directory from git
- [ ] Remove __pycache__ directories
- [ ] Clean up any test files

```bash
rm -f app.py run.sh
rm -rf templates/
rm -rf venv/
find . -type d -name "__pycache__" -exec rm -rf {} +
```

### 3. Update Personal Information
- [ ] Edit `setup.py` - Add your name and email
- [ ] Edit `PKGBUILD` - Add your name and email as maintainer
- [ ] Edit `LICENSE` - Add your name and year
- [ ] Update GitHub URLs in all files

### 4. Documentation
- [ ] Review README.md for accuracy
- [ ] Update screenshots (if you add any)
- [ ] Check all links work
- [ ] Verify installation instructions
- [ ] Spell check all documentation

### 5. Version Control
- [ ] Initialize git repository
- [ ] Add all necessary files
- [ ] Create initial commit
- [ ] Add .gitignore

```bash
git init
git add instagram_downloader_gui.py setup.py LICENSE README.md
git add PKGBUILD .SRCINFO instagram-reels-downloader.desktop
git add run-gui.sh requirements.txt MANIFEST.in .gitignore
git add QUICKSTART.md AUR-SUBMISSION-GUIDE.md QUICK-AUR-GUIDE.md
git commit -m "Initial commit: Instagram Reels Downloader v1.0.0"
```

### 6. GitHub Setup
- [ ] Create GitHub account (if needed)
- [ ] Create new public repository named `instagram-reels-downloader`
- [ ] Push code to GitHub
- [ ] Create release v1.0.0
- [ ] Add release notes
- [ ] Download release tarball URL

```bash
git remote add origin git@github.com:YOUR_USERNAME/instagram-reels-downloader.git
git branch -M main
git push -u origin main
```

### 7. Update PKGBUILD
- [ ] Replace `yourusername` with your GitHub username
- [ ] Get SHA256 checksum of release tarball
- [ ] Update sha256sums in PKGBUILD
- [ ] Test build locally with `makepkg -si`

```bash
# Get checksum
curl -sL "https://github.com/YOUR_USERNAME/instagram-reels-downloader/archive/v1.0.0.tar.gz" | sha256sum
```

### 8. AUR Account Setup
- [ ] Register at https://aur.archlinux.org/register
- [ ] Generate SSH key (if needed)
- [ ] Add SSH public key to AUR account
- [ ] Test SSH connection

```bash
ssh-keygen -t ed25519 -C "your@email.com"
cat ~/.ssh/id_ed25519.pub
# Add to https://aur.archlinux.org/account/
```

### 9. AUR Submission
- [ ] Clone AUR repository
- [ ] Copy PKGBUILD and generate .SRCINFO
- [ ] Commit and push to AUR
- [ ] Verify package appears on AUR website

```bash
git clone ssh://aur@aur.archlinux.org/instagram-reels-downloader.git aur-repo
cd aur-repo
cp ../PKGBUILD .
makepkg --printsrcinfo > .SRCINFO
git add PKGBUILD .SRCINFO
git commit -m "Initial upload: Instagram Reels Downloader v1.0.0"
git push
```

### 10. Post-Publishing
- [ ] Add badges to README (AUR version, license, etc.)
- [ ] Test installation from AUR
- [ ] Share on social media (optional)
- [ ] Monitor for issues/comments
- [ ] Respond to user feedback

## 📊 Quality Checklist

### Testing on Clean System
- [ ] Test on fresh Arch Linux install
- [ ] Test on Ubuntu/Debian
- [ ] Test on Fedora
- [ ] Verify all dependencies install correctly
- [ ] Test first-time user experience

### Functionality Tests
- [ ] Download public Instagram reel
- [ ] Test with various reel URLs
- [ ] Test error handling (invalid URL)
- [ ] Test error handling (network issues)
- [ ] Test folder selection
- [ ] Test "Open Downloads Folder" button
- [ ] Test progress bar updates
- [ ] Test multiple consecutive downloads

### UI/UX Tests
- [ ] Window opens properly
- [ ] All text is readable
- [ ] Buttons respond correctly
- [ ] Progress bar is visible
- [ ] Status messages are clear
- [ ] App doesn't freeze during download

## 🔧 Final Touches

### Optional Enhancements
- [ ] Add app icon (256x256 PNG)
- [ ] Create screenshots for README
- [ ] Add demo GIF/video
- [ ] Create project website
- [ ] Add internationalization (i18n)
- [ ] Add keyboard shortcuts
- [ ] Add settings/preferences dialog
- [ ] Add download history

### Marketing (Optional)
- [ ] Post on r/linux
- [ ] Post on r/archlinux
- [ ] Tweet about it
- [ ] Share on Linux forums
- [ ] Add to awesome-linux lists
- [ ] Create YouTube demo

## ✨ Ready to Publish!

Once all checkboxes are complete, your app is ready for the world!

**Current Version:** 1.0.0
**Target Platform:** Linux (all distros)
**Distribution:** AUR (Arch User Repository)

---

**Good luck with your publish! 🚀**
