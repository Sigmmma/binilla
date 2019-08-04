# hotkeys
hotkey_combo = "Additional combination to hold when pressing the key"
hotkey_method = "Function to run when this hotkey is pressed"


# main window
main_window_load_last_workspace = (
    "Whether to reload the tags that were open when the program was closed.")
main_window_log_output = "Whether to write console output to a log."
main_window_log_tag_print = "Whether to write tag printouts to the log file"
main_window_debug_mode = (
    "Whether to be in debug mode or not.\nDoesnt do much right now.")
main_window_disable_io_redirect = (
    "Whether to disable redirecting sys.stdout to the io text frame.")


# file handling
file_handling_write_as_temp = (
    "Whether to write tags to temp files instead of the original filepath")
file_handling_allow_corrupt = (
    "Whether to allow loading corrupt tags, which can then be displayed.\n"
    "(This is a debugging feature and should be used with care)")
file_handling_integrity_test = (
    "Whether to do an 'integrity test' after saving a tag to ensure it isnt corrupt.\n"
    "If the tag can be re-opened, it passes the test.\n"
    "If it cant, it is considered corrupt and the saving is cancelled.")


# field widgets
field_widget_edit_uneditable = "Enables editing all fields.\nBE CAREFUL!"
field_widget_show_invisible = (
    "Shows hidden fields(except for fields that describe the structure)."
    )
field_widget_show_structure_meta = (
    "Shows fields that describe the structure of the data\n"
    "This even shows internal values like array counts, so BE CAREFUL!"
    )
field_widget_show_comments = "Whether to show comments. Comments appear above fields"
field_widget_show_tooltips = "Whether to show tooltips. Fields with tooltips are suffixed with �"
field_widget_show_sidetips = "Whether to show sidetips. Sidetips appear on the right side of fields."
field_widget_show_all_bools = (
    "Whether to display a checkbox for each available bit in a boolean, even\n"
    "if that bit doesnt represent anything. Used for debugging and testing.")
field_widget_enforce_max = (
    "Whether to clip entered data to the 'max' value for all fields.\n"
    "For integers and floats, this is the highest number you can enter.\n"
    "For arrays, it is the maximum number of entries in the array.\n"
    "For everything else, it is the maximum number of bytes the data is.")
field_widget_enforce_min = (
    "Whether to clip entered data to the 'min' value for all fields.\n"
    "For integers and floats, this is the lowest number you can enter.\n"
    "For arrays, it is the minimum number of entries in the array.\n"
    "For everything else, it is the minimum number of bytes the data is.")
field_widget_use_unit_scales = (
    "Whether to scale values by their 'unit scale' before displaying them.")
field_widget_use_gui_names = (
    "Whether to use a specially given 'gui name' for the title of each\n"
    "field instead of replacing all underscores in its name with spaces.")
field_widget_blocks_start_hidden = (
    "Whether to start all collapsable blocks in a tag as expanded or collapsed.")
field_widget_empty_blocks_start_hidden = (
    "Whether to start empty collapsable blocks in a tag as expanded or collapsed.")
field_widget_scroll_unselected = (
    "Whether to enable scrolling on widgets that aren't\n" +
    "currently selected, but are underneath the mouse.")
field_widget_evaluate_entry_fields = (
    "Whether to evaluate the contents of a number entry field, rather\n"
    "than directly converting it to a float. Allows user to type in\n"
    "simple functions for a number, such as '(log10(50) + 1) / 2'")

# main window
app_window_recent_tag_max = "Max number of files in the 'recent' menu."
app_window_window_menu_max_len = (
    "Max number of entries to display in the 'windows' menu.\n"
    "After this, a 'window manager' button will be added.")
app_window_max_step = (
    "Number of locations a tag window can be placed\n"
    "before moving down one step.")
app_window_max_step_x = (
    "Number of locations a tag window can be placed\n"
    "horizontally before moving down one step.")
app_window_max_step_y = (
    "Number of locations a tag window can be placed\n"
    "vertically before resetting to placing at the top left.")
app_window_cascade_stride = (
    "Amount of horizontal spacing between 'steps' when cascading tag windows.")
app_window_tile_stride = (
    "Amount of spacing between 'steps' when tiling tag windows.\n"
    "This is also used when placing new tag windows.")
app_window_tile_stride_x = (
    "Amount of horizontal spacing between 'steps' when tiling tag windows.\n"
    "This is also used when placing new tag windows.")
app_window_tile_stride_y = (
    "Amount of vertical spacing between 'steps' when tiling tag windows.\n"
    "This is also used when placing new tag windows.")


# tag windows
tag_windows_sync_window_movement = (
    "Whether to syncronize movement of tag windows with the main window.")
tag_windows_use_default_dimensions = (
    "Whether to set tag window dimensions to the default ones when opening a tag.")
tag_windows_cap_window_size = (
    "Whether to cap the size of tag windows when auto-sizing them\n"
    "so that they dont expand past the edge of the screen.")
tag_windows_dont_shrink_width = (
    "Disables shrinking a tag windows width when auto-sizing it.")
tag_windows_dont_shrink_height = (
    "Disables shrinking a tag windows height when auto-sizing it.")
tag_windows_auto_resize_width = (
    "Whether to resize a tag windows width to fit its contents when something\n"
    "happens to the contents(mouse scrolling, a widget is changed, etc).")
tag_windows_auto_resize_height = (
    "Whether to resize a tag windows height to fit its contents when something\n"
    "happens to the contents(mouse scrolling, a widget is changed, etc).")
tag_windows_max_undos = (
    "Max number of undo/redo operations per tag window.")
tag_windows_default_dimensions = (
    "Default width/height of tag windows if not auto-sizing them.")
tag_windows_default_width = (
    "Default width of tag windows if not auto-sizing them.")
tag_windows_default_height = (
    "Default height of tag windows if not auto-sizing them.")
tag_windows_scroll_increment = (
    "Number of pixels to jump when scrolling horizontally/vertically.")
tag_windows_scroll_increment_x = (
    "Number of pixels to jump when scrolling horizontally.")
tag_windows_scroll_increment_y = (
    "Number of pixels to jump when scrolling vertically.")


# tag printing
tag_printing_flags = "Flags governing what is shown when a tag is printed."
tag_printint_print_indent = (
    "Number of spaces to indent each print level.")

# tag backup
tag_backup_notify = (
    "When a backup occurs, the path to the backup will be printed in the console.")
tag_backup_max_count = (
    "Max number of rolling backups to make before overwriting the oldest.")
tag_backup_interval = (
    "The amount of time in seconds that must pass between saves before\n"
    "the rolling backup system will backup a tag being overwritten.")
tag_backup_folder_basename = (
    "The name of the folder to backup to. For files that are relative to a tags\n"
    "directory, this backup folder will be created in the root of the tags\n"
    "directory. Otherwise it will be created in the same folder as the file.")
