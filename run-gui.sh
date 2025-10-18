#!/bin/bash

# Instagram Reels Downloader - Native GUI Launcher
# This script ensures dependencies are installed and launches the native GUI app

echo "================================================"
echo "  Instagram Reels Downloader - Native GUI"
echo "================================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed."
    echo "   Please install Python 3 and try again."
    exit 1
fi

echo "✅ Python 3 found"

# Check for GTK3 system dependencies
echo "🔍 Checking GTK dependencies..."

# Check if PyGObject dependencies are available
if ! pkg-config --exists gtk+-3.0; then
    echo "⚠️  Warning: GTK3 development libraries not found."
    echo "   Installing GTK3 dependencies..."
    echo ""
    echo "   For Arch Linux, run:"
    echo "   sudo pacman -S gtk3 python-gobject"
    echo ""
    echo "   For Debian/Ubuntu, run:"
    echo "   sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0"
    echo ""
    echo "   For Fedora, run:"
    echo "   sudo dnf install python3-gobject gtk3"
    echo ""
    read -p "Press Enter after installing the dependencies, or Ctrl+C to exit..."
fi

# Check if virtual environment exists, if not create one
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv --system-site-packages
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        echo "   You may need to install python3-venv package"
        echo "   Run: sudo pacman -S python-virtualenv"
        exit 1
    else
        echo "✅ Virtual environment created"
    fi
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated"

# Install/Update dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install --upgrade pip setuptools wheel --quiet
pip install yt-dlp --quiet

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    echo "   Trying again with verbose output..."
    pip install yt-dlp
    if [ $? -ne 0 ]; then
        exit 1
    fi
fi

echo "✅ Dependencies installed"
echo ""
echo "🚀 Starting Instagram Reels Downloader GUI..."
echo ""

# Run the GUI application
python instagram_downloader_gui.py
