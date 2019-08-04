from tkinter import ttk
import tkinter.font

from supyr_struct.defs.tag_def import TagDef
from supyr_struct.field_types import *

from binilla.constants import NAME, VALUE, GUI_NAME, VISIBILITY_METADATA
from binilla.defs import style_tooltips as ttip
from binilla.widgets.field_widgets.color_picker_frame import ColorPickerFrame
from binilla.editor_constants import widget_depth_names, color_names, font_names


__all__ = (
    "font_families", "theme_names", "get", "style_def",
    )

font_families = ()
theme_names = ()
try:
    font_families = tuple(sorted(tkinter.font.families()))
    theme_names = tuple(sorted(ttk.Style().theme_names()))
    # classic just looks like total ass for the buttons
    theme_names = tuple(n for n in theme_names if n != "classic")
except Exception:
    print("Cannot import list of font families or theme names. Create Tkinter "
          "interpreter instance before attempting to import config.")


color = QStruct("color",
    UInt8('r'), UInt8('g'), UInt8('b'),
    ORIENT='h', WIDGET=ColorPickerFrame, TOOLTIP=ttip.color
    )

font = Struct("font",
    UInt16("size", TOOLTIP=ttip.font_size),
    Bool16("flags",
        "bold",
        "italic",
        "underline",
        "overstrike",
        TOOLTIP=ttip.font_flags
        ),
    Pad(4),
    StrUtf8Enum("family",
        *({NAME:"_%s_%s" % (i, font_families[i]),
           GUI_NAME: font_families[i], VALUE: font_families[i]}
          for i in range(len(font_families))),
        SIZE=120, TOOLTIP=ttip.font_family
        ),
    )

theme_name = StrUtf8Enum("theme_name",
    *({NAME:"_%s" % theme_names[i],
       GUI_NAME: theme_names[i], VALUE: theme_names[i]}
      for i in range(len(theme_names))),
    SIZE=64, TOOLTIP=ttip.appearance_theme
    )

array_counts = Struct("array_counts",
    UInt32("depth_count", EDITABLE=False),
    UInt32("color_count", EDITABLE=False),
    UInt32("font_count", EDITABLE=False),
    SIZE=128, VISIBLE=VISIBILITY_METADATA, EDITABLE=False,
    COMMENT="Messing with these can damage your style file."
    )

widths_and_heights = Struct("widths_and_heights",
    UInt16("title_width", TOOLTIP=ttip.title_width),
    UInt16("scroll_menu_width", TOOLTIP=ttip.scroll_menu_width,
        GUI_NAME="default scroll menu width"),
    UInt16("enum_menu_width", TOOLTIP=ttip.enum_menu_width,
        GUI_NAME="default enum menu width"),
    UInt16("min_entry_width", TOOLTIP=ttip.min_entry_width,
        GUI_NAME="entry min width"),

    Struct("textbox",
        UInt16("max_width",  TOOLTIP=ttip.textbox_max_width),
        UInt16("max_height", TOOLTIP=ttip.textbox_max_height),
        ORIENT="h", TOOLTIP=ttip.textbox_max_width_height
        ),
    Struct("scroll_menu",
        UInt16("max_width",  TOOLTIP=ttip.scroll_menu_max_width),
        UInt16("max_height", TOOLTIP=ttip.scroll_menu_max_height),
        ORIENT="h", TOOLTIP=ttip.scroll_menu_width_height
        ),

    Struct("bool_frame_width",
        UInt16("min", TOOLTIP=ttip.bool_frame_min_width),
        UInt16("max", TOOLTIP=ttip.bool_frame_max_width),
        ORIENT="h", TOOLTIP=ttip.bool_frame_width
        ),
    Struct("bool_frame_height",
        UInt16("min", TOOLTIP=ttip.bool_frame_min_height),
        UInt16("max", TOOLTIP=ttip.bool_frame_max_height),
        ORIENT="h", TOOLTIP=ttip.bool_frame_height
        ),

    Struct("default_entry_widths",
        UInt16("integer", TOOLTIP=ttip.default_integer_entry_width),
        UInt16("float",   TOOLTIP=ttip.default_float_entry_width),
        UInt16("string",  TOOLTIP=ttip.default_string_entry_width),
        ORIENT="h", TOOLTIP=ttip.default_entry_widths
        ),
    Struct("max_entry_widths",
        UInt16("integer", TOOLTIP=ttip.max_integer_entry_width),
        UInt16("float",   TOOLTIP=ttip.max_float_entry_width),
        UInt16("string",  TOOLTIP=ttip.max_string_entry_width),
        ORIENT="h", TOOLTIP=ttip.max_entry_widths
        ),

    SIZE=64, GUI_NAME="Widths / heights"
    )

padding = Struct("padding",
    QStruct("vertical_padx",
        UInt16("l", TOOLTIP=ttip.vertical_padx_l),
        UInt16("r", TOOLTIP=ttip.vertical_padx_r),
        ORIENT='h', TOOLTIP=ttip.vertical_padx
        ),
    QStruct("vertical_pady",
        UInt16("t", TOOLTIP=ttip.vertical_pady_l),
        UInt16("b", TOOLTIP=ttip.vertical_pady_r),
        ORIENT='h', TOOLTIP=ttip.vertical_pady
        ),
    QStruct("horizontal_padx",
        UInt16("l", TOOLTIP=ttip.horizontal_padx_l),
        UInt16("r", TOOLTIP=ttip.horizontal_padx_r),
        ORIENT='h', TOOLTIP=ttip.horizontal_padx
        ),
    QStruct("horizontal_pady",
        UInt16("t", TOOLTIP=ttip.horizontal_pady_l),
        UInt16("b", TOOLTIP=ttip.horizontal_pady_r),
        ORIENT='h', TOOLTIP=ttip.horizontal_pady
        ),
    GUI_NAME='Padding', SIZE=64
    )

depths = Array("depths",
    SUB_STRUCT=UInt16("depth", TOOLTIP=ttip.widget_depth),
    SIZE="array_counts.depth_count",
    MAX=len(widget_depth_names), MIN=len(widget_depth_names),
    NAME_MAP=widget_depth_names,
    GUI_NAME="Depths"
    )

colors = Array("colors",
    SUB_STRUCT=color, SIZE="array_counts.color_count",
    MAX=len(color_names), MIN=len(color_names),
    NAME_MAP=color_names,
    GUI_NAME="Colors"
    )

fonts = Array("fonts",
    SUB_STRUCT=font, SIZE="array_counts.font_count",
    MAX=len(font_names), MIN=len(font_names),
    NAME_MAP=font_names,
    GUI_NAME="Fonts"
    )

version_info = Struct("version_info",
    UEnum32("id", ('Styl', 'lytS'), VISIBLE=VISIBILITY_METADATA, DEFAULT='lytS'),
    UInt32("version", DEFAULT=2, VISIBLE=VISIBILITY_METADATA),
    Timestamp32("date_created"),
    Timestamp32("date_modified"),
    SIZE=16
    )

appearance = Container("appearance",
    theme_name,
    widths_and_heights,
    padding,
    depths,
    colors,
    fonts,
    GUI_NAME="Appearance", COMMENT=(
        "\nThese settings control how everything looks. Colors, fonts, etc."
        "\nThese settings are what get saved to/loaded from style files.\n")
    )

style_def = TagDef("binilla_style",
    version_info,
    array_counts,
    appearance,
    ENDIAN='<', ext=".sty",
    )

style_version_def = TagDef(version_info)


def get():
    return style_def
