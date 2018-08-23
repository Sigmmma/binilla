'''
This module contains various widgets which the FieldWidget classes utilize.
'''
import gc
import os
import random
import tempfile
import weakref
from math import log
from time import time
from traceback import format_exc
from tkinter.filedialog import asksaveasfilename

import threadsafe_tkinter as tk
import tkinter.ttk as ttk
from . import editor_constants as e_c

field_widgets = None  # linked to through __init__.py

win_10_pad = 2


def import_arbytmap(force=False):
    # dont import it if an import was already attempted
    if "arbytmap" not in globals() or force:
        try:
            global arbytmap
            import arbytmap
        except ImportError:
            arbytmap = None

    return bool(arbytmap)


def get_mouse_delta(e):
    if e_c.IS_WIN or e_c.IS_MAC:
        return 1 if e.delta < 0 else -1
    elif e_c.IS_LNX:
        return -1 if e.num == 4 else 1
    else:
        return e.delta


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

    read_traces = ()
    write_traces = ()
    undefine_traces = ()

    def __init__(self, *args, **kwargs):
        self.read_traces = {}
        self.write_traces = {}
        self.undefine_traces = {}

    def read_trace(self, var, function):
        cb_name = var.trace("r", function)
        self.read_traces[cb_name] = var

    def write_trace(self, var, function):
        cb_name = var.trace("w", function)
        self.write_traces[cb_name] = var

    def undefine_trace(self, var, function):
        cb_name = var.trace("u", function)
        self.undefine_traces[cb_name] = var

    def delete_all_traces(self, modes="rw"):
        for mode, traces in (("r", self.read_traces),
                             ("w", self.write_traces),
                             ("u", self.undefine_traces)):
            if mode not in modes:
                continue
            for cb_name in tuple(traces.keys()):
                var = traces.pop(cb_name)
                var.trace_vdelete(mode, cb_name)

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

                if isinstance(w, tk.Menu):
                    w.config(fg=self.text_normal_color, bg=self.default_bg_color)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, tk.Listbox):
                    w.config(bg=self.enum_normal_color, fg=self.text_normal_color,
                             selectbackground=self.enum_highlighted_color,
                             selectforeground=self.text_highlighted_color)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, ttk.Treeview):
                    w.tag_configure(
                        'item', background=self.entry_normal_color,
                        foreground=self.text_normal_color)
                elif isinstance(w, tk.Text):
                    w.config(bg=self.entry_normal_color, fg=self.text_normal_color,
                             selectbackground=self.entry_highlighted_color,
                             selectforeground=self.text_highlighted_color)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, tk.Spinbox):
                    w.config(bg=self.entry_normal_color, fg=self.text_normal_color,
                             disabledbackground=self.entry_disabled_color,
                             disabledforeground=self.text_disabled_color,
                             selectbackground=self.entry_highlighted_color,
                             selectforeground=self.text_highlighted_color,
                             activebackground=self.default_bg_color,
                             readonlybackground=self.entry_disabled_color,
                             buttonbackground=self.default_bg_color,)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, tk.LabelFrame):
                    w.config(fg=self.text_normal_color, bg=self.default_bg_color)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, tk.Label):
                    w.config(fg=self.text_normal_color, bg=self.default_bg_color)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, (tk.Frame, tk.Canvas, tk.Toplevel)):
                    w.config(bg=self.default_bg_color)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, tk.Checkbutton):
                    w.config(disabledforeground=self.text_disabled_color,
                             bg=self.default_bg_color, fg=self.text_normal_color,
                             activebackground=self.default_bg_color,
                             activeforeground=self.text_normal_color,
                             selectcolor=self.entry_normal_color,)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, tk.Button):
                    w.config(bg=self.button_color, activebackground=self.button_color,
                             fg=self.text_normal_color, bd=self.button_depth,
                             disabledforeground=self.text_disabled_color)
                    next_widgets.extend(w.children.values())
                elif isinstance(w, tk.Entry):
                    w.config(bd=self.entry_depth,
                        bg=self.entry_normal_color, fg=self.text_normal_color,
                        disabledbackground=self.entry_disabled_color,
                        disabledforeground=self.text_disabled_color,
                        selectbackground=self.entry_highlighted_color,
                        selectforeground=self.text_highlighted_color,
                        readonlybackground=self.entry_disabled_color,)
                    next_widgets.extend(w.children.values())

            widgets = next_widgets


