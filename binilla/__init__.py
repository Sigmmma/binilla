# ##############
#   metadata   #
# ##############
__author__ = "Devin Bobadilla"
#           YYYY.MM.DD
__date__ = "2019.09.05"
__version__ = (1, 1, 3)
__all__ = (
    'defs', 'widgets', 'windows',
    'app_window', 'constants', 'edit_manager', 'editor_constants', 'handler',
    )

from binilla import constants

constants.inject()

# Hack: Temp import filedialog before anything else to avoid import order
# conflict to do with FieldWidget.
# TODO: Moses, please fix the root of this issue.
from binilla.windows import filedialog
del filedialog
