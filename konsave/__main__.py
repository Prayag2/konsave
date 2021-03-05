## IMPORT ##
import argparse
from konsave.funcs import *


## MAIN ##
def main():
    ## PARSER SETTINGS ##
    parser = argparse.ArgumentParser(
        prog='Konsave',
        epilog="Please report bugs at https://www.github.com/prayag2/konsave"
    )

    ## ADDING ARGS ##
    parser.add_argument('-l', '--list', required=False, action='store_true', help='Lists created profiles')
    parser.add_argument('-s', '--save', required=False, type=str, help='Save current config as a profile',
                        metavar='<name>')
    parser.add_argument('-r', '--remove', required=False, type=int, help='Remove the specified profile', metavar='<id>')
    parser.add_argument('-a', '--apply', required=False, type=int, help='Apply the specified profile', metavar='<id>')
    parser.add_argument('-e', '--export-profile', required=False, type=int,
                        help='Export a profile and share with your friends!', metavar='<id>')
    parser.add_argument('-i', '--import-profile', required=False, type=str, help='Import a konsave file',
                        metavar='<path>')
    parser.add_argument('-f', '--force', required=False, action='store_true', help='Overwrite already saved profiles')

    ## PARSING ARGS ##
    args = parser.parse_args()

    ## CHECKING FOR ARGUMENTS ##
    if args.list:
        check_error(list_profiles, list_of_profiles, length_of_lop)
    elif args.save is not None:
        check_error(save_profile, args.save, list_of_profiles, args.force)
    elif args.remove is not None:
        check_error(remove_profile, args.remove, list_of_profiles, length_of_lop)
    elif args.apply is not None:
        check_error(apply_profile, args.apply, list_of_profiles, length_of_lop)
    elif args.export_profile is not None:
        check_error(export, args.export_profile, list_of_profiles, length_of_lop)
    elif args.import_profile is not None:
        check_error(import_profile, args.import_profile)
    else:
        parser.print_help()


## CALLING MAIN ##
if __name__ == '__main__':
    main()
