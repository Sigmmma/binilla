import threadsafe_tkinter as tk
import tkinter.ttk as ttk

from traceback import format_exc

from binilla import editor_constants as e_c
from binilla.widgets.scroll_menu import ScrollMenu
from binilla.widgets.field_widgets import field_widget, container_frame,\
     data_frame


class UnionFrame(container_frame.ContainerFrame):
    '''Used for enumerator nodes. When clicked, creates
    a dropdown box of all available enumerator options.'''

    option_cache = None
    u_node_widgets_by_u_index = ()

    def __init__(self, *args, **kwargs):
        field_widget.FieldWidget.__init__(self, *args, **kwargs)
        self.u_node_widgets_by_u_index = {}

        if self.f_widget_parent is None:
            self.pack_padx = self.pack_pady = 0

        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)

        show_frame = bool(kwargs.pop('show_frame', not self.blocks_start_hidden))
        if self.is_empty and self.hide_if_blank:
            show_frame = False

        tk.Frame.__init__(self, *args, **e_c.fix_kwargs(**kwargs))

        self.show = tk.BooleanVar(self)
        self.show.set(show_frame)

        max_u_index = len(self.desc['CASE_MAP'])
        u_index = getattr(self.node, "u_index", None)
        if u_index is None:
            u_index = max_u_index

        toggle_text = '-' if show_frame else '+'

        self.title = tk.Frame(self, relief='raised')
        self.show_btn = ttk.Checkbutton(
            self.title, width=3, text=toggle_text, command=self.toggle_visible,
            style='ShowButton.TButton')
        self.title_label = tk.Label(
            self.title, text=self.gui_name, anchor='w',
            width=self.title_size, justify='left')
        self.title_label.font_type = "frame_title"
        self.sel_menu = ScrollMenu(
            self.title, f_widget_parent=self, sel_index=u_index,
            max_index=max_u_index, disabled=self.disabled,
            callback=self.select_option, option_getter=self.get_options)

        self.show_btn.pack(side="left")
        self.title_label.pack(side="left", fill="x", expand=True)
        self.sel_menu.pack(side="left", fill="x")
        self.title.pack(fill="x", expand=True)

        self.content = tk.Frame(self, relief="sunken")

        # make the default raw bytes union frame
        self.raw_frame = tk.Frame(self.content, relief="flat", bd=0)
        self.raw_label = tk.Label(
            self.raw_frame, text='DataUnion', width=self.title_size,
            anchor='w', disabledforeground=self.text_disabled_color)
        self.import_btn = ttk.Button(
            self.raw_frame, text='Import', command=self.import_node, width=7)
        self.export_btn = ttk.Button(
            self.raw_frame, text='Export', command=self.export_node, width=7)

        self.raw_label.pack(side="left", expand=True, fill='x')
        for w in (self.export_btn, self.import_btn):
            w.pack(side="left", padx=(0, 4), pady=2)

        self.populate()
        self._initialized = True

    def apply_style(self, seen=None):
        container_frame.ContainerFrame.apply_style(self, seen)
        self.title.config(bd=self.frame_depth, bg=self.frame_bg_color)
        self.title_label.config(bg=self.frame_bg_color)
        self.content.config(bd=self.frame_depth)

    def load_child_node_data(self):
        desc = self.desc
        sub_node = None
        for wid in self.f_widgets:
            # try and load any existing FieldWidgets with appropriate node data
            w = self.f_widgets[wid]
            attr_index = self.f_widget_ids_map_inv.get(wid)
            if attr_index is None:
                continue
            elif self.node:
                sub_node = self.node.u_node

            w.load_node_data(self.node, sub_node, attr_index)

        return False

    def set_disabled(self, disable=True):
        disable = disable or not self.editable
        if self.node is None and not disable:
            return

        if bool(disable) != self.disabled and getattr(self, "sel_menu", None):
            self.sel_menu.set_disabled(disable)

        container_frame.ContainerFrame.set_disabled(self, disable)

    def get_options(self, opt_index=None):
        '''
        Returns a list of the option strings sorted by option index.
        '''
        if self.option_cache is None:
            return self.generate_options(opt_index)

        if opt_index is None:
            return self.option_cache
        elif opt_index == e_c.ACTIVE_ENUM_NAME:
            opt_index = getattr(self.node, "u_index", None)
            if opt_index is None:
                opt_index = len(self.option_cache) - 1

        if opt_index is None:
            opt_index = -1

        return self.option_cache.get(opt_index, None)

    def generate_options(self, opt_index=None):
        options = {i: c for c, i in self.desc['CASE_MAP'].items()}
        options[len(options)] = e_c.RAW_BYTES

        if opt_index is None:
            self.option_cache = options
            if self.sel_menu is not None:
                self.sel_menu.options_menu_sane = False
            return options
        return options.get(opt_index, None)

    def edit_apply(self=None, *, edit_state, undo=True):
        edit_info = edit_state.edit_info

        w, node = field_widget.FieldWidget.get_widget_and_node(
            nodepath=edit_state.nodepath, tag_window=edit_state.tag_window)

        if undo:
            node.u_index = edit_info.get('undo_u_index')
            u_node = edit_state.undo_node
        else:
            node.u_index = edit_info.get('redo_u_index')
            u_node = edit_state.redo_node

        if node.u_index is None:
            node.u_node = None
            node[:] = u_node
        else:
            node.u_node = u_node

        if w is not None:
            try:
                if w.desc is not edit_state.desc:
                    return

                w.needs_flushing = False
                w.set_edited()
                w.reload()
            except Exception:
                print(format_exc())

    def select_option(self, opt_index=None, force=False, reload=True):
        self.flush()
        if self.node is None:
            return

        node = self.node
        curr_index = self.sel_menu.sel_index

        if (opt_index < 0 or opt_index > self.sel_menu.max_index or
            opt_index is None or force):
            return

        undo_u_index = node.u_index
        undo_node = node.u_node
        if node.u_index is None:
            undo_node = node[:]

        if opt_index == self.sel_menu.max_index:
            # setting to rawdata
            self.node.set_active()
        else:
            self.node.set_active(opt_index)

        self.set_edited()
        # make an edit state
        if undo_u_index != node.u_index:
            self.edit_create(
                undo_u_index=undo_u_index, redo_u_index=node.u_index,
                redo_node=node[:] if node.u_index is None else node.u_node,
                undo_node=undo_node)

        self.sel_menu.sel_index = opt_index
        if reload:
            self.reload()

    def populate(self):
        try:
            old_u_node_frames = []
            for u_index in self.u_node_widgets_by_u_index:
                # delete any existing widgets
                if u_index is not None:
                    old_u_node_frames.append(
                        self.u_node_widgets_by_u_index[u_index])

            self.u_node_widgets_by_u_index.clear()
            self.u_node_widgets_by_u_index[None] = self.raw_frame

            for w in (self, self.content, self.title_label):
                w.tooltip_string = self.desc.get('TOOLTIP')

            self.display_comment(self.content)
            self.reload()

            # do things in this order to prevent the window from scrolling up
            for w in old_u_node_frames:
                w.destroy()
        except Exception:
            print(format_exc())

    def reload(self):
        try:
            # clear the f_widget_ids list
            self.f_widget_ids = []
            self.f_widget_ids_map = {}
            self.f_widget_ids_map_inv = {}
            u_index = u_node = None
            if self.node is not None:
                self.raw_label.config(text='DataUnion: %s raw bytes' %
                                      self.node.get_size())
                sel_index = self.sel_menu.sel_index
                u_index = self.node.u_index
                u_node = self.node.u_node

                new_sel_index = (self.sel_menu.max_index if
                                 u_index is None else u_index)
                if new_sel_index != self.sel_menu.sel_index:
                    self.sel_menu.sel_index = new_sel_index
                    
            u_desc = self.desc.get(u_index)
            if hasattr(u_node, 'desc'):
                u_desc = u_node.desc

            active_widget = self.u_node_widgets_by_u_index.get(u_index)
            if active_widget is None:
                if u_index is not None:
                    widget_cls = self.widget_picker.get_widget(u_desc)
                    kwargs = dict(
                        show_title=False, tag_window=self.tag_window,
                        attr_index=u_index, disabled=self.disabled,
                        f_widget_parent=self, desc=u_desc,
                        show_frame=self.show.get(), dont_padx_fields=True)

                    try:
                        active_widget = widget_cls(self.content, **kwargs)
                    except Exception:
                        print(format_exc())
                        active_widget = data_frame.NullFrame(self.content, **kwargs)
                else:
                    active_widget = self.raw_frame

                self.u_node_widgets_by_u_index[u_index] = active_widget

            wid = id(active_widget)
            self.f_widget_ids.append(wid)
            self.f_widget_ids_map[u_index] = wid
            self.f_widget_ids_map_inv[wid] = u_index
            if hasattr(active_widget, "load_node_data"):
                if active_widget.load_node_data(self.node, u_node,
                                                u_index, u_desc):
                    self.populate()
                    return
                active_widget.reload()
                active_widget.apply_style()

            self.build_f_widget_cache()
            # now that the field widgets are created, position them
            if self.show.get():
                self.pose_fields()
        except Exception:
            print(format_exc())

        self.sel_menu.update_label()
        if self.node is None:
            self.set_disabled(True)
        else:
            self.set_children_disabled(not self.node)

    def pose_fields(self):
        u_index = None if self.node is None else self.node.u_index
        w = self.u_node_widgets_by_u_index.get(u_index)
        for child in self.content.children.values():
            if child not in (w, self.comment_frame):
                child.pack_forget()

        if w:
            # by adding a fixed amount of padding, we fix a problem
            # with difficult to predict padding based on nesting
            w.pack(fill='x', anchor='nw',
                   padx=self.vertical_padx, pady=self.vertical_pady)

        self.content.pack(fill='x', anchor='nw', expand=True)
