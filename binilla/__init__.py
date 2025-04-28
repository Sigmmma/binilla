# ##############
#   metadata   #
# ##############
__author__ = "Sigmmma"
#           YYYY.MM.DD
__date__ = "2025.01.18"
__version__ = (1, 4, 0)
__website__ = "https://github.com/Sigmmma/binilla"
__all__ = (
    'defs', 'widgets', 'windows',
    'app_window', 'constants', 'edit_manager', 'editor_constants', 'handler',
    )

try:
    from binilla import constants

    constants.inject()
except ModuleNotFoundError as e:
    # this is a bit of a hack to account for instances where 
    # binilla is being imported from its setup.py. at this
    # time supyr_struct may not be installed/accessible yet.
    if e.msg != "No module named 'supyr_struct'":
        raise