import threadsafe_tkinter as tk
import tkinter.ttk as ttk

from copy import deepcopy
from traceback import format_exc

from binilla import editor_constants as e_c
from binilla.widgets.scroll_menu import ScrollMenu
from binilla.widgets.field_widgets import field_widget, container_frame,\
     data_frame


class ArrayFrame(container_frame.ContainerFrame):
    '''Used for array nodes. Displays a single element in
    the ArrayBlock represented by it, and contains a combobox
    for selecting which array element is displayed.'''

    sel_index = -1
    sel_menu = None
    populated = False
    option_cache = None
    options_sane = False

    def __init__(self, *args, **kwargs):
        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)
        field_widget.FieldWidget.__init__(self, *args, **kwargs)
        tk.Frame.__init__(self, *args, **e_c.fix_kwargs(**kwargs))

        show_frame = bool(kwargs.pop('show_frame', not self.blocks_start_hidden))
        if self.is_empty and self.hide_if_blank:
            show_frame = False

        self.show = tk.BooleanVar()
        self.show.set(show_frame)
        self.options_sane = False

        node_len = 0
        try: node_len = len(self.node)
        except Exception: pass

        self.sel_index = (node_len > 0) - 1

        # make the title, element menu, and all the buttons
        self.controls = tk.Frame(self, relief='raised', bd=self.frame_depth)
        self.title = title = tk.Frame(self.controls, relief='flat', bd=0)
        self.buttons = buttons = tk.Frame(self.controls, relief='flat', bd=0)

        toggle_text = '-' if show_frame else '+'

        self.title_label = tk.Label(
            title, text=self.gui_name, justify='left', anchor='w',
            width=self.title_size, font=self.get_font("frame_title"),
            disabledforeground=self.text_disabled_color)
        self.title_label.font_type = "frame_title"

        self.show_btn = ttk.Checkbutton(
            title, width=3, text=toggle_text, command=self.toggle_visible,
            style='ShowButton.TButton')
        self.sel_menu = ScrollMenu(
            title, f_widget_parent=self,
            sel_index=self.sel_index, max_index=node_len-1,
            option_getter=self.get_options, callback=self.select_option)

        self.shift_up_btn = ttk.Button(
            title, width=7, text='Shift ▲',
            command=self.shift_entry_up)
        self.shift_down_btn = ttk.Button(
            buttons, width=7, text='Shift ▼',
            command=self.shift_entry_down)
        self.add_btn = ttk.Button(
            buttons, width=4, text='Add',
            command=self.add_entry)
        self.insert_btn = ttk.Button(
            buttons, width=6, text='Insert',
            command=self.insert_entry)
        self.duplicate_btn = ttk.Button(
            buttons, width=9, text='Duplicate',
            command=self.duplicate_entry)
        self.delete_btn = ttk.Button(
            buttons, width=6, text='Delete',
            command=self.delete_entry)
        self.delete_all_btn = ttk.Button(
            buttons, width=10, text='Delete all',
            command=self.delete_all_entries)

        self.import_btn = ttk.Button(
            buttons, width=6, text='Import',
            command=self.import_node)
        self.export_btn = ttk.Button(
            buttons, width=6, text='Export',
            command=self.export_node)

        # pack the title, menu, and all the buttons
        for w in (self.shift_down_btn, self.export_btn, self.import_btn,
                  self.delete_all_btn, self.delete_btn, self.duplicate_btn,
                  self.insert_btn, self.add_btn):
            w.pack(side="right", padx=(0, 4), pady=(2, 2))

        self.show_btn.pack(side="left")
        if self.gui_name != '':
            self.title_label.pack(side="left", fill="x", expand=True)

        self.sel_menu.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.shift_up_btn.pack(side="right", padx=(0, 1), pady=(2, 2))

        self.title.pack(fill="x", expand=True, padx=0)
        self.buttons.pack(fill="x", expand=True, padx=0)
        self.controls.pack(fill="x", expand=True, padx=0)

        self.populate()
        self._initialized = True

    @property
    def is_empty(self):
        if getattr(self, "node", None) is None:
            return True
        return len(self.node) == 0

    def load_node_data(self, parent, node, attr_index, desc=None):
        field_widget.FieldWidget.load_node_data(
            self, parent, node, attr_index, desc)
        sub_node = attr_index = None
        if self.node:
            attr_index = self.sel_index
            if attr_index in range(len(self.node)):
                sub_node = self.node[attr_index]
            else:
                attr_index = len(self.node) - 1
                if attr_index < 0:
                    attr_index = None

        if self.sel_menu is not None:
            self.options_sane = self.sel_menu.options_menu_sane = False

        for wid in self.f_widgets:
            # there must be only one entry in self.f_widgets
            w = self.f_widgets[wid]
            if w.load_node_data(self.node, sub_node, attr_index):
                return True

        return False

    def unload_node_data(self):
        self.sel_menu.update_label(" ")
        container_frame.ContainerFrame.unload_node_data(self)

    def set_disabled(self, disable=True):
        disable = disable or not self.editable
        if self.node is None and not disable:
            return

        if getattr(self, "sel_menu", None):
            self.sel_menu.set_disabled(disable)

        if bool(disable) == self.disabled:
            pass
        elif not disable:
            self.set_all_buttons_disabled(False)
            self.disable_unusable_buttons()
        else:
            new_state = tk.DISABLED if disable else tk.NORMAL
            for w in (self.shift_up_btn, self.shift_down_btn,
                      self.add_btn, self.insert_btn, self.duplicate_btn,
                      self.delete_btn, self.delete_all_btn):
                if w:
                    w.config(state=new_state)

        container_frame.ContainerFrame.set_disabled(self, disable)

    def apply_style(self, seen=None):
        container_frame.ContainerFrame.apply_style(self, seen)
        self.controls.config(bd=self.frame_depth, bg=self.frame_bg_color)
        self.title.config(bg=self.frame_bg_color)
        self.title_label.config(bg=self.frame_bg_color)
        self.buttons.config(bg=self.frame_bg_color)
        #if self.show.get():
        #    self.pose_fields()

    def destroy(self):
        # These will linger and take up RAM, even if the widget is destroyed.
        # Need to remove the references manually
        self.option_cache = None
        container_frame.ContainerFrame.destroy(self)

    def export_node(self):
        try:
            # pass call to the export_node method of the array entry's widget
            w = self.f_widgets[self.f_widget_ids[0]]
        except Exception:
            return
        w.export_node()

    def import_node(self):
        try:
            # pass call to the import_node method of the array entry's widget
            w = self.f_widgets[self.f_widget_ids[0]]
        except Exception:
            return
        w.import_node()

    def get_options(self, opt_index=None):
        '''
        Returns a list of the option strings sorted by option index.
        '''
        if (self.option_cache is None or not self.options_sane or
                opt_index is not None):
            result = self.generate_options(opt_index)
            if opt_index is not None:
                return result

        if opt_index is None:
            return self.option_cache
        elif opt_index == e_c.ACTIVE_ENUM_NAME:
            opt_index = self.sel_index

        if opt_index < 0: opt_index = -1

        return self.option_cache.get(opt_index)

    def generate_options(self, opt_index=None):
        # sort the options by value(values are integers)
        options = {i: n for n, i in self.desc.get('NAME_MAP', {}).items()}

        if self.node:
            node, desc = self.node, self.desc
            sub_desc = desc['SUB_STRUCT']
            def_struct_name = sub_desc['NAME']
            if self.use_gui_names and 'GUI_NAME' in sub_desc:
                def_struct_name = sub_desc['GUI_NAME']

            options_to_generate = range(len(node))
            if opt_index is not None:
                options_to_generate = (
                    (opt_index, ) if opt_index in options_to_generate else ())

            for i in options_to_generate:
                if i in options:
                    continue
                sub_node = node[i]
                if not hasattr(sub_node, 'desc'):
                    continue
                sub_desc = sub_node.desc
                sub_struct_name = sub_desc.get('GUI_NAME', sub_desc['NAME'])
                if sub_struct_name == def_struct_name:
                    continue

                options[i] = sub_struct_name

        if opt_index is None:
            self.options_sane = True
            self.option_cache = options
            if self.sel_menu is not None:
                self.sel_menu.options_menu_sane = False
                self.sel_menu.max_index = len(node) - 1
            return options
        return options.get(opt_index, None)

    def set_shift_up_disabled(self, disable=True):
        '''
        Disables the move up button if disable is True. Enables it if not.
        '''
        if disable: self.shift_up_btn.config(state="disabled")
        else:       self.shift_up_btn.config(state="normal")

    def set_shift_down_disabled(self, disable=True):
        '''
        Disables the move down button if disable is True. Enables it if not.
        '''
        if disable: self.shift_down_btn.config(state="disabled")
        else:       self.shift_down_btn.config(state="normal")

    def set_add_disabled(self, disable=True):
        '''Disables the add button if disable is True. Enables it if not.'''
        if disable: self.add_btn.config(state="disabled")
        else:       self.add_btn.config(state="normal")

    def set_insert_disabled(self, disable=True):
        '''Disables the insert button if disable is True. Enables it if not.'''
        if disable: self.insert_btn.config(state="disabled")
        else:       self.insert_btn.config(state="normal")

    def set_duplicate_disabled(self, disable=True):
        '''
        Disables the duplicate button if disable is True. Enables it if not.
        '''
        if disable: self.duplicate_btn.config(state="disabled")
        else:       self.duplicate_btn.config(state="normal")

    def set_delete_disabled(self, disable=True):
        '''Disables the delete button if disable is True. Enables it if not.'''
        if disable: self.delete_btn.config(state="disabled")
        else:       self.delete_btn.config(state="normal")

    def set_delete_all_disabled(self, disable=True):
        '''
        Disables the delete_all button if disable is True. Enables it if not.
        '''
        if disable: self.delete_all_btn.config(state="disabled")
        else:       self.delete_all_btn.config(state="normal")

    def edit_apply(self=None, *, edit_state, undo=True):
        state = edit_state

        edit_type = state.edit_type
        i = state.attr_index
        undo_node = state.undo_node
        redo_node = state.redo_node

        edit_info = state.edit_info
        sel_index = edit_info.get('sel_index', 0)

        w, node = field_widget.FieldWidget.get_widget_and_node(
            nodepath=state.nodepath, tag_window=state.tag_window)

        if edit_type == 'shift_up':
            node[i], node[i - 1] = node[i - 1], node[i]
        elif edit_type == 'shift_down':
            node[i], node[i + 1] = node[i + 1], node[i]
        elif edit_type in ('add', 'insert', 'duplicate'):
            if undo:
                sel_index = None
                node.pop(i)
            else:
                node.insert(i, redo_node)
        elif edit_type == 'delete':
            if undo:
                node.insert(i, undo_node)
            else:
                sel_index = None
                node.pop(i)
        elif edit_type == 'delete_all':
            if undo:
                node[:] = undo_node
            else:
                del node[:]
                sel_index = None
        else:
            raise TypeError('Unknown edit_state type')

        if w is not None:
            try:
                if w.desc is not state.desc:
                    return

                if sel_index is None:
                    pass
                elif edit_type in ('add', 'insert', 'duplicate', 'delete'):
                    w.sel_index = sel_index
                elif edit_type in ('shift_up', 'shift_down'):
                    w.sel_index = sel_index
                    if undo:
                        pass
                    elif 'down' in edit_type:
                        w.sel_index += 1
                    else:
                        w.sel_index -= 1

                max_index = len(node) - 1
                w.sel_menu.max_index = max_index
                w.options_sane = w.sel_menu.options_menu_sane = False
                if w.sel_index < 0:
                    w.select_option(0, force=True)
                elif w.sel_index > max_index:
                    w.select_option(max_index, force=True)
                else:
                    w.select_option(w.sel_index, force=True)

                w.needs_flushing = False
                w.set_edited()
            except Exception:
                print(format_exc())

    def edit_create(self, **kwargs):
        # add own stuff
        kwargs.setdefault("sel_index", self.sel_index)
        field_widget.FieldWidget.edit_create(self, **kwargs)

    def shift_entry_up(self):
        if not hasattr(self.node, '__len__') or len(self.node) < 2:
            return

        node = self.node
        index = self.sel_index
        if index <= 0:
            return

        self.set_edited() # do this first so the TagWindow detects that
        #                   the title needs to be updated with an asterisk
        self.edit_create(edit_type='shift_up', attr_index=index)
        node[index], node[index - 1] = node[index - 1], node[index]

        self.sel_index = self.sel_menu.sel_index = index - 1
        self.options_sane = self.sel_menu.options_menu_sane = False
        self.sel_menu.update_label()

    def shift_entry_down(self):
        if not hasattr(self.node, '__len__') or len(self.node) < 2:
            return

        node = self.node
        index = self.sel_index
        if index >= len(node) - 1:
            return

        self.set_edited() # do this first so the TagWindow detects that
        #                   the title needs to be updated with an asterisk
        self.edit_create(edit_type='shift_down', attr_index=index)
        node[index], node[index + 1] = node[index + 1], node[index]

        self.sel_index = self.sel_menu.sel_index = index + 1
        self.options_sane = self.sel_menu.options_menu_sane = False
        self.sel_menu.update_label()

    def add_entry(self):
        if not hasattr(self.node, '__len__'):
            return

        field_max = self.field_max
        if field_max is not None and len(self.node) >= field_max:
            if self.enforce_max:
                return

        attr_index = len(self.node)
        self.set_edited() # do this first so the TagWindow detects that
        #                   the title needs to be updated with an asterisk
        self.node.append()

        self.edit_create(edit_type='add', attr_index=attr_index,
                         redo_node=self.node[attr_index], sel_index=attr_index)

        self.options_sane = self.sel_menu.options_menu_sane = False
        self.set_all_buttons_disabled(self.disabled)
        self.disable_unusable_buttons() 
        self.select_option(len(self.node) - 1, True)

    def insert_entry(self):
        if not hasattr(self.node, '__len__'):
            return

        field_max = self.field_max
        if field_max is not None and len(self.node) >= field_max:
            if self.enforce_max:
                return

        attr_index = self.sel_index = max(self.sel_index, 0)
        self.set_edited() # do this first so the TagWindow detects that
        #                   the title needs to be updated with an asterisk
        self.node.insert(attr_index)

        self.edit_create(edit_type='insert', attr_index=attr_index,
                         redo_node=self.node[attr_index], sel_index=attr_index)

        self.options_sane = self.sel_menu.options_menu_sane = False
        self.set_all_buttons_disabled(self.disabled)
        self.disable_unusable_buttons()
        self.select_option(attr_index, True)  # select the new entry

    def duplicate_entry(self):
        if not hasattr(self.node, '__len__') or len(self.node) < 1:
            return

        field_max = self.field_max
        if field_max is not None and len(self.node) >= field_max:
            if self.enforce_max:
                return

        self.sel_index = self.sel_menu.sel_index = max(self.sel_index, 0)
        self.set_edited() # do this first so the TagWindow detects that
        #                   the title needs to be updated with an asterisk
        new_subnode = deepcopy(self.node[self.sel_index])
        attr_index = len(self.node)

        self.edit_create(edit_type='duplicate', attr_index=attr_index,
                         redo_node=new_subnode, sel_index=attr_index)

        self.node.append(new_subnode)

        self.options_sane = self.sel_menu.options_menu_sane = False
        self.set_all_buttons_disabled(self.disabled)
        self.disable_unusable_buttons()
        self.select_option(attr_index, True)

    def delete_entry(self):
        if not hasattr(self.node, '__len__') or len(self.node) == 0:
            return

        field_min = self.field_min
        if field_min is None:
            field_min = 0

        if len(self.node) <= field_min:
            if self.enforce_min:
                return

        if not len(self.node):
            self.sel_menu.disable()
            return

        attr_index = max(self.sel_index, 0)

        self.set_edited() # do this first so the TagWindow detects that
        #                   the title needs to be updated with an asterisk
        self.edit_create(edit_type='delete', undo_node=self.node[attr_index],
                         attr_index=attr_index, sel_index=attr_index)

        del self.node[attr_index]
        attr_index = max(-1, min(len(self.node) - 1, attr_index))

        self.options_sane = self.sel_menu.options_menu_sane = False
        self.select_option(attr_index, True)
        self.set_all_buttons_disabled(self.disabled)
        self.disable_unusable_buttons()

    def delete_all_entries(self):
        if not hasattr(self.node, '__len__') or len(self.node) == 0:
            return

        field_min = self.field_min
        if field_min is None:
            field_min = 0

        if len(self.node) <= field_min:
            if self.enforce_min:
                return

        if not len(self.node):
            self.sel_menu.disable()
            return

        self.set_edited() # do this first so the TagWindow detects that
        #                   the title needs to be updated with an asterisk
        self.edit_create(edit_type='delete_all', undo_node=tuple(self.node[:]))

        del self.node[:]

        self.options_sane = self.sel_menu.options_menu_sane = False
        self.set_all_buttons_disabled(self.disabled)
        self.disable_unusable_buttons()
        self.select_option(self.sel_index, True)

    def set_all_buttons_disabled(self, disable=False):
        for btn in (self.add_btn, self.insert_btn, self.duplicate_btn,
                    self.delete_btn, self.delete_all_btn,
                    self.import_btn, self.export_btn,
                    self.shift_up_btn, self.shift_down_btn):
            if disable:
                btn.config(state=tk.DISABLED)
            else:
                btn.config(state=tk.NORMAL)

    def disable_unusable_buttons(self):
        no_node = not hasattr(self.node, '__len__')
        if no_node or len(self.node) < 2:
            self.set_shift_up_disabled()
            self.set_shift_down_disabled()

        if no_node or (isinstance(self.desc.get('SIZE'), int)
                       and self.enforce_min):
            self.set_add_disabled()
            self.set_insert_disabled()
            self.set_duplicate_disabled()
            self.set_delete_disabled()
            self.set_delete_all_disabled()
            return

        field_max = self.field_max
        field_min = self.field_min
        if field_min is None or field_min < 0: field_min = 0
        enforce_min = self.enforce_min or field_min == 0
        enforce_max = self.enforce_max

        if field_max is not None and len(self.node) >= field_max and enforce_max:
            self.set_add_disabled()
            self.set_insert_disabled()
            self.set_duplicate_disabled()

        if len(self.node) <= field_min and (enforce_min or not self.node):
            self.set_delete_disabled()
            self.set_delete_all_disabled()

        if not self.node:
            self.set_export_disabled()
            self.set_import_disabled()
            self.set_duplicate_disabled()

    def populate(self):
        node = self.node
        desc = self.desc
        sub_node = None
        sub_desc = desc['SUB_STRUCT']

        if node and self.sel_index in range(len(node)):
            sub_node = node[self.sel_index]
            sub_desc = desc['SUB_STRUCT']
            if hasattr(sub_node, 'desc'):
                sub_desc = sub_node.desc

        if self.content in (None, self):
            self.content = tk.Frame(self, relief="sunken", bd=self.frame_depth,
                                    bg=self.default_bg_color)

        self.sel_menu.default_text = sub_desc.get(
            'GUI_NAME', sub_desc.get('NAME', ""))
        self.sel_menu.update_label()
        self.disable_unusable_buttons()

        rebuild = not bool(self.f_widgets)
        if hasattr(node, '__len__') and len(node) == 0:
            # disabling existing widgets
            self.sel_index = -1
            self.sel_menu.max_index = -1
            if self.f_widgets:
                self.unload_child_node_data()
        else:
            for w in self.f_widgets:
                if getattr(w, "desc", None) != sub_desc:
                    rebuild = True
                    break

        if rebuild:
            # destroy existing widgets and make new ones
            self.populated = False
            self.f_widget_ids = []
            self.f_widget_ids_map = {}
            self.f_widget_ids_map_inv = {}

            # destroy any child widgets of the content
            for c in list(self.f_widgets.values()):
                c.destroy()

            for w in (self, self.content, self.title, self.title_label,
                      self.controls, self.buttons):
                w.tooltip_string = self.desc.get('TOOLTIP')

            self.display_comment(self.content)

            widget_cls = self.widget_picker.get_widget(sub_desc)
            try:
                widget = widget_cls(
                    self.content, node=sub_node, parent=node,
                    show_title=False, dont_padx_fields=True,
                    attr_index=self.sel_index, tag_window=self.tag_window,
                    f_widget_parent=self, disabled=self.disabled)
            except Exception:
                print(format_exc())
                widget = data_frame.NullFrame(
                    self.content, node=sub_node, parent=node,
                    show_title=False, dont_padx_fields=True,
                    attr_index=self.sel_index, tag_window=self.tag_window,
                    f_widget_parent=self, disabled=self.disabled)

            wid = id(widget)
            self.f_widget_ids.append(wid)
            self.f_widget_ids_map[self.sel_index] = wid
            self.f_widget_ids_map_inv[wid] = self.sel_index

            self.populated = True
            self.build_f_widget_cache()

            # now that the field widgets are created, position them
            if self.show.get():
                self.pose_fields()

        if self.node is None:
            self.set_disabled(True)
        else:
            self.set_children_disabled(not self.node)

    def reload(self):
        '''Resupplies the nodes to the widgets which display them.'''
        try:
            node = self.node if self.node else ()
            desc = self.desc

            is_empty = len(node) == 0
            field_max = self.field_max
            field_min = self.field_min
            if field_min is None: field_min = 0

            self.set_all_buttons_disabled(self.disabled)
            self.disable_unusable_buttons()

            if is_empty:
                self.sel_menu.sel_index = -1
                self.sel_menu.max_index = -1
                # if there is no index to select, destroy the content
                if self.sel_index != -1:
                    self.sel_index = -1

                self.unload_child_node_data()
            else:
                self.f_widget_ids_map = {}
                self.f_widget_ids_map_inv = {}

            self.sel_menu.sel_index = self.sel_index
            self.sel_menu.max_index = len(node) - 1

            sub_node = None
            sub_desc = desc['SUB_STRUCT']
            if node and self.sel_index in range(len(node)):
                sub_node = node[self.sel_index]
                sub_desc = desc['SUB_STRUCT']
                if hasattr(sub_node, 'desc'):
                    sub_desc = sub_node.desc

            for wid in self.f_widget_ids:
                w = self.f_widgets[wid]
                wid = id(w)

                if node and self.sel_index not in range(len(node)):
                    # current selection index is invalid. call select_option
                    # to reset it to some valid option. Don't reload though,
                    # as we will be either reloading or repopulating below.
                    self.select_option(force=True, reload=False)

                self.f_widget_ids_map[self.sel_index] = wid
                self.f_widget_ids_map_inv[wid] = self.sel_index

                # if the descriptors are different, gotta repopulate!
                if w.load_node_data(node, sub_node, self.sel_index, sub_desc):
                    self.populate()
                    self.apply_style()
                    return

                w.reload()
                if w.desc.get("PORTABLE", True) and self.node:
                    self.set_import_disabled(False)
                    self.set_export_disabled(False)
                else:
                    self.set_import_disabled()
                    self.set_export_disabled()

            self.sel_menu.update_label()
            if self.node is None:
                self.set_disabled(True)
            else:
                self.set_children_disabled(not self.node)
        except Exception:
            print(format_exc())

    def pose_fields(self):
        # there should only be one wid in here, but for
        # the sake of consistancy we'll loop over them.
        for wid in self.f_widget_ids:
            w = self.f_widgets[wid]

            # by adding a fixed amount of padding, we fix a problem
            # with difficult to predict padding based on nesting
            w.pack(fill='x', side='top', expand=True,
                   padx=self.vertical_padx, pady=self.vertical_pady)

        # if there are no children in the content, we need to
        # pack in SOMETHING, update the idletasks, and then
        # destroy that something to resize the content frame
        if not self.f_widgets:
            f = tk.Frame(self.content, width=0, height=0, bd=0)
            f.pack()
            self.content.update_idletasks()
            f.destroy()

        self.content.pack(fill='both', side='top', anchor='nw', expand=True)

    def select_option(self, opt_index=None, force=False, reload=True):
        node = self.node if self.node else ()
        curr_index = self.sel_index
        if opt_index is None:
            opt_index = curr_index

        if opt_index < 0:
            opt_index = 0

        if opt_index == curr_index and not force:
            return
        elif not node:
            opt_index = -1
        elif opt_index not in range(len(node)):
            opt_index = len(node) - 1

        # flush any lingering changes
        self.flush()
        self.sel_index = opt_index
        self.sel_menu.sel_index = opt_index
        self.sel_menu.max_index = len(node) - 1
        if reload:
            self.reload()

        self.sel_menu.update_label()

    @property
    def visible_field_count(self):
        # array frames only display one item at a time
        return 1


