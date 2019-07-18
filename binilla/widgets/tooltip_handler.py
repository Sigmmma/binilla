from time import time
import threadsafe_tkinter as tk

from binilla import editor_constants as e_c
from binilla.widgets.binilla_widget import BinillaWidget


__all__ = ("ToolTipHandler", )


class ToolTipHandler(BinillaWidget):
    app_root = None
    tag_window = None
    tip_window = None
    focus_widget = None

    hover_time = 1.0
    rehover_time = 0.5
    hover_start = 0.0
    rehover_start = 0.0

    curr_tip_text = ''

    # run the check 15 times a second
    schedule_rate = int(1000/15)
    last_mouse_x = 0
    last_mouse_y = 0

    tip_offset_x = 15
    tip_offset_y = 0

    def __init__(self, app_root, *args, **kwargs):
        BinillaWidget.__init__(self)
        self.app_root = app_root
        self.hover_start = time()

        # begin the looping
        app_root.after(int(self.schedule_rate), self.check_loop)

    def check_loop(self):
        # get the widget under the mouse
        root = self.app_root
        mouse_x, mouse_y = root.winfo_pointerx(), root.winfo_pointery()

        mouse_dx = mouse_x - self.last_mouse_x
        mouse_dy = mouse_y - self.last_mouse_y

        self.last_mouse_x = mouse_x
        self.last_mouse_y = mouse_y

        # move the tip_window to where it needs to be
        if self.tip_window and mouse_dx or mouse_dy:
            try:
                self.tip_window.geometry("+%s+%s" % (mouse_x + self.tip_offset_x,
                                                     mouse_y + self.tip_offset_y))
            except Exception:
                pass

        try:
            focus = root.winfo_containing(mouse_x, mouse_y)
        except KeyError:
            self.app_root.after(self.schedule_rate, self.check_loop)
            return

        try:
            tip_text = focus.tooltip_string
        except Exception:
            tip_text = None

        curr_time = time()

        if self.curr_tip_text != tip_text and self.tip_window:
            # a tip window is displayed and the focus is different
            self.hide_tip()
            self.rehover_start = curr_time

        if self.tip_window is None:
            # no tip window is displayed, so start trying to display one

            can_display = (curr_time >= self.hover_time + self.hover_start or
                           curr_time <= self.rehover_time + self.rehover_start)
            
            if not tip_text or not self.show_tooltips:
                # reset the hover counter cause nothing is under focus
                self.hover_start = curr_time
            elif focus is not self.focus_widget:
                # start counting how long this widget has been in focus
                self.hover_start = curr_time
                self.focus_widget = focus
            elif can_display:
                # reached the hover time! display the tooltip window
                self.show_tip(mouse_x + self.tip_offset_x,
                              mouse_y + self.tip_offset_y, tip_text)
                self.curr_tip_text = tip_text
        self.app_root.after(self.schedule_rate, self.check_loop)

    @property
    def widget_flags(self):
        try:
            return self.app_root.config_file.data.tag_windows.widget_flags
        except Exception:
            return None

    @property
    def show_tooltips(self):
        try:
            return bool(self.widget_flags.show_tooltips)
        except Exception:
            return False

    def show_tip(self, pos_x, pos_y, tip_text):
        if self.tip_window:
            return

        self.tip_window = tk.Toplevel(self.app_root)
        self.tip_window.wm_overrideredirect(1)
        self.tip_window.wm_geometry("+%d+%d" % (pos_x, pos_y))
        label = tk.Label(
            self.tip_window, text=tip_text, justify='left', relief='solid',
            bg=self.tooltip_bg_color, fg=self.text_normal_color, borderwidth=1,
            font=self.get_font("tooltip"))
        label.pack()

    def hide_tip(self):
        try: self.tip_window.destroy()
        except Exception: pass
        self.tip_window = None
        self.focus_widget = None
