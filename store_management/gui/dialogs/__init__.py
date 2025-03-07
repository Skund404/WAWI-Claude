# gui/dialogs/__init__.py
"""
Initialization file for the dialogs package.
Provides easy imports for all dialog classes.
"""

from .add_dialog import AddDialog
from .confirmation_dialog import ConfirmationDialog
from .edit_dialog import EditDialog
from .export_dialog import ExportDialog
from .filter_dialog import FilterDialog
from .import_dialog import ImportDialog
from .message_dialog import MessageDialog
from .report_dialog import ReportDialog
from .search_dialog import SearchDialog

__all__ = [
    'AddDialog',
    'ConfirmationDialog',
    'EditDialog',
    'ExportDialog',
    'FilterDialog',
    'ImportDialog',
    'MessageDialog',
    'ReportDialog',
    'SearchDialog',
]

import logging
logger = logging.getLogger(__name__)
logger.debug("Dialogs module initialized")