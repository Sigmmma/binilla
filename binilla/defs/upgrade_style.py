from binilla.widgets import binilla_widget

__all__ = ("upgrade_v1_to_v2", )

def upgrade_v1_to_v2(old_style, new_style):
    new_style.filepath = old_style.filepath

    new_version_info = new_style.data.version_info
    new_version_info.parse(attr_index='date_modified')

    if hasattr(old_style.data.version_info, "date_created"):
        date_created = old_style.data.version_info.date_created
    elif hasattr(old_style.data.general, "date_created"):
        date_created = old_style.data.general.date_created
    else:
        date_created = new_version_info.date_modified

    new_version_info.date_created = date_created

    appearance = new_style.data.appearance
    try:
        appearance.theme_name.set_to("_alt")
    except Exception:
        appearance.theme_name.data = "default"

    appearance.widths_and_heights.parse(initdata=old_style.data.widths_and_heights)
    bool_frame_min = old_style.data.widths_and_heights.bool_frame_min
    bool_frame_max = old_style.data.widths_and_heights.bool_frame_max
    appearance.widths_and_heights.bool_frame_width[:] = (
        bool_frame_min.width, bool_frame_max.width)
    appearance.widths_and_heights.bool_frame_height[:] = (
        bool_frame_min.height, bool_frame_max.height)

    appearance.padding.parse(initdata=old_style.data.padding)
    appearance.depths.parse(initdata=old_style.data.depths)
    del appearance.colors[:]
    appearance.colors.extend(len(appearance.colors.NAME_MAP))

    for name in appearance.colors.NAME_MAP:
        new_color = appearance.colors[name]
        binilla_color = getattr(binilla_widget.BinillaWidget, name + '_color', None)

        try:
            new_color[:] = old_style.data.colors[name]
        except Exception:
            if binilla_color is not None:
                binilla_color = binilla_color[1:]
                new_color[0] = int(binilla_color[0:2], 16)
                new_color[1] = int(binilla_color[2:4], 16)
                new_color[2] = int(binilla_color[4:6], 16)

    appearance.colors.button_border_light[:] = appearance.colors.button
    appearance.colors.button_border_dark[:]  = appearance.colors.button
    return new_style
