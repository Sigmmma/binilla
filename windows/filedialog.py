'''
This module is our wrapper for filedialog so we can use a better one
if it is available.

The filepicker for Tkinter on Linux is just... ouch.
So, this is the alternative solution.
'''
try:
    # Import all of these with a prepended underscore to avoid people thinking
    # about using these instead of importing them properly.
    import subprocess
    from os.path import splitext
    from tkinter import messagebox
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
        return res.stdout.strip("\n")

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
        return list(filter(len, res.stdout.split("\n")))

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
        return res.stdout.strip("\n")

    def asksaveasfilename(
            title="Open file", initialdir=".",
            filetypes=(('All', '*'),),
            defaultextension="", **kw):
        '''
        Tkinter style wrapper for kdialog --getsavefilename.
        Arguments listed at the top are the only ones actually accounted for.
        The rest are discarded.

        If defaultextension was supplied, but the user tried to save without
        an extension it prompts the user asking if they want the default
        extension appended. This is because kdialog does not have the ability
        to add an extension by default.
        '''
        res = subprocess.run(
            ["kdialog",
            "--title", str(title),
            "--getsavefilename",
            str(initialdir), _parse_file_filters(filetypes)],
            capture_output=True, universal_newlines=True)
        out_path = res.stdout.strip("\n")

        # Don't ask about extensions if no path was returned.
        if not out_path:
            return ""

        _, ext = splitext(out_path)
        # Only ask this if a default extension was supplied.
        if not ext and defaultextension:
            new_path = out_path + defaultextension
            if messagebox.askyesno(
                    title="Oopsie?",
                    message="You saved this file without an extension.\n"
                    "Should I append the default extension so it becomes:\n"
                    "%r?" % (new_path)):
                out_path = new_path

        return out_path

except Exception:
    from sys import platform
    if 'linux' in platform.lower():
        print("kdialog is not installed.\n"
              "If you want somewhat decent filedialogs "
              "you should consider getting it.")
    from tkinter.filedialog import ( askopenfilename, askopenfilenames,
        askdirectory, asksaveasfilename )
