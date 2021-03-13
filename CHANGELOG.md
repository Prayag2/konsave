# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- ``CHANGELOG.md`` file with (Keep a Changelog)[https://keepachangelog.com/en/1.0.0/] format.

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

## Additions
- Added a CONTRIBUTIONS.md

## Fixes
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
