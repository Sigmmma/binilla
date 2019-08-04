import math
import threadsafe_tkinter as tk

from traceback import format_exc

from binilla import editor_constants as e_c
from binilla import widgets
from binilla.widgets.field_widgets import field_widget, data_frame


class BoolFrame(data_frame.DataFrame):
    children_can_scroll = True
    can_scroll = False
    checkvars = None  # used to know which IntVars to set when undo/redoing
    checkbtns = ()
    bit_opt_map = None

    def __init__(self, *args, **kwargs):
        self.bit_opt_map = {}
        self.checkvars = {}
        self.checkbtns = {}
        data_frame.DataFrame.__init__(self, *args, **kwargs)

        self.content = tk.Frame(self, highlightthickness=0)

        self.display_comment()

        self.title_label = tk.Label(
            self.content, text=self.gui_name, width=self.title_size, anchor='w',
            disabledforeground=self.text_disabled_color,
            font=self.get_font("default"))

        if self.gui_name != '':
            self.title_label.pack(side='left')

        self.check_canvas = tk.Canvas(self.content, highlightthickness=0)
        self.check_frame = tk.Frame(
            self.check_canvas, bd=self.listbox_depth,
            relief='sunken',  highlightthickness=0)

        self.scrollbar_y = tk.Scrollbar(self.content, orient='vertical',
                                        command=self.check_canvas.yview)

        self.check_canvas.config(yscrollcommand=self.scrollbar_y.set,
                                 yscrollincrement=1, xscrollincrement=1)
        self.check_frame_id = self.check_canvas.create_window(
            (0, 0), window=self.check_frame, anchor='nw')

        if e_c.IS_LNX:
            self.check_frame.bind('<4>', self.mousewheel_scroll_y)
            self.check_frame.bind('<5>', self.mousewheel_scroll_y)
            self.check_canvas.bind('<4>', self.mousewheel_scroll_y)
            self.check_canvas.bind('<5>', self.mousewheel_scroll_y)
        else:
            self.check_frame.bind('<MouseWheel>', self.mousewheel_scroll_y)
            self.check_canvas.bind('<MouseWheel>', self.mousewheel_scroll_y)

        self.populate()
        self._initialized = True

    def unload_node_data(self):
        field_widget.FieldWidget.unload_node_data(self)
        for var in self.checkvars.values():
            var.set(0)

    def set_disabled(self, disable=True):
        disable = disable or not self.editable
        if self.node is None and not disable:
            return

        if bool(disable) != self.disabled:
            new_state = tk.DISABLED if disable else tk.NORMAL
            for bit in self.checkbtns:
                self.checkbtns[bit].config(state=new_state)

        data_frame.DataFrame.set_disabled(self, disable)

    def apply_style(self, seen=None):
        field_widget.FieldWidget.apply_style(self, seen)
        self.check_frame.config(bg=self.entry_normal_color,
                                bd=self.listbox_depth)

        for w in self.check_frame.children.values():
            if isinstance(w, tk.Checkbutton):
                w.config(bg=self.entry_normal_color, selectcolor="",
                         activebackground=self.entry_highlighted_color,
                         activeforeground=self.text_highlighted_color)

    def flush(self): pass

    def edit_apply(self=None, *, edit_state, undo=True):
        state = edit_state

        new_val = state.redo_node

        bit = state.edit_info['bit']
        mask = state.edit_info['mask']

        w, node = field_widget.FieldWidget.get_widget_and_node(nodepath=state.nodepath,
                                                  tag_window=state.tag_window)

        if undo:
            new_val = not new_val

        mask, data = 1 << bit, node.data
        node.data = data - (data & mask) + mask*bool(new_val)

        if w is not None:
            try:
                if w.desc is not state.desc:
                    return

                w.needs_flushing = False
                w.set_edited()
                w.checkvars[bit].set(new_val)
            except Exception:
                print(format_exc())

    def populate(self):
        bit_opt_map = {}

        desc = self.desc
        for w in (self, self.content, self.check_canvas,
                  self.check_frame, self.title_label):
            w.tooltip_string = self.desc.get('TOOLTIP')

        visible_bits = [int(math.log(mask, 2.0)) for mask in sorted(desc['VALUE_MAP'])]
        # create visible bits for all flags that dont have one defined
        if self.all_bools_visible:
            bit_ct = self.field_size * (1 if self.is_bit_based else 8)
            for i in range(bit_ct):
                if len(visible_bits) <= i:
                    visible_bits.extend(range(i, bit_ct))
                    break
                elif visible_bits[i] != i:
                    visible_bits.insert(i, i)

        # make a condensed mapping of all visible flags and their information
        for bit in visible_bits:
            mask = 1 << bit
            opt = desc.get(desc['VALUE_MAP'].get(mask))

            if opt is None or not self.get_visible(opt.get("VISIBLE", True)):
                if not self.all_bools_visible:
                    continue
                name = e_c.UNKNOWN_BOOLEAN % bit
                opt = dict(GUI_NAME=name.replace('_', ' '), NAME=name)
            else:
                opt = dict(opt)
                defname = opt.get('NAME', e_c.UNNAMED_FIELD).replace('_', ' ')
                opt.setdefault('GUI_NAME', defname)

            bit_opt_map[bit] = opt

        if self.bit_opt_map != bit_opt_map:
            self.checkvars = {}
            self.checkbtns = {}

            # destroy all the child widgets of the content
            for c in list(self.check_frame.children.values()):
                c.destroy()

            # loop over each possible boolean(even unused ones)
            for bit in sorted(bit_opt_map):
                opt = bit_opt_map[bit]

                name = opt.get('GUI_NAME', opt['NAME'])
                if opt.get('TOOLTIP'):
                    name += " �"

                self.checkvars[bit] = check_var = tk.IntVar(self.check_frame)
                state = tk.DISABLED
                if opt.get("EDITABLE", not self.disabled):
                    state = tk.NORMAL

                self.checkbtns[bit] = check_btn = tk.Checkbutton(
                    self.check_frame, variable=check_var, padx=0, pady=0,
                    text=name, anchor='nw', justify='left',
                    borderwidth=0, state=state,)

                check_btn.config(command=lambda b=check_btn, i=bit, v=check_var:
                                 self._check_bool(b, i, v))

                check_btn.pack(anchor='nw', fill='x', expand=True)
                check_btn.tooltip_string = opt.get('TOOLTIP')

                if e_c.IS_LNX:
                    check_btn.bind('<4>', self.mousewheel_scroll_y)
                    check_btn.bind('<5>', self.mousewheel_scroll_y)
                else:
                    check_btn.bind('<MouseWheel>', self.mousewheel_scroll_y)

            self.apply_style()
            self.bit_opt_map = bit_opt_map

        self.reload()

    def reload(self):
        data = getattr(self.node, "data", 0)

        # check/uncheck each flag
        for bit in sorted(self.bit_opt_map):
            self.checkvars[bit].set(bool(data & (1 << bit)))

    def _check_bool(self, check_btn, bit, check_var):
        check_btn.focus_set()
        self.set_bool_to(bit, check_var)

    def set_bool_to(self, bit, new_val_var):
        if self.node is None:
            return

        self.set_edited()
        mask, data, new_val = 1 << bit, self.node.data, bool(new_val_var.get())

        self.edit_create(bit=bit, mask=mask, redo_node=new_val)
        self.node.data = data - (data & mask) + mask*new_val

    def apply_style(self, seen=None):
        super(BoolFrame, self).apply_style(seen)

        for k in self.checkbtns:
            self.checkbtns[k].config(
                bg=self.entry_normal_color, fg=self.text_normal_color, 
                activebackground=self.entry_highlighted_color,
                activeforeground=self.text_highlighted_color,)
        self.pose_fields()

    def pose_fields(self):
        self.content.pack(side='left', anchor='nw')
        self.check_canvas.pack(side='left', fill='both')
        self.update()
        if not getattr(self, "check_frame", None):
            return

        width  = self.check_frame.winfo_reqwidth()
        height = self.check_frame.winfo_reqheight()

        self.check_canvas.config(scrollregion="0 0 %s %s" % (width, height))

        width  = max(width,  self.bool_frame_min_width)
        height = max(height, self.bool_frame_min_height)
        if height > self.bool_frame_max_height:
            height = self.bool_frame_max_height
            self.scrollbar_y.pack(side='left', fill="y")
            self.children_can_scroll = True
        else:
            self.scrollbar_y.forget()
            self.children_can_scroll = False

        self.check_canvas.can_scroll = self.children_can_scroll
        self.check_frame.can_scroll = self.children_can_scroll
        self.scrollbar_y.can_scroll = self.children_can_scroll

        self.check_canvas.f_widget_parent = self
        self.check_frame.f_widget_parent = self
        self.scrollbar_y.f_widget_parent = self
        for w in self.check_frame.children.values():
            w.can_scroll = self.children_can_scroll
            w.f_widget_parent = self

        width = min(self.bool_frame_max_width, width)
        height = min(self.bool_frame_max_height, height)
        self.content.config(width=width + self.frame_depth*2,
                            height=height + self.frame_depth*2)
        self.check_canvas.config(width=width, height=height)
        self.check_canvas.itemconfigure(
            self.check_frame_id, width=self.check_canvas.winfo_reqwidth())

    def mousewheel_scroll_y(self, e):
        if self.should_scroll(e):
            delta = (getattr(self.tag_window.app_root,
                             "scroll_increment_x", 20) *
                     int(widgets.get_mouse_delta(e)))
            self.check_canvas.yview_scroll(delta, "units")


