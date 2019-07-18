class FontConfig(dict):
    __slots__ = ()
    def __init__(self, *a, **kw):
        dict.__init__(self, *a, **kw)
        # default these so the dict is properly filled with defaults
        self.setdefault('family', "")
        self.setdefault('size', 12)
        self.setdefault('weight', "normal")
        self.setdefault('slant', "roman")
        self.setdefault('underline', 0)
        self.setdefault('overstrike', 0)

    @property
    def family(self): return str(self.get("family", ""))
    @property
    def size(self): return int(self.get("size", 12))
    @property
    def weight(self): return str(self.get("weight", "normal"))
    @property
    def slant(self): return str(self.get("slant", "roman"))
    @property
    def underline(self): return bool(self.get("underline", 0))
    @property
    def overstrike(self): return bool(self.get("overstrike", 0))
