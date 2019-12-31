import math
import struct
import threadsafe_tkinter as tk

from traceback import format_exc

from binilla.util import float_to_str, FLOAT_PREC, DOUBLE_PREC
from binilla.widgets.field_widgets import field_widget, data_frame
from binilla.windows.filedialog import askopenfilename


def float_from_bytes(val, end='<'):
    if isinstance(val, bytes):
        if len(val) == 4:
            return struct.unpack(end + 'f', val)[0]
        elif len(val) == 8:
            return struct.unpack(end + 'd', val)[0]
    else:
        return float(val)


number_eval_globals = dict(
    abs=abs, e=math.e, pi=math.pi, inf=math.inf,
    acos=math.acos, asin=math.asin, atan=math.atan, atan2=math.atan2,
    acosh=math.acosh, asinh=math.asinh, atanh=math.atanh,
    ceil=math.ceil, floor=math.floor, erf=math.erf, erfc=math.erfc,
    exp=math.exp, expm1=math.expm1, fact=math.factorial, fmod=math.fmod,
    sum=math.fsum, gamma=math.gamma, gcd=math.gcd, hypot=math.hypot,
    log=math.log, log2=math.log2, loge=math.log1p, log10=math.log10,
    lgamma=math.lgamma, pow=math.pow, sqrt=math.sqrt,
    float=float_from_bytes
    )


class EntryFrame(data_frame.DataFrame):

    last_flushed_val = None  # used for determining if a change has been made
    #                          since the last value was flushed to the node.
    _flushing = False

    def __init__(self, *args, **kwargs):
        kwargs.update(relief='flat', bd=0, highlightthickness=0,
                      bg=self.default_bg_color)
        data_frame.DataFrame.__init__(self, *args, **kwargs)

        # make the widgets
        self.entry_string = tk.StringVar(self)
        self.content = tk.Frame(self, relief='flat', bd=0)

        self.title_label = tk.Label(
            self.content, text=self.gui_name, justify='left',
            anchor='w', width=self.title_size,
            disabledforeground=self.text_disabled_color)

        self.data_entry = tk.Entry(
            self.content, textvariable=self.entry_string, justify='left')

        self.data_entry.bind('<Return>', self.flush)
        self.data_entry.bind('<FocusOut>', self.flush)

        self.write_trace(self.entry_string, self.set_modified)

        if self.gui_name != '':
            self.title_label.pack(side="left", fill="x")

        self.sidetip_label = tk.Label(
            self.content, anchor='w', justify='left')

        self.populate()
        self._initialized = True

    def unload_node_data(self):
        field_widget.FieldWidget.unload_node_data(self)
        self.entry_string.set("")

    def set_disabled(self, disable=True):
        disable = disable or not self.editable
        if self.node is None and not disable:
            return

        if bool(disable) != self.disabled and getattr(self, "data_entry", None):
            self.data_entry.config(state=tk.DISABLED if disable else tk.NORMAL)
        data_frame.DataFrame.set_disabled(self, disable)

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
                    prec = field_type.mantissa_len*math.log(2, 10)

                str_node = new_node
                if unit_scale:
                    prec -= math.ceil(math.log(abs(unit_scale), 10))
                    str_node = new_node * unit_scale

                str_node = float_to_str(str_node, prec)
            elif unit_scale and isinstance(node, int):
                str_node = float_to_str(float(new_node * unit_scale),
                                        -1*math.ceil(math.log(abs(unit_scale), 10)))
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
        if f_type.data_cls is not type(None):
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
                    prec = field_type.mantissa_len*math.log(2, 10)

                if unit_scale:
                    prec -= math.ceil(math.log(abs(unit_scale), 10))
                self.last_flushed_val = float_to_str(node, prec)
            elif unit_scale and isinstance(self.node, int):
                self.last_flushed_val = float_to_str(
                    float(node), -1*math.ceil(math.log(abs(unit_scale), 10)))
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
        if self.evaluate_entry_fields:
            if "__" in new_node:
                raise ValueError("Unsafe operations included in evaluation string.")
            new_node = eval(new_node, {'__builtins__': {}}, number_eval_globals)

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
        if f_type.data_cls is not type(None):
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
            value_width = max(int(math.ceil(node_size * 5/2)),
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

            value_width = int(math.ceil(math.log(value_max, 10))) + adjust

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
