"""Graphical interface for Konsave.

The window is built around a *profile library*: one folder that holds every
profile. Point the laptop and the desktop at the same folder (a synced or
network location works) and both machines see the same profiles.

Run with ``konsave-gui`` (or ``python -m konsave.gui``).
"""

import copy
import os
import re
import shutil
import sys
import tempfile
import traceback

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont, QIcon, QPalette, QTextCursor
    from PyQt5.QtWidgets import (
        QAbstractItemView,
        QAction,
        QApplication,
        QDialog,
        QDialogButtonBox,
        QFileDialog,
        QHBoxLayout,
        QHeaderView,
        QInputDialog,
        QLabel,
        QLineEdit,
        QListWidget,
        QMainWindow,
        QMenu,
        QMessageBox,
        QPlainTextEdit,
        QPushButton,
        QSplitter,
        QStyleFactory,
        QTextEdit,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    QT_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on the user's environment
    QT_AVAILABLE = False

from konsave.consts import CONFIG_FILE, KONSAVE_DIR, PROFILES_DIR
from konsave import funcs
from konsave.funcs import (
    apply_profile,
    cache_profiles,
    copy_item,
    export,
    group_entries,
    import_profile,
    read_konsave_config,
    remove_profile,
    resolve_location,
    save_profile,
)

try:
    import yaml
except ModuleNotFoundError as error:  # pragma: no cover
    raise ModuleNotFoundError(
        "Please install the module PyYAML using pip: \n pip install PyYAML"
    ) from error


# Where the GUI remembers the selected profile library.
LIBRARY_SETTINGS = os.path.join(KONSAVE_DIR, "gui.yaml")
_DEFAULT_LIBRARY = PROFILES_DIR

# Entries which are likely to contain credentials or private keys. They are
# marked in the GUI so they are not shared by accident.
SENSITIVE_PATTERNS = re.compile(
    r"(^|/)(\.gnupg|hosts\.yml|credentials|keyrings?|secrets?|"
    r"\.git-credentials|auth\.json|id_rsa|id_ed25519|id_ecdsa|\.p12|\.pfx)(/|$)"
)

# Files inside ~/.ssh which are safe to share.
SSH_SAFE_FILES = {
    "config",
    "known_hosts",
    "known_hosts.old",
    "authorized_keys",
}


def _is_sensitive(entry):
    """Returns True when an entry is likely to contain secrets."""
    normalized = entry.replace("\\", "/")
    if normalized == ".ssh" or normalized.startswith(".ssh/"):
        if normalized == ".ssh":
            return True
        name = normalized.split("/", 1)[1]
        # The agent directory holds runtime sockets, never portable config.
        if name == "agent" or name.startswith("agent/"):
            return True
        # Public keys and the handful of safe files are fine to share;
        # anything else in ~/.ssh (private keys, agent data) is not.
        return not (name.endswith(".pub") or name in SSH_SAFE_FILES)
    return bool(SENSITIVE_PATTERNS.search(normalized)) or normalized.startswith(
        ".gnupg"
    )


def _read_raw_config(path):
    """Reads a YAML config without expanding placeholders.

    Returns an empty dict when the file is missing or unreadable.
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file) or {}
    except (OSError, yaml.YAMLError):
        return {}


def _dump_config(config):
    """Serializes a config back to YAML."""
    return yaml.safe_dump(config, default_flow_style=False, sort_keys=False)


def _load_library():
    """Returns the profile library remembered by the GUI."""
    try:
        with open(LIBRARY_SETTINGS, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
    except (OSError, yaml.YAMLError):
        data = {}
    path = data.get("profiles_dir")
    return os.path.abspath(os.path.expanduser(str(path))) if path else _DEFAULT_LIBRARY


def _save_library(path):
    """Remembers the selected profile library."""
    try:
        os.makedirs(KONSAVE_DIR, exist_ok=True)
        temporary = LIBRARY_SETTINGS + ".tmp"
        with open(temporary, "w", encoding="utf-8") as file:
            file.write(_dump_config({"profiles_dir": path}))
        os.replace(temporary, LIBRARY_SETTINGS)
    except OSError:
        pass


def set_library(path):
    """Makes ``path`` the profile library used by the core functions."""
    global PROFILES_DIR
    PROFILES_DIR = path
    funcs.PROFILES_DIR = path
    from konsave import consts

    consts.PROFILES_DIR = path


def _profiles_in_library():
    """Returns the names of the valid profiles found in the library."""
    if not os.path.isdir(PROFILES_DIR):
        return []
    try:
        entries = sorted(os.listdir(PROFILES_DIR))
    except OSError:
        return []
    names = []
    for name in entries:
        if name.startswith("."):
            continue
        path = os.path.join(PROFILES_DIR, name)
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, "conf.yaml")):
            names.append(name)
    return names


def _valid_profile_name(name):
    """Returns True when a name can be used for a profile directory."""
    return (
        bool(name)
        and name not in (".", "..")
        and not name.startswith(".")
        and "/" not in name
        and "\\" not in name
    )


def _muted_brush(widget):
    """Returns a brush suitable for unavailable items."""
    return widget.palette().brush(QPalette.Disabled, QPalette.Text)


def _selection_from_tree(tree):
    """Reads a group/entry selection back out of a QTreeWidget.

    Args:
        tree: populated QTreeWidget

    Returns:
        dict mapping group name to the selected entries.
    """
    selection = {}
    for i in range(tree.topLevelItemCount()):
        group_item = tree.topLevelItem(i)
        entries = []
        for j in range(group_item.childCount()):
            child = group_item.child(j)
            if child.checkState(0) == Qt.Checked:
                data = child.data(0, Qt.UserRole)
                if isinstance(data, tuple) and data and data[0] == "entry":
                    entries.append(data[2])
        selection[group_item.text(0)] = entries
    return selection


class ConfigurationDialog(QDialog):
    """Advanced editor for the Konsave YAML configuration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Konsave configuration")
        self.resize(820, 620)

        layout = QVBoxLayout(self)
        hint = QLabel(
            "Edit the Konsave configuration. Locations may use $HOME, "
            "$CONFIG_DIR, $SHARE_DIR, $BIN_DIR and ${ENDS_WITH=...} / "
            "${BEGINS_WITH=...}."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.editor = QTextEdit()
        self.editor.setLineWrapMode(QTextEdit.NoWrap)
        font = QFont("Monospace")
        font.setStyleHint(QFont.TypeWriter)
        self.editor.setFont(font)
        layout.addWidget(self.editor, 1)

        row = QHBoxLayout()
        reload_button = QPushButton(QIcon.fromTheme("view-refresh"), "Reload")
        reload_button.clicked.connect(self.reload)
        save_button = QPushButton(QIcon.fromTheme("document-save"), "Save")
        save_button.setDefault(True)
        save_button.clicked.connect(self.on_save)
        load_button = QPushButton(QIcon.fromTheme("document-open"), "Load from file…")
        load_button.clicked.connect(self.on_load_file)
        export_button = QPushButton(
            QIcon.fromTheme("document-save-as"), "Save to file…"
        )
        export_button.clicked.connect(self.on_export_file)
        merge_button = QPushButton("Add missing default groups…")
        merge_button.clicked.connect(self.on_merge_defaults)
        reset_button = QPushButton("Reset to defaults…")
        reset_button.clicked.connect(self.on_reset)
        row.addWidget(reload_button)
        row.addWidget(save_button)
        row.addWidget(load_button)
        row.addWidget(export_button)
        row.addStretch(1)
        row.addWidget(merge_button)
        row.addWidget(reset_button)
        layout.addLayout(row)

        box = QDialogButtonBox(QDialogButtonBox.Close)
        box.rejected.connect(self.reject)
        layout.addWidget(box)

        self.reload()

    def reload(self):
        """Loads the configuration from disk into the editor."""
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                self.editor.setPlainText(file.read())
        except OSError as error:
            QMessageBox.critical(self, "Could not read configuration", str(error))

    def on_save(self):
        """Validates and writes the edited configuration."""
        text = self.editor.toPlainText()
        try:
            parsed = yaml.safe_load(text)
        except yaml.YAMLError as error:
            QMessageBox.critical(self, "Invalid YAML", str(error))
            return
        if not isinstance(parsed, dict) or "save" not in parsed:
            QMessageBox.critical(
                self,
                "Invalid configuration",
                "The configuration must be a YAML mapping with a 'save' section.",
            )
            return
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as file:
                file.write(text)
        except OSError as error:
            QMessageBox.critical(self, "Could not save configuration", str(error))
            return
        self.accept()

    def on_load_file(self):
        """Loads a YAML configuration into the editor from another file."""
        path, _filter = QFileDialog.getOpenFileName(
            self,
            "Load configuration",
            os.path.expanduser("~"),
            "YAML files (*.yaml *.yml);;All files (*)",
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
            parsed = yaml.safe_load(content)
        except (OSError, yaml.YAMLError) as error:
            QMessageBox.critical(self, "Could not load configuration", str(error))
            return
        if not isinstance(parsed, dict) or "save" not in parsed:
            QMessageBox.critical(
                self,
                "Invalid configuration",
                "The file must be a YAML mapping with a 'save' section.",
            )
            return
        self.editor.setPlainText(content)

    def on_export_file(self):
        """Saves the configuration shown in the editor to a chosen file."""
        path, _filter = QFileDialog.getSaveFileName(
            self,
            "Save configuration to file",
            os.path.join(os.path.expanduser("~"), "konsave-conf.yaml"),
            "YAML files (*.yaml *.yml);;All files (*)",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write(self.editor.toPlainText())
        except OSError as error:
            QMessageBox.critical(self, "Could not save configuration", str(error))

    def on_merge_defaults(self):
        """Adds default groups and items that are missing from the config."""
        desktop = os.path.expandvars("$XDG_CURRENT_DESKTOP")
        filename = "conf_kde.yaml" if "KDE" in desktop else "conf_other.yaml"
        default_path = os.path.join(os.path.dirname(__file__), filename)
        with open(default_path, "r", encoding="utf-8") as file:
            defaults = yaml.safe_load(file) or {}

        current = _read_raw_config(CONFIG_FILE)
        added_groups = []
        added_items = []
        for section in ("save", "export"):
            default_section = defaults.get(section) or {}
            current_section = current.setdefault(section, {}) or {}
            current[section] = current_section
            for group_name, group in default_section.items():
                if group_name not in current_section:
                    current_section[group_name] = group
                    added_groups.append(f"{section}.{group_name}")
                    continue
                # Groups using traversal manage their entries dynamically.
                current_group = current_section[group_name]
                if (group.get("traversal") or "").lower() == "files" or (
                    current_group.get("traversal") or ""
                ).lower() == "files":
                    continue
                existing = current_group.get("entries") or []
                if current_group.get("entries") is None:
                    current_group["entries"] = existing
                location = resolve_location(group.get("location", ""))
                new_entries = []
                for entry in group.get("entries") or []:
                    if entry in existing or _is_sensitive(entry):
                        continue
                    if os.path.exists(os.path.join(location, entry)):
                        new_entries.append(entry)
                if new_entries:
                    existing.extend(new_entries)
                    added_items.append(
                        f"{section}.{group_name}: " + ", ".join(new_entries)
                    )

        if not added_groups and not added_items:
            QMessageBox.information(
                self,
                "Nothing to add",
                "All default groups and available items are already present.",
            )
            return

        details = []
        if added_groups:
            details.append("Groups:\n  " + "\n  ".join(added_groups))
        if added_items:
            details.append("New items:\n  " + "\n  ".join(added_items))
        answer = QMessageBox.question(
            self,
            "Add default groups",
            "Add these defaults from the packaged config?\n\n" + "\n".join(details),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as file:
                file.write(_dump_config(current))
        except OSError as error:
            QMessageBox.critical(self, "Could not save configuration", str(error))
            return
        self.reload()

    def on_reset(self):
        """Restores the packaged default config for the current desktop."""
        answer = QMessageBox.question(
            self,
            "Reset configuration",
            "Replace the current configuration with the packaged default?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        desktop = os.path.expandvars("$XDG_CURRENT_DESKTOP")
        filename = "conf_kde.yaml" if "KDE" in desktop else "conf_other.yaml"
        default_config = os.path.join(os.path.dirname(__file__), filename)
        try:
            with open(default_config, "r", encoding="utf-8") as file:
                content = file.read()
            with open(CONFIG_FILE, "w", encoding="utf-8") as file:
                file.write(content)
        except OSError as error:
            QMessageBox.critical(self, "Could not reset configuration", str(error))
            return
        self.reload()


class KonsaveWindow(QMainWindow):
    """Main Konsave window: a profile library and an editor for one profile."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Konsave")
        self.resize(1120, 760)

        self._config = {}
        self._raw_config = {}
        self._catalog = []
        self._raw_profile_config = {}
        self._current_profile = None
        self._dirty = False
        self._updating_tree = False
        self._updating_list = False
        self._last_op_failed = False

        set_library(_load_library())
        self._build_ui()
        self._build_menus()
        self.refresh_all()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        """Builds the library bar, profile list, editor and output pane."""
        central = QWidget()
        outer = QVBoxLayout(central)

        bar = QHBoxLayout()
        bar.addWidget(QLabel("<b>Profile library</b>"))
        self.library_edit = QLineEdit()
        self.library_edit.setReadOnly(True)
        self.library_edit.setToolTip(
            "All profiles are stored here. Use the same folder on every machine."
        )
        bar.addWidget(self.library_edit, 1)
        choose_button = QPushButton(
            QIcon.fromTheme("folder-open"), "Change location…"
        )
        choose_button.clicked.connect(self.on_choose_library)
        rescan_button = QPushButton(QIcon.fromTheme("view-refresh"), "Rescan")
        rescan_button.clicked.connect(self.on_rescan)
        bar.addWidget(choose_button)
        bar.addWidget(rescan_button)
        outer.addLayout(bar)

        splitter = QSplitter(Qt.Horizontal)

        # -- profiles ---------------------------------------------------
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Profiles"))
        self.profile_list = QListWidget()
        self.profile_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.profile_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.profile_list.customContextMenuRequested.connect(self._profile_menu)
        self.profile_list.currentItemChanged.connect(self._on_profile_changed)
        left_layout.addWidget(self.profile_list, 1)
        list_row = QHBoxLayout()
        new_button = QPushButton(QIcon.fromTheme("document-new"), "New…")
        new_button.clicked.connect(self.on_new_profile)
        import_button = QPushButton(QIcon.fromTheme("document-import"), "Import…")
        import_button.clicked.connect(self.on_import_profile)
        list_row.addWidget(new_button)
        list_row.addWidget(import_button)
        left_layout.addLayout(list_row)
        self.library_status = QLabel()
        self.library_status.setWordWrap(True)
        left_layout.addWidget(self.library_status)
        splitter.addWidget(left)

        # -- profile editor ---------------------------------------------
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel("Select a profile")
        title_font = self.title_label.font()
        if title_font.pointSize() > 0:
            title_font.setPointSize(title_font.pointSize() + 5)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        right_layout.addWidget(self.title_label)
        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.path_label.setStyleSheet("color: palette(mid);")
        right_layout.addWidget(self.path_label)

        hint = QLabel(
            "Tick the items this profile should contain, then choose "
            "“Save changes to profile”."
        )
        hint.setWordWrap(True)
        right_layout.addWidget(hint)

        action_row = QHBoxLayout()
        self.apply_button = QPushButton(
            QIcon.fromTheme("dialog-ok-apply"), "Apply"
        )
        self.apply_button.clicked.connect(self.on_apply_profile)
        self.rename_button = QPushButton(
            QIcon.fromTheme("edit-rename"), "Rename…"
        )
        self.rename_button.clicked.connect(self.on_rename_profile)
        self.duplicate_button = QPushButton(
            QIcon.fromTheme("edit-copy"), "Duplicate…"
        )
        self.duplicate_button.clicked.connect(self.on_duplicate_profile)
        self.export_button = QPushButton(
            QIcon.fromTheme("document-export"), "Export…"
        )
        self.export_button.clicked.connect(self.on_export_profile)
        self.delete_button = QPushButton(
            QIcon.fromTheme("edit-delete"), "Delete…"
        )
        self.delete_button.clicked.connect(self.on_delete_profiles)
        for button in (
            self.apply_button,
            self.rename_button,
            self.duplicate_button,
            self.export_button,
            self.delete_button,
        ):
            action_row.addWidget(button)
        action_row.addStretch(1)
        right_layout.addLayout(action_row)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter:"))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Show only matching items")
        self.filter_edit.textChanged.connect(self._apply_filter)
        filter_row.addWidget(self.filter_edit, 1)
        right_layout.addLayout(filter_row)

        self.item_tree = QTreeWidget()
        self.item_tree.setHeaderLabels(["Item", "Status"])
        self.item_tree.setAlternatingRowColors(True)
        self.item_tree.setUniformRowHeights(True)
        self.item_tree.setSelectionMode(QAbstractItemView.NoSelection)
        self.item_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.item_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.item_tree.itemChanged.connect(self._on_tree_item_changed)
        self.item_tree.setEnabled(False)
        right_layout.addWidget(self.item_tree, 1)

        select_row = QHBoxLayout()
        select_all = QPushButton("Select all")
        select_all.clicked.connect(lambda: self._set_all(True))
        select_none = QPushButton("Select none")
        select_none.clicked.connect(lambda: self._set_all(False))
        restore = QPushButton(QIcon.fromTheme("edit-undo"), "Restore saved")
        restore.clicked.connect(self.on_restore_profile)
        select_row.addWidget(select_all)
        select_row.addWidget(select_none)
        select_row.addWidget(restore)
        select_row.addStretch(1)
        self.dirty_label = QLabel()
        select_row.addWidget(self.dirty_label)
        self.save_button = QPushButton(
            QIcon.fromTheme("document-save"), "Save changes to profile"
        )
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.on_save_profile)
        select_row.addWidget(self.save_button)
        right_layout.addLayout(select_row)

        splitter.addWidget(right)
        splitter.setSizes([280, 840])
        outer.addWidget(splitter, 1)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(5000)
        self.log.setMaximumHeight(90)
        font = QFont("Monospace")
        font.setStyleHint(QFont.TypeWriter)
        self.log.setFont(font)
        outer.addWidget(QLabel("Output"))
        outer.addWidget(self.log)

        self.setCentralWidget(central)
        self._update_action_states()

    def _build_menus(self):
        """Creates the menu bar with the same actions as the buttons."""
        file_menu = self.menuBar().addMenu("&File")
        new_action = QAction(QIcon.fromTheme("document-new"), "New profile…", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.on_new_profile)
        import_action = QAction(
            QIcon.fromTheme("document-import"), "Import .knsv…", self
        )
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.on_import_profile)
        export_action = QAction(
            QIcon.fromTheme("document-export"), "Export .knsv…", self
        )
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.on_export_profile)
        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(new_action)
        file_menu.addSeparator()
        file_menu.addAction(import_action)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)

        profile_menu = self.menuBar().addMenu("&Profile")
        apply_action = QAction(QIcon.fromTheme("dialog-ok-apply"), "Apply", self)
        apply_action.setShortcut("Ctrl+Return")
        apply_action.triggered.connect(self.on_apply_profile)
        rename_action = QAction(QIcon.fromTheme("edit-rename"), "Rename…", self)
        rename_action.setShortcut("F2")
        rename_action.triggered.connect(self.on_rename_profile)
        duplicate_action = QAction(QIcon.fromTheme("edit-copy"), "Duplicate…", self)
        duplicate_action.setShortcut("Ctrl+D")
        duplicate_action.triggered.connect(self.on_duplicate_profile)
        delete_action = QAction(QIcon.fromTheme("edit-delete"), "Delete…", self)
        delete_action.setShortcut("Shift+Del")
        delete_action.triggered.connect(self.on_delete_profiles)
        rescan_action = QAction(QIcon.fromTheme("view-refresh"), "Rescan", self)
        rescan_action.setShortcut("F5")
        rescan_action.triggered.connect(self.on_rescan)
        profile_menu.addAction(apply_action)
        profile_menu.addAction(rename_action)
        profile_menu.addAction(duplicate_action)
        profile_menu.addSeparator()
        profile_menu.addAction(delete_action)
        profile_menu.addSeparator()
        profile_menu.addAction(rescan_action)

        tools_menu = self.menuBar().addMenu("&Tools")
        config_action = QAction(
            QIcon.fromTheme("configure"), "Configuration…", self
        )
        config_action.triggered.connect(self.on_open_configuration)
        tools_menu.addAction(config_action)

    # ------------------------------------------------------------------
    # Loading and refresh
    # ------------------------------------------------------------------
    def _load_live_config(self):
        """Reloads the system Konsave configuration used by the editor."""
        self._raw_config = _read_raw_config(CONFIG_FILE)
        parsed = read_konsave_config(CONFIG_FILE)
        if not parsed:
            self._config = self._raw_config or {"save": {}, "export": {}}
            self.log.appendPlainText(
                f"Could not read the Konsave configuration at {CONFIG_FILE}."
            )
        else:
            self._config = parsed

    def refresh_all(self):
        """Rescans the library and reloads the selected profile."""
        self._load_live_config()
        profiles = _profiles_in_library()

        self.library_edit.setText(PROFILES_DIR)
        self.library_edit.setCursorPosition(0)
        if os.path.isdir(PROFILES_DIR):
            self.library_status.setText(
                f"{len(profiles)} profile(s) found in this library."
            )
        else:
            self.library_status.setText(
                "Library unavailable. Choose a location that exists and is "
                "mounted on this machine."
            )

        target = self._current_profile if self._current_profile in profiles else None
        if target is None and profiles:
            target = profiles[0]

        self._updating_list = True
        self.profile_list.clear()
        self.profile_list.addItems(profiles)
        if target:
            items = self.profile_list.findItems(target, Qt.MatchExactly)
            if items:
                self.profile_list.setCurrentItem(items[0])
        self._updating_list = False

        if target:
            self._load_profile(target)
        else:
            self._current_profile = None
            self._clear_editor()

    def _clear_editor(self):
        """Empties the profile editor."""
        self._current_profile = None
        self._catalog = []
        self._raw_profile_config = {}
        self._dirty = False
        self.title_label.setText("Select a profile")
        self.path_label.setText("")
        self.item_tree.clear()
        self.item_tree.setEnabled(False)
        self.dirty_label.setText("")
        self._update_action_states()

    def _on_profile_changed(self, current, previous):
        """Loads the profile the user selected, guarding unsaved changes."""
        if self._updating_list:
            return
        if current is None:
            if not self._dirty:
                self._clear_editor()
            return
        name = current.text()
        if name == self._current_profile:
            self._update_action_states()
            return
        if self._dirty and self._current_profile:
            choice = self._confirm_unsaved(self._current_profile)
            if choice == "cancel":
                self._reselect(previous)
                return
            if choice == "save" and not self._save_edits():
                self._reselect(previous)
                return
        self._load_profile(name)

    def _reselect(self, previous):
        """Restores the list selection without triggering a profile change."""
        self._updating_list = True
        if previous is not None:
            self.profile_list.setCurrentItem(previous)
        elif self._current_profile:
            items = self.profile_list.findItems(
                self._current_profile, Qt.MatchExactly
            )
            if items:
                self.profile_list.setCurrentItem(items[0])
            else:
                self.profile_list.clearSelection()
        else:
            self.profile_list.clearSelection()
        self._updating_list = False

    def _load_profile(self, name):
        """Loads one profile into the editor."""
        profile_dir = os.path.join(PROFILES_DIR, name)
        conf_path = os.path.join(profile_dir, "conf.yaml")
        if not os.path.isfile(conf_path):
            self._clear_editor()
            return
        self._raw_profile_config = _read_raw_config(conf_path)
        parsed = read_konsave_config(conf_path)
        if not parsed:
            parsed = {"save": {}, "export": {}}
            self.log.appendPlainText(f"Could not read the profile config {conf_path}.")
        self._current_profile = name
        self._catalog = self._build_catalog(profile_dir, parsed)
        self._populate_profile_tree()
        self.title_label.setText(name)
        self.path_label.setText(profile_dir)
        self._dirty = False
        self._update_action_states()
        self.item_tree.setEnabled(True)
        self._apply_filter(self.filter_edit.text())

    def _build_catalog(self, profile_dir, parsed_profile):
        """Combines this machine's config with the profile's own config.

        The result is the list of groups/entries shown in the editor. Entries
        already stored in the profile are checked; entries that exist locally
        are offered so the profile can be extended.
        """
        live_save = self._config.get("save") or {}
        raw_live_save = self._raw_config.get("save") or {}
        profile_save = parsed_profile.get("save") or {}
        raw_profile_save = self._raw_profile_config.get("save") or {}

        order = list(live_save)
        order.extend(name for name in profile_save if name not in live_save)

        catalog = []
        for name in order:
            live_def = live_save.get(name)
            profile_def = profile_save.get(name)
            raw_def = raw_profile_save.get(name) or raw_live_save.get(name) or {}
            entries = []
            for definition in (live_def, profile_def):
                if not definition:
                    continue
                for entry in group_entries(definition):
                    if entry not in entries:
                        entries.append(entry)

            group_dir = os.path.join(profile_dir, name)
            try:
                stored = set(os.listdir(group_dir)) if os.path.isdir(group_dir) else set()
            except OSError:
                stored = set()
            for entry in sorted(stored):
                if entry not in entries:
                    entries.append(entry)

            raw_location = raw_def.get("location")
            if not raw_location:
                fallback = live_def or profile_def or {}
                raw_location = fallback.get("location", "")
            catalog.append(
                {
                    "name": name,
                    "entries": entries,
                    "profile_entries": stored,
                    "raw_location": raw_location or "",
                    "live_location": (live_def or {}).get("location"),
                    "profile_location": (profile_def or {}).get("location"),
                }
            )
        return catalog

    def _entry_available(self, group, entry):
        """Returns True when the entry's source exists on this machine."""
        for location in (group["live_location"], group["profile_location"]):
            if location and os.path.exists(os.path.join(location, entry)):
                return True
        return False

    # ------------------------------------------------------------------
    # Item tree
    # ------------------------------------------------------------------
    def _populate_profile_tree(self):
        """Fills the item tree with the current profile catalog."""
        self._updating_tree = True
        self.item_tree.clear()
        for group in self._catalog:
            parent = QTreeWidgetItem(self.item_tree, [group["name"], ""])
            parent.setExpanded(True)
            parent.setFlags(
                (parent.flags() | Qt.ItemIsUserCheckable) & ~Qt.ItemIsSelectable
            )
            parent.setData(0, Qt.UserRole, ("group", group["name"]))
            font = parent.font(0)
            font.setBold(True)
            parent.setFont(0, font)

            checked = 0
            for entry in group["entries"]:
                in_profile = entry in group["profile_entries"]
                available = self._entry_available(group, entry)
                sensitive = _is_sensitive(entry)
                label = entry
                if sensitive:
                    label += "  (sensitive)"
                if in_profile and not available:
                    status = "Saved · unavailable here"
                elif in_profile:
                    status = "Saved"
                elif available:
                    status = "Available"
                else:
                    status = "Missing"

                child = QTreeWidgetItem(parent, [label, status])
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setData(0, Qt.UserRole, ("entry", group["name"], entry))
                child.setCheckState(0, Qt.Checked if in_profile else Qt.Unchecked)
                if in_profile:
                    checked += 1
                if not available and not in_profile:
                    child.setFlags(child.flags() & ~Qt.ItemIsUserCheckable)
                    child.setCheckState(0, Qt.Unchecked)
                if not available:
                    child.setForeground(0, _muted_brush(self.item_tree))
                    child.setForeground(1, _muted_brush(self.item_tree))

                location = (
                    group["live_location"]
                    or group["profile_location"]
                    or group["raw_location"]
                )
                tooltip = os.path.join(location, entry) if location else entry
                if sensitive:
                    tooltip += "\nLikely to contain credentials or private keys."
                child.setToolTip(0, tooltip)

            if group["entries"]:
                if checked == len(group["entries"]):
                    parent.setCheckState(0, Qt.Checked)
                elif checked:
                    parent.setCheckState(0, Qt.PartiallyChecked)
                else:
                    parent.setCheckState(0, Qt.Unchecked)
            else:
                parent.setFlags(parent.flags() & ~Qt.ItemIsUserCheckable)
            parent.setText(1, f"{checked}/{len(group['entries'])} selected")
        self._updating_tree = False

    def _on_tree_item_changed(self, item, column):
        """Keeps group checkboxes in sync with their children."""
        if self._updating_tree or column != 0:
            return
        data = item.data(0, Qt.UserRole)
        if not isinstance(data, tuple):
            return
        if data[0] == "group":
            state = item.checkState(0)
            if state != Qt.PartiallyChecked:
                self._updating_tree = True
                for index in range(item.childCount()):
                    child = item.child(index)
                    if child.flags() & Qt.ItemIsUserCheckable:
                        child.setCheckState(0, state)
                self._updating_tree = False
                self._update_group_state(item)
            self._mark_dirty()
        elif data[0] == "entry":
            self._update_group_state(item.parent())
            self._mark_dirty()

    def _update_group_state(self, group_item):
        """Recomputes a group checkbox and its selected counter."""
        if group_item is None:
            return
        total = group_item.childCount()
        checked = sum(
            1
            for index in range(total)
            if group_item.child(index).checkState(0) == Qt.Checked
        )
        self._updating_tree = True
        if total == 0:
            group_item.setCheckState(0, Qt.Unchecked)
        elif checked == total:
            group_item.setCheckState(0, Qt.Checked)
        elif checked:
            group_item.setCheckState(0, Qt.PartiallyChecked)
        else:
            group_item.setCheckState(0, Qt.Unchecked)
        group_item.setText(1, f"{checked}/{total} selected")
        self._updating_tree = False

    def _set_all(self, state):
        """Checks or unchecks every selectable entry."""
        if not self._current_profile:
            return
        self._updating_tree = True
        for index in range(self.item_tree.topLevelItemCount()):
            group_item = self.item_tree.topLevelItem(index)
            for child_index in range(group_item.childCount()):
                child = group_item.child(child_index)
                if child.flags() & Qt.ItemIsUserCheckable:
                    child.setCheckState(0, Qt.Checked if state else Qt.Unchecked)
            if group_item.flags() & Qt.ItemIsUserCheckable:
                group_item.setCheckState(0, Qt.Checked if state else Qt.Unchecked)
        self._updating_tree = False
        for index in range(self.item_tree.topLevelItemCount()):
            self._update_group_state(self.item_tree.topLevelItem(index))
        self._mark_dirty()

    def _apply_filter(self, text):
        """Hides items which do not match the filter text."""
        needle = text.strip().lower()
        for index in range(self.item_tree.topLevelItemCount()):
            group_item = self.item_tree.topLevelItem(index)
            group_match = needle in group_item.text(0).lower()
            visible_children = 0
            for child_index in range(group_item.childCount()):
                child = group_item.child(child_index)
                match = (
                    not needle or group_match or needle in child.text(0).lower()
                )
                child.setHidden(not match)
                if match:
                    visible_children += 1
            group_item.setHidden(
                bool(needle) and not group_match and not visible_children
            )
            if needle:
                group_item.setExpanded(True)

    def _mark_dirty(self):
        """Marks the edited profile as changed."""
        if not self._current_profile:
            return
        self._dirty = True
        self._update_action_states()

    def _update_action_states(self):
        """Enables actions which make sense for the current state."""
        has_profile = self._current_profile is not None
        for button in (
            self.apply_button,
            self.rename_button,
            self.duplicate_button,
            self.export_button,
        ):
            button.setEnabled(has_profile)
        self.delete_button.setEnabled(has_profile)
        self.save_button.setEnabled(has_profile and self._dirty)
        self.item_tree.setEnabled(has_profile)
        self.filter_edit.setEnabled(has_profile)
        self.dirty_label.setText(
            "Unsaved changes" if has_profile and self._dirty else ""
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _selected_profiles(self):
        """Returns the names of all selected profiles."""
        return [item.text() for item in self.profile_list.selectedItems()]

    def _select_profile(self, name):
        """Selects a profile by name."""
        items = self.profile_list.findItems(name, Qt.MatchExactly)
        if items:
            self.profile_list.setCurrentItem(items[0])

    def _run(self, func, *args, **kwargs):
        """Runs a core function while redirecting its output into the log."""
        old_stdout = sys.stdout

        class _Stream:
            def __init__(self, widget):
                self.widget = widget

            def write(self, text):
                if text:
                    cursor = self.widget.textCursor()
                    cursor.movePosition(QTextCursor.End)
                    self.widget.setTextCursor(cursor)
                    self.widget.insertPlainText(text)

            def flush(self):
                pass

        self._last_op_failed = False
        funcs.LAST_ERROR = None
        sys.stdout = _Stream(self.log)
        try:
            return func(*args, **kwargs)
        except Exception as error:  # pragma: no cover - interactive safety net
            self._last_op_failed = True
            self.log.appendPlainText(f"Konsave: {error}")
            traceback.print_exc(file=sys.stderr)
            return None
        finally:
            sys.stdout = old_stdout
            if funcs.LAST_ERROR:
                self._last_op_failed = True

    def _confirm_unsaved(self, name):
        """Asks what to do with unsaved edits."""
        box = QMessageBox(self)
        box.setWindowTitle("Unsaved changes")
        box.setIcon(QMessageBox.Question)
        box.setText(f"Profile '{name}' has unsaved changes.")
        box.setInformativeText("Save them before continuing?")
        save_button = box.addButton("Save changes", QMessageBox.AcceptRole)
        box.addButton("Discard changes", QMessageBox.DestructiveRole)
        box.addButton(QMessageBox.Cancel)
        box.setDefaultButton(save_button)
        box.exec_()
        clicked = box.clickedButton()
        if clicked is save_button:
            return "save"
        if clicked is None or clicked == box.button(QMessageBox.Cancel):
            return "cancel"
        return "discard"

    # ------------------------------------------------------------------
    # Saving edits
    # ------------------------------------------------------------------
    def _save_edits(self):
        """Writes the checkbox selection back into the current profile."""
        if not self._current_profile:
            return False
        selection = _selection_from_tree(self.item_tree)
        try:
            self._write_profile(self._current_profile, selection)
        except Exception as error:
            self.log.appendPlainText(f"Could not save profile: {error}")
            QMessageBox.critical(self, "Could not save profile", str(error))
            return False
        self._load_profile(self._current_profile)
        self.log.appendPlainText(
            f"Profile '{self._current_profile}' updated from this machine."
        )
        return True

    def _write_profile(self, name, selection):
        """Rewrites a profile from the selection, preserving files it cannot
        reproduce on this machine (for example an app which is installed on
        the other computer)."""
        profile_dir = os.path.join(PROFILES_DIR, name)
        parent = os.path.dirname(profile_dir.rstrip(os.sep)) or PROFILES_DIR
        os.makedirs(parent, exist_ok=True)
        temp_dir = tempfile.mkdtemp(prefix=f".konsave-{name}-", dir=parent)
        merged_save = {}
        try:
            for group in self._catalog:
                group_name = group["name"]
                if not group["raw_location"]:
                    self.log.appendPlainText(
                        f"Skipping group '{group_name}': no location is configured."
                    )
                    continue
                chosen = [
                    entry for entry in selection.get(group_name, []) if entry
                ]
                dest_group = os.path.join(temp_dir, group_name)
                os.makedirs(dest_group, exist_ok=True)
                stored = []
                for entry in chosen:
                    candidates = []
                    for location in (
                        group["live_location"],
                        group["profile_location"],
                    ):
                        if location:
                            candidate = os.path.join(location, entry)
                            if candidate not in candidates:
                                candidates.append(candidate)
                    old = os.path.join(profile_dir, group_name, entry)
                    if old not in candidates:
                        candidates.append(old)
                    source = next(
                        (candidate for candidate in candidates if os.path.exists(candidate)),
                        None,
                    )
                    if source is None:
                        self.log.appendPlainText(
                            f"Skipping '{group_name}/{entry}': not available."
                        )
                        continue
                    destination = os.path.join(dest_group, entry)
                    copy_item(source, destination)
                    if os.path.exists(destination):
                        stored.append(entry)
                merged_save[group_name] = {
                    "location": group["raw_location"],
                    "entries": stored,
                }

            merged = copy.deepcopy(self._raw_profile_config or self._raw_config)
            if not merged:
                merged = {"save": {}}
            merged["save"] = merged_save
            with open(os.path.join(temp_dir, "conf.yaml"), "w", encoding="utf-8") as file:
                file.write(_dump_config(merged))

            self._replace_dir(profile_dir, temp_dir)
            cache_profiles()
        finally:
            if os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _replace_dir(self, profile_dir, new_dir):
        """Replaces ``profile_dir`` with ``new_dir`` safely."""
        if not os.path.exists(profile_dir):
            os.rename(new_dir, profile_dir)
            return
        parent = os.path.dirname(profile_dir.rstrip(os.sep)) or PROFILES_DIR
        backup = os.path.join(
            parent, f".{os.path.basename(profile_dir)}.backup-{os.getpid()}"
        )
        if os.path.exists(backup):
            shutil.rmtree(backup, ignore_errors=True)
        os.rename(profile_dir, backup)
        try:
            os.rename(new_dir, profile_dir)
        except OSError:
            os.rename(backup, profile_dir)
            raise
        else:
            shutil.rmtree(backup, ignore_errors=True)

    # ------------------------------------------------------------------
    # Library
    # ------------------------------------------------------------------
    def on_choose_library(self):
        """Lets the user pick the folder that holds all profiles."""
        if self._dirty and self._current_profile:
            choice = self._confirm_unsaved(self._current_profile)
            if choice == "cancel":
                return
            if choice == "save" and not self._save_edits():
                return
        start = PROFILES_DIR if os.path.isdir(PROFILES_DIR) else os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(
            self, "Choose the profile library", start
        )
        if not directory:
            return
        directory = os.path.abspath(directory)
        if directory == os.path.abspath(PROFILES_DIR):
            self.refresh_all()
            return
        if not os.access(directory, os.W_OK):
            answer = QMessageBox.question(
                self,
                "Read-only location",
                "This folder is not writable. Profiles can be opened and "
                "applied, but not saved.\n\nUse it anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return
        set_library(directory)
        _save_library(directory)
        self._current_profile = None
        self.refresh_all()
        self.log.appendPlainText(f"Profile library set to {directory}.")

    def on_rescan(self):
        """Rescans the profile library."""
        if self._dirty and self._current_profile:
            choice = self._confirm_unsaved(self._current_profile)
            if choice == "cancel":
                return
            if choice == "save" and not self._save_edits():
                return
        self.refresh_all()
        self.log.appendPlainText(f"Rescanned {PROFILES_DIR}.")

    # ------------------------------------------------------------------
    # Profile actions
    # ------------------------------------------------------------------
    def on_new_profile(self):
        """Creates an empty profile in the library and opens it for editing."""
        if self._dirty and self._current_profile:
            choice = self._confirm_unsaved(self._current_profile)
            if choice == "cancel":
                return
            if choice == "save" and not self._save_edits():
                return
        name, ok = QInputDialog.getText(
            self, "New profile", "Name for the new profile:"
        )
        if not ok:
            return
        name = name.strip()
        if not _valid_profile_name(name):
            QMessageBox.warning(
                self,
                "Invalid name",
                "Choose a non-empty name without slashes; names may not start "
                "with a dot.",
            )
            return
        profiles = _profiles_in_library()
        if name in profiles:
            QMessageBox.warning(
                self,
                "Profile exists",
                f"A profile named '{name}' already exists in the library.",
            )
            return
        try:
            os.makedirs(PROFILES_DIR, exist_ok=True)
        except OSError as error:
            QMessageBox.critical(self, "Could not create profile", str(error))
            return

        self._run(save_profile, name, profiles, force=False, selection={})
        if self._last_op_failed or name not in _profiles_in_library():
            QMessageBox.critical(
                self,
                "Could not create profile",
                "The profile could not be created. See the output pane for details.",
            )
            return
        self._current_profile = name
        self.refresh_all()
        self.log.appendPlainText(
            f"Created '{name}'. Tick the items to include, then choose "
            '"Save changes to profile".'
        )

    def on_save_profile(self):
        """Saves the current selection into the open profile."""
        self._save_edits()

    def on_restore_profile(self):
        """Reloads the profile from disk, discarding unsaved changes."""
        if not self._current_profile:
            return
        if self._dirty:
            answer = QMessageBox.question(
                self,
                "Restore profile",
                "Discard the unsaved changes and reload the profile from disk?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return
        self._load_profile(self._current_profile)
        self.log.appendPlainText(
            f"Reloaded '{self._current_profile}' from disk."
        )

    def on_apply_profile(self):
        """Applies the open profile to this machine."""
        name = self._current_profile
        if not name:
            QMessageBox.warning(self, "No profile", "Select a profile first.")
            return
        if self._dirty:
            choice = self._confirm_unsaved(name)
            if choice == "cancel":
                return
            if choice == "save" and not self._save_edits():
                return
        answer = QMessageBox.question(
            self,
            "Apply profile",
            f"Apply '{name}' to this machine?\n\n"
            "Files from the profile will overwrite the current configuration.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        profiles = _profiles_in_library()
        profile_config = os.path.join(PROFILES_DIR, name, "conf.yaml")
        self._run(
            apply_profile,
            name,
            profiles,
            len(profiles),
            config_path=profile_config if os.path.exists(profile_config) else None,
        )
        if not self._last_op_failed:
            self.log.appendPlainText(f"Profile '{name}' applied.")

    def on_rename_profile(self):
        """Renames the open profile."""
        name = self._current_profile
        if not name:
            return
        if self._dirty:
            choice = self._confirm_unsaved(name)
            if choice == "cancel":
                return
            if choice == "save" and not self._save_edits():
                return
        new_name, ok = QInputDialog.getText(
            self, "Rename profile", "New name:", text=name
        )
        if not ok:
            return
        new_name = new_name.strip()
        if not new_name or new_name == name:
            return
        if not _valid_profile_name(new_name):
            QMessageBox.warning(
                self,
                "Invalid name",
                "Choose a non-empty name without slashes; names may not start "
                "with a dot.",
            )
            return
        if new_name in _profiles_in_library():
            QMessageBox.warning(
                self,
                "Profile exists",
                f"A profile named '{new_name}' already exists.",
            )
            return
        try:
            os.rename(
                os.path.join(PROFILES_DIR, name),
                os.path.join(PROFILES_DIR, new_name),
            )
        except OSError as error:
            QMessageBox.critical(self, "Could not rename", str(error))
            return
        cache_profiles()
        self._current_profile = new_name
        self.refresh_all()
        self.log.appendPlainText(f"Renamed '{name}' to '{new_name}'.")

    def on_duplicate_profile(self):
        """Creates a copy of the open profile."""
        name = self._current_profile
        if not name:
            return
        if self._dirty:
            choice = self._confirm_unsaved(name)
            if choice == "cancel":
                return
            if choice == "save" and not self._save_edits():
                return
        new_name, ok = QInputDialog.getText(
            self, "Duplicate profile", "Name for the copy:", text=f"{name}-copy"
        )
        if not ok:
            return
        new_name = new_name.strip()
        if not new_name:
            return
        if not _valid_profile_name(new_name):
            QMessageBox.warning(
                self,
                "Invalid name",
                "Choose a non-empty name without slashes; names may not start "
                "with a dot.",
            )
            return
        if new_name in _profiles_in_library():
            QMessageBox.warning(
                self,
                "Profile exists",
                f"A profile named '{new_name}' already exists.",
            )
            return
        try:
            shutil.copytree(
                os.path.join(PROFILES_DIR, name),
                os.path.join(PROFILES_DIR, new_name),
            )
        except OSError as error:
            QMessageBox.critical(self, "Could not duplicate", str(error))
            return
        cache_profiles()
        self._current_profile = new_name
        self.refresh_all()
        self.log.appendPlainText(f"Duplicated '{name}' as '{new_name}'.")

    def on_delete_profiles(self):
        """Deletes the selected profile(s) from the library."""
        names = self._selected_profiles()
        if not names:
            return
        if len(names) == 1:
            message = f"Permanently delete profile '{names[0]}'?"
        else:
            message = (
                f"Permanently delete {len(names)} profiles?\n\n"
                + "\n".join(f"• {name}" for name in names)
            )
        answer = QMessageBox.question(
            self,
            "Delete profile(s)",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        deleted = []
        current = self._current_profile
        for name in names:
            profiles = _profiles_in_library()
            self._run(remove_profile, name, profiles, len(profiles))
            if not self._last_op_failed:
                deleted.append(name)
        if current in deleted:
            self._current_profile = None
        self.refresh_all()
        if deleted:
            self.log.appendPlainText("Deleted: " + ", ".join(deleted))

    # ------------------------------------------------------------------
    # Import / export
    # ------------------------------------------------------------------
    def on_export_profile(self):
        """Exports the open profile as a .knsv archive."""
        name = self._current_profile
        if not name:
            QMessageBox.warning(self, "No profile", "Select a profile first.")
            return
        if self._dirty:
            choice = self._confirm_unsaved(name)
            if choice == "cancel":
                return
            if choice == "save" and not self._save_edits():
                return
        path, _filter = QFileDialog.getSaveFileName(
            self,
            "Export profile",
            os.path.join(os.path.expanduser("~"), f"{name}.knsv"),
            "Konsave archives (*.knsv);;All files (*)",
        )
        if not path:
            return
        if not path.endswith(".knsv"):
            path += ".knsv"
        archive_dir = os.path.dirname(os.path.abspath(path))
        archive_name = os.path.basename(path)[: -len(".knsv")]
        profiles = _profiles_in_library()
        self._run(
            export,
            name,
            profiles,
            len(profiles),
            archive_dir,
            archive_name,
            True,
        )
        if not self._last_op_failed:
            self.log.appendPlainText(f"Exported '{name}' to {path}.")

    def on_import_profile(self):
        """Imports a .knsv archive into the library."""
        path, _filter = QFileDialog.getOpenFileName(
            self,
            "Import profile",
            os.path.expanduser("~"),
            "Konsave archives (*.knsv);;All files (*)",
        )
        if not path:
            return
        try:
            os.makedirs(PROFILES_DIR, exist_ok=True)
        except OSError as error:
            QMessageBox.critical(self, "Could not import profile", str(error))
            return
        self._run(import_profile, path)
        if self._last_op_failed:
            QMessageBox.critical(
                self,
                "Could not import profile",
                "The archive could not be imported. See the output pane for details.",
            )
            return
        imported = os.path.basename(path)
        if imported.endswith(".knsv"):
            imported = imported[: -len(".knsv")]
        self._current_profile = imported
        self.refresh_all()
        self.log.appendPlainText(f"Imported '{imported}'.")

    # ------------------------------------------------------------------
    # Menus / dialogs
    # ------------------------------------------------------------------
    def _profile_menu(self, pos):
        """Shows the context menu for the profile list."""
        item = self.profile_list.itemAt(pos)
        if item is None:
            return
        if not item.isSelected():
            self.profile_list.setCurrentItem(item)
        menu = QMenu(self)
        new_action = menu.addAction(QIcon.fromTheme("document-new"), "New profile…")
        menu.addSeparator()
        apply_action = menu.addAction(
            QIcon.fromTheme("dialog-ok-apply"), "Apply"
        )
        rename_action = menu.addAction(QIcon.fromTheme("edit-rename"), "Rename…")
        duplicate_action = menu.addAction(
            QIcon.fromTheme("edit-copy"), "Duplicate…"
        )
        export_action = menu.addAction(
            QIcon.fromTheme("document-export"), "Export…"
        )
        menu.addSeparator()
        delete_action = menu.addAction(QIcon.fromTheme("edit-delete"), "Delete…")
        chosen = menu.exec_(self.profile_list.viewport().mapToGlobal(pos))
        if chosen == new_action:
            self.on_new_profile()
        elif chosen == apply_action:
            self.on_apply_profile()
        elif chosen == rename_action:
            self.on_rename_profile()
        elif chosen == duplicate_action:
            self.on_duplicate_profile()
        elif chosen == export_action:
            self.on_export_profile()
        elif chosen == delete_action:
            self.on_delete_profiles()

    def on_open_configuration(self):
        """Opens the advanced YAML configuration editor."""
        if self._dirty and self._current_profile:
            choice = self._confirm_unsaved(self._current_profile)
            if choice == "cancel":
                return
            if choice == "save" and not self._save_edits():
                return
        dialog = ConfigurationDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_all()
            self.log.appendPlainText("Configuration saved.")

    def closeEvent(self, event):
        """Gives the user a chance to save unsaved edits."""
        if self._dirty and self._current_profile:
            choice = self._confirm_unsaved(self._current_profile)
            if choice == "cancel":
                event.ignore()
                return
            if choice == "save" and not self._save_edits():
                event.ignore()
                return
        event.accept()


def main():
    """Starts the Konsave GUI."""
    if not QT_AVAILABLE:
        raise SystemExit(
            "PyQt5 is required for the Konsave GUI.\n"
            "Install it with: python3 -m pip install PyQt5"
        )

    # Use the Plasma theme, palette and icon set when running on KDE.
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
    if "KDE" in desktop and not os.environ.get("QT_QPA_PLATFORMTHEME"):
        os.environ["QT_QPA_PLATFORMTHEME"] = "kde"

    app = QApplication(sys.argv)
    app.setApplicationName("Konsave")
    app.setApplicationDisplayName("Konsave")
    if "Breeze" in QStyleFactory.keys():
        app.setStyle("Breeze")
    window = KonsaveWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
