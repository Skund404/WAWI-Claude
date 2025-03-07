"""
Base package for common view components.
Provides base classes and utilities for building consistent UIs.
"""

from .base_view import BaseView
from .base_dialog import BaseDialog
from .view_mixins import (
    SearchMixin,
    FilterMixin,
    SortableMixin,
    ExportMixin,
    UndoRedoMixin,
    ValidationMixin
)
from .widget_factory import WidgetFactory

__all__ = [
    'BaseView',
    'BaseDialog',
    'SearchMixin',
    'FilterMixin',
    'SortableMixin',
    'ExportMixin',
    'UndoRedoMixin',
    'ValidationMixin',
    'WidgetFactory'
]
