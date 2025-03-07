# gui/dialogs/message_dialog.py
"""
Message dialog for displaying information, warnings, and errors.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable

from gui.base.base_dialog import BaseDialog
from gui.theme import get_color

logger = logging.getLogger(__name__)


class MessageType:
    """Enum-like class for message types."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class MessageDialog(BaseDialog):
    """Dialog for displaying various types of messages to the user."""

    def __init__(self, parent: tk.Widget, title: str, message: str,
                 message_type: str = MessageType.INFO,
                 detail: Optional[str] = None,
                 callback: Optional[Callable[[], None]] = None,
                 size: tuple = (450, 250)):
        """Initialize the message dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Primary message to display
            message_type: Type of message (info, warning, error, success)
            detail: Optional detailed message
            callback: Optional callback function when dialog is closed
            size: Dialog size (width, height)
        """
        self.message = message
        self.message_type = message_type
        self.detail = detail
        self.callback = callback

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

        # Create icon based on message type
        icon_frame = ttk.Frame(body)
        icon_frame.pack(side=tk.LEFT, padx=(0, 15))

        icon_text = "ℹ️"  # Default info icon
        icon_color = get_color("info")

        if self.message_type == MessageType.WARNING:
            icon_text = "⚠️"
            icon_color = get_color("warning")
        elif self.message_type == MessageType.ERROR:
            icon_text = "❌"
            icon_color = get_color("error")
        elif self.message_type == MessageType.SUCCESS:
            icon_text = "✓"
            icon_color = get_color("success")

        icon_label = ttk.Label(icon_frame, text=icon_text, font=("", 24))
        icon_label.pack(padx=5, pady=5)

        # Create message content
        message_frame = ttk.Frame(body)
        message_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Main message
        message_label = ttk.Label(
            message_frame,
            text=self.message,
            wraplength=350,
            justify=tk.LEFT,
            font=("", 10, "bold")
        )
        message_label.pack(anchor=tk.W, pady=(5, 10))

        # Detail message if provided
        if self.detail:
            detail_frame = ttk.Frame(message_frame)
            detail_frame.pack(fill=tk.BOTH, expand=True)

            detail_text = tk.Text(
                detail_frame,
                wrap=tk.WORD,
                width=40,
                height=8,
                padx=5,
                pady=5,
                borderwidth=1,
                relief=tk.SUNKEN,
                font=("", 9)
            )
            detail_text.insert(tk.END, self.detail)
            detail_text.config(state=tk.DISABLED)  # Make read-only

            scrollbar = ttk.Scrollbar(detail_frame, command=detail_text.yview)
            detail_text.config(yscrollcommand=scrollbar.set)

            detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        return body

    def _create_buttons(self) -> ttk.Frame:
        """Create dialog buttons.

        Returns:
            ttk.Frame: The button frame
        """
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Create OK button
        ok_btn = ttk.Button(
            button_frame,
            text="OK",
            command=self._on_ok,
            width=10
        )
        ok_btn.pack(side=tk.RIGHT, padx=5)

        return button_frame

    def _validate(self) -> bool:
        """Validation not needed for message dialogs."""
        return True

    def _apply(self) -> None:
        """Apply not needed for message dialogs."""
        pass

    def _on_ok(self) -> None:
        """Handle OK button click."""
        if self.callback:
            self.callback()
        self._dismiss(True)

    @staticmethod
    def show_message(parent: tk.Widget, title: str, message: str,
                     message_type: str = MessageType.INFO,
                     detail: Optional[str] = None,
                     size: tuple = (450, 250)) -> None:
        """Show a message dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Primary message to display
            message_type: Type of message (info, warning, error, success)
            detail: Optional detailed message
            size: Dialog size (width, height)
        """
        dialog = MessageDialog(parent, title, message, message_type, detail, None, size)
        dialog.transient(parent)
        dialog.grab_set()
        parent.wait_window(dialog)

    @staticmethod
    def show_info(parent: tk.Widget, title: str, message: str, detail: Optional[str] = None,
                  size: tuple = (450, 200)) -> None:
        """Show an information message.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Primary message to display
            detail: Optional detailed message
            size: Dialog size (width, height)
        """
        MessageDialog.show_message(parent, title, message, MessageType.INFO, detail, size)

    @staticmethod
    def show_warning(parent: tk.Widget, title: str, message: str, detail: Optional[str] = None,
                     size: tuple = (450, 200)) -> None:
        """Show a warning message.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Primary message to display
            detail: Optional detailed message
            size: Dialog size (width, height)
        """
        MessageDialog.show_message(parent, title, message, MessageType.WARNING, detail, size)

    @staticmethod
    def show_error(parent: tk.Widget, title: str, message: str, detail: Optional[str] = None,
                   size: tuple = (450, 200)) -> None:
        """Show an error message.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Primary message to display
            detail: Optional detailed message
            size: Dialog size (width, height)
        """
        MessageDialog.show_message(parent, title, message, MessageType.ERROR, detail, size)

    @staticmethod
    def show_success(parent: tk.Widget, title: str, message: str, detail: Optional[str] = None,
                     size: tuple = (450, 200)) -> None:
        """Show a success message.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Primary message to display
            detail: Optional detailed message
            size: Dialog size (width, height)
        """
        MessageDialog.show_message(parent, title, message, MessageType.SUCCESS, detail, size)

    @staticmethod
    def show_exception(parent: tk.Widget, title: str, message: str, exception: Exception,
                       size: tuple = (550, 350)) -> None:
        """Show an error message with exception details.

        Args:
            parent: Parent widget
            title: Dialog title
            message: Primary message to display
            exception: Exception object with details
            size: Dialog size (width, height)
        """
        import traceback
        detail = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        MessageDialog.show_error(parent, title, message, detail, size)