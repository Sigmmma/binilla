import threadsafe_tkinter as tk
import tkinter.ttk as ttk

from tkcolorpicker import askcolor

from binilla.widgets.field_widgets import container_frame


class ColorPickerFrame(container_frame.ContainerFrame):

    color_type = int

    def __init__(self, *args, **kwargs):
        container_frame.ContainerFrame.__init__(self, *args, **kwargs)

        name_map = self.desc['NAME_MAP']
        for c in 'argb':
            if c in name_map:
                self.color_type = self.desc[name_map[c]]['TYPE'].node_cls
                break

        self._initialized = True
        self.reload()

    def apply_style(self, seen=None):
        container_frame.ContainerFrame.apply_style(self, seen)
        if getattr(self, 'color_btn', None):
            self.update_selector_button()

    def update_selector_button(self):
        if not getattr(self, 'color_btn', None):
            return

        self.color_btn.config(
            bg=self.get_color()[1], activebackground=self.get_color()[1],
            highlightbackground=self.get_color()[1], highlightthickness=1,
            state=tk.DISABLED if self.disabled else tk.NORMAL)

    def reload(self):
        self.has_alpha = 'a' in self.desc['NAME_MAP']
    
        container_frame.ContainerFrame.reload(self)
        self.update_selector_button()

    def set_disabled(self, disable=True):
        disable = disable or not self.editable
        if self.node is None and not disable:
            return

        if bool(disable) != self.disabled:
            self.color_btn.config(state=tk.DISABLED if disable else tk.NORMAL)

        container_frame.ContainerFrame.set_disabled(self, disable)

    def populate(self):
        self.has_alpha = 'a' in self.desc['NAME_MAP']

        container_frame.ContainerFrame.populate(self)
        self.color_btn = tk.Button(
            self.content, width=4, command=self.select_color)
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

    def get_color(self, alpha=False):
        if alpha:
            try:
                int_color = (int(self.red   * 255.0 + 0.5),
                             int(self.green * 255.0 + 0.5),
                             int(self.blue  * 255.0 + 0.5),
                             int(self.alpha * 255.0 + 0.5),
                             )
                return (int_color, '#%02x%02x%02x%02x' % int_color)
            except Exception:
                return ((0, 0, 0), '#00000000')
        else:
            try:
                int_color = (int(self.red   * 255.0 + 0.5),
                             int(self.green * 255.0 + 0.5),
                             int(self.blue  * 255.0 + 0.5),
                             )
                return (int_color, '#%02x%02x%02x' % int_color)
            except Exception:
                return ((0, 0, 0), '#000000')

    def select_color(self):
        self.flush()
        if getattr(self, 'color_btn', None):
            self.color_btn.config(bg=self.get_color()[1])

        color, hex_color = askcolor(
            self.get_color(alpha=self.has_alpha)[1],
            alpha=self.has_alpha,
            parent=self
            )

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
        if self.has_alpha:
            self.red, self.green, self.blue, self.alpha = float_c_color
        else:
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
