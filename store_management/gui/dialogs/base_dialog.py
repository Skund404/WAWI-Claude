# File: store_management/gui/dialogs/base_dialog.py
# Description: Base Dialog Class for Consistent Dialog Implementation

import tkinter as tk
import tkinter.ttk as ttk
from typing import Optional, Tuple, Callable


class BaseDialog(tk.Toplevel):
    """
    Base class for all dialog windows in the application.

    Provides common dialog functionality:
    - Centered positioning
    - Standardized button layout
    - Modal window support
    - Basic validation mechanism

    Attributes:
        parent (tk.Tk or tk.Toplevel): Parent window
        title (str): Dialog title
        size (Optional[Tuple[int, int]]): Optional dialog size
        modal (bool): Whether the dialog should be modal
    """

    def __init__(
            self,
            parent: tk.Tk | tk.Toplevel,
            title: str = "Dialog",
            size: Optional[Tuple[int, int]] = None,
            modal: bool = True
    ):
        """
        Initialize the base dialog.

        Args:
            parent: Parent window
            title: Dialog title
            size: Optional dialog size (width, height)
            modal: Whether the dialog should block parent window interaction
        """
        # Initialize Toplevel window
        super().__init__(parent)

        # Set dialog properties
        self.title(title)
        self.resizable(False, False)

        # Set dialog size if provided
        if size:
            self.geometry(f"{size[0]}x{size[1]}")

        # Configure modal behavior
        if modal:
            self.transient(parent)
            self.grab_set()

        # Center the dialog on the screen
        self.center_on_parent()

        # Create standard dialog components
        self._create_main_frame()
        self._create_button_frame()

    def _create_main_frame(self) -> None:
        """
        Create the main content frame for dialog content.
        Subclasses should override and add specific content.
        """
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def _create_button_frame(self) -> None:
        """
        Create a standard button frame with OK and Cancel buttons.
        """
        # Button frame
        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(padx=10, pady=10, fill=tk.X)

        # Add standard buttons
        self.add_ok_cancel_buttons()

    def add_ok_cancel_buttons(
            self,
            ok_text: str = "OK",
            cancel_text: str = "Cancel",
            ok_command: Optional[Callable] = None
    ) -> None:
        """
        Add standard OK and Cancel buttons to the dialog.

        Args:
            ok_text: Text for the OK button
            cancel_text: Text for the Cancel button
            ok_command: Optional custom command for OK button
        """
        # Cancel button (right-aligned)
        cancel_btn = ttk.Button(
            self.button_frame,
            text=cancel_text,
            command=self.cancel
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

        # OK button (right-aligned, before Cancel)
        ok_btn = ttk.Button(
            self.button_frame,
            text=ok_text,
            command=ok_command or self.ok
        )
        ok_btn.pack(side=tk.RIGHT)

        # Bind Return and Escape keys
        self.bind('<Return>', self.ok)
        self.bind('<Escape>', self.cancel)

    def add_button(
            self,
            text: str,
            command: Callable,
            side: str = tk.RIGHT,
            width: int = 10,
            default: bool = False
    ) -> ttk.Button:
        """
        Add a custom button to the button frame.

        Args:
            text: Button text
            command: Button click command
            side: Side to pack the button (default: right)
            width: Button width
            default: Whether this is the default button

        Returns:
            The created button
        """
        button = ttk.Button(
            self.button_frame,
            text=text,
            command=command,
            width=width
        )
        button.pack(side=side, padx=5)

        # Set default button if specified
        if default:
            button.bind('<Return>', command)

        return button

    def center_on_parent(self) -> None:
        """
        Center the dialog on its parent window.
        """
        # Update window to get correct dimensions
        self.update_idletasks()

        # Get parent window dimensions
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()

        # Get parent window position
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()

        # Get dialog dimensions
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()

        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        # Set dialog position
        self.geometry(f'+{x}+{y}')

    def ok(self, event: Optional[tk.Event] = None) -> None:
        """
        Standard OK button handler.
        Subclasses should override to add specific validation logic.

        Args:
            event: Optional tkinter event
        """
        # Basic validation (override in subclasses)
        validation_result = self.validate()

        if validation_result:
            # Close dialog
            self.destroy()

    def cancel(self, event: Optional[tk.Event] = None) -> None:
        """
        Standard Cancel button handler.

        Args:
            event: Optional tkinter event
        """
        self.destroy()

    def validate(self) -> bool:
        """
        Validate dialog contents before closing.

        Subclasses should override to implement specific validation.

        Returns:
            True if validation passes, False otherwise
        """
        return True