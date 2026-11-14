"""
This module contains all the variables for konsave
"""
import os
from konsave import __version__


HOME = os.path.expandvars("$HOME")
CONFIG_DIR = os.path.join(HOME, ".config")
SHARE_DIR = os.path.join(HOME, ".local/share")
BIN_DIR = os.path.join(HOME, ".local/bin")
KONSAVE_DIR = os.path.join(CONFIG_DIR, "konsave")
DEFAULT_PROFILES_DIR = os.path.join(KONSAVE_DIR, "profiles")
CONFIG_FILE = os.path.join(KONSAVE_DIR, "conf.yaml")

# The GUI stores the selected profile library here. Reading it here means the
# command-line tools use the same library as the GUI (for example a shared,
# synced folder used by a laptop and a desktop).
GUI_SETTINGS_FILE = os.path.join(KONSAVE_DIR, "gui.yaml")


def _configured_profiles_dir():
    """Returns the profile library selected in the GUI, or the default."""
    try:
        import yaml

        with open(GUI_SETTINGS_FILE, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        path = data.get("profiles_dir")
        if path:
            return os.path.abspath(os.path.expanduser(str(path)))
    except Exception:
        pass
    return DEFAULT_PROFILES_DIR


PROFILES_DIR = _configured_profiles_dir()

EXPORT_EXTENSION = ".knsv"

# Create PROFILES_DIR if it doesn't exist
if not os.path.exists(PROFILES_DIR):
    try:
        os.makedirs(PROFILES_DIR)
    except OSError:
        pass

try:
    list_of_profiles = os.listdir(PROFILES_DIR)
except OSError:
    list_of_profiles = []

length_of_lop = len(list_of_profiles)

VERSION = __version__
