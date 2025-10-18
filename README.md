# 📹 Instagram Reels Downloader

A beautiful **native Linux desktop application** for downloading Instagram reels with just one click!

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Platform: Linux](https://img.shields.io/badge/Platform-Linux-orange.svg)
![Language: Python](https://img.shields.io/badge/Language-Python-green.svg)

## ✨ Features

- 🖥️ **Native GTK Interface** - True Linux desktop application (no browser needed)
- 🎯 **One-Click Downloads** - Simply paste the URL and click download
- 🎨 **Beautiful Modern UI** - Clean design with gradient header and smooth animations
- 📊 **Real-time Progress** - Visual progress bar shows download status
- 📁 **Custom Download Location** - Choose where to save your reels
- 🔒 **Private & Safe** - All downloads happen locally on your machine
- 🐧 **Cross-Distro Compatible** - Works on all Linux distributions
- ⚡ **Fast & Efficient** - Uses yt-dlp for reliable downloads

## 🚀 Quick Start

### For Arch Linux Users

Install from AUR (coming soon):
```bash
yay -S instagram-reels-downloader
```

### For All Linux Users

#### Prerequisites

1. **Python 3.7+**
2. **GTK 3** and **PyGObject**

#### Installation

**Step 1: Install System Dependencies**

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

**Step 2: Install Python Dependencies**

```bash
# Create virtual environment with system packages
python3 -m venv venv --system-site-packages

# Activate it
source venv/bin/activate

# Install yt-dlp
pip install yt-dlp
```

**Step 3: Run the Application**

```bash
# Easy way
./run-gui.sh

# Or manually
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

## 🎨 Interface Preview

The app features:
- **Purple gradient header** with app branding
- **Large text input** for easy URL pasting
- **Prominent download button** with icon
- **Real-time progress bar** during downloads
- **Status messages** for success/error feedback
- **Folder management** to change download location
- **Quick access button** to open downloads folder

## 🔧 Configuration

By default, reels are saved to `~/Downloads/Instagram_Reels/`. You can change this location directly in the app by clicking the **"Change"** button.

## 📦 Dependencies

- **Python 3.7+** - Programming language
- **GTK 3** - GUI framework
- **PyGObject** - Python bindings for GTK
- **yt-dlp** - Video downloader

## 🐛 Troubleshooting

### "No module named 'gi'"
Install PyGObject:
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

## 🔐 Privacy

This application runs entirely on your local machine. No data is sent to external servers except for downloading the reels directly from Instagram.

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to:
- Report bugs by opening an issue
- Suggest new features
- Submit pull requests
- Improve documentation

## 🌟 Support

If you find this project helpful, please:
- ⭐ Star this repository
- 🐛 Report any bugs you find
- 📢 Share it with others

## 📚 Additional Resources

- **AUR Submission Guide** - See [AUR-SUBMISSION-GUIDE.md](AUR-SUBMISSION-GUIDE.md)
- **Quick Start Guide** - See [QUICKSTART.md](QUICKSTART.md)

## ⚠️ Disclaimer

This tool is for personal use only. Please respect Instagram's terms of service and content creators' rights. Only download content you have permission to download.

## 🛠️ Built With

- Python 3
- GTK 3 (PyGObject)
- yt-dlp

---

**Enjoy your native Linux Instagram Reels Downloader! 🎉**
