import collections
import gc
import os
import platform
import re
import sys
import threadsafe_tkinter as tk
import webbrowser

# make the ui more responsive by lowering the time between processing events
tk.TkWrapper.idle_time = 2

from datetime import datetime
from pathlib import Path, PurePath
from time import time, sleep
from traceback import format_exc
from tkinter import messagebox

import binilla

# load the binilla constants so they are injected before any defs are loaded
from binilla import constants as s_c
s_c.inject()
from supyr_struct.field_types import FieldType

from binilla import editor_constants as e_c
from binilla.widgets.field_widget_picker import WidgetPicker
from binilla.widgets.binilla_widget import BinillaWidget
from binilla.widgets.tooltip_handler import ToolTipHandler
from binilla.handler import Handler
from binilla.util import IORedirecter, is_path_empty
from binilla.windows.about_window import AboutWindow
from binilla.windows.def_selector_window import DefSelectorWindow
from binilla.windows import filedialog
from binilla.windows.filedialog import askopenfilenames, askopenfilename,\
     askdirectory, asksaveasfilename
from binilla.windows.tag_window import TagWindow, ConfigWindow,\
     make_hotkey_string, read_hotkey_string
from binilla.windows.tag_window_manager import TagWindowManager


this_curr_dir = Path.cwd()
default_config_path = this_curr_dir.joinpath('binilla.cfg')
if "linux" in sys.platform:
    default_config_path = Path(
        Path.home(), ".local", "share", "binilla", 'binilla.cfg')

default_hotkeys = collections.OrderedDict()
for k, v in (
        ('<Control-w>', 'close_selected_window'),
        ('<Control-o>', 'load'),
        ('<Control-n>', 'new'),
        ('<Control-s>', 'save'),
        ('<Control-f>', 'show_defs'),
        ('<Control-p>', 'print_tag'),

        ('<Control-BackSpace>', 'clear_console'),
        ('<Control-backslash>', 'cascade'),
        ('<Control-Shift-bar>', 'tile_vertical'),
        ('<Control-Shift-underscore>', 'tile_horizontal'),

        ('<Alt-m>', 'minimize_all'),
        ('<Alt-r>', 'restore_all'),
        ('<Alt-w>', 'show_window_manager'),
        ('<Alt-c>', 'show_config_file'),
        ('<Alt-o>', 'load_as'),
        ('<Alt-s>', 'save_as'),
        ('<Alt-F4>', 'exit'),

        ('<Alt-Control-c>', 'apply_config'),

        ('<Control-Shift-s>', 'save_all'),
        ):
    default_hotkeys[k] = v


default_tag_window_hotkeys = collections.OrderedDict()
for k, v in (
        ('<Control-z>', 'edit_undo'),
        ('<Control-y>', 'edit_redo'),
        ('<MouseWheel>', 'mousewheel_scroll_y'),
        ('<Shift-MouseWheel>', 'mousewheel_scroll_x'),
        ):
    default_tag_window_hotkeys[k] = v


