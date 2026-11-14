"""
This module contains all the functions for konsave.
"""

import fnmatch
import os
import shutil
import stat
import tempfile
import traceback
from datetime import datetime
from zipfile import is_zipfile, ZipFile
from konsave.consts import (
    HOME,
    CONFIG_FILE,
    PROFILES_DIR,
    EXPORT_EXTENSION,
    KONSAVE_DIR,
)
from konsave.parse import TOKEN_SYMBOL, tokens, parse_functions, parse_keywords

try:
    import yaml
except ModuleNotFoundError as error:
    raise ModuleNotFoundError(
        "Please install the module PyYAML using pip: \n pip install PyYAML"
    ) from error


# Set by exception_handler so front-ends can tell whether the last wrapped
# operation failed without parsing console output.
LAST_ERROR = None


def exception_handler(func):
    """Handles errors and prints nicely.

    Args:
        func: any function

    Returns:
        Returns function
    """

    def inner_func(*args, **kwargs):
        global LAST_ERROR
        LAST_ERROR = None
        try:
            function = func(*args, **kwargs)
        except Exception as err:
            LAST_ERROR = str(err)
            dateandtime = datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
            log_file = os.path.join(HOME, ".cache/konsave_log.txt")
            mkdir(os.path.dirname(log_file))

            with open(log_file, "a", encoding="utf-8") as file:
                file.write(dateandtime + "\n")
                traceback.print_exc(file=file)
                file.write("\n")

            print(
                f"Konsave: {err}\nPlease check the log at {log_file} for more details."
            )
            return None

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
    print(f"Konsave: {msg}", *args, **kwargs)


@exception_handler
def copy(source, dest):
    """
    This function was created because shutil.copytree gives error if the destination folder
    exists and the argument "dirs_exist_ok" was introduced only after python 3.8.
    This restricts people with python 3.7 or less from using Konsave.
    This function will let people with python 3.7 or less use Konsave without any issues.
    It uses recursion to copy files and folders from "source" to "dest"

    Special files such as sockets (for example the ssh-agent socket) are
    skipped, and a failing entry does not abort the whole operation.

    Args:
        source: the source destination
        dest: the destination to copy the file/folder to
    """
    assert isinstance(source, str) and isinstance(dest, str), "Invalid path"
    assert source != dest, "Source and destination can't be same"
    assert os.path.exists(source), "Source path doesn't exist"

    if not os.path.exists(dest):
        os.mkdir(dest)

    for item in os.listdir(source):
        source_path = os.path.join(source, item)
        dest_path = os.path.join(dest, item)

        try:
            mode = os.stat(source_path).st_mode
        except OSError as error:
            log(f'Warning: skipping "{source_path}": {error}')
            continue

        # Skip sockets, fifos and device files; they cannot be copied and are
        # never part of a portable profile.
        if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            log(f'Warning: skipping special file "{source_path}"')
            continue

        if os.path.isdir(source_path):
            copy(source_path, dest_path)
        else:
            try:
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                if os.path.exists(source_path):
                    shutil.copy(source_path, dest)
            except OSError as error:
                log(f'Warning: could not copy "{source_path}": {error}')


def copy_item(source, dest):
    """Copies a single file or directory, skipping special files.

    Args:
        source: path to copy from
        dest: path to copy to
    """
    if not os.path.exists(source):
        return
    try:
        mode = os.stat(source).st_mode
    except OSError as error:
        log(f'Warning: skipping "{source}": {error}')
        return
    if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
        log(f'Warning: skipping special file "{source}"')
        return
    if os.path.isdir(source):
        copy(source, dest)
    else:
        try:
            shutil.copy(source, dest)
        except OSError as error:
            log(f'Warning: could not copy "{source}": {error}')


def group_entries(group) -> list:
    """Returns the entries of a config group.

    Groups normally list their entries explicitly. A group may instead set
    ``traversal: files`` to include every regular file directly inside the
    location (useful for apps like Tabby whose config lives next to large
    cache directories). ``exclude`` is an optional list of glob patterns that
    are filtered out in traversal mode.

    Args:
        group: a config group dict with "location" and optionally "entries"

    Returns:
        The list of entries for the group.
    """
    if (group.get("traversal") or "").lower() == "files":
        location = group.get("location", "")
        patterns = group.get("exclude") or []
        try:
            return sorted(
                entry
                for entry in os.listdir(location)
                if os.path.isfile(os.path.join(location, entry))
                and not any(fnmatch.fnmatch(entry, pattern) for pattern in patterns)
            )
        except OSError:
            return []
    return group.get("entries") or []


