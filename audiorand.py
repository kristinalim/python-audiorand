#!/usr/bin/python3

import gi
import random
import os
from playsound import playsound
from threading import Thread

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

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

class AudioWidget(Gtk.Window):
    def __init__(self):
        super().__init__(title="Audio Widget")
        self.set_default_size(200, 100)
        self.set_resizable(False)
        self.set_border_width(10)

        self.audio_files = load_audio_files()

        self.button = Gtk.Button(label="Right-click me")
        self.button.connect("button-press-event", self.on_button_press)
        self.add(self.button)

        self.show_all()

    def on_button_press(self, widget, event):
        if event.button == Gdk.BUTTON_SECONDARY:  # Right-click
            menu = Gtk.Menu()

            upload_item = Gtk.MenuItem(label="Upload Audio Files")
            upload_item.connect("activate", self.on_upload_files)
            menu.append(upload_item)

            play_item = Gtk.MenuItem(label="Play Random Audio")
            play_item.connect("activate", self.on_play_random_audio)
            menu.append(play_item)

            menu.show_all()
            menu.popup(None, None, None, None, event.button, event.time)

    def on_upload_files(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select Audio Files", parent=self,
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

    def on_play_random_audio(self, widget):
        if not self.audio_files:
            self.show_message("No audio files available.")
            return
        audio_file = random.choice(self.audio_files)
        Thread(target=playsound, args=(audio_file,), daemon=True).start()

    def show_message(self, text):
        md = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=text
        )
        md.run()
        md.destroy()

def main():
    win = AudioWidget()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()

if __name__ == "__main__":
    main()

