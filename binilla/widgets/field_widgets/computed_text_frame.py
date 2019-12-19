import tkinter as tk

from traceback import format_exc
from binilla.widgets.field_widgets import text_frame


class ComputedTextFrame(text_frame.TextFrame):
    def export_node(self): pass
    def import_node(self): pass
    def build_replace_map(self): pass
    def flush(self, *a, **kw): pass
    def set_edited(self, *a, **kw): pass
    def set_needs_flushing(self, *a, **kw): pass
    def populate(self): self.reload()

    def reload(self):
        if self.parent is None:
            return

        try:
            try:
                new_text = self.get_text()
            except Exception:
                return

            self.data_text.config(state=tk.NORMAL)
            self.data_text.delete(1.0, tk.END)
            self.data_text.insert(1.0, new_text)
        except Exception:
            print(format_exc())
        finally:
            if self.disabled:
                self.data_text.config(state=tk.DISABLED)
            else:
                self.data_text.config(state=tk.NORMAL)

    def get_text(self):
        raise NotImplementedError()
