import platform

IS_WIN = "windows" in platform.system().lower()
IS_MAC = "darwin" in platform.system().lower()
IS_LNX = "linux" in platform.system().lower()


# padding to use when packing a widget being oriented vertically
VERTICAL_PADX = (20, 0)
VERTICAL_PADY = (0, 5)

# padding to use when packing a widget being oriented horizontally
HORIZONTAL_PADX = (0, 10)
HORIZONTAL_PADY = (0, 5)

# The default text width of the title label for widgets
TITLE_WIDTH = 35
# The default number of text units wide a ScrollMenu is
SCROLL_MENU_WIDTH = 35
ENUM_MENU_WIDTH = 10

TEXTBOX_HEIGHT = 10
TEXTBOX_WIDTH = 80

# The number of pixels wide and tall a BoolFrame is at a minimum
BOOL_FRAME_MIN_WIDTH = 160
BOOL_FRAME_MIN_HEIGHT = 17
# The number of pixels wide and tall a BoolFrame is at a maximum
BOOL_FRAME_MAX_WIDTH = 300
BOOL_FRAME_MAX_HEIGHT = 255

# Widths of different types of data that an EntryFrame can be used for
MIN_ENTRY_WIDTH = 4

DEF_INT_ENTRY_WIDTH = 8
DEF_FLOAT_ENTRY_WIDTH = 10
DEF_STRING_ENTRY_WIDTH = 35

MAX_INT_ENTRY_WIDTH = 20
MAX_FLOAT_ENTRY_WIDTH = 20
MAX_STRING_ENTRY_WIDTH = 35

SCROLL_MENU_MAX_WIDTH = 35
SCROLL_MENU_MAX_HEIGHT = 15

# default colors for the widgets
IO_FG_COLOR = '#%02x%02x%02x' % (200, 200, 200)  # very light grey
IO_BG_COLOR = '#%02x%02x%02x' % (50, 50, 50)  # dark grey
INVALID_PATH_COLOR = '#%02x%02x%02x' % (255, 0, 0)  # red
TOOLTIP_BG_COLOR = '#%02x%02x%02x' % (255, 255, 224)
WHITE = '#%02x%02x%02x' % (255, 255, 255)
BLACK = '#%02x%02x%02x' % (0, 0, 0)

# ORIGINAL GUERILLA SETTINGS
'''
# default depths for each of the different widget types
COMMENT_DEPTH = 1
LISTBOX_DEPTH = ENTRY_DEPTH = BUTTON_DEPTH = 2
FRAME_DEPTH = 3

DEFAULT_BG_COLOR = '#%02x%02x%02x' % (236, 233, 216)  # light tan
COMMENT_BG_COLOR = '#%02x%02x%02x' % (241, 239, 226)  # lighter tan
FRAME_BG_COLOR = '#%02x%02x%02x' % (172, 168, 153)  # muddy tan
'''

# default depths for each of the different widget types
COMMENT_DEPTH = 1
LISTBOX_DEPTH = ENTRY_DEPTH = BUTTON_DEPTH = 1
FRAME_DEPTH = 1


DEFAULT_BG_COLOR = '#%02x%02x%02x' % (240, 240, 240)
COMMENT_BG_COLOR = '#%02x%02x%02x' % (200, 200, 200)
FRAME_BG_COLOR = '#%02x%02x%02x' % (160, 160, 160)
BUTTON_COLOR = DEFAULT_BG_COLOR
BITMAP_CANVAS_BG_COLOR = '#%02x%02x%02x' % (0, 0, 255)
BITMAP_CANVAS_OUTLINE_COLOR = '#%02x%02x%02x' % (0, 255, 0)

TEXT_NORMAL_COLOR = BLACK
TEXT_DISABLED_COLOR = FRAME_BG_COLOR
TEXT_HIGHLIGHTED_COLOR = WHITE

ENTRY_NORMAL_COLOR = WHITE
ENTRY_DISABLED_COLOR = DEFAULT_BG_COLOR
ENTRY_HIGHLIGHTED_COLOR = '#%02x%02x%02x' % (55, 110, 210)  # pale lightish blue

ENUM_NORMAL_COLOR = ENTRY_NORMAL_COLOR
ENUM_DISABLED_COLOR = ENTRY_DISABLED_COLOR
ENUM_HIGHLIGHTED_COLOR = ENTRY_HIGHLIGHTED_COLOR

# Fonts
if IS_WIN:
    DEFAULT_FONT_FAMILY = "Segoe UI"
    DEFAULT_FONT_SIZE   = 9
    FIXED_FONT_FAMILY = "Courier"
    FIXED_FONT_SIZE   = 10
    HEADING_FONT_FAMILY = 'Courier'
    HEADING_FONT_SIZE   = 24
else:
    DEFAULT_FONT_FAMILY = "Bitstream Charter"
    DEFAULT_FONT_SIZE   = 9
    FIXED_FONT_FAMILY = "Bitstream Vera Sans Mono"
    FIXED_FONT_SIZE   = 8
    HEADING_FONT_FAMILY = 'Bitstream Vera Sans Mono'
    HEADING_FONT_SIZE   = 24

DEFAULT_FONT_WEIGHT = "normal"
DEFAULT_FONT_SLANT  = "roman"
FIXED_FONT_WEIGHT = DEFAULT_FONT_WEIGHT
FIXED_FONT_SLANT  = "roman"

HEADING_FONT_WEIGHT = "bold"
HEADING_FONT_SLANT = "italic"
CONTAINER_TITLE_FONT_FAMILY = FIXED_FONT_FAMILY
CONTAINER_TITLE_FONT_SIZE   = FIXED_FONT_SIZE + 2
CONTAINER_TITLE_FONT_WEIGHT = "bold"
CONTAINER_TITLE_FONT_SLANT  = "roman"
COMMENT_FONT_FAMILY = FIXED_FONT_FAMILY
COMMENT_FONT_SIZE   = FIXED_FONT_SIZE + 1
COMMENT_FONT_WEIGHT = DEFAULT_FONT_WEIGHT
COMMENT_FONT_SLANT  = "roman"


# A list of the kwargs used by FrameWidget classes. This list
# exists to prune these items from kwargs as they are passed
# to the actual tkinter class that they are subclassing.
WIDGET_KWARGS = [
    'parent', 'desc', 'node', 'attr_index', 'app_root', 'f_widget_parent',
    'vert_oriented', 'show_frame', 'show_title', 'disabled',
    'pack_padx', 'pack_pady', 'tag_window', 'dont_padx_fields',
    'use_parent_pack_padx', 'use_parent_pack_pady'
    ]

RAW_BYTES = '<RAW BYTES>'
ACTIVE_ENUM_NAME = '<ACTIVE>'
UNNAMED_FIELD = '<UNNAMED>'
INVALID_OPTION = '<INVALID>'
UNKNOWN_BOOLEAN = 'unknown %s'


widget_depth_names = (
    "frame", "button", "entry", "listbox", "comment"
    )

color_names = (
    "io_fg", "io_bg",
    "default_bg", "comment_bg", "frame_bg", "button",
    "text_normal", "text_disabled", "text_highlighted",
    "enum_normal", "enum_disabled", "enum_highlighted",
    "entry_normal", "entry_disabled", "entry_highlighted",
    "invalid_path", "tooltip_bg",
    "bitmap_canvas_bg", "bitmap_canvas_outline"
    )

font_names = (
    "default", "fixed", "fixed_small", "heading", "frame_title",
    "treeview", "console", "comment", "tooltip"
    )