class DynamicArrayFrame(ArrayFrame):

    def __init__(self, *args, **kwargs):
        ArrayFrame.__init__(self, *args, **kwargs)

        self.sel_menu.bind('<FocusIn>', self.flag_sanity_change)
        self.sel_menu.arrow_button.bind('<FocusIn>', self.flag_sanity_change)
        self.sel_menu.options_volatile = 'DYN_NAME_PATH' in self.desc

    def generate_dynamic_options(self, options, options_to_generate):
        node, desc = self.node, self.desc
        dyn_name_path = desc.get('DYN_NAME_PATH')
        if dyn_name_path:
            try:
                for i in options_to_generate:
                    name = str(node[i].get_neighbor(dyn_name_path))
                    if name:
                        options[i] = name.split('\n')[0]
            except Exception:
                pass

    def generate_options(self, opt_index=None):
        node, desc = self.node, self.desc
        if node is None:
            if opt_index is None:
                return options
            return ""

        options = {}
        options_to_generate = range(len(node))
        if opt_index is not None:
            options_to_generate = (
                (opt_index, ) if opt_index in options_to_generate else ())

        if desc.get('DYN_NAME_PATH'):
            try:
                self.generate_dynamic_options(options, options_to_generate)
            except Exception:
                print(format_exc())
        else:
            # sort the options by value(values are integers)
            options.update({i: n for n, i in
                            self.desc.get('NAME_MAP', {}).items()
                            if i not in options})
            sub_desc = desc['SUB_STRUCT']
            def_struct_name = sub_desc['NAME']
            if self.use_gui_names and 'GUI_NAME' in sub_desc:
                def_struct_name = sub_desc['GUI_NAME']

            for i in options_to_generate:
                if i in options:
                    continue
                sub_node = node[i]
                if not hasattr(sub_node, 'desc'):
                    continue
                sub_struct_name = sub_node.desc['NAME']
                if self.use_gui_names and 'GUI_NAME' in sub_node.desc:
                    sub_struct_name = sub_node.desc['GUI_NAME']

                if sub_struct_name != def_struct_name:
                    options[i] = sub_struct_name

        for i, v in options.items():
            options[i] = '%s. %s' % (i, v)


        if opt_index is None:
            self.option_cache = options
            self.options_sane = True
            if self.sel_menu is not None:
                self.sel_menu.options_menu_sane = False
                self.sel_menu.max_index = len(node) - 1
            return options
        return options.get(opt_index, None)

    def flag_sanity_change(self, e=None):
        self.options_sane = self.sel_menu.options_menu_sane = (
            not self.sel_menu.options_volatile)
