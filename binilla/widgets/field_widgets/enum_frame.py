import threadsafe_tkinter as tk

from traceback import format_exc

from binilla import editor_constants as e_c
from binilla.widgets.scroll_menu import ScrollMenu
from binilla.widgets.field_widgets import field_widget, data_frame


class EnumFrame(data_frame.DataFrame):
    '''Used for enumerator nodes. When clicked, creates
    a dropdown box of all available enumerator options.'''

    option_cache = None
    sel_menu = None

    def __init__(self, *args, **kwargs):
        kwargs.update(relief='flat', bd=0, highlightthickness=0)
        data_frame.DataFrame.__init__(self, *args, **kwargs)

        try:
            sel_index = self.node.get_index()
        except Exception:
            sel_index = -1

        # make the widgets
        self.content = tk.Frame(self, relief='flat', bd=0)

        self.display_comment()

        self.title_label = tk.Label(
            self.content, text=self.gui_name,
            justify='left', anchor='w', width=self.title_size,
            disabledforeground=self.text_disabled_color)
        self.sel_menu = ScrollMenu(
            self.content, f_widget_parent=self, menu_width=self.widget_width,
            sel_index=sel_index, max_index=self.desc.get('ENTRIES', 0) - 1,
            disabled=self.disabled, default_text="<INVALID>",
            option_getter=self.get_options, callback=self.select_option)

        if self.gui_name != '':
            self.title_label.pack(side="left", fill="x")
        self.content.pack(fill="x", expand=True)
        self.sel_menu.pack(side="left", fill="x")
        self.populate()
        self.pose_fields()
        self._initialized = True

    @property
    def widget_width(self):
        desc = self.desc
        width = desc.get('WIDGET_WIDTH', self.enum_menu_width)
        if width <= 0:
            for s in self.get_options().values():
                width = max(width, len(s))

        return width

    def apply_style(self, seen=None):
        self.sel_menu.menu_width = self.widget_width
        data_frame.DataFrame.apply_style(self, seen)

    def unload_node_data(self):
        field_widget.FieldWidget.unload_node_data(self)
        self.sel_menu.update_label(" ")

    def set_disabled(self, disable=True):
        disable = disable or not self.editable
        if self.node is None and not disable:
            return

        if bool(disable) != self.disabled and getattr(self, "sel_menu", None):
            self.sel_menu.set_disabled(disable)

        data_frame.DataFrame.set_disabled(self, disable)

    def flush(self): pass

    def edit_apply(self=None, *, edit_state, undo=True):
        state = edit_state
        w, node = field_widget.FieldWidget.get_widget_and_node(nodepath=state.nodepath,
                                                  tag_window=state.tag_window)

        if undo:
            node.data = state.undo_node
        else:
            node.data = state.redo_node

        if w is not None:
            try:
                if w.desc is not state.desc:
                    return
                try:
                    w.sel_menu.sel_index = node.get_index()
                except Exception:
                    # option doesnt exist, so make the displayed one blank
                    w.sel_menu.sel_index = -1

                w.needs_flushing = False
                w.sel_menu.update_label()
                w.set_edited()
            except Exception:
                print(format_exc())

    def edit_create(self, **kwargs):
        # add own stuff
        kwargs.update(sel_index=self.sel_menu.sel_index,
                      max_index=self.sel_menu.max_index)
        field_widget.FieldWidget.edit_create(self, **kwargs)

    def get_options(self, opt_index=None):
        '''
        Returns a list of the option strings sorted by option index.
        '''
        if self.option_cache is None or opt_index is not None:
            return self.generate_options(opt_index)

        if opt_index is None:
            return self.option_cache
        elif opt_index == e_c.ACTIVE_ENUM_NAME:
            opt_index = self.sel_menu.sel_index

        return self.option_cache.get(opt_index, None)

    def generate_options(self, opt_index=None):
        desc = self.desc
        options = {}
        option_count = desc.get('ENTRIES', 0)
        options_to_generate = range(option_count)
        if opt_index is not None:
            options_to_generate = (
                (opt_index, ) if opt_index in options_to_generate else ())

        # sort the options by value(values are integers)
        use_gui_names = self.use_gui_names
        for i in options_to_generate:
            opt = desc[i]
            if use_gui_names and 'GUI_NAME' in opt:
                options[i] = opt['GUI_NAME']
            else:
                options[i] = opt.get('NAME', '<UNNAMED %s>' % i)\
                             .replace('_', ' ')

        if opt_index is None:
            self.options_sane = True
            self.option_cache = options
            if self.sel_menu is not None:
                self.sel_menu.options_menu_sane = False
                self.sel_menu.max_index = option_count - 1
            return options
        return options.get(opt_index, None)

    def reload(self):
        try:
            if self.disabled == self.sel_menu.disabled:
                pass
            elif self.disabled:
                self.sel_menu.disable()
            else:
                self.sel_menu.enable()

            for w in (self, self.content, self.sel_menu, self.title_label):
                w.tooltip_string = self.desc.get('TOOLTIP')

            options = self.get_options()
            option_count = len(options)
            if not option_count:
                self.sel_menu.sel_index = -1
                self.sel_menu.max_index = -1
                return

            try:
                curr_index = self.node.get_index()
            except Exception:
                curr_index = -1

            self.sel_menu.sel_index = curr_index
            self.sel_menu.max_index = option_count - 1
            self.sel_menu.update_label()
        except Exception:
            print(format_exc())

    populate = reload

    def pose_fields(self): pass

    def select_option(self, opt_index=None):
        if None in (self.parent, self.node):
            return

        node = self.node
        curr_index = self.sel_menu.sel_index

        if (opt_index is None or opt_index < 0 or
            opt_index > self.sel_menu.max_index):
            print("Invalid option index '%s'" % opt_index)
            return

        self.sel_menu.sel_index = opt_index

        undo_node = self.node.data
        self.node.set_to(opt_index)

        # make an edit state
        if undo_node != self.node.data:
            self.set_edited()
            self.edit_create(undo_node=undo_node, redo_node=self.node.data)

        self.sel_menu.update_label()


