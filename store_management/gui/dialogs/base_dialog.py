import tkinter as tk
from tkinter import ttk
from typing import Optional, Tuple


class BaseDialog(tk.Toplevel):
    """Base class for all dialogs in the application"""

    def __init__(
            self,
            parent,
            title: str = "Dialog",
            size: Tuple[int, int] = (400, 300),
            modal: bool = True
    ):
        """
        Initialize base dialog

        Args:
            parent: Parent window
            title: Dialog title
            size: Dialog size as (width, height)
            modal: Whether dialog should be modal
        """
        super().__init__(parent)

        self.title(title)
        self.geometry(f"{size[0]}x{size[1]}")

        if modal:
            self.transient(parent)
            self.grab_set()

        # Create main frame with padding
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Set up standard button frame
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

        # Configure grid
        self.main_frame.columnconfigure(0, weight=1)

        # Protocol handler for window close button
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        # Center dialog on parent
        self.center_on_parent()

    def center_on_parent(self):
        """Center the dialog on its parent window"""
        self.update_idletasks()

        # Get parent and dialog dimensions
        parent = self.master
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()

        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        # Ensure dialog is fully visible
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = max(0, min(x, screen_width - dialog_width))
        y = max(0, min(y, screen_height - dialog_height))

        self.geometry(f"+{x}+{y}")

    def add_button(
            self,
            text: str,
            command,
            side: str = tk.RIGHT,
            width: Optional[int] = None,
            default: bool = False
    ) -> ttk.Button:
        """
        Add a button to the standard button frame

        Args:
            text: Button text
            command: Button command
            side: Pack side (tk.RIGHT or tk.LEFT)
            width: Button width
            default: Whether this is the default button

        Returns:
            The created button
        """
        kwargs = {'text': text, 'command': command}
        if width:
            kwargs['width'] = width

        button = ttk.Button(self.button_frame, **kwargs)
        button.pack(side=side, padx=5)

        if default:
            self.bind('<Return>', lambda e: command())
            button.focus_set()

        return button

    def add_ok_cancel_buttons(
            self,
            ok_text: str = "OK",
            cancel_text: str = "Cancel",
            ok_command=None
    ):
        """Add standard OK and Cancel buttons"""
        if ok_command is None:
            ok_command = self.ok

        self.add_button(cancel_text, self.cancel, tk.RIGHT)
        self.add_button(ok_text, ok_command, tk.RIGHT, default=True)

    def ok(self, event=None):
        """OK button handler"""
        self.destroy()

    def cancel(self, event=None):
        """Cancel button handler"""
        self.destroy()

    def validate(self) -> bool:
        """
        Validate dialog contents
        Override in subclasses to implement validation
        """
        return True