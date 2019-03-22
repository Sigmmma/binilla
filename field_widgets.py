from os.path import splitext
import threadsafe_tkinter as tk
import tkinter.ttk as ttk

from copy import deepcopy
from math import log, ceil
from tkinter import messagebox
from tkinter import constants as t_const
from tkinter.font import Font
from tkinter.colorchooser import askcolor
from tkinter.filedialog import asksaveasfilename, askopenfilename
from traceback import format_exc

from supyr_struct.buffer import get_rawdata
from .edit_manager import EditState
from . import widgets
from . import editor_constants as e_c
from .util import float_to_str, FLOAT_PREC, DOUBLE_PREC

NoneType = type(None)


__all__ = (
    "fix_kwargs", "FieldWidget",
    "ContainerFrame", "ColorPickerFrame",
    "ArrayFrame", "DynamicArrayFrame",
    "DataFrame", "NullFrame", "VoidFrame", "PadFrame",
    "UnionFrame", "StreamAdapterFrame",
    "BoolFrame", "BoolSingleFrame",
    "EnumFrame", "DynamicEnumFrame",
    "EntryFrame", "HexEntryFrame", "TimestampFrame", "NumberEntryFrame",
    "TextFrame", "RawdataFrame",
    )


def fix_kwargs(**kw):
    '''Returns a dict where all items in the provided keyword arguments
    that use keys found in WIDGET_KWARGS are removed.'''
    return {s:kw[s] for s in kw if s not in e_c.WIDGET_KWARGS}


# These classes are used for laying out the visual structure
# of many sub-widgets, and effectively the whole window.
class FieldWidget(widgets.BinillaWidget):
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
        widgets.BinillaWidget.__init__(self)

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
        widgets.BinillaWidget.apply_style(self, seen)
        if self.comment_frame:
            self.comment_frame.config(bd=self.comment_depth,
                                      bg=self.comment_bg_color)
        if self.comment_label:
            self.comment_label.config(bg=self.comment_bg_color,
                                      fg=self.text_normal_color)

    @property
    def is_empty(self):
        return getattr(self, "node", None) is None

    @property
    def blocks_start_hidden(self):
        try:
            flags = self.tag_window.app_root.config_file.data.\
                    header.tag_window_flags
            return bool(flags.blocks_start_hidden)
        except Exception:
            return True

    @property
    def hide_if_blank(self):
        try:
            flags = self.tag_window.app_root.config_file.data.\
                    header.tag_window_flags
            return bool(flags.empty_blocks_start_hidden)
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
    def all_visible(self):
        try:
            return bool(self.tag_window.all_visible)
        except Exception:
            return False

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
            try: comment_font = self.tag_window.app_root.comment_font
            except AttributeError: comment_font = None

            self.comment_label = tk.Label(
                self.comment_frame, text=comment, anchor='nw',
                justify='left', font=comment_font,
                bg=self.comment_bg_color, fg=self.text_normal_color)
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

        filepath, ext = splitext(filepath)
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
                    desc = parent_desc[self.attr_index]
                
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


class ContainerFrame(tk.Frame, FieldWidget):
    show = None
    import_btn = None
    export_btn = None

    def __init__(self, *args, **kwargs):
        FieldWidget.__init__(self, *args, **kwargs)

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

        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)

        show_frame = True
        if self.f_widget_parent is not None:
            show_frame = bool(
                kwargs.pop('show_frame', not self.blocks_start_hidden))

        if self.is_empty and self.hide_if_blank:
            show_frame = False

        tk.Frame.__init__(self, *args, **fix_kwargs(**kwargs))
        self.show = tk.BooleanVar(self)

        # if the orientation is vertical, make a title frame
        if self.show_title:
            self.show.set(show_frame)
            toggle_text = '-' if show_frame else '+'

            btn_kwargs = dict(
                bg=self.button_color, fg=self.text_normal_color,
                disabledforeground=self.text_disabled_color,
                bd=self.button_depth,
                )

            try: title_font = self.tag_window.app_root.container_title_font
            except AttributeError: title_font = None
            self.title = tk.Frame(self, relief='raised', bd=self.frame_depth,
                                  bg=self.frame_bg_color)

            self.show_btn = ttk.Checkbutton(
                self.title, width=3, text=toggle_text,
                command=self.toggle_visible, style='ShowButton.TButton')
            self.title_label = tk.Label(
                self.title, text=self.gui_name, anchor='w',
                width=self.title_size, justify='left', font=title_font,
                bg=self.frame_bg_color, fg=self.text_normal_color)
            self.import_btn = tk.Button(
                self.title, width=5, text='Import',
                command=self.import_node, **btn_kwargs)
            self.export_btn = tk.Button(
                self.title, width=5, text='Export',
                command=self.export_node, **btn_kwargs)

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
        if FieldWidget.load_node_data(self, parent, node, attr_index, desc):
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
        FieldWidget.unload_node_data(self)
        self.unload_child_node_data()

    def unload_child_node_data(self):
        for w in self.f_widgets.values():
            if hasattr(w, "unload_node_data"):
                w.unload_node_data()

    def apply_style(self, seen=None):
        FieldWidget.apply_style(self, seen)
        w = getattr(self, "title", None)
        if w is not None:
            w.config(bd=self.frame_depth, bg=self.frame_bg_color)

        w = getattr(self, "title_label", None)
        if w:
            if self.desc.get('ORIENT', 'v')[:1].lower() == 'v':
                w.config(bd=0, bg=self.frame_bg_color)
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

            if self.all_visible:
                return len(entries)

            for i in entries:
                sub_desc = desc[i]
                if hasattr(node, "__getitem__"):
                    sub_node = node[i]

                if hasattr(sub_node, 'desc'):
                    sub_desc = sub_node.desc

                if sub_desc.get('VISIBLE', True):
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

        w, node = FieldWidget.get_widget_and_node(nodepath=state.nodepath,
                                                  tag_window=state.tag_window)
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

        all_visible = self.all_visible
        visible_count = self.visible_field_count

        # if only one sub-widget being displayed, dont
        # display the title of the widget being displayed
        if not all_visible:
            s_desc = desc.get('STEPTREE', dict(VISIBLE=False))
            if visible_count < 2:
                if not s_desc.get('VISIBLE', 1):
                    # only make the title not shown if the only
                    # visible widget will not be the subtree
                    kwargs.update(show_title=False)
                kwargs.update(dont_padx_fields=True)

        if self.dont_padx_fields:
            kwargs.update(pack_padx=0)
        elif visible_count < 2 and not self.show_title:
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
            if not(sub_desc.get('VISIBLE', True) or all_visible):
                continue

            widget_cls = picker.get_widget(sub_desc)
            if i == field_indices[-1] and vertical:
                kwargs.update(pack_pady=0)

            try:
                widget = widget_cls(content, node=sub_node,
                                    attr_index=i, desc=sub_desc, **kwargs)
            except Exception:
                print(format_exc())
                widget = NullFrame(content, node=sub_node,
                                   attr_index=i, desc=sub_desc, **kwargs)

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
            desc = self.desc
            field_indices = range(desc['ENTRIES'])
            # if the node has a steptree node, include its index in the indices
            if 'STEPTREE' in desc:
                field_indices = tuple(field_indices) + ('STEPTREE',)

            f_widget_ids_map = self.f_widget_ids_map
            all_visible = self.all_visible

            # if any of the descriptors are different between
            # the sub-nodes of the previous and new sub-nodes,
            # then this widget will need to be repopulated.
            if self.load_child_node_data():
                self.populate()
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

        FieldWidget.set_disabled(self, disable)

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


