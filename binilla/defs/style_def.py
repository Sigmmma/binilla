from tkinter import ttk
import tkinter.font

from supyr_struct.defs.tag_def import TagDef
from supyr_struct.field_types import *
from binilla.widgets.field_widgets.color_picker_frame import ColorPickerFrame
from binilla.widgets.field_widgets.array_frame import DynamicArrayFrame
from binilla.constants import GUI_NAME, NAME, TOOLTIP, VALUE, NODE_PRINT_INDENT
from binilla.editor_constants import widget_depth_names, color_names,\
     font_names


__all__ = (
    "font_families", "theme_names", "get", "style_def",
    )

font_families = ()
theme_names = ()
try:
    font_families = tuple(sorted(tkinter.font.families()))
    theme_names = tuple(sorted(ttk.Style().theme_names()))
except Exception:
    print("Cannot import list of font families or theme names. Create Tkinter "
          "interpreter instance before attempting to import config.")


pad_str = "Padding applied to the %s of widgets oriented %sally"

widget_tooltips = (
    "Number of characters wide the title of each vertically oriented field is.",
    ("Default number of characters wide an enumerator widget will be when\n" +
     "not being used to represent an enumerator(such as in an array or union)"),
    "Default number of characters wide an enumerator widget will be.",
    "Minimum number of characters wide an entry field must be.",

    "Width of multi-line text boxes",
    "Height of multi-line text boxes",

    "Minimum number of pixels wide a boolean frame must be.",
    "Minimum number of pixels tall a boolean frame must be.",
    "Maximum number of pixels wide a boolean frame can be.",
    "Maximum number of pixels tall a boolean frame can be.",

    "Default number of characters wide an integer entry field will be.",
    "Default number of characters wide a float entry field will be.",
    "Default number of characters wide a string entry field will be.",

    "Maximum number of characters wide an integer entry field can be.",
    "Maximum number of characters wide a float entry field can be.",
    "Maximum number of characters wide a string entry field can be.",

    ("Maximum number of characters wide an enumerator widget can be.\n" +
     "(This is regardless of what the enumerator widget is being used for)"),
    ("Maximum number of characters tall an enumerator widget can be.\n" +
     "(This is regardless of what the enumerator widget is being used for)"),
    )

depth_tooltip = "\
Number of pixels to surround the widget with to give an appearance of depth."

color = QStruct("color",
    UInt8('r'), UInt8('g'), UInt8('b'),
    ORIENT='h', WIDGET=ColorPickerFrame
    )

font = Struct("font",
    UInt16("size"),
    Bool16("flags",
        "bold",
        "italic",
        "underline",
        "overstrike",
        ),
    Pad(12),
    StrUtf8Enum("family",
        *({NAME:"_%s_%s" % (i, font_families[i]),
           GUI_NAME: font_families[i], VALUE: font_families[i]}
          for i in range(len(font_families))),
        SIZE=240
        ),
    )

theme_name = StrUtf8Enum("theme_name",
    *({NAME:"_%s" % theme_names[i],
       GUI_NAME: theme_names[i], VALUE: theme_names[i]}
      for i in range(len(theme_names))),
    SIZE=64
    )

style_header = Struct("header",
    Timestamp32("date_created"),
    Timestamp32("date_modified"),
    SIZE=120
    )

v1_array_counts = Struct("array_counts",
    UInt32("open_tag_count", VISIBLE=False),
    UInt32("recent_tag_count", VISIBLE=False),
    UInt32("directory_path_count", VISIBLE=False),
    UInt32("widget_depth_count", VISIBLE=False),
    UInt32("color_count", VISIBLE=False),
    UInt32("hotkey_count", VISIBLE=False),
    UInt32("tag_window_hotkey_count", VISIBLE=False),
    UInt32("font_count", VISIBLE=False),
    SIZE=128, VISIBLE=False,
    COMMENT="You really shouldnt be messing with these."
    )

array_counts = Struct("array_counts",
    UInt32("widget_depth_count", VISIBLE=False),
    UInt32("color_count", VISIBLE=False),
    UInt32("font_count", VISIBLE=False),
    SIZE=128, VISIBLE=False,
    COMMENT="You really shouldnt be messing with these."
    )

