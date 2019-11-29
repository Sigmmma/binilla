import os
import threadsafe_tkinter as tk
import tkinter.ttk as ttk

from tkinter import messagebox
from traceback import format_exc

from binilla.edit_manager import EditState
from binilla import constants
from binilla import editor_constants as e_c
from binilla.widgets.binilla_widget import BinillaWidget
from binilla.windows.filedialog import asksaveasfilename, askopenfilename


# These classes are used for laying out the visual structure
# of many sub-widgets, and effectively the whole window.
class FieldWidget(BinillaWidget):
    '''
    Provides the basic methods and attributes for widgets
    to utilize and interact with supyr_structs node trees.

    This class is meant to be subclassed, and is
    not actually a tkinter widget class itself.
    '''
    # the data or Block this widget exposes to viewing/editing
    node = None
    # the parent of the node
    parent = None
    # the provided descriptor of the node
    _desc = None
    # the index the node is in in the parent. If this is not None,
    # it must be valid to use parent[attr_index] to get the node.
    attr_index = None

    # whether or not to clone the node when exporting it
    export_clone = False
    # whether or not to calculate pointers for the node when exporting it
    export_calc_pointers = False

    tag_window = None

    # the FieldWidget that contains this one. If this is None,
    # it means that this is the root of the FieldWidget tree.
    f_widget_parent = None

    # a mapping of {id(f_widget): f_widget} for each child
    # FieldWidget of this object.
    f_widgets = ()

    # a list of the id's of the widgets that are parented
    # to this widget, in the order that they were created
    f_widget_ids = ()

    # the mapping is {attr_index: id(f_widget)}
    # a mapping that maps each field widget's id to the attr_index
    # it is under in its parent, which is this widgets node.
    f_widget_ids_map = ()

    # an inverse mapping of f_widget_ids_map
    f_widget_ids_map_inv = ()

    content = None
    comment_label = None
    comment_frame = None

    # the amount of external padding this widget needs
    _pack_padx = 0
    _pack_pady = 0

    # whether or not this FieldWidget's title is shown
    dont_padx_fields = False
    _show_title = True
    _use_parent_pack_padx = False
    _use_parent_pack_pady = False

    # whether the widget is being oriented vertically or horizontally
    _vert_oriented = True

    show_button_style = None

    # whether or not this widget can use the scrollwheel when selected.
    # setting this to True prevents the TagWindow from scrolling when
    # using the mousewheel if this widget is the one currently in focus
    can_scroll = False

    # same as the above, but for this widgets children
    children_can_scroll = False

    # whether or not to disable using this widget and its children
    disabled = False

    # whether or not something in this FieldWidget has been edited.
    edited = False

    # whether or not a widget needs to have its content flushed to the node
    needs_flushing = False

    # whether or not the widget has been fully initialized
    _initialized = False

    def __init__(self, *args, **kwargs):
        BinillaWidget.__init__(self)

        self.f_widgets = {}
        self.f_widget_ids = []
        self.f_widget_ids_map = {}
        self.f_widget_ids_map_inv = {}
        self.content = self
        self._desc = kwargs.get('desc', self._desc)
        self.tag_window = kwargs.get('tag_window', None)
        self.f_widget_parent = kwargs.get('f_widget_parent', None)
        self._vert_oriented = bool(kwargs.get('vert_oriented', True))
        self.export_clone = bool(kwargs.get('export_clone', self.export_clone))
        self.export_calc_pointers = bool(kwargs.get('export_calc_pointers',
                                                    self.export_calc_pointers))
        self.dont_padx_fields = kwargs.get('dont_padx_fields',
                                           self.dont_padx_fields)
        self.use_parent_pack_padx = kwargs.get('use_parent_pack_padx',
                                               self.use_parent_pack_padx)
        self.use_parent_pack_pady = kwargs.get('use_parent_pack_pady',
                                               self.use_parent_pack_pady)

        self.load_node_data(kwargs.get('parent', None),
                            kwargs.get('node', None),
                            kwargs.get('attr_index', None),
                            kwargs.get('desc', None))

        # default to self editability for disable state, but
        # change to disabled if parent explicitely says to
        self.disabled = not self.editable
        if kwargs.get('disabled', False):
            self.disabled = True

        # make sure a button style exists for the 'show' button
        if FieldWidget.show_button_style is None:
            FieldWidget.show_btn_style = ttk.Style()
            FieldWidget.show_btn_style.configure('ShowButton.TButton',
                                                 background=self.frame_bg_color)

        # if custom padding is given, set it
        if not self.use_parent_pack_padx:
            if 'pack_padx' in kwargs:
                self.pack_padx = kwargs['pack_padx']
            elif self._vert_oriented:
                self.pack_padx = self.vertical_padx
            else:
                self.pack_padx = self.horizontal_padx

        if not self.use_parent_pack_pady:
            if 'pack_pady' in kwargs:
                self.pack_pady = kwargs['pack_pady']
            elif self._vert_oriented:
                self.pack_pady = self.vertical_pady
            else:
                self.pack_pady = self.horizontal_pady

    def apply_style(self, seen=None):
        BinillaWidget.apply_style(self, seen)
        if self.comment_frame:
            self.comment_frame.config(bd=self.comment_depth,
                                      bg=self.comment_bg_color)

        if self.comment_label:
            self.comment_label.config(bg=self.comment_bg_color,
                                      fg=self.text_normal_color)

    def get_visible(self, visibility_level):
        try:
            return self.tag_window.get_visible(visibility_level)
        except Exception:
            return (visibility_level is None or
                    visibility_level >= constants.VISIBILITY_SHOWN)

    @property
    def is_empty(self):
        return getattr(self, "node", None) is None

    @property
    def blocks_start_hidden(self):
        try:
            return bool(self.tag_window.widget_flags.blocks_start_hidden)
        except Exception:
            return True

    @property
    def evaluate_entry_fields(self):
        try:
            return bool(self.tag_window.widget_flags.evaluate_entry_fields)
        except Exception:
            return False

    @property
    def hide_if_blank(self):
        try:
            return bool(self.tag_window.widget_flags.empty_blocks_start_hidden)
        except Exception:
            return False

    @property
    def enforce_max(self):
        try:
            return bool(self.tag_window.enforce_max)
        except Exception:
            return True

    @property
    def enforce_min(self):
        try:
            return bool(self.tag_window.enforce_min)
        except Exception:
            return True

    @property
    def use_gui_names(self):
        try:
            return bool(self.tag_window.use_gui_names)
        except Exception:
            return True

    @property
    def editable(self):
        try:
            return self.desc.get('EDITABLE', True) or self.all_editable
        except Exception:
            return self.all_editable

    @property
    def all_editable(self):
        try:
            return bool(self.tag_window.all_editable)
        except Exception:
            return False

    @property
    def all_bools_visible(self):
        try:
            return bool(self.tag_window.all_bools_visible)
        except Exception:
            return False

    @property
    def show_comments(self):
        try:
            return bool(self.tag_window.show_comments)
        except Exception:
            return False

    @property
    def show_sidetips(self):
        try:
            return bool(self.tag_window.show_sidetips)
        except Exception:
            return False

    @property
    def max_undos(self):
        try:
            return bool(self.tag_window.max_undos)
        except Exception:
            pass
        return 0

    @property
    def desc(self):
        if self._desc is not None:
            return self._desc
        elif hasattr(self.node, 'desc'):
            return self.node.desc
        elif hasattr(self.parent, 'desc') and self.attr_index is not None:
            desc = self.parent.desc
            if desc['TYPE'].is_array:
                return desc['SUB_STRUCT']
            return desc[self.attr_index]
        raise AttributeError("Cannot locate a descriptor for this node.")

    @property
    def field_default(self):
        desc = self.desc
        return desc.get('DEFAULT', desc['TYPE'].default())

    @property
    def field_ext(self):
        '''The export extension of this FieldWidget.'''
        desc = self.desc
        try:
            if self.parent is None:
                tag_ext = self.node.get_root().ext
            else:
                tag_ext = self.parent.get_root().ext
        except Exception:
            tag_ext = ''
        return desc.get('EXT', '%s.%s' % (tag_ext, desc['NAME']))

    @property
    def field_max(self):
        desc = self.desc
        return desc.get('MAX', desc['TYPE'].max)

    @property
    def field_min(self):
        desc = self.desc
        return desc.get('MIN', desc['TYPE'].min)

    @property
    def field_size(self):
        desc = self.desc
        f_type = desc['TYPE']
        field_size = desc.get('SIZE', f_type.size)
        if not isinstance(field_size, int):
            if hasattr(self.parent, "get_size"):
                field_size = self.parent.get_size(self.attr_index)
            else:
                field_size = 0

        return field_size

    @property
    def is_bit_based(self):
        desc = self.desc
        return desc['TYPE'].is_bit_based

    @property
    def unit_scale(self):
        desc = self.desc
        unit_scale = desc.get('UNIT_SCALE')
        if hasattr(unit_scale, '__call__'):
            unit_scale = unit_scale(f_widget=self)
        return unit_scale

    @property
    def gui_name(self):
        '''The gui_name of the node of this FieldWidget.'''
        name = self.name.replace('_', ' ')
        if self.use_gui_names:
            name = self.desc.get('GUI_NAME', name)

        if self.desc.get('TOOLTIP') and name:
            name += " �"

        return name

    @property
    def show_title(self):
        return self._show_title and not self.desc.get('HIDE_TITLE', False)

    @show_title.setter
    def show_title(self, new_val):
        self._show_title = new_val

    @property
    def name(self):
        '''The name of the node of this FieldWidget.'''
        return self.desc['NAME']

    @property
    def title_size(self):
        if self._vert_oriented:
            return self.title_width
        return 0

    @property
    def widget_width(self):
        desc = self.desc
        if 'WIDGET_WIDTH' in desc:
            return desc['WIDGET_WIDTH']
        return 0

    @property
    def widget_picker(self):
        try:
            return self.tag_window.widget_picker
        except AttributeError:
            if "widget_picker" not in globals():
                global widget_picker
                from binilla import widget_picker

        return widget_picker.def_widget_picker

    @property
    def pack_padx(self):
        if self.use_parent_pack_padx:
            return self.f_widget_parent.pack_padx
        return self._pack_padx

    @pack_padx.setter
    def pack_padx(self, new_val):
        self._pack_padx = new_val

    @property
    def pack_pady(self):
        if self.use_parent_pack_pady:
            return self.f_widget_parent.pack_pady
        return self._pack_pady

    @pack_pady.setter
    def pack_pady(self, new_val):
        self._pack_pady = new_val

    @property
    def use_parent_pack_padx(self):
        return bool(self.f_widget_parent) and self._use_parent_pack_padx

    @use_parent_pack_padx.setter
    def use_parent_pack_padx(self, new_val):
        self._use_parent_pack_padx = bool(new_val)

    @property
    def use_parent_pack_pady(self):
        return bool(self.f_widget_parent) and self._use_parent_pack_pady

    @use_parent_pack_pady.setter
    def use_parent_pack_pady(self, new_val):
        self._use_parent_pack_pady = bool(new_val)

    def display_comment(self, master=None):
        if not self.show_comments:
            return

        desc = self.desc
        comment = desc.get('COMMENT')
        try:
            self.comment_frame.destroy()
            self.comment_frame = None
        except Exception: pass

        if comment:
            if master is None:
                master = self
            self.comment_frame = tk.Frame(
                master, relief='sunken', bd=self.comment_depth,
                bg=self.comment_bg_color)

            self.comment_label = tk.Label(
                self.comment_frame, text=comment, anchor='nw',
                justify='left', font=self.get_font("comment"),
                bg=self.comment_bg_color, fg=self.text_normal_color)
            self.comment_label.font_type = "comment"
            self.comment_label.pack(side='left', fill='both', expand=True)
            self.comment_frame.pack(fill='both', expand=True)

    def edit_apply(self=None, *, edit_state, undo=True):
        '''This function will apply the given edit state to this widget'''
        raise NotImplementedError

    def edit_create(self, **kwargs):
        kwargs.setdefault('apply_func', self.edit_apply)
        kwargs.setdefault('attr_index', self.attr_index)
        kwargs.setdefault('parent', self.parent)
        kwargs.setdefault('tag_window', self.tag_window)
        kwargs.setdefault('desc', self.desc)
        if 'nodepath' not in kwargs:
            kwargs['nodepath'] = nodepath = []
            parent = self
            try:
                while parent.f_widget_parent:
                    nodepath.insert(0, parent.attr_index)
                    parent = parent.f_widget_parent
            except AttributeError:
                pass
            except Exception:
                print(format_exc())
        self.edit_state_add(EditState(**kwargs))

    def edit_state_add(self, edit_state):
        try: self.tag_window.edit_state_add(edit_state)
        except AttributeError: pass

    def edit_clear(self):
        try: self.tag_window.edit_clear()
        except AttributeError: pass

    def edit_clear_warn(self):
        clear = False
        try:
            # if the edit_index is zero, we can clear the history
            # without worry since there is nothing to undo to.
            if not self.tag_window.edit_manager.edit_index:
                clear = True
        except AttributeError:
            pass

        if not clear:
            clear = messagebox.askyesno(
                "Edit history clear.",
                "This operation will clear all of the undo history!\n" +
                "Are you sure you want to continue?",
                icon='warning', parent=self)

        if clear:
            self.edit_clear()

        return clear

    def get_widget(widget=None, *, nodepath, tag_window=None):
        if tag_window is None:
            tag_window = widget.tag_window

        if widget is None:
            widget = tag_window.field_widget

        try:
            # loop over each attr_index in the nodepath
            for i in nodepath:
                i = widget.desc.get('NAME_MAP', {}).get(i, i)
                widget = widget.f_widgets[widget.f_widget_ids_map[i]]
        except (AttributeError, KeyError):
            pass
        except Exception:
            print(format_exc())

        return widget

    def get_widget_and_node(widget=None, *, nodepath, tag_window=None):
        try:
            if tag_window is None:
                tag_window = widget.tag_window

            if widget is None:
                widget = tag_window.field_widget

            node = widget.node
            try:
                # loop over each attr_index in the nodepath
                for i in nodepath:
                    new_node = node[i]
                    # make sure the node can be navigated from
                    if not hasattr(new_node, 'parent'):
                        break
                    node = new_node

                    if widget is None:
                        continue

                    try:
                        widget = widget.f_widgets[widget.f_widget_ids_map[i]]
                    except Exception:
                        widget = None
            except (AttributeError, KeyError):
                pass
            except Exception:
                print(format_exc())

            return widget, node
        except Exception:
            return None, None

    def export_node(self):
        if self.node is None:
            return

        '''Prompts the user for a location to export the node and exports it'''
        try:
            initialdir = self.tag_window.app_root.last_load_dir
        except AttributeError:
            initialdir = None

        def_ext = self.field_ext

        filepath = asksaveasfilename(
            initialdir=initialdir, title="Export '%s' to..." % self.name,
            parent=self, filetypes=[(self.name, '*' + def_ext),
                                    ('All', '*')])

        if not filepath:
            return

        filepath, ext = os.path.splitext(filepath)
        if not ext: ext = def_ext
        filepath += ext

        try:
            if hasattr(self.node, 'serialize'):
                self.node.serialize(filepath=filepath, clone=self.export_clone,
                                    calc_pointers=self.export_calc_pointers)
            else:
                # the node isnt a block, so we need to call its parents
                # serialize method with the attr_index necessary to export.
                self.parent.serialize(filepath=filepath,
                                      clone=self.export_clone,
                                      calc_pointers=self.export_calc_pointers,
                                      attr_index=self.attr_index)
        except Exception:
            print(format_exc())
            print("Could not export '%s' node." % self.name)

    def import_node(self):
        '''Prompts the user for an exported node file.
        Imports data into the node from the file.'''
        if self.node is None:
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

        try:
            clear = self.edit_clear_warn()
            if not clear:
                return

            if hasattr(self.node, 'parse'):
                self.node.parse(filepath=filepath)
            else:
                # the node isnt a block, so we need to call its parents
                # parse method with the attr_index necessary to import.
                self.parent.parse(filepath=filepath, attr_index=self.attr_index)
                self.node = self.parent[self.attr_index]

            self.reload()
            self.set_edited()
        except Exception:
            print(format_exc())
            print("Could not import '%s' node." % self.name)

    def populate(self):
        '''Destroys and rebuilds this widgets children.'''
        raise NotImplementedError("This method must be overloaded")

    def flush(self):
        '''Flushes values from the widgets to the nodes they are displaying.'''
        raise NotImplementedError("This method must be overloaded")

    def reload(self):
        '''Resupplies the nodes to the widgets which display them.'''
        raise NotImplementedError("This method must be overloaded")

    def unload_node_data(self):
        self.node = self.parent = None

    def load_node_data(self, parent, node, attr_index, desc=None):
        '''Returns True if this FieldWidget will need to be repopulated.'''
        self.parent = parent
        self.node = node
        self.attr_index = attr_index
        if self.node is None and self.parent:
            try:
                self.node = self.parent[self.attr_index]
            except Exception:
                self.unload_node_data()
                return True

        prev_desc = self._desc
        if desc is None:
            if hasattr(self.node, "desc"):
                desc = self.node.desc
            elif self.f_widget_parent:
                parent_desc = self.f_widget_parent.desc
                if parent_desc['TYPE'].is_array:
                    desc = parent_desc['SUB_STRUCT']
                else:
                    desc = parent_desc.get(self.attr_index)

        self._desc = desc
        return self._desc != prev_desc

    def build_f_widget_cache(self):
        self.f_widgets = {}
        try:
            for w in self.content.children.values():
                if isinstance(w, FieldWidget):
                    self.f_widgets[id(w)] = w
        except Exception:
            print(format_exc())

    def set_edited(self, new_value=True):
        self.edited = bool(new_value)
        try:
            if self.edited:
                if hasattr(self.f_widget_parent, "set_edited"):
                    # Tell all parents that there are unsaved edits
                    self.f_widget_parent.set_edited()
                return
            else:
                # Tell all children that there are no longer unsaved edits
                for f_wid in self.f_widget_ids:
                    w = self.f_widgets.get(f_wid)
                    if getattr(w, "edited", False):
                        w.set_edited(False)
        except Exception:
            print(format_exc())

    def set_needs_flushing(self, new_value=True):
        self.needs_flushing = new_value
        try:
            if self.needs_flushing:
                # Tell all parents that there are unflushed edits
                if not self.f_widget_parent.needs_flushing:
                    self.f_widget_parent.set_needs_flushing()
                return

            # Tell all children that there are no longer unflushed edits
            for f_wid in self.f_widget_ids:
                w = self.f_widgets.get(f_wid)
                if w.needs_flushing:
                    w.set_needs_flushing(False)
        except Exception:
            pass
