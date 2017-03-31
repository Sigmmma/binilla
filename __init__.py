from binilla import app_window, config_def, constants, edit_manager,\
     editor_constants, field_widgets, handler, tag_window, widget_picker,\
     widgets

__all__ = (
    'app_window', 'config_def', 'constants', 'edit_manager',
    'editor_constants', 'field_widgets', 'handler',
    'tag_window', 'widget_picker', 'widgets',
    )

# give the field_widgets module a reference to the widget_picker module
field_widgets.widget_picker = widget_picker

# give widgets a reference to field_widgets
widgets.field_widgets = field_widgets