class ScrollMenu(tk.Frame, BinillaWidget):
    '''
    Used as a menu for certain FieldWidgets, such as when
    selecting an array element or an enumerator option.
    '''
    disabled = False
    variable = None
    callback = None
    option_box = None
    max_height = None
    max_index = -1

    option_cache = None
    option_getter = None
    options_sane = False
    options_volatile = False
    selecting = False  # prevents multiple selections at once

    can_scroll = True
    option_box_visible = False
    click_outside_funcid = None

    default_text = None

    menu_width = BinillaWidget.scroll_menu_width

    def __init__(self, *args, **kwargs):
        BinillaWidget.__init__(self)
        sel_index = kwargs.pop('sel_index', -1)
        disabled = kwargs.pop('disabled', False)

        options = kwargs.pop('options', None)
        self.option_getter = kwargs.pop('option_getter', None)
        self.callback = kwargs.pop('callback', None)
        self.variable = kwargs.pop('variable', None)
        self.max_index = kwargs.pop('max_index', self.max_index)
        self.max_height = kwargs.pop('max_height', self.max_height)
        self.f_widget_parent = kwargs.pop('f_widget_parent', None)
        self.menu_width = kwargs.pop('menu_width', self.menu_width)
        self.options_sane = kwargs.pop('options_sane', False)
        self.options_volatile = kwargs.pop('options_volatile', False)
        self.default_text = kwargs.pop('default_text', e_c.INVALID_OPTION)

        if self.max_height is None:
            self.max_height = self.scroll_menu_max_height

        kwargs.update(relief='sunken', bd=self.listbox_depth,
                      bg=self.default_bg_color)
        tk.Frame.__init__(self, *args, **kwargs)

        if self.variable is None:
            self.variable = tk.IntVar(self, sel_index)

        self.write_trace(self.variable, lambda *a: self.update_label())

        self.sel_label = tk.Label(
            self, bg=self.enum_normal_color, fg=self.text_normal_color,
            bd=2, relief='groove',
            width=self.menu_width if self.menu_width else self.enum_menu_width)
        # the button_frame is to force the button to be a certain size
        self.button_frame = tk.Frame(self, relief='flat', height=18, width=18,
                                     bd=0, bg=self.default_bg_color)
        self.button_frame.pack_propagate(0)
        self.arrow_button = tk.Button(
            self.button_frame, bd=self.button_depth, text="▼", width=1,
            bg=self.button_color, activebackground=self.button_color,
            fg=self.text_normal_color, disabledforeground=self.text_disabled_color)
        self.sel_label.pack(side="left", fill="both", expand=True)
        self.button_frame.pack(side="left", fill=None, expand=False)
        self.arrow_button.pack(side="left", fill='both', expand=True)

        # make the option box to populate
        self.option_frame = tk.Frame(
            self.winfo_toplevel(), highlightthickness=0, bd=0)
        self.option_frame.pack_propagate(0)
        self.option_bar = tk.Scrollbar(self.option_frame, orient="vertical")
        self.option_box = tk.Listbox(
            self.option_frame, highlightthickness=0, exportselection=False,
            bg=self.enum_normal_color, fg=self.text_normal_color,
            selectbackground=self.enum_highlighted_color,
            selectforeground=self.text_highlighted_color,
            yscrollcommand=self.option_bar.set, width=self.menu_width)
        self.option_bar.config(command=self.option_box.yview)

        # make sure the TagWindow knows these widgets are scrollable
        for w in (self.sel_label, self.button_frame, self.arrow_button,
                  self.option_frame, self.option_bar, self.option_box):
            w.can_scroll = self.can_scroll
            w.f_widget_parent = self.f_widget_parent

        # make bindings so arrow keys can be used to navigate the menu
        self.button_frame.bind('<Up>', self.decrement_sel)
        self.button_frame.bind('<Down>', self.increment_sel)
        self.arrow_button.bind('<Up>', self.decrement_sel)
        self.arrow_button.bind('<Down>', self.increment_sel)
        self.option_bar.bind('<Up>', self.decrement_listbox_sel)
        self.option_bar.bind('<Down>', self.increment_listbox_sel)

        if e_c.IS_LNX:
            self.sel_label.bind('<4>', self._mousewheel_scroll)
            self.sel_label.bind('<5>', self._mousewheel_scroll)
            self.button_frame.bind('<4>', self._mousewheel_scroll)
            self.button_frame.bind('<5>', self._mousewheel_scroll)
            self.arrow_button.bind('<4>', self._mousewheel_scroll)
            self.arrow_button.bind('<5>', self._mousewheel_scroll)
        else:
            self.sel_label.bind('<MouseWheel>', self._mousewheel_scroll)
            self.button_frame.bind('<MouseWheel>', self._mousewheel_scroll)
            self.arrow_button.bind('<MouseWheel>', self._mousewheel_scroll)

        self.sel_label.bind('<Button-1>', self.click_label)
        self.arrow_button.bind('<ButtonRelease-1>', self.select_option_box)
        self.arrow_button.bind('<Return>', self.select_option_box)
        self.arrow_button.bind('<space>', self.select_option_box)
        self.option_bar.bind('<FocusOut>', self.deselect_option_box)
        self.option_bar.bind('<Return>', self.select_menu)
        self.option_bar.bind('<space>', self.select_menu)
        self.option_box.bind('<<ListboxSelect>>', self.select_menu)

        if disabled:
            self.disable()

        if options is not None:
            self.set_options(options)

    def apply_style(self, seen=None):
        BinillaWidget.apply_style(self, seen)
        if self.disabled:
            bg = self.entry_disabled_color
            fg = self.text_disabled_color
        else:
            bg = self.enum_normal_color
            fg = self.text_normal_color
        self.sel_label.config(bg=bg, fg=fg)

    @property
    def sel_index(self):
        return self.variable.get()

    @sel_index.setter
    def sel_index(self, new_val):
        self.variable.set(new_val)

    def get_option(self, opt_index=None):
        if opt_index is None:
            opt_index = "active"
        assert isinstance(opt_index, (int, str))
        return self.get_options(opt_index)

    def get_options(self, opt_index=None):
        if self.option_getter is not None:
            return self.option_getter(opt_index)
        elif self.option_cache is None:
            self.option_cache = {}

        if opt_index is None:
            return self.option_cache
        elif opt_index == "active":
            opt_index = self.sel_index
        return self.option_cache.get(opt_index)

    def set_options(self, new_options):
        if (not isinstance(new_options, dict) and
                hasattr(new_options, "__iter__")):
            new_options = {i: new_options[i] for i in range(len(new_options))}
        self.option_cache = dict(new_options)
        self.max_index = len(new_options) - 1
        self.options_sane = False
        self.update_label()

    def _mousewheel_scroll(self, e):
        if not self.should_scroll(e) or (self.option_box_visible or
                                         self.disabled):
            return

        delta = get_mouse_delta(e)
        if delta < 0:
            self.decrement_sel()
        elif delta > 0:
            self.increment_sel()

    def click_outside_option_box(self, e):
        if not self.option_box_visible or self.disabled:
            return
        under_mouse = self.winfo_containing(e.x_root, e.y_root)
        if under_mouse not in (self.option_frame, self.option_bar,
                               self.option_box, self.sel_label,
                               self.arrow_button):
            self.select_menu()

    def decrement_listbox_sel(self, e=None):
        if self.selecting:
            return
        sel_indices = self.option_box.curselection()
        if not sel_indices:
            return
        sel_index = sel_indices[0] - 1
        if sel_index < 0:
            new_index = (self.max_index >= 0) - 1
        try:
            self.selecting = True
            self.option_box.select_clear(0, tk.END)
            self.option_box.select_set(sel_index)
            self.option_box.see(sel_index)
            self.sel_index = sel_index
            if self.callback is not None:
                self.callback(sel_index)
            self.selecting = False
        except Exception:
            self.selecting = False
            raise

    def decrement_sel(self, e=None):
        if self.selecting:
            return
        new_index = self.sel_index - 1
        if new_index < 0:
            new_index = (self.max_index >= 0) - 1
        try:
            self.selecting = True
            self.sel_index = new_index
            if self.callback is not None:
                self.callback(new_index)
            self.selecting = False
        except Exception:
            self.selecting = False
            raise

    def destroy(self):
        if self.click_outside_funcid is not None:
            self.winfo_toplevel().unbind('<Button>', self.click_outside_funcid)
        tk.Frame.destroy(self)
        self.delete_all_traces()
        self.delete_all_widget_refs()

    def deselect_option_box(self, e=None):
        if self.disabled:
            self.sel_label.config(bg=self.enum_disabled_color,
                                  fg=self.text_disabled_color)
        else:
            self.sel_label.config(bg=self.enum_normal_color,
                                  fg=self.text_normal_color)

        if self.option_box_visible:
            self.option_frame.place_forget()
            self.option_bar.forget()
            self.option_box_visible = False
            self.click_outside_funcid = None

        self.arrow_button.unbind('<FocusOut>')

    def disable(self):
        if self.disabled:
            return

        self.disabled = True
        self.config(bg=self.enum_disabled_color)
        self.sel_label.config(bg=self.enum_disabled_color,
                              fg=self.text_disabled_color)
        self.arrow_button.config(state='disabled')

    def enable(self):
        if not self.disabled:
            return
        self.disabled = False
        self.sel_label.config(bg=self.enum_normal_color,
                              fg=self.text_normal_color)
        self.arrow_button.config(state='normal')

    def increment_listbox_sel(self, e=None):
        if self.selecting:
            return
        sel_indices = self.option_box.curselection()
        if not sel_indices:
            return
        sel_index = sel_indices[0] + 1
        if sel_index > self.max_index:
            new_index = self.max_index
        try:
            self.selecting = True
            self.option_box.select_clear(0, tk.END)
            self.option_box.select_set(sel_index)
            self.option_box.see(sel_index)
            self.sel_index = sel_index
            if self.callback is not None:
                self.callback(sel_index)
            self.selecting = False
        except Exception:
            self.selecting = False
            raise

    def increment_sel(self, e=None):
        if self.selecting:
            return
        new_index = self.sel_index + 1
        if new_index > self.max_index:
            new_index = self.max_index
        try:
            self.selecting = True
            self.sel_index = new_index
            if self.callback is not None:
                self.callback(new_index)
            self.selecting = False
        except Exception:
            self.selecting = False
            raise

    def select_menu(self, e=None):
        sel_index = [int(i) for i in self.option_box.curselection()]
        if not sel_index:
            return
        self.sel_index = sel_index[0]
        if self.callback is not None:
            self.callback(self.sel_index)
        self.deselect_option_box()
        self.arrow_button.focus_set()
        self.arrow_button.bind('<FocusOut>', self.deselect_option_box)

    def click_label(self, e=None):
        if self.option_box_visible:
            self.select_menu()
        else:
            self.select_option_box()

    def select_option_box(self, e=None):
        if not self.disabled:
            self.show_menu()
            if self.option_box_visible:
                self.sel_label.config(bg=self.enum_highlighted_color,
                                      fg=self.text_highlighted_color)

    def show_menu(self):
        if not (self.max_index + 1):
            return

        self.arrow_button.unbind('<FocusOut>')

        # get the options before checking if sane
        # since getting them will force a sanity check
        options = self.get_options()
        option_cnt = self.max_index + 1

        if not self.options_sane or self.options_volatile:
            END = tk.END
            self.option_box.delete(0, END)
            insert = self.option_box.insert
            def_str = '%s' + ('. %s' % self.default_text)
            menu_width = self.menu_width if self.menu_width else\
                         self.enum_menu_width
            for i in range(option_cnt):
                if i in options:
                    insert(END, options[i])
                else:
                    insert(END, def_str % i)

            self.options_sane = True
            self.sel_label.config(width=menu_width)

        self.option_box.pack(side='left', expand=True, fill='both')
        self.update()

        self_height = self.winfo_reqheight()
        root = self.winfo_toplevel()

        pos_x = self.sel_label.winfo_rootx() - root.winfo_rootx()
        pos_y = self.winfo_rooty() - root.winfo_rooty() + self_height
        height = min(max(option_cnt, 0), self.max_height)*(14 + win_10_pad) + 4
        width = max(self.option_box.winfo_reqwidth(),
                    self.sel_label.winfo_width() +
                    self.arrow_button.winfo_width())

        # figure out how much space is above and below where the list will be
        space_above = pos_y - self_height - 32
        space_below = (root.winfo_height() + 32 - pos_y - 4)

        # if there is more space above than below, swap the position
        if space_below >= height:
            pass
        elif space_above <= space_below:
            # there is more space below than above, so cap by the space below
            height = min(height, space_below)
        elif space_below < height:
            # there is more space above than below and the space below
            # isnt enough to fit the height, so cap it by the space above
            height = min(height, space_above)
            pos_y -= self_height + height - 4

        # pack the scrollbar is there isnt enough room to display the list
        if option_cnt > self.max_height or (height - 4)//14 < option_cnt:
            self.option_bar.pack(side='left', fill='y')
        else:
            # place it off the frame so it can still be used for key bindings
            self.option_bar.place(x=pos_x + width, y=pos_y, anchor=tk.NW)
        self.option_bar.focus_set()
        self.option_frame.place(x=pos_x, y=pos_y, anchor=tk.NW,
                                height=height, width=width)
        # make a binding to the parent Toplevel to remove the
        # options box if the mouse is clicked outside of it.
        self.click_outside_funcid = self.winfo_toplevel().bind(
            '<Button>', lambda e, s=self: s.click_outside_option_box(e))
        self.option_box_visible = True

        if self.sel_index >= option_cnt:
            self.sel_index = self.max_index

        try:
            self.option_box.select_clear(0, tk.END)
            if self.sel_index >= 0:
                self.option_box.select_set(self.sel_index)
                self.option_box.see(self.sel_index)
        except Exception:
            pass

    def update_label(self, text=''):
        if not text and self.sel_index >= 0:
            text = self.get_options("active")
            if text is None:
                text = '%s. %s' % (self.sel_index, self.default_text)
        self.sel_label.config(text=text, anchor="w")


