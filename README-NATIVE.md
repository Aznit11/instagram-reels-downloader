# 📹 Instagram Reels Downloader - Native Desktop App

A beautiful **native Linux desktop application** for downloading Instagram reels with just one click!

## ✨ Features

- 🖥️ **Native GTK Interface** - True Linux desktop application (no browser needed)
- 🎯 **One-Click Downloads** - Simply paste the URL and click download
- 🎨 **Beautiful Modern UI** - Clean design with gradient header and smooth animations
- 📊 **Real-time Progress** - See download progress with a progress bar
- 📁 **Custom Download Location** - Choose where to save your reels
- 🔒 **Private & Safe** - All downloads happen locally on your machine
- 🐧 **Cross-Distro Compatible** - Works on all Linux distributions
- ⚡ **Fast & Efficient** - Uses yt-dlp for reliable downloads

## 🚀 Quick Start

### Prerequisites

1. **Python 3.7+**
2. **GTK 3** and **PyGObject** (system packages)

### Installation

#### Step 1: Install System Dependencies

**For Arch Linux:**
```bash
sudo pacman -S gtk3 python-gobject
```

**For Debian/Ubuntu:**
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

**For Fedora:**
```bash
sudo dnf install python3-gobject gtk3
```

#### Step 2: Install Python Dependencies

```bash
# Create virtual environment (with system packages access)
python3 -m venv venv --system-site-packages

# Activate it
source venv/bin/activate

# Install yt-dlp
pip install yt-dlp
```

#### Step 3: Run the Application

**Easy way (Recommended):**
```bash
./run-gui.sh
```

**Manual way:**
```bash
source venv/bin/activate
python3 instagram_downloader_gui.py
```

## 📖 How to Use

1. Launch the application
2. Copy an Instagram reel URL (e.g., `https://www.instagram.com/reel/ABC123/`)
3. Paste it into the URL field
4. Click **"⬇️ Download Reel"**
5. Watch the progress bar
6. Click **"📂 Open Downloads Folder"** to view your reel

## 🎨 Features Overview

### Main Window
- **Header**: Beautiful gradient header with app title
- **URL Input**: Large, easy-to-use text field for pasting URLs
- **Download Button**: Prominent button to start downloads
- **Progress Bar**: Real-time download progress indicator
- **Status Messages**: Clear success/error notifications
- **Folder Management**: Easy access to change download location

### UI Elements
- ⚡ Fast Downloads
- 🎨 Best Quality
- 🔒 Private & Safe
- 📂 Open folder directly from the app
- 🔄 Change download location anytime

## 🔧 Configuration

### Change Download Folder
Click the **"Change"** button next to the folder path to select a new download location.

### Default Location
By default, reels are saved to: `~/Downloads/Instagram_Reels/`

## 🐛 Troubleshooting

### "No module named 'gi'"
Install PyGObject system package:
```bash
# Arch Linux
sudo pacman -S python-gobject

# Debian/Ubuntu
sudo apt install python3-gi
```

### "Could not find Gtk"
Install GTK3:
```bash
# Arch Linux
sudo pacman -S gtk3

# Debian/Ubuntu
sudo apt install gir1.2-gtk-3.0
```

### Virtual Environment Issues
Create venv with system packages access:
```bash
python3 -m venv venv --system-site-packages
```

### Download Fails
- Update yt-dlp: `pip install -U yt-dlp`
- Check your internet connection
- Verify the Instagram URL is correct and public

## 🆚 Web vs Native Version

This repository now includes **both versions**:

### Native Desktop App (This File)
- **File**: `instagram_downloader_gui.py`
- **Launcher**: `./run-gui.sh`
- **Pros**: Native look, no browser needed, feels like a real app
- **Requires**: GTK3 system packages

### Web-Based App
- **File**: `app.py`
- **Launcher**: `./run.sh`
- **Pros**: Easier to install, works anywhere
- **Requires**: Just Flask and yt-dlp

Choose the one you prefer!

## 📝 Technical Details

- **Language**: Python 3
- **GUI Framework**: GTK 3 (via PyGObject)
- **Downloader**: yt-dlp
- **Threading**: Background downloads don't freeze the UI
- **Platform**: Linux (all distributions)

## 🔐 Privacy

This application runs entirely on your local machine. No data is sent to external servers except for downloading the reels directly from Instagram.

## ⚠️ Disclaimer

This tool is for personal use only. Please respect Instagram's terms of service and content creators' rights. Only download content you have permission to download.

---

**Enjoy your native Linux Instagram Reels Downloader! 🎉**
