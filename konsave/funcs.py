## IMPORT ##
import os, shutil, argparse, configparser
from random import shuffle
from zipfile import is_zipfile, ZipFile
from konsave.vars import *

from pkg_resources import resource_stream, resource_filename

try:
    import yaml
except ModuleNotFoundError:
    raise ModuleNotFoundError("Please install the module PyYAML using pip: \n"
                              "pip install PyYAML")


## FUNCTIONS ##
# ERROR HANDLING DECORATOR
def exception_handler(func):
    '''
    This is a decorator that will check for errors in a function.
    '''
    def inner_func(*args, **kwargs):
        try:
            f = func(*args, **kwargs)
        except Exception as e:
            print(f"Konsave: {e}\nTry 'konsave -h' for more info!")
        else:
            return f
    return inner_func


def mkdir(path):
    '''
    Creates directory if it doesn't exist
    '''
    if not os.path.exists(path):
        os.makedirs(path)
    return path


# PRINT/LOG
def log(msg, *args, **kwargs):
    '''
    Logs text
    '''
    print(f"Konsave: {msg.capitalize()}", *args, **kwargs)  


# RESTART KDE
def restart_kde():
    '''
    Restarts
    '''
    log('restarting kde...')
    os.system('plasmashell --replace > /dev/null 2>&1 & disown')


# PARSE AND SEARCH IN A CONFIG FILE
@exception_handler
def search_config(path, section, option):
    '''
    This function will parse config files and search for specific values
    '''
    config = configparser.ConfigParser(strict=False)
    config.read(path)
    return config[section][option]


# LOAD CONFIG FILE
@exception_handler
def load_config():
    """
    Load the yaml file which contains the files and folders to be saved

    The file should be formatted like this:

    ---
    entries:
        - folder name
        - file name
        - another file name
        - another folder name

    """
    default_config_path = resource_filename('konsave', 'conf.yaml')
    if not os.path.exists(CONFIG_FILE):
        shutil.copy(default_config_path, CONFIG_FILE)
        return yaml.load(resource_stream('konsave', 'conf.yaml'), Loader=yaml.FullLoader)["entries"]

    with open(CONFIG_FILE) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config["entries"]


# COPY FILE/FOLDER
@exception_handler
def copy(source, dest):
    '''
    This function was created because shutil.copytree gives error if the destination folder
    exists and the argument "dirs_exist_ok" was introduced only after python 3.8.
    This restricts people with python 3.7 or less from using Konsave.
    This function will let people with python 3.7 or less use Konsave without any issues.
    It uses recursion to copy files and folders from "source" to "dest"
    '''
    assert (type(source) == str and type(dest) == str), "Invalid path"
    assert (source != dest), "Source and destination can't be same"
    assert (os.path.exists(source)), "Source path doesn't exist"
    
    if not os.path.exists(dest):
        os.mkdir(dest)
    
    if os.path.isdir(source):
        for item in os.listdir(source): 
            source_path = os.path.join(source, item)
            dest_path = os.path.join(dest, item)

            if os.path.isdir(source_path):
                copy(source_path, dest_path)
            else:
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                shutil.copy(source_path, dest)
    else:
        shutil.copy(source, dest)


# LIST PROFILES
@exception_handler
def list_profiles(list_of_profiles, length_of_lop):
    '''
    Lists all the created profiles
    '''

    # assert
    assert (os.path.exists(PROFILES_DIR) and length_of_lop != 0), "No profile found."

    # run
    print("Konsave profiles:")
    print(f"ID\tNAME")
    for i, item in enumerate(list_of_profiles):
        print(f"{i + 1}\t{item}")


# SAVE PROFILE
@exception_handler
def save_profile(name, list_of_profiles, force=False):
    '''
    Saves necessary config files in ~/.config/konsave/profiles/<name>
    '''

    # assert
    assert (name not in list_of_profiles or force), "Profile with this name already exists"

    # run
    log("saving profile...")
    PROFILE_DIR = os.path.join(PROFILES_DIR, name)
    mkdir(PROFILE_DIR)

    entries = load_config()
    for entry in entries:
        source = os.path.join(CONFIG_DIR, entry)
        if os.path.exists(source):
            if os.path.isdir(source):
                copy(source, os.path.join(PROFILE_DIR, entry))
            else:
                shutil.copy(source, PROFILE_DIR)

    log('Profile saved successfully!')


# APPLY PROFILE
@exception_handler
def apply_profile(id, list_of_profiles, length_of_lop):
    '''
    Applies profile of the given id
    '''

    # Lowering id by 1
    id -= 1

    # assert
    assert (length_of_lop != 0), "No profile saved yet."
    assert (id in range(length_of_lop)), "Profile not found :("

    # run
    name = list_of_profiles[id]
    PROFILE_DIR = os.path.join(PROFILES_DIR, name)

    log('copying files...')

    copy(PROFILE_DIR, CONFIG_DIR)
    restart_kde()

    log("Profile applied successfully! Please log-out and log-in to see the changes completely!")


# REMOVE PROFILE
@exception_handler
def remove_profile(id, list_of_profiles, length_of_lop):
    '''
    Removes the specified profile
    '''

    # Lowering id by 1
    id -= 1

    # assert
    assert (id in range(length_of_lop)), "Profile not found."

    # run
    item = list_of_profiles[id]
    log('removing profile...')
    shutil.rmtree(os.path.join(PROFILES_DIR, item))
    log('removed profile successfully')


