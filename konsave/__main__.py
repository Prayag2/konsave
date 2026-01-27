"""Konsave entry point."""

import argparse
import os
import shutil
from importlib.resources import files

from konsave.consts import (
    CONFIG_FILE,
    VERSION,
    length_of_lop,
    list_of_profiles,
)
from konsave.funcs import (
    apply_profile,
    export,
    import_profile,
    list_profiles,
    remove_profile,
    save_profile,
    wipe,
)


def _get_parser() -> argparse.ArgumentParser:
    """Returns CLI parser.

    Returns:
        argparse.ArgumentParser: Created parser.
    """
    parser = argparse.ArgumentParser(
        prog="Konsave",
        description="A simple and powerful utility for managing your dotfiles.",
        epilog="Please report bugs at https://www.github.com/prayag2/konsave",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )

    # Profile Management Group
    profile_group = parser.add_argument_group(
        "Profile Management", "Commands for managing configuration profiles"
    )
    profile_group.add_argument(
        "-l", "--list",
        action="store_true",
        help="List all saved profiles",
    )
    profile_group.add_argument(
        "-s", "--save",
        type=str,
        help="Save current configuration as a new profile",
        metavar="<name>",
    )
    profile_group.add_argument(
        "-a", "--apply",
        type=str,
        help="Apply a saved profile to restore its configuration",
        metavar="<name>",
    )
    profile_group.add_argument(
        "-r", "--remove",
        type=str,
        help="Delete a saved profile permanently",
        metavar="<name>",
    )
    profile_group.add_argument(
        "-w", "--wipe",
        action="store_true",
        help="Delete all saved profiles (use with caution!)",
    )

    # Import/Export Group
    transfer_group = parser.add_argument_group(
        "Import & Export",
        "Commands for sharing profiles with others",
    )
    transfer_group.add_argument(
        "-e", "--export-profile",
        type=str,
        help="Export a profile as a shareable .knsv archive file",
        metavar="<name>",
    )
    transfer_group.add_argument(
        "-i", "--import-profile",
        type=str,
        help="Import a profile from a .knsv archive file",
        metavar="<path>",
    )

    # Options Group
    options_group = parser.add_argument_group(
        "Options", "Additional options to modify command behavior"
    )
    options_group.add_argument(
        "-f", "--force",
        action="store_true",
        help="Force overwrite when saving/exporting (skip confirmation prompts)",
    )
    options_group.add_argument(
        "-d", "--export-directory",
        help="Specify custom directory for exported profile (default: current directory)",
        metavar="<directory>",
    )
    options_group.add_argument(
        "-n", "--export-name",
        help="Specify custom filename for exported profile archive",
        metavar="<archive-name>",
    )

    # Miscellaneous Group
    misc_group = parser.add_argument_group("Miscellaneous", "Other utility commands")
    misc_group.add_argument(
        "-h", "--help", action="help", help="Show this help message and exit"
    )
    misc_group.add_argument(
        "-v", "--version",
        action="store_true",
        help="Display the current version of Konsave",
    )

    return parser


def main():
    """The main function that handles all the arguments and options."""

    if not os.path.exists(CONFIG_FILE):
        if os.path.expandvars("$XDG_CURRENT_DESKTOP") == "KDE":
            default_config_path = str(files("konsave") / "conf_kde.yaml")
            shutil.copy(default_config_path, CONFIG_FILE)
        else:
            default_config_path = str(files("konsave") / "conf_other.yaml")
            shutil.copy(default_config_path, CONFIG_FILE)

    parser = _get_parser()
    args = parser.parse_args()

    if args.list:
        list_profiles(list_of_profiles, length_of_lop)
    elif args.save:
        save_profile(args.save, list_of_profiles, force=args.force)
    elif args.remove:
        remove_profile(args.remove, list_of_profiles, length_of_lop)
    elif args.apply:
        apply_profile(args.apply, list_of_profiles, length_of_lop)
    elif args.export_profile:
        export(args.export_profile, list_of_profiles, length_of_lop,
               args.export_directory, args.export_name, args.force)
    elif args.import_profile:
        import_profile(args.import_profile)
    elif args.version:
        print(f"Konsave: {VERSION}")
    elif args.wipe:
        wipe()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
