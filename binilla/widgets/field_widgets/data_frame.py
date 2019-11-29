import threadsafe_tkinter as tk
import tkinter.ttk as ttk

from traceback import format_exc

from supyr_struct.buffer import get_rawdata_context

from binilla import editor_constants as e_c
from binilla.widgets.field_widgets import field_widget
from binilla.windows.filedialog import askopenfilename


class DataFrame(field_widget.FieldWidget, tk.Frame):

    def __init__(self, *args, **kwargs):
        kwargs.update(bg=self.default_bg_color)
        field_widget.FieldWidget.__init__(self, *args, **kwargs)
        tk.Frame.__init__(self, *args, **e_c.fix_kwargs(**kwargs))

    def destroy(self):
        # These will linger and take up RAM, even if the widget is destroyed.
        # Need to remove the references manually
        self.node = self.parent = self.f_widget_parent = self.tag_window = None
        tk.Frame.destroy(self)
        self.delete_all_traces()
        self.delete_all_widget_refs()

    def populate(self):
        pass

    def pose_fields(self):
        pass

    def flush(self):
        '''Flushes values from the widgets to the nodes they are displaying.'''
        raise NotImplementedError("This method must be overloaded")

    def reload(self):
        '''Resupplies the nodes to the widgets which display them.'''
        raise NotImplementedError("This method must be overloaded")


class NullFrame(DataFrame):
    '''This FieldWidget is meant to represent an unknown field.'''
    def __init__(self, *args, **kwargs):
        DataFrame.__init__(self, *args, **kwargs)
        self.populate()

    def flush(self): pass

    def populate(self):
        self.title_label = tk.Label(
            self, text=self.gui_name, width=self.title_size, anchor='w',
            disabledforeground=self.text_disabled_color)
        self.field_type_name = tk.Label(
            self, text='<%s>' % self.desc['TYPE'].name,
            anchor='w', justify='left',
            disabledforeground=self.text_disabled_color)

        for w in (self, self.title_label, self.field_type_name):
            w.tooltip_string = self.desc.get('TOOLTIP')

        # now that the field widgets are created, position them
        self.pose_fields()
        self._initialized = True

    def pose_fields(self):
        if self.gui_name != '':
            self.title_label.pack(side='left')
        self.field_type_name.pack(side='left', fill="x")

    def reload(self): pass


