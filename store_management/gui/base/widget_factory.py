# gui/base/widget_factory.py
"""
Widget factory for the leatherworking application.

Provides factory methods to create common widgets with consistent styling.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional, Callable, Union, Tuple

from gui.theme import COLORS, FONTS, PADDING, get_status_style, create_custom_font
from gui.widgets.status_badge import StatusBadge
from gui.widgets.enhanced_treeview import EnhancedTreeview
from gui.widgets.enum_combobox import EnumCombobox
from gui.widgets.search_frame import SearchFrame, SearchField

logger = logging.getLogger(__name__)


class WidgetFactory:
    """Factory for creating consistently styled widgets."""

    @staticmethod
    def create_frame(parent, **kwargs):
        """
        Create a styled frame.

        Args:
            parent: Parent widget
            **kwargs: Additional arguments for ttk.Frame

        Returns:
            ttk.Frame widget
        """
        frame = ttk.Frame(parent, **kwargs)
        return frame

    @staticmethod
    def create_label(parent, text, font_style="body", **kwargs):
        """
        Create a styled label.

        Args:
            parent: Parent widget
            text: Label text
            font_style: Font style from theme.FONTS
            **kwargs: Additional arguments for ttk.Label

        Returns:
            ttk.Label widget
        """
        label = ttk.Label(parent, text=text, **kwargs)
        if font_style in FONTS:
            label.configure(font=create_custom_font(FONTS[font_style]))
        return label

    @staticmethod
    def create_button(parent, text, command=None, **kwargs):
        """
        Create a styled button.

        Args:
            parent: Parent widget
            text: Button text
            command: Button command
            **kwargs: Additional arguments for ttk.Button

        Returns:
            ttk.Button widget
        """
        button = ttk.Button(parent, text=text, command=command, **kwargs)
        return button

    @staticmethod
    def create_entry(parent, textvariable=None, **kwargs):
        """
        Create a styled entry.

        Args:
            parent: Parent widget
            textvariable: StringVar for entry value
            **kwargs: Additional arguments for ttk.Entry

        Returns:
            ttk.Entry widget
        """
        entry = ttk.Entry(parent, textvariable=textvariable, **kwargs)
        return entry

    @staticmethod
    def create_combobox(parent, values=None, textvariable=None, **kwargs):
        """
        Create a styled combobox.

        Args:
            parent: Parent widget
            values: List of values for the combobox
            textvariable: StringVar for combobox value
            **kwargs: Additional arguments for ttk.Combobox

        Returns:
            ttk.Combobox widget
        """
        combo = ttk.Combobox(parent, values=values, textvariable=textvariable, **kwargs)
        return combo

    @staticmethod
    def create_enum_combobox(parent, enum_class, **kwargs):
        """
        Create a combobox for an enum.

        Args:
            parent: Parent widget
            enum_class: Enum class to use
            **kwargs: Additional arguments for EnumCombobox

        Returns:
            EnumCombobox widget
        """
        combo = EnumCombobox(parent, enum_class=enum_class, **kwargs)
        return combo

    @staticmethod
    def create_treeview(parent, columns, **kwargs):
        """
        Create an enhanced treeview.

        Args:
            parent: Parent widget
            columns: List of column identifiers
            **kwargs: Additional arguments for EnhancedTreeview

        Returns:
            EnhancedTreeview widget
        """
        treeview = EnhancedTreeview(parent, columns=columns, **kwargs)
        return treeview

    @staticmethod
    def create_status_badge(parent, text, status_value=None, **kwargs):
        """
        Create a status badge.

        Args:
            parent: Parent widget
            text: Badge text
            status_value: Status value for styling
            **kwargs: Additional arguments for StatusBadge

        Returns:
            StatusBadge widget
        """
        badge = StatusBadge(parent, text=text, status_value=status_value, **kwargs)
        return badge

    @staticmethod
    def create_search_frame(parent, fields, callback=None, **kwargs):
        """
        Create a search frame.

        Args:
            parent: Parent widget
            fields: List of SearchField objects
            callback: Function to call when search is performed
            **kwargs: Additional arguments for SearchFrame

        Returns:
            SearchFrame widget
        """
        search_frame = SearchFrame(parent, fields=fields, callback=callback, **kwargs)
        return search_frame

    @staticmethod
    def create_header(parent, text, **kwargs):
        """
        Create a header label.

        Args:
            parent: Parent widget
            text: Header text
            **kwargs: Additional arguments for ttk.Label

        Returns:
            ttk.Label widget with header styling
        """
        header = ttk.Label(parent, text=text, **kwargs)
        header.configure(font=create_custom_font(FONTS["header"]))
        return header

    @staticmethod
    def create_subheader(parent, text, **kwargs):
        """
        Create a subheader label.

        Args:
            parent: Parent widget
            text: Subheader text
            **kwargs: Additional arguments for ttk.Label

        Returns:
            ttk.Label widget with subheader styling
        """
        subheader = ttk.Label(parent, text=text, **kwargs)
        subheader.configure(font=create_custom_font(FONTS["subheader"]))
        return subheader

    @staticmethod
    def create_section_frame(parent, title=None, **kwargs):
        """
        Create a frame for a section with optional title.

        Args:
            parent: Parent widget
            title: Optional section title
            **kwargs: Additional arguments for ttk.LabelFrame

        Returns:
            ttk.LabelFrame widget
        """
        if title:
            frame = ttk.LabelFrame(parent, text=title, **kwargs)
        else:
            frame = ttk.Frame(parent, **kwargs)
        return frame

    @staticmethod
    def create_form_row(parent, label_text, widget_factory, **kwargs):
        """
        Create a form row with label and widget.

        Args:
            parent: Parent widget
            label_text: Label text
            widget_factory: Function to create the widget
            **kwargs: Additional arguments for widget_factory

        Returns:
            Tuple of (frame, widget)
        """
        frame = ttk.Frame(parent)

        label = WidgetFactory.create_label(frame, text=label_text)
        label.pack(side=tk.LEFT, padx=(0, PADDING["medium"]))

        widget = widget_factory(frame, **kwargs)
        widget.pack(side=tk.LEFT, fill=tk.X, expand=True)

        return frame, widget

    @staticmethod
    def create_button_group(parent, buttons, orientation=tk.HORIZONTAL, spacing=PADDING["medium"]):
        """
        Create a group of buttons.

        Args:
            parent: Parent widget
            buttons: List of (text, command) tuples
            orientation: tk.HORIZONTAL or tk.VERTICAL
            spacing: Spacing between buttons

        Returns:
            Frame containing the buttons
        """
        frame = ttk.Frame(parent)

        for text, command in buttons:
            button = WidgetFactory.create_button(frame, text=text, command=command)
            if orientation == tk.HORIZONTAL:
                button.pack(side=tk.LEFT, padx=(0, spacing))
            else:
                button.pack(side=tk.TOP, pady=(0, spacing))

        return frame


# For direct imports
create_frame = WidgetFactory.create_frame
create_label = WidgetFactory.create_label
create_button = WidgetFactory.create_button
create_entry = WidgetFactory.create_entry
create_combobox = WidgetFactory.create_combobox
create_enum_combobox = WidgetFactory.create_enum_combobox
create_treeview = WidgetFactory.create_treeview
create_status_badge = WidgetFactory.create_status_badge
create_search_frame = WidgetFactory.create_search_frame
create_header = WidgetFactory.create_header
create_subheader = WidgetFactory.create_subheader
create_section_frame = WidgetFactory.create_section_frame
create_form_row = WidgetFactory.create_form_row
create_button_group = WidgetFactory.create_button_group