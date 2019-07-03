from binilla import editor_constants as e_c

__all__ = (
    "binilla_widget", "bitmap_display_frame", "field_widget_picker",
    "scroll_menu", "tooltip_handler", "field_widgets"
    )


def get_mouse_delta(event):
    if e_c.IS_WIN or e_c.IS_MAC:
        return 1 if event.delta < 0 else -1
    elif e_c.IS_LNX:
        return -1 if event.num == 4 else 1
    else:
        return event.delta


def get_relative_widget_position(child, parent):
    x = y = 0
    while child is not parent and parent:
        if child.master is None and child.master is not parent:
            raise Exception("Provided child is not a descendent of parent.")
        x += child.winfo_x()
        y += child.winfo_y()
        child = child.master

    return x, y
