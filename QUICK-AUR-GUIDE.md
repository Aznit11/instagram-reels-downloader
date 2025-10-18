# 🚀 Quick AUR Submission Guide

## TL;DR - 5 Minute Setup

### 1. Create AUR Account
→ Go to https://aur.archlinux.org/register

### 2. Create GitHub Repository
```bash
cd "/home/azeroual/Documents/Instagram reels downloader"

# Initialize and push to GitHub
git init
git add instagram_downloader_gui.py setup.py LICENSE README-NATIVE.md instagram-reels-downloader.desktop
git commit -m "Initial commit v1.0.0"
git remote add origin git@github.com:YOUR_USERNAME/instagram-reels-downloader.git
git push -u origin main
```

### 3. Create GitHub Release
- Go to your repo → Releases → Create release
- Tag: `v1.0.0`
- Publish

### 4. Update PKGBUILD
```bash
# Get checksum
curl -sL "https://github.com/YOUR_USERNAME/instagram-reels-downloader/archive/v1.0.0.tar.gz" | sha256sum

# Edit PKGBUILD:
# - Replace 'yourusername' with your GitHub username
# - Replace 'SKIP' with the actual sha256sum
# - Add your name and email
nano PKGBUILD
```

### 5. Submit to AUR
```bash
# Test it works
makepkg -si

# Clone AUR repo
git clone ssh://aur@aur.archlinux.org/instagram-reels-downloader.git aur-repo
cd aur-repo

# Copy files
cp ../PKGBUILD .
makepkg --printsrcinfo > .SRCINFO

# Push to AUR
git add PKGBUILD .SRCINFO
git commit -m "Initial upload v1.0.0"
git push
```

## ✅ Done!

Anyone can now install your app:
```bash
yay -S instagram-reels-downloader
```

## 📚 Full Guide
See `AUR-SUBMISSION-GUIDE.md` for detailed instructions.

## 🔑 SSH Key Setup (if needed)
```bash
ssh-keygen -t ed25519 -C "your@email.com"
cat ~/.ssh/id_ed25519.pub
# Add to https://aur.archlinux.org/account/
```