class ToolTipHandler(BinillaWidget):
    app_root = None
    tag_window = None
    tip_window = None
    focus_widget = None

    hover_time = 1.0
    rehover_time = 0.5
    hover_start = 0.0
    rehover_start = 0.0

    curr_tip_text = ''

    # run the check 15 times a second
    schedule_rate = int(1000/15)
    last_mouse_x = 0
    last_mouse_y = 0

    tip_offset_x = 15
    tip_offset_y = 0

    def __init__(self, app_root, *args, **kwargs):
        BinillaWidget.__init__(self)
        self.app_root = app_root
        self.hover_start = time()

        # begin the looping
        app_root.after(int(self.schedule_rate), self.check_loop)

    def check_loop(self):
        # get the widget under the mouse
        root = self.app_root
        mouse_x, mouse_y = root.winfo_pointerx(), root.winfo_pointery()

        mouse_dx = mouse_x - self.last_mouse_x
        mouse_dy = mouse_y - self.last_mouse_y

        self.last_mouse_x = mouse_x
        self.last_mouse_y = mouse_y

        # move the tip_window to where it needs to be
        if self.tip_window and mouse_dx or mouse_dy:
            try:
                self.tip_window.geometry("+%s+%s" % (mouse_x + self.tip_offset_x,
                                                     mouse_y + self.tip_offset_y))
            except Exception:
                pass

        try:
            focus = root.winfo_containing(mouse_x, mouse_y)
        except KeyError:
            self.app_root.after(self.schedule_rate, self.check_loop)
            return

        # get the widget in focus if nothing is under the mouse
        #if tip_widget is None:
        #    focus = root.focus_get()

        try:
            tip_text = focus.tooltip_string
        except Exception:
            tip_text = None

        curr_time = time()

        if self.curr_tip_text != tip_text and self.tip_window:
            # a tip window is displayed and the focus is different
            self.hide_tip()
            self.rehover_start = curr_time

        if self.tip_window is None:
            # no tip window is displayed, so start trying to display one

            can_display = (curr_time >= self.hover_time + self.hover_start or
                           curr_time <= self.rehover_time + self.rehover_start)
            
            if not tip_text or not self.show_tooltips:
                # reset the hover counter cause nothing is under focus
                self.hover_start = curr_time
            elif focus is not self.focus_widget:
                # start counting how long this widget has been in focus
                self.hover_start = curr_time
                self.focus_widget = focus
            elif can_display:
                # reached the hover time! display the tooltip window
                self.show_tip(mouse_x + self.tip_offset_x,
                              mouse_y + self.tip_offset_y, tip_text)
                self.curr_tip_text = tip_text
        self.app_root.after(self.schedule_rate, self.check_loop)

    @property
    def show_tooltips(self):
        try:
            return bool(self.app_root.config_file.data.header.\
                        tag_window_flags.show_tooltips)
        except Exception:
            return False

    def show_tip(self, pos_x, pos_y, tip_text):
        if self.tip_window:
            return

        self.tip_window = tk.Toplevel(self.app_root)
        self.tip_window.wm_overrideredirect(1)
        self.tip_window.wm_geometry("+%d+%d" % (pos_x, pos_y))
        label = tk.Label(
            self.tip_window, text=tip_text, justify='left', relief='solid',
            bg=self.tooltip_bg_color, fg=self.text_normal_color, borderwidth=1)
        label.pack()

    def hide_tip(self):
        try: self.tip_window.destroy()
        except Exception: pass
        self.tip_window = None
        self.focus_widget = None


