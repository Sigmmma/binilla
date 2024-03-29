import os
import platform
import threadsafe_tkinter as tk
import string
import time
import tkinter.ttk

from os.path import exists
from threading import Thread
from tkinter import messagebox
from tkinter import constants as t_c
from traceback import format_exc

from binilla import constants
from binilla.edit_manager import EditManager
from binilla.widgets.field_widgets import FieldWidget
from binilla.widgets.field_widget_picker import def_widget_picker
from binilla.widgets.binilla_widget import BinillaWidget
from binilla.widgets import get_mouse_delta


__all__ = ("TagWindow", "ConfigWindow",
           "make_hotkey_string", "read_hotkey_string", "get_mouse_delta")



is_lnx = "linux" in platform.system().lower()
try:
    from platform import win32_ver
    win_info = win32_ver()
except Exception:
    win_info = None

if win_info is None or win_info[0] == '':
    OS_PAD_X, OS_PAD_Y = 0, 0
elif win_info[0] in ('XP', '2000', '2003Server'):
    OS_PAD_X, OS_PAD_Y = 8, 64
elif win_info[0] in ('Vista', '7', '8.1', '10'):
    OS_PAD_X, OS_PAD_Y = 15, 77
else:
    OS_PAD_X, OS_PAD_Y = 8, 64


def make_hotkey_string(hotkey):
    keys = hotkey.combo
    prefix = keys.modifier.enum_name.replace('_', '-')
    key = keys.key.enum_name

    if key == 'NONE':
        return None
    elif prefix == 'NONE':
        prefix = ''
    else:
        prefix += '-'

    combo = '<%s%s>'
    if key[0] == '_': key = key[1:]
    if key in string.digits:
        combo = '%s%s'
    elif key in string.ascii_lowercase and 'Shift' in prefix:
        key = key.upper()

    return combo % (prefix, key)


def read_hotkey_string(combo):
    combo = combo.strip('<>')
    pieces = combo.split('-')

    keys = ['', 'NONE']
    if len(pieces):
        keys[1] = pieces.pop(-1)

        # sort them alphabetically so the enum_name will match
        if len(pieces):
            pieces = sorted(pieces)
            for i in range(len(pieces)):
                keys[0] += pieces[i] + '_'
            keys[0] = keys[0][:-1]
        else:
            keys[0] = 'NONE'

    return keys


