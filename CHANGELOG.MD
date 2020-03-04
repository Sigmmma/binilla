# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0]
### Added
 - Added \_\_main\_\_ so Binilla can be executed using `python -m binilla` or just `binilla` on some systems.

## [1.2.6]
### Changed
 - Make Arbytmap an optional requirement under the feature name `bitmap_viewing`. This should improve Python 3.5 compatibility on Windows as Arbytmap does not have compiled Windows wheels below 3.6.

## [1.2.5]
### Changed
 - Fix improper use of start command for windows in util.open_in_default_program.

## [1.2.4]
### Changed
 - Fix readme potentially breaking setup.

## [1.2.3]
### Changed
 - Fix tags with relative tagpaths not being deletable from handler.

## [1.2.2]
### Changed
 - (Windows) Fix startup crash.

## [1.2.1]
### Added
 - (Linux) Add support for Zenity and Yad filedialogs.
 - (Linux) Warn user when they don't have either Yad, Zenity, or kdialog installed.

### Changed
 - Filter out invalid stdout from kdialog on Linux. Fixes configurations that wrongfully print other stuff to the stdout of the system while kdialog is running.

## [1.2.0]
### Added
 - A button to reset the style, which allows you to reset to both a light or dark theme.
 - A default dark theme.
 - A report bug button.
 - filedialog wrapper that uses kdialog when available to fix it being unusable on Linux.
 - Michelle as an author.
 - Michelle in the license.
 - This changelog!
 - util.open_in_default_program, opens files and folders in their default program.

### Changed
 - About window now opens licenses and readmes in default program if the requirements for the about window cannot be imported.
 - Better default fonts for Linux.
 - Binilla window path properties always return pathlib.Path objects and convert to them.
 - Disabled blocks start hidden and auto-rescale on Linux by default (Fixes some issues with some window managers on Linux).
 - Fix loads of filesystem path things breaking on case sensitive file systems.
 - Fix scroll menu widths.
 - Improve reliability of DynamicEnumFrame when options are volatile.
 - Make default spacing on widgets a little nicer.
 - Requirements. Now has a minimum version for supyr_struct. And a tkinter extensions.
 - Several places where try-except blocks could catch control+c.
 - Switch to tkcolorpicker that supports alphas (Fixes linux having a terrible colorpicker).
 - Update repo url to be github
 - Use pathlib Path for handling filesystem paths.

### Removed
 - get_cwd. Use pathlib or os for this instead.
 - **REMOVED SUPPORT FOR VERSIONS OF PYTHON BELOW 3.5**
