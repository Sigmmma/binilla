import subprocess
try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk
from io import StringIO

from time import sleep
from supyr_struct.defs.util import *
from traceback import format_exc


class IORedirecter(StringIO):
    text_out = None   # a Tkinter text widget to display output
    log_file = None   # a writable file to log input/output to
    edit_log = False  # whether or not to log text input/output to the log_file

    def __init__(self, text_out, *args, **kwargs):
        self.log_file = kwargs.pop('log_file', None)
        self.edit_log = kwargs.pop('edit_log', False)
        StringIO.__init__(self, *args, **kwargs)
        self.text_out = text_out

    def write(self, string):
        if self.edit_log and self.log_file is not None:
            try:
                self.log_file.write(string)
            except Exception:
                pass
        self.text_out.config(state=tk.NORMAL)
        self.text_out.insert(tk.END, string)
        self.text_out.see(tk.END)
        self.text_out.config(state=tk.DISABLED)


class ProcController():
    kill = False
    abandon = False

    def __init__(self, kill=False, abandon=False):
        self.kill = kill
        self.abandon = abandon


def do_subprocess(exec_path, cmd_args=(), exec_args=(), **kw):
    result = 1
    proc_controller = kw.pop("proc_controller", ProcController())
    try:
        cmd_args  = ''.join((" /%s" % a) for a in cmd_args)
        exec_args = ''.join(( " %s" % a) for a in exec_args)
        cmd_str = '"%s" %s'
        if cmd_args:
            cmd_str = "cmd %s %s" % (cmd_args, cmd_str)

        with subprocess.Popen(cmd_str % (exec_path, exec_args), **kw) as p:
            while p.poll() is None:
                if proc_controller.kill:
                    p.kill()
                    p.wait()
                elif proc_controller.abandon:
                    break
                sleep(0.02)
    except Exception:
        print(format_exc())
    return result
