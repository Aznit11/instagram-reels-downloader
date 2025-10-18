# 📦 How to Submit Your App to the AUR (Arch User Repository)

This guide will help you publish **Instagram Reels Downloader** to the AUR so anyone in the world can install it with a simple command.

## 📋 Prerequisites

1. **AUR Account** - Create one at https://aur.archlinux.org/register
2. **SSH Key** - Set up SSH key authentication with AUR
3. **GitHub Account** - To host your source code
4. **Git** - Install with `sudo pacman -S git`
5. **Base-devel** - Install with `sudo pacman -S base-devel`

## 🚀 Step-by-Step Guide

### Step 1: Create a GitHub Repository

1. Go to https://github.com/new
2. Create a new repository named `instagram-reels-downloader`
3. Make it **public** (required for AUR)
4. Don't initialize with README (we already have files)

### Step 2: Upload Your Code to GitHub

```bash
cd "/home/azeroual/Documents/Instagram reels downloader"

# Initialize git repository
git init

# Create .gitignore
cat > .gitignore << 'EOF'
venv/
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
.DS_Store
*.swp
*.swo
EOF

# Add your files
git add instagram_downloader_gui.py
git add setup.py
git add LICENSE
git add README-NATIVE.md
git add instagram-reels-downloader.desktop
git add requirements.txt

# Commit
git commit -m "Initial commit: Instagram Reels Downloader v1.0.0"

# Add remote (replace with your GitHub username)
git remote add origin git@github.com:YOUR_USERNAME/instagram-reels-downloader.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 3: Create a Release on GitHub

1. Go to your GitHub repository
2. Click **"Releases"** → **"Create a new release"**
3. Tag version: `v1.0.0`
4. Release title: `Instagram Reels Downloader v1.0.0`
5. Description: Copy content from README-NATIVE.md
6. Click **"Publish release"**

### Step 4: Update PKGBUILD with Real Information

After creating the release, update the PKGBUILD file:

```bash
# Get the SHA256 checksum of your release tarball
curl -sL "https://github.com/YOUR_USERNAME/instagram-reels-downloader/archive/v1.0.0.tar.gz" | sha256sum

# Edit PKGBUILD and replace:
# 1. 'yourusername' with your actual GitHub username
# 2. 'SKIP' in sha256sums with the actual checksum
# 3. Maintainer info with your name and email
```

### Step 5: Set Up AUR SSH Key

```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "your.email@example.com"

# Copy your public key
cat ~/.ssh/id_ed25519.pub

# Go to https://aur.archlinux.org/account/
# Under "SSH Public Key", paste your public key
# Click "Update"
```

### Step 6: Test Your PKGBUILD Locally

```bash
cd "/home/azeroual/Documents/Instagram reels downloader"

# Test building the package
makepkg -si

# If successful, it will install the package
# Test running it:
instagram-reels-downloader-gui

# Clean up test files
makepkg --clean
```

### Step 7: Submit to AUR

```bash
# Clone the AUR repository (use your package name)
git clone ssh://aur@aur.archlinux.org/instagram-reels-downloader.git aur-repo
cd aur-repo

# Copy necessary files
cp ../PKGBUILD .
cp ../.SRCINFO .

# Generate .SRCINFO (important!)
makepkg --printsrcinfo > .SRCINFO

# Add files to git
git add PKGBUILD .SRCINFO

# Commit
git commit -m "Initial upload: Instagram Reels Downloader v1.0.0"

# Push to AUR
git push origin master
```

### Step 8: Update Package Information on AUR Website

1. Go to https://aur.archlinux.org/packages/instagram-reels-downloader
2. Click **"Edit Package Details"**
3. Add detailed description
4. Add screenshots (if available)
5. Update package relations

## 📦 Users Can Now Install Your App!

Once published, anyone can install your app with:

```bash
# Using an AUR helper (yay, paru, etc.)
yay -S instagram-reels-downloader

# Or manually
git clone https://aur.archlinux.org/instagram-reels-downloader.git
cd instagram-reels-downloader
makepkg -si
```

## 🔄 Updating Your Package

When you release a new version:

```bash
# 1. Update version in setup.py
# 2. Create new GitHub release (e.g., v1.0.1)
# 3. Update PKGBUILD:
#    - Change pkgver to new version
#    - Increment pkgrel or reset to 1
#    - Update sha256sum
# 4. Generate new .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# 5. Commit and push to AUR
git add PKGBUILD .SRCINFO
git commit -m "Update to version 1.0.1"
git push
```

## 📚 Additional Distribution Options

### Option 1: PyPI (Python Package Index)
Make it installable with `pip`:
```bash
pip install twine
python setup.py sdist bdist_wheel
twine upload dist/*
```

Users install with: `pip install instagram-reels-downloader`

### Option 2: Snap Package
Universal Linux package:
```bash
snapcraft
```

Users install with: `snap install instagram-reels-downloader`

### Option 3: Flatpak
Another universal format:
```bash
flatpak-builder
```

Users install with: `flatpak install instagram-reels-downloader`

### Option 4: AppImage
Portable single-file application:
```bash
# Create AppImage bundle
```

Users just download and run: `./instagram-reels-downloader.AppImage`

## 🌍 Making It Popular

1. **Add README badges** - Build status, downloads, etc.
2. **Add screenshots** - Show the beautiful UI
3. **Create a website** - GitHub Pages is free
4. **Share on social media** - Reddit (r/linux, r/archlinux), Twitter
5. **Add to lists** - Awesome Linux Software lists
6. **Write a blog post** - Explain how you built it
7. **Create video demo** - YouTube tutorial

## ⚠️ Important Notes

- **AUR guidelines**: Read https://wiki.archlinux.org/title/AUR_submission_guidelines
- **Naming conventions**: Use lowercase and hyphens
- **License**: Make sure LICENSE file is correct
- **Dependencies**: Keep them minimal
- **Testing**: Test on clean Arch install before submitting
- **Maintenance**: Respond to comments and bug reports
- **Orphaning**: If you can't maintain it, mark as orphaned

## 📊 After Publishing

Monitor your package:
- AUR page: https://aur.archlinux.org/packages/instagram-reels-downloader
- Check comments regularly
- Fix reported issues
- Keep dependencies updated
- Watch GitHub issues

## 🎉 Success!

Once published, your app will be available to **millions of Arch Linux users worldwide**!

You can proudly add this badge to your README:
```markdown
[![AUR version](https://img.shields.io/aur/version/instagram-reels-downloader)](https://aur.archlinux.org/packages/instagram-reels-downloader)
```

---

**Questions?** Check the [AUR Wiki](https://wiki.archlinux.org/title/Arch_User_Repository) or ask in the Arch forums!
