from tkinter import ttk
import tkinter.font

from supyr_struct.defs.tag_def import TagDef
from supyr_struct.field_types import *
from binilla.defs.hotkey_enums import method_enums, modifier_enums, hotkey_enums
from binilla.defs.style_def import appearance, widths_and_heights, padding,\
     depths, colors, fonts, theme_name
from binilla.widgets.field_widgets.array_frame import DynamicArrayFrame
from binilla.constants import GUI_NAME, NAME, TOOLTIP, VALUE, VISIBLE, NODE_PRINT_INDENT
from binilla.editor_constants import widget_depth_names, color_names,\
     font_names


__all__ = (
    "get", "config_def",
    )


pad_str = "Padding applied to the %s of widgets oriented %sally"

flag_tooltips = (
    "Whether to syncronize movement of tag windows with the main window.",
    "Whether to reload the tags that were open when the program was closed.",
    "Whether to write console output to a log.",
    "Whether to write tag printouts to the log file",
    "Whether to be in debug mode or not.\nDoesnt do much right now.",
    "Whether to disable redirecting sys.stdout to the io text frame."
    )

handler_flag_tooltips = (
    ("Whether to rename original files with a .backup extension before\n" +
     "the first time you save, so as to keep an original backup."),
    "Whether to write tags to temp files instead of the original filepath",
    ("Whether to allow loading corrupt tags, which can then be displayed.\n" +
     "(This is a debugging feature and should be used with care)"),
    ("Whether to do an 'integrity test' after saving a tag to ensure it isnt corrupt.\n" +
     "If the tag can be re-opened, it passes the test.\n" +
     "If it cant, it is considered corrupt and the saving is cancelled."),
    )

tag_window_flag_tooltips = (
    "Enables editing all fields.\nBE CAREFUL!",
    "Shows every field(even internal values like array counts).\nBE CAREFUL!",
    ("Whether to clip entered data to the 'max' value for all fields.\n" +
     "For integers and floats, this is the highest number you can enter.\n" +
     "For arrays, it is the maximum number of entries in the array.\n" +
     "For everything else, it is the maximum number of bytes the data is."),
    ("Whether to clip entered data to the 'min' value for all fields.\n" +
     "For integers and floats, this is the lowest number you can enter.\n" +
     "For arrays, it is the minimum number of entries in the array.\n" +
     "For everything else, it is the minimum number of bytes the data is."),
    "Whether to scale values by their 'unit scale' before displaying them.",
    ("Whether to use a specially given 'gui name' for the title of each\n" +
     "field instead of replacing all underscores in its name with spaces."),
    "Whether to start all collapsable blocks in a tag as expanded or collapsed.",
    "Whether to show comments.",
    "Whether to show tooltips.",
    "Whether to show sidetips.",
    ("Whether to cap the size of tag windows when auto-sizing them\n" +
     "so that they dont expand past the edge of the screen."),
    "Disables shrinking a tag windows width when auto-sizing it.",
    "Disables shrinking a tag windows height when auto-sizing it.",
    "Whether to set tag window dimensions to the default ones when opening a tag.",
    ("Whether to enable scrolling on widgets that aren't\n" +
     "currently selected, but are underneath the mouse."),
    ("Whether to resize a tag windows width to fit its contents when something\n" +
     "happens to the contents(mouse scrolling, a widget is changed, etc)."),
    ("Whether to resize a tag windows height to fit its contents when something\n" +
     "happens to the contents(mouse scrolling, a widget is changed, etc)."),
    ("Whether to start empty collapsable blocks in a tag as expanded or collapsed."),
    ("Whether to evaluate the contents of a number entry field, rather\n"
     "than directly converting it to a float. Allows user to type in\n"
     "simple functions for a number, such as '(log10(50) + 1) / 2'"),
    ("Whether to display a checkbox for each available bit in a boolean, even\n" +
     "if that bit doesnt represent anything. Used for debugging and testing."),
    )