class TagWindow(tk.Toplevel, BinillaWidget):
    tag = None  # The tag this Toplevel is displaying
    app_root = None  # The Tk widget controlling this Toplevel. This Tk
    #                  should also have certain methods, like delete_tag
    field_widget = None  # The single FieldWidget held in this window
    widget_picker = def_widget_picker  # The WidgetPicker to use for selecting
    #                                    the widget to build when populating
    # The tag handler that built the tag this window is displaying
    handler = None

    can_scroll = True

    edit_manager = None

    # whether the user declined to resize the edit history
    resize_declined = False

    # Whether or not the Tag this window is editing was created
    # from scratch, i.e. it isn't actually being read from anything.
    is_new_tag = False

    iconbitmap_filepath = None

    # Determines whether this TagWindow is currently trying to undo or redo
    # This exists to prevent trying to apply multiple undos or redos at once
    _applying_edit_state = False
    _resizing_window = False
    _saving = False
    _initialized = False
    _scrolling = False
    _last_saved_edit_index = 0
    _pending_scroll_counts = ()

    def __init__(self, master, tag=None, *args, **kwargs):
        self._pending_scroll_counts = [0, 0]
        self.tag = tag
        self.is_new_tag = kwargs.pop("is_new_tag", self.is_new_tag)

        if 'tag_def' in kwargs:
            self.tag_def = kwargs.pop('tag_def')
        elif self.tag is not None:
            self.tag_def = self.tag.definition

        if 'widget_picker' in kwargs:
            self.widget_picker = kwargs.pop('widget_picker')
        elif hasattr(self.app_root, 'widget_picker'):
            self.widget_picker = self.app_root.widget_picker

        self.app_root = kwargs.pop('app_root', master)
        self.handler = kwargs.pop('handler', None)

        kwargs.update(bg=self.default_bg_color)

        BinillaWidget.__init__(self)
        tk.Toplevel.__init__(self, master, *args, **kwargs)

        # do any initialization that requires this object
        # be initialized as a tk.Toplevel object
        self.post_toplevel_init()


        try:
            max_undos = self.app_root.max_undos
        except AttributeError:
            max_undos = 100

        try:
            use_def_dims = self.settings.window_flags.use_default_dimensions
        except AttributeError:
            use_def_dims = False

        self.edit_manager = EditManager(max_undos)

        with self.style_change_lock:
            self.update()
            if use_def_dims:
                width  = self.settings.default_dimensions.w
                height = self.settings.default_dimensions.h
            else:
                width  = self.root_frame.winfo_reqwidth()  + self.root_vsb.winfo_reqwidth()  + 2
                height = self.root_frame.winfo_reqheight() + self.root_hsb.winfo_reqheight() + 2

            self.resize_window(width, height)
            self.apply_style()

        self._initialized = True

    def post_toplevel_init(self):
        self.update_title()
        try:
            self.iconbitmap(self.iconbitmap_filepath)
        except Exception:
            print("Could not load window icon.")

        self.creating_label = tk.Label(
            self, text=("Creating widgets. Please wait..."))
        self.styling_label = tk.Label(
            self, text=("Styling widgets. Please wait..."))

        # create the root_canvas and the root_frame within the canvas
        self.root_canvas = rc = tk.Canvas(self, highlightthickness=0)
        self.root_frame = rf = tk.Frame(rc, highlightthickness=0)

        # create and set the x and y scrollbars for the root_canvas
        self.root_hsb = tk.Scrollbar(
            self, orient='horizontal', command=rc.xview)
        self.root_vsb = tk.Scrollbar(
            self, orient='vertical', command=rc.yview)
        rc.config(xscrollcommand=self.root_hsb.set, xscrollincrement=1,
                  yscrollcommand=self.root_vsb.set, yscrollincrement=1)
        self.root_frame_id = rc.create_window((0, 0), window=rf, anchor='nw')

        # make it so if this window is selected it changes the
        # selected_tag attribute of self.app_root to self.tag
        self.bind('<Button>', self.select_window)
        self.bind('<FocusIn>', self.select_window)

        rf.bind('<Configure>', self._resize_canvas)
        rc.bind('<Configure>', self._resize_frame)

        # make the window not show up on the start bar
        if self.app_root:
            self.transient(self.app_root)

        # populate the window
        self.creating_label.pack(fill="both", expand=True)
        self.populate()

        # pack da stuff
        self.root_hsb.pack(side=t_c.BOTTOM, fill='x')
        self.root_vsb.pack(side=t_c.RIGHT,  fill='y')

        # set the hotkey bindings
        self.bind_hotkeys()

        # if this tag doesnt exist at the given filepath, it's new.
        try:
            new = not self.tag.filepath.is_file()
        except Exception:
            new = True

        if new:
            try:
                self.field_widget.set_edited()
            except Exception:
                pass

        self.creating_label.pack_forget()

    # The config settings governing the way the window works
    @property
    def settings(self):
        try:
            return self.app_root.config_file.data.tag_windows
        except Exception:
            return None

    @property
    def backup_settings(self):
        try:
            return self.app_root.config_file.data.tag_backup
        except Exception:
            return None

    @property
    def window_flags(self):
        try:
            return self.settings.window_flags
        except Exception:
            return None

    @property
    def widget_flags(self):
        try:
            return self.settings.widget_flags
        except Exception:
            return None

    @property
    def file_handling_flags(self):
        try:
            return self.settings.file_handling_flags
        except Exception:
            return None

    @property
    def needs_flushing(self):
        return getattr(self.field_widget, "needs_flushing", False)

    @property
    def has_unsaved_changes(self):
        if self.is_new_tag:
            return True
        elif self.edit_manager:
            if self.edit_manager.len != 0 and (self._last_saved_edit_index <
                                               self.edit_manager.len - 1):
                if self._last_saved_edit_index == self.edit_manager.edit_index:
                    return False

        return getattr(self.field_widget, "edited", False)

    @property
    def max_undos(self):
        try:
            return bool(self.app_root.config_file.data.tag_windows.max_undos)
        except Exception:
            return 0

    @property
    def enforce_max(self):
        try:
            return bool(self.widget_flags.enforce_max)
        except Exception:
            return True

    @property
    def enforce_min(self):
        try:
            return bool(self.widget_flags.enforce_min)
        except Exception:
            return True

    @property
    def use_gui_names(self):
        try:
            return bool(self.widget_flags.use_gui_names)
        except Exception:
            return True

    @property
    def is_config(self):
        try:
            return self.tag is self.app_root.config_file
        except Exception:
            return False

    @property
    def all_editable(self):
        try:
            return bool(self.widget_flags.edit_uneditable)
        except Exception:
            return False

    @property
    def all_bools_visible(self):
        try:
            return bool(self.widget_flags.show_all_bools)
        except Exception:
            return False

    @property
    def show_comments(self):
        try:
            return bool(self.widget_flags.show_comments)
        except Exception:
            return False

    @property
    def show_sidetips(self):
        try:
            return bool(self.widget_flags.show_sidetips)
        except Exception:
            return False

    @property
    def max_height(self):
        # OS_PAD_Y accounts for the width of the windows border
        return self.winfo_screenheight() - self.winfo_y() - OS_PAD_Y

    @property
    def max_width(self):
        # OS_PAD_X accounts for the width of the windows border
        return self.winfo_screenwidth() - self.winfo_x() - OS_PAD_X

    def get_visible(self, visibility_level):
        if (visibility_level is None or
            visibility_level >= constants.VISIBILITY_SHOWN):
            return True

        try:
            if self.is_config and not (self.app_root.config_file.data.\
                                       app_window.flags.debug_mode):
                # No one should be fucking with the configs hidden values
                return False
        except Exception:
            pass

        try:
            if visibility_level == constants.VISIBILITY_METADATA:
                return bool(self.widget_flags.show_structure_meta)
            elif visibility_level == constants.VISIBILITY_HIDDEN:
                return bool(self.widget_flags.show_invisible)
            else:
                return True
        except Exception:
            return False

    def _resize_canvas(self, e):
        '''
        Updates the size of the canvas when the window is resized.
        '''
        if self._resizing_window:
            return

        self._resizing_window = True
        try:
            rf,   rc   = self.root_frame,     self.root_canvas
            rf_w, rf_h = rf.winfo_reqwidth(), rf.winfo_reqheight()
            rc.config(scrollregion="0 0 %s %s" % (rf_w, rf_h))
            if rf_w != rc.winfo_reqwidth() or rf_h != rc.winfo_reqheight():
                rc.config(width=rf_w, height=rf_h)

            # account for the size of the scrollbars when resizing the window
            new_window_width  = rf_w + self.root_vsb.winfo_reqwidth()  + 2
            new_window_height = rf_h + self.root_hsb.winfo_reqheight() + 2

            if self.window_flags is not None:
                cap_size = self.window_flags.cap_window_size
                dont_shrink_width  = self.window_flags.dont_shrink_width
                dont_shrink_height = self.window_flags.dont_shrink_height
                if not self.window_flags.auto_resize_width:
                    new_window_width = None
                if not self.window_flags.auto_resize_height:
                    new_window_height = None
            else:
                cap_size = dont_shrink_width = dont_shrink_height = True

            if new_window_width is not None or new_window_height is not None:
                self.resize_window(
                    new_window_width, new_window_height, cap_size,
                    dont_shrink_width, dont_shrink_height)
            self._resizing_window = False
        except Exception:
            self._resizing_window = False
            raise

    def _resize_frame(self, e):
        '''
        Update the size of the frame and scrollbars when the canvas is resized.
        '''
        rf_id = self.root_frame_id
        rf,   rc   = self.root_frame, self.root_canvas
        rc_w, rc_h = rc.winfo_reqwidth(), rc.winfo_reqheight()
        if rc_w != rf.winfo_reqwidth() or rc_h != rf.winfo_reqheight():
            rc.itemconfigure(rf_id, width=rc_w, height=rc_h)

    def mousewheel_scroll_x(self, e):
        if self.should_scroll(e):
            self.after_idle(
                lambda func=self.mousewheel_scroll, event=e: func(0, event))

    def mousewheel_scroll_y(self, e):
        if self.should_scroll(e):
            self.after_idle(
                lambda func=self.mousewheel_scroll, event=e: func(1, event))

    def mousewheel_scroll(self, axis, event):
        bbox = self.root_canvas.bbox(tk.ALL)
        dims = (self.root_canvas.winfo_width(),
                self.root_canvas.winfo_height())
        if not bbox or (dims[axis] >= (bbox[2 + axis] - bbox[axis])):
            return

        self._pending_scroll_counts[axis] += 1
        if self._scrolling:
            return

        self._scrolling = True
        try:
            axis_char = "xy"[axis]
            scroll_func = getattr(self.root_canvas, axis_char + "view_scroll")
            scroll_inc = (getattr(self.app_root, "scroll_increment_" + axis_char, 20) *
                          self._pending_scroll_counts[axis] * get_mouse_delta(event))
            self._pending_scroll_counts[axis] = 0
            scroll_func(int(scroll_inc), "units")
            self.root_canvas.update()
            self._scrolling = False
        except Exception:
            self._scrolling = False
            raise

    def should_scroll(self, e):
        '''
        Returns True if, when given a tkinter event, this TagWindow should
        have its scrolling method follow through when it is invoked.
        Returns False otherwise.
        '''
        if not self.can_scroll:
            return False

        try:
            hover = self.winfo_containing(e.x_root, e.y_root)
            if not hover.can_scroll:
                return True

            if (not isinstance(hover, FieldWidget) and
                hasattr(hover, "f_widget_parent")):
                # ScrollMenu option boxes are parented to the root frame,
                # so climbing their masters won't work like below.
                hover = hover.f_widget_parent
            else:
                # climb up the masters until we find one that can scroll
                while hover.master and not hasattr(hover, "should_scroll"):
                    hover = hover.master

            if hover is not self:
                return not hover.should_scroll(e)
        except AttributeError:
            pass
        return True

    def bind_hotkeys(self, new_hotkeys=None):
        '''
        Binds the given hotkeys to the given methods of this class.
        Class methods must be the name of each method as a string.
        '''
        if not hasattr(self.app_root, 'config_file'):
            return

        if new_hotkeys is None:
            new_hotkeys = {}
            for hotkey in self.app_root.config_file.data.all_hotkeys.tag_window_hotkeys:
                combo = make_hotkey_string(hotkey)
                if combo is None or not hotkey.method.enum_name:
                    continue
                new_hotkeys[combo] = hotkey.method.enum_name

        assert isinstance(new_hotkeys, dict)

        # unbind any old hotkeys
        self.unbind_hotkeys()
        curr_hotkeys = self.app_root.curr_tag_window_hotkeys

        self.new_hotkeys = {}

        for hotkey, func_name in new_hotkeys.items():
            try:
                func = getattr(self, func_name, None)
                if func is not None:
                    if is_lnx and "MouseWheel" in hotkey:
                        self.bind(hotkey.replace("MouseWheel", "4"), func)
                        self.bind(hotkey.replace("MouseWheel", "5"), func)
                    else:
                        self.bind(hotkey, func)

                    curr_hotkeys[hotkey] = func_name
            except Exception:
                print(format_exc())

    def destroy(self):
        '''
        Handles destroying this Toplevel and removing the tag from app_root
        '''
        if self._saving:
            print("Still saving. Please wait.")
            return True
        elif self.applying_style_change:
            print("Still applying style change. Please wait.")
            return True
        elif not self._initialized:
            print("Still initializing window. Please wait.")
            return True

        try:
            app_root = self.app_root
            tag = self.tag
            try:
                if self.needs_flushing:
                    self.field_widget.flush()

                if self.has_unsaved_changes:
                    try:
                        path = tag.filepath
                    except Exception:
                        path = "This tag"

                    try: self.app_root.select_tag_window(self)
                    except Exception: pass

                    ans = messagebox.askyesnocancel(
                        "Unsaved changes", ("%s contains unsaved changes!\n" +
                        "Do you want to save changes before closing?") % path,
                        icon='warning', parent=self)

                    if ans is None:
                        return True
                    elif ans is True:
                        app_root.save_tag(tag)
            except Exception:
                print(format_exc())

            self.tag = None
            self.app_root = None

            if tag is not None:
                # remove the tag and tag_window from the app_root
                try: app_root.delete_tag(tag, 0)
                except Exception: print(format_exc())

        except Exception:
            print(format_exc())

        # call pack_forget so destroying doesn't keep redrawing the widgets
        self.field_widget.pack_forget()
        tk.Toplevel.destroy(self)
        self.delete_all_widget_refs()

    def save(self, **kwargs):
        '''Flushes any lingering changes in the widgets to the tag.'''
        if self._saving:
            print("Still saving. Please wait.")
            return

        self._saving = True
        title = self.title()
        exception = None
        try:
            self.title("Saving... " + title)
            if self.field_widget.needs_flushing:
                self.field_widget.flush()

            if hasattr(self.app_root, 'config_file'):
                kwargs.setdefault('temp', self.file_handling_flags.write_as_temp)
                kwargs.setdefault('int_test', self.file_handling_flags.integrity_test)
                kwargs.setdefault("replace_backup", True)

                kwargs.setdefault(
                    'backup', self.backup_settings.max_count > 0)
                time_since_backup = float("inf")
                if kwargs["backup"]:
                    backup_paths = self.tag.handler.\
                                   get_backup_paths_by_timestamps(
                                       self.tag.filepath, True)
                    if backup_paths:
                        time_since_backup = time.time() - max(backup_paths)

                if time_since_backup < max(0.0, self.backup_settings.interval):
                    # not enough time has passed to backup
                    kwargs["backup"] = False

                if kwargs["backup"]:
                    if not kwargs.get("backuppath"):
                        kwargs["backuppath"] = self.tag.handler.get_next_backup_filepath(
                            self.tag.filepath, self.backup_settings.max_count)

                    if kwargs["backuppath"] == self.tag.filepath:
                        # somehow backuppath became self.tag.filepath
                        kwargs["backup"] = False

                    if (self.tag.filepath.is_file() and
                        self.backup_settings.flags.notify_when_backing_up):
                        print("Backing up to: '%s'" % kwargs["backuppath"])

            self.field_widget.set_disabled(True)
            save_thread = Thread(target=self.tag.serialize, kwargs=kwargs,
                                 daemon=True)
            save_thread.start()
            # do this threaded so it doesn't freeze the ui
            while True:
                save_thread.join(0.05)
                self.update()
                # NOTE TO SELF: is_alive is a method, NOT a decorated property...
                if not save_thread.is_alive():
                    break

            self.field_widget.set_edited(False)
            self.is_new_tag = False
            if self.edit_manager and self.edit_manager.maxlen:
                self._last_saved_edit_index = self.edit_manager.edit_index

        except Exception as e:
            exception = e
        finally:
            self.field_widget.set_disabled(False)
            self.title(title)
            self._saving = False

        if exception:
            raise exception

    def resize_window(self, new_width=None, new_height=None, cap_size=True,
                      dont_shrink_width=True, dont_shrink_height=True):
        '''
        Resizes this TagWindow to the width and height specified.
        If cap_size is True the width and height will be capped so they
        do not expand beyond the right and bottom edges of the screen.
        '''

        old_width, old_height  = self.winfo_width(), self.winfo_height()
        if new_width is None or (dont_shrink_width and new_width < old_width):
            new_width = old_width
        if new_height is None or (dont_shrink_height and new_height < old_height):
            new_height = old_height

        if cap_size:
            # get the max size the width and height that the window
            # can be set to before it would be partially offscreen
            max_width = self.max_width
            max_height = self.max_height

            # if the new width/height is larger than the max, cap them
            if max_width < new_width:
                new_width = max_width
                old_width = 0
            if max_height < new_height:
                new_height = max_height
                old_height = 0

        if dont_shrink_width  and new_width  < old_width:
            new_width  = old_width
        if dont_shrink_height and new_height < old_height:
            new_height = old_height

        # aint nothin to do if they're the same!
        if new_width == old_width and new_height == old_height:
            return
        self.geometry('%sx%s' % (new_width, new_height))

    def enter_style_change(self):
        self.root_canvas.pack_forget()
        self.styling_label.pack(fill="both", expand=True)
        self.update()

    def exit_style_change(self):
        self.styling_label.pack_forget()
        self.root_canvas.pack(side='left', fill='both', expand=True)

    def apply_style(self, seen=None):
        BinillaWidget.apply_style(self, seen)
        self.root_canvas.config(bg=self.default_bg_color)
        self.root_frame.config(bg=self.default_bg_color)

    def populate(self):
        '''
        Destroys the FieldWidget attached to this TagWindow and remakes it.
        '''
        # Destroy everything
        if hasattr(self.field_widget, 'destroy'):
            self.field_widget.destroy()
            self.field_widget = None

        if self.tag is None:
            return

        # Get the desc of the top block in the tag
        root_block = self.tag.data

        # Get the widget to build
        widget_cls = self.widget_picker.get_widget(root_block.desc)

        # Rebuild everything
        self.field_widget = widget_cls(self.root_frame, node=root_block,
                                       show_frame=True, tag_window=self)
        self.field_widget.pack(expand=True, fill='both')

    def reload(self, e=None):
        self.field_widget.reload()

    def select_window(self, e):
        '''Makes this windows tag the selected tag in self.app_root'''
        if self.app_root:
            self.app_root.selected_tag = self.tag

    def unbind_hotkeys(self, hotkeys=None):
        if hotkeys is None:
            hotkeys = {}
            for hotkey in self.app_root.config_file.data.all_hotkeys.tag_window_hotkeys:
                combo = make_hotkey_string(hotkey)
                if combo is None or not hotkey.method.enum_name:
                    continue
                hotkeys[combo] = hotkey.method.enum_name
        if isinstance(hotkeys, dict):
            hotkeys = hotkeys.keys()

        for hotkey in hotkeys:
            try:
                if is_lnx and "MouseWheel" in hotkey:
                    self.unbind(hotkey.replace("MouseWheel", "4"))
                    self.unbind(hotkey.replace("MouseWheel", "5"))
                else:
                    self.unbind(hotkey)
            except Exception:
                pass

    def edit_undo(self, e=None):
        if self.edit_manager is None or self._saving: return
        focus = self.focus_get()

        # Text widgets handle their own undo/redo states, and it
        # would be a real pain to try and override all of that
        if isinstance(focus, tk.Text):
            if hasattr(focus, 'text_undo'):
                focus.text_undo()
            return

        # make this a separate check to make it more likely to hold
        if self._applying_edit_state: return
        self._applying_edit_state = True
        try:
            state = self.edit_manager.undo()
            if state is not None:
                state.apply_func(edit_state=state, undo=True)
            self._applying_edit_state = False

            is_dirty = self._last_saved_edit_index != self.edit_manager.edit_index
            if is_dirty != self.field_widget.edited:
                self.field_widget.set_edited(is_dirty)

            self.title(self.title())
        except Exception:
            self._applying_edit_state = False
            raise

    def edit_redo(self, e=None):
        if self.edit_manager is None or self._saving: return
        focus = self.focus_get()

        # Text widgets handle their own undo/redo states, and it
        # would be a real pain to try and override all of that
        if isinstance(focus, tk.Text):
            if hasattr(focus, 'text_redo'):
                focus.text_redo()
            return

        # make this a separate check to make it more likely to hold
        if self._applying_edit_state: return
        self._applying_edit_state = True
        try:
            state = self.edit_manager.redo()
            if state is not None:
                state.apply_func(edit_state=state, undo=False)
            self._applying_edit_state = False

            is_dirty = self._last_saved_edit_index != self.edit_manager.edit_index
            if is_dirty != self.field_widget.edited:
                self.field_widget.set_edited(is_dirty)

            self.title(self.title())
        except Exception:
            self._applying_edit_state = False
            raise

    def edit_state_add(self, edit_state):
        if self.edit_manager is None: return
        # make this a separate check to make it more likely to hold
        if self._applying_edit_state: return
        self._applying_edit_state = True
        try:
            em = self.edit_manager
            # if we are adding a new edit state in such a way that
            # it'll erase our ability to redo to the last point we
            # saved, we need to make sure the last_saved_edit_index
            # cannot be equal to the edit_index until a save is done.
            if em.edit_index < self._last_saved_edit_index:
                self._last_saved_edit_index = -1

            if em.edit_index < em.maxlen:
                self.resize_declined = False
            elif em.edit_index == em.maxlen:
                # shift the last edit index down if it's valid
                if self._last_saved_edit_index >= 0:
                    self._last_saved_edit_index -= 1

                if not self.resize_declined and em.maxlen:
                    try:
                        added = max(self.app_root.max_undos, 100)
                    except AttributeError:
                        added = 100
                    ans = messagebox.askyesno(
                        "Edit history maxed.",
                        "This edit will begin overwriting the edit history!\n" +
                        "Do you wish to extend the history by %s states first?" %
                        added, icon='warning', parent=self)

                    if ans:
                        em.resize(em.maxlen + added)
                    else:
                        self.resize_declined = True

            em.add_state(edit_state)
            self._applying_edit_state = False
            self.title(self.title())
        except Exception:
            self._applying_edit_state = False
            raise

    def edit_clear(self):
        if self.edit_manager is None: return
        # make this a separate check to make it more likely to hold
        if self._applying_edit_state: return
        self._applying_edit_state = True
        try:
            self.edit_manager.clear()
            self.resize_declined = False
            self._applying_edit_state = False
            self.title(self.title())
        except Exception:
            self._applying_edit_state = False
            raise

    def edit_resize(self, maxlen):
        if self.edit_manager is None: return
        # make this a separate check to make it more likely to hold
        if self._applying_edit_state: return
        self._applying_edit_state = True
        try:
            self.edit_manager.resize(maxlen)
            self.resize_declined = False
            self._applying_edit_state = False
        except Exception:
            self._applying_edit_state = False
            raise

    def title(self, new_title=None):
        if new_title is not None:
            if self.has_unsaved_changes:
                new_title = "*" + new_title

            tk.Toplevel.title(self, new_title)
            return new_title.lstrip("*")

        return tk.Toplevel.title(self).lstrip("*")

    def update_title(self, new_title=None):
        if new_title is None:
            new_title = str(self.tag.filepath)
        self.title(new_title)


class ConfigWindow(TagWindow):

    def destroy(self):
        if self._saving:
            print("Still saving. Please wait.")
            return True
        elif self.applying_style_change:
            print("Still applying style change. Please wait.")
            return True
        elif not self._initialized:
            print("Still initializing window. Please wait.")
            return True

        tag = self.tag
        self.tag = None
        try:
            self.field_widget.flush()
            self.app_root.save_config()
        except Exception:
            pass
        try:
            self.app_root.delete_tag(tag, False)
        except Exception:
            pass
        tk.Toplevel.destroy(self)
        self.app_root.config_window = None

    def update_config_window(self):
        self.field_widget.set_edited(False)
        self.title(self.title())
        if self.edit_manager and self.edit_manager.maxlen:
            self._last_saved_edit_index = self.edit_manager.edit_index