@exception_handler
def read_konsave_config(config_file) -> dict:
    """Reads "conf.yaml" and parses it.

    Args:
        config_file: path to the config file
    """
    with open(config_file, "r", encoding="utf-8") as text:
        konsave_config = yaml.load(text.read(), Loader=yaml.SafeLoader)
    parse_keywords(tokens, TOKEN_SYMBOL, konsave_config)
    parse_functions(tokens, TOKEN_SYMBOL, konsave_config)

    # in some cases conf.yaml may contain nothing in "entries". Yaml parses
    # these as NoneType which are not iterable which throws an exception
    # we can convert all None-Entries into empty lists recursively so they
    # are simply skipped in loops later on
    def convert_none_to_empty_list(data):
        if isinstance(data, list):
            data[:] = [convert_none_to_empty_list(i) for i in data]
        elif isinstance(data, dict):
            for k, v in data.items():
                data[k] = convert_none_to_empty_list(v)
        return [] if data is None else data

    return convert_none_to_empty_list(konsave_config)


def resolve_location(location) -> str:
    """Resolves placeholders and functions in a location string.

    Args:
        location: raw location from conf.yaml

    Returns:
        The location with placeholders like "$HOME" expanded.
    """
    config = {"save": {"item": {"location": location, "entries": []}}}
    parse_keywords(tokens, TOKEN_SYMBOL, config)
    parse_functions(tokens, TOKEN_SYMBOL, config)
    return config["save"]["item"]["location"]


def cache_profiles():
    """Refreshes the cached profile list in konsave.consts."""
    from konsave import consts

    consts.list_of_profiles = os.listdir(PROFILES_DIR)
    consts.length_of_lop = len(consts.list_of_profiles)
    return consts.list_of_profiles


@exception_handler
def list_profiles(profile_list, profile_count):
    """Lists all the created profiles.

    Args:
        profile_list: the list of all created profiles
        profile_count: number of profiles created
    """

    # assert
    assert os.path.exists(PROFILES_DIR) and profile_count != 0, "No profile found."

    # sort in alphabetical order
    profile_list.sort()

    # run
    print("Konsave profiles:")
    print("ID\tNAME")
    for i, item in enumerate(profile_list):
        print(f"{i + 1}\t{item}")


@exception_handler
def save_profile(name, profile_list, force=False, selection=None):
    """Saves necessary config files in ~/.config/konsave/profiles/<name>.

    Args:
        name: name of the profile
        profile_list: the list of all created profiles
        force: force overwrite already created profile, optional
        selection: optional mapping of save group name to the entries that
            should be included in the profile. If omitted, every entry is saved.
    """

    # assert
    assert name not in profile_list or force, "Profile with this name already exists"
    if name in profile_list and force:
        shutil.rmtree(os.path.join(PROFILES_DIR, name))

    # run
    log("saving profile...")
    profile_dir = os.path.join(PROFILES_DIR, name)
    mkdir(profile_dir)

    konsave_config = read_konsave_config(CONFIG_FILE)["save"]

    for section in konsave_config:
        location = konsave_config[section]["location"]
        folder = os.path.join(profile_dir, section)
        mkdir(folder)
        for entry in group_entries(konsave_config[section]):
            if selection is not None and entry not in selection.get(section, []):
                continue
            source = os.path.join(location, entry)
            dest = os.path.join(folder, entry)
            copy_item(source, dest)

    shutil.copy(CONFIG_FILE, profile_dir)
    cache_profiles()

    log("Profile saved successfully!")


@exception_handler
def apply_profile(profile_name, profile_list, profile_count, config_path=None):
    """Applies profile of the given id.

    Args:
        profile_name: name of the profile to be applied
        profile_list: the list of all created profiles
        profile_count: number of profiles created
        config_path: optional path of the profile's own conf.yaml. This ensures
            the profile is applied with the definitions it was saved with.
    """

    # assert
    assert profile_count != 0, "No profile saved yet."
    assert profile_name in profile_list, "Profile not found :("

    # run
    profile_dir = os.path.join(PROFILES_DIR, profile_name)

    log("copying files...")

    config_location = config_path or os.path.join(profile_dir, "conf.yaml")
    profile_config = read_konsave_config(config_location)["save"]
    for name in profile_config:
        location = os.path.join(profile_dir, name)
        if not os.path.isdir(location):
            continue
        copy(location, profile_config[name]["location"])

    log(
        "Profile applied successfully! Please log-out and log-in to see the changes completely!"
    )


@exception_handler
def remove_profile(profile_name, profile_list, profile_count):
    """Removes the specified profile.

    Args:
        profile_name: name of the profile to be removed
        profile_list: the list of all created profiles
        profile_count: number of profiles created
    """

    # assert
    assert profile_count != 0, "No profile saved yet."
    assert profile_name in profile_list, "Profile not found."

    # run
    log("removing profile...")
    shutil.rmtree(os.path.join(PROFILES_DIR, profile_name))
    cache_profiles()
    log("removed profile successfully")


