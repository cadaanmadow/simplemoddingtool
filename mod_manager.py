import sys
import os
import json
import shutil
import ctypes

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QTreeWidget, QTreeWidgetItem,
    QLabel, QInputDialog, QMenu, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

CONFIG_FILE = "config.json"


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class ModManager(QWidget):
    def __init__(self):
        super().__init__()

        icon = QIcon(resource_path("mod_manager.ico"))
        self.setWindowIcon(icon)

        self.setWindowTitle("Simple Modding Tool")
        self.setMinimumSize(700, 550)

        self.games = {}
        self.load_config()

        layout = QVBoxLayout(self)

        # Top controls
        top = QHBoxLayout()

        self.add_game_btn = QPushButton("Add Game Mod Folder")
        self.add_game_btn.clicked.connect(self.add_game)

        self.status = QLabel("Ready")

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_view)

        top.addWidget(self.add_game_btn)
        top.addWidget(self.status)
        top.addStretch()
        top.addWidget(self.refresh_btn)

        layout.addLayout(top)

        # Tree view
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Games & Mod Files")
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)
        layout.addWidget(self.tree)

        # Buttons
        buttons = QHBoxLayout()

        enable_sel = QPushButton("Enable Selected")
        disable_sel = QPushButton("Disable Selected")
        enable_all = QPushButton("Enable All")
        disable_all = QPushButton("Disable All")

        enable_sel.clicked.connect(self.enable_selected)
        disable_sel.clicked.connect(self.disable_selected)
        enable_all.clicked.connect(self.enable_all)
        disable_all.clicked.connect(self.disable_all)

        buttons.addWidget(enable_sel)
        buttons.addWidget(disable_sel)
        buttons.addWidget(enable_all)
        buttons.addWidget(disable_all)

        add_files = QPushButton("Add Files")
        delete_files = QPushButton("Delete Selected")

        add_files.clicked.connect(self.add_files_to_game)
        delete_files.clicked.connect(self.delete_selected_files)

        buttons.addWidget(add_files)
        buttons.addWidget(delete_files)

        layout.addLayout(buttons)

        self.load_all_games()

    # ---------------- Config ----------------

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                self.games = json.load(f)

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.games, f, indent=4)

    # ---------------- Game management ----------------

    def refresh_view(self):
        self.load_all_games()
        self.status.setText("Refreshed")

    def add_game(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Mod Folder")
        if not folder:
            return

        game_name, ok = QInputDialog.getText(self, "Game Name", "Enter game name:")
        if not ok or not game_name.strip():
            return

        self.games[game_name] = folder
        self.save_config()
        self.load_all_games()

    def rename_game(self, old_name, item):
        new_name, ok = QInputDialog.getText(
            self, "Rename Game", "New game name:", text=old_name
        )
        if not ok or not new_name.strip():
            return

        if new_name in self.games:
            return

        self.games[new_name] = self.games.pop(old_name)
        self.save_config()

        item.setText(0, new_name)

        for i in range(item.childCount()):
            child = item.child(i)
            _, rel, enabled = child.data(0, Qt.UserRole)
            child.setData(0, Qt.UserRole, (new_name, rel, enabled))

    def delete_game(self, game_name):
        reply = QMessageBox.question(
            self,
            "Delete Game",
            f'Are you sure you want to remove "{game_name}"?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        self.games.pop(game_name, None)
        self.save_config()
        self.load_all_games()

    def open_context_menu(self, position):
        item = self.tree.itemAt(position)
        if item and item.parent() is None:
            menu = QMenu()

            rename_action = menu.addAction("Rename Game")
            delete_action = menu.addAction("Delete Game")

            action = menu.exec(self.tree.viewport().mapToGlobal(position))

            if action == rename_action:
                self.rename_game(item.text(0), item)
            elif action == delete_action:
                self.delete_game(item.text(0))

    # ---------------- Expansion state helpers ----------------

    def get_expanded_games(self):
        expanded = set()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.isExpanded():
                expanded.add(item.text(0))
        return expanded

    def restore_expanded_games(self, expanded):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.text(0) in expanded:
                item.setExpanded(True)

    def get_selected_game(self):
        item = self.tree.currentItem()
        if not item:
            return None

        if item.parent() is None:
            return item.text(0)

        return item.data(0, Qt.UserRole)[0]

    # ---------------- Load files ----------------

    def load_all_games(self):
        expanded = self.get_expanded_games()
        self.tree.clear()

        for game, mods_path in self.games.items():
            disabled_path = self.get_disabled_path(mods_path)
            os.makedirs(disabled_path, exist_ok=True)

            game_item = QTreeWidgetItem([game])
            self.tree.addTopLevelItem(game_item)

            for root, _, files in os.walk(mods_path):
                if root.startswith(disabled_path):
                    continue
                for file in files:
                    rel = os.path.relpath(os.path.join(root, file), mods_path)
                    item = QTreeWidgetItem([f"[ENABLED] {rel}"])
                    item.setCheckState(0, Qt.Unchecked)
                    item.setData(0, Qt.UserRole, (game, rel, True))
                    game_item.addChild(item)

            for root, _, files in os.walk(disabled_path):
                for file in files:
                    rel = os.path.relpath(os.path.join(root, file), disabled_path)
                    item = QTreeWidgetItem([f"[DISABLED] {rel}"])
                    item.setCheckState(0, Qt.Unchecked)
                    item.setData(0, Qt.UserRole, (game, rel, False))
                    game_item.addChild(item)

        self.restore_expanded_games(expanded)

    # ---------------- Actions ----------------

    def enable_selected(self):
        for item in self.get_checked_items():
            game, rel, enabled = item.data(0, Qt.UserRole)
            if not enabled:
                self.enable_file(game, rel)
        self.load_all_games()

    def disable_selected(self):
        for item in self.get_checked_items():
            game, rel, enabled = item.data(0, Qt.UserRole)
            if enabled:
                self.disable_file(game, rel)
        self.load_all_games()

    def enable_all(self):
        for game in self.games:
            mods_path = self.games[game]
            disabled_path = self.get_disabled_path(mods_path)
            for root, _, files in os.walk(disabled_path):
                for file in files:
                    rel = os.path.relpath(os.path.join(root, file), disabled_path)
                    self.enable_file(game, rel)
        self.load_all_games()

    def disable_all(self):
        for game in self.games:
            mods_path = self.games[game]
            disabled_path = self.get_disabled_path(mods_path)
            for root, _, files in os.walk(mods_path):
                if root.startswith(disabled_path):
                    continue
                for file in files:
                    rel = os.path.relpath(os.path.join(root, file), mods_path)
                    self.disable_file(game, rel)
        self.load_all_games()

    def get_checked_items(self):
        checked = []
        for i in range(self.tree.topLevelItemCount()):
            game_item = self.tree.topLevelItem(i)
            for j in range(game_item.childCount()):
                child = game_item.child(j)
                if child.checkState(0) == Qt.Checked:
                    checked.append(child)
        return checked

    # ---------------- File movement ----------------

    def enable_file(self, game, rel):
        mods_path = self.games[game]
        disabled_path = self.get_disabled_path(mods_path)

        src = os.path.join(disabled_path, rel)
        dst = os.path.join(mods_path, rel)

        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)

    def disable_file(self, game, rel):
        mods_path = self.games[game]
        disabled_path = self.get_disabled_path(mods_path)

        src = os.path.join(mods_path, rel)
        dst = os.path.join(disabled_path, rel)

        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)

    def get_disabled_path(self, mods_path):
        parent = os.path.dirname(mods_path)
        return os.path.join(parent, "Mods_DISABLED")

    def add_files_to_game(self):
        game = self.get_selected_game()
        if not game:
            QMessageBox.warning(self, "No Game Selected", "Please select a game first.")
            return

        mods_path = self.games[game]

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Mod Files",
            "",
            "All Files (*)"
        )

        if not files:
            return

        for file in files:
            dst = os.path.join(mods_path, os.path.basename(file))
            shutil.copy2(file, dst)

        self.load_all_games()
        self.status.setText(f"Added {len(files)} file(s)")

    def delete_selected_files(self):
        items = self.get_checked_items()

        if not items:
            QMessageBox.warning(self, "No Files Selected", "Select files to delete.")
            return

        reply = QMessageBox.question(
            self,
            "Delete Files",
            f"Delete {len(items)} selected file(s)? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        for item in items:
            game, rel, enabled = item.data(0, Qt.UserRole)
            mods_path = self.games[game]
            disabled_path = self.get_disabled_path(mods_path)

            base = mods_path if enabled else disabled_path
            path = os.path.join(base, rel)

            if os.path.exists(path):
                os.remove(path)

        self.load_all_games()
        self.status.setText("Files deleted")


# ---------------- Run ----------------

if __name__ == "__main__":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "SimpleModdingTool"
    )

    app = QApplication(sys.argv)

    app.setApplicationName("Simple Modding Tool")
    app.setOrganizationName("Simple Modding Tool")

    icon = QIcon(resource_path("mod_manager.ico"))
    app.setWindowIcon(icon)

    window = ModManager()
    window.show()

    sys.exit(app.exec())
