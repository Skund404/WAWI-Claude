"""
Leatherworking Application GUI Package.

This package contains all GUI components for the Leatherworking Workshop Manager application.
"""

import logging

# Set up package-level logger
logger = logging.getLogger(__name__)

# Version information
__version__ = '0.5.0'
__author__ = 'Leatherworking Workshop Team'

# Import commonly used modules
from . import base
from . import components
from . import dialogs

# Export commonly used classes
from .base import BaseView, BaseDialog
from .components import treeview, form_builder, charts

# Initialize module
logger.debug("GUI module initialized")