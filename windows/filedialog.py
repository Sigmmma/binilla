'''
This module is our wrapper for filedialog so we can use a better one
if it is available without crashing if it doesn't exist.
'''
try:
    from tkfilebrowser_nonabs import askopenfilename, askopenfilenames, askdirectory, asksaveasfilename
except Exception:
    from sys import platform
    if 'linux' in platform:
        print("Couldn't find tkfilebrowser_nonabs module!\n"
              "All your file picker dialogs will suck.")
    from tkinter.filedialog import askopenfilename, askopenfilenames, askdirectory, asksaveasfilename
