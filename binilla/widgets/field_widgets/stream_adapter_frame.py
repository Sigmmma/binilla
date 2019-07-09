import threadsafe_tkinter as tk
import tkinter.ttk as ttk

from traceback import format_exc

from binilla import editor_constants as e_c
from binilla.widgets.field_widgets import field_widget, container_frame,\
     union_frame, data_frame


class StreamAdapterFrame(container_frame.ContainerFrame):

    def __init__(self, *args, **kwargs):
        field_widget.FieldWidget.__init__(self, *args, **kwargs)

        if self.f_widget_parent is None:
            self.pack_padx = self.pack_pady = 0

        kwargs.update(relief='flat', bd=0, highlightthickness=0)

        show_frame = bool(kwargs.pop('show_frame', not self.blocks_start_hidden))
        if self.is_empty and self.hide_if_blank:
            show_frame = False

        tk.Frame.__init__(self, *args, **e_c.fix_kwargs(**kwargs))

        self.show = tk.BooleanVar(self)
        self.show.set(show_frame)

        toggle_text = '-' if show_frame else '+'

        self.title = tk.Frame(self, relief='raised')
        self.content = tk.Frame(self, relief="sunken")
        self.show_btn = ttk.Checkbutton(
            self.title, width=3, text=toggle_text, command=self.toggle_visible,
            style='ShowButton.TButton')
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
        self.title_label.pack(side="left", fill="x", expand=True)

        self.title.pack(fill="x", expand=True)
        for w in (self.export_btn, self.import_btn):
            w.pack(side="right", padx=(0, 4), pady=2)

        self.populate()
        self._initialized = True

    def apply_style(self, seen=None):
        container_frame.ContainerFrame.apply_style(self, seen)
        self.title.config(bd=self.frame_depth, bg=self.frame_bg_color)
        self.title_label.config(bg=self.frame_bg_color)
        self.content.config(bd=self.frame_depth)

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
                          tag_window=self.tag_window, attr_index='SUB_STRUCT',
                          disabled=self.disabled, f_widget_parent=self,
                          desc=data_desc, show_frame=self.show.get(),
                          dont_padx_fields=True)
            try:
                widget = widget_cls(self.content, **kwargs)
            except Exception:
                print(format_exc())
                widget = data_frame.NullFrame(self.content, **kwargs)

            wid = id(widget)
            f_widget_ids.append(wid)
            f_widget_ids_map['SUB_STRUCT'] = wid
            f_widget_ids_map_inv[wid] = 'SUB_STRUCT'

            self.build_f_widget_cache()

            # now that the field widgets are created, position them
            if self.show.get():
                self.pose_fields()
        except Exception:
            print(format_exc())

    reload = populate

    def pose_fields(self):
        w = self.f_widgets[self.f_widget_ids_map.get("SUB_STRUCT")]
        for child in self.content.children.values():
            if child not in (w, self.comment_frame):
                child.pack_forget()

        if w:
            # by adding a fixed amount of padding, we fix a problem
            # with difficult to predict padding based on nesting
            w.pack(fill='x', anchor='nw',
                   padx=self.vertical_padx, pady=self.vertical_pady)

        self.content.pack(fill='x', anchor='nw', expand=True)
