import gc
import os
import random
import tempfile
import weakref
from traceback import format_exc

import threadsafe_tkinter as tk
import tkinter.ttk as ttk

from binilla import editor_constants as e_c
from binilla.widgets.binilla_widget import BinillaWidget
from binilla.widgets.scroll_menu import ScrollMenu
from binilla.widgets import get_mouse_delta
from binilla.windows.filedialog import asksaveasfilename


__all__ = ("PhotoImageHandler", "BitmapDisplayFrame", "BitmapDisplayButton")


def import_arbytmap(force=False):
    # dont import it if an import was already attempted
    if "arbytmap" not in globals() or force:
        try:
            global arbytmap
            import arbytmap
        except ImportError:
            arbytmap = None

    return bool(arbytmap)


class PhotoImageHandler():
    # this class utilizes the arbytmap module, but will only
    # import it once an instance of this class is created
    temp_path = ""
    arby = None
    _images = None  # loaded and cached PhotoImages
    channels = ()
    channel_mapping = None

    def __init__(self, tex_block=None, tex_info=None, temp_path=""):
        if not import_arbytmap():
            raise ValueError(
                "Arbytmap is not loaded. Cannot generate PhotoImages.")
        self.arby = arbytmap.Arbytmap()
        self._images = {}
        self.channels = dict(A=False, L=True, R=True, G=True, B=True)
        self.temp_path = temp_path

        if tex_block and tex_info:
            self.load_texture(tex_block, tex_info)

    def load_texture(self, tex_block, tex_info):
        self.arby.load_new_texture(texture_block=tex_block,
                                   texture_info=tex_info)

    def set_channel_mode(self, mode=-1):
        # 0 = RGB or L, 1 = A, 2 = ARGB or AL, 3 = R, 4 = G, 5 = B
        if mode not in range(-1, 6):
            return

        channels = self.channels
        channels.update(L=False, R=False, G=False, B=False, A=False)
        if self.channel_count <= 2:
            channels.update(L=(mode != 1), A=(mode != 0))
        else:
            if   mode == 0: channels.update(R=True, G=True, B=True)
            elif mode == 1: channels.update(A=True)
            elif mode == 2: channels.update(A=True, R=True, G=True, B=True)
            elif mode == 3: channels.update(R=True)
            elif mode == 4: channels.update(G=True)
            elif mode == 5: channels.update(B=True)

        if self.channel_count == 1:
            chan_map = [-1]
            if "A" not in self.tex_format:
                if channels["L"]:
                    chan_map = [-1, 0, 0, 0]
            elif channels["A"]:
                if channels["L"]:
                    chan_map = [0, -1, -1, -1]
                else:
                    chan_map = [-1, 0, 0, 0]
        elif self.channel_count == 2:
            chan_map = [0, 1, 1, 1]
            if channels["L"] and channels["A"]: pass
            elif not channels["A"]: chan_map = [-1, 1, 1, 1]
            elif not channels["L"]: chan_map = [-1, 0, 0, 0]
        else:
            chan_map = [0, 1, 2, 3]
            if not channels["A"]: chan_map[0] = -1
            if not channels["R"]: chan_map[1] = -1
            if not channels["G"]: chan_map[2] = -1
            if not channels["B"]: chan_map[3] = -1
            if min(chan_map[1:]) < 0:
                chan_map[1] = chan_map[2] = chan_map[3] = max(chan_map[1:])

            if max(chan_map[1:]) < 0:
                chan_map = [-1, 0, 0, 0]

        self.channel_mapping = chan_map

    def load_images(self, mip_levels="all", sub_bitmap_indexes="all"):
        if not self.temp_path:
            raise ValueError("Cannot create PhotoImages without a specified "
                             "temporary filepath to save their PNG's to.")

        if not sub_bitmap_indexes and not mip_levels:
            return {}

        if sub_bitmap_indexes == "all":
            sub_bitmap_indexes = range(self.max_sub_bitmap + 1)
        elif isinstance(sub_bitmap_indexes, int):
            sub_bitmap_indexes = (sub_bitmap_indexes, )

        if mip_levels == "all":
            mip_levels = range(self.max_mipmap + 1)
        elif isinstance(mip_levels, int):
            mip_levels = (mip_levels, )

        new_images = {}
        try:
            image_list = self.arby.make_photoimages(
                self.temp_path, bitmap_indexes=sub_bitmap_indexes,
                keep_alpha=self.channels.get("A"), mip_levels="all",
                channel_mapping=self.channel_mapping, intensity_to_rgb=True,
                swizzle_mode=False, tile_mode=False)
        except TypeError:
            print(format_exc())
            print("Could not load texture.")
            # no texture loaded(probably)
            return {}
        except Exception:
            print(format_exc())
            return {}

        c = frozenset((k, v) for k, v in self.channels.items())
        mip_ct        = self.max_mipmap + 1
        sub_bitmap_ct = self.max_sub_bitmap + 1
        for i in range(mip_ct):
            for j in range(sub_bitmap_ct):
                b = sub_bitmap_indexes[j]
                self._images[(b, i, c)] = image_list[i*sub_bitmap_ct + j]

        for i in range(len(mip_levels)):
            for j in range(sub_bitmap_ct):
                key = (sub_bitmap_indexes[j], mip_levels[i], c)
                new_images[key] = self._images[key]

        return new_images

    def get_images(self, mip_levels="all", sub_bitmap_indexes="all"):
        if sub_bitmap_indexes == "all":
            sub_bitmap_indexes = range(self.max_sub_bitmap + 1)
        elif isinstance(sub_bitmap_indexes, int):
            sub_bitmap_indexes = (sub_bitmap_indexes, )

        if mip_levels == "all":
            mip_levels = range(self.max_mipmap + 1)
        elif isinstance(mip_levels, int):
            mip_levels = (mip_levels, )

        sub_bitmap_indexes = list(sub_bitmap_indexes)
        mip_levels         = list(mip_levels)
        req_images         = {}

        c = frozenset((k, v) for k, v in self.channels.items())
        for i in range(len(sub_bitmap_indexes) - 1, -1, -len(mip_levels)):
            b = sub_bitmap_indexes[i]
            exists = 0
            for m in mip_levels:
                image = self._images.get((b, m, c))
                req_images[(b, m, c)] = image
                exists += image is not None

            if exists == len(mip_levels):
                sub_bitmap_indexes.pop(i)

        if sub_bitmap_indexes:
            for k, v in self.load_images(
                    mip_levels, sub_bitmap_indexes).items():
                req_images[k] = v

        return req_images

    @property
    def tex_type(self): return self.arby.texture_type
    @property
    def tex_format(self): return self.arby.format
    @property
    def max_sub_bitmap(self): return self.arby.sub_bitmap_count - 1
    @property
    def max_mipmap(self): return self.arby.mipmap_count
    @property
    def channel_count(self):
        fmt = self.arby.format
        if fmt in arbytmap.THREE_CHANNEL_FORMATS:
            return 3
        return arbytmap.CHANNEL_COUNTS[fmt]

    def mip_width(self, mip_level):
        return max(self.arby.width // (1<<mip_level), 1)

    def mip_height(self, mip_level):
        return max(self.arby.height // (1<<mip_level), 1)

    def mip_depth(self, mip_level):
        return max(self.arby.depth // (1<<mip_level), 1)


class BitmapDisplayFrame(BinillaWidget, tk.Frame):
    app_root = None
    root_frame_id = None

    bitmap_index  = None  # index of the bitmap being displayed
    mipmap_index  = None  # the mip level to display of that bitmap
    channel_index = None  # how to display the bitmap:
    #                       0=RGB or L, 1=A, 2=ARGB or AL, 3=R, 4=G, 5=B
    depth_index   = None  # since 3d bitmaps must be viewed in 2d slices,
    #                       this is the depth of the slice to display.
    cube_display_index = None  # mode to display the cubemap in:
    #                            0 == horizontal, 1 == vertical,
    #                            2 == linear strip

    prev_bitmap_index = None
    prev_mipmap_index = None
    prev_channel_index = None
    prev_depth_index = None
    prev_cube_display_index = None
    changing_settings = False

    curr_depth = 0
    depth_canvas = None
    depth_canvas_id = None
    depth_canvas_image_id = None

    default_bitmap_mapping = (
        (0,),
        )

    cubemap_cross_mapping = (
        (-1,  2),
        ( 1,  4,  0,  5),
        (-1,  3),
        )

    cubemap_strip_mapping = (
        (0, 1, 2, 3, 4, 5),
        )

    _image_handlers = None
    image_canvas_ids = ()  # does NOT include the depth_canvas_id
    textures = ()  # List of textures ready to be loaded into arbytmap.
    # Structure is as follows:  [ (tex_block0, tex_info0),
    #                             (tex_block1, tex_info1),
    #                             (tex_block2, tex_info2), ... ]

    temp_root = os.path.join(tempfile.gettempdir(), "arbytmaps")
    temp_dir = ''

    def __init__(self, master, *args, **kwargs):
        BinillaWidget.__init__(self)
        self.temp_root = kwargs.pop('temp_root', self.temp_root)
        textures = kwargs.pop('textures', ())
        app_root = kwargs.pop('app_root', ())

        self.image_canvas_ids = []
        self.textures = []
        self._image_handlers = {}

        temp_name = str(int(random.random() * (1<<32)))
        self.temp_dir = os.path.join(self.temp_root, temp_name)

        kwargs.update(relief='flat', bd=self.frame_depth,
                      bg=self.default_bg_color)
        tk.Frame.__init__(self, master, *args, **kwargs)

        self.bitmap_index  = tk.IntVar(self)
        self.mipmap_index  = tk.IntVar(self)
        self.depth_index   = tk.IntVar(self)
        self.channel_index = tk.IntVar(self)
        self.cube_display_index = tk.IntVar(self)
        self.root_canvas = tk.Canvas(self, highlightthickness=0)
        self.root_frame = tk.Frame(self.root_canvas, highlightthickness=0)

        # create the root_canvas and the root_frame within the canvas
        self.controls_frame0 = tk.Frame(self.root_frame, highlightthickness=0)
        self.controls_frame1 = tk.Frame(self.root_frame, highlightthickness=0)
        self.controls_frame2 = tk.Frame(self.root_frame, highlightthickness=0)
        self.image_root_frame = tk.Frame(self.root_frame, highlightthickness=0)
        self.image_canvas = tk.Canvas(self.image_root_frame,
                                      highlightthickness=0,
                                      bg=self.bitmap_canvas_bg_color)
        self.depth_canvas = tk.Canvas(self.image_canvas, highlightthickness=0,
                                      bg=self.bitmap_canvas_bg_color)

        self.bitmap_menu  = ScrollMenu(self.controls_frame0, menu_width=7,
                                       variable=self.bitmap_index, can_scroll=True)
        self.mipmap_menu  = ScrollMenu(self.controls_frame1, menu_width=7,
                                       variable=self.mipmap_index, can_scroll=True)
        self.depth_menu   = ScrollMenu(self.controls_frame2, menu_width=7,
                                       variable=self.depth_index, can_scroll=True)
        self.channel_menu = ScrollMenu(self.controls_frame0, menu_width=9,
                                       variable=self.channel_index, can_scroll=True)
        self.cube_display_menu = ScrollMenu(self.controls_frame1, menu_width=9,
                                            variable=self.cube_display_index,
                                            options=("cross", "linear"), can_scroll=True)

        self.save_button = ttk.Button(self.controls_frame2, width=11,
                                     text="Browse", command=self.save_as)
        self.depth_menu.default_text = self.mipmap_menu.default_text =\
                                       self.bitmap_menu.default_text =\
                                       self.channel_menu.default_text =\
                                       self.cube_display_menu.default_text = ""

        labels = []
        labels.append(tk.Label(self.controls_frame0, text="Bitmap index"))
        labels.append(tk.Label(self.controls_frame1, text="Mipmap level"))
        labels.append(tk.Label(self.controls_frame2, text="Depth level"))
        labels.append(tk.Label(self.controls_frame0, text="Channels"))
        labels.append(tk.Label(self.controls_frame1, text="Cubemap display"))
        labels.append(tk.Label(self.controls_frame2, text="Save to file"))
        for lbl in labels:
            lbl.config(width=15, anchor='w',
                       bg=self.default_bg_color, fg=self.text_normal_color,
                       disabledforeground=self.text_disabled_color)

        self.hsb = tk.Scrollbar(self, orient="horizontal",
                                command=self.root_canvas.xview)
        self.vsb = tk.Scrollbar(self, orient="vertical",
                                command=self.root_canvas.yview)
        self.root_canvas.config(xscrollcommand=self.hsb.set, xscrollincrement=1,
                                yscrollcommand=self.vsb.set, yscrollincrement=1)
        for w in [self.root_frame, self.root_canvas, self.image_canvas,
                  self.controls_frame0, self.controls_frame1,
                  self.controls_frame2] + labels:
            if e_c.IS_LNX:
                w.bind('<Shift-4>', self.mousewheel_scroll_x)
                w.bind('<Shift-5>', self.mousewheel_scroll_x)
                w.bind('<4>',       self.mousewheel_scroll_y)
                w.bind('<5>',       self.mousewheel_scroll_y)
            else:
                w.bind('<Shift-MouseWheel>', self.mousewheel_scroll_x)
                w.bind('<MouseWheel>',       self.mousewheel_scroll_y)

        # pack everything
        # pack in this order so scrollbars aren't shrunk
        self.root_frame_id = self.root_canvas.create_window(
            (0, 0), anchor="nw", window=self.root_frame)
        self.hsb.pack(side='bottom', fill='x', anchor='nw')
        self.vsb.pack(side='right', fill='y', anchor='nw')
        self.root_canvas.pack(fill='both', anchor='nw', expand=True)
        self.controls_frame0.pack(side='top', fill='x', anchor='nw')
        self.controls_frame1.pack(side='top', fill='x', anchor='nw')
        self.controls_frame2.pack(side='top', fill='x', anchor='nw')
        self.image_root_frame.pack(fill='both', anchor='nw', expand=True)
        self.image_canvas.pack(fill='both', side='right',
                               anchor='nw', expand=True)

        padx = self.horizontal_padx
        pady = self.horizontal_pady
        for lbl in labels[:3]:
            lbl.pack(side='left', padx=(25, 0), pady=pady)
        self.bitmap_menu.pack(side='left', padx=padx, pady=pady)
        self.mipmap_menu.pack(side='left', padx=padx, pady=pady)
        self.depth_menu.pack(side='left', padx=padx, pady=pady)
        for lbl in labels[3:]:
            lbl.pack(side='left', padx=(15, 0), pady=pady)
        self.save_button.pack(side='left', padx=padx, pady=pady)
        self.channel_menu.pack(side='left', padx=padx, pady=pady)
        self.cube_display_menu.pack(side='left', padx=padx, pady=pady)

        self.change_textures(textures)

        self.write_trace(self.bitmap_index, self.settings_changed)
        self.write_trace(self.mipmap_index, self.settings_changed)
        self.write_trace(self.depth_index, self.settings_changed)
        self.write_trace(self.cube_display_index, self.settings_changed)
        self.write_trace(self.channel_index, self.settings_changed)

        self.apply_style()

    def destroy(self):
        try:
            self.clear_canvas()
            self.clear_depth_canvas()
        except Exception:
            pass
        try: del self.textures[:]
        except Exception: pass
        try: del self._image_handlers[:]
        except Exception: pass
        self.image_canvas_ids = self._image_handlers = None
        self.textures = None
        tk.Frame.destroy(self)
        self.delete_all_traces()
        self.delete_all_widget_refs()
        gc.collect()

    @property
    def active_image_handler(self):
        b = self.bitmap_index.get()
        if b not in range(len(self.textures)) or not import_arbytmap():
            return None
        elif b not in self._image_handlers:
            # make a new PhotoImageHandler if one doesnt exist already
            self._image_handlers[b] = PhotoImageHandler(
                self.textures[b][0], self.textures[b][1], self.temp_dir)

        return self._image_handlers[b]

    @property
    def should_update(self):
        return (self.prev_bitmap_index  != self.bitmap_index.get() or
                self.prev_mipmap_index  != self.mipmap_index.get() or
                self.prev_channel_index != self.channel_index.get())

    def mousewheel_scroll_x(self, e):
        # prevent scrolling if the root_canvas.bbox width >= canvas width
        bbox = self.root_canvas.bbox(tk.ALL)
        if not bbox or (self.root_canvas.winfo_width() >= bbox[2] - bbox[0]):
            return

        delta = getattr(self.app_root, "scroll_increment_x", 20)
        self.root_canvas.xview_scroll(int(get_mouse_delta(e) * delta), "units")

    def mousewheel_scroll_y(self, e):
        # prevent scrolling if the root_canvas.bbox height >= canvas height
        bbox = self.root_canvas.bbox(tk.ALL)
        if not bbox or (self.root_canvas.winfo_height() >= bbox[3] - bbox[1]):
            return

        delta = getattr(self.app_root, "scroll_increment_y", 20)
        self.root_canvas.yview_scroll(int(get_mouse_delta(e) * delta), "units")

    def update_scroll_regions(self):
        if not self.image_canvas_ids and not self.depth_canvas_id:
            return
        rf = self.root_frame
        region = self.image_canvas.bbox(tk.ALL)
        # bbox region isn't actually x, y, w, h, but if the
        # origin is at (0,0) we can treat it like that
        if region is None:
            x, y, w, h = (0,0,0,0)
        else:
            x, y, w, h = region

        self.image_canvas.config(scrollregion=(x, y, w, h))
        rf.update_idletasks()
        max_w = w
        total_h = h
        for widget in self.root_frame.children.values():
            if widget is not self.image_root_frame:
                max_w = max(widget.winfo_reqwidth(), max_w)
                total_h += widget.winfo_reqheight()

        self.root_canvas.itemconfigure(self.root_frame_id,
                                       width=max_w, height=total_h)
        self.root_canvas.config(scrollregion=(0, 0, max_w, total_h))

    def save_as(self, e=None, initial_dir=None):
        handler = self.active_image_handler
        if handler is None:
            return None
        fp = asksaveasfilename(
            initialdir=initial_dir, defaultextension='.dds',
            title="Save bitmap as...", parent=self,
            filetypes=(("DirectDraw surface",          "*.dds"),
                       ('Portable network graphics',   '*.png'),
                       ('Truevision graphics adapter', '*.tga'),
                       ('Raw pixel data',              '*.bin'))
            )

        fp, ext = os.path.splitext(fp)
        if not fp:
            return
        elif not ext:
            ext = ".dds"

        mip_levels = "all" if ext.lower() == ".dds" else self.mipmap_index.get()

        handler.arby.save_to_file(
            output_path=fp, ext=ext, overwrite=True, mip_levels=mip_levels,
            bitmap_indexes="all", keep_alpha=handler.channels.get("A"),
            swizzle_mode=False, channel_mapping=handler.channel_mapping,
            target_big_endian=False, tile_mode=False
            )

    def clear_depth_canvas(self):
        self.depth_canvas.delete(tk.ALL)
        self.prev_depth_index = None
        self.prev_cube_display_index = None
        self.depth_canvas_image_id = None

    def clear_canvas(self):
        self.image_canvas.delete(tk.ALL)
        self.clear_depth_canvas()
        self.depth_canvas_id = None
        self.image_canvas_ids = []

    def hide_depth_canvas(self):
        if self.depth_canvas_id is not None:
            self.image_canvas.delete(self.depth_canvas_id)
            self.depth_canvas_id = None

    def show_depth_canvas(self):
        self.depth_canvas_id = self.image_canvas.create_window(
            (0, 0), anchor="nw", window=self.depth_canvas)

    def change_textures(self, textures):
        assert hasattr(textures, '__iter__')

        for tex in textures:
            assert len(tex) == 2
            assert isinstance(tex[1], dict)

        if self._image_handlers: del self._image_handlers
        if self.textures:        del self.textures[:]

        self.textures = list(textures)

        self._image_handlers = {}
        self.bitmap_index.set(0)
        self.mipmap_index.set(0)
        self.channel_index.set(0)
        self.depth_index.set(0)
        self.cube_display_index.set(0)

        self.bitmap_menu.set_options(range(len(textures)))

        self.prev_bitmap_index       = None
        self.prev_mipmap_index       = None
        self.prev_channel_index      = None
        self.prev_depth_index        = None
        self.prev_cube_display_index = None
        self.update_bitmap(force=True)

    def get_images(self):
        image_handler = self.active_image_handler
        if not image_handler: return
        images = image_handler.get_images(mip_levels=self.mipmap_index.get())
        return tuple(images[i] for i in sorted(images.keys()))

    def settings_changed(self, *args, force=False):
        handler = self.active_image_handler
        force = False
        if not handler:
            return
        elif self.changing_settings:
            return
        elif self.prev_bitmap_index != self.bitmap_index.get():
            force = True
        elif self.prev_mipmap_index != self.mipmap_index.get():
            force = True
        elif self.prev_channel_index != self.channel_index.get():
            force = True
        elif self.prev_depth_index != self.depth_index.get():
            pass
        elif self.prev_cube_display_index != self.cube_display_index.get():
            force = True
        else:
            return
        self.changing_settings = True

        new_mip_options = range(handler.max_mipmap + 1)
        if self.mipmap_index.get() not in new_mip_options:
            self.mipmap_index.set(0)

        max_depth = handler.mip_depth(self.mipmap_index.get())
        self.mipmap_menu.set_options(new_mip_options)
        self.depth_menu.set_options(range(max_depth))
        if self.depth_menu.sel_index > max_depth - 1:
            self.depth_menu.sel_index = max_depth - 1

        channel_count = handler.channel_count
        if channel_count <= 2:
            opts = ("Luminance", "Alpha", "AL")
        else:
            opts = ("RGB", "Alpha", "ARGB", "Red", "Green", "Blue")
        self.channel_menu.set_options(opts)

        try:
            handler.set_channel_mode(self.channel_index.get())
            self.update_bitmap(force=force)
            self.changing_settings = False
        except Exception:
            self.changing_settings = False
            raise

    def update_bitmap(self, *args, force=False):
        handler = self.active_image_handler
        if handler is None:
            return None

        tex_type = handler.tex_type
        if   tex_type == "2D":   self._display_2d_bitmap(force)
        elif tex_type == "3D":   self._display_3d_bitmap(force)
        elif tex_type == "CUBE": self._display_cubemap(force)

        self.prev_bitmap_index  = self.bitmap_index.get()
        self.prev_mipmap_index  = self.mipmap_index.get()
        self.prev_channel_index = self.channel_index.get()
        self.prev_depth_index   = self.depth_index.get()
        self.prev_cube_display_index = self.cube_display_index.get()

    def _display_cubemap(self, force=False, bitmap_mapping=None):
        mapping_type = self.cube_display_index.get()
        if bitmap_mapping is None:
            if mapping_type == 0:
                bitmap_mapping = self.cubemap_cross_mapping
            else:
                bitmap_mapping = self.cubemap_strip_mapping

        self._display_2d_bitmap(force, bitmap_mapping)

    def _display_2d_bitmap(self, force=False, bitmap_mapping=None):
        images = self.get_images()
        if not images or not(self.should_update or force): return
        w = max(image.width()  for image in images)
        h = max(image.height() for image in images)
        if bitmap_mapping is None:
            bitmap_mapping = self.default_bitmap_mapping

        self.clear_canvas()
        # place the bitmaps on the canvas
        y = 0
        for line in bitmap_mapping:
            max_column_ct = max(0, len(line))
            x = 0
            for image_index in line:
                if image_index in range(len(images)):
                    # place the cube face on the canvas
                    self.image_canvas_ids.append(
                        self.image_canvas.create_image(
                            (x, y), anchor="nw", image=images[image_index],
                            tags=("BITMAP", "2D_BITMAP")))
                x += w
            y += h
        self.update_scroll_regions()

    def _display_3d_bitmap(self, force=False):
        if self.should_update or self.depth_canvas_image_id is None or force:
            self.clear_canvas()
            self.show_depth_canvas()
            handler = self.active_image_handler
            images  = self.get_images()
            if not(images and handler): return
            m = self.mipmap_index.get()
            w, h = images[0].width(), handler.mip_height(m)
            self.curr_depth = handler.mip_depth(m)

            # place the bitmap on the canvas
            self.depth_canvas_image_id = self.depth_canvas.create_image(
                (0, 0), anchor="nw", image=images[0],
                tags=("BITMAP", "3D_BITMAP"))
            self.image_canvas.itemconfig(self.depth_canvas_id,
                                         width=w, height=h)
            self.depth_canvas.config(scrollregion="0 0 %s %s" % (w, h))
            self.update_scroll_regions()

        self.depth_canvas.coords(self.depth_canvas_image_id,
                                 (0, -self.depth_index.get()*self.curr_depth))


class BitmapDisplayButton(BinillaWidget, ttk.Button):
    bitmap_tag = None
    display_frame = None
    display_frame_class = BitmapDisplayFrame

    def __init__(self, master, *args, **kwargs):
        BinillaWidget.__init__(self)
        self.change_bitmap(kwargs.pop('bitmap_tag', None))
        kwargs.setdefault("command", self.show_window)
        kwargs.setdefault("text", "Bitmap preview")
        ttk.Button.__init__(self, master, *args, **kwargs)

    def set_disabled(self, disable=True):
        if bool(disable) != self.disabled:
            self.config(state='disabled' if disable else 'normal')
            BinillaWidget.set_disabled(self, disable)

    def change_bitmap(self, bitmap_tag):
        if bitmap_tag is not None:
            self.bitmap_tag = bitmap_tag

        f = self.display_frame
        if f is not None and f() is not None:
            f().change_textures(self.get_textures(self.bitmap_tag))

    def get_textures(self, bitmap_tag):
        raise NotImplementedError("This method must be overloaded.")

    def destroy(self, e=None):
        self.bitmap_tag = None
        self.f_widget_parent = None
        ttk.Button.destroy(self)
        self.delete_all_traces()
        self.delete_all_widget_refs()

    def show_window(self, e=None, parent=None):
        if parent is None:
            parent = self
        w = tk.Toplevel()
        self.display_frame = weakref.ref(self.display_frame_class(w))
        self.display_frame().change_textures(self.get_textures(self.bitmap_tag))
        self.display_frame().pack(expand=True, fill="both")
        w.transient(parent)
        try:
            #tag_name = self.bitmap_tag().filepath
            tag_name = self.bitmap_tag.filepath
        except Exception:
            tag_name = "untitled"
        w.title("Preview: %s" % tag_name)
        w.focus_force()
        return w
