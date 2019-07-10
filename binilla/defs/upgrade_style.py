from binilla.widgets import binilla_widget

__all__ = ("upgrade_v1_to_v2", )

def upgrade_v1_to_v2(old_style, new_style):
    new_style.filepath = old_style.filepath

    new_style.data.header.parse(initdata=old_style.data.header)
    new_appearance = new_style.data.appearance
    try:
        new_appearance.theme_name.set_to("_alt")
    except Exception:
        new_appearance.theme_name.set_to("_default")

    new_appearance.widths_and_heights.parse(initdata=old_style.data.widths_and_heights)
    bool_frame_min = old_style.data.widths_and_heights.bool_frame_min
    bool_frame_max = old_style.data.widths_and_heights.bool_frame_max
    new_appearance.widths_and_heights.bool_frame_width[:] = (
        bool_frame_min.width, bool_frame_max.width)
    new_appearance.widths_and_heights.bool_frame_height[:] = (
        bool_frame_min.height, bool_frame_max.height)

    new_appearance.padding.parse(initdata=old_style.data.padding)
    new_appearance.depths.parse(initdata=old_style.data.depths)
    del new_appearance.colors[:]
    new_appearance.colors.extend(len(new_appearance.colors.NAME_MAP))

    for name in new_appearance.colors.NAME_MAP:
        new_color = new_appearance.colors[name]
        binilla_color = getattr(binilla_widget.BinillaWidget, name + '_color', None)

        try:
            new_color[:] = old_style.data.colors[name]
        except Exception:
            if binilla_color is not None:
                binilla_color = binilla_color[1:]
                new_color[0] = int(binilla_color[0:2], 16)
                new_color[1] = int(binilla_color[2:4], 16)
                new_color[2] = int(binilla_color[4:6], 16)

    new_appearance.colors.button_border_light[:] = new_appearance.colors.button
    new_appearance.colors.button_border_dark[:] = new_appearance.colors.button
    return new_style
