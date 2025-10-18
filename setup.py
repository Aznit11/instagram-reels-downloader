#!/usr/bin/env python3
"""
Setup script for Instagram Reels Downloader
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README-NATIVE.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name='instagram-reels-downloader',
    version='1.0.0',
    description='A beautiful native GTK application for downloading Instagram reels',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/instagram-reels-downloader',
    license='MIT',
    py_modules=['instagram_downloader_gui'],
    install_requires=[
        'yt-dlp>=2024.8.6',
        'PyGObject>=3.42.0',
    ],
    entry_points={
        'console_scripts': [
            'instagram-reels-downloader=instagram_downloader_gui:main',
        ],
        'gui_scripts': [
            'instagram-reels-downloader-gui=instagram_downloader_gui:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Multimedia :: Video',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Operating System :: POSIX :: Linux',
        'Environment :: X11 Applications :: GTK',
    ],
    keywords='instagram reels downloader gtk video social-media',
    python_requires='>=3.7',
    data_files=[
        ('share/applications', ['instagram-reels-downloader.desktop']),
    ],
)
