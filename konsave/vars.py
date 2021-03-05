## IMPORT ##
import os


## GLOBAL VARS ##
HOME = os.path.expandvars('$HOME')
CONFIG_DIR = os.path.join(HOME, '.config')
KONSAVE_DIR = os.path.join(CONFIG_DIR, 'konsave')
PROFILES_DIR = os.path.join(KONSAVE_DIR, 'profiles')

folder_names = ['gtk-2.0', 'gtk-3.0', 'gtk-4.0', 'Kvantum', 'latte']
file_names = ['dolphinrc', 'konsolerc', 'kcminputrc', 'kdeglobals', 'kglobalshortcutsrc', 'klipperrc', 'krunnerrc', 'kscreenlockerrc', 'ksmserverrc', 'kwinrc', 'kwinrulesrc', 'plasma-org.kde.plasma.desktop-appletsrc', 'plasmarc', 'plasmashellrc', 'gtkrc', 'gtkrc-2.0', 'lattedockrc', 'breezerc', 'oxygenrc', 'lightlyrc', 'ksplashrc']
export_extension = '.knsv'

if not os.path.exists(PROFILES_DIR):
    os.mkdirs(PROFILES_DIR)

list_of_profiles = os.listdir(PROFILES_DIR)
length_of_lop = len(list_of_profiles)