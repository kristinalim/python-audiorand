#!/usr/bin/env python3

import gi
import os
import json
import random
from threading import Thread
import pygame

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3, GLib

pygame.mixer.init()

DATA_FILE = os.path.expanduser("~/.audiorand_data.json")
ICON_IDLE = "audiorand-idle"
ICON_PLAYING = "audiorand-playing"
ICON_PAUSED = "audiorand-paused"
VALID_CATEGORY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789():;- ,./"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"audio_files": [], "categories": []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def validate_category(name):
    return all(c in VALID_CATEGORY_CHARS for c in name)

class AudioTrayApp:
    def __init__(self):
        self.data = load_data()
        self.is_paused = False
        self.current_audio = None
        self.indicator = AppIndicator3.Indicator.new(
            "audiorand",
            ICON_IDLE,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())
        # Start polling for playback end
        GLib.timeout_add(500, self.poll_playback)

    def set_icon(self, icon_name):
        self.indicator.set_icon(icon_name)

    def build_menu(self):
        menu = Gtk.Menu()

        self.play_any = Gtk.MenuItem(label="Play Any")
        self.play_any.connect("activate", self.on_play_any)
        menu.append(self.play_any)

        self.category_items = []
        for cat in sorted(self.data["categories"]):
            item = Gtk.MenuItem(label=f"Play {cat}")
            item.connect("activate", self.on_play_category, cat)
            menu.append(item)
            self.category_items.append((item, cat))

        menu.append(Gtk.SeparatorMenuItem())

        self.pause_item = Gtk.MenuItem(label="Pause Audio")
        self.pause_item.connect("activate", self.on_pause_audio)
        menu.append(self.pause_item)

        self.resume_item = Gtk.MenuItem(label="Resume Audio")
        self.resume_item.connect("activate", self.on_resume_audio)
        menu.append(self.resume_item)

        self.stop_item = Gtk.MenuItem(label="Stop Audio")
        self.stop_item.connect("activate", self.on_stop_audio)
        menu.append(self.stop_item)

        menu.append(Gtk.SeparatorMenuItem())

        manage = Gtk.MenuItem(label="Manage Audio Files...")
        manage.connect("activate", self.show_manager)
        menu.append(manage)

        manage_categories = Gtk.MenuItem(label="Manage Categories...")
        manage_categories.connect("activate", self.show_categories)
        menu.append(manage_categories)

        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", Gtk.main_quit)
        menu.append(quit_item)

        menu.show_all()
        self.update_menu_state()
        return menu

    def update_menu_state(self):
        playing = pygame.mixer.music.get_busy()
        self.pause_item.set_sensitive(playing and not self.is_paused)
        self.resume_item.set_sensitive(self.is_paused)
        self.stop_item.set_sensitive(playing)
        self.play_any.set_sensitive(bool(self.data["audio_files"]))
        for item, cat in self.category_items:
            item.set_sensitive(any(cat in f["categories"] for f in self.data["audio_files"]))
        if self.is_paused:
            self.set_icon(ICON_PAUSED)
        elif playing:
            self.set_icon(ICON_PLAYING)
        else:
            self.set_icon(ICON_IDLE)

    def play_file(self, path):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            self.current_audio = path
            self.is_paused = False
        except Exception as e:
            self.show_message(f"Failed to play {path}:\n{e}")
        self.update_menu_state()

    def on_play_any(self, _):
        if not self.data["audio_files"]:
            self.show_message("No audio files available.")
            return
        file = random.choice(self.data["audio_files"])
        self.play_file(file["path"])

    def on_play_category(self, _, category):
        files = [f for f in self.data["audio_files"] if category in f["categories"]]
        if not files:
            self.show_message(f"No files in category '{category}'")
            return
        file = random.choice(files)
        self.play_file(file["path"])

    def on_pause_audio(self, _):
        pygame.mixer.music.pause()
        self.is_paused = True
        self.update_menu_state()

    def on_resume_audio(self, _):
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.update_menu_state()

    def on_stop_audio(self, _):
        pygame.mixer.music.stop()
        self.is_paused = False
        self.update_menu_state()

    def show_message(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=None, flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()

    def show_manager(self, _):
        AudioManagerWindow(self)

    def show_categories(self, _):
        CategoryEditorWindow(self)

    def poll_playback(self):
        # Called periodically to check if playback has ended
        playing = pygame.mixer.music.get_busy()
        if not playing and not self.is_paused:
            self.set_icon(ICON_IDLE)
        return True  # Continue calling

class AudioManagerWindow(Gtk.Window):
    def __init__(self, app_ref):
        super().__init__(title="AudioRand — Manage Audio Files")
        self.set_default_size(600, 400)
        self.app_ref = app_ref
        self.data = app_ref.data

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        self.store = Gtk.ListStore(str, str)
        for f in self.data["audio_files"]:
            self.store.append([f["path"], ", ".join(f["categories"])])

        self.tree = Gtk.TreeView(model=self.store)
        for i, col_title in enumerate(["Audio File", "Categories"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(col_title, renderer, text=i)
            self.tree.append_column(column)

        scroller = Gtk.ScrolledWindow()
        scroller.set_vexpand(True)
        scroller.add(self.tree)
        vbox.pack_start(scroller, True, True, 0)

        btn_box = Gtk.Box(spacing=6)
        vbox.pack_start(btn_box, False, False, 0)

        add_btn = Gtk.Button(label="Add Audio")
        add_btn.connect("clicked", self.on_add_audio)
        btn_box.pack_start(add_btn, True, True, 0)

        del_btn = Gtk.Button(label="Delete Selected")
        del_btn.connect("clicked", self.on_delete_audio)
        btn_box.pack_start(del_btn, True, True, 0)

        self.show_all()

    def on_add_audio(self, _):
        dialog = Gtk.Dialog(title="Add Audio File", parent=self)
        content_area = dialog.get_content_area()

        file_chooser = Gtk.FileChooserButton(title="Select Audio File")
        filter_audio = Gtk.FileFilter()
        filter_audio.set_name("Audio Files")
        filter_audio.add_pattern("*.mp3")
        filter_audio.add_pattern("*.wav")
        file_chooser.add_filter(filter_audio)
        content_area.pack_start(Gtk.Label(label="Audio File:"), False, False, 0)
        content_area.pack_start(file_chooser, False, False, 0)

        content_area.pack_start(Gtk.Label(label="Categories:"), False, False, 5)
        self.checks = []
        for cat in self.data["categories"]:
            check = Gtk.CheckButton(label=cat)
            self.checks.append(check)
            content_area.pack_start(check, False, False, 0)

        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OK, Gtk.ResponseType.OK)
        dialog.show_all()

        if dialog.run() == Gtk.ResponseType.OK:
            selected_file = file_chooser.get_filename()
            if not selected_file:
                self.app_ref.show_message("You must select an audio file.")
            elif not any(e["path"] == selected_file for e in self.data["audio_files"]):
                selected_categories = [c.get_label() for c in self.checks if c.get_active()]
                self.data["audio_files"].append({"path": selected_file, "categories": selected_categories})
                self.store.append([selected_file, ", ".join(selected_categories)])
                save_data(self.data)
                self.app_ref.update_menu_state()

        dialog.destroy()

    def on_delete_audio(self, _):
        selection = self.tree.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            path = model[treeiter][0]
            self.data["audio_files"] = [f for f in self.data["audio_files"] if f["path"] != path]
            model.remove(treeiter)
            save_data(self.data)
            self.app_ref.update_menu_state()

class CategoryEditorWindow(Gtk.Window):
    def __init__(self, app_ref):
        super().__init__(title="Edit Categories")
        self.set_default_size(400, 300)
        self.app_ref = app_ref
        self.data = app_ref.data

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        self.store = Gtk.ListStore(str)
        for c in self.data["categories"]:
            self.store.append([c])

        self.tree = Gtk.TreeView(model=self.store)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Category", renderer, text=0)
        self.tree.append_column(column)

        scroller = Gtk.ScrolledWindow()
        scroller.set_vexpand(True)
        scroller.add(self.tree)
        vbox.pack_start(scroller, True, True, 0)

        btn_box = Gtk.Box(spacing=6)
        vbox.pack_start(btn_box, False, False, 0)

        add_btn = Gtk.Button(label="Add")
        add_btn.connect("clicked", self.on_add)
        btn_box.pack_start(add_btn, True, True, 0)

        del_btn = Gtk.Button(label="Delete")
        del_btn.connect("clicked", self.on_delete)
        btn_box.pack_start(del_btn, True, True, 0)

        self.show_all()

    def on_add(self, _):
        dialog = Gtk.Dialog(title="New Category", parent=self, flags=0)
        box = dialog.get_content_area()
        entry = Gtk.Entry()
        box.add(Gtk.Label(label="Category name:"))
        box.add(entry)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OK, Gtk.ResponseType.OK)
        dialog.show_all()
        if dialog.run() == Gtk.ResponseType.OK:
            name = entry.get_text().strip()
            if validate_category(name) and name not in self.data["categories"]:
                self.data["categories"].append(name)
                self.store.append([name])
                save_data(self.data)
                self.app_ref.update_menu_state()
        dialog.destroy()

    def on_delete(self, _):
        selection = self.tree.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            cat = model[treeiter][0]
            self.data["categories"].remove(cat)
            for f in self.data["audio_files"]:
                if cat in f["categories"]:
                    f["categories"].remove(cat)
            model.remove(treeiter)
            save_data(self.data)
            self.app_ref.update_menu_state()

def main():
    AudioTrayApp()
    Gtk.main()

if __name__ == "__main__":
    main()
