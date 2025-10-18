# 🚀 Quick Start Guide - Native Desktop App

## Installation (One-time setup)

### Step 1: Install System Dependencies

**Arch Linux:**
```bash
sudo pacman -S gtk3 python-gobject
```

**Debian/Ubuntu:**
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

**Fedora:**
```bash
sudo dnf install python3-gobject gtk3
```

### Step 2: Setup Virtual Environment

```bash
# Create virtual environment with system packages
python3 -m venv venv --system-site-packages

# Activate it
source venv/bin/activate

# Install yt-dlp
pip install yt-dlp
```

## Running the App

### Option 1: Using the launcher script (Recommended)
```bash
./run-gui.sh
```

### Option 2: Direct Python execution
```bash
# Activate venv first
source venv/bin/activate

# Run the app
python3 instagram_downloader_gui.py
```

### Option 3: Install system-wide (after AUR submission)
```bash
yay -S instagram-reels-downloader
instagram-reels-downloader-gui
```

## First Time Use

1. After running the app, a native GTK window will open

2. You'll see:
   - Purple gradient header with 📹 icon
   - "Instagram Reels Downloader" title
   - Large URL input field
   - Download button
   - Downloads folder location

3. Paste an Instagram reel URL and click "⬇️ Download Reel"

4. Watch the progress bar fill up

5. Click "📂 Open Downloads Folder" to see your reel

## Testing with a Sample URL

Try downloading any public Instagram reel:
- Go to Instagram and find any public reel
- Copy its URL (looks like: `https://www.instagram.com/reel/XXXXX/`)
- Paste it in the app
- Click Download
- Wait for completion

## Troubleshooting

### "No module named 'gi'" error?
```bash
# Arch Linux
sudo pacman -S python-gobject

# Debian/Ubuntu
sudo apt install python3-gi
```

### GTK not found?
```bash
# Arch Linux
sudo pacman -S gtk3

# Debian/Ubuntu
sudo apt install gir1.2-gtk-3.0
```

### Virtual environment issues?
Recreate with system packages:
```bash
rm -rf venv
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install yt-dlp
```

### Download fails?
- Update yt-dlp: `pip install -U yt-dlp`
- Check your internet connection
- Verify the Instagram URL is correct and public

## Closing the App

Simply close the window or press `Ctrl+Q`.

---

**Need more help?** Check the full [README.md](README.md) file.
