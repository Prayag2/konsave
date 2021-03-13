"""
This module contains all the functions for konsave.
"""

import os
import shutil
import sys
import configparser
from random import shuffle
from zipfile import is_zipfile, ZipFile
from pkg_resources import resource_stream, resource_filename
from konsave.vars import (
    HOME,
    CONFIG_FILE,
    PROFILES_DIR,
    CONFIG_DIR,
    EXPORT_EXTENSION,
    KONSAVE_DIR,
)

try:
    import yaml
except ModuleNotFoundError as error:
    raise ModuleNotFoundError(
        "Please install the module PyYAML using pip: \n" "pip install PyYAML"
    ) from error


def exception_handler(func):
    """Handles errors and prints nicely.

    Args:
        func: any function

    Returns:
        Returns function
    """

    def inner_func(*args, **kwargs):
        try:
            function = func(*args, **kwargs)
        except Exception as error:
            print(f"Konsave: {error}\nTry 'konsave -h' for more info!")
            sys.exit(0)
        else:
            return function

    return inner_func


def mkdir(path):
    """Creates directory if it doesn't exist.

    Args:
        path: path to the new directory

    Returns:
        path: the same path
    """
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def log(msg, *args, **kwargs):
    """Logs text.

    Args:
        msg: the text to be printed
        *args: any arguments for the function print()
        **kwargs: any keyword arguments for the function print()
    """
    print(f"Konsave: {msg.capitalize()}", *args, **kwargs)


def restart_kde():
    """Replaces plasmashell."""
    log("restarting kde...")
    os.system("plasmashell --replace > /dev/null 2>&1 & disown")


@exception_handler
def search_config(path, section, option):
    """This function will parse config files and search for specific values.

    Args:
        path: path to a config file
        section: name of the section to search in
        option: name of the option to search for

    Returns:
        str: the found value
    """
    config = configparser.ConfigParser(strict=False)
    config.read(path)
    return config[section][option]


@exception_handler
def load_config():
    """Loads config file.

    Returns:
        list: the names of files and folders in conf.yaml
    """
    default_config_path = resource_filename("konsave", "conf.yaml")
    if not os.path.exists(CONFIG_FILE):
        shutil.copy(default_config_path, CONFIG_FILE)
        return yaml.load(
            resource_stream("konsave", "conf.yaml"), Loader=yaml.FullLoader
        )["entries"]

    with open(CONFIG_FILE) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config["entries"]


@exception_handler
def copy(source, dest):
    """
    This function was created because shutil.copytree gives error if the destination folder
    exists and the argument "dirs_exist_ok" was introduced only after python 3.8.
    This restricts people with python 3.7 or less from using Konsave.
    This function will let people with python 3.7 or less use Konsave without any issues.
    It uses recursion to copy files and folders from "source" to "dest"

    Args:
        source: the source destination
        dest: the destination to copy the file/folder to
    """
    assert type(source) == str and type(dest) == str, "Invalid path"
    assert source != dest, "Source and destination can't be same"
    assert os.path.exists(source), "Source path doesn't exist"

    if not os.path.exists(dest):
        os.mkdir(dest)

    for item in os.listdir(source):
        source_path = os.path.join(source, item)
        dest_path = os.path.join(dest, item)

        if os.path.isdir(source_path):
            copy(source_path, dest_path)
        else:
            if os.path.exists(dest_path):
                os.remove(dest_path)
            if os.path.exists(source_path):
                shutil.copy(source_path, dest)


@exception_handler
def list_profiles(profile_list, profile_count):
    """Lists all the created profiles.

    Args:
        profile_list: the list of all created profiles
        profile_count: number of profiles created
    """

    # assert
    assert os.path.exists(PROFILES_DIR) and profile_count != 0, "No profile found."

    # run
    print("Konsave profiles:")
    print("ID\tNAME")
    for i, item in enumerate(profile_list):
        print(f"{i + 1}\t{item}")


@exception_handler
def save_profile(name, profile_list, force=False):
    """Saves necessary config files in ~/.config/konsave/profiles/<name>.

    Args:
        name: name of the profile
        profile_list: the list of all created profiles
        force: force overwrite already created profile, optional
    """

    # assert
    assert name not in profile_list or force, "Profile with this name already exists"

    # run
    log("saving profile...")
    profile_dir = os.path.join(PROFILES_DIR, name)
    mkdir(profile_dir)

    entries = load_config()
    for entry in entries:
        source = os.path.join(CONFIG_DIR, entry)
        if os.path.exists(source):
            if os.path.isdir(source):
                copy(source, os.path.join(profile_dir, entry))
            else:
                shutil.copy(source, profile_dir)

    log("Profile saved successfully!")


@exception_handler
def apply_profile(profile_id, profile_list, profile_count):
    """Applies profile of the given id.

    Args:
        profile_id: id of the profile to be applied
        profile_list: the list of all created profiles
        profile_count: number of profiles created
    """

    # Lowering id by 1
    profile_id -= 1

    # assert
    assert profile_count != 0, "No profile saved yet."
    assert profile_id in range(profile_count), "Profile not found :("

    # run
    name = profile_list[profile_id]
    profile_dir = os.path.join(PROFILES_DIR, name)

    log("copying files...")

    copy(profile_dir, CONFIG_DIR)
    restart_kde()

    log(
        "Profile applied successfully! Please log-out and log-in to see the changes completely!"
    )


