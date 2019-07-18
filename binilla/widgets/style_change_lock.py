import weakref

class StyleChangeLock:
    __slots__ = ("_lock_depth", "_binilla_widget")

    def __init__(self, binilla_widget):
        self._lock_depth = 0
        self._binilla_widget = weakref.ref(binilla_widget)

    def __enter__(self):
        curr_lock_depth = self._lock_depth
        if not curr_lock_depth and self._binilla_widget():
            self._binilla_widget().enter_style_change()

        self._lock_depth += 1
        return curr_lock_depth

    def __exit__(self, except_type, except_value, traceback):
        if self._lock_depth <= 0:
            return

        try:
            self._lock_depth -= 1
            if not self._lock_depth and self._binilla_widget():
                self._binilla_widget().exit_style_change()
        except AttributeError:
            return

    @property
    def lock_depth(self): return self._lock_depth

    def acquire_lock(self):
        '''Do not call this unless you know what you are doing.'''
        self.__enter__()

    def release_lock(self):
        '''Do not call this unless you know what you are doing.'''
        self.__exit__(None, None, None)