class BoolSingleFrame(data_frame.DataFrame):
    checked = None

    def __init__(self, *args, **kwargs):
        data_frame.DataFrame.__init__(self, *args, **kwargs)

        self.checked = tk.IntVar(self)
        self.checkbutton = tk.Checkbutton(
            self, variable=self.checked, command=self.check, text="  ",
            disabledforeground=self.text_disabled_color)

        self.title_label = tk.Label(
            self, text=self.gui_name, width=self.title_size, anchor='w',
            disabledforeground=self.text_disabled_color)

        if self.gui_name != '':
            self.title_label.pack(side='left')
        self.checkbutton.pack(side='left')

        self.populate()
        self._initialized = True

    def unload_node_data(self):
        field_widget.FieldWidget.unload_node_data(self)
        self.checked.set(0)

    def set_disabled(self, disable=True):
        disable = disable or not self.editable
        if self.node is None and not disable:
            return

        if bool(disable) != self.disabled:
            self.checkbutton.config(state=tk.DISABLED if disable else tk.NORMAL)

        data_frame.DataFrame.set_disabled(self, disable)

    def apply_style(self, seen=None):
        field_widget.FieldWidget.apply_style(self, seen)
        self.checkbutton.config(
            selectcolor=self.entry_normal_color,
            activebackground=self.default_bg_color,
            activeforeground=self.text_highlighted_color)

    def flush(self): pass

    def edit_apply(self=None, *, edit_state, undo=True):
        state = edit_state

        attr_index = state.attr_index
        undo_value = state.undo_node

        w, parent = field_widget.FieldWidget.get_widget_and_node(
            nodepath=state.nodepath, tag_window=state.tag_window)

        if undo:
            parent[attr_index] = int(undo_value)
        else:
            parent[attr_index] = int(not undo_value)

        if w is not None:
            try:
                if w.desc is not state.desc:
                    return

                w.needs_flushing = False
                w.checked.set(bool(parent[attr_index]))
            except Exception:
                print(format_exc())

    def check(self):
        if None in (self.parent, self.node):
            return

        try:
            desc = self.desc
            self.set_edited()
            self.checkbutton.focus_set()
            self.edit_create(undo_node=bool(self.parent[self.attr_index]))
            self.node = self.parent[self.attr_index] = self.checked.get()
        except Exception:
            print(format_exc())

    def reload(self):
        try:
            for w in (self, self.checkbutton, self.title_label):
                w.tooltip_string = self.desc.get('TOOLTIP')
            if self.disabled:
                self.checkbutton.config(state=tk.NORMAL)
            self.checked.set(bool(self.node))
        except Exception:
            print(format_exc())
        finally:
            if self.disabled:
                self.checkbutton.config(state=tk.DISABLED)

    populate = reload
