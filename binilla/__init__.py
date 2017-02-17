from binilla import app_window, config_def, constants, edit_manager,\
     editor_constants, field_widgets, handler, tag_window, widget_picker,\
     widgets

# ##############
#   metadata   #
# ##############
__version__ = "0.9.1"
__author__ = "MosesBobadilla, <mosesbobadilla@gmail.com>"

__all__ = (
    'app_window', 'config_def', 'constants', 'edit_manager',
    'editor_constants', 'field_widgets', 'handler',
    'tag_window', 'widget_picker', 'widgets',
    )

# give the field_widgets module a reference to the widget_picker module
field_widgets.widget_picker = widget_picker
