# gui/dialogs/confirmation_dialog.py
"""
Confirmation dialog for confirming user actions.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable

from gui.base.base_dialog import BaseDialog
from gui.theme import get_color

logger = logging.getLogger(__name__)


class ConfirmationDialog(BaseDialog):
    """Dialog for confirming user actions with customizable options."""

    def __init__(self, parent: tk.Widget, title: str, message: str,
                 confirm_text: str = "OK", cancel_text: str = "Cancel",
                 confirm_style: str = "Accent.TButton", icon: str = "warning",
                 callback: Optional[Callable[[bool], None]] = None,
                 size: tuple = (400, 200)):
        """Initialize the confirmation dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Message to display
            confirm_text: Text for the confirm button
            cancel_text: Text for the cancel button
            confirm_style: Style for the confirm button
            icon: Icon type ('info', 'warning', 'error', 'question')
            callback: Optional callback function
            size: Dialog size (width, height)
        """
        self.message = message
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        self.confirm_style = confirm_style
        self.icon = icon
        self.callback = callback
        self.result = False

        # Set dialog size
        self.width, self.height = size

        super().__init__(parent, title)

    def _create_body(self) -> ttk.Frame:
        """Create the dialog body with message and icon.

        Returns:
            ttk.Frame: The dialog body frame
        """
        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create icon based on type
        icon_frame = ttk.Frame(body)
        icon_frame.pack(side=tk.LEFT, padx=(0, 15))

        icon_text = "❓"  # Default question mark
        icon_color = get_color("info")

        if self.icon == "info":
            icon_text = "ℹ️"
            icon_color = get_color("info")
        elif self.icon == "warning":
            icon_text = "⚠️"
            icon_color = get_color("warning")
        elif self.icon == "error":
            icon_text = "❌"
            icon_color = get_color("error")

        icon_label = ttk.Label(icon_frame, text=icon_text, font=("", 24))
        icon_label.pack(padx=5, pady=5)

        # Create message
        message_frame = ttk.Frame(body)
        message_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        message_label = ttk.Label(message_frame, text=self.message, wraplength=300, justify=tk.LEFT)
        message_label.pack(pady=10, anchor=tk.W)

        # If don't ask again option is needed, add it here
        # self.dont_ask_var = tk.BooleanVar(value=False)
        # dont_ask_cb = ttk.Checkbutton(message_frame, text="Don't ask again",
        #                              variable=self.dont_ask_var)
        # dont_ask_cb.pack(pady=(5, 0), anchor=tk.W)

        return body

    def _create_buttons(self) -> ttk.Frame:
        """Create dialog buttons.

        Returns:
            ttk.Frame: The button frame
        """
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Create confirm button
        confirm_btn = ttk.Button(
            button_frame,
            text=self.confirm_text,
            command=self._on_confirm,
            style=self.confirm_style
        )
        confirm_btn.pack(side=tk.RIGHT, padx=5)

        # Create cancel button if cancel text is provided
        if self.cancel_text:
            cancel_btn = ttk.Button(
                button_frame,
                text=self.cancel_text,
                command=self._on_cancel
            )
            cancel_btn.pack(side=tk.RIGHT, padx=5)

        return button_frame

    def _on_confirm(self) -> None:
        """Handle confirm button click."""
        self.result = True
        if self.callback:
            self.callback(True)
        self._dismiss(True)

    def _on_cancel(self, event=None) -> None:
        """Handle cancel button click."""
        self.result = False
        if self.callback:
            self.callback(False)
        self._dismiss(False)

    def _validate(self) -> bool:
        """Validation not needed for confirmation dialogs."""
        return True

    def _apply(self) -> None:
        """Apply not needed for confirmation dialogs."""
        pass

    @staticmethod
    def show_confirmation(parent: tk.Widget, title: str, message: str,
                          confirm_text: str = "OK", cancel_text: str = "Cancel",
                          icon: str = "warning", size: tuple = (400, 200)) -> bool:
        """Show a confirmation dialog and get the result.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Message to display
            confirm_text: Text for the confirm button
            cancel_text: Text for the cancel button
            icon: Icon type ('info', 'warning', 'error', 'question')
            size: Dialog size (width, height)

        Returns:
            bool: True if confirmed, False if cancelled
        """
        dialog = ConfirmationDialog(
            parent, title, message, confirm_text, cancel_text,
            "Accent.TButton", icon, None, size
        )
        dialog.transient(parent)
        dialog.grab_set()
        parent.wait_window(dialog)
        return dialog.result

    @staticmethod
    def show_info(parent: tk.Widget, title: str, message: str, size: tuple = (350, 180)) -> None:
        """Show an information dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Message to display
            size: Dialog size (width, height)
        """
        ConfirmationDialog.show_confirmation(
            parent, title, message, "OK", "", "info", size
        )

    @staticmethod
    def show_warning(parent: tk.Widget, title: str, message: str, size: tuple = (350, 180)) -> None:
        """Show a warning dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Message to display
            size: Dialog size (width, height)
        """
        ConfirmationDialog.show_confirmation(
            parent, title, message, "OK", "", "warning", size
        )

    @staticmethod
    def show_error(parent: tk.Widget, title: str, message: str, size: tuple = (350, 180)) -> None:
        """Show an error dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Message to display
            size: Dialog size (width, height)
        """
        ConfirmationDialog.show_confirmation(
            parent, title, message, "OK", "", "error", size
        )

    @staticmethod
    def show_question(parent: tk.Widget, title: str, message: str,
                      confirm_text: str = "Yes", cancel_text: str = "No",
                      size: tuple = (400, 180)) -> bool:
        """Show a question dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Message to display
            confirm_text: Text for the confirm button
            cancel_text: Text for the cancel button
            size: Dialog size (width, height)

        Returns:
            bool: True if confirmed, False if cancelled
        """
        return ConfirmationDialog.show_confirmation(
            parent, title, message, confirm_text, cancel_text, "question", size
        )

    @staticmethod
    def show_delete_confirmation(parent: tk.Widget, item_type: str, item_name: str,
                                 size: tuple = (450, 180)) -> bool:
        """Show a confirmation dialog for deleting an item.

        Args:
            parent: Parent widget
            item_type: Type of item being deleted
            item_name: Name of the item being deleted
            size: Dialog size (width, height)

        Returns:
            bool: True if deletion is confirmed, False otherwise
        """
        message = f"Are you sure you want to delete the {item_type} '{item_name}'?\n\nThis action cannot be undone."
        return ConfirmationDialog.show_confirmation(
            parent, f"Delete {item_type}", message, "Delete", "Cancel", "warning", size
        )

    @staticmethod
    def show_discard_changes_confirmation(parent: tk.Widget, size: tuple = (400, 180)) -> bool:
        """Show a confirmation dialog for discarding changes.

        Args:
            parent: Parent widget
            size: Dialog size (width, height)

        Returns:
            bool: True if discarding changes is confirmed, False otherwise
        """
        message = "You have unsaved changes. Are you sure you want to discard them?"
        return ConfirmationDialog.show_confirmation(
            parent, "Discard Changes", message, "Discard", "Cancel", "warning", size
        )