class RawdataFrame(DataFrame):

    def __init__(self, *args, **kwargs):
        DataFrame.__init__(self, *args, **kwargs)
        self.populate()
        self._initialized = True

    def flush(self): pass

    @property
    def field_ext(self):
        desc = self.desc
        parent_name = tag_ext = ''
        try:
            if self.parent is None:
                tag_ext = self.node.get_root().ext
            else:
                tag_ext = self.parent.get_root().ext
        except Exception: pass

        try: parent_name = '.' + self.parent.desc['NAME']
        except Exception: pass

        return desc.get('EXT', '%s%s.%s' %
                        (tag_ext, parent_name, desc['NAME']))

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

    def populate(self):
        self.title_label = tk.Label(
            self, text=self.gui_name, width=self.title_size, anchor='w',
            disabledforeground=self.text_disabled_color)

        self.tooltip_string = self.desc.get('TOOLTIP')
        self.title_label.tooltip_string = self.tooltip_string
        for w in (self, self.title_label):
            w.tooltip_string = self.desc.get('TOOLTIP')

        self.import_btn = ttk.Button(
            self, width=6, text='Import',
            command=self.import_node)
        self.export_btn = ttk.Button(
            self, width=6, text='Export',
            command=self.export_node)
        self.delete_btn = ttk.Button(
            self, width=6, text='Delete',
            command=self.delete_node)

        # now that the field widgets are created, position them
        self.pose_fields()

    def set_disabled(self, disable=True):
        disable = disable or not self.editable
        if self.node is None and not disable:
            return

        if bool(disable) != self.disabled:
            for w in (self.import_btn, self.export_btn, self.delete_btn):
                if w:
                    w.config(state=tk.DISABLED if disable else tk.NORMAL)

        DataFrame.set_disabled(self, disable)

    def delete_node(self):
        if None in (self.parent, self.node):
            return

        curr_size = None
        index = self.attr_index

        try:
            undo_node = self.node
            curr_size = self.parent.get_size(attr_index=index)
            try:
                self.parent.set_size(0, attr_index=index)
                new_size = self.parent.get_size(index)
            except Exception:
                # sometimes rawdata has an explicit size, so an exception
                # will be raised when trying to change it. just ignore it
                new_size = curr_size

            self.parent.parse(rawdata=b'\x00'*new_size, attr_index=index)
            self.node = self.parent[index]
            self.set_edited()

            self.edit_create(undo_node=undo_node, redo_node=self.node)

            # until i come up with a better method, i'll have to rely on
            # reloading the root field widget so sizes will be updated
            try:
                root = self.f_widget_parent
                while hasattr(root, 'f_widget_parent'):
                    if root.f_widget_parent is None:
                       break
                    root = root.f_widget_parent

                root.reload()
            except Exception:
                print(format_exc())
                print("Could not reload after deleting '%s' node." % self.name)
        except Exception:
            print(format_exc())
            print("Could not delete '%s' node." % self.name)
            if curr_size is None:
                pass
            elif hasattr(self.node, 'parse'):
                self.node.set_size(curr_size)
            else:
                self.parent.set_size(curr_size, attr_index=index)

    def import_node(self):
        '''Prompts the user for an exported node file.
        Imports data into the node from the file.'''
        if None in (self.parent, self.node):
            return

        try:
            initialdir = self.tag_window.app_root.last_load_dir
        except AttributeError:
            initialdir = None

        ext = self.field_ext

        filepath = askopenfilename(
            initialdir=initialdir, defaultextension=ext,
            filetypes=[(self.name, "*" + ext), ('All', '*')],
            title="Import '%s' from..." % self.name, parent=self)

        if not filepath:
            return

        curr_size = None
        index = self.attr_index

        try:
            undo_node = self.node
            curr_size = self.parent.get_size(attr_index=index)

            with get_rawdata_context(writable=False, filepath=filepath) as rawdata:
                try:
                    self.parent.set_size(len(rawdata), attr_index=index)
                except Exception:
                    # sometimes rawdata has an explicit size, so an exception
                    # will be raised when trying to change it. just ignore it
                    pass

                self.parent.parse(rawdata=rawdata, attr_index=index)
                self.node = self.parent[index]
                self.set_edited()

                self.edit_create(undo_node=undo_node, redo_node=self.node)

                # until i come up with a better method, i'll have to rely on
                # reloading the root field widget so stuff(sizes) will be updated
                try:
                    root = self.f_widget_parent
                    while hasattr(root, 'f_widget_parent'):
                        if root.f_widget_parent is None:
                           break
                        root = root.f_widget_parent

                    root.reload()
                except Exception:
                    print(format_exc())
                    print("Could not reload after importing '%s' node." % self.name)
        except Exception:
            print(format_exc())
            print("Could not import '%s' node." % self.name)
            if curr_size is None:
                pass
            elif hasattr(self.node, 'parse'):
                self.node.set_size(curr_size)
            else:
                self.parent.set_size(curr_size, attr_index=index)

    def pose_fields(self):
        padx, pady = self.horizontal_padx, self.horizontal_pady
        if self.gui_name != '':
            self.title_label.pack(side='left')
        self.import_btn.pack(side='left', fill="x", padx=padx, pady=pady)
        self.export_btn.pack(side='left', fill="x", padx=padx, pady=pady)
        self.delete_btn.pack(side='left', fill="x", padx=padx, pady=pady)

    def reload(self): pass


class VoidFrame(DataFrame):
    '''This FieldWidget is blank, as the matching field represents nothing.'''

    def __init__(self, *args, **kwargs):
        DataFrame.__init__(self, *args, **kwargs)
        self.populate()
        self._initialized = True

    def flush(self): pass

    def populate(self):
        self.title_label = tk.Label(
            self, text=self.gui_name, width=self.title_size, anchor='w',
            disabledforeground=self.text_disabled_color)
        self.field_type_name = tk.Label(
            self, text='<VOIDED>', anchor='w', justify='left',
            disabledforeground=self.text_disabled_color)

        for w in (self, self.title_label, self.field_type_name):
            w.tooltip_string = self.desc.get('TOOLTIP')

        # now that the field widgets are created, position them
        self.pose_fields()

    def pose_fields(self):
        if self.gui_name != '':
            self.title_label.pack(side='left')
        self.field_type_name.pack(side='left', fill="x")

    def reload(self): pass


class PadFrame(VoidFrame):
    '''This FieldWidget is blank, as the matching field represents nothing.'''

    def __init__(self, *args, **kwargs):
        kwargs.update(bg=self.default_bg_color, pack_padx=0, pack_pady=0)
        DataFrame.__init__(self, *args, **kwargs)
        self._initialized = True

    def populate(self): pass

    def pose_fields(self):
        if self.gui_name != '':
            self.title_label.pack(side='left')
        self.field_type_name.pack(side='left', fill="x")
        for w in (self, self.field_type_name):
            w.tooltip_string = self.desc.get('TOOLTIP')
