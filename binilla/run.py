#!/usr/bin/env python3
import sys

info = sys.version_info

try:
    from binilla import stdout_redirect
    stdout_redirect.start_storing_output()
except ImportError:
    # Well, I guess we're not logging anything
    pass

if info[0] < 3 or info[1] < 5:
    input(
        "You must have python 3.5 or higher installed to run Binilla.\n"
        "You currently have %s.%s.%s installed instead." % info[:3])
    raise SystemExit(0)

from datetime import datetime
from traceback import format_exc

try:
    from binilla.app_window import Binilla
    main_window = Binilla(debug=3)
    try:
        stdout_redirect.flush_buffered_output()
    except Exception:
        # I eat poo
        pass
    main_window.mainloop()

except Exception:
    exception = format_exc()
    try:
        main_window.log_file.write('\n' + exception)
    except Exception:
        try:
            with open('startup_crash.log', 'a+') as cfile:
                time = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
                cfile.write("\n%s%s%s\n" % ("-"*30, time, "-"*(50-len(time))))
                cfile.write(time + exception)
        except Exception:
            pass
    print(exception)
    input()