@exception_handler
def export(
    profile_name,
    profile_list,
    profile_count,
    archive_dir,
    archive_name,
    force,
    selection=None,
    save_selection=None,
):
    """It will export the specified profile as a ".knsv" to the specified directory.
       If there is no specified directory, the directory is set to the current working directory.

    Args:
        profile_name: name of the profile to be exported
        profile_list: the list of all created profiles
        profile_count: number of profiles created
        archive_dir: output directory for the export
        force: force the overwrite of existing export file
        archive_name: the name of the resulting archive
        selection: optional mapping of export group name to the entries that
            should be included in the archive. If omitted, every entry is exported.
        save_selection: optional mapping of save group name to the entries that
            should be copied from the profile. If omitted, the whole profile is
            exported.
    """

    # assert
    assert profile_count != 0, "No profile saved yet."
    assert profile_name in profile_list, "Profile not found."

    # run
    profile_dir = os.path.join(PROFILES_DIR, profile_name)

    if archive_name:
        profile_name = archive_name

    if archive_dir:
        export_path = os.path.join(archive_dir, profile_name)
    else:
        export_path = os.path.join(os.getcwd(), profile_name)

    # Only continue if export_path, export_path.ksnv and export_path.zip don't exist
    # Appends date and time to create a unique file name
    if not force:
        while True:
            paths = [f"{export_path}", f"{export_path}.knsv", f"{export_path}.zip"]
            if any(os.path.exists(path) for path in paths):
                time = "f{:%d-%m-%Y:%H-%M-%S}".format(datetime.now())
                export_path = f"{export_path}_{time}"
            else:
                break

    # compressing the files as zip
    log("Exporting profile. It might take a minute or two...")

    profile_config_file = os.path.join(profile_dir, "conf.yaml")
    konsave_config = read_konsave_config(profile_config_file)

    export_path_save = mkdir(os.path.join(export_path, "save"))
    for name in konsave_config.get("save") or {}:
        location = os.path.join(profile_dir, name)
        if not os.path.isdir(location):
            continue
        log(f'Exporting "{name}"...')
        if save_selection is None:
            copy(location, os.path.join(export_path_save, name))
        else:
            allowed = save_selection.get(name, [])
            dest_dir = mkdir(os.path.join(export_path_save, name))
            for entry in os.listdir(location):
                if entry not in allowed:
                    continue
                source = os.path.join(location, entry)
                dest = os.path.join(dest_dir, entry)
                copy_item(source, dest)

    konsave_config_export = konsave_config.get("export") or {}
    export_path_export = mkdir(os.path.join(export_path, "export"))
    for name in konsave_config_export:
        location = konsave_config_export[name]["location"]
        path = mkdir(os.path.join(export_path_export, name))
        for entry in group_entries(konsave_config_export[name]):
            if selection is not None and entry not in selection.get(name, []):
                continue
            source = os.path.join(location, entry)
            dest = os.path.join(path, entry)
            log(f'Exporting "{entry}"...')
            copy_item(source, dest)

    # The archive must carry the profile's own config so it can be imported
    # and applied on another machine.
    shutil.copy(profile_config_file, export_path)

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

    temp_path = tempfile.mkdtemp(prefix="konsave-import-", dir=KONSAVE_DIR)

    with ZipFile(path, "r") as zip_file:
        zip_file.extractall(temp_path)

    config_file_location = os.path.join(temp_path, "conf.yaml")
    konsave_config = read_konsave_config(config_file_location)

    profile_dir = os.path.join(PROFILES_DIR, item)
    copy(os.path.join(temp_path, "save"), profile_dir)
    shutil.copy(os.path.join(temp_path, "conf.yaml"), profile_dir)

    for section in konsave_config.get("export") or {}:
        location = konsave_config["export"][section]["location"]
        path = os.path.join(temp_path, "export", section)
        if not os.path.isdir(path):
            continue
        for entry in os.listdir(path):
            source = os.path.join(path, entry)
            dest = os.path.join(location, entry)
            log(f'Importing "{entry}"...')
            if os.path.exists(source):
                if os.path.isdir(source):
                    copy(source, dest)
                else:
                    shutil.copy(source, dest)

    shutil.rmtree(temp_path)
    cache_profiles()

    log("Profile successfully imported!")


@exception_handler
def wipe():
    """Wipes all profiles."""
    confirm = input('This will wipe all your profiles. Enter "WIPE" To continue: ')
    if confirm == "WIPE":
        shutil.rmtree(PROFILES_DIR)
        log("Removed all profiles!")
    else:
        log("Aborting...")
