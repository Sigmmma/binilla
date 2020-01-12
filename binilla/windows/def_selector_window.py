import threadsafe_tkinter as tk
from binilla.widgets.binilla_widget import BinillaWidget


class DefSelectorWindow(tk.Toplevel, BinillaWidget):

    def __init__(self, app_root, action, *args, **kwargs):
        self.app_root = app_root
        try:
            title = app_root.handler.defs_filepath
        except AttributeError:
            title = "Tag definitions"

        title = "%s (%s total)" % (kwargs.pop('title', title),
                                   len(self.app_root.handler.defs))

        BinillaWidget.__init__(self)
        tk.Toplevel.__init__(self, app_root, *args, **kwargs)
        self.title(title)

        self.action = action
        self.def_id = None
        self.sorted_def_ids = []
        self.minsize(width=400, height=300)

        self.list_canvas = tk.Canvas(self, highlightthickness=0)
        self.button_canvas = tk.Canvas(self, height=50, highlightthickness=0)

        #create and set the y scrollbar for the canvas root
        self.def_listbox = tk.Listbox(
            self.list_canvas, selectmode='single', exportselection=False,
            highlightthickness=0, font=self.get_font("fixed"))
        self.def_listbox.font_type = "fixed"

        self.ok_btn = tk.Button(
            self.button_canvas, text='OK', command=self.complete_action, width=16)
        self.cancel_btn = tk.Button(
            self.button_canvas, text='Cancel', command=self.destroy, width=16)
        self.hsb = tk.Scrollbar(self.button_canvas, orient='horizontal')
        self.vsb = tk.Scrollbar(self.list_canvas,   orient='vertical')

        self.def_listbox.config(xscrollcommand=self.hsb.set,
                                yscrollcommand=self.vsb.set)

        self.hsb.config(command=self.def_listbox.xview)
        self.vsb.config(command=self.def_listbox.yview)

        self.list_canvas.pack(fill='both', expand=True)
        self.button_canvas.pack(fill='x')

        self.vsb.pack(side='right', fill='y')
        self.def_listbox.pack(fill='both', expand=True)

        self.hsb.pack(side='top', fill='x')
        self.ok_btn.pack(side='left',      padx=9)
        self.cancel_btn.pack(side='right', padx=9)

        # make selecting things more natural
        self.def_listbox.bind('<<ListboxSelect>>', self.set_selected_def)
        self.def_listbox.bind('<Return>', self.complete_action)
        self.def_listbox.bind('<Double-Button-1>', self.complete_action)
        self.ok_btn.bind('<Return>', self.complete_action)
        self.cancel_btn.bind('<Return>', self.destroy)
        self.bind('<Escape>', self.destroy)

        self.transient(self.app_root)
        self.wait_visibility()
        self.lift()
        self.grab_set()

        self.apply_style()
        self.cancel_btn.focus_set()
        self.populate_listbox()

    def destroy(self, e=None):
        try:
            self.app_root.def_selector_window = None
        except AttributeError:
            pass
        tk.Toplevel.destroy(self)

    def complete_action(self, e=None):
        if self.def_id is not None:
            self.action(self.def_id)
        self.destroy()

    def populate_listbox(self):
        defs_root = self.app_root.handler.defs_path
        defs = self.app_root.handler.defs

        id_pad = ext_pad = 0
        defs_by_ext = {}

        #loop over all the defs and find the max amount of
        #padding needed between the ID and the Ext strings
        for def_id in defs:
            d = defs[def_id]
            if len(def_id) > id_pad:
                id_pad = len(def_id)

        for def_id in defs.keys():
            definiton = defs[def_id]
            ext = definiton.ext[1:]
            local_defs = defs_by_ext.get(ext, {})
            local_defs[def_id] = definiton

            defs_by_ext[ext] = local_defs

        sorted_ids = []
        for ext in sorted(defs_by_ext.keys()):
            sorted_ids.extend(tuple(defs_by_ext[ext].keys()))

        self.sorted_def_ids = tuple(sorted_ids)

        #loop over all the definitions
        for def_id in sorted_ids:
            d = defs[def_id]

            self.def_listbox.insert('end', 'ID=%s  %sExt=%s'%
                                    (def_id, ' '*(id_pad-len(def_id)),
                                     d.ext[1:] ))

    def set_selected_def(self, event=None):
        indexes = [int(i) for i in self.def_listbox.curselection()]

        if len(indexes) == 1:
            self.def_id = self.sorted_def_ids[indexes[0]]