app_window_tooltips = (
    "Width of the main window",
    "Height of the main window",
    "X position of the main window",
    "Y position of the main window",
    ("Max number of entries to display in the 'windows' menu." +
     "\nAfter this, a 'window manager' button will be added."),
    ("Number of locations a tag window can be placed\n" +
     "horizontally before moving down one step."),
    ("Number of locations a tag window can be placed\n" +
     "vertically before resetting to placing at the top left."),
    "Amount of horizontal spacing between 'steps' when cascading tag windows.",
    ("Amount of horizontal spacing between 'steps' when tiling tag windows.\n" +
     "This is also used when placing new tag windows."),
    ("Amount of vertical spacing between 'steps' when tiling tag windows.\n" +
     "This is also used when placing new tag windows."),
    "Default width of tag windows if not auto-sizing them.",
    "Default height of tag windows if not auto-sizing them.",
    "Number of pixels to jump when scrolling horizontally.",
    "Number of pixels to jump when scrolling vertically.",
    )

hotkey = Struct("hotkey",
    BitStruct("combo",
        UBitEnum("modifier", GUI_NAME="", *modifier_enums, SIZE=4,
            TOOLTIP="Additional combination to hold when pressing the key"),
        UBitEnum("key", GUI_NAME="and", *hotkey_enums, SIZE=28),
        SIZE=4, ORIENT='h'
        ),
    UEnum32("method", *method_enums,
        TOOLTIP="Function to run when this hotkey is pressed")
    )

open_tag = Container("open_tag",
    Struct("header",
        UInt16("width"),
        UInt16("height"),
        SInt16("offset_x"),
        SInt16("offset_y"),
        Bool32("flags",
            "minimized",
            ),

        # UPDATE THIS PADDING WHEN ADDING STUFF ABOVE IT
        Pad(48 - 2*4 - 4*1),

        UInt16("def_id_len", VISIBLE=False, EDITABLE=False),
        UInt16("path_len", VISIBLE=False, EDITABLE=False),
        SIZE=64
        ),

    StrUtf8("def_id", SIZE=".header.def_id_len"),
    StrUtf8("path", SIZE=".header.path_len"),
    )

filepath = Container("filepath",
    UInt16("path_len", VISIBLE=False),
    StrUtf8("path", SIZE=".path_len")
    )

main_window_flags = Bool32("flags",
    {NAME: "load_last_workspace", TOOLTIP: flag_tooltips[1]},
    {NAME: "log_output",    TOOLTIP: flag_tooltips[2]},
    {NAME: "log_tag_print", TOOLTIP: flag_tooltips[3]},
    {NAME: "debug_mode",    TOOLTIP: flag_tooltips[4]},
    {NAME: "disable_io_redirect", TOOLTIP: flag_tooltips[5]},
       
    DEFAULT=sum([1<<i for i in (1, 2)])
    )

file_handling_flags = Bool32("file_handling_flags",
    {NAME: "backup_tags",   TOOLTIP: handler_flag_tooltips[0]},
    {NAME: "write_as_temp", TOOLTIP: handler_flag_tooltips[1]},
    {NAME: "allow_corrupt", TOOLTIP: handler_flag_tooltips[2]},
    {NAME: "integrity_test", TOOLTIP: handler_flag_tooltips[3]},
    DEFAULT=sum([1<<i for i in (0, 3)])
    )

field_widget_flags = Bool32("widget_flags",
    {NAME: "edit_uneditable", TOOLTIP: tag_window_flag_tooltips[0]},
    {NAME: "show_invisible",  TOOLTIP: tag_window_flag_tooltips[1]},
    #"row_row_fight_powuh",
    {NAME: "show_comments", TOOLTIP: tag_window_flag_tooltips[7]},
    {NAME: "show_tooltips", TOOLTIP: tag_window_flag_tooltips[8]},
    {NAME: "show_sidetips", TOOLTIP: tag_window_flag_tooltips[9]},
    {NAME: "show_all_bools", TOOLTIP: tag_window_flag_tooltips[-1]},

    {NAME: "enforce_max", TOOLTIP: tag_window_flag_tooltips[2]},
    {NAME: "enforce_min", TOOLTIP: tag_window_flag_tooltips[3]},
    {NAME: "use_unit_scales", TOOLTIP: tag_window_flag_tooltips[4]},
    {NAME: "use_gui_names", TOOLTIP: tag_window_flag_tooltips[5]},

    {NAME: "blocks_start_hidden", TOOLTIP: tag_window_flag_tooltips[6]},
    {NAME: "empty_blocks_start_hidden", TOOLTIP: tag_window_flag_tooltips[17]},

    {NAME: "scroll_unselected", TOOLTIP: tag_window_flag_tooltips[14]}, # RENAMED
    {NAME: "evaluate_entry_fields", TOOLTIP: tag_window_flag_tooltips[18]},
    DEFAULT=sum([1<<i for i in (2, 3, 4, 6, 7, 8, 9, 10)])
    )