class DynamicEnumFrame(EnumFrame):
    options_sane = False

    def __init__(self, *args, **kwargs):
        kwargs.update(relief='flat', bd=0, highlightthickness=0)
        data_frame.DataFrame.__init__(self, *args, **kwargs)

        sel_index = -1 if self.node is None else self.node + 1

        # make the widgets
        self.content = tk.Frame(self, relief='flat', bd=0)
        self.title_label = tk.Label(
            self.content, text=self.gui_name,
            justify='left', anchor='w', width=self.title_size,
            disabledforeground=self.text_disabled_color)
        self.sel_menu = ScrollMenu(
            self.content, f_widget_parent=self, menu_width=self.widget_width,
            sel_index=sel_index, max_index=0,
            disabled=self.disabled, default_text="<INVALID>",
            option_getter=self.get_options,  callback=self.select_option)

        self.sel_menu.bind('<FocusIn>', self.flag_sanity_change)
        self.sel_menu.arrow_button.bind('<FocusIn>', self.flag_sanity_change)
        self.sel_menu.bind('<Enter>', self.flag_sanity_change)
        self.sel_menu.arrow_button.bind('<Enter>', self.flag_sanity_change)
        self.sel_menu.options_volatile = 'DYN_NAME_PATH' in self.desc

        if self.gui_name != '':
            self.title_label.pack(side="left", fill="x")
        self.content.pack(fill="x", expand=True)
        self.sel_menu.pack(side="left", fill="x")
        self.populate()
        self._initialized = True

    def edit_apply(self=None, *, edit_state, undo=True):
        state = edit_state
        attr_index = state.attr_index

        w_parent, parent = field_widget.FieldWidget.get_widget_and_node(
            nodepath=state.nodepath, tag_window=state.tag_window)

        if undo:
            parent[attr_index] = state.undo_node
        else:
            parent[attr_index] = state.redo_node

        if w_parent is not None:
            try:
                w = w_parent.f_widgets[
                    w_parent.f_widget_ids_map[attr_index]]
                if w.desc is not state.desc:
                    return

                w.sel_menu.sel_index = parent[attr_index] + 1
                w.needs_flushing = False
                w.sel_menu.update_label()
                w.set_edited()
            except Exception:
                print(format_exc())

    def generate_options(self, opt_index=None):
        desc = self.desc
        options = {0: "-1. NONE"}

        dyn_name_path = desc.get('DYN_NAME_PATH')
        if self.node is None:
            if opt_index is None:
                return options
            return None
        elif not dyn_name_path:
            print("Missing DYN_NAME_PATH path in dynamic enumerator.")
            print(self.parent.get_root().def_id, self.name)
            if opt_index is None:
                return options
            return None

        try:
            p_out, p_in = dyn_name_path.split('[DYN_I]')

            # We are ALWAYS going to go to the parent, so we need to slice
            if p_out.startswith('..'): p_out = p_out.split('.', 1)[-1]
            array = self.parent.get_neighbor(p_out)

            options_to_generate = range(len(array))
            if opt_index is not None:
                options_to_generate = (
                    (opt_index - 1, ) if opt_index - 1 in
                    options_to_generate else ())

            for i in options_to_generate:
                name = array[i].get_neighbor(p_in)
                if isinstance(name, list):
                    name = repr(name).strip("[").strip("]")
                else:
                    name = str(name)

                options[i + 1] = '%s. %s' % (i, name.split('\n')[0])
            option_count = len(array) + 1
        except Exception:
            print(format_exc())
            option_count = 1

        if opt_index is None:
            self.option_cache = options
            self.options_sane = True
            if self.sel_menu is not None:
                self.sel_menu.options_menu_sane = False
                self.sel_menu.max_index = option_count - 1
            return options
        return options.get(opt_index, None)

    def reload(self):
        try:
            self.options_sane = False
            if self.disabled == self.sel_menu.disabled:
                pass
            elif self.disabled:
                self.sel_menu.disable()
            else:
                self.sel_menu.enable()

            self.generate_options()
            if self.node is not None:
                self.sel_menu.sel_index = self.node + 1
            self.sel_menu.update_label()
        except Exception:
            print(format_exc())

    populate = reload

    def select_option(self, opt_index=None):
        if None in (self.parent, self.node):
            return

        # make an edit state
        if self.node != opt_index - 1:
            self.set_edited()
            self.edit_create(undo_node=self.node, redo_node=opt_index - 1)

        self.sel_menu.sel_index = opt_index

        # since the node value is actually signed and can be -1, we'll
        # set entry 0 to be a node value of -1 and all other values
        # are one less than the entry index they are located in.
        self.node = self.parent[self.attr_index] = opt_index - 1
        self.sel_menu.update_label()

    def flag_sanity_change(self, e=None):
        self.options_sane = self.sel_menu.options_menu_sane = (
            not self.sel_menu.options_volatile)

        if not self.options_sane:
            self.option_cache = None