class PhotoImageHandler():
    # this class utilizes the arbytmap module, but will only
    # import it once an instance of this class is created
    temp_path = ""
    arby = None
    _images = None  # loaded and cached PhotoImages
    channels = ()
    channel_mapping = None

    def __init__(self, tex_block=None, tex_info=None, temp_path=""):
        if not import_arbytmap():
            raise ValueError(
                "Arbytmap is not loaded. Cannot generate PhotoImages.")
        self.arby = arbytmap.Arbytmap()
        self._images = {}
        self.channels = dict(A=False, L=True, R=True, G=True, B=True)
        self.temp_path = temp_path

        if tex_block and tex_info:
            self.load_texture(tex_block, tex_info)

    def load_texture(self, tex_block, tex_info):
        #w = max(tex_info.get("width", 1), 1)
        #h = max(tex_info.get("height", 1), 1)
        #d = max(tex_info.get("depth", 1), 1)
        #if ((2**int(log(w, 2)) != w) or
        #    (2**int(log(h, 2)) != h) or
        #    (2**int(log(d, 2)) != d)):
        #    print("Cannot display non-power of 2 textures.")
        #    return
        self.arby.load_new_texture(texture_block=tex_block,
                                   texture_info=tex_info)

    def set_channel_mode(self, mode=-1):
        # 0 = RGB or L, 1 = A, 2 = ARGB or AL, 3 = R, 4 = G, 5 = B
        if mode not in range(-1, 6):
            return

        channels = self.channels
        channels.update(L=False, R=False, G=False, B=False, A=False)
        if self.channel_count <= 2:
            if mode in (0, 2):
                channels.update(L=True)
        elif mode == 0: channels.update(R=True, G=True, B=True)
        elif mode == 2: channels.update(R=True, G=True, B=True)
        elif mode == 3: channels.update(R=True)
        elif mode == 4: channels.update(G=True)
        elif mode == 5: channels.update(B=True)

        if mode in (1, 2):
            channels.update(A=True)

        if self.channel_count == 1:
            chan_map = [0]
            if   "A" in self.tex_format and not channels["A"]: chan_map[0] = -1
            elif "L" in self.tex_format and not channels["L"]: chan_map[0] = -1
        elif self.channel_count == 2:
            chan_map = [0, 1, 1, 1]
            if not channels["A"]: chan_map[0]  = -1
            if not channels["L"]: chan_map[1:] = (-1, -1, -1)
        else:
            chan_map = [0, 1, 2, 3]
            if not channels["A"]: chan_map[0] = -1
            if not channels["R"]: chan_map[1] = -1
            if not channels["G"]: chan_map[2] = -1
            if not channels["B"]: chan_map[3] = -1
            if min(chan_map[1:]) < 0:
                chan_map[1] = chan_map[2] = chan_map[3] = max(chan_map[1:])

        if len(chan_map) > 1 and max(chan_map[1:]) < 0:
            chan_map = [-1, 0, 0, 0]

        self.channel_mapping = chan_map

    def load_images(self, mip_levels="all", sub_bitmap_indexes="all"):
        if not self.temp_path:
            raise ValueError("Cannot create PhotoImages without a specified "
                             "temporary filepath to save their PNG's to.")

        if not sub_bitmap_indexes and not mip_levels:
            return {}

        if sub_bitmap_indexes == "all":
            sub_bitmap_indexes = range(self.max_sub_bitmap + 1)
        elif isinstance(sub_bitmap_indexes, int):
            sub_bitmap_indexes = (sub_bitmap_indexes, )

        if mip_levels == "all":
            mip_levels = range(self.max_mipmap + 1)
        elif isinstance(mip_levels, int):
            mip_levels = (mip_levels, )

        new_images = {}
        try:
            self.arby.swizzle_mode = False
            image_list = self.arby.make_photoimages(
                self.temp_path, bitmap_indexes=sub_bitmap_indexes,
                keep_alpha=self.channels.get("A"), mip_levels="all",
                channel_mapping=self.channel_mapping)
        except TypeError:
            # no texture loaded
            return {}

        c = frozenset((k, v) for k, v in self.channels.items())
        mip_ct        = self.max_mipmap + 1
        sub_bitmap_ct = self.max_sub_bitmap + 1
        for i in range(mip_ct):
            for j in range(sub_bitmap_ct):
                b = sub_bitmap_indexes[j]
                self._images[(b, i, c)] = image_list[i*sub_bitmap_ct + j]

        for i in range(len(mip_levels)):
            for j in range(sub_bitmap_ct):
                key = (sub_bitmap_indexes[j], mip_levels[i], c)
                new_images[key] = self._images[key]

        return new_images

    def get_images(self, mip_levels="all", sub_bitmap_indexes="all"):
        if sub_bitmap_indexes == "all":
            sub_bitmap_indexes = range(self.max_sub_bitmap + 1)
        elif isinstance(sub_bitmap_indexes, int):
            sub_bitmap_indexes = (sub_bitmap_indexes, )

        if mip_levels == "all":
            mip_levels = range(self.max_mipmap + 1)
        elif isinstance(mip_levels, int):
            mip_levels = (mip_levels, )

        sub_bitmap_indexes = list(sub_bitmap_indexes)
        mip_levels         = list(mip_levels)
        req_images         = {}

        c = frozenset((k, v) for k, v in self.channels.items())
        for i in range(len(sub_bitmap_indexes) - 1, -1, -len(mip_levels)):
            b = sub_bitmap_indexes[i]
            exists = 0
            for m in mip_levels:
                image = self._images.get((b, m, c))
                req_images[(b, m, c)] = image
                exists += image is not None

            if exists == len(mip_levels):
                sub_bitmap_indexes.pop(i)

        if sub_bitmap_indexes:
            for k, v in self.load_images(
                    mip_levels, sub_bitmap_indexes).items():
                req_images[k] = v

        return req_images

    @property
    def tex_type(self): return self.arby.texture_type
    @property
    def tex_format(self): return self.arby.format
    @property
    def max_sub_bitmap(self): return self.arby.sub_bitmap_count - 1
    @property
    def max_mipmap(self): return self.arby.mipmap_count
    @property
    def channel_count(self):
        fmt = self.arby.format
        if fmt in arbytmap.THREE_CHANNEL_FORMATS:
            return 3
        return arbytmap.CHANNEL_COUNTS[fmt]

    def mip_width(self, mip_level):
        return max(self.arby.width // (1<<mip_level), 1)

    def mip_height(self, mip_level):
        return max(self.arby.height // (1<<mip_level), 1)

    def mip_depth(self, mip_level):
        return max(self.arby.depth // (1<<mip_level), 1)


class BitmapDisplayFrame(BinillaWidget, tk.Frame):
    app_root = None
    root_frame_id = None

    bitmap_index  = None  # index of the bitmap being displayed
    mipmap_index  = None  # the mip level to display of that bitmap
    channel_index = None  # how to display the bitmap:
    #                       0=RGB or L, 1=A, 2=ARGB or AL, 3=R, 4=G, 5=B
    depth_index   = None  # since 3d bitmaps must be viewed in 2d slices,
    #                       this is the depth of the slice to display.
    cube_display_index = None  # mode to display the cubemap in:
    #                            0 == horizontal, 1 == vertical,
    #                            2 == linear strip

    prev_bitmap_index = None
    prev_mipmap_index = None
    prev_channel_index = None
    prev_depth_index = None
    prev_cube_display_index = None
    changing_settings = False

    curr_depth = 0
    depth_canvas = None
    depth_canvas_id = None
    depth_canvas_image_id = None

    cubemap_cross_mapping = (
        (-1,  2),
        ( 1,  4,  0,  5),
        (-1,  3),
        )

    cubemap_strip_mapping = (
        (0, 1, 2, 3, 4, 5),
        )

    _image_handlers = None
    image_canvas_ids = ()  # does NOT include the depth_canvas_id
    textures = ()  # List of textures ready to be loaded into arbytmap.
    # Structure is as follows:  [ (tex_block0, tex_info0),
    #                             (tex_block1, tex_info1),
    #                             (tex_block2, tex_info2), ... ]

    temp_root = os.path.join(tempfile.gettempdir(), "arbytmaps")
    temp_dir = ''

    def __init__(self, master, *args, **kwargs):
        BinillaWidget.__init__(self)
        self.temp_root = kwargs.pop('temp_root', self.temp_root)
        textures = kwargs.pop('textures', ())
        app_root = kwargs.pop('app_root', ())

        self.image_canvas_ids = []
        self.textures = []
        self._image_handlers = {}

        temp_name = str(int(random.random() * (1<<32)))
        self.temp_dir = os.path.join(self.temp_root, temp_name)

        kwargs.update(relief='flat', bd=self.frame_depth,
                      bg=self.default_bg_color)
        tk.Frame.__init__(self, master, *args, **kwargs)

        self.bitmap_index  = tk.IntVar(self)
        self.mipmap_index  = tk.IntVar(self)
        self.depth_index   = tk.IntVar(self)
        self.channel_index = tk.IntVar(self)
        self.cube_display_index = tk.IntVar(self)
        self.root_canvas = tk.Canvas(self, highlightthickness=0)
        self.root_frame = tk.Frame(self.root_canvas, highlightthickness=0)

        # create the root_canvas and the root_frame within the canvas
        self.controls_frame0 = tk.Frame(self.root_frame, highlightthickness=0)
        self.controls_frame1 = tk.Frame(self.root_frame, highlightthickness=0)
        self.controls_frame2 = tk.Frame(self.root_frame, highlightthickness=0)
        self.image_root_frame = tk.Frame(self.root_frame, highlightthickness=0)
        self.image_canvas = tk.Canvas(self.image_root_frame,
                                      highlightthickness=0,
                                      bg=self.bitmap_canvas_bg_color)
        self.depth_canvas = tk.Canvas(self.image_canvas, highlightthickness=0,
                                      bg=self.bitmap_canvas_bg_color)

        self.bitmap_menu  = ScrollMenu(self.controls_frame0, menu_width=7,
                                       variable=self.bitmap_index)
        self.mipmap_menu  = ScrollMenu(self.controls_frame1, menu_width=7,
                                       variable=self.mipmap_index)
        self.depth_menu   = ScrollMenu(self.controls_frame2, menu_width=7,
                                       variable=self.depth_index)
        self.channel_menu = ScrollMenu(self.controls_frame0, menu_width=9,
                                       variable=self.channel_index)
        self.cube_display_menu = ScrollMenu(self.controls_frame1, menu_width=9,
                                            variable=self.cube_display_index,
                                            options=("cross", "linear"))
        self.save_button = tk.Button(self.controls_frame2, width=11,
                                     text="Browse", command=self.save_as)
        self.depth_menu.default_text = self.mipmap_menu.default_text =\
                                       self.bitmap_menu.default_text =\
                                       self.channel_menu.default_text =\
                                       self.cube_display_menu.default_text = ""

        labels = []
        labels.append(tk.Label(self.controls_frame0, text="Bitmap index"))
        labels.append(tk.Label(self.controls_frame1, text="Mipmap level"))
        labels.append(tk.Label(self.controls_frame2, text="Depth level"))
        labels.append(tk.Label(self.controls_frame0, text="Channels"))
        labels.append(tk.Label(self.controls_frame1, text="Cubemap display"))
        labels.append(tk.Label(self.controls_frame2, text="Save to file"))
        for lbl in labels:
            lbl.config(width=15, anchor='w',
                       bg=self.default_bg_color, fg=self.text_normal_color,
                       disabledforeground=self.text_disabled_color)

        self.hsb = tk.Scrollbar(self, orient="horizontal",
                                command=self.root_canvas.xview)
        self.vsb = tk.Scrollbar(self, orient="vertical",
                                command=self.root_canvas.yview)
        self.root_canvas.config(xscrollcommand=self.hsb.set, xscrollincrement=1,
                                yscrollcommand=self.vsb.set, yscrollincrement=1)
        for w in [self.root_frame, self.root_canvas, self.image_canvas,
                  self.controls_frame0, self.controls_frame1,
                  self.controls_frame2] + labels:
            if e_c.IS_LNX:
                w.bind('<Shift-4>', self.mousewheel_scroll_x)
                w.bind('<Shift-5>', self.mousewheel_scroll_x)
                w.bind('<4>',       self.mousewheel_scroll_y)
                w.bind('<5>',       self.mousewheel_scroll_y)
            else:
                w.bind('<Shift-MouseWheel>', self.mousewheel_scroll_x)
                w.bind('<MouseWheel>',       self.mousewheel_scroll_y)

        # pack everything
        # pack in this order so scrollbars aren't shrunk
        self.root_frame_id = self.root_canvas.create_window(
            (0, 0), anchor="nw", window=self.root_frame)
        self.hsb.pack(side='bottom', fill='x', anchor='nw')
        self.vsb.pack(side='right', fill='y', anchor='nw')
        self.root_canvas.pack(fill='both', anchor='nw', expand=True)
        self.controls_frame0.pack(side='top', fill='x', anchor='nw')
        self.controls_frame1.pack(side='top', fill='x', anchor='nw')
        self.controls_frame2.pack(side='top', fill='x', anchor='nw')
        self.image_root_frame.pack(fill='both', anchor='nw', expand=True)
        self.image_canvas.pack(fill='both', side='right',
                               anchor='nw', expand=True)

        padx = self.horizontal_padx
        pady = self.horizontal_pady
        for lbl in labels[:3]:
            lbl.pack(side='left', padx=(25, 0), pady=pady)
        self.bitmap_menu.pack(side='left', padx=padx, pady=pady)
        self.mipmap_menu.pack(side='left', padx=padx, pady=pady)
        self.depth_menu.pack(side='left', padx=padx, pady=pady)
        for lbl in labels[3:]:
            lbl.pack(side='left', padx=(15, 0), pady=pady)
        self.save_button.pack(side='left', padx=padx, pady=pady)
        self.channel_menu.pack(side='left', padx=padx, pady=pady)
        self.cube_display_menu.pack(side='left', padx=padx, pady=pady)

        self.change_textures(textures)

        self.write_trace(self.bitmap_index, self.settings_changed)
        self.write_trace(self.mipmap_index, self.settings_changed)
        self.write_trace(self.depth_index, self.settings_changed)
        self.write_trace(self.cube_display_index, self.settings_changed)
        self.write_trace(self.channel_index, self.settings_changed)

        self.apply_style()

    def destroy(self):
        try:
            self.clear_canvas()
            self.clear_depth_canvas()
        except Exception:
            pass
        try: del self.textures[:]
        except Exception: pass
        try: del self._image_handlers[:]
        except Exception: pass
        self.image_canvas_ids = self._image_handlers = None
        self.textures = None
        tk.Frame.destroy(self)
        self.delete_all_traces()
        self.delete_all_widget_refs()
        gc.collect()

    @property
    def active_image_handler(self):
        b = self.bitmap_index.get()
        if b not in range(len(self.textures)) or not import_arbytmap():
            return None
        elif b not in self._image_handlers:
            # make a new PhotoImageHandler if one doesnt exist already
            self._image_handlers[b] = PhotoImageHandler(
                self.textures[b][0], self.textures[b][1], self.temp_dir)

        return self._image_handlers[b]

    @property
    def should_update(self):
        return (self.prev_bitmap_index  != self.bitmap_index.get() or
                self.prev_mipmap_index  != self.mipmap_index.get() or
                self.prev_channel_index != self.channel_index.get())

    def mousewheel_scroll_x(self, e):
        # prevent scrolling if the root_canvas.bbox width >= canvas width
        bbox = self.root_canvas.bbox(tk.ALL)
        if not bbox or (self.root_canvas.winfo_width() >= bbox[2] - bbox[0]):
            return

        delta = getattr(self.app_root, "scroll_increment_x", 20)
        self.root_canvas.xview_scroll(int(get_mouse_delta(e) * delta), "units")

    def mousewheel_scroll_y(self, e):
        # prevent scrolling if the root_canvas.bbox height >= canvas height
        bbox = self.root_canvas.bbox(tk.ALL)
        if not bbox or (self.root_canvas.winfo_height() >= bbox[3] - bbox[1]):
            return

        delta = getattr(self.app_root, "scroll_increment_y", 20)
        self.root_canvas.yview_scroll(int(get_mouse_delta(e) * delta), "units")

    def update_scroll_regions(self):
        if not self.image_canvas_ids and not self.depth_canvas_id:
            return
        rf = self.root_frame
        region = self.image_canvas.bbox(tk.ALL)
        # bbox region isn't actually x, y, w, h, but if the
        # origin is at (0,0) we can treat it like that
        if region is None:
            x, y, w, h = (0,0,0,0)
        else:
            x, y, w, h = region

        self.image_canvas.config(scrollregion=(x, y, w, h))
        rf.update_idletasks()
        max_w = w
        total_h = h
        for widget in self.root_frame.children.values():
            if widget is not self.image_root_frame:
                max_w = max(widget.winfo_reqwidth(), max_w)
                total_h += widget.winfo_reqheight()

        self.root_canvas.itemconfigure(self.root_frame_id,
                                       width=max_w, height=total_h)
        self.root_canvas.config(scrollregion=(0, 0, max_w, total_h))

    def save_as(self, e=None, initial_dir=None):
        handler = self.active_image_handler
        if handler is None:
            return None
        fp = asksaveasfilename(
            initialdir=initial_dir, defaultextension='.dds',
            title="Save bitmap as...", parent=self,
            filetypes=(("DirectDraw surface",          "*.dds"),
                       ('Portable network graphics',   '*.png'),
                       ('Truevision graphics adapter', '*.tga'),
                       ('Raw pixel data',              '*.bin')))

        fp, ext = os.path.splitext(fp)
        if not fp:
            return
        if not ext:
            ext = ".dds"

        mip_levels = "all"
        if ext.lower() != ".dds":
            mip_levels = self.mipmap_index.get()

        handler.arby.save_to_file(output_path=fp, ext=ext, overwrite=True,
                                  mip_levels=mip_levels, bitmap_indexes="all",
                                  swizzle_mode=False)

    def clear_depth_canvas(self):
        self.depth_canvas.delete(tk.ALL)
        self.prev_depth_index = None
        self.prev_cube_display_index = None
        self.depth_canvas_image_id = None

    def clear_canvas(self):
        self.image_canvas.delete(tk.ALL)
        self.clear_depth_canvas()
        self.depth_canvas_id = None
        self.image_canvas_ids = []

    def hide_depth_canvas(self):
        if self.depth_canvas_id is not None:
            self.image_canvas.delete(self.depth_canvas_id)
            self.depth_canvas_id = None

    def show_depth_canvas(self):
        self.depth_canvas_id = self.image_canvas.create_window(
            (0, 0), anchor="nw", window=self.depth_canvas)

    def change_textures(self, textures):
        assert hasattr(textures, '__iter__')

        for tex in textures:
            assert len(tex) == 2
            assert isinstance(tex[1], dict)

        if self._image_handlers: del self._image_handlers
        if self.textures:        del self.textures[:]

        self.textures = list(textures)

        self._image_handlers = {}
        self.bitmap_index.set(0)
        self.mipmap_index.set(0)
        self.channel_index.set(0)
        self.depth_index.set(0)
        self.cube_display_index.set(0)

        self.bitmap_menu.set_options(range(len(textures)))

        self.prev_bitmap_index       = None
        self.prev_mipmap_index       = None
        self.prev_channel_index      = None
        self.prev_depth_index        = None
        self.prev_cube_display_index = None
        self.update_bitmap(force=True)

    def get_images(self):
        image_handler = self.active_image_handler
        if not image_handler: return
        images = image_handler.get_images(mip_levels=self.mipmap_index.get())
        return tuple(images[i] for i in sorted(images.keys()))

    def settings_changed(self, *args, force=False):
        handler = self.active_image_handler
        force = False
        if not handler:
            return
        elif self.changing_settings:
            return
        elif self.prev_bitmap_index != self.bitmap_index.get():
            force = True
        elif self.prev_mipmap_index != self.mipmap_index.get():
            force = True
        elif self.prev_channel_index != self.channel_index.get():
            force = True
        elif self.prev_depth_index != self.depth_index.get():
            pass
        elif self.prev_cube_display_index != self.cube_display_index.get():
            force = True
        else:
            return
        self.changing_settings = True

        max_depth = handler.mip_depth(self.mipmap_index.get())
        self.mipmap_menu.set_options(range(handler.max_mipmap + 1))
        self.depth_menu.set_options(range(max_depth))
        if self.depth_menu.sel_index > max_depth - 1:
            self.depth_menu.sel_index = max_depth - 1

        channel_count = handler.channel_count
        if channel_count <= 2:
            opts = ("Luminence", "Alpha", "AL")
        else:
            opts = ("RGB", "Alpha", "ARGB", "Red", "Green", "Blue")
        self.channel_menu.set_options(opts)

        try:
            handler.set_channel_mode(self.channel_index.get())
            self.update_bitmap(force=force)
            self.changing_settings = False
        except Exception:
            self.changing_settings = False
            raise

    def update_bitmap(self, *args, force=False):
        handler = self.active_image_handler
        if handler is None:
            return None

        tex_type = handler.tex_type
        if   tex_type == "2D":   self._display_2d_bitmap(force)
        elif tex_type == "3D":   self._display_3d_bitmap(force)
        elif tex_type == "CUBE": self._display_cubemap(force)

        self.prev_bitmap_index  = self.bitmap_index.get()
        self.prev_mipmap_index  = self.mipmap_index.get()
        self.prev_channel_index = self.channel_index.get()
        self.prev_depth_index   = self.depth_index.get()
        self.prev_cube_display_index = self.cube_display_index.get()

    def _display_cubemap(self, force=False):
        images = self.get_images()
        if not images or not(self.should_update or force): return
        w = max(image.width()  for image in images)
        h = max(image.height() for image in images)

        max_column_ct = 0
        mapping_type = self.cube_display_index.get()
        if mapping_type == 0:
            face_mapping = self.cubemap_cross_mapping
        else:
            face_mapping = self.cubemap_strip_mapping

        self.clear_canvas()
        y = 0
        for line in face_mapping:
            max_column_ct = max(max_column_ct, len(line))
            x = 0
            for face_index in line:
                if face_index in range(len(images)):
                    # place the cube face on the canvas
                    self.image_canvas_ids.append(
                        self.image_canvas.create_image(
                            (x, y), anchor="nw", image=images[face_index],
                            tags=("BITMAP", "CUBE_FACE")))
                x += w
            y += h
        self.update_scroll_regions()

    def _display_2d_bitmap(self, force=False):
        images = self.get_images()
        if not images or not(self.should_update or force): return

        self.clear_canvas()
        # place the bitmap on the canvas
        self.image_canvas_ids.append(
            self.image_canvas.create_image((0, 0), anchor="nw", image=images[0],
                                           tags=("BITMAP", "2D_BITMAP")))
        self.update_scroll_regions()

    def _display_3d_bitmap(self, force=False):
        if self.should_update or self.depth_canvas_image_id is None or force:
            self.clear_canvas()
            self.show_depth_canvas()
            handler = self.active_image_handler
            images  = self.get_images()
            if not(images and handler): return
            m = self.mipmap_index.get()
            w, h = images[0].width(), handler.mip_height(m)
            self.curr_depth = handler.mip_depth(m)

            # place the bitmap on the canvas
            self.depth_canvas_image_id = self.depth_canvas.create_image(
                (0, 0), anchor="nw", image=images[0],
                tags=("BITMAP", "3D_BITMAP"))
            self.image_canvas.itemconfig(self.depth_canvas_id,
                                         width=w, height=h)
            self.depth_canvas.config(scrollregion="0 0 %s %s" % (w, h))
            self.update_scroll_regions()

        self.depth_canvas.coords(self.depth_canvas_image_id,
                                 (0, -self.depth_index.get()*self.curr_depth))


class BitmapDisplayButton(BinillaWidget, tk.Button):
    bitmap_tag = None
    display_frame = None
    display_frame_class = BitmapDisplayFrame

    def __init__(self, master, *args, **kwargs):
        BinillaWidget.__init__(self)
        self.change_bitmap(kwargs.pop('bitmap_tag', None))
        kwargs.setdefault("command", self.show_window)
        kwargs.setdefault("text", "Bitmap preview")
        kwargs.setdefault("bg", self.button_color)
        kwargs.setdefault("fg", self.text_normal_color)
        kwargs.setdefault("disabledforeground", self.text_disabled_color)
        kwargs.setdefault("bd", self.button_depth)
        tk.Button.__init__(self, master, *args, **kwargs)

    def change_bitmap(self, bitmap_tag):
        if bitmap_tag is not None:
            self.bitmap_tag = bitmap_tag

        f = self.display_frame
        if f is not None and f() is not None:
            f().change_textures(self.get_textures(self.bitmap_tag))

    def get_textures(self, bitmap_tag):
        raise NotImplementedError("This method must be overloaded.")

    def destroy(self, e=None):
        self.bitmap_tag = None
        self.f_widget_parent = None
        tk.Button.destroy(self)
        self.delete_all_traces()
        self.delete_all_widget_refs()

    def show_window(self, e=None, parent=None):
        if parent is None:
            parent = self
        w = tk.Toplevel()
        self.display_frame = weakref.ref(self.display_frame_class(w))
        self.display_frame().change_textures(self.get_textures(self.bitmap_tag))
        self.display_frame().pack(expand=True, fill="both")
        w.transient(parent)
        try:
            #tag_name = self.bitmap_tag().filepath
            tag_name = self.bitmap_tag.filepath
        except Exception:
            tag_name = "untitled"
        w.title("Preview: %s" % tag_name)
        w.focus_force()
        return w