tag_window_flags = Bool32("window_flags",
    {NAME: "sync_window_movement", TOOLTIP: flag_tooltips[0], VISIBLE: False},
    {NAME: "use_default_window_dimensions", TOOLTIP: tag_window_flag_tooltips[13]},
    {NAME: "cap_window_size", TOOLTIP: tag_window_flag_tooltips[10]},
    {NAME: "dont_shrink_width", TOOLTIP: tag_window_flag_tooltips[11]},
    {NAME: "dont_shrink_height", TOOLTIP: tag_window_flag_tooltips[12]},
    {NAME: "auto_resize_width", TOOLTIP: tag_window_flag_tooltips[15]},
    {NAME: "auto_resize_height", TOOLTIP: tag_window_flag_tooltips[16]},

    DEFAULT=sum([1<<i for i in (0, 2, 4, 5)])
    )

block_print_flags = Bool32("block_print",
    "show_index",
    "show_name",
    "show_value",
    "show_type",
    "show_size",
    "show_offset",
    "show_parent_id",
    "show_node_id",
    "show_node_cls",
    "show_endian",
    "show_flags",
    "show_trueonly",
    "show_steptrees",
    "show_filepath",
    "show_unique",
    "show_binsize",
    "show_ramsize",

    ("show_all", 1<<31),
    DEFAULT=sum([1<<i for i in (
        0, 1, 2, 3, 4, 5, 10, 11, 12, 13, 15, 16)]),
    GUI_NAME="tag printout flags",
    TOOLTIP="Flags governing what is shown when a tag is printed."
    )

app_window = Struct("app_window",
    main_window_flags,
    UInt16("recent_tag_max", DEFAULT=20,
        TOOLTIP="Max number of files in the 'recent' menu."),
    UInt16("backup_count", DEFAULT=1, MIN=1, MAX=1, VISIBLE=False,
        TOOLTIP="Max number of backups to make before overwriting the oldest"),

    Pad(32 - 4*1 - 2*2),

    UInt16("app_width", DEFAULT=640, TOOLTIP=app_window_tooltips[0], VISIBLE=False),
    UInt16("app_height", DEFAULT=480, TOOLTIP=app_window_tooltips[1], VISIBLE=False),
    SInt16("app_offset_x", TOOLTIP=app_window_tooltips[2], VISIBLE=False),
    SInt16("app_offset_y", TOOLTIP=app_window_tooltips[3], VISIBLE=False),

    UInt16("window_menu_max_len", DEFAULT=15,
        TOOLTIP=app_window_tooltips[4],
        GUI_NAME="max items in tag window menu"),

    QStruct("max_step",
        UInt8("x", DEFAULT=4, TOOLTIP=app_window_tooltips[5]),
        UInt8("y", DEFAULT=8, TOOLTIP=app_window_tooltips[6]),
        ORIENT="h"
        ),

    UInt16("cascade_stride", DEFAULT=60, TOOLTIP=app_window_tooltips[7]),
    QStruct("tile_stride",
        UInt16("x", DEFAULT=120, TOOLTIP=app_window_tooltips[8]),
        UInt16("y", DEFAULT=30, TOOLTIP=app_window_tooltips[9]),
        ORIENT="h"
        ),
    SIZE=64,
    GUI_NAME='Main window settings'
    )

