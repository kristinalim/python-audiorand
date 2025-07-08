# AudioRand - Random Audio Player Tray Widget

**AudioRand** is a lightweight Linux tray widget that lets you quickly play random audio files from specific categories. It is ideal for alert sounds, motivational clips, voice reminders, or fun soundbites.

## Features

- Tray icon with context menu
- Play a random audio file or by category
- Pause, Resume, and Stop playback
- Add and remove audio files
- Organize files into multiple categories
- Category-sensitive context menu items
- Dynamic icon updates: idle, playing, paused
- Packaged as a `.deb` installer for easy setup

## Dependencies

- Python 3
- GTK 3 bindings: python3-gi, gir1.2-gtk-3.0, gir1.2-appindicator3-0.1
- pygame (for audio playback)

Install them with:

```
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-appindicator3-0.1
pip3 install pygame
```

## Installation

### From `.deb` Package

```
sudo dpkg -i audiorand.deb
sudo apt-get install -f  # To resolve any missing dependencies
```

## Usage

After installation, run:

```
audiorand
```

This will place an icon in your system tray.

- Right-click the icon to open the menu.
- Add categories.
- Add audio files and assign them to one or more categories.
- Choose "Play Any" or "Play [Category]" to start playback.

Use the Pause, Resume, and Stop controls as needed.

## Data Storage

Audio file list and category mappings are saved to:

```
~/.audiorand_data.json
```

This file is automatically updated when you add/remove files or add/remove
categories.

## Author

**Kristina Lim** [https://www.bitcontroltech.com](https://www.bitcontroltech.com)

## License

MIT License © 2025 Kristina Lim
