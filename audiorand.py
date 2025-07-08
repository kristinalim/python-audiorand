#!/usr/bin/python3

import gi
import os
import random
from threading import Thread
import pygame  # NEW: used instead of playsound

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3

pygame.mixer.init()

AUDIO_STORAGE_FILE = os.path.expanduser("~/.audiorand_files.txt")

def load_audio_files():
    if os.path.exists(AUDIO_STORAGE_FILE):
        with open(AUDIO_STORAGE_FILE, 'r') as f:
            return [line.strip() for line in f if os.path.isfile(line.strip())]
    return []

def save_audio_files(files):
    with open(AUDIO_STORAGE_FILE, 'w') as f:
        for path in files:
            f.write(path + '\n')

class AudioManagerWindow(Gtk.Window):
    def __init__(self, app_ref):
        super().__init__(title="Audiorand — Manage Audio Files")
        self.set_default_size(400, 300)
        self.app_ref = app_ref
        self.set_border_width(10)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        self.store = Gtk.ListStore(str)
        for path in self.app_ref.audio_files:
            self.store.append([path])

        self.tree = Gtk.TreeView(model=self.store)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Audio File Path", renderer, text=0)
        self.tree.append_column(column)
        scroller = Gtk.ScrolledWindow()
        scroller.set_vexpand(True)
        scroller.add(scroller.get_child() if scroller.get_child() else self.tree)
        vbox.pack_start(scroller, True, True, 0)

        button_box = Gtk.Box(spacing=6)
        vbox.pack_start(button_box, False, False, 0)

        add_btn = Gtk.Button(label="Add Files")
        add_btn.connect("clicked", self.on_add_files)
        button_box.pack_start(add_btn, True, True, 0)

        delete_btn = Gtk.Button(label="Delete Selected")
        delete_btn.connect("clicked", self.on_delete_selected)
        button_box.pack_start(delete_btn, True, True, 0)

        replace_btn = Gtk.Button(label="Replace All")
        replace_btn.connect("clicked", self.on_replace_all)
        button_box.pack_start(replace_btn, True, True, 0)

    def on_add_files(self, _):
        dialog = self.create_file_chooser("Add Audio Files")
        if dialog.run() == Gtk.ResponseType.OK:
            files = dialog.get_filenames()
            for f in files:
                if f not in self.app_ref.audio_files:
                    self.app_ref.audio_files.append(f)
                    self.store.append([f])
            save_audio_files(self.app_ref.audio_files)
        dialog.destroy()

    def on_delete_selected(self, _):
        selection = self.tree.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            path = model[treeiter][0]
            self.app_ref.audio_files.remove(path)
            model.remove(treeiter)
            save_audio_files(self.app_ref.audio_files)

    def on_replace_all(self, _):
        dialog = self.create_file_chooser("Select New Audio Files", multiple=True)
        if dialog.run() == Gtk.ResponseType.OK:
            new_files = dialog.get_filenames()
            self.app_ref.audio_files = new_files
            self.store.clear()
            for f in new_files:
                self.store.append([f])
            save_audio_files(new_files)
        dialog.destroy()

    def create_file_chooser(self, title, multiple=True):
        dialog = Gtk.FileChooserDialog(
            title=title, parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        dialog.set_select_multiple(multiple)

        filter_audio = Gtk.FileFilter()
        filter_audio.set_name("Audio files")
        filter_audio.add_pattern("*.mp3")
        filter_audio.add_pattern("*.wav")
        filter_audio.add_mime_type("audio/mpeg")
        dialog.add_filter(filter_audio)

        return dialog

class AudioTrayApp:
    def __init__(self):
        self.audio_files = load_audio_files()
        self.manager_window = None

        self.indicator = AppIndicator3.Indicator.new(
            "audiorand",
            os.path.abspath("icon.png") if os.path.exists("icon.png") else "media-playback-start",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())

    def build_menu(self):
        menu = Gtk.Menu()

        open_manager_item = Gtk.MenuItem(label="Manage Audio Files...")
        open_manager_item.connect("activate", self.open_manager_window)
        menu.append(open_manager_item)

        play_item = Gtk.MenuItem(label="Play Random Audio")
        play_item.connect("activate", self.on_play_random_audio)
        menu.append(play_item)

        pause_item = Gtk.MenuItem(label="Pause/Resume Audio")
        pause_item.connect("activate", self.on_pause_audio)
        menu.append(pause_item)

        stop_item = Gtk.MenuItem(label="Stop Audio")
        stop_item.connect("activate", self.on_stop_audio)
        menu.append(stop_item)

        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self.quit)
        menu.append(quit_item)

        menu.show_all()
        return menu

    def open_manager_window(self, *_):
        if self.manager_window and self.manager_window.is_visible():
            self.manager_window.present()
        else:
            self.manager_window = AudioManagerWindow(self)
            self.manager_window.show_all()

    def on_play_random_audio(self, _):
        if not self.audio_files:
            self.show_message("No audio files available.")
            return

        # Stop any existing playback
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

        audio_file = random.choice(self.audio_files)
        try:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
        except Exception as e:
            self.show_message(f"Failed to play audio:\n{e}")

    def on_pause_audio(self, _):
        if pygame.mixer.music.get_busy():
            if pygame.mixer.music.get_pos() > 0:
                if pygame.mixer.music.get_volume() > 0.0:
                    pygame.mixer.music.pause()
                else:
                    pygame.mixer.music.unpause()

    def on_stop_audio(self, _):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

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

