import weakref
import threadsafe_tkinter as tk

from binilla.widgets.field_widgets import container_frame


class SimpleImageFrame(container_frame.ContainerFrame):
    tag = None
    image_frame = None
    display_frame_cls = type(None)

    def __init__(self, *args, **kwargs):
        container_frame.ContainerFrame.__init__(self, *args, **kwargs)
        try:
            self.tag = self.tag_window.tag
        except AttributeError:
            pass
        self.populate()

    def populate(self):
        container_frame.ContainerFrame.populate(self)
        if self.image_frame is None or self.image_frame() is None:
            self.image_frame = weakref.ref(self.display_frame_cls(self))
        self.reload()

    def pose_fields(self):
        orient = self.desc.get('ORIENT', 'v')[:1].lower()
        side = 'left' if orient == 'h' else 'top'
        if self.image_frame:
            self.image_frame().pack(side=side, fill='x')
        container_frame.ContainerFrame.pose_fields(self)
