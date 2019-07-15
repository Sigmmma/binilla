from tkinter import ttk
import tkinter.font

from supyr_struct.defs.tag_def import TagDef
from supyr_struct.field_types import *
from binilla.editor_constants import v1_color_names
from binilla.defs.style_def import padding, depths, color


__all__ = (
    "get", "v1_style_def",
    )


v1_version_info = Struct("version_info",
    UInt32("id", DEFAULT='lytS'),
    UInt32("version"),
    Timestamp32("date_created"),
    Timestamp32("date_modified"),
    SIZE=16
    )

v1_array_counts = Struct("array_counts",
    Pad(12),
    UInt32("depth_count"),
    UInt32("color_count"),
    SIZE=128
    )

v1_widths_and_heights = Struct("widths_and_heights",
    UInt16("title_width"),
    UInt16("scroll_menu_width"),
    UInt16("enum_menu_width"),
    UInt16("min_entry_width"),
    Struct("textbox",
        UInt16("max_width"), UInt16("max_height")),
    Struct("bool_frame_min",
        UInt16("width"), UInt16("height")),
    Struct("bool_frame_max",
        UInt16("width"), UInt16("height")),
    Struct("default_entry_widths",
        UInt16("integer"), UInt16("float"), UInt16("string")),
    Struct("max_entry_widths",
        UInt16("integer"), UInt16("float"), UInt16("string")),
    Struct("scroll_menu",
        UInt16("max_width"), UInt16("max_height")),
    SIZE=64,
    )

v1_colors = Array("colors",
    SUB_STRUCT=color, SIZE="array_counts.color_count",
    NAME_MAP=v1_color_names,
    )

v1_style_def = TagDef("v1_binilla_style",
    v1_version_info,
    Pad(112),
    v1_array_counts,
    v1_widths_and_heights,
    padding,
    depths,
    v1_colors,
    ENDIAN='<', ext=".sty",
    )


def get():
    return v1_style_def
