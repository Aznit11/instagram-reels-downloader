#!/usr/bin/env python3
"""
Instagram Reels Downloader - Native Linux Desktop Application
Beautiful GTK-based GUI for downloading Instagram reels
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
import yt_dlp
import re
import threading
from pathlib import Path
import os

# Configuration
DOWNLOAD_FOLDER = Path.home() / 'Downloads' / 'Instagram_Reels'
DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


class InstagramDownloaderWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Instagram Reels Downloader")
        self.set_default_size(600, 450)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)
        
        # Variables
        self.is_downloading = False
        self.download_folder = DOWNLOAD_FOLDER
        
        # Apply custom CSS styling
        self.apply_css()
        
        # Create main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)
        
        # Header section
        header_box = self.create_header()
        main_box.pack_start(header_box, False, False, 0)
        
        # Content section
        content_box = self.create_content()
        main_box.pack_start(content_box, True, True, 0)
        
        # Footer section
        footer_box = self.create_footer()
        main_box.pack_start(footer_box, False, False, 0)
    
    def apply_css(self):
        """Apply custom CSS styling"""
        css_provider = Gtk.CssProvider()
        css = b"""
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            background-color: #667eea;
            padding: 30px;
        }
        
        .title {
            color: white;
            font-size: 24px;
            font-weight: bold;
        }
        
        .subtitle {
            color: rgba(255, 255, 255, 0.9);
            font-size: 13px;
        }
        
        .content {
            background-color: #f5f5f5;
            padding: 30px;
        }
        
        .card {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .url-entry {
            padding: 12px;
            border-radius: 8px;
            border: 2px solid #e0e0e0;
            font-size: 14px;
        }
        
        .url-entry:focus {
            border-color: #667eea;
        }
        
        .download-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            background-color: #667eea;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 14px;
            border: none;
        }
        
        .download-button:hover {
            background-color: #5568d3;
        }
        
        .download-button:disabled {
            opacity: 0.6;
        }
        
        .success-label {
            color: #10b981;
            font-weight: bold;
        }
        
        .error-label {
            color: #ef4444;
            font-weight: bold;
        }
        
        .info-label {
            color: #666;
            font-size: 12px;
        }
        
        .folder-button {
            color: #667eea;
            border: 1px solid #667eea;
            border-radius: 6px;
            padding: 6px 12px;
        }
        
        .folder-button:hover {
            background-color: #f0f0ff;
        }
        """
        css_provider.load_from_data(css)
        
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def create_header(self):
        """Create the header section"""
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        header_box.get_style_context().add_class('header')
        
        # Icon and title
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        title_box.set_halign(Gtk.Align.CENTER)
        
        icon_label = Gtk.Label(label="📹")
        icon_label.set_markup('<span size="32000">📹</span>')
        title_box.pack_start(icon_label, False, False, 0)
        
        title_label = Gtk.Label(label="Instagram Reels Downloader")
        title_label.get_style_context().add_class('title')
        title_box.pack_start(title_label, False, False, 0)
        
        header_box.pack_start(title_box, False, False, 0)
        
        # Subtitle
        subtitle_label = Gtk.Label(label="Download your favorite reels in one click")
        subtitle_label.get_style_context().add_class('subtitle')
        subtitle_label.set_halign(Gtk.Align.CENTER)
        header_box.pack_start(subtitle_label, False, False, 5)
        
        return header_box
    
    def create_content(self):
        """Create the main content section"""
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content_box.get_style_context().add_class('content')
        
        # Card container
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        card.get_style_context().add_class('card')
        
        # URL input section
        url_label = Gtk.Label(label="Instagram Reel URL:")
        url_label.set_halign(Gtk.Align.START)
        url_label.set_markup('<b>Instagram Reel URL:</b>')
        card.pack_start(url_label, False, False, 0)
        
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("Paste Instagram reel URL here...")
        self.url_entry.get_style_context().add_class('url-entry')
        self.url_entry.connect("activate", self.on_download_clicked)
        card.pack_start(self.url_entry, False, False, 0)
        
        # Download button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        button_box.set_halign(Gtk.Align.CENTER)
        
        self.download_button = Gtk.Button(label="⬇️  Download Reel")
        self.download_button.get_style_context().add_class('download-button')
        self.download_button.set_size_request(200, 45)
        self.download_button.connect("clicked", self.on_download_clicked)
        button_box.pack_start(self.download_button, False, False, 0)
        
        card.pack_start(button_box, False, False, 10)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_text("")
        self.progress_bar.set_no_show_all(True)
        card.pack_start(self.progress_bar, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label(label="")
        self.status_label.set_line_wrap(True)
        self.status_label.set_max_width_chars(50)
        card.pack_start(self.status_label, False, False, 0)
        
        # Folder info
        folder_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        folder_box.set_halign(Gtk.Align.CENTER)
        folder_box.set_margin_top(10)
        
        folder_icon = Gtk.Label(label="📁")
        folder_box.pack_start(folder_icon, False, False, 0)
        
        self.folder_label = Gtk.Label(label=f"Downloads save to: {self.download_folder}")
        self.folder_label.get_style_context().add_class('info-label')
        self.folder_label.set_line_wrap(True)
        self.folder_label.set_max_width_chars(40)
        folder_box.pack_start(self.folder_label, False, False, 0)
        
        change_folder_btn = Gtk.Button(label="Change")
        change_folder_btn.get_style_context().add_class('folder-button')
        change_folder_btn.connect("clicked", self.on_change_folder)
        folder_box.pack_start(change_folder_btn, False, False, 0)
        
        card.pack_start(folder_box, False, False, 0)
        
        # Open folder button
        open_folder_btn = Gtk.Button(label="📂  Open Downloads Folder")
        open_folder_btn.connect("clicked", self.on_open_folder)
        open_folder_btn.set_margin_top(10)
        card.pack_start(open_folder_btn, False, False, 0)
        
        content_box.pack_start(card, True, True, 0)
        
        return content_box
    
    def create_footer(self):
        """Create the footer section"""
        footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        footer_box.set_halign(Gtk.Align.CENTER)
        footer_box.set_margin_top(10)
        footer_box.set_margin_bottom(10)
        
        features = [
            ("⚡", "Fast Downloads"),
            ("🎨", "Best Quality"),
            ("🔒", "Private & Safe")
        ]
        
        for icon, text in features:
            feature_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            feature_box.set_halign(Gtk.Align.CENTER)
            
            icon_label = Gtk.Label(label=icon)
            icon_label.set_markup(f'<span size="16000">{icon}</span>')
            feature_box.pack_start(icon_label, False, False, 0)
            
            text_label = Gtk.Label(label=text)
            text_label.get_style_context().add_class('info-label')
            feature_box.pack_start(text_label, False, False, 0)
            
            footer_box.pack_start(feature_box, False, False, 0)
        
        return footer_box
    
    def on_download_clicked(self, widget):
        """Handle download button click"""
        if self.is_downloading:
            return
        
        url = self.url_entry.get_text().strip()
        
        if not url:
            self.show_error("Please enter a valid URL")
            return
        
        # Validate Instagram URL
        if not re.match(r'https?://(www\.)?(instagram\.com|instagr\.am)/(reel|reels|p)/', url):
            self.show_error("Please enter a valid Instagram reel URL")
            return
        
        # Start download
        self.start_download(url)
    
    def start_download(self, url):
        """Start the download in a separate thread"""
        self.is_downloading = True
        self.download_button.set_sensitive(False)
        self.url_entry.set_sensitive(False)
        self.progress_bar.show()
        self.progress_bar.set_fraction(0)
        self.progress_bar.set_text("Preparing download...")
        self.status_label.set_text("")
        
        thread = threading.Thread(target=self.download_reel, args=(url,))
        thread.daemon = True
        thread.start()
    
    def download_reel(self, url):
        """Download the reel using yt-dlp"""
        try:
            def progress_hook(d):
                if d['status'] == 'downloading':
                    if 'total_bytes' in d:
                        percent = (d['downloaded_bytes'] / d['total_bytes'])
                        GLib.idle_add(self.update_progress, percent, f"Downloading... {int(percent * 100)}%")
                    elif '_percent_str' in d:
                        percent_str = d['_percent_str'].strip().replace('%', '')
                        try:
                            percent = float(percent_str) / 100
                            GLib.idle_add(self.update_progress, percent, f"Downloading... {int(percent * 100)}%")
                        except:
                            pass
                elif d['status'] == 'finished':
                    GLib.idle_add(self.update_progress, 1.0, "Processing...")
            
            ydl_opts = {
                'format': 'best',
                'outtmpl': str(self.download_folder / '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                title = info.get('title', 'Instagram Reel')
                
                GLib.idle_add(self.download_complete, os.path.basename(filename), title)
        
        except Exception as e:
            GLib.idle_add(self.download_error, str(e))
    
    def update_progress(self, fraction, text):
        """Update progress bar"""
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(text)
        return False
    
    def download_complete(self, filename, title):
        """Handle successful download"""
        self.is_downloading = False
        self.download_button.set_sensitive(True)
        self.url_entry.set_sensitive(True)
        self.progress_bar.hide()
        
        self.status_label.set_markup(f'<span foreground="#10b981" weight="bold">✅ Download Complete!</span>\n{title}')
        self.url_entry.set_text("")
        
        return False
    
    def download_error(self, error_msg):
        """Handle download error"""
        self.is_downloading = False
        self.download_button.set_sensitive(True)
        self.url_entry.set_sensitive(True)
        self.progress_bar.hide()
        
        self.show_error(f"Download failed: {error_msg}")
        
        return False
    
    def show_error(self, message):
        """Show error message"""
        self.status_label.set_markup(f'<span foreground="#ef4444" weight="bold">❌ {message}</span>')
    
    def on_change_folder(self, widget):
        """Handle change folder button"""
        dialog = Gtk.FileChooserDialog(
            title="Choose Download Folder",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        dialog.set_current_folder(str(self.download_folder))
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            new_folder = Path(dialog.get_filename())
            self.download_folder = new_folder
            self.folder_label.set_text(f"Downloads save to: {self.download_folder}")
        
        dialog.destroy()
    
    def on_open_folder(self, widget):
        """Open the downloads folder in file manager"""
        os.system(f'xdg-open "{self.download_folder}"')


def main():
    """Main entry point"""
    app = InstagramDownloaderWindow()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    app.progress_bar.hide()
    Gtk.main()


if __name__ == '__main__':
    main()
