# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
## [2.2.0] - 2023-01-31
### Added
- You can now set the output directory and archive name when exporting a profile ([#72](https://github.com/Prayag2/konsave/pull/72))
- Profiles will now be listed in alphabetical order (#67)

### Fixed
- Fixed typo in README (#48)

### Changed
- Improved README (#75)
- Made it clear that a profile needs to be saved before exporting in the help text.
- Logs will now be saved to `$HOME/.cache/konsave_log.txt`


## [2.1.2] - 2022-04-20
### Fixed
- Empty entries in the config files will now be parsed as empty strings to prevent an exception. See [#50](https://github.com/Prayag2/konsave/pull/50)
- A small typo was fixed. See [#51](https://github.com/Prayag2/konsave/pull/51)
- Fixed incorrect PyYaml version in `requirements.txt`. See [#56](https://github.com/Prayag2/konsave/pull/56)

### Added
- Kate's (KDE's code editor) config files were added in the default KDE config file. See [#58](https://github.com/Prayag2/konsave/pull/58)

## [2.1.1] - 2021-10-24
### Removed
- Removed the prompt that asked you which desktop environment you use when you ran Konsave for the first time. See [#45](https://github.com/Prayag2/konsave/issues/45).
- Removed unused import of the `log` function in `__main__.py`.

### Changed
- Konsave will now automatically detect if you're using KDE plasma or not.
- Fixed some Pylint errors.

## [2.1.0] - 2021-09-07
### Added
- The following placeholders for `config.yaml` were added:
    1. `$SHARE_DIR`: It points to `$HOME/.local/share`
    2. `$BIN_DIR`: It points to `$HOME/.local/bin`

### Changed
- Now, there's no need to check for the ID of a profile if you already know its name. You can remove, apply and export a profile using its name. For example `konsave --export myprofile`. See [#38](https://github.com/Prayag2/konsave/issues/38)
- Replaced the words "variables and functions" with "placeholders".
- Updated readme.

### Removed
- You'll no longer be able to use IDs to remove, apply and export profiles. You have to use the name of the profile to do so.
- The following placeholders were removed:
    - `$KONSAVE_DIR`
    - `$CONFIG_DIR`

## [2.0.2] - 2021-04-13
### Fixed
- Fixed a bug with export. Previously, exporting a profile would export the current profile but now it will export the specified profile.
- Fixed a typo in the readme

## Added
- Added a line in the readme

## [2.0.1] - 2021-04-11
### Removed
- KDE Plasma won't be restarted after applying a new configuration now. You'll have to restart it yourself. This was done because using Konsave on other DEs would give an error.

## [2.0.0] - 2021-04-11
### Added
- Possibility to define multiple backup targets via the configuration file.
- Errors will be saved to `konsave_log.txt` in the home directory.
- Ability to use a few variables and functions in the configuration file.
- Ability to use Konsave on all desktop environments.

### Changed
- Improved export and import feature. You'll be able change which files to export and import from the configuration file.
- Changed yaml loader from `yaml.FullLoader` to `yaml.SafeLoader`
- The version will now be dynamically printed.

### Break
- The old configuration files and profiles won't work with this version of Konsave.

## [1.1.9] - 2021-03-18
### Fixes
- Fixes [#26](https://github.com/Prayag2/konsave/issues/26)
- Prints help when entering "konsave" without any arguments

## [1.1.8] - 2021-03-18
### Changes
- Add missing new lines at end of `.pylintrc` and `CONTRIBUTION.md`.
- Gitignore:
    - Common VS Code and JetBrains IDE user-specific stuff.
    - All `__pycache__` dirs (`**/__pycache__`).
- Delete and untrack all `*.pyc` files.
- Reformat and improve some docstrings.
- Remove some excessive comments, e.g. `## IMPORTS ##` or `# WIPE`. The import section is clear and visible enough to not need such additional comment. Same with functions - docstrings do that job well.
- Refactor and simplify CLI argument parsing.
- Adapt `setup.py` to use pip requirement text files.
    - Create extra `dev` and corresponding `requirements_dev.txt` requirement text file. Can be installed via `pip install -e .[dev]` or from PyPI via `pip install konsave[dev]`.
- Remove "Dependencies" section from `README.md` - dependencies get installed automatically anyway.

## [1.1.7] - 2021-03-13
### Fixes
- Fixed [#28](https://github.com/Prayag2/konsave/issues/28)

## Changes
- The program will now quit on any error


## [1.1.6] - 2021-03-11
### Changes
- Changed code style to [PEP8](https://www.python.org/dev/peps/pep-0008/)
- Changed docstring style to [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- Updated README

### Additions
- Added a CONTRIBUTIONS.md

### Fixes
- Fixed a possible bug. Refer to [#26](https://github.com/Prayag2/konsave/issues/26).

## [1.1.5] - 2021-03-08
### Changes
- Changed `print_msg` to `log`.
- Changed `check_error` function to a decorator (Thanks to (this article)[https://medium.com/swlh/handling-exceptions-in-python-a-cleaner-way-using-decorators-fae22aa0abec]) for easier maintenance.
- Improved logging

## [1.1.4] - 2021-03-07
### Changes
- Created a function called `copy` to replace `shutil.copytree`. This would add support for python versions <= 3.7. 
- Changed version in `vars.py` from 1.1.3 to 1.1.4

### Fixes
- Previously, running `konsave --export <id>` would cause it to export the CURRENT icon and cursor theme. Now, it will export the icon and cursor theme of the profile being exported.
- Some fixes in `copy()`

## [1.1.3] - 2021-03-06
### Changes
- Fixed something

## [1.1.2] - 2021-03-06
### Changes
- Fixed something

## [1.1.1] - 2021-03-06
### Changes
- Fixed a bug

## [1.1.0] - 2021-03-06
### Changes
- You can now wipe all your profiles at once using konsave -w or konsave --wipe

## [1.0.7] - 2021-03-06
### Changes
- bug fixes

## [1.0.6] - 2021-03-06
### Changes made by @majabojarska
- Add GitHub Actions workflow "Release". Runs on tag push, named v* (e.g. v1.0.5). This workflow creates a GitHub release and publishes the package to PyPI repository.
- Change setup.py manual versioning to SCM versioning - the tag's version determines the package's version. This means that tag v1.0.5 results in package version 1.0.5 on PyPI. This also means that the package version won't be maintained via source code, but via Git tags.


## [1.0.5] - 2021-03-06
### Changes
- Fixed a small mistake with the versioning

## [1.0.4] - 2021-03-05
### Changes
- You can now use the --force or -f option to overwrite existing profiles!
- A separate config file has been introduced for easier maintenance

## [1.0.3] - 2021-03-05
### Changes
- Deployed it to PyPI!

## [1.0.2] - 2021-02-28
### Changes
- Fixed a small bug

## [1.0.1] - 2021-02-28
### Changes
- Bug fixes
- Better import and export
    + It will now export and import the installed themes, icons, cursors and plasmoids so there will be no need to install the themes manually on other machines.

## [1.0.0] - 2021-02-27
### Changes
- You can now export and import your favourite profiles as ".knsv" files and share them with your friends!
- You can also import ".knsv" files as profiles!


[2.2.0]: https://github.com/Prayag2/konsave/compare/v2.1.2...v2.2.0
[2.1.2]: https://github.com/Prayag2/konsave/compare/v2.1.1...v2.1.2
[2.1.1]: https://github.com/Prayag2/konsave/compare/v2.1.0...v2.1.1
[2.1.0]: https://github.com/Prayag2/konsave/compare/v2.0.2...v2.1.0
[2.0.2]: https://github.com/Prayag2/konsave/compare/v2.0.1...v2.0.2
[2.0.1]: https://github.com/Prayag2/konsave/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/Prayag2/konsave/compare/v1.1.9...v2.0.0
[1.1.9]: https://github.com/Prayag2/konsave/compare/v1.1.8...v1.1.9
[1.1.8]: https://github.com/Prayag2/konsave/compare/v1.1.7...v1.1.8
[1.1.7]: https://github.com/Prayag2/konsave/compare/v1.1.6...v1.1.7
[1.1.6]: https://github.com/Prayag2/konsave/compare/v1.1.5...v1.1.6
[1.1.5]: https://github.com/Prayag2/konsave/compare/v1.1.4...v1.1.5
[1.1.4]: https://github.com/Prayag2/konsave/compare/v1.1.3...v1.1.4
[1.1.3]: https://github.com/Prayag2/konsave/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/Prayag2/konsave/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/Prayag2/konsave/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/Prayag2/konsave/compare/v1.0.7...v1.1.0
[1.0.7]: https://github.com/Prayag2/konsave/compare/v1.0.6...v1.0.7
[1.0.6]: https://github.com/Prayag2/konsave/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/Prayag2/konsave/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/Prayag2/konsave/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/Prayag2/konsave/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/Prayag2/konsave/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/Prayag2/konsave/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/Prayag2/konsave/compare/6b4a0c0bbf8c29684cc2a334065314bc8e4ea529...v1.0.0
[Unreleased]: https://github.com/Prayag2/konsave/compare/v1.0.0...HEAD
