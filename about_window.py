import os

from traceback import format_exc
import threadsafe_tkinter as tk
import tkinter.ttk as ttk

from tkinter.messagebox import showerror

from binilla.widgets import BinillaWidget

try:
    from idlelib.textView import TextViewer

    class BinillaTextViewer(TextViewer, BinillaWidget):
        def __init__(self, *a, **kw):
            BinillaWidget.__init__(self, *a, **kw)
            TextViewer.__init__(self, *a)
            self.apply_style()


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

    def __init__(self, master, *a, **kw):
        BinillaWidget.__init__(self, *a, **kw)
        kw.update(width=450, height=270, bd=0, highlightthickness=0)
        title = kw.pop("title", "About")
        module_names = kw.pop("module_names", ())
        iconbitmap = kw.pop("iconbitmap", "")

        tk.Toplevel.__init__(self, master, *a, **kw)
        self.resizable(0, 0)
        self.title(title)
        self.transient(master)

        self.update()
        try:
            if iconbitmap:
                self.iconbitmap(iconbitmap)
        except Exception:
            print("Could not load window icon.")

        self.module_infos = {}
        for name in module_names:
            try:
                self.module_infos[name] = self.get_module_info(name)
            except Exception:
                print(format_exc())

        self.bind('<Return>', self.destroy)
        self.bind('<Escape>', self.destroy)
        self.apply_style()

    def get_module_info(self, module_name):
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
            version_string), license_fp)

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
            version_string), readme_fp)

    def open_module_location(self, module_name):
        module_location = self.module_infos.get(module_name, {}).get("location")
        if not(module_location and os.path.isdir(module_location)):
            print("'%s' does not exist" % module_location)
            return

        try:
            os.startfile(module_location)
        except Exception as e:
            showerror('Browser open error', str(e), parent=self.master)