# EXPORT PROFILE
@exception_handler
def export(id, list_of_profiles, length_of_lop):
    '''
    It will export the specified profile as a ".knsv" file in the home directory
    '''

    # lowering id by 1
    id -= 1

    # assert
    assert (id in range(length_of_lop)), "Profile not found."

    # run
    item = list_of_profiles[id]
    PROFILE_DIR = os.path.join(PROFILES_DIR, item)
    EXPORT_PATH = os.path.join(HOME, item)

    if os.path.exists(EXPORT_PATH):
        rand_str = list('abcdefg12345')
        shuffle(rand_str)
        EXPORT_PATH = EXPORT_PATH + ''.join(rand_str)

    # compressing the files as zip
    log("Exporting profile. It might take a minute or two...")

    CONFIG_EXPORT_PATH = mkdir(os.path.join(EXPORT_PATH, "config"))
    PLASMA_EXPORT_PATH = mkdir(os.path.join(EXPORT_PATH, "plasma"))
    CURSOR_EXPORT_PATH = mkdir(os.path.join(EXPORT_PATH, "cursor"))
    ICON_EXPORT_PATH = mkdir(os.path.join(EXPORT_PATH, "icons"))

    # VARIABLES
    KDE_GLOBALS = os.path.join(PROFILE_DIR, 'kdeglobals')

    icon = search_config(KDE_GLOBALS, 'Icons', 'Theme')
    cursor = search_config(os.path.join(PROFILE_DIR, 'kcminputrc'), 'Mouse', 'cursorTheme')

    PLASMA_DIR = os.path.join(HOME, '.local/share/plasma')
    LOCAL_ICON_DIR = os.path.join(HOME, '.local/share/icons', icon)
    USR_ICON_DIR = os.path.join('/usr/share/icons', icon)
    LOCAL_CURSOR_DIR = os.path.join(HOME, '.icons', cursor)
    USR_CURSOR_DIR = os.path.join('/usr/share/icons', cursor)

    def check_path_and_copy(path1, path2, export_location, name):
        if os.path.exists(path1):
            copy(path1, os.path.join(export_location, name))
        elif os.path.exists(path2):
            copy(path2, os.path.join(export_location, name))
        else:
            log(f"Couldn't find {path1} or {path2}. Skipping...")


    log("Exporting icon theme")
    check_path_and_copy(LOCAL_ICON_DIR, USR_ICON_DIR, ICON_EXPORT_PATH, icon)

    log("Exporting cursors...")
    check_path_and_copy(LOCAL_CURSOR_DIR, USR_CURSOR_DIR, CURSOR_EXPORT_PATH, cursor)

    log("Exporting plasma files")
    copy(PLASMA_DIR, PLASMA_EXPORT_PATH)

    log("Exporting config files")
    copy(PROFILE_DIR, CONFIG_EXPORT_PATH)

    log("Creating archive")
    shutil.make_archive(EXPORT_PATH, 'zip', EXPORT_PATH)

    shutil.rmtree(EXPORT_PATH)
    shutil.move(EXPORT_PATH + '.zip', EXPORT_PATH + export_extension)

    log(f"Successfully exported to {EXPORT_PATH}{export_extension}")


# IMPORT PROFILE
@exception_handler
def import_profile(path):
    '''
    This will import an exported profile
    '''

    # assert
    assert (is_zipfile(path) and path[-5:] == export_extension), "Not a valid konsave file"
    item = os.path.basename(path)[:-5]
    assert (not os.path.exists(os.path.join(PROFILES_DIR, item))), "A profile with this name already exists"

    # run

    log("Importing profile. It might take a minute or two...")

    item = os.path.basename(path).replace(export_extension, '')

    TEMP_PATH = os.path.join(KONSAVE_DIR, 'temp', item)

    with ZipFile(path, 'r') as zip:
        zip.extractall(TEMP_PATH)

    CONFIG_IMPORT_PATH = os.path.join(TEMP_PATH, 'config')
    PLASMA_IMPORT_PATH = os.path.join(TEMP_PATH, 'plasma')
    ICON_IMPORT_PATH = os.path.join(TEMP_PATH, 'icons')
    CURSOR_IMPORT_PATH = os.path.join(TEMP_PATH, 'cursor')

    PLASMA_DIR = os.path.join(HOME, '.local/share/plasma')
    LOCAL_ICON_DIR = os.path.join(HOME, '.local/share/icons')
    LOCAL_CURSOR_DIR = os.path.join(HOME, '.icons')
    PROFILE_DIR = os.path.join(PROFILES_DIR, item)

    check_mark = u'\u2713'

    log("Importing config files")
    copy(CONFIG_IMPORT_PATH, PROFILE_DIR)

    log("Importing plasma files")
    copy(PLASMA_IMPORT_PATH, PLASMA_DIR)

    log("Importing icons")
    copy(ICON_IMPORT_PATH, LOCAL_ICON_DIR)

    log("Importing cursors")
    copy(CURSOR_IMPORT_PATH, LOCAL_CURSOR_DIR)

    shutil.rmtree(TEMP_PATH)

    log("Profile successfully imported!")


# WIPE
@exception_handler
def wipe():
    '''
    This function will wipe all profiles
    '''
    confirm = input("This will wipe all your profiles. Enter \"WIPE\" Tto continue: ")
    if confirm == 'WIPE':
        shutil.rmtree(PROFILES_DIR)
        log("Removed all profiles!")
    else:
        log("Aborting...")