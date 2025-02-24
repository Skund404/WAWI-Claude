

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


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

    @inject(MaterialService)
        def __init__(self, parent: (tk.Tk | tk.Toplevel), title: str = 'Dialog',
                 size: Optional[Tuple[int, int]] = None, modal: bool = True):
        """
        Initialize the base dialog.

        Args:
            parent: Parent window
            title: Dialog title
            size: Optional dialog size (width, height)
            modal: Whether the dialog should block parent window interaction
        """
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        if size:
            self.geometry(f'{size[0]}x{size[1]}')
        if modal:
            self.transient(parent)
            self.grab_set()
        self.center_on_parent()
        self._create_main_frame()
        self._create_button_frame()

        @inject(MaterialService)
            def _create_main_frame(self) -> None:
        """
        Create the main content frame for dialog content.
        Subclasses should override and add specific content.
        """
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        @inject(MaterialService)
            def _create_button_frame(self) -> None:
        """
        Create a standard button frame with OK and Cancel buttons.
        """
        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(padx=10, pady=10, fill=tk.X)
        self.add_ok_cancel_buttons()

        @inject(MaterialService)
            def add_ok_cancel_buttons(self, ok_text: str = 'OK', cancel_text: str =
                                  'Cancel', ok_command: Optional[Callable] = None) -> None:
        """
        Add standard OK and Cancel buttons to the dialog.

        Args:
            ok_text: Text for the OK button
            cancel_text: Text for the Cancel button
            ok_command: Optional custom command for OK button
        """
        cancel_btn = ttk.Button(self.button_frame, text=cancel_text,
                                command=self.cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        ok_btn = ttk.Button(self.button_frame, text=ok_text,
                            command=ok_command or self.ok)
        ok_btn.pack(side=tk.RIGHT)
        self.bind('<Return>', self.ok)
        self.bind('<Escape>', self.cancel)

        @inject(MaterialService)
            def add_button(self, text: str, command: Callable, side: str = tk.RIGHT,
                       width: int = 10, default: bool = False) -> ttk.Button:
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
        button = ttk.Button(self.button_frame, text=text, command=command,
                            width=width)
        button.pack(side=side, padx=5)
        if default:
            button.bind('<Return>', command)
        return button

        @inject(MaterialService)
            def center_on_parent(self) -> None:
        """
        Center the dialog on its parent window.
        """
        self.update_idletasks()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        self.geometry(f'+{x}+{y}')

        @inject(MaterialService)
            def ok(self, event: Optional[tk.Event] = None) -> None:
        """
        Standard OK button handler.
        Subclasses should override to add specific validation logic.

        Args:
            event: Optional tkinter event
        """
        validation_result = self.validate()
        if validation_result:
            self.destroy()

        @inject(MaterialService)
            def cancel(self, event: Optional[tk.Event] = None) -> None:
        """
        Standard Cancel button handler.

        Args:
            event: Optional tkinter event
        """
        self.destroy()

        @inject(MaterialService)
            def validate(self) -> bool:
        """
        Validate dialog contents before closing.

        Subclasses should override to implement specific validation.

        Returns:
            True if validation passes, False otherwise
        """
        return True
