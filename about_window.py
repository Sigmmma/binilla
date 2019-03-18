import os
import string

from sys import version_info
from traceback import format_exc
import threadsafe_tkinter as tk

from tkinter.messagebox import showerror

from binilla.widgets import BinillaWidget

VALID_MODULE_CHARACTERS = frozenset(string.ascii_letters + "_" + string.digits)

try:
    from idlelib.textView import TextViewer

    class BinillaTextViewer(TextViewer, BinillaWidget):
        def __init__(self, *a, **kw):
            iconbitmap = kw.pop("iconbitmap", "")
            BinillaWidget.__init__(self, *a, **kw)
            TextViewer.__init__(self, *a)
            self.apply_style()
            if iconbitmap:
                try:
                    if os.path.isfile(iconbitmap):
                        self.iconbitmap(iconbitmap)
                except Exception:
                    print("Could not load window icon.")

        def wait_window(self):
            # null this method
            pass

    def view_file(master, title, filepath, *a, **kw):
        try:
            with open(filepath, 'r') as f:
                text = f.read()
        except Exception as e:
            showerror('File open error', str(e), parent=master)
            return
        return BinillaTextViewer(master, title, text, *a, **kw)

except ImportError:
    BinillaTextViewer = view_file = None


class AboutWindow(tk.Toplevel, BinillaWidget):
    module_infos = {}
    _initialized = False
    _button_pressed = 0
    _start = 3

    app_name = ""

    def __init__(self, master, *a, **kw):
        BinillaWidget.__init__(self, *a, **kw)
        kw.update(highlightthickness=0)
        self.app_name = kw.pop("app_name", "Unknown")
        module_names = kw.pop("module_names", ())
        self.iconbitmap_filepath = kw.pop("iconbitmap", "")

        tk.Toplevel.__init__(self, master, *a, **kw)
        self.resizable(0, 0)
        self.title("About " + self.app_name)
        self.transient(master)

        self.update()
        try:
            if os.path.isfile(self.iconbitmap_filepath):
                self.iconbitmap(self.iconbitmap_filepath)
        except Exception:
            print("Could not load window icon.")

        self.module_infos = {}
        for name in module_names:
            try:
                self.module_infos[name] = self.get_module_info(name)
            except Exception:
                print(format_exc())

        self.generate_widgets()

        self.bind('<Return>', self.destroy)
        self.bind('<Escape>', self.destroy)
        self.apply_style()

        self.update()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        self.geometry("%sx%s" % (w, h))
        self.minsize(width=w, height=h)

    def _pressed(self):
        self._button_pressed += 1
        if self._button_pressed >= self._start:
            self._()

    def _(self):
        pass

    def generate_widgets(self):
        if self._initialized:
            return

        pr_version_str = "%s.%s.%s" % version_info[: 3]
        tk_version_str = str(tk.TkVersion)

        main_frame = tk.Frame(self, borderwidth=0, relief='sunken')
        buttons_frame = tk.Frame(self)
        header_frame = tk.Frame(main_frame)
        py_label_frame = tk.Frame(header_frame, borderwidth=0)

        image_filepath = os.path.splitext(self.iconbitmap_filepath)[0] + ".png"
        app_image_button = None
        if os.path.isfile(image_filepath):
            self.app_image = tk.PhotoImage(file=image_filepath)
            app_image_button = tk.Button(header_frame, text='[picture]', bd=0,
                                         image=self.app_image, relief='flat',
                                         command=self._pressed,
                                         highlightthickness=0)

        app_name_label = tk.Label(header_frame, text=self.app_name,
                                  font=('Copperplate Gothic', 24, 'bold italic'))
        python_ver_label = tk.Label(
            py_label_frame, text='Python version:  %s' % pr_version_str)
        tk_ver_label = tk.Label(
            py_label_frame, text='Tk version:  %s' % tk_version_str)

        close_button = tk.Button(buttons_frame, text='Close', width=12)

        modules_frame = tk.Frame(main_frame, borderwidth=0)
        names = tuple(sorted(self.module_infos))
        max_width = 1
        if len(names) > 3:
            max_width = 2

        x = y = 0
        for name in names:
            info = self.module_infos[name]
            proper_name = self.get_proper_module_name(name)

            module_frame = tk.LabelFrame(
                modules_frame, text="%s  -  %s: %s" % (
                    info["date"], proper_name, self.get_version_string(name)))

            license_button = tk.Button(
                module_frame, text='License', width=8,
                command=lambda s=self, n=name: s.display_module_license(n))
            readme_button = tk.Button(
                module_frame, text='Readme', width=8,
                command=lambda s=self, n=name: s.display_module_readme(n))
            browse_button = tk.Button(
                module_frame, text='Browse', width=8,
                command=lambda s=self, n=name: s.open_module_location(n))

            browse_button.pack(expand=True, fill='both', side='left', padx=6, pady=4)
            license_button.pack(expand=True, fill='both', side='left', padx=6, pady=4)
            readme_button.pack(expand=True, fill='both', side='left', padx=6, pady=4)
            if not info["location"]:
                browse_button.config(state="disabled")
            if not info["license"]:
                license_button.config(state="disabled")
            if not info["readme"]:
                readme_button.config(state="disabled")

            module_frame.grid(row=y, column=x)
            x += 1
            if x == max_width:
                x = 0
                y += 1


        app_name_label.pack(padx=10, fill='both')
        if app_image_button:
            app_image_button.pack(padx=0, pady=3)
        py_label_frame.pack(padx=10, pady=0)

        python_ver_label.pack(padx=10, pady=0, side='left')
        tk_ver_label.pack(padx=10, pady=0, side='right')
        close_button.pack(padx=5, pady=5)

        header_frame.pack(expand=True, fill="both")
        main_frame.pack(expand=True, fill="both")
        modules_frame.pack(fill='both')
        buttons_frame.pack(fill="x")

        self._initialized = True

    def get_module_info(self, module_name):
        # make sure input is sanitary(we ARE running an exec after all)
        bad_chars = set(module_name).difference(VALID_MODULE_CHARACTERS)
        if bad_chars:
            raise ValueError("Bad characters in module name:\n%s" % bad_chars)

        exec("import %s" % module_name)
        module = eval(module_name)

        date = getattr(module, "__date__", "unknown")
        version = getattr(module, "__version__", "unknown")
        module_location = readme_filepath = license_filepath = None

        try:
            module_location = os.path.dirname(module.__file__)

            for root, _, files in os.walk(module_location):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    base, ext = os.path.splitext(filename)
                    if base.lower() == "readme":
                        readme_filepath = filepath
                    elif base.lower() == "license":
                        license_filepath = filepath

                # don't check more than the first level
                break
        except AttributeError:
            pass

        return {"license": license_filepath, "date": date,
                "readme": readme_filepath, "version": version,
                "location": module_location}

    def get_proper_module_name(self, module_name):
        return " ".join(s.capitalize() for s in module_name.split("_"))

    def get_version_string(self, module_name):
        version = self.module_infos.get(module_name, {}).get("version")
        try:
            return "%s.%s.%s" % version
        except Exception:
            return ""

    def display_module_license(self, module_name):
        if not view_file:
            return

        license_fp = self.module_infos.get(module_name, {}).get("license")
        if not(license_fp and os.path.isfile(license_fp)):
            print("'%s' does not exist" % license_fp)
            return

        version_string = self.get_version_string(module_name)
        if version_string:
            version_string = " v%s" % version_string

        view_file(self, "%s%s license" % (
            self.get_proper_module_name(module_name),
            version_string), license_fp, iconbitmap=self.iconbitmap_filepath)

    def display_module_readme(self, module_name):
        if not view_file:
            return

        readme_fp = self.module_infos.get(module_name, {}).get("readme")
        if not(readme_fp and os.path.isfile(readme_fp)):
            print("'%s' does not exist" % readme_fp)
            return

        version_string = self.get_version_string(module_name)
        if version_string:
            version_string = " v%s" % version_string

        view_file(self, "%s%s readme" % (
            self.get_proper_module_name(module_name),
            version_string), readme_fp, iconbitmap=self.iconbitmap_filepath)

    def open_module_location(self, module_name):
        module_location = self.module_infos.get(module_name, {}).get("location")
        if not(module_location and os.path.isdir(module_location)):
            print("'%s' does not exist" % module_location)
            return

        try:
            os.startfile(module_location)
        except Exception as e:
            showerror('Browser open error', str(e), parent=self.master)


if __name__ == "__main__":
    AboutWindow(None, module_names=(
            "binilla",
            "supyr_struct",
            "threadsafe_tkinter",
            ))
