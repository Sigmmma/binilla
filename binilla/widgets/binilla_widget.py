'''
This module contains various widgets which the FieldWidget classes utilize.
'''
import threadsafe_tkinter as tk
import tkinter.ttk as ttk
import tkinter.font

from traceback import format_exc
from binilla import editor_constants as e_c
from binilla.widgets import style_change_lock, font_config


__all__ = ("BinillaWidget", )



class BinillaWidget():
    '''
    This class exists solely as an easy way to change
    the config properties of the widgets in Binilla.
    '''

    can_scroll = False
    tooltip_string = None
    f_widget_parent = None
    disabled = False

    read_traces = ()
    write_traces = ()
    undefine_traces = ()

    _filedialog_style_fix = None
    style_change_lock = None

    # Define class defaults here so they can be easily reset if needed.
    @staticmethod
    def set_style_defaults(dark=False):
        '''
        This sets the default widget settings for this class.
        Useful for resetting after changing the style around.
        '''
        # PADDING
        BinillaWidget.vertical_padx = e_c.VERTICAL_PADX
        BinillaWidget.vertical_pady = e_c.VERTICAL_PADY
        BinillaWidget.horizontal_padx = e_c.HORIZONTAL_PADX
        BinillaWidget.horizontal_pady = e_c.HORIZONTAL_PADY

        # DEPTHS
        BinillaWidget.comment_depth = e_c.COMMENT_DEPTH
        BinillaWidget.listbox_depth = e_c.LISTBOX_DEPTH
        BinillaWidget.entry_depth = e_c.ENTRY_DEPTH
        BinillaWidget.button_depth = e_c.BUTTON_DEPTH
        BinillaWidget.frame_depth = e_c.FRAME_DEPTH

        # COLORS
        if dark:
            BinillaWidget.default_bg_color = e_c.DARK_DEFAULT_BG_COLOR
            BinillaWidget.comment_bg_color = e_c.DARK_COMMENT_BG_COLOR
            BinillaWidget.frame_bg_color = e_c.DARK_FRAME_BG_COLOR

            BinillaWidget.button_color = e_c.DARK_BUTTON_COLOR
            BinillaWidget.button_border_light_color = e_c.DARK_BUTTON_BORDER_LIGHT_COLOR
            BinillaWidget.button_border_dark_color = e_c.DARK_BUTTON_BORDER_DARK_COLOR

            BinillaWidget.text_normal_color = e_c.DARK_TEXT_NORMAL_COLOR
            BinillaWidget.text_disabled_color = e_c.DARK_TEXT_DISABLED_COLOR
            BinillaWidget.text_highlighted_color = e_c.DARK_TEXT_HIGHLIGHTED_COLOR

            BinillaWidget.entry_normal_color = e_c.DARK_ENTRY_NORMAL_COLOR
            BinillaWidget.entry_disabled_color = e_c.DARK_ENTRY_DISABLED_COLOR
            BinillaWidget.entry_highlighted_color = e_c.DARK_ENTRY_HIGHLIGHTED_COLOR

            BinillaWidget.enum_normal_color = e_c.DARK_ENUM_NORMAL_COLOR
            BinillaWidget.enum_disabled_color = e_c.DARK_ENUM_DISABLED_COLOR
            BinillaWidget.enum_highlighted_color = e_c.DARK_ENUM_HIGHLIGHTED_COLOR

            BinillaWidget.tooltip_bg_color = e_c.DARK_COMMENT_BG_COLOR
        else:
            BinillaWidget.default_bg_color = e_c.DEFAULT_BG_COLOR
            BinillaWidget.comment_bg_color = e_c.COMMENT_BG_COLOR
            BinillaWidget.frame_bg_color = e_c.FRAME_BG_COLOR

            BinillaWidget.button_color = e_c.BUTTON_COLOR
            BinillaWidget.button_border_light_color = e_c.BUTTON_BORDER_LIGHT_COLOR
            BinillaWidget.button_border_dark_color = e_c.BUTTON_BORDER_DARK_COLOR

            BinillaWidget.text_normal_color = e_c.TEXT_NORMAL_COLOR
            BinillaWidget.text_disabled_color = e_c.TEXT_DISABLED_COLOR
            BinillaWidget.text_highlighted_color = e_c.TEXT_HIGHLIGHTED_COLOR

            BinillaWidget.entry_normal_color = e_c.ENTRY_NORMAL_COLOR
            BinillaWidget.entry_disabled_color = e_c.ENTRY_DISABLED_COLOR
            BinillaWidget.entry_highlighted_color = e_c.ENTRY_HIGHLIGHTED_COLOR

            BinillaWidget.enum_normal_color = e_c.ENUM_NORMAL_COLOR
            BinillaWidget.enum_disabled_color = e_c.ENUM_DISABLED_COLOR
            BinillaWidget.enum_highlighted_color = e_c.ENUM_HIGHLIGHTED_COLOR

            BinillaWidget.tooltip_bg_color = e_c.TOOLTIP_BG_COLOR

        BinillaWidget.bitmap_canvas_bg_color = e_c.BITMAP_CANVAS_BG_COLOR
        BinillaWidget.bitmap_canvas_outline_color = e_c.BITMAP_CANVAS_OUTLINE_COLOR

        BinillaWidget.io_fg_color = e_c.IO_FG_COLOR
        BinillaWidget.io_bg_color = e_c.IO_BG_COLOR
        BinillaWidget.invalid_path_color = e_c.INVALID_PATH_COLOR

        # FONTS
        BinillaWidget._fonts = {}
        BinillaWidget._ttk_style = None

        BinillaWidget.font_settings = dict(
            # "default" font is required to be here at the very least
            default=font_config.FontConfig(
                family=e_c.DEFAULT_FONT_FAMILY, size=e_c.DEFAULT_FONT_SIZE,
                weight=e_c.DEFAULT_FONT_WEIGHT, slant=e_c.DEFAULT_FONT_SLANT),

            fixed=font_config.FontConfig(
                family=e_c.FIXED_FONT_FAMILY, size=e_c.FIXED_FONT_SIZE,
                weight=e_c.FIXED_FONT_WEIGHT, slant=e_c.FIXED_FONT_SLANT),
            fixed_small=font_config.FontConfig(
                family=e_c.FIXED_FONT_FAMILY, size=e_c.FIXED_FONT_SIZE - 2,
                weight=e_c.FIXED_FONT_WEIGHT, slant=e_c.FIXED_FONT_SLANT),

            treeview=font_config.FontConfig(
                family=e_c.DEFAULT_FONT_FAMILY, size=e_c.DEFAULT_FONT_SIZE,
                weight=e_c.DEFAULT_FONT_WEIGHT, slant=e_c.DEFAULT_FONT_SLANT),

            console=font_config.FontConfig(
                family=e_c.FIXED_FONT_FAMILY, size=e_c.FIXED_FONT_SIZE + 1,
                weight=e_c.FIXED_FONT_WEIGHT, slant=e_c.FIXED_FONT_SLANT),

            heading=font_config.FontConfig(
                family=e_c.HEADING_FONT_FAMILY, size=e_c.HEADING_FONT_SIZE,
                weight=e_c.HEADING_FONT_WEIGHT, slant=e_c.HEADING_FONT_SLANT),
            heading_small=font_config.FontConfig(
                family=e_c.HEADING_SMALL_FONT_FAMILY, size=e_c.HEADING_SMALL_FONT_SIZE,
                weight=e_c.HEADING_SMALL_FONT_WEIGHT, slant=e_c.HEADING_SMALL_FONT_SLANT),
            frame_title=font_config.FontConfig(
                family=e_c.CONTAINER_TITLE_FONT_FAMILY, size=e_c.CONTAINER_TITLE_FONT_SIZE,
                weight=e_c.CONTAINER_TITLE_FONT_WEIGHT, slant=e_c.CONTAINER_TITLE_FONT_SLANT),

            comment=font_config.FontConfig(
                family=e_c.COMMENT_FONT_FAMILY, size=e_c.COMMENT_FONT_SIZE,
                weight=e_c.COMMENT_FONT_WEIGHT, slant=e_c.COMMENT_FONT_SLANT),
            tooltip=font_config.FontConfig(
                family=e_c.DEFAULT_FONT_FAMILY, size=e_c.DEFAULT_FONT_SIZE,
                weight=e_c.DEFAULT_FONT_WEIGHT, slant=e_c.DEFAULT_FONT_SLANT),
            )

        # MISC
        BinillaWidget.title_width = e_c.TITLE_WIDTH
        BinillaWidget.enum_menu_width = e_c.ENUM_MENU_WIDTH
        BinillaWidget.scroll_menu_width = e_c.SCROLL_MENU_WIDTH
        BinillaWidget.min_entry_width = e_c.MIN_ENTRY_WIDTH
        BinillaWidget.textbox_height = e_c.TEXTBOX_HEIGHT
        BinillaWidget.textbox_width = e_c.TEXTBOX_WIDTH

        BinillaWidget.bool_frame_min_width = e_c.BOOL_FRAME_MIN_WIDTH
        BinillaWidget.bool_frame_min_height = e_c.BOOL_FRAME_MIN_HEIGHT
        BinillaWidget.bool_frame_max_width = e_c.BOOL_FRAME_MAX_WIDTH
        BinillaWidget.bool_frame_max_height = e_c.BOOL_FRAME_MAX_HEIGHT

        BinillaWidget.def_int_entry_width = e_c.DEF_INT_ENTRY_WIDTH
        BinillaWidget.def_float_entry_width = e_c.DEF_FLOAT_ENTRY_WIDTH
        BinillaWidget.def_string_entry_width = e_c.DEF_STRING_ENTRY_WIDTH

        BinillaWidget.max_int_entry_width = e_c.MAX_INT_ENTRY_WIDTH
        BinillaWidget.max_float_entry_width = e_c.MAX_FLOAT_ENTRY_WIDTH
        BinillaWidget.max_string_entry_width = e_c.MAX_STRING_ENTRY_WIDTH

        BinillaWidget.scroll_menu_max_width = e_c.SCROLL_MENU_MAX_WIDTH
        BinillaWidget.scroll_menu_max_height = e_c.SCROLL_MENU_MAX_HEIGHT

        BinillaWidget.font_type = "default"  # the type of font to use
        if dark:
            BinillaWidget.ttk_theme = "clam"
        else:
            BinillaWidget.ttk_theme = "alt"

    def __init__(self, *args, **kwargs):
        self.read_traces = {}
        self.write_traces = {}
        self.undefine_traces = {}
        self.fix_filedialog_style()
        self.style_change_lock = style_change_lock.StyleChangeLock(self)

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

    def configure_ttk_style(self, ttk_class_names, **config_kw):
        config_kw = self._setup_ttk_style(ttk_class_names, **config_kw)
        for ttk_class_name in ttk_class_names:
            self._ttk_style.configure(ttk_class_name, **config_kw)

    def map_ttk_style(self, ttk_class_names, **config_kw):
        config_kw = self._setup_ttk_style(ttk_class_names, **config_kw)
        for ttk_class_name in ttk_class_names:
            self._ttk_style.map(ttk_class_name, **config_kw)

    def _setup_ttk_style(self, ttk_class_names, **config_kw):
        if "font" in config_kw:
            config_kw["font"] = self.get_font(config_kw["font"])

        if self._ttk_style is None:
            self._ttk_style = ttk.Style(self._root())

        self._ttk_style.theme_use(self.ttk_theme)
        return config_kw

    def get_font_config(self, font_type):
        return font_config.FontConfig(**self.font_settings.get(font_type, {}))

    def set_font_config(self, font_type, reload=True, **kw):
        cfg = font_config.FontConfig(**self.get_font_config(font_type))
        cfg.update(**kw)
        self.font_settings[font_type] = cfg
        if reload:
            self.reload_fonts((font_type, ))

    def reload_fonts(self, font_types=None):
        if font_types is None:
            font_types = self.font_settings.keys()

        root = self._root()
        for typ in sorted(font_types):
            settings = self.get_font_config(typ)
            if settings is None:
                continue

            try:
                if typ not in self._fonts or self._fonts[typ].actual() != settings:
                    self._fonts[typ] = tkinter.font.Font(root, **settings)
            except Exception:
                pass

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
                    pass

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
                scroll_unselect = self.f_widget_parent.tag_window.\
                                  widget_flags.scroll_unselected
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

    @property
    def applying_style_change(self):
        return bool(self.style_change_lock.lock_depth)

    def enter_style_change(self):
        pass

    def exit_style_change(self):
        pass

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
                    if w.style_change_lock is None:
                        raise TypeError("TELL MOSES HE FUCKED UP: " + str(type(w)))

                    if w is not self:
                        with w.style_change_lock as depth:
                            w.apply_style(seen)

                seen.add(id(w))

                font_type = getattr(w, "font_type", self.font_type)
                font = self.get_font(font_type)

                try:
                    if isinstance(w, tk.Menu):
                        w.config(
                            fg=self.text_normal_color, bg=self.default_bg_color,
                            font=font, highlightthickness=0,)
                    elif isinstance(w, tk.PanedWindow):
                        w.config(
                            bd=self.frame_depth, bg=self.default_bg_color,
                            highlightthickness=0,)
                    elif isinstance(w, tk.Listbox):
                        w.config(
                            bg=self.enum_normal_color, fg=self.text_normal_color,
                            selectbackground=self.enum_highlighted_color,
                            selectforeground=self.text_highlighted_color,
                            font=font, highlightthickness=0,)
                    elif isinstance(w, tk.Text):
                        w.config(
                            bd=self.entry_depth, font=font,
                            bg=self.entry_normal_color, fg=self.text_normal_color,
                            selectbackground=self.entry_highlighted_color,
                            selectforeground=self.text_highlighted_color,
                            highlightthickness=0,)
                    elif isinstance(w, tk.Spinbox):
                        w.config(
                            bd=self.entry_depth, font=font,
                            bg=self.entry_normal_color, fg=self.text_normal_color,
                            disabledbackground=self.entry_disabled_color,
                            disabledforeground=self.text_disabled_color,
                            selectbackground=self.entry_highlighted_color,
                            selectforeground=self.text_highlighted_color,
                            activebackground=self.default_bg_color,
                            readonlybackground=self.entry_disabled_color,
                            buttonbackground=self.default_bg_color,
                            highlightthickness=0,)
                    elif isinstance(w, tk.LabelFrame):
                        w.config(
                            fg=self.text_normal_color, bg=self.default_bg_color,
                            font=font, highlightthickness=0,)
                    elif isinstance(w, tk.Label):
                        w.config(
                            fg=self.text_normal_color, bg=self.default_bg_color,
                            font=font, highlightthickness=0,)
                    elif isinstance(w, (tk.Frame, tk.Canvas, tk.Toplevel)):
                        w.config(bg=self.default_bg_color, highlightthickness=0,)
                    elif isinstance(w, (tk.Radiobutton, tk.Checkbutton)):
                        w.config(
                            disabledforeground=self.text_disabled_color,
                            bg=self.default_bg_color, fg=self.text_normal_color,
                            activebackground=self.default_bg_color,
                            activeforeground=self.text_normal_color,
                            selectcolor=self.entry_normal_color, font=font,
                            highlightthickness=0,)
                    elif isinstance(w, tk.Button):
                        w.config(
                            bg=self.button_color, activebackground=self.button_color,
                            fg=self.text_normal_color, bd=self.button_depth,
                            disabledforeground=self.text_disabled_color, font=font,
                            highlightthickness=0,)
                    elif isinstance(w, tk.Entry):
                        w.config(
                            bd=self.entry_depth, font=font,
                            bg=self.entry_normal_color, fg=self.text_normal_color,
                            disabledbackground=self.entry_disabled_color,
                            disabledforeground=self.text_disabled_color,
                            selectbackground=self.entry_highlighted_color,
                            selectforeground=self.text_highlighted_color,
                            readonlybackground=self.entry_disabled_color,
                            highlightthickness=0,)
                except tk.TclError:
                    pass

                if hasattr(w, "children"):
                    next_widgets.extend(w.children.values())

            widgets = next_widgets

    def update_ttk_style(self):
        # TButton
        self.configure_ttk_style(
            ("TButton", ), font="default", border=(0, 0, 0, 0),
            highlightthickness=0, borderwidth=self.button_depth,
            background=self.button_color,
            foreground=self.text_normal_color,
            selectbackground=self.button_color,
            selectforeground=self.text_disabled_color,
            disabledforeground=self.text_disabled_color,
            bordercolor=self.button_border_light_color,
            lightcolor=self.button_border_light_color,
            darkcolor=self.button_border_dark_color,
            default=self.button_border_dark_color,
            troughcolor=self.button_color,
            )
        self.map_ttk_style(
            ("TButton", ),
            background=[("active", self.button_color),
                        ("pressed", self.button_color),
                        ("focus", self.button_color),
                        ("selected", self.button_color),
                        ("alternate", self.button_color),  # used for alt style
                        ],
            foreground=[("active", self.text_normal_color),
                        ("pressed", self.text_normal_color),
                        ("focus", self.text_normal_color),  # alt theme uses this
                        #                                     as a border outline
                        ("selected", self.text_disabled_color),
                        ("disabled", self.text_disabled_color),
                        ],
            bordercolor=[("active", self.button_color),
                         ("pressed", self.button_color),
                         ("focus", self.button_color)
                         ],
            lightcolor=[("active", self.button_border_light_color),
                        ("pressed", self.button_border_light_color)
                        ],
            darkcolor=[("active", self.button_border_dark_color),
                       ("pressed", self.button_border_dark_color)
                       ],
            default=[("active", self.button_border_dark_color),
                     ("pressed", self.button_border_dark_color)
                     ]
            )

        # Treeview
        self.configure_ttk_style(
            ("Treeview", ), font="treeview",
            background=self.entry_normal_color,
            foreground=self.text_normal_color,
            fieldbackground=self.entry_normal_color,
            )
        self.configure_ttk_style(
            ("Treeview.Row", "Treeview.Item", "Treeview.Cell"), font="treeview",
            background=self.entry_normal_color,
            foreground=self.text_normal_color,
            fieldbackground=self.entry_normal_color,
            )
        self.configure_ttk_style(
            ("Treeview.Heading", ), font="heading_small",
            background=self.default_bg_color,
            foreground=self.text_normal_color
            )

        self.map_ttk_style(
            ("Treeview.Heading", ),
            background=[("active", self.default_bg_color)],
            foreground=[("active", self.text_normal_color)]
            )

        # TNotebook
        self.configure_ttk_style(
            ("TNotebook", ),
            background=self.default_bg_color,
            )
        self.configure_ttk_style(
            ("TNotebook.Tab", ), font="heading_small",
            background=self.default_bg_color,
            foreground=self.text_normal_color,
            )

        self.map_ttk_style(
            ("TNotebook.Tab", ),
            background=[("active", self.default_bg_color)],
            foreground=[("active", self.text_normal_color)]
            )

# Set widget defaults. ABSOLUTELY REQUIRED.
BinillaWidget.set_style_defaults(dark=True)
