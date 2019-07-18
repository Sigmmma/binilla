from binilla.defs import upgrade_style

__all__ = ("upgrade_v1_to_v2", )

def upgrade_v1_to_v2(old_config, new_config):
    upgrade_style.upgrade_v1_to_v2(old_config, new_config)

    old_data, new_data = old_config.data, new_config.data

    #new_data.general.parse(initdata=old_data.general)
    new_app_window = new_data.app_window
    old_app_window = old_data.app_window
    new_app_window.parse(initdata=old_app_window)

    for name in new_app_window.flags.NAME_MAP:
        new_app_window.flags[name] = old_data.general.flags[name]

    new_app_window.recent_tag_max = old_data.general.recent_tag_max

    tag_windows = new_data.tag_windows
    tag_windows.max_undos = old_data.general.max_undos
    tag_windows.default_dimensions[:] = old_app_window.default_dimensions
    tag_windows.scroll_increment[:]   = old_app_window.scroll_increment

    # copy and rearrange flags
    new_flags = new_data.tag_windows.window_flags
    old_flags = old_data.general.tag_window_flags
    new_flags.sync_window_movement = old_data.general.flags.sync_window_movement
    for name in new_flags.NAME_MAP:
        if name in old_flags.NAME_MAP:
            new_flags[name] = old_flags[name]

    new_flags = new_data.tag_windows.widget_flags
    for name in new_flags.NAME_MAP:
        if name in old_flags.NAME_MAP:
            new_flags[name] = old_flags[name]

    new_flags = new_data.tag_windows.file_handling_flags
    old_flags = old_data.general.file_handling_flags
    for name in new_flags.NAME_MAP:
        if name in old_flags.NAME_MAP:
            new_flags[name] = old_flags[name]

    new_data.tag_backup.max_count = int(bool(old_flags.backup_tags))

    tag_printing = new_data.tag_printing
    tag_printing.block_print_flags = old_data.general.block_print_flags
    tag_printing.print_precision = old_data.general.print_precision
    tag_printing.print_indent = old_data.general.print_indent

    new_data.open_tags.parse(initdata=old_data.open_tags)
    new_data.recent_tags.parse(initdata=old_data.recent_tags)
    new_data.directory_paths.parse(initdata=old_data.directory_paths)
    new_data.all_hotkeys.hotkeys.parse(
        initdata=old_data.hotkeys)
    new_data.all_hotkeys.tag_window_hotkeys.parse(
        initdata=old_data.tag_window_hotkeys)
    return new_config


#if __name__ == "__main__":
#    from binilla.defs import v1_config_def, config_def
#    src_cfg = v1_config_def.v1_config_def.build(filepath="..\\binilla.cfg")
#    dst_cfg = config_def.config_def.build()
#    upgrade_v1_to_v2(src_cfg, dst_cfg)
#    dst_cfg.pprint(printout=True)
