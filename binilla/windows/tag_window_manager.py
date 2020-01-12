import threadsafe_tkinter as tk
from binilla.widgets.binilla_widget import BinillaWidget


class TagWindowManager(tk.Toplevel, BinillaWidget):

    app_root = None

    list_index_to_window = None

    def __init__(self, app_root, *args, **kwargs):
        self.app_root = app_root
        BinillaWidget.__init__(self)
        tk.Toplevel.__init__(self, app_root, *args, **kwargs)

        self.list_index_to_window = []

        self.title("Tag window manager")
        self.minsize(width=400, height=250)

        # make the frames
        self.windows_frame = tk.Frame(self)
        self.button_frame = tk.Frame(self)
        self.ok_frame = tk.Frame(self.button_frame)
        self.cancel_frame = tk.Frame(self.button_frame)

        # make the buttons
        self.ok_button = tk.Button(
            self.ok_frame, text='OK', width=15, command=self.select)
        self.cancel_button = tk.Button(
            self.cancel_frame, text='Cancel', width=15, command=self.destroy)

        # make the scrollbars and listbox
        self.scrollbar_y = tk.Scrollbar(self.windows_frame, orient="vertical")
        self.scrollbar_x = tk.Scrollbar(self, orient="horizontal")
        self.windows_listbox = tk.Listbox(
            self.windows_frame, selectmode='single',
            exportselection=False, highlightthickness=0,
            xscrollcommand=self.scrollbar_x.set,
            yscrollcommand=self.scrollbar_y.set)

        # set up the scrollbars
        self.scrollbar_x.config(command=self.windows_listbox.xview)
        self.scrollbar_y.config(command=self.windows_listbox.yview)

        # set up the keybindings
        self.windows_listbox.bind('<Return>', self.select)
        self.scrollbar_x.bind('<Return>', self.select)
        self.scrollbar_y.bind('<Return>', self.select)
        self.windows_listbox.bind('<Double-Button-1>', self.select)
        self.ok_button.bind('<Return>', self.select)
        self.cancel_button.bind('<Return>', self.destroy)
        self.bind('<Escape>', self.destroy)

        # store the windows by title
        windows_by_title = {}
        for w in self.app_root.tag_windows.values():
            windows_by_title[w.title()] = w

        # populate the listbox
        for title in sorted(windows_by_title):
            self.list_index_to_window.append(windows_by_title[title])
            self.windows_listbox.insert('end', title)

        self.windows_listbox.select_set(0)

        # pack everything
        self.ok_button.pack(padx=12, pady=5, side='right')
        self.cancel_button.pack(padx=12, pady=5, side='left')
        self.ok_frame.pack(side='left', fill='x', expand=True)
        self.cancel_frame.pack(side='right', fill='x', expand=True)

        self.windows_listbox.pack(side='left', fill="both", expand=True)
        self.scrollbar_y.pack(side='left', fill="y")

        self.windows_frame.pack(fill="both", expand=True)
        self.scrollbar_x.pack(fill="x")
        self.button_frame.pack(fill="x")

        self.apply_style()
        self.transient(self.app_root)
        self.ok_button.focus_set()
        self.wait_visibility()
        self.lift()
        self.grab_set()

    def destroy(self, e=None):
        try:
            self.app_root.tag_window_manager = None
        except AttributeError:
            pass
        tk.Toplevel.destroy(self)

    def select(self, e=None):
        indexes = [int(i) for i in self.windows_listbox.curselection()]
        w = self.list_index_to_window[indexes[0]]

        self.destroy()
        self.app_root.select_tag_window(w)
