'''
This module is our wrapper for filedialog so we can use a better one
if it is available.

The filepicker for Tkinter on Linux is just... ouch.
So, this is the alternative solution.
'''

import sys

use_tk_dialog = True

if "linux" in sys.platform:
    try:
        # Import all of these with a prepended underscore to avoid people thinking
        # about using these instead of importing them properly.
        import subprocess
        from os.path import splitext, join
        from tkinter import messagebox
        # capture_output to hide it from our terminal.
        if subprocess.run("kdialog", capture_output=True).returncode != 0:
            # Hacky way to jump into the except block.
            raise ValueError

        def _fix_output(output):
            '''
            Removes miscelanous stdout output that can with Mesa drivers.
            Only accept absolute paths that start with the root separator.
            '''
            return list(filter(lambda a : a.startswith("/"), output.split("\n")))

        def _parse_file_filters(the_filters):
            '''
            Parses the tkinter file filters into a set of filters for kdialog.
            '''
            # This sucks right now.
            # We can't get file type descriptions into kdialog.
            # Still, anything better than the default filedialog
            # from tkinter on Linux.
            # This joins all the filters like so: "*.mp3|*.ogg|*.wav"

            # If we weren't supplying * as a filter everywhere I would have
            # done a "thing1 thing2 thing3 ( *.ext1 *.ext2 *.ext3 )" filter.
            # kdialog sadly isn't the nicest thing ever. But we have something at
            # least.
            return "|".join(map(lambda a : a[1], the_filters))

        def askopenfilename(
                title="Open file", initialdir=".",
                filetypes=(('All', '*'),), **kw):
            '''
            Tkinter style wrapper for kdialog --getopenfilename.
            Arguments listed at the top are the only ones actually accounted for.
            The rest are discarded.
            '''
            res = subprocess.run(
                ["kdialog",
                "--title", str(title),
                "--getopenfilename",
                str(initialdir), _parse_file_filters(filetypes)],
                capture_output=True, universal_newlines=True)
            try:
                return _fix_output(res.stdout)[0]
            except IndexError:
                return ""

        def askopenfilenames(
                title="Open files", initialdir=".",
                filetypes=(('All', '*'),), **kw):
            '''
            Tkinter style wrapper for kdialog --getopenfilename.
            Arguments listed at the top are the only ones actually accounted for.
            The rest are discarded.
            '''
            res = subprocess.run(
                ["kdialog",
                "--title", str(title),
                # Get multiple items, put them on different lines for parsing.
                "--multiple", "--separate-output",
                "--getopenfilename",
                str(initialdir), _parse_file_filters(filetypes)],
                capture_output=True, universal_newlines=True)
            return _fix_output(res.stdout)

        def askdirectory(
                title="Choose folder", initialdir=".", **kw):
            '''
            Tkinter style wrapper for kdialog --getexistingdirectory.
            Arguments listed at the top are the only ones actually accounted for.
            The rest are absolutely trashed.
            '''
            res = subprocess.run(
                ["kdialog",
                "--title", str(title),
                "--getexistingdirectory",
                str(initialdir)],
                capture_output=True, universal_newlines=True)
            try:
                return _fix_output(res.stdout)[0]
            except IndexError:
                return ""

        def asksaveasfilename(
                title="Open file", initialdir=".",
                filetypes=(('All', '*'),),
                defaultextension="", **kw):
            '''
            Tkinter style wrapper for kdialog --getsavefilename.
            Arguments listed at the top are the only ones actually accounted for.
            The rest are discarded.
            '''
            res = subprocess.run(
                ["kdialog",
                "--title", str(title),
                "--getsavefilename",
                # Joining these causes the extension to appear in the name box
                join(str(initialdir), defaultextension),
                _parse_file_filters(filetypes)],
                capture_output=True, universal_newlines=True)
            try:
                return _fix_output(res.stdout)[0]
            except IndexError:
                return ""

        use_tk_dialog = False

    except Exception:
        print("kdialog is not installed.\n"
              "If you want somewhat decent filedialogs "
              "you should consider getting it.")

del sys

# Fallback for Linux, default for mac and Windows.
if use_tk_dialog:
    from tkinter.filedialog import ( askopenfilename, askopenfilenames,
        askdirectory, asksaveasfilename )

del use_tk_dialog
