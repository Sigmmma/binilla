'''
This module is our wrapper for filedialog so we can use a better one
if it is available.

The filepicker for Tkinter on Linux is just... ouch.
So, this is the alternative solution.
'''

import sys
from pathlib import Path

USE_TK_DIALOG = True

if "linux" in sys.platform:
    import subprocess
    import re
    from os.path import join

    def _fix_output(output):
        '''
        Removes miscelanous stdout output that can happen with Mesa drivers.
        Only accept absolute paths that start with the root separator.
        '''
        return list(filter(lambda a : a.startswith("/"), output.split("\n")))



    # Name of the command of the native filedialog if we have one.
    DIALOG_NAME = ""

    # Used for getting the width and height of the primary monitor from the
    # xrandr command output. Tests here: https://regex101.com/r/clpmtZ/1
    SCREEN_RES_REGEX = re.compile(r'primary (\d+)x(\d+)')

    screen_resolution = (0,0,)

    # Try to get the primary screen resolution from xrandr.

    try:
        screen_resolution = SCREEN_RES_REGEX.search(
            subprocess.run(
                "xrandr",
                capture_output=True, universal_newlines=True).stdout
        ).group(1,2)
        screen_resolution = (
            int(screen_resolution[0]),
            int(screen_resolution[1]),
        )
    except Exception:
        print("Couldn't retrieve screen resolution.")



    # Figure out what native file dialog we can use.

    try:
        # Yad is the best, please have yad.
        if subprocess.run(["yad", "--help"], capture_output=True).returncode == 0:
            DIALOG_NAME = "yad"
    except Exception:
        try:
            # kdialog is second best, give us that.
            if subprocess.run("kdialog", capture_output=True).returncode == 0:
                DIALOG_NAME = "kdialog"
        except Exception:
            # This one is nice. But it has a tendency to keep opening the
            # recent files folder. And I don't like that >:P
            if subprocess.run("zenity", capture_output=True).returncode == 255:
                DIALOG_NAME = "zenity"

    if not DIALOG_NAME:
        # Can't "import" any good dialogs.
        raise ImportError



    # These are the functions to wrap zenity and yad.

    if DIALOG_NAME in ("yad", "zenity"):

        # Construct the common arguments for the calling of zenity or yad.

        ZENITY_COMMON_ARGS = [
            "--file-selection",
            "--separator=\n",
        ]

        # If any of these arguments are present zenity won't open.
        if DIALOG_NAME == "yad":
            ZENITY_COMMON_ARGS.extend([
                "--on-top",
                "--mouse",
            ])

        # Yad likes to open with a really small window size. Work around that.
        if screen_resolution[0] and screen_resolution[1]:
            ZENITY_COMMON_ARGS.extend([
                "--width=%d" % (int(screen_resolution[0]/1.5)),
                "--height=%d" % (int(screen_resolution[1]/1.5)),
            ])

        def _parse_file_filters(the_filters):
            '''
            Parses the tkinter file filters into a set of filters for zenity.
            '''
            # Filters look like "name (extension)" to users.
            # Filters get a * prepended so they actually work.
            return list(map(lambda a : '--file-filter=%s (%s) | *%s' %
                                (a[0], a[1], a[1].lstrip('*')), the_filters))

        def askopenfilename(
                title="Open file", initialdir=str(Path.cwd()),
                filetypes=(('All', '*'),), **kw):
            '''
            Tkinter style wrapper for zenity --file-selection.
            Arguments listed at the top are the only ones actually accounted for.
            The rest are discarded.
            '''
            res = subprocess.run(
                [DIALOG_NAME,
                "--title=%s" % (title),
                *ZENITY_COMMON_ARGS,
                "--filename=%s/" % (initialdir),
                *_parse_file_filters(filetypes)],
                capture_output=True, universal_newlines=True)
            try:
                return _fix_output(res.stdout)[0]
            except IndexError:
                return ""

        def askopenfilenames(
                title="Open files", initialdir=str(Path.cwd()),
                filetypes=(('All', '*'),), **kw):
            '''
            Tkinter style wrapper for zenity --file-selection.
            Arguments listed at the top are the only ones actually accounted for.
            The rest are discarded.
            '''
            res = subprocess.run(
                [DIALOG_NAME,
                "--title=%s" % (title),
                *ZENITY_COMMON_ARGS,
                # Get multiple items, put them on different lines for parsing.
                "--multiple",
                "--filename=%s/%s" % (initialdir, filetypes[0][1]),
                *_parse_file_filters(filetypes)],
                capture_output=True, universal_newlines=True)
            return _fix_output(res.stdout)

        def askdirectory(
                title="Choose folder", initialdir=str(Path.cwd()), **kw):
            '''
            Tkinter style wrapper for zenity --file-selection.
            Arguments listed at the top are the only ones actually accounted for.
            The rest are absolutely trashed.
            '''
            res = subprocess.run(
                [DIALOG_NAME,
                "--title=%s" % (title),
                *ZENITY_COMMON_ARGS,
                # Get a directory.
                "--directory",
                "--filename=%s/" % (initialdir)],
                capture_output=True, universal_newlines=True)
            try:
                return _fix_output(res.stdout)[0]
            except IndexError:
                return ""

        def asksaveasfilename(
                title="Open file", initialdir=str(Path.cwd()),
                filetypes=(('All', '*'),),
                defaultextension="", **kw):
            '''
            Tkinter style wrapper for zenity --file-selection.
            Arguments listed at the top are the only ones actually accounted for.
            The rest are discarded.
            '''
            res = subprocess.run(
                [DIALOG_NAME,
                "--title=%s" % (title),
                *ZENITY_COMMON_ARGS,
                # Start in save mode.
                "--save", "--confirm-overwrite",
                "--filename=%s/%s" % (initialdir, defaultextension),
                *_parse_file_filters(filetypes)],
                capture_output=True, universal_newlines=True)
            try:
                return _fix_output(res.stdout)[0]
            except IndexError:
                return ""

        USE_TK_DIALOG = False



    # These are the functions used for kdialog.

    if DIALOG_NAME == "kdialog":
        # capture_output to hide it from our terminal.
        if subprocess.run("kdialog", capture_output=True).returncode != 0:
            # Hacky way to jump into the except block.
            raise ValueError

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
            return "|".join(map(lambda a : "*%s" % a[1].lstrip('*'), the_filters))

        def askopenfilename(
                title="Open file", initialdir=str(Path.cwd()),
                filetypes=(('All', '*'),), **kw):
            '''
            Tkinter style wrapper for kdialog --getopenfilename.
            Arguments listed at the top are the only ones actually accounted for.
            The rest are discarded.
            '''
            res = subprocess.run(
                [DIALOG_NAME,
                "--title", str(title),
                "--getopenfilename",
                str(initialdir), _parse_file_filters(filetypes)],
                capture_output=True, universal_newlines=True)
            try:
                return _fix_output(res.stdout)[0]
            except IndexError:
                return ""

        def askopenfilenames(
                title="Open files", initialdir=str(Path.cwd()),
                filetypes=(('All', '*'),), **kw):
            '''
            Tkinter style wrapper for kdialog --getopenfilename.
            Arguments listed at the top are the only ones actually accounted for.
            The rest are discarded.
            '''
            res = subprocess.run(
                [DIALOG_NAME,
                "--title", str(title),
                # Get multiple items, put them on different lines for parsing.
                "--multiple", "--separate-output",
                "--getopenfilename",
                str(initialdir), _parse_file_filters(filetypes)],
                capture_output=True, universal_newlines=True)
            return _fix_output(res.stdout)

        def askdirectory(
                title="Choose folder", initialdir=str(Path.cwd()), **kw):
            '''
            Tkinter style wrapper for kdialog --getexistingdirectory.
            Arguments listed at the top are the only ones actually accounted for.
            The rest are absolutely trashed.
            '''
            res = subprocess.run(
                [DIALOG_NAME,
                "--title", str(title),
                "--getexistingdirectory",
                str(initialdir)],
                capture_output=True, universal_newlines=True)
            try:
                return _fix_output(res.stdout)[0]
            except IndexError:
                return ""

        def asksaveasfilename(
                title="Open file", initialdir=str(Path.cwd()),
                filetypes=(('All', '*'),),
                defaultextension="", **kw):
            '''
            Tkinter style wrapper for kdialog --getsavefilename.
            Arguments listed at the top are the only ones actually accounted for.
            The rest are discarded.
            '''
            res = subprocess.run(
                [DIALOG_NAME,
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

        USE_TK_DIALOG = False

    if DIALOG_NAME and not USE_TK_DIALOG:
        print("Using native %s for filedialogs." % DIALOG_NAME)


# Fallback for Linux, default for mac and Windows.
if USE_TK_DIALOG:
    if "linux" in sys.platform:
        from tkinter import messagebox
        error = ("No supported native filedialog package installed.",
                "The default tkinter filedialog for Linux does not work\n"
                "properly with symlinks.\n\n"
                "Please install either yad, kdialog, or zenity.\n"
                "(These suggestions are ordered based on how well they work.)")
        print("\n".join(error))

        def no_native_file_dialog_error():
            '''
            Only exists if there is no native file dialog.
            Displays an error warning the user when called.
            '''
            messagebox.showerror(error[0], error[1])

    from tkinter.filedialog import ( askopenfilename, askopenfilenames,
        askdirectory, asksaveasfilename )

del sys
