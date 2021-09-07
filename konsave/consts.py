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
PROFILES_DIR = os.path.join(KONSAVE_DIR, "profiles")
CONFIG_FILE = os.path.join(KONSAVE_DIR, "conf.yaml")

EXPORT_EXTENSION = ".knsv"

# Create PROFILES_DIR if it doesn't exist
if not os.path.exists(PROFILES_DIR):
    os.makedirs(PROFILES_DIR)

list_of_profiles = os.listdir(PROFILES_DIR)
length_of_lop = len(list_of_profiles)

VERSION = __version__