class Binilla(tk.Tk, BinillaWidget):
    # the tag of the currently in-focus TagWindow
    selected_tag = None
    # the Handler for managing loaded tags
    handler = None

    # a window that displays and allows selecting loaded definitions
    def_selector_window = None
    # a window that allows you to select a TagWindow from all open ones
    tag_window_manager = None

    # the default WidgetPicker instance to use for selecting widgets
    widget_picker = WidgetPicker()
    def_tag_window_cls = TagWindow
    config_window_class = ConfigWindow

    # dict of open TagWindow instances. keys are the ids of each of the windows
    tag_windows = None
    # map of the id of each tag to the id of the window displaying it
    tag_id_to_window_id = None

    '''Directories/filepaths'''
    curr_dir = this_curr_dir
    _styles_dir = curr_dir.joinpath("styles")
    _last_load_dir = curr_dir
    _last_defs_dir = curr_dir
    _last_imp_dir  = curr_dir
    _config_path = default_config_path

    recent_tag_max = 20
    recent_tagpaths = ()

    '''Modules to display in About window'''
    about_module_names = (
        "arbytmap",
        "binilla",
        "supyr_struct",
        "threadsafe_tkinter",
        )

    about_messages = ()

    '''Miscellaneous properties'''
    _initialized = False
    _window_geometry_initialized = False
    config_made_anew = False
    app_name = "Binilla"  # the name of the app(used in window title)
    version = "%s.%s.%s" % binilla.__version__
    log_filename = 'binilla.log'
    debug = 0
    debug_mode = False
    untitled_num = 0  # when creating a new, untitled tag, this integer is used
    #                   in its name like so: 'untitled%s' % self.untitled_num
    max_undos = 1000
    icon_filepath = Path("")
    app_bitmap_filepath = Path("")

    issue_tracker_url = binilla.__website__ + "/issues"

    '''Config properties'''
    style_def = None
    config_def = None
    config_version_def = None
    style_version_def = None
    style_defs = ()
    config_defs = ()

    config_version = 2
    style_version = 2
    config_window = None
    # the tag that holds all the config settings for this application
    config_file = None
    log_file = None

    widget_depth_names = e_c.widget_depth_names
    color_names = e_c.color_names
    font_names = e_c.font_names

    '''Window properties'''
    # When tags are opened they are tiled, first vertically, then horizontally.
    # curr_step_y is incremented for each tag opened till it reaches max_step_y
    # At that point it resets to 0 and increments curr_step_x by 1.
    # If curr_step_x reaches max_step_x it will reset to 0. The position of an
    # opened TagWindow is set relative to the application's top left corner.
    # The x offset is shifted right by curr_step_x*tile_stride_x and
    # the y offset is shifted down  by curr_step_y*tile_stride_y.
    max_step_x = 4
    max_step_y = 8

    curr_step_x = 0
    curr_step_y = 0

    cascade_stride = 60
    tile_stride_x = 120
    tile_stride_y = 30

    default_tag_window_width = 480
    default_tag_window_height = 640

    window_menu_max_len = 15

    app_width = 640
    app_height = 480
    app_offset_x = 0
    app_offset_y = 0

    sync_offset_x = 0
    sync_offset_y = 0

    scroll_increment_x = 50
    scroll_increment_y = 50

    terminal_out = None

    sync_window_movement = True  # Whether or not to sync the movement of
    #                              the TagWindow instances with the app.

    # a mapping of hotkey bindings to method names
    curr_hotkeys = None
    curr_tag_window_hotkeys = None

    # the ToolTipFrame that displays the tooltip of whatever
    # widget is currently in focus or under the mouse.
    tooltip_handler = None

    def __init__(self, *args, **kwargs):
        for s in ('curr_dir', 'config_version', 'window_menu_max_len',
                  'app_width', 'app_height', 'app_offset_x', 'app_offset_y'):
            if s in kwargs:
                setattr(self, s, kwargs.pop(s))

        self.widget_picker = kwargs.pop('widget_picker', self.widget_picker)
        self.debug = kwargs.pop('debug', self.debug)
        self.tag_windows = {}
        self.tag_id_to_window_id = {}

        if 'handler' in kwargs:
            self.handler = kwargs.pop('handler')
        else:
            self.handler = Handler(debug=self.debug, case_sensitive=e_c.IS_LNX)

        self.recent_tagpaths = []
        if self.curr_hotkeys is None:
            self.curr_hotkeys = {}
        if self.curr_tag_window_hotkeys is None:
            self.curr_tag_window_hotkeys = {}

        try:
            # will fail with an AttributeError not initialized.
            # also, cant use getattr, as tkinter.Tk overloads __getattr__
            # with a call to getattr, so it will recurse to max stack depth
            _tk = object.__getattribute__(self, "tk")
        except AttributeError:
            _tk = None

        if _tk is None:
            tk.Tk.__init__(self, *args, **{
                k: v for k, v in kwargs.items() if k in (
                "screenName", "baseName", "className", "useTk", "sync", "use"
                )})

        BinillaWidget.__init__(self)
        # NOTE: Do this import AFTER Tk interpreter is set up, otherwise
        # it will fail to get the names of the font families
        from binilla.defs.config_def import config_def, config_version_def
        from binilla.defs.style_def import style_def, style_version_def
        from binilla.defs.v1_config_def import v1_config_def
        from binilla.defs.v1_style_def import v1_style_def

        style_defs  = {1: v1_style_def,  2: style_def}
        config_defs = {1: v1_config_def, 2: config_def}

        self.style_def  = kwargs.pop('style_def', style_def)
        self.config_def = kwargs.pop('config_def', config_def)
        self.style_defs  = kwargs.pop('style_defs', style_defs)
        self.config_defs = kwargs.pop('config_defs', config_defs)
        self.style_version_def  = kwargs.pop('style_version_def', style_version_def)
        self.config_version_def = kwargs.pop('config_version_def', config_version_def)
        if self.config_file is not None:
            pass
        elif self.config_path.is_file():
            # load the config file
            try:
                self.load_config()
            except Exception:
                print(format_exc())
                self.make_config()
                self.config_made_anew = True
        else:
            # make a config file
            self.make_config()
            self.config_made_anew = True

        if not self.curr_dir.exists():
            self.curr_dir = this_curr_dir
            try:
                self.config_file.data.directory_paths.curr_dir.path = str(this_curr_dir)
            except Exception:
                pass

        if self.handler is not None:
            self.handler.log_filename = self.log_filename

        #fonts
        self.reload_fonts()

        self.app_name = str(kwargs.pop('app_name', self.app_name))
        self.version  = str(kwargs.pop('version', self.version))
        self.title('%s v%s' % (self.app_name, self.version))
        self.minsize(width=200, height=50)
        self.protocol("WM_DELETE_WINDOW", self.exit)
        self.bind('<Configure>', self.sync_tag_window_pos)

        self.bind_hotkeys()

        ######################################################################
        ######################################################################
        # MAKE METHODS FOR CREATING/DESTROYING MENUS SO THEY CAN BE CUSTOMIZED
        # This includes creating a system to manage the menus and keep track
        # of which ones exist, their order on the menu bar, their names, etc.
        # Once that is done, replace the below code with code that uses them.
        ######################################################################
        ######################################################################

        #create the main menu and add its commands
        self.main_menu = tk.Menu(self)
        self.file_menu = tk.Menu(self.main_menu, tearoff=0)
        self.edit_menu = tk.Menu(self.main_menu, tearoff=0)
        self.settings_menu = tk.Menu(self.main_menu, tearoff=0)
        self.debug_menu   = tk.Menu(self.main_menu, tearoff=0)
        self.windows_menu = tk.Menu(
            self.main_menu, tearoff=0, postcommand=self.generate_windows_menu)
        self.recent_tags_menu = tk.Menu(
            self.main_menu, tearoff=0,
            postcommand=self.generate_recent_tag_menu)

        self.config(menu=self.main_menu)

        #add cascades and commands to the main_menu
        self.main_menu.add_cascade(label="File",    menu=self.file_menu)
        #self.main_menu.add_cascade(label="Edit",   menu=self.edit_menu)
        self.main_menu.add_cascade(label="Settings", menu=self.settings_menu)
        self.main_menu.add_cascade(label="Tag Windows", menu=self.windows_menu)
        #self.main_menu.add_command(label="Help")
        self.main_menu.add_command(label="About", command=self.show_about_window)
        self.main_menu.add_command(label="Report Bug", command=self.open_issue_tracker)
        try:
            self.debug_mode = bool(self.config_file.data.app_window.flags.debug_mode)
        except Exception:
            self.debug_mode = True

        if self.debug_mode:
            self.main_menu.add_cascade(label="Debug", menu=self.debug_menu)

        #add the commands to the file_menu
        fm_ac = self.file_menu.add_command
        fm_ac(label="New",        command=self.new)
        self.file_menu.add_cascade(label="Recent tags     ",
                                   menu=self.recent_tags_menu)
        fm_ac(label="Open",       command=self.load)
        fm_ac(label="Open as...", command=self.load_as)
        fm_ac(label="Close", command=self.close_selected_window)
        self.file_menu.add_separator()
        fm_ac(label="Save",       command=self.save)
        fm_ac(label="Save as...", command=self.save_as)
        fm_ac(label="Save all",   command=self.save_all)
        self.file_menu.add_separator()
        fm_ac(label="Exit",       command=self.exit)

        #add the commands to the settings_menu
        self.settings_menu.add_command(
            label="Load definitions", command=self.select_defs)
        self.settings_menu.add_command(
            label="Show definitions", command=self.show_defs)
        self.settings_menu.add_separator()
        self.settings_menu.add_command(
            label="Edit config", command=self.show_config_file)
        self.settings_menu.add_separator()
        self.settings_menu.add_command(
            label="Load style", command=self.load_style)
        self.settings_menu.add_command(
            label="Save current style", command=self.make_style)
        self.settings_menu.add_command(
            label="Reset style", command=self.reset_style)

        self.debug_menu.add_command(label="Print tag", command=self.print_tag)
        self.debug_menu.add_command(label="Clear console",
                                    command=self.clear_console)
        self.debug_menu.add_separator()
        self.debug_menu.add_command(
            label="Force big endian", command=self.force_big_endian)
        self.debug_menu.add_command(
            label="Force little endian", command=self.force_little_endian)
        self.debug_menu.add_command(
            label="Force normal endian", command=self.force_normal_endian)
        self.debug_menu.add_separator()

        # make the canvas for anything in the main window
        self.root_frame = tk.Frame(self, bd=3, highlightthickness=0,
                                   relief=tk.SUNKEN)
        self.root_frame.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)
        self.tooltip_handler = ToolTipHandler(self)

        # make the io redirector and redirect sys.stdout to it
        self.orig_stdout = sys.stdout

        # make the console output
        self.make_io_text()
        self.apply_style()

        if self.config_file.data.app_window.flags.load_last_workspace:
            try:
                self.load_last_workspace()
            except Exception:
                pass

        self.sync_offset_x = self.winfo_x()
        self.sync_offset_y = self.winfo_y()

        if hasattr(filedialog, "no_native_file_dialog_error"):
            filedialog.no_native_file_dialog_error()

        self._initialized = True

    @property
    def styles_dir(self):
        return self._styles_dir
    @styles_dir.setter
    def styles_dir(self, new_val):
        if not isinstance(new_val, Path):
            new_val = Path(new_val)
        self._styles_dir = new_val

    @property
    def last_load_dir(self):
        return self._last_load_dir
    @last_load_dir.setter
    def last_load_dir(self, new_val):
        if not isinstance(new_val, Path):
            new_val = Path(new_val)
        self._last_load_dir = new_val

    @property
    def last_defs_dir(self):
        return self._last_defs_dir
    @last_defs_dir.setter
    def last_defs_dir(self, new_val):
        if not isinstance(new_val, Path):
            new_val = Path(new_val)
        self._defs_load_dir = new_val

    @property
    def last_imp_dir(self):
        return self._last_imp_dir
    @last_imp_dir.setter
    def last_imp_dir(self, new_val):
        if not isinstance(new_val, Path):
            new_val = Path(new_val)
        self._last_imp_dir = new_val

    @property
    def config_path(self):
        return self._config_path
    @config_path.setter
    def config_path(self, new_val):
        if not isinstance(new_val, Path):
            new_val = Path(new_val)
        self._config_path = new_val

    def add_to_recent(self, filepath):
        recent = self.recent_tagpaths
        for i in range(len(recent)-1, -1, -1):
            if recent[i] == filepath:
                recent.pop(i)

        if len(recent) >= self.recent_tag_max:
            del recent[0: len(recent) - (self.recent_tag_max - 1)]

        if self.recent_tag_max > 0:
            recent.append(filepath)

    def add_tag(self, tag, new_filepath=''):
        '''
        new_filepath is expected to be a relative filepath if
        self.handler.tagsdir_relative == True
        '''
        filepath = tag.filepath
        handler = self.handler
        tags_dir = handler.tagsdir
        add_to_recent = True
        new_filepath = Path(new_filepath)

        if handler.tagsdir_relative:
            abs_filepath = Path(tags_dir, tag.filepath)
            abs_new_filepath = Path(tags_dir, new_filepath)
        else:
            abs_filepath = Path(tag.filepath)
            abs_new_filepath = Path(new_filepath)

        try:
            existing_tag = handler.get_tag(tag.rel_filepath, tag.def_id)
        except Exception:
            existing_tag = None

        if not existing_tag:
            # tag doesnt already exist.
            # we dont need to remove it from anything.
            pass
        elif existing_tag is tag:
            # remove the tag from the handler under its current filepath
            self.delete_tag(tag, False, False)
        else:
            print('"%s" is already loaded' % abs_filepath)
            return False

        if is_path_empty(filepath):
            # the path is blank(new tag), give it a unique name
            new_filepath = Path('untitled%s%s' % (self.untitled_num, tag.ext))
            abs_new_filepath = Path(tags_dir, new_filepath)
            self.untitled_num += 1
            add_to_recent = False

        if not is_path_empty(abs_new_filepath):
            tag.filepath = abs_new_filepath

        if add_to_recent:
            self.add_to_recent(tag.filepath)

        tag.tags_dir = tags_dir
        if handler.tagsdir_relative:
            try:
                tag.rel_filepath = new_filepath.relative_to(Path(tags_dir))
            except Exception:
                tag.rel_filepath = new_filepath

        # index the tag under its new filepath
        handler.add_tag(tag, new_filepath)

        return True

    def make_io_text(self, master=None):
        if master is None:
            master = self.root_frame

        self.io_frame = tk.Frame(master, highlightthickness=0)
        self.io_text = tk.Text(
            self.io_frame, font=self.get_font("console"), state=tk.DISABLED,
            fg=self.io_fg_color, bg=self.io_bg_color)
        self.io_text.font_type = "console"
        self.io_scroll_y = tk.Scrollbar(self.io_frame, orient=tk.VERTICAL)

        self.io_scroll_y.config(command=self.io_text.yview)
        self.io_text.config(yscrollcommand=self.io_scroll_y.set)

        self.io_scroll_y.pack(fill=tk.Y, side=tk.RIGHT)
        self.io_text.pack(fill=tk.BOTH, expand=True)
        self.io_frame.pack(fill=tk.BOTH, expand=True)

        try:
            flags = self.config_file.data.app_window.flags
            edit_log, disable = flags.log_output, flags.disable_io_redirect
        except Exception:
            edit_log, disable = True, False

        self.terminal_out = IORedirecter(self.io_text, edit_log=edit_log,
                                         log_file=self.log_file)
        sys.stdout = self.orig_stdout if disable else self.terminal_out

    def bind_hotkeys(self, new_hotkeys=None):
        '''
        Binds the given hotkeys to the given methods of this class.
        Class methods must be the name of each method as a string.
        '''
        if new_hotkeys is None:
            new_hotkeys = {}
            for hotkey in self.config_file.data.all_hotkeys.hotkeys:
                combo = make_hotkey_string(hotkey)
                if combo is None or not hotkey.method.enum_name:
                    continue
                new_hotkeys[combo] = hotkey.method.enum_name
        assert isinstance(new_hotkeys, dict)

        # unbind any old hotkeys
        self.unbind_hotkeys()
        self.curr_hotkeys = new_hotkeys

        for hotkey, func_name in new_hotkeys.items():
            try:
                func = getattr(self, func_name, None)
                if func is not None:
                    if e_c.IS_LNX and "MouseWheel" in hotkey:
                        self.bind_all(hotkey.replace("MouseWheel", "4"), func)
                        self.bind_all(hotkey.replace("MouseWheel", "5"), func)
                    else:
                        self.bind_all(hotkey, func)
            except Exception:
                print(format_exc())

    def cascade(self, e=None):
        windows = self.tag_windows

        # reset the offsets to 0 and get the strides
        self.curr_step_y = 0
        self.curr_step_x = 0
        x_stride = self.cascade_stride
        y_stride = self.tile_stride_y

        # reposition the window
        for wid in sorted(windows):
            window = windows[wid]

            # dont cascade hidden windows
            if window.state() == 'withdrawn':
                continue

            if self.curr_step_y > self.max_step_y:
                self.curr_step_y = 0
                self.curr_step_x += 1
            if self.curr_step_x > self.max_step_x:
                self.curr_step_x = 0

            self.place_window_relative(
                window, (self.curr_step_x * x_stride +
                         self.curr_step_y * (x_stride//2) + 5),
                self.curr_step_y*y_stride + 50)
            self.curr_step_y += 1
            window.update_idletasks()

            self.selected_tag = None
            self.select_tag_window(window)

    def close_selected_window(self, e=None):
        if self.selected_tag is None:
            return

        # close the window and make sure the tag is deleted
        self.delete_tag(self.selected_tag)

        # select the next TagWindow
        try:
            for wid in reversed(sorted(self.tag_windows)):
                w = self.tag_windows[wid]
                if hasattr(w, 'tag') and w.state() != 'withdrawn':
                    self.select_tag_window(w)
                    self.update()
                    return
        except Exception:
            pass

    def clear_console(self, e=None):
        try:
            self.io_text.config(state=tk.NORMAL)
            self.io_text.delete('1.0', tk.END)
            self.io_text.config(state=tk.DISABLED)
        except Exception:
            print(format_exc())

    def delete_tag(self, tag, destroy_window=True, forget_window=True):
        try:
            if tag is None:
                return

            if destroy_window or forget_window:
                tid = id(tag)
                def_id = tag.def_id
                tid_to_wid = self.tag_id_to_window_id

                if tid in tid_to_wid:
                    wid = tid_to_wid[tid]
                    t_window = self.tag_windows[wid]
                    if destroy_window and t_window.destroy():
                        # couldn't destroy window, it's saving or something
                        return

                    tid_to_wid.pop(tid, None)
                    self.tag_windows.pop(wid, None)

            if tag is self.config_file:
                pass
            elif hasattr(tag, "rel_filepath"):
                # remove the tag from the handlers tag library.
                # We need to delete it by the relative filepath
                # rather than having it detect it using the tag
                # because the handlers tagsdir may have changed
                # from what it was when the tag was created, so
                # it wont be able to determine the rel_filepath
                tag.handler.delete_tag(filepath=tag.rel_filepath)
            else:
                tag.handler.delete_tag(filepath=tag.filepath)

            if self.selected_tag is tag:
                self.selected_tag = None

            gc.collect()
        except Exception:
            print(format_exc())

    def exit(self, e=None):
        '''Exits the program.'''
        try:
            self.record_open_tags()
            self.update_config()
        except Exception:
            print(format_exc())

        windows = []
        try:
            for wid in reversed(sorted(self.tag_windows)):
                windows.append(self.tag_windows[wid])
        except Exception:
            print(format_exc())

        for w in windows:
            try:
                if w.destroy():
                    # couldn't destroy. window is saving or something
                    return
            except Exception:
                pass

        try:
            # need to save before destroying the
            # windows or bindings wont be saved
            self.config_file.serialize(temp=False, backup=False)
        except Exception:
            print(format_exc())

        try:
            sys.stdout = self.orig_stdout
            if self.log_file:
                self.log_file.close()
        except Exception:
            print(format_exc())

        try: self.destroy()  # wont close if a listener is open without this
        except Exception: pass

    def force_big_endian(self, e=None):
        FieldType.force_big()

    def force_little_endian(self, e=None):
        FieldType.force_little()

    def force_normal_endian(self, e=None):
        FieldType.force_normal()

    def record_open_tags(self):
        try:
            handler = self.handler
            config_file = self.config_file
            open_tags = config_file.data.open_tags
            del open_tags[:]

            for wid in sorted(self.tag_windows):
                w = self.tag_windows[wid]
                tag = w.tag

                # dont store tags that arent from the current handler
                if tag in (config_file, None) or tag.handler is not handler:
                    continue

                open_tags.append()
                open_tag = open_tags[-1]
                open_header = open_tag.header

                if w.state() == 'withdrawn':
                    open_header.flags.minimized = True

                pos_x, pos_y = w.winfo_x(), w.winfo_y()
                width, height = w.geometry().split('+')[0].split('x')[:2]

                open_header.offset_x, open_header.offset_y = pos_x, pos_y
                open_header.width, open_header.height = int(width), int(height)

                open_tag.def_id, open_tag.path = tag.def_id, str(tag.filepath)
        except Exception:
            print(format_exc())

    def load_last_workspace(self):
        try:
            config_file = self.config_file
            open_tags = config_file.data.open_tags

            for open_tag in open_tags:
                open_header = open_tag.header
                windows = self.load_tags(filepaths=open_tag.path,
                                         def_id=open_tag.def_id)
                if not windows:
                    continue

                w = windows[0]
                if open_header.flags.minimized:
                    windows[0].withdraw()
                    self.selected_tag = None

                windows[0].geometry("%sx%s+%s+%s" % (
                    open_header.width, open_header.height,
                    open_header.offset_x, open_header.offset_y))
        except Exception:
            print(format_exc())

    def generate_windows_menu(self):
        menu = self.windows_menu
        menu.delete(0, "end")  # clear the menu
        sync_word = 'off' if self.sync_window_movement else 'on'

        #add the commands to the windows_menu
        menu.add_command(label="Minimize all", command=self.minimize_all)
        menu.add_command(label="Restore all", command=self.restore_all)
        menu.add_command(label="Turn movement sync " + sync_word,
                         command=self.toggle_sync)
        menu.add_separator()
        menu.add_command(label="Cascade", command=self.cascade)
        menu.add_command(label="Tile vertical", command=self.tile_vertical)
        menu.add_command(label="Tile horizontal", command=self.tile_horizontal)

        i = 0
        max_len = self.window_menu_max_len

        if not self.tag_windows:
            return

        menu.add_separator()

        # store the windows by label
        windows_by_label = {}
        for w in self.tag_windows.values():
            windows_by_label[w.title()] = w

        for label in sorted(windows_by_label):
            w = windows_by_label[label]
            if i >= max_len:
                menu.add_separator()
                menu.add_command(label="Window manager",
                                 command=self.show_window_manager)
                break
            try:
                menu.add_command(
                    label=label, command=lambda w=w: self.select_tag_window(w))
                i += 1
            except Exception:
                print(format_exc())

    def generate_recent_tag_menu(self):
        menu = self.recent_tags_menu
        menu.delete(0, "end")  # clear the menu

        i = 0
        for tagpath in reversed(self.recent_tagpaths):
            try:
                menu.add_command(
                    label="%s  %s" % (i, str(tagpath)),
                    command=lambda s=str(tagpath): self.load_tags(s))
                i += 1
            except Exception:
                print(format_exc())

        menu.add_separator()
        menu.add_command(label="Clear recently opened tags",
                         command=lambda self=self:
                         self.recent_tagpaths.__delitem__(
                             slice(None, None, None))
                         )

    def apply_config(self, e=None):
        config_data = self.config_file.data
        app_window = config_data.app_window
        tag_windows = config_data.tag_windows

        open_tags = config_data.open_tags
        recent_tags = config_data.recent_tags
        dir_paths = config_data.directory_paths

        self.debug = self.handler.debug = app_window.flags.debug_mode
        self.sync_window_movement = tag_windows.window_flags.sync_window_movement

        if self._initialized:
            self.bind_hotkeys()
            sys.stdout = (self.orig_stdout
                          if app_window.flags.disable_io_redirect
                          else self.terminal_out)
        else:
            # only load the recent tagpaths when loading binilla
            self.recent_tagpaths = []

            for tagpath in recent_tags:
                self.recent_tagpaths.append(Path(tagpath.path))

        try:
            for s in app_window.NAME_MAP.keys():
                if hasattr(self, s):
                    setattr(self, s, app_window[s])

            self.max_step_x, self.max_step_y = app_window.max_step
            self.tile_stride_x, self.tile_stride_y = app_window.tile_stride

            self.default_tag_window_width, self.default_tag_window_height = \
                                           tag_windows.default_dimensions
            self.scroll_increment_x, self.scroll_increment_y = \
                                     tag_windows.scroll_increment
        except Exception:
            print(format_exc())

        self.recent_tag_max = app_window.recent_tag_max
        self.max_undos = tag_windows.max_undos

        for s in ('last_load_dir', 'last_defs_dir', 'last_imp_dir',
                  'curr_dir', 'styles_dir')[:len(dir_paths)]:
            try: setattr(self, s, Path(dir_paths[s].path))
            except IndexError: pass

        for wid in sorted(self.tag_windows):
            w = self.tag_windows[wid]
            try:
                w.edit_resize(self.max_undos)
            except Exception:
                print(format_exc())

        self.handler.tagsdir = dir_paths.tags_dir.path
        self.handler.backup_dir_basename = config_data.tag_backup.folder_basename

        self.log_filename = Path(dir_paths.debug_log_path.path).name

        try:
            self.debug_mode = bool(app_window.flags.debug_mode)
        except Exception:
            self.debug_mode = True

        if self.log_file is None:
            if config_data.app_window.flags.log_output:
                try:
                    self.log_file = self.config_path.parent.joinpath(
                        self.log_filename).open('a+')

                    # write a timestamp to the file
                    time = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
                    self.log_file.write("\n%s%s%s\n" %
                                        ("-"*30, time, "-"*(50-len(time))))
                except Exception:
                    print(format_exc())

            if self.terminal_out is not None:
                if config_data.app_window.flags.log_output:
                    self.terminal_out.log_file = self.log_file
                else:
                    self.terminal_out.log_file = None

        self.load_style(style_file=self.config_file)

    def load_config(self, filepath=None):
        if filepath is None:
            filepath = self.config_path
        filepath = Path(filepath)
        assert filepath.is_file()

        # load the config file
        version_info = self.config_version_def.build(filepath=str(filepath)).data
        if version_info.id.data != version_info.id.DEFAULT:
            raise ValueError("Config header signature is invalid.")

        if version_info.version == self.config_version:
            self.config_file = self.config_def.build(filepath=str(filepath))
        else:
            print("Upgrading config to version %s" % self.config_version)
            self.config_file = self.upgrade_config_version(filepath)

        app_window = self.config_file.data.app_window

        self.app_width = app_window.app_width
        self.app_height = app_window.app_height
        self.app_offset_x = app_window.app_offset_x
        self.app_offset_y = app_window.app_offset_y

        self.apply_config()

        hotkeys = self.config_file.data.all_hotkeys.hotkeys
        tag_window_hotkeys = self.config_file.data.all_hotkeys.tag_window_hotkeys

        for hotkey in hotkeys:
            combo = make_hotkey_string(hotkey)
            if combo is None or not hotkey.method.enum_name:
                continue
            self.curr_hotkeys[combo] = hotkey.method.enum_name

        for hotkey in tag_window_hotkeys:
            combo = make_hotkey_string(hotkey)
            if combo is None or not hotkey.method.enum_name:
                continue
            self.curr_tag_window_hotkeys[combo] = hotkey.method.enum_name

    def load_style(self, filepath=None, style_file=None):
        if isinstance(filepath, tk.Event):
            filepath = None

        if style_file is None:
            if filepath is None:
                filepath = askopenfilename(
                    initialdir=self.styles_dir, parent=self,
                    title="Select style to load",
                    filetypes=(("binilla_style", "*.sty"), ('All', '*')))

            if is_path_empty(filepath):
                return
            else:
                filepath = Path(filepath)

            assert filepath.is_file()
            self.styles_dir = filepath.parent

            version_info = self.style_version_def.build(filepath=str(filepath)).data
            if version_info.id.data != version_info.id.DEFAULT:
                raise ValueError("Style header signature is invalid.")

            if version_info.version == self.style_version:
                style_file = self.style_def.build(filepath=str(filepath))
            else:
                print("Upgrading style to version %s" % self.style_version)
                style_file = self.upgrade_style_version(filepath)

        assert hasattr(style_file, 'data')

        style_data = style_file.data

        w_and_h = style_data.appearance.widths_and_heights
        padding = style_data.appearance.padding
        depths = style_data.appearance.depths
        colors = style_data.appearance.colors
        fonts = style_data.appearance.fonts

        try:
            BinillaWidget.title_width = w_and_h.title_width
            BinillaWidget.scroll_menu_width = w_and_h.scroll_menu_width
            BinillaWidget.enum_menu_width = w_and_h.enum_menu_width
            BinillaWidget.min_entry_width = w_and_h.min_entry_width

            BinillaWidget.textbox_width, BinillaWidget.textbox_height = w_and_h.textbox
            BinillaWidget.scroll_menu_max_width, BinillaWidget.scroll_menu_max_height = w_and_h.scroll_menu
            BinillaWidget.bool_frame_min_width, BinillaWidget.bool_frame_max_width = w_and_h.bool_frame_width
            BinillaWidget.bool_frame_min_height, BinillaWidget.bool_frame_max_height = w_and_h.bool_frame_height

            BinillaWidget.def_int_entry_width, BinillaWidget.def_float_entry_width,\
                                               BinillaWidget.def_string_entry_width\
                                               = w_and_h.default_entry_widths
            BinillaWidget.max_int_entry_width, BinillaWidget.max_float_entry_width,\
                                               BinillaWidget.max_string_entry_width\
                                               = w_and_h.max_entry_widths
        except Exception:
            print(format_exc())

        for s in ('vertical_padx', 'vertical_pady',
                  'horizontal_padx', 'horizontal_pady'):
            try: setattr(BinillaWidget, s, tuple(padding[s]))
            except IndexError: pass

        for s in self.widget_depth_names[:len(depths)]:
            try: setattr(BinillaWidget, s + '_depth', depths[s])
            except IndexError: pass

        for i in range(len(colors)):
            try:
                setattr(BinillaWidget, self.color_names[i] + '_color',
                        '#%02x%02x%02x' % tuple(colors[i]))
            except IndexError:
                pass

        for i in range(len(fonts)):
            try:
                font_flags = fonts[i].flags
                self.set_font_config(
                    self.font_names[i],
                    family=fonts[i].family.data, size=fonts[i].size,
                    weight=("bold" if font_flags.bold else "normal"),
                    slant=("italic" if font_flags.italic else "roman"),
                    underline=bool(font_flags.underline),
                    overstrike=bool(font_flags.overstrike),
                    )
            except IndexError:
                pass

        try:
            BinillaWidget.ttk_theme = style_data.appearance.theme_name.data
        except Exception:
            pass

        if self._initialized:
            self.update_config()
            self.apply_style()

    def make_config(self, filepath=None):
        if filepath is None:
            filepath = self.config_path
        filepath = Path(filepath)

        # create the config file from scratch
        self.config_file = self.config_def.build()
        self.config_file.filepath = filepath

        data = self.config_file.data

        # make sure these have as many entries as they're supposed to
        for block in (data.directory_paths, data.appearance.colors,
                      data.appearance.depths):
            block.extend(len(block.NAME_MAP))

        self.curr_hotkeys = dict(default_hotkeys)
        self.curr_tag_window_hotkeys = dict(default_tag_window_hotkeys)

        self.update_config()

        c_hotkeys = data.all_hotkeys.hotkeys
        c_tag_window_hotkeys = data.all_hotkeys.tag_window_hotkeys

        for k_set, b in ((default_hotkeys, c_hotkeys),
                         (default_tag_window_hotkeys, c_tag_window_hotkeys)):
            default_keys = k_set
            hotkeys = b
            for combo, method in k_set.items():
                hotkeys.append()
                keys = hotkeys[-1].combo

                modifier, key = read_hotkey_string(combo)
                keys.modifier.set_to(modifier)
                keys.key.set_to(key)

                hotkeys[-1].method.set_to(method)

    def make_style(self):
        # create the style file from scratch
        filepath = asksaveasfilename(
            initialdir=self.styles_dir, defaultextension='.sty',
            title="Save style as...", parent=self,
            filetypes=(("binilla style", "*.sty"), ('All', '*')))

        if not filepath:
            return

        filepath = Path(filepath)
        self.styles_dir = filepath.parent
        style_file = self.style_def.build()
        style_file.filepath = filepath

        appearance = style_file.data.appearance
        appearance.depths.extend(len(self.widget_depth_names))
        appearance.colors.extend(len(self.color_names))
        appearance.fonts.extend(len(self.font_names))
        appearance.theme_name.data = BinillaWidget.ttk_theme

        self.update_style(style_file)
        style_file.serialize(temp=0, backup=0, calc_pointers=0)

    def reset_style(self):
        '''Resets style to the constants found in editor constants.'''
        answer = messagebox.askyesnocancel("Style reset",
            "You're resetting the style.\nDo you want to use the dark style?")
        if answer is None:
            return
        BinillaWidget.set_style_defaults(dark=answer)
        style_file = self.style_def.build()
        self.update_style(style_file)
        self.load_style(style_file=style_file)


    def toggle_sync(self):
        self.config_file.data.tag_windows.window_flags.sync_window_movement = (
            self.sync_window_movement) = not self.sync_window_movement

    def get_tag(self, filepath, def_id=None):
        '''
        Returns the tag from the handler under the given def_id and filepath.
        filepath is expected to be relative to self.tags_dir
        '''
        if def_id is None:
            def_id = self.handler.get_def_id(filepath)
        try:
            return self.handler.get_tag(filepath, def_id)
        except Exception:
            pass

    def get_tag_window_id_by_tag(self, tag):
        try:
            return self.tag_id_to_window_id.get(id(tag))
        except Exception:
            return None

    def get_tag_window_by_tag(self, tag):
        try:
            return self.tag_windows[self.get_tag_window_id_by_tag(tag)]
        except Exception:
            print(format_exc())
            print("Could not locate tag window for: %s" % tag.filepath)

    def get_is_tag_loaded(self, filepath, def_id=None):
        if def_id is None:
            def_id = self.handler.get_def_id(filepath)
        return bool(self.get_tag(filepath, def_id))

    def load_tags(self, filepaths=None, def_id=None):
        '''Prompts the user for a tag(s) to load and loads it.'''
        if filepaths is None:
            filetypes = [('All', '*')]
            defs = self.handler.defs
            for id in sorted(defs.keys()):
                filetypes.append((id, defs[id].ext))
            filepaths = askopenfilenames(initialdir=str(self.last_load_dir),
                                         filetypes=filetypes, parent=self,
                                         title="Select the tag to load")
            if not filepaths:
                return ()
            elif isinstance(filepaths, str) and filepaths.startswith('{'):
                # account for a stupid bug with certain versions of windows
                filepaths = re.split("\}\W\{", filepaths[1:-1])

        if isinstance(filepaths, (str, PurePath)):
            filepaths = (filepaths, )

        if not filepaths:
            return ()

        filepaths = tuple(Path(fp) for fp in filepaths)
        self.last_load_dir = filepaths[-1].parent
        w = None

        windows = []
        handler = self.handler
        handler_flags = self.config_file.data.tag_windows.file_handling_flags
        tags_dir = handler.tagsdir
        for path in filepaths:
            abs_path = path
            is_new_tag = is_path_empty(abs_path)

            if self.get_is_tag_loaded(path):
                # the tag is somehow still loaded.
                # need to see if there is still a window
                new_tag = self.get_tag(path, handler.get_def_id(path))
                if self.get_tag_window_id_by_tag(new_tag) is not None:
                    w = self.get_tag_window_by_tag(new_tag)
                    if w:
                        print('%s is already loaded' % path)
                        continue

                # there isn't a window, so continue like normal
            else:
                # try to load the new tags
                try:
                    if handler.tagsdir_relative and not is_new_tag:
                        abs_path = tags_dir.joinpath(abs_path)

                    new_tag = handler.build_tag(
                        filepath=abs_path, def_id=def_id,
                        allow_corrupt=handler_flags.allow_corrupt)
                except FileNotFoundError:
                    print("The selected file does not exist.\n"
                          "Could not load: %s" % path)
                    continue
                except PermissionError:
                    print("This program does not have permission to work in this folder.\n"
                          "Could not load: %s" % path)
                    continue
                except Exception:
                    if handler.debug:
                        print(format_exc())
                    print("Could not load: %s" % path)
                    continue

            self.add_tag(new_tag, path)

            try:
                #build the window
                w = self.make_tag_window(new_tag, focus=False,
                                         is_new_tag=is_new_tag)
                windows.append(w)
            except Exception:
                print(format_exc())
                raise IOError("Could not display tag '%s'." % path)

        self.select_tag_window(w)
        return windows

    def load_tag_as(self, e=None):
        '''Prompts the user for a tag to load and loads it.'''
        if self.def_selector_window:
            return

        filetypes = [('All', '*')]
        defs = self.handler.defs
        for def_id in sorted(defs.keys()):
            filetypes.append((def_id, defs[def_id].ext))

        filepath = askopenfilename(
            initialdir=str(self.last_load_dir), filetypes=filetypes,
            parent=self, title="Select the tag to load")

        if not filepath:
            return

        filepath = Path(filepath)
        self.last_load_dir = filepath.parent
        self.def_selector_window = DefSelectorWindow(
            self, title="Select a definition to use", action=lambda def_id:
            self.load_tags(filepaths=filepath, def_id=def_id))
        self.update()
        self.place_window_relative(self.def_selector_window, 30, 50)

    def make_tag_window(self, tag, *, focus=True, window_cls=None,
                        is_new_tag=False):
        '''
        Creates and returns a TagWindow instance for the supplied
        tag and sets the current focus to the new TagWindow.
        '''
        if len(self.tag_windows) == 0:
            self.curr_step_y = self.curr_step_x = 0
        if window_cls is None:
            window_cls = self.def_tag_window_cls
        window = window_cls(
            self, tag, app_root=self, handler=self.handler,
            is_new_tag=is_new_tag, widget_picker=self.widget_picker)
        window.update()  # make sure the window gets a chance to update its size

        # reposition the window
        if self.curr_step_y > self.max_step_y:
            self.curr_step_y = 0
            self.curr_step_x += 1
        if self.curr_step_x > self.max_step_x:
            self.curr_step_x = 0

        try:
            self.place_window_relative(
                window, self.curr_step_x*self.tile_stride_x + 5,
                self.curr_step_y*self.tile_stride_y + 50)

            self.curr_step_y += 1

            self.tag_windows[id(window)] = window
            self.tag_id_to_window_id[id(tag)] = id(window)

            # make sure the window is drawn now that it exists
            window.update_idletasks()

            if focus:
                # set the focus to the new TagWindow
                self.select_tag_window(window)

        except tk.TclError:
            # something happened to the window while trying to position
            # it or select it. not really an issue, so don't report it.
            return

        return window

    def minimize_all(self, e=None):
        '''Minimizes all open TagWindows.'''
        windows = self.tag_windows
        for wid in sorted(windows):
            w = windows[wid]
            try:
                w.withdraw()
            except Exception:
                print(format_exc())

    def new(self, e=None):
        if self.def_selector_window:
            return

        dsw = DefSelectorWindow(
            self, title="Select a definition to use", action=lambda def_id:
            self.load_tags(filepaths='', def_id=def_id))
        self.def_selector_window = dsw
        self.update()
        self.place_window_relative(self.def_selector_window, 30, 50)

    def load(self, e=None):
        self.load_tags()

    def load_as(self, e=None):
        self.load_tag_as()

    def save(self, e=None):
        self.save_tag()

    def save_as(self, e=None):
        self.save_tag_as()

    def print_tag(self, e=None):
        '''Prints the currently selected tag to the console.'''
        try:
            if self.selected_tag is None:
                return

            precision = indent = None
            try:
                show = set()
                app_window = self.config_file.data.app_window
                tag_printing = self.config_file.data.tag_printing
                precision = tag_printing.print_precision
                indent = tag_printing.print_indent

                for name in tag_printing.block_print.NAME_MAP:
                    if tag_printing.block_print.get(name):
                        show.add(name.split('show_')[-1])

                if not app_window.flags.log_tag_print:
                    self.terminal_out.edit_log = False
            except Exception:
                show = s_c.MOST_SHOW

            tag_str = self.selected_tag.pprint(
                show=show, precision=precision, indent=indent)

            try:
                self.terminal_out.edit_log = bool(app_window.flags.log_output)
            except Exception:
                pass

            # print the string line by line
            for line in tag_str.split('\n'):
                try:
                    print(line)
                except Exception:
                    print(' '*(len(line)-len(line.lstrip(' ')))+s_c.UNPRINTABLE)
                self.io_text.update()
        except Exception:
            print(format_exc())

    def restore_all(self, e=None):
        '''Restores all open TagWindows to being visible.'''
        windows = self.tag_windows
        for wid in sorted(windows):
            w = windows[wid]
            try:
                if w.state() == 'withdrawn':
                    w.deiconify()
            except Exception:
                print(format_exc())

    def save_config(self, e=None):
        self.config_file.serialize(temp=False, backup=False)
        if self.config_window:
            self.config_window.update_config_window()

        self.apply_config()

    def save_tag(self, tag=None):
        if tag is None:
            if self.selected_tag is None:
                print("Cannot save(no tag is selected).")
                return
            tag = self.selected_tag

        if tag is self.config_file:
            return self.save_config()

        if hasattr(tag, "serialize"):
            # make sure the tag has a valid filepath whose directories
            # can be made if they dont already exist(dirname must not be '')
            w = self.get_tag_window_by_tag(tag)
            if ((w and w.is_new_tag) or (not(hasattr(tag, "filepath") and
                                             not is_path_empty(tag.filepath) and
                                             not is_path_empty(tag.filepath.parent)))):
                return self.save_tag_as(tag)

            exception = None
            try:
                w.save()
            except Exception as e:
                exception = e
                print(format_exc())

            if exception:
                raise IOError("Could not save tag.")

            self.add_to_recent(tag.filepath)

        return tag

    def save_tag_as(self, tag=None, filepath=None):
        if tag is None:
            if self.selected_tag is None:
                print("Cannot save(no tag is selected).")
                return
            tag = self.selected_tag

        if not hasattr(tag, "serialize"):
            return

        if filepath is None:
            ext = tag.ext
            filepath = asksaveasfilename(
                initialdir=os.path.dirname(tag.filepath), defaultextension=ext,
                title="Save tag as...", filetypes=[
                    (ext[1:], "*" + ext), ('All', '*')])

        filepath = Path(filepath)
        if is_path_empty(filepath):
            return

        # make sure to flush any changes made using widgets to the tag
        w = self.get_tag_window_by_tag(tag)

        try:
            self.last_load_dir = filepath.parent
            if tag.handler.tagsdir_relative:
                filepath = Path(os.path.relpath(str(filepath), str(tag.tags_dir)))

            self.add_tag(tag, filepath)
            w.save(temp=False)
        except PermissionError:
            print("This program does not have permission to save to this folder.\n"
                  "Could not save: %s" % filepath)
            return None
        except Exception:
            print(format_exc())
            raise IOError("Could not save: %s" % filepath)

        try:
            w.update_title()
        except Exception:
            # this isnt really a big deal
            #print(format_exc())
            pass

        return tag

    def save_all(self, e=None):
        '''
        Saves all currently loaded tags to their files.
        '''
        tags = self.handler.tags
        for def_id in tags:
            tag_coll = tags[def_id]
            for tag_path in tag_coll:
                try:
                    self.save_tag(tag_coll[tag_path])
                except Exception:
                    print(format_exc())
                    print("Exception occurred while trying to save '%s'" %
                          tag_path)

    def select_tag_window(self, window=None):
        try:
            if window is None:
                self.selected_tag = None
                self.focus_set()
                return

            if window.tag is not None:
                tag = window.tag
                # if the window IS selected, minimize it
                if self.selected_tag is tag:
                    self.selected_tag = None
                    return

                self.selected_tag = window.tag
                if window.state() == 'withdrawn':
                    window.deiconify()

                # focus_set wasnt working, so i had to play hard ball
                window.focus_force()
        except Exception:
            print(format_exc())

    def select_tag_window_by_tag(self, tag=None):
        if tag is None:
            return
        try:
            self.select_tag_window(self.get_tag_window_by_tag(tag))
        except Exception:
            print(format_exc())

    def select_defs(self):
        '''Prompts the user to specify where to load the tag defs from.
        Reloads the tag definitions from the folder specified.'''
        defs_dir = askdirectory(initialdir=self.last_defs_dir, parent=self,
                                title="Select the tag definitions folder")
        if defs_dir == "":
            return

        print('Loading selected definitions...')
        defs_dir = Path(defs_dir)
        self.update_idletasks()

        # try and find the module_root
        mod_root = defs_dir
        while mod_root.parent.joinpath("__init__.py").is_file():
            mod_root = mod_root.parent

        mod_root = mod_root.parent

        # if the module_root isnt in sys.path, we need to add it so
        # the importer can resolve the import path for the definitions
        if str(mod_root) not in sys.path:
            sys.path.insert(0, str(mod_root))

        mod_relpath = Path(str(defs_dir).split(str(mod_root))[-1])
        import_path = ".".join(piece for piece in mod_relpath.parts[1:-1])
        import_path = ".".join((import_path, mod_relpath.parts[-1])).lstrip(".")
        print("    Module path:  %s\n    Import path:  %s" % (
            mod_root, import_path))
        try:
            self.handler.reload_defs(defs_path=import_path)
            self.last_defs_dir = defs_dir
            print('Selected definitions loaded\n')
        except Exception:
            raise IOError("Could not load tag definitions\n.")

    def show_config_file(self, e=None):
        if self.config_window is not None:
            return

        # update the config file's directory paths
        dir_paths = self.config_file.data.directory_paths
        for s in ('last_load_dir', 'last_defs_dir', 'last_imp_dir',
                  'curr_dir', 'styles_dir', ):
            try: dir_paths[s].path = str(getattr(self, s))
            except IndexError: pass

        self.config_window = self.make_tag_window(
            self.config_file, window_cls=self.config_window_class)

    def show_defs(self, e=None):
        if self.def_selector_window:
            return

        self.def_selector_window = DefSelectorWindow(self, action=lambda x: x)
        self.place_window_relative(self.def_selector_window, 30, 50)

    def show_window_manager(self, e=None):
        if self.tag_window_manager is not None:
            return

        self.tag_window_manager = TagWindowManager(self)
        self.place_window_relative(self.tag_window_manager, 30, 50)

    def sync_tag_window_pos(self, e):
        '''Syncs TagWindows to move with the app.'''
        if not(self._window_geometry_initialized and self._initialized):
            return

        dx = int(self.winfo_x()) - self.sync_offset_x
        dy = int(self.winfo_y()) - self.sync_offset_y

        self.sync_offset_x = self.winfo_x()
        self.sync_offset_y = self.winfo_y()

        if not self.sync_window_movement:
            return

        for w in self.tag_windows.values():
            # use geometry method to get accurate location, even on linux
            x_base, y_base = w.geometry().split('+')[1:]
            w.geometry('%sx%s+%s+%s' %
                       (w.winfo_width(), w.winfo_height(),
                        dx + int(x_base), dy + int(y_base)))

    def tile_vertical(self, e=None):
        windows = self.tag_windows

        # reset the offsets to 0 and get the strides
        self.curr_step_y = 0
        self.curr_step_x = 0
        x_stride = self.tile_stride_x
        y_stride = self.tile_stride_y

        # reposition the window
        for wid in sorted(windows):
            window = windows[wid]

            # dont tile hidden windows
            if window.state() == 'withdrawn':
                continue

            if self.curr_step_y > self.max_step_y:
                self.curr_step_y = 0
                self.curr_step_x += 1
            if self.curr_step_x > self.max_step_x:
                self.curr_step_x = 0

            self.place_window_relative(window,
                                       self.curr_step_x*x_stride + 5,
                                       self.curr_step_y*y_stride + 50)
            self.curr_step_y += 1
            window.update_idletasks()

            self.selected_tag = None
            self.select_tag_window(window)

    def tile_horizontal(self, e=None):
        windows = self.tag_windows

        # reset the offsets to 0 and get the strides
        self.curr_step_y = 0
        self.curr_step_x = 0
        x_stride = self.tile_stride_x
        y_stride = self.tile_stride_y

        # reposition the window
        for wid in sorted(windows):
            window = windows[wid]

            # dont tile hidden windows
            if window.state() == 'withdrawn':
                continue

            if self.curr_step_x > self.max_step_x:
                self.curr_step_x = 0
                self.curr_step_y += 1
            if self.curr_step_y > self.max_step_y:
                self.curr_step_y = 0

            self.place_window_relative(window,
                                       self.curr_step_x*x_stride + 5,
                                       self.curr_step_y*y_stride + 50)
            self.curr_step_x += 1
            window.update_idletasks()

            self.selected_tag = None
            self.select_tag_window(window)

    def unbind_hotkeys(self, hotkeys=None):
        if hotkeys is None:
            hotkeys = self.curr_hotkeys
        if isinstance(hotkeys, dict):
            hotkeys = hotkeys.keys()

        for hotkey in tuple(hotkeys):
            try:
                if e_c.IS_LNX and "MouseWheel" in hotkey:
                    self.unbind_all(hotkey.replace("MouseWheel", "4"))
                    self.unbind_all(hotkey.replace("MouseWheel", "5"))
                else:
                    self.unbind_all(hotkey)
            except Exception:
                pass

    def update_config(self, config_file=None):
        if config_file is None:
            config_file = self.config_file

        config_data = config_file.data
        config_data.version_info.version = self.config_version

        open_tags = config_data.open_tags
        recent_tags = config_data.recent_tags
        dir_paths = config_data.directory_paths
        app_window = config_data.app_window
        tag_windows = config_data.tag_windows

        tag_windows.window_flags.sync_window_movement = self.sync_window_movement

        del recent_tags[:]

        if self._window_geometry_initialized:
            w, geom = self.geometry().split("x")
            h, x, y = geom.split("+")
            self.app_width = int(w)
            self.app_height = int(h)
            self.app_offset_x = int(x)
            self.app_offset_y = int(y)

        if self._initialized:
            try:
                for s in app_window.NAME_MAP.keys():
                    if hasattr(self, s):
                        app_window[s] = getattr(self, s)

                app_window.max_step[:] = (self.max_step_x, self.max_step_y)
                app_window.tile_stride[:] = (self.tile_stride_x, self.tile_stride_y)

                tag_windows.default_dimensions[:] = (self.default_tag_window_width,
                                                     self.default_tag_window_height)
                tag_windows.scroll_increment[:] = (self.scroll_increment_x,
                                                   self.scroll_increment_y)
            except Exception:
                print(format_exc())

        # make sure there are enough tagsdir entries in the directory_paths
        if len(dir_paths.NAME_MAP) > len(dir_paths):
            dir_paths.extend(len(dir_paths.NAME_MAP) - len(dir_paths))

        for path in self.recent_tagpaths:
            recent_tags.append()
            recent_tags[-1].path = str(path)

        app_window.recent_tag_max = self.recent_tag_max
        tag_windows.max_undos = self.max_undos

        for s in ('last_load_dir', 'last_defs_dir', 'last_imp_dir',
                  'curr_dir', 'styles_dir', ):
            try: dir_paths[s].path = str(getattr(self, s))
            except IndexError: pass

        dir_paths.tags_dir.path = str(self.handler.tagsdir)
        dir_paths.debug_log_path.path = str(self.log_filename)

        self.update_style(config_file)

    def update_style(self, style_file):
        style_data = style_file.data
        style_data.version_info.parse(attr_index='date_modified')

        w_and_h = style_data.appearance.widths_and_heights
        padding = style_data.appearance.padding
        depths = style_data.appearance.depths
        colors = style_data.appearance.colors
        fonts = style_data.appearance.fonts

        try:
            w_and_h.title_width = BinillaWidget.title_width
            w_and_h.scroll_menu_width = BinillaWidget.scroll_menu_width
            w_and_h.enum_menu_width = BinillaWidget.enum_menu_width
            w_and_h.min_entry_width = BinillaWidget.min_entry_width

            w_and_h.textbox[:] = (BinillaWidget.textbox_width,
                                  BinillaWidget.textbox_height)
            w_and_h.scroll_menu[:] = (BinillaWidget.scroll_menu_max_width,
                                      BinillaWidget.scroll_menu_max_height)
            w_and_h.bool_frame_width[:] = (BinillaWidget.bool_frame_min_width,
                                           BinillaWidget.bool_frame_max_width)
            w_and_h.bool_frame_height[:] = (BinillaWidget.bool_frame_min_height,
                                            BinillaWidget.bool_frame_max_height)
            w_and_h.default_entry_widths[:] = (BinillaWidget.def_int_entry_width,
                                               BinillaWidget.def_float_entry_width,
                                               BinillaWidget.def_string_entry_width)
            w_and_h.max_entry_widths[:] = (BinillaWidget.max_int_entry_width,
                                           BinillaWidget.max_float_entry_width,
                                           BinillaWidget.max_string_entry_width)
        except Exception:
            print(format_exc())

        for s in ('vertical_padx', 'vertical_pady',
                  'horizontal_padx', 'horizontal_pady'):
            try: padding[s][:] = tuple(getattr(BinillaWidget, s))
            except IndexError: pass

        for s in self.widget_depth_names:
            try: depths[s] = getattr(BinillaWidget, s + '_depth')
            except IndexError: pass

        for i in range(len(self.color_names)):
            try:
                color_block = colors[i]
            except IndexError:
                colors.append()
                try:
                    color_block = colors[i]
                except IndexError:
                    continue

            try:
                color = getattr(BinillaWidget, self.color_names[i] + '_color')[1:]
                color_block[0] = int(color[0:2], 16)
                color_block[1] = int(color[2:4], 16)
                color_block[2] = int(color[4:6], 16)
            except IndexError:
                pass

        for i in range(len(self.font_names)):
            try:
                font_block = fonts[i]
            except IndexError:
                fonts.append()
                try:
                    font_block = fonts[i]
                except IndexError:
                    continue

            try:
                font_cfg = self.get_font_config(self.font_names[i])
                font_block.family.data = font_cfg.family
                font_block.size = font_cfg.size

                font_flags = font_block.flags
                font_flags.bold = font_cfg.weight.lower() == "bold"
                font_flags.italic = font_cfg.slant.lower() == "italic"
                font_flags.underline = font_cfg.underline
                font_flags.overstrike = font_cfg.overstrike
            except IndexError:
                pass

        try:
            style_data.appearance.theme_name.data = BinillaWidget.ttk_theme
        except Exception:
            pass

    def enter_style_change(self):
        # force all tag windows to unpack their root frame to make updating fast
        try:
            for w in self.tag_windows.values():
                w.enter_style_change()
        except Exception:
            pass

    def exit_style_change(self):
        try:
            for w in self.tag_windows.values():
                w.exit_style_change()
        except Exception:
            pass

    def apply_style(self, seen=None):
        with self.style_change_lock as lock_depth:
            self.update_ttk_style()
            BinillaWidget.apply_style(self, seen)
            self.io_text.config(fg=self.io_fg_color, bg=self.io_bg_color)
            if not self._window_geometry_initialized:
                self._window_geometry_initialized = True
                self.update()
                if self.app_offset_x not in range(0, self.winfo_screenwidth()):
                    self.app_offset_x = 0

                if self.app_offset_y not in range(0, self.winfo_screenheight()):
                    self.app_offset_y = 0

                self.geometry("%sx%s+%s+%s" %
                              (self.app_width, self.app_height,
                               self.app_offset_x, self.app_offset_y))

    def show_about_window(self):
        w = getattr(self, "about_window", None)
        if w is not None:
            try: w.destroy()
            except Exception: pass
            self.about_window = None

        self.about_window = AboutWindow(
            self, module_names=self.about_module_names,
            iconbitmap=self.icon_filepath, appbitmap=self.app_bitmap_filepath,
            app_name=self.app_name, messages=self.about_messages)
        self.place_window_relative(self.about_window, 30, 50)

    def open_issue_tracker(self):
        webbrowser.open_new_tab(self.issue_tracker_url)

    def upgrade_config_version(self, filepath):
        old_version = self.config_version_def.build(filepath=str(filepath)).data.version
        if old_version == 1:
            new_config = binilla.defs.upgrade_config.upgrade_v1_to_v2(
                self.config_defs[1].build(filepath=str(filepath)),
                self.config_defs[2].build())
        else:
            raise ValueError("Config header version is not valid")

        return new_config

    def upgrade_style_version(self, filepath):
        old_version = self.style_version_def.build(filepath=str(filepath)).data.version
        if old_version == 1:
            new_style = binilla.defs.upgrade_style.upgrade_v1_to_v2(
                self.style_defs[1].build(filepath=str(filepath)),
                self.style_defs[2].build())
        else:
            raise ValueError("Style header version is not valid")

        return new_style
