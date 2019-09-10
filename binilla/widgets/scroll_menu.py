import threadsafe_tkinter as tk
import tkinter.ttk as ttk

from binilla import editor_constants as e_c
from binilla.widgets.binilla_widget import BinillaWidget
from binilla.widgets import get_mouse_delta, get_relative_widget_position


win_10_pad = 2


__all__ = ("ScrollMenu", )


class ScrollMenu(tk.Frame, BinillaWidget):
    '''
    Used as a menu for certain FieldWidgets, such as when
    selecting an array element or an enumerator option.
    '''
    variable = None
    str_variable = None
    callback = None
    option_box = None
    max_height = None
    max_index = -1

    option_cache = None
    option_getter = None
    options_menu_sane = False
    options_volatile = False
    selecting = False  # prevents multiple selections at once

    can_scroll = True
    option_box_visible = False
    click_outside_funcid = None

    default_text = None

    menu_width = None

    def __init__(self, *args, **kwargs):
        BinillaWidget.__init__(self)

        sel_index = kwargs.pop('sel_index', -1)
        disabled = kwargs.pop('disabled', False)

        options = kwargs.pop('options', None)
        self.can_scroll = kwargs.pop('can_scroll', self.can_scroll)
        self.option_getter = kwargs.pop('option_getter', None)
        self.callback = kwargs.pop('callback', None)
        self.variable = kwargs.pop('variable', None)
        self.str_variable = kwargs.pop('str_variable', None)
        self.max_index = kwargs.pop('max_index', self.max_index)
        self.max_height = kwargs.pop('max_height', self.max_height)
        self.f_widget_parent = kwargs.pop('f_widget_parent', None)
        self.menu_width = kwargs.pop('menu_width', 0)
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

        menu_width = self.menu_width if self.menu_width else self.scroll_menu_width
        self.sel_label = tk.Label(
            self, bg=self.enum_normal_color, fg=self.text_normal_color,
            bd=2, relief='groove',
            width=max(min(menu_width, self.scroll_menu_max_width), 1))
        # the button_frame is to force the button to be a certain size
        self.button_frame = tk.Frame(self, relief='flat', height=18, width=18, bd=0)
        self.button_frame.pack_propagate(0)
        self.arrow_button = tk.Button(self.button_frame, text="▼", width=2)
        self.arrow_button.font_type = "fixed_small"
        self.arrow_button.pack()
        #self.arrow_button = ttk.Button(self.button_frame, text="▼", width=2)
        #self.arrow_button.grid(row=1, column=1, sticky='news',
        #                       ipadx=0, ipady=0, padx=0, pady=0)
        self.sel_label.pack(side="left", fill="both", expand=True)
        self.button_frame.pack(side="left", fill="both")

        # make the option box to populate
        option_frame_root = self.winfo_toplevel()
        if hasattr(option_frame_root, "root_frame"):
            option_frame_root = option_frame_root.root_frame

        self.option_frame = tk.Frame(
            option_frame_root, highlightthickness=0, bd=0)
        self.option_frame.pack_propagate(0)
        self.option_bar = tk.Scrollbar(self.option_frame, orient="vertical")
        self.option_box = tk.Listbox(
            self.option_frame, highlightthickness=0, exportselection=False,
            bg=self.enum_normal_color, fg=self.text_normal_color,
            selectbackground=self.enum_highlighted_color,
            selectforeground=self.text_highlighted_color,
            yscrollcommand=self.option_bar.set, width=menu_width)
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

        self.set_disabled(disabled)

        if options is not None:
            self.set_options(options)

        if self.str_variable is None:
            self.str_variable = tk.StringVar(self, "")

    def apply_style(self, seen=None):
        BinillaWidget.apply_style(self, seen)
        if self.disabled:
            bg = self.entry_disabled_color
            fg = self.text_disabled_color
        else:
            bg = self.enum_normal_color
            fg = self.text_normal_color

        menu_width = self.menu_width if self.menu_width else self.scroll_menu_width
        self.sel_label.config(
            bg=bg, fg=fg, width=max(min(menu_width, self.scroll_menu_max_width), 1))
        self.option_box.config(width=menu_width)

    @property
    def sel_index(self):
        return self.variable.get()

    @sel_index.setter
    def sel_index(self, new_val):
        self.variable.set(new_val)
        self.str_variable.set(self.sel_name)
        # not necessary to call update_label as there is a
        # write_trace to call it if the sel_index is touched
        #self.update_label()

    @property
    def sel_name(self):
        if self.sel_index < 0:
            return ""
        text = self.get_option()
        if text is None:
            text = '%s. %s' % (self.sel_index, self.default_text)
        return text

    def get_option(self, opt_index=None):
        if opt_index in (None, e_c.ACTIVE_ENUM_NAME):
            opt_index = self.sel_index

        assert isinstance(opt_index, (int, str))
        if self.option_getter is not None:
            return self.option_getter(opt_index)
        elif self.option_cache is None:
            self.option_cache = {}

        return self.option_cache.get(opt_index)

    def get_options(self):
        if self.option_getter is not None:
            return self.option_getter()
        elif self.option_cache is None:
            self.option_cache = {}

        return self.option_cache

    def set_options(self, new_options):
        if (not isinstance(new_options, dict) and
                hasattr(new_options, "__iter__")):
            new_options = {i: new_options[i] for i in range(len(new_options))}
        self.option_cache = dict(new_options)
        self.max_index = len(new_options) - 1
        self.options_menu_sane = False
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
            self.deselect_option_box()

    def decrement_listbox_sel(self, e=None):
        if self.selecting:
            return
        sel_indices = self.option_box.curselection()
        if not sel_indices:
            return
        new_index = sel_indices[0] - 1
        if new_index < 0:
            new_index = (self.max_index >= 0) - 1

        try:
            self.selecting = True
            self.option_box.select_clear(0, tk.END)
            self.option_box.select_set(new_index)
            self.option_box.see(new_index)
            self.sel_index = new_index
            if self.callback is not None:
                self.callback(new_index)
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

    def set_disabled(self, disable=True):
        if disable:
            self.disable()
        else:
            self.enable()

    def disable(self):
        if self.disabled:
            return
        BinillaWidget.set_disabled(self, True)
        self.config(bg=self.enum_disabled_color)
        self.sel_label.config(bg=self.enum_disabled_color,
                              fg=self.text_disabled_color)
        self.arrow_button.config(state='disabled')

    def enable(self):
        if not self.disabled:
            return
        BinillaWidget.set_disabled(self, False)
        self.config(bg=self.default_bg_color)
        self.sel_label.config(bg=self.enum_normal_color,
                              fg=self.text_normal_color)
        self.arrow_button.config(state='normal')

    def increment_listbox_sel(self, e=None):
        if self.selecting:
            return
        sel_indices = self.option_box.curselection()
        if not sel_indices:
            return
        new_index = sel_indices[0] + 1
        if new_index > self.max_index:
            new_index = self.max_index

        try:
            self.selecting = True
            self.option_box.select_clear(0, tk.END)
            self.option_box.select_set(new_index)
            self.option_box.see(new_index)
            self.sel_index = new_index
            if self.callback is not None:
                self.callback(new_index)
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

        if not self.options_menu_sane or self.options_volatile:
            END = tk.END
            self.option_box.delete(0, END)
            insert = self.option_box.insert
            def_str = '%s' + ('. %s' % self.default_text)
            menu_width = self.menu_width if self.menu_width else\
                         self.scroll_menu_width
            for i in range(option_cnt):
                if i in options:
                    insert(END, options[i])
                else:
                    insert(END, def_str % i)

            self.options_menu_sane = True
            self.sel_label.config(width=menu_width)

        # explicitly forget these so they can be repacked properly
        self.option_bar.pack_forget()
        self.option_box.pack_forget()
        self.option_bar.pack(side='right', fill='y')
        self.option_box.pack(side='right', expand=True, fill='both')
        #self.update()

        self_height = self.winfo_reqheight()
        root = self.winfo_toplevel()

        pos_x, pos_y = get_relative_widget_position(
            self.sel_label, self.option_frame.master)
        pos_y += self_height - 4
        height = min(max(option_cnt, 0), self.max_height)*(14 + win_10_pad) + 4
        width = max(self.option_box.winfo_reqwidth(),
                    self.sel_label.winfo_width() +
                    self.arrow_button.winfo_width())

        # figure out how much space is above and below where the list will be
        space_above = pos_y - self_height
        space_below = self.option_frame.master.winfo_height() - pos_y

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
            pos_y -= self_height + height

        # unpack the scrollbar if there is enough room to display the whole list
        if option_cnt <= self.max_height and (height - 4) // 14 >= option_cnt:
            # place it off the frame so it can still be used for key bindings
            self.option_bar.pack_forget()
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
        if not text:
            text = self.sel_name
        self.sel_label.config(text=text, anchor="w")
