#!/usr/bin/python3

import gi
import os
import json
import random
from threading import Thread
import pygame

# GTK and AppIndicator bindings
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3

# Initialize pygame mixer for audio playback
pygame.mixer.init()

# Constants and file locations
DATA_FILE = os.path.expanduser("~/.audiorand_data.json")
VALID_CATEGORY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789():;- ,./"

# Load and save data from JSON

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

# Main Tray Application
class AudioTrayApp:
    def __init__(self):
        self.data = load_data()
        self.is_paused = False
        self.indicator = AppIndicator3.Indicator.new(
            "audiorand",
            "media-playback-start",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())

    def build_menu(self):
        menu = Gtk.Menu()

        # Play Any
        self.play_any = Gtk.MenuItem(label="Play Any")
        self.play_any.connect("activate", self.on_play_any)
        menu.append(self.play_any)

        # Play by Category
        for cat in sorted(self.data["categories"]):
            item = Gtk.MenuItem(label=f"Play {cat}")
            item.connect("activate", self.on_play_category, cat)
            menu.append(item)

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

        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", Gtk.main_quit)
        menu.append(quit_item)

        menu.show_all()
        self.update_menu_state()
        return menu

    def update_menu_state(self):
        playing = pygame.mixer.music.get_busy()
        self.pause_item.set_sensitive(playing and not self.is_paused)
        self.resume_item.set_sensitive(playing and self.is_paused)
        self.stop_item.set_sensitive(playing)
        self.play_any.set_sensitive(bool(self.data["audio_files"]))

    def play_file(self, path):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
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

# Window to Manage Audio Files
class AudioManagerWindow(Gtk.Window):
    def __init__(self, app_ref):
        super().__init__(title="Audiorand — Manage Audio Files")
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

        cat_btn = Gtk.Button(label="Edit Categories")
        cat_btn.connect("clicked", self.on_edit_categories)
        btn_box.pack_start(cat_btn, True, True, 0)

        self.show_all()

    def on_add_audio(self, _):
        dialog = Gtk.FileChooserDialog(
            title="Add Audio Files", parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.set_select_multiple(True)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        filter_audio = Gtk.FileFilter()
        filter_audio.set_name("Audio")
        filter_audio.add_pattern("*.mp3")
        filter_audio.add_pattern("*.wav")
        dialog.add_filter(filter_audio)

        if dialog.run() == Gtk.ResponseType.OK:
            selected_files = dialog.get_filenames()
            dialog.destroy()
            category_dialog = Gtk.Dialog(title="Assign Categories", parent=self, flags=0)
            category_box = category_dialog.get_content_area()
            category_box.add(Gtk.Label(label="Select categories for the new audio files:"))

            category_checks = []
            for cat in self.data["categories"]:
                check = Gtk.CheckButton(label=cat)
                category_checks.append(check)
                category_box.add(check)

            category_dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OK, Gtk.ResponseType.OK)
            category_dialog.show_all()

            if category_dialog.run() == Gtk.ResponseType.OK:
                selected_categories = [c.get_label() for c in category_checks if c.get_active()]
                for f in selected_files:
                    if not any(e["path"] == f for e in self.data["audio_files"]):
                        self.data["audio_files"].append({"path": f, "categories": selected_categories})
                        self.store.append([f, ", ".join(selected_categories)])
                save_data(self.data)

            category_dialog.destroy()
        else:
            dialog.destroy()

    def on_delete_audio(self, _):
        selection = self.tree.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            path = model[treeiter][0]
            self.data["audio_files"] = [f for f in self.data["audio_files"] if f["path"] != path]
            model.remove(treeiter)
            save_data(self.data)

    def on_edit_categories(self, _):
        CategoryEditorWindow(self.app_ref)

# Window to Manage Categories
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

# Entry point

def main():
    AudioTrayApp()
    Gtk.main()

if __name__ == "__main__":
    main()