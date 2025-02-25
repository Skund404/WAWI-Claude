# relative/path/base_dialog.py
"""
Base Dialog module providing a foundational dialog class for the application.

This module defines a BaseDialog class that serves as a template for creating
standardized dialog windows with common functionality like centering, 
modal support, and standard button layouts.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Tuple, Union, Any

from di.core import inject
from services.interfaces import MaterialService
from utils.logging import get_logger

logger = get_logger(__name__)


class BaseDialog(tk.Toplevel):
    """
    Base class for creating standardized dialog windows in the application.

    Provides common dialog functionality:
    - Centered positioning
    - Standardized button layout
    - Modal window support
    - Basic validation mechanism

    Attributes:
        parent (Union[tk.Tk, tk.Toplevel]): Parent window
        title (str): Dialog title
        size (Optional[Tuple[int, int]]): Optional dialog size
        modal (bool): Whether the dialog should block parent window interaction
    """

    @inject(MaterialService)
    def __init__(
            self,
            parent: Union[tk.Tk, tk.Toplevel],
            title: str = 'Dialog',
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
        try:
            super().__init__(parent)

            # Configure basic dialog properties
            self.title(title)
            self.resizable(False, False)

            # Set dialog size if provided
            if size:
                self.geometry(f'{size[0]}x{size[1]}')

            # Configure modal behavior
            if modal:
                self.transient(parent)
                self.grab_set()

            # Center dialog on parent
            self._center_on_parent()

            # Create main content frames
            self._create_main_frame()
            self._create_button_frame()

        except Exception as e:
            logger.error(f"Error initializing BaseDialog: {e}")
            tk.messagebox.showerror("Initialization Error", str(e))
            self.destroy()

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
        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(padx=10, pady=10, fill=tk.X)
        self.add_ok_cancel_buttons()

    def add_ok_cancel_buttons(
            self,
            ok_text: str = 'OK',
            cancel_text: str = 'Cancel',
            ok_command: Optional[Callable] = None
    ) -> None:
        """
        Add standard OK and Cancel buttons to the dialog.

        Args:
            ok_text: Text for the OK button
            cancel_text: Text for the Cancel button
            ok_command: Optional custom command for OK button
        """
        # Cancel button
        cancel_btn = ttk.Button(
            self.button_frame,
            text=cancel_text,
            command=self._cancel
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

        # OK button
        ok_cmd = ok_command or self._ok
        ok_btn = ttk.Button(
            self.button_frame,
            text=ok_text,
            command=ok_cmd
        )
        ok_btn.pack(side=tk.RIGHT)

        # Bind keyboard shortcuts
        self.bind('<Return>', lambda e: ok_cmd())
        self.bind('<Escape>', lambda e: self._cancel())

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
        try:
            button = ttk.Button(
                self.button_frame,
                text=text,
                command=command,
                width=width
            )
            button.pack(side=side, padx=5)

            if default:
                button.bind('<Return>', command)
                button.focus_set()

            return button
        except Exception as e:
            logger.error(f"Error adding button: {e}")
            tk.messagebox.showerror("Button Creation Error", str(e))
            raise

    def _center_on_parent(self) -> None:
        """
        Center the dialog on its parent window.
        """
        try:
            self.update_idletasks()

            # Get parent window dimensions
            parent_width = self.master.winfo_width()
            parent_height = self.master.winfo_height()
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

        except Exception as e:
            logger.warning(f"Could not center dialog: {e}")
            # Fallback to default positioning

    def _ok(self, event: Optional[tk.Event] = None) -> None:
        """
        Standard OK button handler.
        Subclasses should override to add specific validation logic.

        Args:
            event: Optional tkinter event
        """
        try:
            # Perform validation
            if self.validate():
                self.destroy()
        except Exception as e:
            logger.error(f"Error in OK handler: {e}")
            tk.messagebox.showerror("Validation Error", str(e))

    def _cancel(self, event: Optional[tk.Event] = None) -> None:
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


# Optional: Add module-level testing if imported directly
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    dialog = BaseDialog(
        root,
        title='Test Base Dialog',
        size=(400, 300)
    )
    root.mainloop()