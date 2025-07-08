#!/usr/bin/python3

import gi
import random
import os
from playsound import playsound
from threading import Thread

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3

AUDIO_STORAGE_FILE = os.path.expanduser("~/.audio_widget_files.txt")

def load_audio_files():
    if os.path.exists(AUDIO_STORAGE_FILE):
        with open(AUDIO_STORAGE_FILE, 'r') as f:
            return [line.strip() for line in f if os.path.isfile(line.strip())]
    return []

def save_audio_files(files):
    with open(AUDIO_STORAGE_FILE, 'w') as f:
        for path in files:
            f.write(path + '\n')

class AudioTrayApp:
    def __init__(self):
        self.audio_files = load_audio_files()
        self.indicator = AppIndicator3.Indicator.new(
            "audio-widget",
            "media-playback-start",  # use an available icon or provide your own .svg/.png
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())

    def build_menu(self):
        menu = Gtk.Menu()

        upload_item = Gtk.MenuItem(label="Upload Audio Files")
        upload_item.connect("activate", self.on_upload_files)
        menu.append(upload_item)

        play_item = Gtk.MenuItem(label="Play Random Audio")
        play_item.connect("activate", self.on_play_random_audio)
        menu.append(play_item)

        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self.quit)
        menu.append(quit_item)

        menu.show_all()
        return menu

    def on_upload_files(self, _):
        dialog = Gtk.FileChooserDialog(
            title="Select Audio Files", parent=None,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        dialog.set_select_multiple(True)

        filter_audio = Gtk.FileFilter()
        filter_audio.set_name("Audio files")
        filter_audio.add_mime_type("audio/mpeg")
        filter_audio.add_pattern("*.mp3")
        filter_audio.add_pattern("*.wav")
        dialog.add_filter(filter_audio)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            selected_files = dialog.get_filenames()
            self.audio_files.extend(f for f in selected_files if f not in self.audio_files)
            save_audio_files(self.audio_files)
        dialog.destroy()

    def on_play_random_audio(self, _):
        if not self.audio_files:
            self.show_message("No audio files available.")
            return
        audio_file = random.choice(self.audio_files)
        Thread(target=playsound, args=(audio_file,), daemon=True).start()

    def show_message(self, text):
        dialog = Gtk.MessageDialog(
            transient_for=None, flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=text
        )
        dialog.run()
        dialog.destroy()

    def quit(self, _):
        Gtk.main_quit()

def main():
    AudioTrayApp()
    Gtk.main()

if __name__ == "__main__":
    main()
