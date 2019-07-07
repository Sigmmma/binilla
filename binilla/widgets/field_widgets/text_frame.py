import threadsafe_tkinter as tk

from traceback import format_exc

from binilla.widgets.field_widgets import field_widget, data_frame


class TextFrame(data_frame.DataFrame):
    '''Used for strings that likely will not fit on one line.'''

    children_can_scroll = True
    can_scroll = False
    _flushing = False

    replace_map = None
    data_text = None

    def __init__(self, *args, **kwargs):
        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)
        data_frame.DataFrame.__init__(self, *args, **kwargs)

        # make the widgets
        self.content = tk.Frame(self, relief='flat', bd=0)

        self.title_label = tk.Label(
            self.content, text=self.gui_name, justify='left', anchor='w',
            disabledforeground=self.text_disabled_color, width=self.title_size)

        self.data_text = tk.Text(
            self.content, wrap=tk.NONE, maxundo=self.max_undos, undo=True,
            height=self.textbox_height, width=self.textbox_width,
            state=tk.DISABLED if self.disabled else tk.NORMAL)

        self.sidetip_label = tk.Label(
            self.content, anchor='w', justify='left')

        self.hsb = tk.Scrollbar(self.content, orient='horizontal',
                                command=self.data_text.xview)
        self.vsb = tk.Scrollbar(self.content, orient='vertical',
                                command=self.data_text.yview)
        self.data_text.config(xscrollcommand=self.hsb.set,
                              yscrollcommand=self.vsb.set)

        self.hsb.can_scroll = self.children_can_scroll
        self.vsb.can_scroll = self.children_can_scroll
        self.data_text.can_scroll = self.children_can_scroll
        self.hsb.f_widget_parent = self
        self.vsb.f_widget_parent = self
        self.data_text.f_widget_parent = self

        self.data_text.bind('<FocusOut>', self.flush)
        self.data_text.bind('<Return>', self.set_modified)
        self.data_text.bind('<Any-KeyPress>', self.set_modified)
        self.data_text.text_undo = self._text_undo
        self.data_text.text_redo = self._text_redo
        self.data_text.bind('<Control-z>', self.disable_undo_redo)
        self.data_text.bind('<Control-y>', self.disable_undo_redo)

        if self.gui_name != '':
            self.title_label.pack(fill="x")
        self.hsb.pack(side="bottom", fill='x', expand=True)
        self.vsb.pack(side="right",  fill='y')
        self.data_text.pack(side="right", fill="x", expand=True)
        self.content.pack(fill="both", expand=True)

        self.build_replace_map()

        self.reload()
        self._initialized = True

    def _text_undo(self):
        if not self.data_text: return
        self.data_text.config(undo=True)
        try:
            self.data_text.edit_undo()
        except Exception:
            pass

    def _text_redo(self):
        if not self.data_text: return
        self.data_text.config(undo=True)
        try:
            self.data_text.edit_redo()
        except Exception:
            pass

    def unload_node_data(self):
        field_widget.FieldWidget.unload_node_data(self)
        if not self.data_text: return
        self.data_text.config(state=tk.NORMAL)
        self.data_text.delete(1.0, tk.END)
        self.data_text.insert(1.0, "")
        if self.disabled:
            self.data_text.config(state=tk.DISABLED)
        else:
            self.data_text.config(state=tk.NORMAL)

    def set_disabled(self, disable=True):
        disable = disable or not self.editable
        if self.node is None and not disable:
            return

        if self.data_text and bool(disable) != self.disabled:
            self.data_text.config(state=tk.DISABLED if disable else tk.NORMAL)
        data_frame.DataFrame.set_disabled(self, disable)

    def disable_undo_redo(self, *args, **kwargs):
        if not self.data_text: return
        # disable the undo/redo ability of the text so we can call it ourselves
        self.data_text.config(undo=False)

    def edit_apply(self=None, *, edit_state, undo=True):
        attr_index = edit_state.attr_index

        w_parent, parent = field_widget.FieldWidget.get_widget_and_node(
            nodepath=edit_state.nodepath, tag_window=edit_state.tag_window)

        if undo:
            parent[attr_index] = edit_state.undo_node
        else:
            parent[attr_index] = edit_state.redo_node

        if w_parent is not None:
            try:
                w = w_parent.f_widgets[
                    w_parent.f_widget_ids_map[attr_index]]
                if w.desc is not edit_state.desc:
                    return

                w.node = parent[attr_index]
                w.set_edited()
                w.reload()
            except Exception:
                print(format_exc())

    def set_modified(self, e=None):
        if None in (self.parent, self.node) or self.needs_flushing:
            return

        self.set_needs_flushing()
        self.set_edited()

    def build_replace_map(self):
        desc = self.desc
        enc = desc['TYPE'].enc
        c_size = desc['TYPE'].size
        endian = 'big' if desc['TYPE'].endian == '>' else 'little'

        self.replace_map = {}
        if not enc:
            return

        # this is the header of what the first
        # 16 characters will be replaced with.
        hex_head = '\\0x0'

        # add a null and return character to the end of it so it can
        # be distinguished from users typing \x00 or \xff and whatnot.
        hex_foot = b'\x00' * c_size
        if endian == 'little':
            hex_foot = b'\x00' * (c_size - 1) + b'\x0d'
            hex_foot = b'\x00' * (c_size - 1) + b'\x0a'
        else:
            hex_foot = b'\x0d' + (b'\x00' * (c_size - 1))
            hex_foot = b'\x0a' + (b'\x00' * (c_size - 1))
        hex_foot = hex_foot.decode(encoding=enc)

        for i in range(0, 32):
            if i in (9, 10, 13):
                # formatting characters
                continue
            elif i == 16:
                hex_head = '\\0x'

            byte_str = i.to_bytes(c_size, endian).decode(encoding=enc)
            self.replace_map[byte_str] = hex_head + hex(i)[2:] + hex_foot

    def flush(self, *args):
        if None in (self.parent, self.node):
            return
        elif self._flushing or not self.needs_flushing:
            return

        try:
            self._flushing = True
            desc = self.desc
            f_type = desc['TYPE']
            node_cls = desc.get('NODE_CLS', f_type.node_cls)
            if node_cls is type(None):
                self._flushing = False
                return

            new_node = self.data_text.get(1.0, "%s-1chars" % tk.END)

            # NEED TO DO THIS SORTED cause the /x00 we inserted will be janked
            for b in sorted(self.replace_map.keys()):
                new_node = new_node.replace(self.replace_map[b], b)

            new_node = node_cls(new_node)
            if self.node != new_node:
                field_max = self.field_max
                if field_max is None:
                    field_max = desc.get('SIZE')

                if self.enforce_max and isinstance(field_max, int):
                    field_size = f_type.sizecalc(new_node, parent=self.parent,
                                                 attr_index=self.attr_index)
                    if field_size > field_max:
                        raise ValueError(
                            ("Max size for the '%s' text field is %s bytes, " +
                             "however %s bytes of data were entered.") % (
                                 self.gui_name, field_max, field_size))

                # make an edit state
                self.edit_create(undo_node=self.node, redo_node=new_node)
                self.parent[self.attr_index] = self.node = new_node

            self._flushing = False
            self.set_needs_flushing(False)
        except Exception:
            self._flushing = False
            self.set_needs_flushing(False)
            print(format_exc())

    def reload(self):
        try:
            new_text = "" if self.node is None else str(self.node)
            # NEED TO DO THIS SORTED cause the /x00 we insert will be mesed up
            for b in sorted(self.replace_map.keys()):
                new_text = new_text.replace(b, self.replace_map[b])

            # set this to true so the StringVar trace function
            # doesnt think the widget has been edited by the user
            self.needs_flushing = True
            self.data_text.config(state=tk.NORMAL)
            self.data_text.delete(1.0, tk.END)
            self.data_text.insert(1.0, new_text)

            self.last_flushed_val = new_text
            self.data_text.edit_reset()
            self.needs_flushing = False
        except Exception:
            print(format_exc())
        finally:
            if self.disabled:
                self.data_text.config(state=tk.DISABLED)
            else:
                self.data_text.config(state=tk.NORMAL)

        sidetip = self.desc.get('SIDETIP')
        if self.show_sidetips and sidetip:
            self.sidetip_label.config(text=sidetip)
            self.sidetip_label.pack(fill="x", side="left")

        for w in (self, self.content, self.title_label,
                  self.data_text, self.sidetip_label):
            w.tooltip_string = self.desc.get('TOOLTIP')

    populate = reload
