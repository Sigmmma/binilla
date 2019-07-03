'''
This module contains various widgets which the FieldWidget classes utilize.
'''
from traceback import format_exc

import threadsafe_tkinter as tk
import tkinter.ttk as ttk
import tkinter.font
from binilla import editor_constants as e_c


__all__ = ("FontConfig", "BinillaWidget", )


class FontConfig(dict):
    __slots__ = ()
    def __init__(self, *a, **kw):
        dict.__init__(self, *a, **kw)
        # default these so the dict is properly filled with defaults
        self.setdefault('family', "")
        self.setdefault('size', 12)
        self.setdefault('weight', "normal")
        self.setdefault('slant', "roman")
        self.setdefault('underline', 0)
        self.setdefault('overstrike', 0)

    @property
    def family(self): return str(self.get("family", ""))
    @property
    def size(self): return int(self.get("size", 12))
    @property
    def weight(self): return str(self.get("weight", "normal"))
    @property
    def slant(self): return str(self.get("slant", "roman"))
    @property
    def underline(self): return bool(self.get("underline", 0))
    @property
    def overstrike(self): return bool(self.get("overstrike", 0))


class BinillaWidget():
    '''
    This class exists solely as an easy way to change
    the config properties of the widgets in Binilla.
    '''
    # PADDING
    vertical_padx = e_c.VERTICAL_PADX
    vertical_pady = e_c.VERTICAL_PADY
    horizontal_padx = e_c.HORIZONTAL_PADX
    horizontal_pady = e_c.HORIZONTAL_PADY

    # DEPTHS
    comment_depth = e_c.COMMENT_DEPTH
    listbox_depth = e_c.LISTBOX_DEPTH
    entry_depth = e_c.ENTRY_DEPTH
    button_depth = e_c.BUTTON_DEPTH
    frame_depth = e_c.FRAME_DEPTH

    # COLORS
    default_bg_color = e_c.DEFAULT_BG_COLOR
    comment_bg_color = e_c.COMMENT_BG_COLOR
    frame_bg_color = e_c.FRAME_BG_COLOR
    button_color = e_c.BUTTON_COLOR
    bitmap_canvas_bg_color = e_c.BITMAP_CANVAS_BG_COLOR
    bitmap_canvas_outline_color = e_c.BITMAP_CANVAS_OUTLINE_COLOR

    text_normal_color = e_c.TEXT_NORMAL_COLOR
    text_disabled_color = e_c.TEXT_DISABLED_COLOR
    text_highlighted_color = e_c.TEXT_HIGHLIGHTED_COLOR

    enum_normal_color = e_c.ENUM_NORMAL_COLOR 
    enum_disabled_color = e_c.ENUM_DISABLED_COLOR 
    enum_highlighted_color = e_c.ENUM_HIGHLIGHTED_COLOR

    entry_normal_color = e_c.ENTRY_NORMAL_COLOR 
    entry_disabled_color = e_c.ENTRY_DISABLED_COLOR 
    entry_highlighted_color = e_c.ENTRY_HIGHLIGHTED_COLOR

    io_fg_color = e_c.IO_FG_COLOR
    io_bg_color = e_c.IO_BG_COLOR
    invalid_path_color = e_c.INVALID_PATH_COLOR
    tooltip_bg_color = e_c.TOOLTIP_BG_COLOR

    # FONTS
    _fonts = {}

    font_settings = dict(
        # "default" font is required to be here at the very least
        default=FontConfig(
            family=e_c.DEFAULT_FONT_FAMILY, size=e_c.DEFAULT_FONT_SIZE,
            weight=e_c.DEFAULT_FONT_WEIGHT, slant=e_c.DEFAULT_FONT_SLANT),

        fixed=FontConfig(
            family=e_c.FIXED_FONT_FAMILY, size=e_c.FIXED_FONT_SIZE,
            weight=e_c.FIXED_FONT_WEIGHT, slant=e_c.FIXED_FONT_SLANT),
        fixed_small=FontConfig(
            family=e_c.FIXED_FONT_FAMILY, size=e_c.FIXED_FONT_SIZE - 2,
            weight=e_c.FIXED_FONT_WEIGHT, slant=e_c.FIXED_FONT_SLANT),

        treeview=FontConfig(
            family=e_c.DEFAULT_FONT_FAMILY, size=e_c.DEFAULT_FONT_SIZE,
            weight=e_c.DEFAULT_FONT_WEIGHT, slant=e_c.DEFAULT_FONT_SLANT),

        console=FontConfig(
            family=e_c.FIXED_FONT_FAMILY, size=e_c.FIXED_FONT_SIZE - 2,
            weight=e_c.FIXED_FONT_WEIGHT, slant=e_c.FIXED_FONT_SLANT),

        heading=FontConfig(
            family=e_c.HEADING_FONT_FAMILY, size=e_c.HEADING_FONT_SIZE,
            weight=e_c.HEADING_FONT_WEIGHT, slant=e_c.HEADING_FONT_SLANT),
        frame_title=FontConfig(
            family=e_c.CONTAINER_TITLE_FONT_FAMILY, size=e_c.CONTAINER_TITLE_FONT_SIZE,
            weight=e_c.CONTAINER_TITLE_FONT_WEIGHT, slant=e_c.CONTAINER_TITLE_FONT_SLANT),

        comment=FontConfig(
            family=e_c.COMMENT_FONT_FAMILY, size=e_c.COMMENT_FONT_SIZE,
            weight=e_c.COMMENT_FONT_WEIGHT, slant=e_c.COMMENT_FONT_SLANT),
        tooltip=FontConfig(
            family=e_c.DEFAULT_FONT_FAMILY, size=e_c.DEFAULT_FONT_SIZE,
            weight=e_c.DEFAULT_FONT_WEIGHT, slant=e_c.DEFAULT_FONT_SLANT),
        )

    # MISC
    title_width = e_c.TITLE_WIDTH
    enum_menu_width = e_c.ENUM_MENU_WIDTH
    scroll_menu_width = e_c.SCROLL_MENU_WIDTH
    min_entry_width = e_c.MIN_ENTRY_WIDTH
    textbox_height = e_c.TEXTBOX_HEIGHT
    textbox_width = e_c.TEXTBOX_WIDTH

    bool_frame_min_width = e_c.BOOL_FRAME_MIN_WIDTH
    bool_frame_min_height = e_c.BOOL_FRAME_MIN_HEIGHT
    bool_frame_max_width = e_c.BOOL_FRAME_MAX_WIDTH
    bool_frame_max_height = e_c.BOOL_FRAME_MAX_HEIGHT

    def_int_entry_width = e_c.DEF_INT_ENTRY_WIDTH
    def_float_entry_width = e_c.DEF_FLOAT_ENTRY_WIDTH
    def_string_entry_width = e_c.DEF_STRING_ENTRY_WIDTH

    max_int_entry_width = e_c.MAX_INT_ENTRY_WIDTH
    max_float_entry_width = e_c.MAX_FLOAT_ENTRY_WIDTH
    max_string_entry_width = e_c.MAX_STRING_ENTRY_WIDTH

    scroll_menu_max_width = e_c.SCROLL_MENU_MAX_WIDTH
    scroll_menu_max_height = e_c.SCROLL_MENU_MAX_HEIGHT

    can_scroll = False
    tooltip_string = None
    f_widget_parent = None
    disabled = False

    font_type = "default"  # the type of font to use

    read_traces = ()
    write_traces = ()
    undefine_traces = ()

    _filedialog_style_fix = None

    def __init__(self, *args, **kwargs):
        self.read_traces = {}
        self.write_traces = {}
        self.undefine_traces = {}
        self.fix_filedialog_style()

    def fix_filedialog_style(self):
        if (BinillaWidget._filedialog_style_fix is not None
            or not hasattr(self, "_root") or e_c.IS_WIN):
            return

        # fix linux using bad colors in the filedialog
        # at times for certain linux distros
        root = self._root()
        root.option_add('*foreground', 'black')

        BinillaWidget._filedialog_style_fix = ttk.Style(root)
        self._filedialog_style_fix.configure('TLabel', foreground='black')
        self._filedialog_style_fix.configure('TEntry', foreground='black')
        self._filedialog_style_fix.configure('TMenubutton', foreground='black')
        self._filedialog_style_fix.configure('TButton', foreground='black')

    def read_trace(self, var, function):
        cb_name = var.trace("r", function)
        self.read_traces[cb_name] = var

    def write_trace(self, var, function):
        cb_name = var.trace("w", function)
        self.write_traces[cb_name] = var

    def undefine_trace(self, var, function):
        cb_name = var.trace("u", function)
        self.undefine_traces[cb_name] = var

    def set_disabled(self, disable=True):
        self.disabled = bool(disable)

    def get_font(self, font_type):
        if font_type not in self.font_settings:
            font_type = "default"

        if font_type not in self._fonts:
            self.reload_fonts((font_type, ))

        return self._fonts[font_type]

    def get_font_config(self, font_type):
        return FontConfig(**self.font_settings.get(font_type, {}))

    def set_font_config(self, font_type, reload=True, **kw):
        font_config = FontConfig(**self.get_font_config(font_type))
        font_config.update(**kw)
        self.font_settings[font_type] = font_config
        if reload:
            self.reload_fonts((font_type, ))

    def reload_fonts(self, font_types=None):
        if font_types is None:
            font_types = self.font_settings.keys()

        for typ in sorted(font_types):
            settings = self.get_font_config(typ)
            if settings is None:
                continue

            if typ not in self._fonts or self._fonts[typ].actual() != settings:
                self._fonts[typ] = tkinter.font.Font(**settings)

    def delete_all_traces(self, modes="rwu"):
        for mode, traces in (("r", self.read_traces),
                             ("w", self.write_traces),
                             ("u", self.undefine_traces)):
            if mode not in modes:
                continue
            for cb_name in tuple(traces.keys()):
                try:
                    var = traces.pop(cb_name)
                    var.trace_vdelete(mode, cb_name)
                except Exception:
                    print(format_exc())

    def delete_all_widget_refs(self):
        '''
        Deletes all objects in this objects __dict__ which inherit from
        the tk.Widget class. Use this for cleaning up dangling references
        to child widgets while inside a widget's destroy method.
        '''
        try:
            widgets = self.__dict__
        except AttributeError:
            widgets = {}
        for k in tuple(widgets.keys()):
            if isinstance(widgets[k], tk.Widget):
                del widgets[k]

    def should_scroll(self, e):
        '''
        Returns True if the widget should have its scrolling method
        follow through when it is invoked. Returns False otherwise.
        '''
        hover = self.winfo_containing(e.x_root, e.y_root)

        if not(getattr(hover, 'can_scroll', False)):
            return False

        try:
            focus = self.focus_get()
            widget = self
            try:
                scroll_unselect = self.f_widget_parent.tag_window.app_root.\
                                  config_file.data.header.tag_window_flags.\
                                  scroll_unselected_widgets
            except AttributeError:
                scroll_unselect = True

            if "field_widgets" not in globals():
                global field_widgets
                from binilla.widgets import field_widgets

            fw = field_widgets.FieldWidget
            if not isinstance(self, fw) and hasattr(self, 'f_widget_parent'):
                widget = self.f_widget_parent
            if not isinstance(hover, fw) and hasattr(hover, 'f_widget_parent'):
                hover = hover.f_widget_parent
            if not isinstance(focus, fw) and hasattr(focus, 'f_widget_parent'):
                focus = focus.f_widget_parent

            if not((focus is hover or scroll_unselect) and hover is widget):
                return False
            elif focus is not widget and hover is not widget:
                # we are not selecting or hovering over this scrollable widget
                return False
        except AttributeError:
            pass
        return True

    def place_window_relative(self, window, x=None, y=None):
        if self.state() in ('iconic', 'withdrawn'):
            # winfo_rootx/y dont work properly when iconic or withdrawn
            window.withdraw()
            return

        # calculate x and y coordinates for this widget
        x_base, y_base = self.winfo_rootx(), self.winfo_rooty()
        w, h = window.geometry().split('+')[0].split('x')[:2]
        if w == '1' and w == '1':
            w = window.winfo_reqwidth()
            h = window.winfo_reqheight()
        if x is None:
            x = self.winfo_width()//2 - int(w)//2
        if y is None:
            y = self.winfo_height()//2 - int(h)//2
        window.geometry('%sx%s+%s+%s' % (w, h, x + x_base, y + y_base))

    def apply_style(self, seen=None):
        if not isinstance(self, (tk.BaseWidget, tk.Tk)):
            return

        widgets = (self, )
        if seen is None:
            seen = set()

        while widgets:
            next_widgets = []
            for w in widgets:
                if id(w) in seen:
                    continue

                if isinstance(w, BinillaWidget):
                    if w is self:
                        seen.add(id(w))

                    w.apply_style(seen)
                    next_widgets.extend(w.children.values())
                    if w is not self:
                        continue
                elif w is not self:
                    seen.add(id(w))

                font = self.get_font(getattr(w, "font_type", self.font_type))

                if isinstance(w, tk.Menu):
                    w.config(fg=self.text_normal_color, bg=self.default_bg_color,
                             font=font)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, tk.PanedWindow):
                    w.config(bd=self.frame_depth, bg=self.default_bg_color)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, tk.Listbox):
                    w.config(bg=self.enum_normal_color, fg=self.text_normal_color,
                             selectbackground=self.enum_highlighted_color,
                             selectforeground=self.text_highlighted_color,
                             font=font)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, tk.Text):
                    w.config(bg=self.entry_normal_color, fg=self.text_normal_color,
                             selectbackground=self.entry_highlighted_color,
                             selectforeground=self.text_highlighted_color, font=font)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, tk.Spinbox):
                    w.config(bg=self.entry_normal_color, fg=self.text_normal_color,
                             disabledbackground=self.entry_disabled_color,
                             disabledforeground=self.text_disabled_color,
                             selectbackground=self.entry_highlighted_color,
                             selectforeground=self.text_highlighted_color,
                             activebackground=self.default_bg_color,
                             readonlybackground=self.entry_disabled_color,
                             buttonbackground=self.default_bg_color, font=font,)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, tk.LabelFrame):
                    w.config(fg=self.text_normal_color, bg=self.default_bg_color,
                             font=font)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, tk.Label):
                    w.config(fg=self.text_normal_color, bg=self.default_bg_color,
                             font=font)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, (tk.Frame, tk.Canvas, tk.Toplevel)):
                    w.config(bg=self.default_bg_color)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, (tk.Radiobutton, tk.Checkbutton)):
                    w.config(disabledforeground=self.text_disabled_color,
                             bg=self.default_bg_color, fg=self.text_normal_color,
                             activebackground=self.default_bg_color,
                             activeforeground=self.text_normal_color,
                             selectcolor=self.entry_normal_color, font=font,)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, tk.Button):
                    w.config(bg=self.button_color, activebackground=self.button_color,
                             fg=self.text_normal_color, bd=self.button_depth,
                             disabledforeground=self.text_disabled_color, font=font)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, tk.Entry):
                    w.config(bd=self.entry_depth,
                        bg=self.entry_normal_color, fg=self.text_normal_color,
                        disabledbackground=self.entry_disabled_color,
                        disabledforeground=self.text_disabled_color,
                        selectbackground=self.entry_highlighted_color,
                        selectforeground=self.text_highlighted_color,
                        readonlybackground=self.entry_disabled_color, font=font,)
                    next_widgets.extend(w.children.values())

                # starting on ttk shit
                elif isinstance(w, ttk.Treeview):
                    w.tag_configure(
                        'item', background=self.entry_normal_color,
                        foreground=self.text_normal_color, font=font)
                elif isinstance(w, ttk.Notebook):
                    next_widgets.extend(w.children.values())

            widgets = next_widgets
