#!/usr/bin/python3
#  _   ___  __
# | | | \ \/ /      Prayag Jain | Hax Guru
# | |_| |\  /       YouTube: https://youtube.com/c/haxguru
# |  _  |/  \       GitHub: https://github.com/Prayag2
# |_| |_/_/\_\      Email: prayagjain2@gmail.com
#

## IMPORT ##
import sys, getopt, os, shutil


## VARIABLES ##
argv = sys.argv[1:]
home = os.path.expanduser('~')
config_dir = home + '/.config/'


## FUNCTIONS ##
def mkdir(path):
    '''
    Creates directory if it doesn't exist
    '''
    if not os.path.exists(path):
        os.mkdir(path)


def save_config(name):
    '''
    Saves necessary config files in ~/.haxguru/consave/profiles/<name>
    '''
    # mkdir(home + '/.haxguru/consave/profiles/' + name)
    print(name)


## VALID OPTIONS AND THEIR FUNCTIONS ##
data = {
    '-h': {'func': print, 'user_args': False, 'default_arg': 'Usage: '},
    '-s': {'func': save_config, 'user_args': True}
}


## MAIN ##
def main():
    try:
        options, args = getopt.getopt(argv, 'hls:')

    except getopt.GetoptError:
        print(f"consave: unrecognised option \"{argv[0]}\"\nTry 'consave -h' for more information.")

    else:
        for option, argument in options:
            if option in data:
                opt = data[option]
                opt['func'](argument if opt['user_args'] else opt['default_arg'])
            


## CALLING MAIN ##
if __name__ == '__main__':
    main()