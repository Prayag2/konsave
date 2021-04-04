<h1 align=center> Konsave (Save Plasma Customization) </h1>
<p align=center>A CLI program that will let you save and apply your KDE Plasma customizations with just one command! Also, it has a "K" in the name :D</p>

---

<p align="center">
<img src="https://user-images.githubusercontent.com/39525869/109611033-a6732c80-7b53-11eb-9ece-ffd9cef49047.gif" />
</p>

---

## Installation
Install from PyPI  
`python -m pip install konsave`

## Usage
### Get Help
`konsave -h` or `konsave --help`
### Save current configuration as a profile
`konsave -s <profile name>` or `konsave --save <profile name>`
### Overwrite an already saved profile
`konsave -s <profile name> -f` or `konsave -s <profile name> --force `
### List all profiles
`konsave -l` or `konsave --list`
### Remove a profile
`konsave -r <profile id>` or `konsave --remove <profile id>`
### Apply a profile
`konsave -a <profile id>` or `konsave --apply <profile id>`
You may need to log out and log in to see all the changes.  
### Export a profile as a ".knsv" file to share it with your friends!
`konsave -e <profile id>` or `konsave --export-profile <profile id>`
### Import a ".knsv file
`konsave -i <path to the file>` or `konsave --import-profile <path to the file>`
### Show current version
`konsave -v` or `konsave --version`  
### Wipe all profiles
`konsave -w` or `konsave --wipe`

## Uninstall Konsave
To uninstall konsave, run the following:  
`python -m pip uninstall konsave`  
<br>

---

# UNRELEASED FEATURES
These features have been recently added to Konsave but will remain unreleased for some time. The version is `2.0.0-alpha.1`. Your feedback will be appreciated greatly.

## Installation of the unreleased version
To test these features out, you can install Konsave by entering the following commands in your terminal:  
-  `git clone https://github.com/prayag2/konsave`  
-  `cd konsave`  
-  `python -m pip install -e .`

## Uninstall
- `python -m pip uninstall konsave`


## The Features:
- You'll be able to edit konsave's configuration file to backup files/folders of your choice! You can add as many configurations to backup as you want.
- You can use a few pre-defined variables and functions in the configuration file.
- Exporting and importing is a lot better now.
- This version of Konsave is not compatible with the older versions so the versioning has changed to 2.0.0. Please give your valuable feedback and help us improve Konsave!

---

<br>

## Contribution
Please read [CONTRIBUTION.md](https://github.com/Prayag2/konsave/blob/master/CONTRIBUTION.md) for info about contributing. 

## License
This project uses GNU General Public License 3.0