class ColorPickerFrame(ContainerFrame):

    color_type = int

    def __init__(self, *args, **kwargs):
        ContainerFrame.__init__(self, *args, **kwargs)

        name_map = self.desc['NAME_MAP']
        for c in 'argb':
            if c in name_map:
                self.color_type = self.desc[name_map[c]]['TYPE'].node_cls
                break

        self._initialized = True
        self.reload()

    def apply_style(self, seen=None):
        ContainerFrame.apply_style(self, seen)
        if getattr(self, 'color_btn', None):
            self.color_btn.config(bg=self.get_color()[1])

    def update_selector_button(self):
        if not getattr(self, 'color_btn', None):
            return

        self.color_btn.config(bg=self.get_color()[1],
                              state=tk.DISABLED if self.disabled else tk.NORMAL)

    def reload(self):
        ContainerFrame.reload(self)
        self.update_selector_button()

    def set_disabled(self, disable=True):
        disable = disable or not self.editable
        if self.node is None and not disable:
            return

        if bool(disable) != self.disabled:
            self.color_btn.config(state=tk.DISABLED if disable else tk.NORMAL)

        ContainerFrame.set_disabled(self, disable)

    def populate(self):
        ContainerFrame.populate(self)
        self.color_btn = tk.Button(
            self.content, width=4, command=self.select_color,
            bd=self.button_depth)
        orient = self.desc.get('ORIENT', 'v')[:1].lower()
        side = 'left' if orient == 'h' else 'top'
        self.color_btn.pack(side=side)
        self.update_selector_button()

        for attr_name in "rgb":
            w = self.get_widget(nodepath=attr_name)
            var = getattr(w, "entry_string", None)
            if isinstance(var, tk.StringVar):
                self.write_trace(var, lambda *a, widget=self, **kw:
                                 widget.update_selector_button())

    def get_color(self):
        try:
            int_color = (int(self.red   * 255.0 + 0.5),
                         int(self.green * 255.0 + 0.5),
                         int(self.blue  * 255.0 + 0.5))
            return (int_color, '#%02x%02x%02x' % int_color)
        except Exception:
            return ((0, 0, 0), '#000000')

    def select_color(self):
        self.flush()
        if getattr(self, 'color_btn', None):
            self.color_btn.config(bg=self.get_color()[1])

        color, hex_color = askcolor(self.get_color()[1], parent=self)

        if None in (color, hex_color):
            return

        # NOTE: NEED to make it into an int. Some versions of
        # tkinter seem to return color values as floats, even
        # though the documentation specifies they will be ints.
        c_color = float_c_color = tuple(int(v) / 255.0 for v in color)
        n_color = (self.red, self.green, self.blue, self.alpha)
        if issubclass(self.color_type, int):
            c_color = tuple(int(v * 255.0 + 0.5) for v in c_color)
            n_color = tuple(int(v * 255.0 + 0.5) for v in n_color)

        self.set_edited()
        self.edit_create(
            attr_index='rgb',
            redo_node=dict(r=c_color[0], g=c_color[1],
                           b=c_color[2], a=n_color[3]),
            undo_node=dict(r=n_color[0], g=n_color[1],
                           b=n_color[2], a=n_color[3]))

        self.red, self.green, self.blue = float_c_color
        self.reload()

    @property
    def alpha(self):
        if not hasattr(self.node, "a"):
            return 0.0
        return max(0.0, min(1.0, self.node.a / 255.0 if
                            issubclass(self.color_type, int)
                            else self.node.a))

    @alpha.setter
    def alpha(self, new_val):
        if issubclass(self.color_type, int) and isinstance(new_val, float):
            new_val = int(new_val * 255.0 + 0.5)
        if hasattr(self.node, "a"):
            self.node.a = new_val

    @property
    def red(self):
        if not hasattr(self.node, "r"):
            return 0.0
        return max(0.0, min(1.0, self.node.r / 255.0 if
                            issubclass(self.color_type, int)
                            else self.node.r))

    @red.setter
    def red(self, new_val):
        if issubclass(self.color_type, int) and isinstance(new_val, float):
            new_val = int(new_val * 255.0 + 0.5)
        if hasattr(self.node, "r"):
            self.node.r = new_val

    @property
    def green(self):
        if not hasattr(self.node, "g"):
            return 0.0
        return max(0.0, min(1.0, self.node.g / 255.0 if
                            issubclass(self.color_type, int)
                            else self.node.g))

    @green.setter
    def green(self, new_val):
        if issubclass(self.color_type, int) and isinstance(new_val, float):
            new_val = int(new_val * 255.0 + 0.5)
        if hasattr(self.node, "g"):
            self.node.g = new_val

    @property
    def blue(self):
        if not hasattr(self.node, "b"):
            return 0.0
        return max(0.0, min(1.0, self.node.b / 255.0 if
                            issubclass(self.color_type, int)
                            else self.node.b))

    @blue.setter
    def blue(self, new_val):
        if issubclass(self.color_type, int) and isinstance(new_val, float):
            new_val = int(new_val * 255.0 + 0.5)
        if hasattr(self.node, "b"):
            self.node.b = new_val


