## IMPORT ##
import os


## GLOBAL VARS ##
HOME = os.path.expandvars('$HOME')
CONFIG_DIR = os.path.join(HOME, '.config')
KONSAVE_DIR = os.path.join(CONFIG_DIR, 'konsave')
PROFILES_DIR = os.path.join(KONSAVE_DIR, 'profiles')
CONFIG_FILE = os.path.join(KONSAVE_DIR, "conf.yaml")

export_extension = '.knsv'

if not os.path.exists(PROFILES_DIR):
    os.mkdir(PROFILES_DIR)

list_of_profiles = os.listdir(PROFILES_DIR)
length_of_lop = len(list_of_profiles)