widgets = Container("widgets",
    UInt16("title_width", TOOLTIP=widget_tooltips[0]),
    UInt16("scroll_menu_width", TOOLTIP=widget_tooltips[1]),
    UInt16("enum_menu_width", TOOLTIP=widget_tooltips[2]),
    UInt16("min_entry_width", TOOLTIP=widget_tooltips[3]),

    UInt16("textbox_width", TOOLTIP=widget_tooltips[4]),
    UInt16("textbox_height", TOOLTIP=widget_tooltips[5]),

    UInt16("bool_frame_min_width", TOOLTIP=widget_tooltips[6]),
    UInt16("bool_frame_min_height", TOOLTIP=widget_tooltips[7]),
    UInt16("bool_frame_max_width", TOOLTIP=widget_tooltips[8]),
    UInt16("bool_frame_max_height", TOOLTIP=widget_tooltips[9]),

    UInt16("def_int_entry_width", TOOLTIP=widget_tooltips[10]),
    UInt16("def_float_entry_width", TOOLTIP=widget_tooltips[11]),
    UInt16("def_string_entry_width", TOOLTIP=widget_tooltips[12]),

    UInt16("max_int_entry_width", TOOLTIP=widget_tooltips[13]),
    UInt16("max_float_entry_width", TOOLTIP=widget_tooltips[14]),
    UInt16("max_string_entry_width", TOOLTIP=widget_tooltips[15]),

    UInt16("scroll_menu_max_width", TOOLTIP=widget_tooltips[16]),
    UInt16("scroll_menu_max_height", TOOLTIP=widget_tooltips[17]),

    # UPDATE THIS PADDING WHEN ADDING STUFF ABOVE IT
    Pad(64 - 2*18),

    QStruct("vertical_padx",
        UInt16("l", TOOLTIP=pad_str % ('left', 'vertic')),
        UInt16("r", TOOLTIP=pad_str % ('right', 'vertic')),
        ORIENT='h', TOOLTIP=pad_str % ('left/right', 'vertic')
        ),
    QStruct("vertical_pady",
        UInt16("t", TOOLTIP=pad_str % ('top', 'vertic')),
        UInt16("b", TOOLTIP=pad_str % ('bottom', 'vertic')),
        ORIENT='h', TOOLTIP=pad_str % ('top/bottom', 'vertic')
        ),
    QStruct("horizontal_padx",
        UInt16("l", TOOLTIP=pad_str % ('left', 'horizont')),
        UInt16("r", TOOLTIP=pad_str % ('right', 'horizont')),
        ORIENT='h', TOOLTIP=pad_str % ('left/right', 'horizont')
        ),
    QStruct("horizontal_pady",
        UInt16("t", TOOLTIP=pad_str % ('top', 'horizont')),
        UInt16("b", TOOLTIP=pad_str % ('bottom', 'horizont')),
        ORIENT='h', TOOLTIP=pad_str % ('top/bottom', 'horizont')
        ),

    # UPDATE THIS PADDING WHEN ADDING STUFF ABOVE IT
    Pad(64 - 2*2*4),

    Array("depths",
        SUB_STRUCT=UInt16("depth", TOOLTIP=depth_tooltip),
        SIZE="array_counts.widget_depth_count",
        MAX=len(widget_depth_names), MIN=len(widget_depth_names),
        NAME_MAP=widget_depth_names,
        GUI_NAME="Widget depths"
        ),
    GUI_NAME='Field widget settings'
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

style_version = Struct("style_version",
    UEnum32("id", ('Styl', 'lytS'), VISIBLE=False, DEFAULT='lytS'),
    UInt32("version", DEFAULT=2, VISIBLE=False),
    SIZE=8
    )

appearance = Container("appearance",
    theme_name,
    widgets,
    colors,
    fonts,
    GUI_NAME="Appearance"
    )

style_def = TagDef("binilla_style",
    style_version,
    style_header,
    array_counts,
    appearance,
    ENDIAN='<', ext=".sty",
    )

style_version_def = TagDef(style_version)


# OLD STRUCT VERSIONS
v1_style_version = Struct("style_version",
    UInt32("id", DEFAULT='lytS', VISIBLE=False),
    UInt32("version", DEFAULT=1, VISIBLE=False),
    SIZE=8
    )

v1_style_def = TagDef("v1_binilla_style",
    v1_style_version,
    style_header,
    v1_array_counts,
    widgets,
    colors,
    ENDIAN='<', ext=".sty",
    )


def get():
    return style_def
