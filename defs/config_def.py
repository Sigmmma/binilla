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
from binilla.defs import config_tooltips as ttip


__all__ = (
    "get", "config_def",
    )

hotkey = Struct("hotkey",
    BitStruct("combo",
        UBitEnum("modifier", *modifier_enums,
            GUI_NAME="", SIZE=4, TOOLTIP=ttip.hotkey_combo),
        UBitEnum("key", GUI_NAME="and", *hotkey_enums, SIZE=28),
        SIZE=4, ORIENT='h'
        ),
    UEnum32("method", *method_enums, TOOLTIP=ttip.hotkey_method)
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
    {NAME: "load_last_workspace", TOOLTIP: ttip.main_window_load_last_workspace},
    {NAME: "log_output",    TOOLTIP: ttip.main_window_log_output},
    {NAME: "log_tag_print", TOOLTIP: ttip.main_window_log_tag_print},
    {NAME: "debug_mode",    TOOLTIP: ttip.main_window_debug_mode},
    {NAME: "disable_io_redirect", TOOLTIP: ttip.main_window_disable_io_redirect},
       
    DEFAULT=sum([1<<i for i in (1, 2)])
    )

file_handling_flags = Bool32("file_handling_flags",
    {NAME: "backup_tags",   TOOLTIP: ttip.file_handling_backup},
    {NAME: "write_as_temp", TOOLTIP: ttip.file_handling_write_as_temp},
    {NAME: "allow_corrupt", TOOLTIP: ttip.file_handling_allow_corrupt},
    {NAME: "integrity_test", TOOLTIP: ttip.file_handling_integrity_test},
    DEFAULT=sum([1<<i for i in (0, 3)])
    )

field_widget_flags = Bool32("widget_flags",
    {NAME: "edit_uneditable", TOOLTIP: ttip.field_widget_edit_uneditable},
    {NAME: "show_invisible",  TOOLTIP: ttip.field_widget_show_invisible},
    #"row_row_fight_powuh",
    {NAME: "show_comments",  TOOLTIP: ttip.field_widget_show_comments},
    {NAME: "show_tooltips",  TOOLTIP: ttip.field_widget_show_tooltips},
    {NAME: "show_sidetips",  TOOLTIP: ttip.field_widget_show_sidetips},
    {NAME: "show_all_bools", TOOLTIP: ttip.field_widget_show_all_bools},

    {NAME: "enforce_max", TOOLTIP: ttip.field_widget_enforce_max},
    {NAME: "enforce_min", TOOLTIP: ttip.field_widget_enforce_min},
    {NAME: "use_unit_scales", TOOLTIP: ttip.field_widget_use_unit_scales},
    {NAME: "use_gui_names",   TOOLTIP: ttip.field_widget_use_gui_names},

    {NAME: "blocks_start_hidden", TOOLTIP: ttip.field_widget_blocks_start_hidden},
    {NAME: "empty_blocks_start_hidden", TOOLTIP: ttip.field_widget_empty_blocks_start_hidden},

    {NAME: "scroll_unselected", TOOLTIP: ttip.field_widget_scroll_unselected}, # RENAMED
    {NAME: "evaluate_entry_fields", TOOLTIP: ttip.field_widget_evaluate_entry_fields},
    DEFAULT=sum([1<<i for i in (2, 3, 4, 6, 7, 8, 9, 10)])
    )

tag_window_flags = Bool32("window_flags",
    {NAME: "sync_window_movement",   TOOLTIP: ttip.tag_window_sync_window_movement, VISIBLE: False},
    {NAME: "use_default_dimensions", TOOLTIP: ttip.tag_window_use_default_dimensions},
    {NAME: "cap_window_size",    TOOLTIP: ttip.tag_window_cap_window_size},
    {NAME: "dont_shrink_width",  TOOLTIP: ttip.tag_window_dont_shrink_width},
    {NAME: "dont_shrink_height", TOOLTIP: ttip.tag_window_dont_shrink_height},
    {NAME: "auto_resize_width",  TOOLTIP: ttip.tag_window_auto_resize_width},
    {NAME: "auto_resize_height", TOOLTIP: ttip.tag_window_auto_resize_height},

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
    TOOLTIP=ttip.tag_printing_flags
    )

