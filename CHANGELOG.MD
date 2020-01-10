# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
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