class ArrayFrame(ContainerFrame):
    '''Used for array nodes. Displays a single element in
    the ArrayBlock represented by it, and contains a combobox
    for selecting which array element is displayed.'''

    sel_index = -1
    populated = False
    option_cache = None
    options_sane = False

    def __init__(self, *args, **kwargs):
        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)
        FieldWidget.__init__(self, *args, **kwargs)
        tk.Frame.__init__(self, *args, **fix_kwargs(**kwargs))

        try: title_font = self.tag_window.app_root.container_title_font
        except AttributeError: title_font = None
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
        self.controls = tk.Frame(self, relief='raised', bd=self.frame_depth,
                                 bg=self.frame_bg_color)
        self.title = title = tk.Frame(self.controls, relief='flat', bd=0,
                                      bg=self.frame_bg_color)
        self.buttons = buttons = tk.Frame(self.controls, relief='flat', bd=0,
                                          bg=self.frame_bg_color)

        toggle_text = '-' if show_frame else '+'

        btn_kwargs = dict(
            bg=self.button_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color,
            bd=self.button_depth,
            )

        self.title_label = tk.Label(
            title, text=self.gui_name, justify='left', anchor='w',
            width=self.title_size, font=title_font,
            bg=self.frame_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color)

        self.show_btn = ttk.Checkbutton(
            title, width=3, text=toggle_text, command=self.toggle_visible,
            style='ShowButton.TButton')
        self.sel_menu = widgets.ScrollMenu(
            title, f_widget_parent=self,
            sel_index=self.sel_index, max_index=node_len-1,
            option_getter=self.get_options, callback=self.select_option)

        self.shift_up_btn = tk.Button(
            title, width=6, text='Shift ▲',
            command=self.shift_entry_up, **btn_kwargs)
        self.shift_down_btn = tk.Button(
            buttons, width=6, text='Shift ▼',
            command=self.shift_entry_down, **btn_kwargs)
        self.add_btn = tk.Button(
            buttons, width=3, text='Add',
            command=self.add_entry, **btn_kwargs)
        self.insert_btn = tk.Button(
            buttons, width=5, text='Insert',
            command=self.insert_entry, **btn_kwargs)
        self.duplicate_btn = tk.Button(
            buttons, width=7, text='Duplicate',
            command=self.duplicate_entry, **btn_kwargs)
        self.delete_btn = tk.Button(
            buttons, width=5, text='Delete',
            command=self.delete_entry, **btn_kwargs)
        self.delete_all_btn = tk.Button(
            buttons, width=7, text='Delete all',
            command=self.delete_all_entries, **btn_kwargs)

        self.import_btn = tk.Button(
            buttons, width=5, text='Import',
            command=self.import_node, **btn_kwargs)
        self.export_btn = tk.Button(
            buttons, width=5, text='Export',
            command=self.export_node, **btn_kwargs)

        # pack the title, menu, and all the buttons
        for w in (self.shift_down_btn, self.export_btn, self.import_btn,
                  self.delete_all_btn, self.delete_btn, self.duplicate_btn,
                  self.insert_btn, self.add_btn):
            w.pack(side="right", padx=(0, 4), pady=(2, 2))
        self.show_btn.pack(side="left")
        if self.gui_name != '':
            self.title_label.pack(side="left", fill="x", expand=True)
        self.sel_menu.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.shift_up_btn.pack(side="right", padx=(4, 4), pady=(2, 2))

        self.title.pack(fill="x", expand=True)
        self.buttons.pack(fill="x", expand=True)
        self.controls.pack(fill="x", expand=True)

        self.populate()
        self._initialized = True

    @property
    def is_empty(self):
        if getattr(self, "node", None) is None:
            return True
        return len(self.node) == 0

    def load_node_data(self, parent, node, attr_index, desc=None):
        FieldWidget.load_node_data(self, parent, node, attr_index, desc)
        sub_node = attr_index = None
        if self.node:
            attr_index = self.sel_index
            if attr_index in range(len(self.node)):
                sub_node = self.node[attr_index]
            else:
                attr_index = len(self.node) - 1
                if attr_index < 0:
                    attr_index = None

        for wid in self.f_widgets:
            # there must be only one entry in self.f_widgets
            w = self.f_widgets[wid]
            if w.load_node_data(self.node, sub_node, attr_index):
                return True

        return False

    def unload_node_data(self):
        self.sel_menu.update_label(" ")
        ContainerFrame.unload_node_data(self)

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

        ContainerFrame.set_disabled(self, disable)

    def apply_style(self, seen=None):
        ContainerFrame.apply_style(self, seen)
        self.controls.config(bd=self.frame_depth, bg=self.frame_bg_color)
        self.buttons.config(bd=0, bg=self.frame_bg_color)

    def destroy(self):
        # These will linger and take up RAM, even if the widget is destroyed.
        # Need to remove the references manually
        self.option_cache = None
        ContainerFrame.destroy(self)

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
        if not self.options_sane or self.option_cache is None:
            self.cache_options()

        if opt_index is None:
            return self.option_cache
        elif opt_index == "active":
            opt_index = self.sel_index

        if opt_index < 0: opt_index = -1

        return self.option_cache.get(opt_index)

    def cache_options(self):
        # sort the options by value(values are integers)
        options = {i: n for n, i in self.desc.get('NAME_MAP', {}).items()}

        if self.node:
            node, desc = self.node, self.desc
            sub_desc = desc['SUB_STRUCT']
            def_struct_name = sub_desc.get('GUI_NAME', sub_desc['NAME'])

            for i in range(len(node)):
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

        self.options_sane = True
        self.option_cache = options

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

        w, node = FieldWidget.get_widget_and_node(nodepath=state.nodepath,
                                                  tag_window=state.tag_window)

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
                w.options_sane = w.sel_menu.options_sane = False
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
        FieldWidget.edit_create(self, **kwargs)

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
        self.options_sane = self.sel_menu.options_sane = False
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
        self.options_sane = self.sel_menu.options_sane = False
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

        self.options_sane = self.sel_menu.options_sane = False
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

        self.options_sane = self.sel_menu.options_sane = False
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

        self.options_sane = self.sel_menu.options_sane = False
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

        self.options_sane = self.sel_menu.options_sane = False
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

        self.options_sane = self.sel_menu.options_sane = False
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
                widget = NullFrame(
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

        self.sel_menu.bind('<FocusIn>', self.set_not_sane)
        self.sel_menu.arrow_button.bind('<FocusIn>', self.set_not_sane)
        self.sel_menu.options_volatile = True

    def cache_options(self):
        node, desc = self.node, self.desc
        dyn_name_path = desc.get('DYN_NAME_PATH')
        if node is None:
            dyn_name_path = ""

        options = {}
        if dyn_name_path:
            try:
                for i in range(len(node)):
                    name = str(node[i].get_neighbor(dyn_name_path))
                    if name:
                        options[i] = name.split('\n')[0]
            except Exception:
                pass

        if not dyn_name_path:
            # sort the options by value(values are integers)
            options.update({i: n for n, i in
                            self.desc.get('NAME_MAP', {}).items()
                            if i not in options})
            sub_desc = desc['SUB_STRUCT']
            def_struct_name = sub_desc.get('GUI_NAME', sub_desc['NAME'])

            for i in range(len(node)):
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

        for i, v in options.items():
            options[i] = '%s. %s' % (i, v)

        self.options_sane = True
        self.option_cache = options
        self.sel_menu.update_label()

    def set_not_sane(self, e=None):
        self.options_sane = self.sel_menu.options_sane = False


class DataFrame(FieldWidget, tk.Frame):

    def __init__(self, *args, **kwargs):
        kwargs.update(bg=self.default_bg_color)
        FieldWidget.__init__(self, *args, **kwargs)
        tk.Frame.__init__(self, *args, **fix_kwargs(**kwargs))

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
    '''This FieldWidget is is meant to represent an unknown field.'''
    def __init__(self, *args, **kwargs):
        DataFrame.__init__(self, *args, **kwargs)
        self.populate()

    def flush(self): pass

    def populate(self):
        try: title_font = self.tag_window.app_root.default_font
        except AttributeError: title_font = None
        self.title_label = tk.Label(
            self, text=self.gui_name, width=self.title_size, anchor='w',
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color, font=title_font)
        self.field_type_name = tk.Label(
            self, text='<%s>'%self.desc['TYPE'].name,
            anchor='w', justify='left',
            bg=self.default_bg_color, fg=self.text_normal_color,
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

        w_parent, parent = FieldWidget.get_widget_and_node(
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
        try: title_font = self.tag_window.app_root.default_font
        except AttributeError: title_font = None
        self.title_label = tk.Label(
            self, text=self.gui_name, width=self.title_size, anchor='w',
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color, font=title_font)

        self.tooltip_string = self.desc.get('TOOLTIP')
        self.title_label.tooltip_string = self.tooltip_string
        for w in (self, self.title_label):
            w.tooltip_string = self.desc.get('TOOLTIP')

        btn_kwargs = dict(
            bg=self.button_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color, bd=self.button_depth)
        self.import_btn = tk.Button(
            self, width=6, text='Import',
            command=self.import_node, **btn_kwargs)
        self.export_btn = tk.Button(
            self, width=6, text='Export',
            command=self.export_node, **btn_kwargs)
        self.delete_btn = tk.Button(
            self, width=6, text='Delete',
            command=self.delete_node, **btn_kwargs)

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
            rawdata = get_rawdata(filepath=filepath)
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
        padx, pady, side= self.horizontal_padx, self.horizontal_pady, 'top'
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
        try: title_font = self.tag_window.app_root.default_font
        except AttributeError: title_font = None
        self.title_label = tk.Label(
            self, text=self.gui_name, width=self.title_size, anchor='w',
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color, font=title_font)
        self.field_type_name = tk.Label(
            self, text='<VOIDED>', anchor='w', justify='left',
            bg=self.default_bg_color, fg=self.text_normal_color,
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


class EntryFrame(DataFrame):

    last_flushed_val = None  # used for determining if a change has been made
    #                          since the last value was flushed to the node.
    _flushing = False

    def __init__(self, *args, **kwargs):
        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)
        DataFrame.__init__(self, *args, **kwargs)

        # make the widgets
        self.entry_string = tk.StringVar(self)
        self.content = tk.Frame(self, relief='flat', bd=0,
                                bg=self.default_bg_color)
        try: title_font = self.tag_window.app_root.default_font
        except AttributeError: title_font = None

        self.title_label = tk.Label(
            self.content, text=self.gui_name, justify='left', anchor='w',
            bg=self.default_bg_color, fg=self.text_normal_color, font=title_font,
            disabledforeground=self.text_disabled_color, width=self.title_size)

        self.data_entry = tk.Entry(
            self.content, textvariable=self.entry_string,
            justify='left', bd=self.entry_depth,
            bg=self.entry_normal_color, fg=self.text_normal_color,
            disabledbackground=self.entry_disabled_color,
            disabledforeground=self.text_disabled_color,
            selectbackground=self.entry_highlighted_color,
            selectforeground=self.text_highlighted_color)

        self.data_entry.bind('<Return>', self.flush)
        self.data_entry.bind('<FocusOut>', self.flush)

        self.write_trace(self.entry_string, self.set_modified)

        if self.gui_name != '':
            self.title_label.pack(side="left", fill="x")

        self.sidetip_label = tk.Label(
            self.content, anchor='w', justify='left',
            bg=self.default_bg_color, fg=self.text_normal_color)

        self.populate()
        self._initialized = True

    def unload_node_data(self):
        FieldWidget.unload_node_data(self)
        self.entry_string.set("")

    def set_disabled(self, disable=True):
        disable = disable or not self.editable
        if self.node is None and not disable:
            return

        if bool(disable) != self.disabled and getattr(self, "data_entry", None):
            self.data_entry.config(state=tk.DISABLED if disable else tk.NORMAL)
        DataFrame.set_disabled(self, disable)

    def edit_apply(self=None, *, edit_state, undo=True):
        attr_index = edit_state.attr_index

        w_parent, parent = FieldWidget.get_widget_and_node(
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
                w.needs_flushing = False
                w.reload()
                w.set_edited()
            except Exception:
                print(format_exc())

    def set_modified(self, *args):
        if None in (self.parent, self.node) or self.needs_flushing:
            return
        elif self.entry_string.get() != self.last_flushed_val:
            self.set_needs_flushing()
            self.set_edited()

    def flush(self, *args):
        if None in (self.parent, self.node):
            return
        elif self._flushing or not self.needs_flushing:
            return

        try:
            self._flushing = True
            node = self.node
            unit_scale = self.unit_scale
            curr_val = self.entry_string.get()
            try:
                new_node = self.parse_input()
            except Exception:
                # Couldnt cast the string to the node class. This is fine this
                # kind of thing happens when entering data. Just dont flush it
                try: self.entry_string.set(curr_val)
                except Exception: pass
                self._flushing = False
                self.set_needs_flushing(False)
                return

            if isinstance(new_node, float):
                # find the precision of the float
                field_type = self.desc.get('TYPE')
                prec = 0
                if   'f' in field_type.enc:
                    prec = FLOAT_PREC
                elif 'd' in field_type.enc:
                    prec = DOUBLE_PREC
                elif hasattr(field_type, "mantissa_len"):
                    prec = field_type.mantissa_len*log(2, 10)

                str_node = new_node
                if unit_scale:
                    prec -= ceil(log(abs(unit_scale), 10))
                    str_node = new_node * unit_scale

                str_node = float_to_str(str_node, prec)
            elif unit_scale and isinstance(node, int):
                str_node = float_to_str(float(new_node * unit_scale),
                                        -1*ceil(log(abs(unit_scale), 10)))
            else:
                str_node = str(new_node)

            # dont need to flush anything if the nodes are the same
            if node != new_node:
                # make an edit state
                self.edit_create(undo_node=node, redo_node=new_node)

                self.last_flushed_val = str_node
                self.node = new_node
                if self.parent is not None:
                    self.parent[self.attr_index] = new_node

            # value may have been clipped, so set the entry string anyway
            self.entry_string.set(str_node)

            self._flushing = False
            self.set_needs_flushing(False)
        except Exception:
            # an error occurred so replace the entry with the last valid string
            self._flushing = False
            self.set_needs_flushing(False)
            raise

    def parse_input(self):
        desc = self.desc
        node_cls = desc.get('NODE_CLS', desc['TYPE'].node_cls)
        new_node = node_cls(self.entry_string.get())

        if self.enforce_max:
            field_max = self.field_max
            sizecalc = desc['TYPE'].sizecalc
            node_size = sizecalc(new_node, parent=self.parent,
                                 attr_index=self.attr_index)
            if field_max is None:
                field_max = desc.get('SIZE')

            if isinstance(field_max, int) and node_size > field_max:
                if self.enforce_max:
                    while node_size > field_max:
                        new_node = new_node[:-1]
                        node_size = sizecalc(new_node, parent=self.parent,
                                             attr_index=self.attr_index)

        return new_node

    @property
    def entry_width(self):
        entry_width = self.widget_width
        if self.widget_width:
            return entry_width

        desc = self.desc
        node = self.node
        f_type = desc['TYPE']
        if f_type.data_cls is not NoneType:
            d_type = f_type.data_cls
        else:
            d_type = f_type.node_cls

        node_size = 0
        if self.parent is not None:
            node_size = self.parent.get_size(self.attr_index)

        value_max = desc.get('MAX', f_type.max)
        value_min = desc.get('MIN', f_type.min)
        if value_max is None: value_max = 0
        if value_min is None: value_min = 0

        max_width = self.max_string_entry_width

        if f_type.is_oe_size:
            return max_width
        else:
            # if the size is not fixed using an int, dont rely on it
            if not isinstance(desc.get('SIZE', f_type.size), int):
                node_size = self.def_string_entry_width

            value_width = max(abs(value_max), abs(value_min), node_size)
            entry_width = max(self.min_entry_width,
                              min(value_width, max_width))
            if issubclass(d_type, str) and isinstance(f_type.size, int):
                entry_width = (entry_width - 1 + f_type.size)//max(1, f_type.size)
        return entry_width

    def populate(self):
        self.display_comment()
        self.data_entry.pack(side="left", fill="x")
        self.content.pack(fill="x", expand=True)
        sidetip = self.desc.get('SIDETIP')
        if self.show_sidetips and sidetip:
            self.sidetip_label.config(text=sidetip)
            self.sidetip_label.pack(fill="x", side="left")

        for w in (self, self.content, self.title_label,
                  self.data_entry, self.sidetip_label):
            w.tooltip_string = self.desc.get('TOOLTIP')

        self.reload()

    def reload(self):
        try:
            node = self.node
            unit_scale = self.unit_scale

            if unit_scale is not None and isinstance(node, (int, float)):
                node *= unit_scale

            highlight = False
            if self.data_entry.selection_present():
                highlight = True

            # set this to true so the StringVar trace function
            # doesnt think the widget has been edited by the user
            self.needs_flushing = True
            self.data_entry.config(width=self.entry_width)
            self.data_entry.config(state=tk.NORMAL)
            
            self.data_entry.delete(0, tk.END)
            if isinstance(node, float):
                # find the precision of the float
                field_type = self.desc.get('TYPE')
                prec = 0
                if   'f' in field_type.enc:
                    prec = FLOAT_PREC
                elif 'd' in field_type.enc:
                    prec = DOUBLE_PREC
                elif hasattr(field_type, "mantissa_len"):
                    prec = field_type.mantissa_len*log(2, 10)

                if unit_scale:
                    prec -= ceil(log(abs(unit_scale), 10))
                self.last_flushed_val = float_to_str(node, prec)
            elif unit_scale and isinstance(self.node, int):
                self.last_flushed_val = float_to_str(
                    float(node), -1*ceil(log(abs(unit_scale), 10)))
            elif node is None:
                self.last_flushed_val = ""
            else:
                self.last_flushed_val = str(node)

            self.data_entry.insert(0, self.last_flushed_val)
            self.needs_flushing = False
            if highlight:
                self.data_entry.selection_range(0, tk.END) 
        except Exception:
            print(format_exc())
        finally:
            if self.disabled:
                self.data_entry.config(state=tk.DISABLED)
            else:
                self.data_entry.config(state=tk.NORMAL)


class NumberEntryFrame(EntryFrame):

    def parse_input(self):
        desc = self.desc
        field_max, field_min = self.field_max, self.field_min
        unit_scale = self.unit_scale
        desc_size  = desc.get('SIZE')
        field_type = desc.get('TYPE')
        node_cls = desc.get('NODE_CLS', field_type.node_cls)

        new_node = self.entry_string.get()
        if unit_scale is None:
            unit_scale = 1
            new_node = node_cls(new_node)
        else:
            new_node = float(new_node) / unit_scale
            if issubclass(node_cls, int):
                # going to int, so decimals dont matter. do rounding
                new_node = node_cls(round(new_node))

        if isinstance(new_node, float):
            pass
        elif field_max is None and isinstance(desc_size, int):
            if not field_type.is_bit_based:
                field_max = 2**(desc_size * 8)
            else:
                field_max = 2**desc_size

        if field_max is not None and new_node >= field_max:
            if self.enforce_max:
                new_node = field_max
                if not desc.get('ALLOW_MAX', True):
                    raise ValueError("Enter a value below %s" %
                                     (field_max * unit_scale))
        elif field_min is not None and new_node <= field_min:
            if self.enforce_min:
                new_node = field_min
                if not desc.get('ALLOW_MIN', True):
                    raise ValueError("Enter a value above %s" %
                                     (field_min * unit_scale))

        return new_node

    @property
    def entry_width(self):
        entry_width = self.widget_width

        if entry_width:
            return entry_width

        desc = self.desc
        node = self.node
        f_type = desc['TYPE']
        if f_type.data_cls is not NoneType:
            d_type = f_type.data_cls
        else:
            d_type = f_type.node_cls
        unit_scale = self.unit_scale
        node_size = 0

        if None not in (unit_scale, node) and issubclass(d_type, (int, float)):
            node *= unit_scale

        fixed_size = isinstance(desc.get('SIZE', f_type.size), int)
        if hasattr(self.parent, "get_size"):
            node_size = self.parent.get_size(self.attr_index)

        value_max = desc.get('MAX', f_type.max)
        value_min = desc.get('MIN', f_type.min)

        if issubclass(d_type, float):
            # floats are hard to choose a reasonable entry width for
            max_width = self.max_float_entry_width
            value_width = max(int(ceil(node_size * 5/2)),
                              self.def_float_entry_width)
        else:
            max_width = self.max_int_entry_width
            if not f_type.is_bit_based:
                node_size *= 8

            adjust = 0
            if value_min is None: value_min = 0
            if value_max is None: value_max = 0

            if isinstance(value_max, int):
                if value_max < 0:
                    adjust = 1
                    value_max *= -1
            if isinstance(value_min, int):
                if value_min < 0:
                    adjust = 1
                    value_min *= -1
            value_max = max(value_min, value_max)

            if 2**node_size > value_max:
                value_max = 2**node_size
                if min(value_min, value_max) < 0:
                    adjust = 1

            if unit_scale is not None:
                value_max *= unit_scale

            value_width = int(ceil(log(value_max, 10))) + adjust

        entry_width = max(self.min_entry_width,
                          min(value_width, max_width))
        return entry_width


class TimestampFrame(EntryFrame):

    def flush(self, *args):
        if None in (self.parent, self.node):
            return
        elif self._flushing or not self.needs_flushing:
            return

        try:
            self._flushing = True
            desc = self.desc
            node_cls = desc.get('NODE_CLS', desc['TYPE'].node_cls)

            new_node = node_cls(self.entry_string.get())
            if self.node != new_node:
                # make an edit state
                self.edit_create(undo_node=self.node, redo_node=new_node)
                self.parent[self.attr_index] = self.node = new_node

            self._flushing = False
            self.set_needs_flushing(False)
        except Exception:
            self._flushing = False
            self.set_needs_flushing(False)
            raise

    @property
    def entry_width(self):
        entry_width = self.widget_width
        if not entry_width:
            entry_width = self.def_string_entry_width
        return entry_width

    
class HexEntryFrame(EntryFrame):

    def flush(self):
        try:
            self.parent[self.attr_index] = self.entry_string.get()
        except Exception:
            print(format_exc())

    def flush(self, *args):
        if None in (self.parent, self.node):
            return
        elif self._flushing or not self.needs_flushing:
            return

        try:
            self._flushing = True
            new_node = self.entry_string.get()
            if self.node != new_node:
                # make an edit state
                self.edit_create(undo_node=self.node, redo_node=new_node)
                self.parent[self.attr_index] = self.node = new_node

            self._flushing = False
            self.set_needs_flushing(False)
        except Exception:
            self._flushing = False
            self.set_needs_flushing(False)
            raise

    @property
    def entry_width(self):
        entry_width = self.widget_width
        if entry_width is not None:
            return entry_width

        desc = self.desc
        node_size = self.parent.get_size(self.attr_index)

        value_max = desc.get('MAX', 0)
        value_min = desc.get('MIN', 0)

        # if the size is not fixed using an int, dont rely on it
        if not isinstance(desc.get('SIZE', desc['TYPE'].size), int):
            node_size = self.def_string_entry_width

        value_width = max(abs(value_max), abs(value_min), node_size) * 2

        return max(self.min_entry_width,
                   min(value_width, self.max_string_entry_width))


class TextFrame(DataFrame):
    '''Used for strings that likely will not fit on one line.'''

    children_can_scroll = True
    can_scroll = False
    _flushing = False

    replace_map = None
    data_text = None

    def __init__(self, *args, **kwargs):
        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)
        DataFrame.__init__(self, *args, **kwargs)

        # make the widgets
        self.content = tk.Frame(self, relief='flat', bd=0,
                                bg=self.default_bg_color)
        try: title_font = self.tag_window.app_root.default_font
        except AttributeError: title_font = None

        self.title_label = tk.Label(
            self.content, text=self.gui_name, justify='left', anchor='w',
            bg=self.default_bg_color, fg=self.text_normal_color, font=title_font,
            disabledforeground=self.text_disabled_color, width=self.title_size)

        self.data_text = tk.Text(
            self.content, bd=self.entry_depth, wrap=tk.NONE,
            height=self.textbox_height, width=self.textbox_width,
            maxundo=self.max_undos, undo=True,
            state=tk.DISABLED if self.disabled else tk.NORMAL,
            bg=self.entry_normal_color, fg=self.text_normal_color,
            selectbackground=self.entry_highlighted_color,
            selectforeground=self.text_highlighted_color,)

        self.sidetip_label = tk.Label(
            self.content, anchor='w', justify='left',
            bg=self.default_bg_color, fg=self.text_normal_color)

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
        FieldWidget.unload_node_data(self)
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
        DataFrame.set_disabled(self, disable)

    def disable_undo_redo(self, *args, **kwargs):
        if not self.data_text: return
        # disable the undo/redo ability of the text so we can call it ourselves
        self.data_text.config(undo=False)

    def edit_apply(self=None, *, edit_state, undo=True):
        attr_index = edit_state.attr_index

        w_parent, parent = FieldWidget.get_widget_and_node(
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


class UnionFrame(ContainerFrame):
    '''Used for enumerator nodes. When clicked, creates
    a dropdown box of all available enumerator options.'''

    option_cache = None
    u_node_widgets_by_u_index = ()

    def __init__(self, *args, **kwargs):
        FieldWidget.__init__(self, *args, **kwargs)
        self.u_node_widgets_by_u_index = {}

        if self.f_widget_parent is None:
            self.pack_padx = self.pack_pady = 0

        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)

        show_frame = bool(kwargs.pop('show_frame', not self.blocks_start_hidden))
        if self.is_empty and self.hide_if_blank:
            show_frame = False

        tk.Frame.__init__(self, *args, **fix_kwargs(**kwargs))

        self.show = tk.BooleanVar(self)
        self.show.set(show_frame)

        max_u_index = len(self.desc['CASE_MAP'])
        u_index = getattr(self.node, "u_index", None)
        if u_index is None:
            u_index = max_u_index

        toggle_text = '-' if show_frame else '+'

        btn_kwargs = dict(
            bg=self.button_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color,
            bd=self.button_depth, width=5,
            )

        try: title_font = self.tag_window.app_root.container_title_font
        except AttributeError: title_font = None

        self.title = tk.Frame(self, relief='raised', bd=self.frame_depth,
                              bg=self.frame_bg_color)
        self.show_btn = ttk.Checkbutton(
            self.title, width=3, text=toggle_text, command=self.toggle_visible,
            style='ShowButton.TButton')
        self.title_label = tk.Label(
            self.title, text=self.gui_name, anchor='w',
            width=self.title_size, justify='left', font=title_font,
            bg=self.frame_bg_color, fg=self.text_normal_color)
        self.sel_menu = widgets.ScrollMenu(
            self.title, f_widget_parent=self, sel_index=u_index,
            max_index=max_u_index, disabled=self.disabled,
            callback=self.select_option, option_getter=self.get_options)

        self.show_btn.pack(side="left")
        self.title_label.pack(side="left", fill="x", expand=True)
        self.sel_menu.pack(side="left", fill="x")
        self.title.pack(fill="x", expand=True)

        self.content = tk.Frame(self, relief="sunken", bd=self.frame_depth,
                                bg=self.default_bg_color)

        # make the default raw bytes union frame
        self.raw_frame = tk.Frame(
            self.content, relief="flat", bd=0, bg=self.default_bg_color)
        self.raw_label = tk.Label(
            self.raw_frame, text='DataUnion', width=self.title_size,
            anchor='w', bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color)
        self.import_btn = tk.Button(
            self.raw_frame, text='Import',
            command=self.import_node, **btn_kwargs)
        self.export_btn = tk.Button(
            self.raw_frame, text='Export',
            command=self.export_node, **btn_kwargs)

        self.raw_label.pack(side="left", expand=True, fill='x')
        for w in (self.export_btn, self.import_btn):
            w.pack(side="left", padx=(0, 4), pady=2)

        self.populate()
        self._initialized = True

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

        ContainerFrame.set_disabled(self, disable)

    def get_options(self, opt_index=None):
        '''
        Returns a list of the option strings sorted by option index.
        '''
        if self.option_cache is None:
            self.cache_options()

        if opt_index is None:
            return self.option_cache
        elif opt_index == "active":
            opt_index = getattr(self.node, "u_index", None)
            if opt_index is None:
                opt_index = len(self.option_cache) - 1

        if opt_index is None:
            opt_index = -1

        return self.option_cache.get(opt_index, e_c.INVALID_OPTION)

    def cache_options(self):
        options = {i: c for c, i in self.desc['CASE_MAP'].items()}
        options[len(options)] = e_c.RAW_BYTES
        self.option_cache = options

    def edit_apply(self=None, *, edit_state, undo=True):
        edit_info = edit_state.edit_info

        w, node = FieldWidget.get_widget_and_node(
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
                        active_widget = NullFrame(self.content, **kwargs)
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


class StreamAdapterFrame(ContainerFrame):

    def __init__(self, *args, **kwargs):
        FieldWidget.__init__(self, *args, **kwargs)

        if self.f_widget_parent is None:
            self.pack_padx = self.pack_pady = 0

        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)

        show_frame = bool(kwargs.pop('show_frame', not self.blocks_start_hidden))
        if self.is_empty and self.hide_if_blank:
            show_frame = False

        tk.Frame.__init__(self, *args, **fix_kwargs(**kwargs))

        self.show = tk.BooleanVar(self)
        self.show.set(show_frame)

        toggle_text = '-' if show_frame else '+'

        btn_kwargs = dict(
            bg=self.button_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color,
            bd=self.button_depth,
            )

        try: title_font = self.tag_window.app_root.container_title_font
        except AttributeError: title_font = None
        self.title = tk.Frame(self, relief='raised', bd=self.frame_depth,
                              bg=self.frame_bg_color)
        self.content = tk.Frame(self, relief="sunken", bd=self.frame_depth,
                                bg=self.default_bg_color)
        self.show_btn = ttk.Checkbutton(
            self.title, width=3, text=toggle_text, command=self.toggle_visible,
            style='ShowButton.TButton')
        self.title_label = tk.Label(
            self.title, text=self.gui_name, anchor='w',
            width=self.title_size, justify='left', font=title_font,
            bg=self.frame_bg_color, fg=self.text_normal_color)
        self.import_btn = tk.Button(
            self.title, width=5, text='Import',
            command=self.import_node, **btn_kwargs)
        self.export_btn = tk.Button(
            self.title, width=5, text='Export',
            command=self.export_node, **btn_kwargs)

        self.show_btn.pack(side="left")
        self.title_label.pack(side="left", fill="x", expand=True)

        self.title.pack(fill="x", expand=True)
        for w in (self.export_btn, self.import_btn):
            w.pack(side="right", padx=(0, 4), pady=2)

        self.populate()
        self._initialized = True

    def populate(self):
        try:
            # clear the f_widget_ids list
            del self.f_widget_ids[:]
            del self.f_widget_ids_map
            del self.f_widget_ids_map_inv

            f_widget_ids = self.f_widget_ids
            f_widget_ids_map = self.f_widget_ids_map = {}
            f_widget_ids_map_inv = self.f_widget_ids_map_inv = {}

            # destroy all the child widgets of the content
            if isinstance(self.f_widgets, dict):
                for c in list(self.f_widgets.values()):
                    c.destroy()

            node = self.node
            desc = self.desc
            data = getattr(node, "data", None)

            for w in (self, self.content, self.title_label):
                w.tooltip_string = self.desc.get('TOOLTIP')

            self.display_comment(self.content)

            data_desc = desc['SUB_STRUCT']
            if hasattr(data, 'desc'):
                data_desc = data.desc

            widget_cls = self.widget_picker.get_widget(data_desc)
            kwargs = dict(node=data, parent=node, show_title=False,
                          tag_window=self.tag_window, attr_index='data',
                          disabled=self.disabled, f_widget_parent=self,
                          desc=data_desc, show_frame=self.show.get(),
                          dont_padx_fields=True)
            try:
                widget = widget_cls(self.content, **kwargs)
            except Exception:
                print(format_exc())
                widget = NullFrame(self.content, **kwargs)

            wid = id(widget)
            f_widget_ids.append(wid)
            f_widget_ids_map['data'] = wid
            f_widget_ids_map_inv[wid] = 'data'

            self.build_f_widget_cache()

            # now that the field widgets are created, position them
            if self.show.get():
                self.pose_fields()
        except Exception:
            print(format_exc())

    reload = populate

    pose_fields = UnionFrame.pose_fields


class EnumFrame(DataFrame):
    '''Used for enumerator nodes. When clicked, creates
    a dropdown box of all available enumerator options.'''

    option_cache = None

    def __init__(self, *args, **kwargs):
        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)
        DataFrame.__init__(self, *args, **kwargs)

        try:
            sel_index = self.node.get_index()
        except Exception:
            sel_index = -1

        label_width = self.widget_width
        if not label_width:
            label_width = self.enum_menu_width
            for s in self.get_options().values():
                label_width = max(label_width, len(s))

        # make the widgets
        try: title_font = self.tag_window.app_root.default_font
        except AttributeError: title_font = None
        self.content = tk.Frame(self, relief='flat', bd=0,
                                bg=self.default_bg_color)

        self.display_comment()

        self.title_label = tk.Label(
            self.content, text=self.gui_name,
            justify='left', anchor='w', width=self.title_size,
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color, font=title_font)
        self.sel_menu = widgets.ScrollMenu(
            self.content, f_widget_parent=self, menu_width=label_width,
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

    def unload_node_data(self):
        FieldWidget.unload_node_data(self)
        self.sel_menu.update_label(" ")

    def set_disabled(self, disable=True):
        disable = disable or not self.editable
        if self.node is None and not disable:
            return

        if bool(disable) != self.disabled and getattr(self, "sel_menu", None):
            self.sel_menu.set_disabled(disable)

        DataFrame.set_disabled(self, disable)

    def flush(self): pass

    def edit_apply(self=None, *, edit_state, undo=True):
        state = edit_state
        w, node = FieldWidget.get_widget_and_node(nodepath=state.nodepath,
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
        FieldWidget.edit_create(self, **kwargs)

    def get_options(self, opt_index=None):
        '''
        Returns a list of the option strings sorted by option index.
        '''
        if self.option_cache is None:
            self.cache_options()

        if opt_index is None:
            return self.option_cache
        elif opt_index == "active":
            opt_index = self.sel_menu.sel_index

        return self.option_cache.get(opt_index, e_c.INVALID_OPTION)

    def cache_options(self):
        desc = self.desc
        options = {}
        # sort the options by value(values are integers)
        for i in range(desc.get('ENTRIES', 0)):
            opt = desc[i]
            if 'GUI_NAME' in opt:
                options[i] = opt['GUI_NAME']
            else:
                options[i] = opt.get('NAME', '<UNNAMED %s>' % i)\
                             .replace('_', ' ')
        self.option_cache = options

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
        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)
        DataFrame.__init__(self, *args, **kwargs)

        sel_index = -1 if self.node is None else self.node + 1

        # make the widgets
        try: title_font = self.tag_window.app_root.default_font
        except AttributeError: title_font = None
        self.content = tk.Frame(self, relief='flat', bd=0,
                                bg=self.default_bg_color)
        self.title_label = tk.Label(
            self.content, text=self.gui_name, font=title_font,
            justify='left', anchor='w', width=self.title_size,
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color)
        self.sel_menu = widgets.ScrollMenu(
            self.content, f_widget_parent=self, menu_width=self.widget_width,
            sel_index=sel_index, max_index=0,
            disabled=self.disabled, default_text="<INVALID>",
            option_getter=self.get_options,  callback=self.select_option)
        self.sel_menu.bind('<FocusIn>', self.set_not_sane)
        self.sel_menu.arrow_button.bind('<FocusIn>', self.set_not_sane)

        if self.gui_name != '':
            self.title_label.pack(side="left", fill="x")
        self.content.pack(fill="x", expand=True)
        self.sel_menu.pack(side="left", fill="x")
        self.populate()
        self._initialized = True

    def get_options(self, opt_index=None):
        '''
        Returns a list of the option strings sorted by option index.
        '''
        if not self.options_sane:
            self.cache_options()
            self.options_sane = True
            self.sel_menu.options_sane = False
        return EnumFrame.get_options(self, opt_index)

    def edit_apply(self=None, *, edit_state, undo=True):
        state = edit_state
        attr_index = state.attr_index

        w_parent, parent = FieldWidget.get_widget_and_node(
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

    def set_not_sane(self, e=None):
        if self.desc.get('DYN_NAME_PATH'):
            self.options_sane = self.sel_menu.options_sane = False

    def cache_options(self):
        desc = self.desc
        options = {0: "-1: NONE"}

        dyn_name_path = desc.get('DYN_NAME_PATH')
        if self.node is None:
            return
        elif not dyn_name_path:
            print("Missing DYN_NAME_PATH path in dynamic enumerator.")
            print(self.parent.get_root().def_id, self.name)
            self.option_cache = options
            return
        try:
            p_out, p_in = dyn_name_path.split('[DYN_I]')

            # We are ALWAYS going to go to the parent, so we need to slice
            if p_out.startswith('..'): p_out = p_out.split('.', 1)[-1]
            array = self.parent.get_neighbor(p_out)
            for i in range(len(array)):
                name = array[i].get_neighbor(p_in)
                if isinstance(name, list):
                    name = repr(name).strip("[").strip("]")
                else:
                    name = str(name)

                options[i + 1] = '%s. %s' % (i, name.split('\n')[0])
        except Exception:
            print(format_exc())
            dyn_name_path = False

        try:
            self.sel_menu.max_index = len(options) - 1
        except Exception:
            pass
        self.option_cache = options

    def reload(self):
        try:
            self.options_sane = False
            if self.disabled == self.sel_menu.disabled:
                pass
            elif self.disabled:
                self.sel_menu.disable()
            else:
                self.sel_menu.enable()

            self.cache_options()
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


class BoolFrame(DataFrame):
    children_can_scroll = True
    can_scroll = False
    checkvars = None  # used to know which IntVars to set when undo/redoing
    checkbtns = ()
    bit_opt_map = None

    def __init__(self, *args, **kwargs):
        self.bit_opt_map = {}
        self.checkvars = {}
        self.checkbtns = {}
        DataFrame.__init__(self, *args, **kwargs)

        try: title_font = self.tag_window.app_root.default_font
        except AttributeError: title_font = None
        self.content = tk.Frame(
            self, bg=self.default_bg_color, highlightthickness=0)

        self.display_comment()

        self.title_label = tk.Label(
            self.content, text=self.gui_name, width=self.title_size, anchor='w',
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color, font=title_font)

        if self.gui_name != '':
            self.title_label.pack(side='left')

        self.check_canvas = tk.Canvas(
            self.content, bg=self.default_bg_color, highlightthickness=0)
        self.check_frame = tk.Frame(
            self.check_canvas, bg=self.entry_normal_color,
            bd=self.listbox_depth, relief='sunken',  highlightthickness=0)

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
        FieldWidget.unload_node_data(self)
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

        DataFrame.set_disabled(self, disable)

    def apply_style(self, seen=None):
        FieldWidget.apply_style(self, seen)
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

        w, node = FieldWidget.get_widget_and_node(nodepath=state.nodepath,
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

        all_visible = self.all_bools_visible

        # make a condensed mapping of all visible flags and their information
        for mask in sorted(desc['VALUE_MAP']):
            bit = int(log(mask, 2.0))
            opt = desc.get(desc['VALUE_MAP'][mask])

            if opt is None or not opt.get("VISIBLE", True):
                if not all_visible:
                    continue
                name = e_c.UNKNOWN_BOOLEAN % bit
                opt = dict(GUI_NAME=name, NAME=name)
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
                    text=name, anchor='nw', justify='left', borderwidth=0,

                    disabledforeground=self.text_disabled_color, state=state,
                    bg=self.entry_normal_color, fg=self.text_normal_color,
                    activebackground=self.entry_highlighted_color,
                    activeforeground=self.text_highlighted_color,)

                check_btn.config(command=lambda b=check_btn, i=bit, v=check_var:
                                 self._check_bool(b, i, v))

                check_btn.pack(anchor='nw', fill='x', expand=True)
                check_btn.tooltip_string = opt.get('TOOLTIP')

                if e_c.IS_LNX:
                    check_btn.bind('<4>', self.mousewheel_scroll_y)
                    check_btn.bind('<5>', self.mousewheel_scroll_y)
                else:
                    check_btn.bind('<MouseWheel>', self.mousewheel_scroll_y)

            self.pose_fields()
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


class BoolSingleFrame(DataFrame):
    checked = None

    def __init__(self, *args, **kwargs):
        DataFrame.__init__(self, *args, **kwargs)
        try: title_font = self.tag_window.app_root.default_font
        except AttributeError: title_font = None

        self.checked = tk.IntVar(self)
        self.checkbutton = tk.Checkbutton(
            self, variable=self.checked, command=self.check,
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color,
            activebackground=self.entry_highlighted_color,
            activeforeground=self.text_highlighted_color)

        self.title_label = tk.Label(
            self, text=self.gui_name, width=self.title_size, anchor='w',
            bg=self.default_bg_color, fg=self.text_normal_color,
            disabledforeground=self.text_disabled_color, font=title_font)

        if self.gui_name != '':
            self.title_label.pack(side='left')
        self.checkbutton.pack(side='left')

        self.populate()
        self._initialized = True

    def unload_node_data(self):
        FieldWidget.unload_node_data(self)
        self.checked.set(0)

    def set_disabled(self, disable=True):
        disable = disable or not self.editable
        if self.node is None and not disable:
            return

        if bool(disable) != self.disabled:
            self.checkbutton.config(state=tk.DISABLED if disable else tk.NORMAL)

        DataFrame.set_disabled(self, disable)

    def apply_style(self, seen=None):
        FieldWidget.apply_style(self, seen)
        self.checkbutton.config(
            activebackground=self.entry_highlighted_color,
            activeforeground=self.text_highlighted_color, selectcolor="")

    def flush(self): pass

    def edit_apply(self=None, *, edit_state, undo=True):
        state = edit_state

        attr_index = state.attr_index
        undo_value = state.undo_node

        w, parent = FieldWidget.get_widget_and_node(
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
