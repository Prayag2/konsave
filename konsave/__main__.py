"""Konsave entry point."""

import argparse
import os
import shutil
from pkg_resources import resource_filename
from konsave.funcs import (
    list_profiles,
    save_profile,
    remove_profile,
    apply_profile,
    export,
    import_profile,
    wipe,
    log,
)
from konsave.consts import (
    VERSION,
    CONFIG_FILE,
    list_of_profiles,
    length_of_lop,
)


def _get_parser() -> argparse.ArgumentParser:
    """Returns CLI parser.

    Returns:
        argparse.ArgumentParser: Created parser.
    """
    parser = argparse.ArgumentParser(
        prog="Konsave",
        epilog="Please report bugs at https://www.github.com/prayag2/konsave",
    )

    parser.add_argument(
        "-l",
        "--list",
        required=False,
        action="store_true",
        help="Lists created profiles",
    )
    parser.add_argument(
        "-s",
        "--save",
        required=False,
        type=str,
        help="Save current config as a profile",
        metavar="<name>",
    )
    parser.add_argument(
        "-r",
        "--remove",
        required=False,
        type=int,
        help="Remove the specified profile",
        metavar="<id>",
    )
    parser.add_argument(
        "-a",
        "--apply",
        required=False,
        type=int,
        help="Apply the specified profile",
        metavar="<id>",
    )
    parser.add_argument(
        "-e",
        "--export-profile",
        required=False,
        type=int,
        help="Export a profile and share with your friends!",
        metavar="<id>",
    )
    parser.add_argument(
        "-i",
        "--import-profile",
        required=False,
        type=str,
        help="Import a konsave file",
        metavar="<path>",
    )
    parser.add_argument(
        "-f",
        "--force",
        required=False,
        action="store_true",
        help="Overwrite already saved profiles",
    )
    parser.add_argument(
        "-v", "--version", required=False, action="store_true", help="Show version"
    )
    parser.add_argument(
        "-w", "--wipe", required=False, action="store_true", help="Wipes all profiles."
    )

    return parser


def main():
    """The main function that handles all the arguments and options."""

    if not os.path.exists(CONFIG_FILE):
        log("Select your desktop environment-")
        try:
            desktop_environment = int(input("1. KDE Plasma\n2. Other\n=>"))
        except ValueError:
            log("Invalid input.")
            return
        else:
            if desktop_environment == 1:
                default_config_path = resource_filename("konsave", "conf_kde.yaml")
                shutil.copy(default_config_path, CONFIG_FILE)
            elif desktop_environment == 2:
                default_config_path = resource_filename("konsave", "conf_other.yaml")
                shutil.copy(default_config_path, CONFIG_FILE)
            else:
                log("Invalid input.")
                return

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
        export(args.export_profile, list_of_profiles, length_of_lop)
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