app_window = Struct("app_window",
    main_window_flags,
    UInt16("recent_tag_max", DEFAULT=20,
        TOOLTIP=ttip.app_window_recent_tag_max),
    UInt16("backup_count", DEFAULT=1, MIN=1, MAX=1, VISIBLE=False,
        TOOLTIP=ttip.app_window_backup_count),

    Pad(32 - 4*1 - 2*2),

    UInt16("app_width", DEFAULT=640, VISIBLE=False),
    UInt16("app_height", DEFAULT=480, VISIBLE=False),
    SInt16("app_offset_x", VISIBLE=False),
    SInt16("app_offset_y", VISIBLE=False),

    UInt16("window_menu_max_len", DEFAULT=15,
        TOOLTIP=ttip.app_window_window_menu_max_len,
        GUI_NAME="max items in tag window menu"),

    QStruct("max_step",
        UInt8("x", DEFAULT=4, TOOLTIP=ttip.app_window_max_step_x),
        UInt8("y", DEFAULT=8, TOOLTIP=ttip.app_window_max_step_y),
        ORIENT="h"
        ),

    UInt16("cascade_stride", DEFAULT=60, TOOLTIP=ttip.app_window_cascade_stride),
    QStruct("tile_stride",
        UInt16("x", DEFAULT=120, TOOLTIP=ttip.app_window_tile_stride_x),
        UInt16("y", DEFAULT=30, TOOLTIP=ttip.app_window_tile_stride_y),
        ORIENT="h"
        ),
    SIZE=64,
    GUI_NAME='Main window settings'
    )

tag_windows = Struct("tag_windows",
    file_handling_flags,
    tag_window_flags,
    field_widget_flags,

    UInt16("max_undos", DEFAULT=1000, TOOLTIP=ttip.tag_window_max_undos),

    Pad(32 - 4*3 - 2*1),

    QStruct("default_window_dimensions",
        UInt16("w", DEFAULT=480, TOOLTIP=ttip.tag_window_default_width),
        UInt16("h", DEFAULT=640, TOOLTIP=ttip.tag_window_default_height),
        ORIENT="h"
        ),

    QStruct("scroll_increment",
        UInt16("x", DEFAULT=50, TOOLTIP=ttip.tag_window_scroll_increment_x),
        UInt16("y", DEFAULT=50, TOOLTIP=ttip.tag_window_scroll_increment_y),
        ORIENT="h"
        ),

    SIZE=64,
    GUI_NAME='Tag window settings'
    )

tag_printing = Struct("tag_printing",
    block_print_flags,

    UInt16("print_precision", DEFAULT=8, TOOLTIP="unused", VISIBLE=False),
    UInt16("print_indent", DEFAULT=NODE_PRINT_INDENT, VISIBLE=False,
        TOOLTIP=ttip.tag_printint_print_indent),

    SIZE=16, VISIBLE=False,
    GUI_NAME='Tag printing settings'
    )

array_counts = Struct("array_counts",
    UInt32("open_tag_count", VISIBLE=False, EDITABLE=False),
    UInt32("recent_tag_count", VISIBLE=False, EDITABLE=False),
    UInt32("directory_path_count", VISIBLE=False, EDITABLE=False),
    UInt32("depth_count", VISIBLE=False, EDITABLE=False),
    UInt32("color_count", VISIBLE=False, EDITABLE=False),
    UInt32("hotkey_count", VISIBLE=False, EDITABLE=False),
    UInt32("tag_window_hotkey_count", VISIBLE=False, EDITABLE=False),
    UInt32("font_count", VISIBLE=False, EDITABLE=False),
    SIZE=128, VISIBLE=False, EDITABLE=False,
    COMMENT="Messing with these can damage your config file."
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
