import os
from traceback import format_exc

try:
    from binilla.app_window import Binilla

    if __name__ == "__main__":
        main_window = Binilla()
        main_window.mainloop()

except Exception:
    print(format_exc())
    input()