tag_windows = Struct("tag_windows",
    file_handling_flags,
    tag_window_flags,
    field_widget_flags,

    UInt16("max_undos", DEFAULT=1000,
        TOOLTIP="Max number of undo/redo operations per tag window."),

    Pad(32 - 4*3 - 2*1),

    QStruct("default_window_dimensions",
        UInt16("w", DEFAULT=480, TOOLTIP=app_window_tooltips[10]),
        UInt16("h", DEFAULT=640, TOOLTIP=app_window_tooltips[11]),
        ORIENT="h"
        ),

    QStruct("scroll_increment",
        UInt16("x", DEFAULT=50, TOOLTIP=app_window_tooltips[12]),
        UInt16("y", DEFAULT=50, TOOLTIP=app_window_tooltips[13]),
        ORIENT="h"
        ),

    SIZE=64,
    GUI_NAME='Tag window settings'
    )

tag_printing = Struct("tag_printing",
    block_print_flags,

    UInt16("print_precision", DEFAULT=8, TOOLTIP="unused", VISIBLE=False),
    UInt16("print_indent", DEFAULT=NODE_PRINT_INDENT, VISIBLE=False,
        TOOLTIP="Number of spaces to indent each print level."),

    SIZE=16, VISIBLE=False,
    GUI_NAME='Tag printing settings'
    )

array_counts = Struct("array_counts",
    UInt32("open_tag_count", VISIBLE=False),
    UInt32("recent_tag_count", VISIBLE=False),
    UInt32("directory_path_count", VISIBLE=False),
    UInt32("depth_count", VISIBLE=False),
    UInt32("color_count", VISIBLE=False),
    UInt32("hotkey_count", VISIBLE=False),
    UInt32("tag_window_hotkey_count", VISIBLE=False),
    UInt32("font_count", VISIBLE=False),
    SIZE=128, VISIBLE=False,
    COMMENT="You really shouldnt be messing with these."
    )

open_tags = Array("open_tags",
    SUB_STRUCT=open_tag, SIZE="array_counts.open_tag_count", VISIBLE=False
    )

recent_tags = Array("recent_tags",
    SUB_STRUCT=filepath, SIZE="array_counts.recent_tag_count", VISIBLE=False
    )

directory_paths = Array("directory_paths",
    SUB_STRUCT=filepath, SIZE="array_counts.directory_path_count",
    NAME_MAP=("last_load_dir", "last_defs_dir", "last_imp_dir", "curr_dir",
              "tags_dir", "debug_log_path", "styles_dir",),
    VISIBLE=False
    )

hotkeys = Array("hotkeys",
    SUB_STRUCT=hotkey, DYN_NAME_PATH='.method.enum_name',
    SIZE="array_counts.hotkey_count", WIDGET=DynamicArrayFrame,
    GUI_NAME="Main window hotkeys"
    )

tag_window_hotkeys = Array(
    "tag_window_hotkeys", SUB_STRUCT=hotkey, DYN_NAME_PATH='.method.enum_name',
    SIZE="array_counts.tag_window_hotkey_count", WIDGET=DynamicArrayFrame,
    GUI_NAME="Tag window hotkeys"
    )

version_info = Struct("version_info",
    UEnum32("id", ('Bnla', 'alnB'), VISIBLE=False, DEFAULT='alnB'),
    UInt32("version", DEFAULT=2, VISIBLE=False, EDITABLE=False),
    Timestamp32("date_created", EDITABLE=False),
    Timestamp32("date_modified", EDITABLE=False),
    SIZE=16, VISIBLE=False
    )

all_hotkeys = Container("all_hotkeys",
    hotkeys,
    tag_window_hotkeys,
    GUI_NAME="Hotkeys"
    )

config_def = TagDef("binilla_config",
    version_info,  # not visible
    array_counts,  # not visible
    app_window,
    tag_windows,
    tag_printing,
    open_tags, # not visible
    recent_tags,  # not visible
    directory_paths,  # not visible
    appearance,
    all_hotkeys,
    ENDIAN='<', ext=".cfg",
    )

config_version_def = TagDef(version_info)

def get():
    return config_def
