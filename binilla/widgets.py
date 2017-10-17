'''
This module contains various widgets which the FieldWidget classes utilize.
'''
import os
import tempfile
import random
from time import time
from traceback import format_exc

from . import threadsafe_tkinter as tk
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

    tooltip_string = None
    f_widget_parent = None

    def should_scroll(self, e):
        '''
        Returns True if the widget should have its scrolling method
        follow through when it is invoked. Returns False otherwise.
        '''
        hover = self.winfo_containing(e.x_root, e.y_root)

        if not(hasattr(hover, 'can_scroll') and hover.can_scroll):
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


class ScrollMenu(tk.Frame, BinillaWidget):
    '''
    Used as a menu for certain FieldWidgets, such as when
    selecting an array element or an enumerator option.
    '''
    disabled = False
    sel_index = None
    option_box = None
    max_height = None
    max_index = 0

    options_sane = False
    selecting = False  # prevents multiple selections at once

    can_scroll = True
    option_box_visible = False
    click_outside_funcid = None

    default_entry_text = None

    menu_width = BinillaWidget.scroll_menu_width

    def __init__(self, *args, **kwargs):
        self.sel_index = kwargs.pop('sel_index', -1)
        self.max_index = kwargs.pop('max_index', self.max_index)
        self.max_height = kwargs.pop('max_height', self.max_height)
        self.f_widget_parent = kwargs.pop('f_widget_parent', None)
        self.menu_width = kwargs.pop('menu_width', self.menu_width)
        self.options_sane = kwargs.pop('options_sane', False)
        self.default_entry_text = kwargs.pop(
            'default_entry_text', e_c.INVALID_OPTION)
        disabled = kwargs.pop('disabled', False)

        if self.max_height is None:
            self.max_height = self.scroll_menu_max_height

        kwargs.update(relief='sunken', bd=self.listbox_depth,
                      bg=self.default_bg_color)
        tk.Frame.__init__(self, *args, **kwargs)

        self.sel_label = tk.Label(
            self, bg=self.enum_normal_color, fg=self.text_normal_color,
            bd=2, relief='groove', width=self.menu_width)
        # the button_frame is to force the button to be a certain size
        self.button_frame = tk.Frame(self, relief='flat', height=18, width=18,
                                     bd=0, bg=self.default_bg_color)
        self.button_frame.pack_propagate(0)
        self.arrow_button = tk.Button(
            self.button_frame, bd=self.button_depth, text="▼", width=1,
            bg=self.button_color, activebackground=self.button_color,
            fg=self.text_normal_color)
        self.sel_label.pack(side="left", fill="both", expand=True)
        self.button_frame.pack(side="left", fill=None, expand=False)
        self.arrow_button.pack(side="left", fill='both', expand=True)

        # make the option box to populate
        self.option_frame = tk.Frame(
            self.winfo_toplevel(), highlightthickness=0, bd=0)
        self.option_frame.pack_propagate(0)
        self.option_bar = tk.Scrollbar(self.option_frame, orient="vertical")
        self.option_box = tk.Listbox(
            self.option_frame, highlightthickness=0,
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

    def _mousewheel_scroll(self, e):
        if not self.should_scroll(e) or (self.option_box_visible or
                                         self.disabled):
            return
        elif e.delta > 0:
            self.decrement_sel()
        elif e.delta < 0:
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
        sel_index = [int(i) - 1 for i in self.option_box.curselection()]
        if sel_index < 0:
            new_index = 0
        try:
            self.selecting = True
            self.option_box.select_clear(0, tk.END)
            self.sel_index = sel_index
            self.option_box.select_set(sel_index)
            self.option_box.see(sel_index)
            self.f_widget_parent.select_option(sel_index)
            self.selecting = False
        except Exception:
            self.selecting = False
            raise

    def decrement_sel(self, e=None):
        if self.selecting:
            return
        new_index = self.sel_index - 1
        if new_index < 0:
            new_index = 0
        try:
            self.selecting = True
            self.sel_index = new_index
            self.f_widget_parent.select_option(new_index)
            self.selecting = False
        except Exception:
            self.selecting = False
            raise

    def destroy(self):
        if self.click_outside_funcid is not None:
            self.winfo_toplevel().unbind('<Button>', self.click_outside_funcid)
        tk.Frame.destroy(self)

    def deselect_option_box(self, e=None):
        if self.disabled:
            self.config(bg=self.enum_disabled_color)
            self.sel_label.config(bg=self.enum_disabled_color,
                                  fg=self.text_disabled_color)
        else:
            self.config(bg=self.enum_normal_color)
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
        sel_index = [int(i) + 1 for i in self.option_box.curselection()]
        if sel_index > self.max_index:
            new_index = self.max_index
        try:
            self.selecting = True
            self.option_box.select_clear(0, tk.END)
            self.sel_index = sel_index
            self.option_box.select_set(sel_index)
            self.option_box.see(sel_index)
            self.f_widget_parent.select_option(sel_index)
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
            self.f_widget_parent.select_option(new_index)
            self.selecting = False
        except Exception:
            self.selecting = False
            raise

    def select_menu(self, e=None):
        sel_index = [int(i) for i in self.option_box.curselection()]
        if not sel_index:
            return
        self.sel_index = sel_index[0]
        self.f_widget_parent.select_option(self.sel_index)
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
        option_cnt = self.max_index + 1

        if not self.options_sane:
            options = self.f_widget_parent.options
            END = tk.END
            self.option_box.delete(0, END)
            insert = self.option_box.insert
            def_str = '%s' + ('. %s' % self.default_entry_text)
            for i in range(option_cnt):
                if i in options:
                    insert(END, options[i])
                else:
                    insert(END, def_str % i)

            self.options_sane = True

        self.option_box.pack(side='left', expand=True, fill='both')

        self_height = self.winfo_reqheight()
        root = self.winfo_toplevel()

        pos_x = self.sel_label.winfo_rootx() - root.winfo_x()
        pos_y = self.winfo_rooty() + self_height - root.winfo_y()
        height = min(option_cnt, self.max_height)*(14 + win_10_pad) + 4
        width = (self.sel_label.winfo_width() +
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
            pos_y = pos_y - self_height - height + 4

        # pack the scrollbar is there isnt enough room to display the list
        if option_cnt > self.max_height or (height - 4)//14 < option_cnt:
            self.option_bar.pack(side='left', fill='y')
        else:
            # place it off the frame so it can still be used for key bindings
            self.option_bar.place(x=pos_x + width, y=pos_y, anchor=tk.NW)
        self.option_bar.focus_set()
        self.option_frame.place(x=pos_x - 4, y=pos_y - 32, anchor=tk.NW,
                                height=height, width=width)
        # make a binding to the parent Toplevel to remove the
        # options box if the mouse is clicked outside of it.
        self.click_outside_funcid = self.winfo_toplevel().bind(
            '<Button>', lambda e, s=self: s.click_outside_option_box(e))
        self.option_box_visible = True

        if self.sel_index >= option_cnt:
            self.sel_index = self.max_index

        self.option_box.select_clear(0, tk.END)
        try:
            self.option_box.select_set(self.sel_index)
            self.option_box.see(self.sel_index)
        except Exception:
            pass

    def update_label(self):
        if self.sel_index == -1:
            option = ''
        else:
            option = self.f_widget_parent.get_option()
            if option is None:
                option = '%s. %s' % (self.sel_index, self.default_entry_text)
        self.sel_label.config(text=option, anchor="w")


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
            try: self.tip_window.geometry("+%s+%s" % (
                mouse_x + self.tip_offset_x, mouse_y + self.tip_offset_y))
            except Exception: pass

        focus = root.winfo_containing(mouse_x, mouse_y)

        # get the widget in focus if nothing is under the mouse
        #if tip_widget is None:
        #    focus = root.focus_get()

        try: tip_text = focus.tooltip_string
        except Exception: tip_text = None

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
    _arby = None
    _images = None  # loaded and cached PhotoImages

    def __init__(self, tex_block=None, tex_info=None, temp_path=""):
        if not import_arbytmap():
            raise ValueError(
                "Arbytmap is not loaded. Cannot generate PhotoImages.")
        self._arby = arbytmap.Arbytmap()
        self._images = {}
        self.temp_path = temp_path

        if tex_block and tex_info:
            self.load_texture(tex_block, tex_info)

    def load_texture(self, tex_block, tex_info):
        self._arby.load_new_texture(texture_block=tex_block,
                                    texture_info=tex_info)

    def set_single_channel_mode(self, channel):
        assert channel in (None, -1, 0, 1, 2, 3)
        # FINISH THIS

    def load_images(self, mip_levels="all", sub_bitmap_indexes="all"):
        if not self.temp_path:
            raise ValueError("Cannot create PhotoImages without a specified "
                             "temporary filepath to save their PNG's to.")

        if not bitmap_indexes and not mip_levels:
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
        image_list = self._arby.make_photoimages(self.temp_path,
            bitmap_indexes=sub_bitmap_indexes, mip_levels=mip_levels)

        for i in range(0, len(image_list), len(mip_levels)):
            b = sub_bitmap_indexes[i]

            for m in mip_levels:
                key = (b, self.mip_width(m),
                       self.mip_height(m), self.mip_depth(m))
                new_images[key] = new_images[(b, m)] = image_list[i + m]

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

        bitmap_indexes = list(bitmap_indexes)
        mip_levels     = list(mip_levels)
        req_images     = {}

        for i in range(len(sub_bitmap_indexes) - 1, -1, -1*len(mip_levels)):
            b = sub_bitmap_indexes[i]
            key = None

            for m in mip_levels:
                key = (b, self.mip_width(m),
                       self.mip_height(m), self.mip_depth(m))
                req_images[key] = req_images[(b, m)] = self._images.get(key)

            if req_images.get(key):
                bitmap_indexes.pop(i)

        if bitmap_indexes:
            for k, v in self.load_images(mip_levels,
                                         sub_bitmap_indexes).items():
                req_images[k] = v

        return req_images

    @property
    def tex_typ(self): return self._arby.texture_type
    @property
    def tex_fmt(self): return self._arby.format
    @property
    def max_sub_bitmap(self): return self._arby.sub_bitmap_count - 1
    @property
    def max_mipmap(self): return self._arby.mipmap_count

    def mip_width(self, mip_level):
        return max(self._arby.width // (1<<mip_level), 1)

    def mip_height(self, mip_level):
        return max(self._arby.width // (1<<mip_level), 1)

    def mip_depth(self, mip_level):
        return max(self._arby.width // (1<<mip_level), 1)


class BitmapDisplayFrame(BinillaWidget, tk.Frame):
    app_root = None

    bitmap_index  = None
    mipmap_index  = None
    channel_index = None  # 0 == RGB or I, 1 == A, 2 == R, 3 == G, 4 == B
    depth_index   = None
    prev_depth_index   = None
    cube_display_index = None

    depth_canvas = None
    depth_canvas_id = None
    depth_canvas_image_id = None

    cubemap_horizontal_mapping = (
        (-1,  2),
        ( 1,  4,  0,  5),
        (-1,  3),
        )

    cubemap_vertical_mapping = (
        (-1,  2),
        ( 4,  0,  5),
        (-1,  3),
        (-1,  1),
        )

    cubemap_strip_mapping = (
        (0, 1, 2, 3, 4, 5),
        )

    _image_handlers = ()
    image_canvas_ids = ()  # does NOT include the depth_canvas_id
    texture_names = ()
    textures = ()  # List of textures ready to be loaded into arbytmap.
    # Structure is as follows:  [ (tex_block0, tex_info0),
    #                             (tex_block1, tex_info1),
    #                             (tex_block2, tex_info2), ... ]

    temp_root = os.path.join(tempfile.gettempdir(), "arbytmaps")
    temp_dir = ''

    def __init__(self, master, *args, **kwargs):
        self.app_root = kwargs.pop('app_root', master)
        self.temp_root = kwargs.pop('temp_root', self.temp_root)
        textures = kwargs.pop('textures', ())
        texture_names = kwargs.pop('texture_names', ())
        self.image_canvas_ids = []
        self._image_handlers = []

        try:
            xscroll_inc = self.app_root.scroll_increment_x
            yscroll_inc = self.app_root.scroll_increment_y
        except AttributeError:
            xscroll_inc = yscroll_inc = 20
        temp_name = str(int(random.random() * (1<<32)))
        self.temp_dir = os.path.join(self.temp_root, temp_name)

        kwargs.update(relief='sunken', bd=self.frame_depth,
                      bg=self.frame_bg_color)
        tk.Frame.__init__(self, master, *args, **kwargs)

        # create the root_canvas and the root_frame within the canvas
        self.controls_frame = tk.Frame(self, highlightthickness=0,
                                       bg=self.default_bg_color)
        self.image_root_frame = tk.Frame(self, highlightthickness=0,
                                          bg=self.default_bg_color)
        self.image_canvas = rc = tk.Canvas(self.image_root_frame,
                                           highlightthickness=0,
                                           bg=self.default_bg_color)
        self.depth_canvas = tk.Canvas(self.image_canvas, highlightthickness=0,
                                      bg=self.default_bg_color)

        self.bitmap_index  = tk.IntVar(self)
        self.mipmap_index  = tk.IntVar(self)
        self.channel_index = tk.IntVar(self)
        self.depth_index   = tk.IntVar(self)
        self.cube_display_index = tk.IntVar(self)

        self.set_textures(textures, texture_names)

        self.bind('<Shift-MouseWheel>', self.mousewheel_scroll_x)
        self.bind('<MouseWheel>',       self.mousewheel_scroll_y)
        self.hsb = tk.Scrollbar(self, orient="horizontal", command=rc.xview)
        self.vsb = tk.Scrollbar(self.image_root_frame,
                                orient="vertical", command=rc.yview)
        rc.config(xscrollcommand=self.hsb.set, xscrollincrement=xscroll_inc,
                  yscrollcommand=self.vsb.set, yscrollincrement=yscroll_inc)

        # pack everything
        # pack in this order so scrollbars aren't shrunk
        self.hsb.pack(side='bottom', fill='x', anchor='nw')
        self.controls_frame.pack(side='top', fill='x', anchor='nw')
        self.image_root_frame.pack(fill='both', anchor='nw', expand=True)
        self.vsb.pack(fill='y', side='right', anchor='nw')
        self.image_canvas.pack(fill='both', side='right',
                               anchor='nw', expand=True)

    @property
    def active_image_handler(self):
        pass

    def mousewheel_scroll_x(self, e):
        if self.should_scroll(e):
            self.xview_scroll(e.delta//60, "units")

    def mousewheel_scroll_y(self, e):
        if self.should_scroll(e):
            self.yview_scroll(e.delta//-120, "units")

    def clear_depth_canvas(self):
        self.depth_canvas.delete("all")
        self.prev_depth_index = None
        self.depth_canvas_image_id = None

    def clear_canvas(self):
        self.image_canvas.delete("all")
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

    def set_textures(self, textures, names=()):
        assert hasattr(textures, '__iter__')
        assert isinstance(names, (list, tuple))
        names = list(names)
        names.extend((None, )*(len(textures) - len(names)))

        for tex in textures:
            assert len(tex) == 2
            assert len(tex[0]) == len(tex[1])
            assert isinstance(tex[1], dict)

        self.clear_depth_canvas()
        del self._image_handlers[:]
        self.bitmap_index.set(-1)
        self.mipmap_index.set(0)
        self.channel_index.set(0)
        self.depth_index.set(0)
        self.cube_display_index.set(0)

        self.textures = textures
        self.texture_names = names

    def display_cubemap(self):
        self.clear_canvas()
        self.hide_depth_canvas()

        image_handler = self.active_image_handler()
        if not image_handler: return
        images = asdf
        if not images: return
        canvas = self.image_canvas
        w, h = images[0].width(), images[0].height()
        for image in images:
            assert image.width() == w
            assert image.height() == h

        max_column_ct = 0
        mapping_type = self.cube_display_index.get()
        if mapping_type == 0:
            face_mapping = self.cubemap_horizontal_mapping
        elif mapping_type == 1:
            face_mapping = self.cubemap_vertical_mapping
        else:
            face_mapping = self.cubemap_strip_mapping

        y = 0
        for line in face_mapping:
            max_column_ct = max(max_column_ct, len(line))
            x = 0
            for face_index in line:
                if face_index in range(len(images)):
                    # place the cube face on the canvas
                    self.image_canvas_ids.append(
                        canvas.create_image((x, y), anchor="nw",
                                            image=images[face_index],
                                            tags=("BITMAP", "CUBE_FACE")))
                x += w
            y += h

        canvas.config(scrollregion="0 0 %s %s" % (w*max_column_ct,
                                                  h*len(face_mapping)))

    def display_2d_bitmap(self):
        self.clear_canvas()
        self.hide_depth_canvas()

        image_handler = self.active_image_handler()
        if not image_handler: return
        images = asdf
        if not images: return
        image = images[0]
        # place the bitmap on the canvas
        self.image_canvas_ids.append(
            self.image_canvas.create_image((0, 0), anchor="nw", image=image,
                                           tags=("BITMAP", "2D_BITMAP")))
        self.image_canvas.config(scrollregion="0 0 %s %s" % (image.width(),
                                                             image.height()))

    def display_3d_bitmap(self):
        if self.prev_depth_index is None or self.depth_canvas_image_id is None:
            self.clear_canvas()
            self.show_depth_canvas()

            image_handler = self.active_image_handler()
            if not image_handler: return
            images = asdf
            if not images: return
            image = images[0]
            mip_level = asdf
            w, h, d = (image_handler.mip_width(mip_level),
                       image_handler.mip_height(mip_level),
                       image_handler.mip_depth(mip_level))

            # place the bitmap on the canvas
            self.depth_canvas.config(scrollregion="0 0 %s %s" % (w, h))
            self.depth_canvas_image_id = self.depth_canvas.create_image(
                (0, 0), anchor="nw", image=image, tags=("BITMAP", "3D_BITMAP"))
            self.image_canvas.item_config(self.depth_canvas_id,
                                          width=w, height=h)

        z = self.depth_index.get()
        self.depth_canvas.coords(self.depth_canvas_image_id, (0, -z*d))
        self.prev_depth_index = z


#root = tk.Tk()
#test = BitmapDisplayFrame(root)
#test.pack(expand=True, fill="both")
