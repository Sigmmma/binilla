import imp
import os
import platform
import sys
import subprocess
try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk
from io import StringIO

from math import log, ceil
from pathlib import Path
from time import sleep
from traceback import format_exc

from binilla import editor_constants as e_c
from supyr_struct.util import is_path_empty

POS_INF = float("inf")
NEG_INF = float("-inf")
FLOAT_PREC  = 23*log(2, 10)
DOUBLE_PREC = 52*log(2, 10)


def is_main_frozen():
   return (hasattr(sys, "frozen") or
           hasattr(sys, "importers")
           or imp.is_frozen("__main__"))


def float_to_str(f, max_sig_figs=FLOAT_PREC):
    if f == POS_INF:
        return "inf"
    elif f == NEG_INF:
        return "-inf"

    sig_figs = -1
    if abs(f) > 0:
        sig_figs = int(round(max_sig_figs - log(abs(f), 10) - 1))

    if sig_figs < 0:
        # do the string conversion this way so large numbers
        # dont get converted into exponential notation
        return ("%f" % f).split(".")[0]

    str_float = ("%" + (".%sf" % sig_figs)) % f
    if "." in str_float:
        return str_float.rstrip("0").rstrip(".")
    return str_float


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
    process = None
    returncode = None

    def __init__(self, kill=False, abandon=False,
                 process=None, returncode=None):
        self.kill = kill
        self.abandon = abandon
        self.process = process
        self.returncode = returncode


def do_subprocess(exec_path, cmd_args=(), exec_args=(), **kw):
    result = 1
    proc_controller = kw.pop("proc_controller", ProcController())
    try:

        if e_c.IS_LNX:
            args = (exec_path, ) + exec_args
        else:
            cmd_args  = ''.join((" /%s" % a.lower()) for a in cmd_args)
            cmd_str = '"%s" %s'
            if cmd_args:
                # ALWAYS make sure either /c or /k are explicitely supplied when
                # calling cmd, otherwise default quote handling will be used and
                # putting quotes around everything won't supply parameters right
                if '/k' not in cmd_args:
                    cmd_args += ' /c'
                cmd_str = 'cmd %s "%s"' % (cmd_args, cmd_str)

            exec_args = ''.join(( " %s" % a.lower()) for a in exec_args)
            args = cmd_str % (exec_path, exec_args)

        with subprocess.Popen(args, **kw) as p:
            proc_controller.process = p
            while p.poll() is None:
                if proc_controller.kill:
                    p.kill()
                    p.wait()
                elif proc_controller.abandon:
                    break
                sleep(0.02)

        result = p.returncode
    except Exception:
        print(format_exc())

    proc_controller.returncode = result
    return result


def open_in_default_program(path):
    '''
    Opens file in default program while not locking execution of the rest
    of the program.
    '''
    try:
        if e_c.IS_MAC:
            os.system('open "%s"' % path)
        elif e_c.IS_LNX:
            os.system('xdg-open "%s"' % path)
        else:
            if Path(path).is_dir():
                # windows does not properly open directories using "start".
                # we have to directly call explorer in this case
                os.system('explorer "%s"' % path)
            else:
                os.system('start /B "" "%s"' % path)
    except Exception:
        print(format_exc())
