import threadsafe_tkinter as tk
import tkinter.ttk as ttk

from traceback import format_exc

from binilla import constants
from binilla import editor_constants as e_c
from binilla.widgets.field_widgets import field_widget, data_frame


class ContainerFrame(tk.Frame, field_widget.FieldWidget):
    show = None
    import_btn = None
    export_btn = None

    def __init__(self, *args, **kwargs):
        field_widget.FieldWidget.__init__(self, *args, **kwargs)

        orient = self.desc.get('ORIENT', 'v')[:1].lower()
        assert orient in ('v', 'h')
        self.show_title = kwargs.pop('show_title', orient == 'v' and
                                     self.f_widget_parent is not None)

        # if only one sub-widget being displayed, dont display the title
        if not self.show_title or self.visible_field_count < 2:
            self.show_title = False
            self.dont_padx_fields = True

        if self.f_widget_parent is None:
            self.pack_padx = self.pack_pady = 0

        kwargs.update(relief='flat', bd=0, highlightthickness=0)

        show_frame = True
        if self.f_widget_parent is not None:
            show_frame = bool(
                kwargs.pop('show_frame', not self.blocks_start_hidden))

        if self.is_empty and self.hide_if_blank:
            show_frame = False

        tk.Frame.__init__(self, *args, **e_c.fix_kwargs(**kwargs))
        self.show = tk.BooleanVar(self)

        # if the orientation is vertical, make a title frame
        if self.show_title:
            self.show.set(show_frame)
            toggle_text = '-' if show_frame else '+'

            self.title = tk.Frame(self, relief='raised')

            self.show_btn = ttk.Checkbutton(
                self.title, width=3, text=toggle_text,
                command=self.toggle_visible, style='ShowButton.TButton')
            self.title_label = tk.Label(
                self.title, text=self.gui_name, anchor='w',
                width=self.title_size, justify='left',
                font=self.get_font("frame_title"))
            self.title_label.font_type = "frame_title"
            self.import_btn = ttk.Button(
                self.title, width=7, text='Import',
                command=self.import_node)
            self.export_btn = ttk.Button(
                self.title, width=7, text='Export',
                command=self.export_node)

            self.show_btn.pack(side="left")
            if self.gui_name != '':
                self.title_label.pack(fill="x", expand=True, side="left")
            for w in (self.export_btn, self.import_btn):
                w.pack(side="right", padx=(0, 4), pady=2)

            self.title.pack(fill="x", expand=True)
        else:
            self.show.set(True)

        self.populate()
        self._initialized = True

    def load_node_data(self, parent, node, attr_index, desc=None):
        if field_widget.FieldWidget.load_node_data(
                self, parent, node, attr_index, desc):
            # needs repopulating. can't load child node data
            return True

        return self.load_child_node_data()

    def load_child_node_data(self):
        desc = self.desc
        sub_node = None
        for wid in self.f_widgets:
            # try and load any existing FieldWidgets with appropriate node data
            w = self.f_widgets[wid]
            attr_index = self.f_widget_ids_map_inv.get(wid)
            if attr_index is None:
                return True
            elif self.node:
                sub_node = self.node[attr_index]

            if w.load_node_data(self.node, sub_node, attr_index):
                # descriptor is different. gotta repopulate self
                return True

        return False

    def unload_node_data(self):
        field_widget.FieldWidget.unload_node_data(self)
        self.unload_child_node_data()

    def unload_child_node_data(self):
        for w in self.f_widgets.values():
            if hasattr(w, "unload_node_data"):
                w.unload_node_data()

    def apply_style(self, seen=None):
        field_widget.FieldWidget.apply_style(self, seen)
        w = getattr(self, "title", None)
        if w is not None:
            w.config(bd=self.frame_depth, bg=self.frame_bg_color)

        w = getattr(self, "title_label", None)
        if w:
            if self.desc.get('ORIENT', 'v')[:1].lower() == 'v':
                w.config(bd=0, bg=self.frame_bg_color)

        #if self.show.get():
        #    self.pose_fields()

    @property
    def field_count(self):
        desc = self.desc
        try:
            return desc.get('ENTRIES', 0) + ('STEPTREE' in desc)
        except Exception:
            return 0

    @property
    def visible_field_count(self):
        desc = self.desc
        try:
            total = 0
            node = self.node
            sub_node = None
            entries = tuple(range(desc.get('ENTRIES', 0)))
            if 'STEPTREE' in desc:
                entries += ('STEPTREE',)

            for i in entries:
                sub_desc = desc[i]
                if hasattr(node, "__getitem__"):
                    sub_node = node[i]

                if hasattr(sub_node, 'desc'):
                    sub_desc = sub_node.desc

                if self.get_visible(sub_desc.get('VISIBLE', True)):
                    total += 1
            return total
        except (IndexError, KeyError, AttributeError):
            return 0

    def edit_apply(self=None, *, edit_state, undo=True):
        state = edit_state

        attr_indices = state.attr_index
        if undo:
            nodes = state.undo_node
        else:
            nodes = state.redo_node

        w, node = field_widget.FieldWidget.get_widget_and_node(
            nodepath=state.nodepath, tag_window=state.tag_window)
        for i in attr_indices:
            node[i] = nodes[i]

        if w is not None:
            try:
                if w.desc is not state.desc:
                    return

                w.needs_flushing = False
                w.reload()
                w.set_edited()
            except Exception:
                print(format_exc())

    def destroy(self):
        # These will linger and take up RAM, even if the widget is destroyed.
        # Need to remove the references manually
        self.node = self.parent = self.f_widget_parent = self.tag_window = None
        tk.Frame.destroy(self)
        self.delete_all_traces()
        self.delete_all_widget_refs()

    def populate(self):
        '''Destroys and rebuilds this widgets children.'''
        orient = self.desc.get('ORIENT', 'v')[:1].lower()
        vertical = True
        assert orient in ('v', 'h')

        content = self
        if getattr(self, 'content', None):
            content = self.content
        if self.show_title and content in (None, self):
            content = tk.Frame(self, relief="sunken", bd=self.frame_depth,
                               bg=self.default_bg_color)

        self.content = content
        # clear the f_widget_ids list
        self.f_widget_ids = []
        self.f_widget_ids_map = {}
        self.f_widget_ids_map_inv = {}

        # destroy all the child widgets of the content
        for w in self.f_widgets.values():
            w.destroy()

        node = self.node
        desc = self.desc
        picker = self.widget_picker
        tag_window = self.tag_window

        self.display_comment(self.content)

        # if the orientation is horizontal, remake its label
        if orient == 'h':
            vertical = False
            self.title_label = tk.Label(
                self, anchor='w', justify='left',
                width=self.title_size, text=self.gui_name,
                bg=self.default_bg_color, fg=self.text_normal_color)
            if self.gui_name != '':
                self.title_label.pack(fill="x", side="left")

            self.sidetip_label = tk.Label(
                self, anchor='w', justify='left',
                bg=self.default_bg_color, fg=self.text_normal_color)

        for w in (self, self.content):
            w.tooltip_string = self.desc.get('TOOLTIP')
        if getattr(self, 'title', None):
            self.title.tooltip_string = self.tooltip_string
        if getattr(self, 'title_label', None):
            self.title_label.tooltip_string = self.tooltip_string

        field_indices = range(desc['ENTRIES'])
        # if the node has a steptree node, include its index in the indices
        if 'STEPTREE' in desc:
            field_indices = tuple(field_indices) + ('STEPTREE',)

        kwargs = dict(parent=node, tag_window=tag_window, f_widget_parent=self,
                      disabled=self.disabled, vert_oriented=vertical)

        visible_field_count = self.visible_field_count
        # if only one sub-widget being displayed, dont
        # display the title of the widget being displayed
        if self.field_count != visible_field_count and visible_field_count < 2:
            if 'STEPTREE' not in desc or not self.get_visible(
                    desc['STEPTREE'].get('VISIBLE', True)):
                # only make the title not shown if the only
                # visible widget will not be the subtree
                kwargs.update(show_title=False)
            kwargs.update(dont_padx_fields=True)

        if self.dont_padx_fields:
            kwargs.update(pack_padx=0)
        elif visible_field_count < 2 and not self.show_title:
            # Use this widgets x padding amount so that its
            # singular child appears where this widget would.
            kwargs.update(use_parent_pack_padx=True)

        # loop over each field and make its widget
        sub_node = None
        for i in field_indices:
            sub_desc = desc[i]
            if hasattr(node, "__getitem__"):
                sub_node = node[i]

            if hasattr(sub_node, 'desc'):
                sub_desc = sub_node.desc

            # if the field shouldnt be visible, dont make its widget
            if not self.get_visible(sub_desc.get('VISIBLE', True)):
                continue

            widget_cls = picker.get_widget(sub_desc)
            if i == field_indices[-1] and vertical:
                kwargs.update(pack_pady=0)

            try:
                widget = widget_cls(content, node=sub_node,
                                    attr_index=i, desc=sub_desc, **kwargs)
            except Exception:
                print(format_exc())
                widget = data_frame.NullFrame(
                    content, node=sub_node, attr_index=i, desc=sub_desc, **kwargs)

            wid = id(widget)
            self.f_widget_ids.append(wid)
            self.f_widget_ids_map[i] = wid
            self.f_widget_ids_map_inv[wid] = i

        self.build_f_widget_cache()

        # now that the field widgets are created, position them
        if self.show.get():
            self.pose_fields()

    def reload(self):
        '''Resupplies the nodes to the widgets which display them.'''
        try:
            # if any of the descriptors are different between
            # the sub-nodes of the previous and new sub-nodes,
            # then this widget will need to be repopulated.
            if self.load_child_node_data():
                self.populate()
                self.apply_style()
                return

            for wid in self.f_widget_ids:
                self.f_widgets[wid].reload()

        except Exception:
            print(format_exc())

    def set_disabled(self, disable=True):
        disable = disable or not self.editable
        if self.node is None and not disable:
            return

        self.set_children_disabled(disable)
        if bool(disable) != self.disabled:
            for w in (self.import_btn, self.export_btn):
                if w:
                    w.config(state=tk.DISABLED if disable else tk.NORMAL)

        field_widget.FieldWidget.set_disabled(self, disable)

    def set_children_disabled(self, disable=True):
        for w in self.f_widgets.values():
            if hasattr(w, "set_disabled"):
                w.set_disabled(disable)

    def flush(self):
        '''Flushes values from the widgets to the nodes they are displaying.'''
        if self.node is None:
            return

        try:
            for w in self.f_widgets.values():
                if hasattr(w, 'flush'):
                    w.flush()
            self.set_needs_flushing(False)
        except Exception:
            print(format_exc())

    def pose_fields(self):
        orient = self.desc.get('ORIENT', 'v')[:1].lower()

        if self.desc.get("PORTABLE", True):
            if getattr(self, "import_btn", None):
                self.set_import_disabled(False)
            if getattr(self, "export_btn", None):
                self.set_export_disabled(False)
        else:
            if getattr(self, "import_btn", None):
                self.set_import_disabled()
            if getattr(self, "export_btn", None):
                self.set_export_disabled()

        side = 'left' if orient == 'h' else 'top'
        for wid in self.f_widget_ids:
            w = self.f_widgets[wid]
            w.pack(fill='x', side=side, anchor='nw',
                   padx=w.pack_padx, pady=w.pack_pady)

        if self.content is not self:
            self.content.pack(fill='x', side=side, anchor='nw', expand=True)

        if not self.show_sidetips:
            return

        sidetip = self.desc.get('SIDETIP')
        if orient == 'h' and sidetip and getattr(self, 'sidetip_label', None):
            self.sidetip_label.config(text=sidetip)
            self.sidetip_label.pack(fill="x", side="left")

    def set_import_disabled(self, disable=True):
        '''Disables the import button if disable is True. Enables it if not.'''
        if disable: self.import_btn.config(state="disabled")
        else:       self.import_btn.config(state="normal")

    def set_export_disabled(self, disable=True):
        '''Disables the export button if disable is True. Enables it if not.'''
        if disable: self.export_btn.config(state="disabled")
        else:       self.export_btn.config(state="normal")

    def toggle_visible(self):
        self.set_collapsed(self.show.get())

    def set_collapsed(self, collapse=True):
        if self.content is self:
            # dont do anything if there is no specific "content" frame to hide
            return
        elif collapse:
            self.content.forget()
            self.show_btn.configure(text='+')
        else:
            self.pose_fields()
            self.show_btn.configure(text='-')
        self.show.set(not collapse)
