# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
 - Michelle as an author.
 - Michelle in the license.
 - This changelog!
 - A report bug button.
 - filedialog wrapper that uses kdialog when available to fix it being unusable on Linux.
 - util.open_in_default_program, opens files and folders in their default program.

### Changed
 - Add colorpicker that supports alphas (Fixes linux having a terrible colorpicker).
 - Fix scroll menu widths.
 - Improve reliability of DynamicEnumFrame when options are volatile.
 - Disabled blocks start hidden on Linux (Fixes some issues with some window managers).
 - Fix loads of filesystem path things breaking on case sensitive file systems.
 - Use pathlib Path for handling filesystem paths.
 - Several places where try-except blocks could catch control+c.
 - Binilla window path properties always return pathlib Path objects and convert to them.
 - Requirements. Now has a minimum version for supyr_struct. And a tkinter extensions.
 - Update repo url to be github
 - About window now opens licenses and readmes in default program if the requirements for the about window cannot be imported.

### Removed
 - get_cwd. Use pathlib or os for this instead.
