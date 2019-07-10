from supyr_struct.defs.tag_def import TagDef
from supyr_struct.field_types import *

from binilla.defs.v1_style_def import v1_widths_and_heights, v1_colors
from binilla.defs.config_def import open_tags, recent_tags, directory_paths,\
     padding, depths, hotkeys, tag_window_hotkeys,\
     handler_flags, tag_window_flags, block_print_flags, general_flags

__all__ = (
    "get", "v1_config_def",
    )


v1_version_info = Struct("version_info",
    UEnum32("id", ('Bnla', 'alnB'), DEFAULT='alnB'),
    UInt32("version", DEFAULT=1),
    SIZE=8
    )

v1_general = Struct("general",
    general_flags,
    handler_flags,
    tag_window_flags,
    block_print_flags,
    Timestamp32("date_created"),
    Timestamp32("date_modified"),
    UInt16("recent_tag_max"),
    UInt16("max_undos"),
    UInt16("print_precision"),
    UInt16("print_indent"),
    UInt16("backup_count"),
    SIZE=120,
    )

v1_array_counts = Struct("array_counts",
    UInt32("open_tag_count"),
    UInt32("recent_tag_count"),
    UInt32("directory_path_count"),
    UInt32("depth_count"),
    UInt32("color_count"),
    UInt32("hotkey_count"),
    UInt32("tag_window_hotkey_count"),
    SIZE=128,
    )

v1_app_window = Struct("app_window",
    UInt16("app_width"), UInt16("app_height"),
    SInt16("app_offset_x"), SInt16("app_offset_y"),

    UInt16("window_menu_max_len"),
    QStruct("max_step", UInt8("x"), UInt8("y")),

    UInt16("tag_window_cascade_stride"),
    QStruct("tag_window_tiling_stride", UInt16("x"), UInt16("y")),
    QStruct("tag_window_default_dimensions", UInt16("w"), UInt16("h")),
    QStruct("tag_window_scroll_increment", UInt16("x"), UInt16("y")),
    SIZE=128,
    )

v1_config_def = TagDef("v1_binilla_config",
    v1_version_info,
    v1_general,
    v1_array_counts,
    v1_app_window,
    v1_widths_and_heights,
    padding,
    depths,
    open_tags,
    recent_tags,
    directory_paths,
    v1_colors,
    hotkeys,
    tag_window_hotkeys,
    ENDIAN='<', ext=".cfg",
    )

def get():
    return v1_config_def