@exception_handler
def remove_profile(profile_id, profile_list, profile_count):
    """Removes the specified profile.

    Args:
        profile_id: id of the profile to be removed
        profile_list: the list of all created profiles
        profile_count: number of profiles created
    """

    # Lowering profile_id by 1
    profile_id -= 1

    # assert
    assert profile_id in range(profile_count), "Profile not found."

    # run
    item = profile_list[profile_id]
    log("removing profile...")
    shutil.rmtree(os.path.join(PROFILES_DIR, item))
    log("removed profile successfully")


@exception_handler
def export(profile_id, profile_list, profile_count):
    """It will export the specified profile as a ".knsv" file in the home directory.

    Args:
        profile_id: id of the profile to be exported
        profile_list: the list of all created profiles
        profile_count: number of profiles created
    """

    # lowering profile_id by 1
    profile_id -= 1

    # assert
    assert profile_id in range(profile_count), "Profile not found."

    # run
    item = profile_list[profile_id]
    profile_dir = os.path.join(PROFILES_DIR, item)
    export_path = os.path.join(HOME, item)

    if os.path.exists(export_path):
        rand_str = list("abcdefg12345")
        shuffle(rand_str)
        export_path = export_path + "".join(rand_str)

    # compressing the files as zip
    log("Exporting profile. It might take a minute or two...")

    # VARIABLES
    config_export_path = mkdir(os.path.join(export_path, "config"))
    plasma_export_path = mkdir(os.path.join(export_path, "plasma"))
    cursor_export_path = mkdir(os.path.join(export_path, "cursor"))
    icon_export_path = mkdir(os.path.join(export_path, "icons"))

    kde_globals = os.path.join(profile_dir, "kdeglobals")

    icon = search_config(kde_globals, "Icons", "Theme")
    cursor = search_config(
        os.path.join(profile_dir, "kcminputrc"), "Mouse", "cursorTheme"
    )

    def check_path_and_copy(path1, path2, export_location, name):
        if os.path.exists(path1):
            copy(path1, os.path.join(export_location, name))
        elif os.path.exists(path2):
            copy(path2, os.path.join(export_location, name))
        else:
            log(f"Couldn't find {path1} or {path2}. Skipping...")

    if icon is not None:
        local_icon_dir = os.path.join(HOME, ".local/share/icons", icon)
        usr_icon_dir = os.path.join("/usr/share/icons", icon)
        log("Exporting icon theme")
        check_path_and_copy(local_icon_dir, usr_icon_dir, icon_export_path, icon)

    if cursor is not None:
        local_cursor_dir = os.path.join(HOME, ".icons", cursor)
        usr_cursor_dir = os.path.join("/usr/share/icons", cursor)
        log("Exporting cursors...")
        check_path_and_copy(
            local_cursor_dir, usr_cursor_dir, cursor_export_path, cursor
        )

    plasma_dir = os.path.join(HOME, ".local/share/plasma")

    log("Exporting plasma files")
    copy(plasma_dir, plasma_export_path)

    log("Exporting config files")
    copy(profile_dir, config_export_path)

    log("Creating archive")
    shutil.make_archive(export_path, "zip", export_path)

    shutil.rmtree(export_path)
    shutil.move(export_path + ".zip", export_path + EXPORT_EXTENSION)

    log(f"Successfully exported to {export_path}{EXPORT_EXTENSION}")


@exception_handler
def import_profile(path):
    """This will import an exported profile.

    Args:
        path: path of the `.knsv` file
    """

    # assert
    assert (
        is_zipfile(path) and path[-5:] == EXPORT_EXTENSION
    ), "Not a valid konsave file"
    item = os.path.basename(path)[:-5]
    assert not os.path.exists(
        os.path.join(PROFILES_DIR, item)
    ), "A profile with this name already exists"

    # run
    log("Importing profile. It might take a minute or two...")

    item = os.path.basename(path).replace(EXPORT_EXTENSION, "")

    temp_path = os.path.join(KONSAVE_DIR, "temp", item)

    with ZipFile(path, "r") as zip_file:
        zip_file.extractall(temp_path)

    config_import_path = os.path.join(temp_path, "config")
    plasma_import_path = os.path.join(temp_path, "plasma")
    icon_import_path = os.path.join(temp_path, "icons")
    cursor_import_path = os.path.join(temp_path, "cursor")

    plasma_dir = os.path.join(HOME, ".local/share/plasma")
    local_icon_dir = os.path.join(HOME, ".local/share/icons")
    local_cursor_dir = os.path.join(HOME, ".icons")
    profile_dir = os.path.join(PROFILES_DIR, item)

    log("Importing config files")
    copy(config_import_path, profile_dir)

    log("Importing plasma files")
    copy(plasma_import_path, plasma_dir)

    log("Importing icons")
    copy(icon_import_path, local_icon_dir)

    log("Importing cursors")
    copy(cursor_import_path, local_cursor_dir)

    shutil.rmtree(temp_path)

    log("Profile successfully imported!")


@exception_handler
def wipe():
    """Wipes all profiles."""
    confirm = input('This will wipe all your profiles. Enter "WIPE" Tto continue: ')
    if confirm == "WIPE":
        shutil.rmtree(PROFILES_DIR)
        log("Removed all profiles!")
    else:
        log("Aborting...")
