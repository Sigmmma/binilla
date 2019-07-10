from binilla.defs import upgrade_style

__all__ = ("upgrade_v1_to_v2", )

def upgrade_v1_to_v2(old_config, new_config):
    upgrade_style.upgrade_v1_to_v2(old_config, new_config)

    old_data, new_data = old_config.data, new_config.data

    new_data.app_window.parse(initdata=old_data.app_window)
    new_data.open_tags.parse(initdata=old_data.open_tags)
    new_data.recent_tags.parse(initdata=old_data.recent_tags)
    new_data.directory_paths.parse(initdata=old_data.directory_paths)
    new_data.all_hotkeys.hotkeys.parse(
        initdata=old_data.hotkeys)
    new_data.all_hotkeys.tag_window_hotkeys.parse(
        initdata=old_data.tag_window_hotkeys)
    return new_config
