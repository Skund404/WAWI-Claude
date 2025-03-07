"""
Base dialog for all application dialogs.
Provides common functionality and standardized layout.
"""
import logging
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger(__name__)


class BaseDialog(tk.Toplevel):
    """
    Base class for all application dialogs.
    
    This class provides common functionality and a standardized layout
    for all dialogs in the application. It handles result management,
    window positioning, and other shared behaviors.
    
    Subclasses should override _create_body to implement their specific
    UI elements and _validate to perform input validation.
    """
    
    def __init__(self, parent, title, size=(400, 300), modal=True, 
                 resizable=(True, True), close_on_escape=True):
        """
        Initialize the base dialog with common structure and functionality.
        
        Args:
            parent (tk.Widget): Parent widget
            title (str): Dialog title
            size (tuple): Default size as (width, height)
            modal (bool): Whether the dialog should be modal
            resizable (tuple): Whether the dialog is resizable in (x, y)
            close_on_escape (bool): Whether to close the dialog on Escape key
        """
        super().__init__(parent)
        
        # Configure dialog properties
        self.title(title)
        self.geometry(f"{size[0]}x{size[1]}")
        self.resizable(resizable[0], resizable[1])
        self.minsize(size[0] // 2, size[1] // 2)
        
        # Make the dialog modal if requested
        if modal:
            self.transient(parent)
            self.grab_set()
        
        # Initialize result
        self.result = None
        
        # Configure dialog layout
        self._configure_layout()
        
        # Create dialog contents
        self._create_body()
        self._create_buttons()
        
        # Bind events
        if close_on_escape:
            self.bind("<Escape>", self._on_cancel)
        
        # Center the dialog
        self._center_dialog()
        
        # Set focus and initialize validation
        self._set_initial_focus()
        
        # Protocol for closing the dialog
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Wait for visibility and set focus again
        self.wait_visibility()
        self.initial_focus.focus_set()
        
        # Wait for dialog to be dismissed
        if modal:
            self.wait_window(self)
        
        logger.debug(f"Initialized dialog: {self.__class__.__name__}")
    
    def _configure_layout(self):
        """Configure the dialog layout."""
        # Create main frames
        self.body_frame = ttk.Frame(self, padding=10)
        self.button_frame = ttk.Frame(self, padding=(10, 0, 10, 10))
        
        # Pack frames
        self.body_frame.pack(fill=tk.BOTH, expand=True)
        self.button_frame.pack(fill=tk.X, pady=5)
    
    def _create_body(self):
        """
        Create the dialog body.
        
        This method should be overridden by subclasses to create
        dialog-specific content.
        """
        # Default empty body with a label
        ttk.Label(self.body_frame, 
                 text="Dialog content should be implemented in subclasses").pack(
                     fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # By default, set focus to the first child of the body frame
        self.initial_focus = self.body_frame
    
    def _create_buttons(self):
        """Create standard OK and Cancel buttons."""
        # Create buttons
        self.ok_button = ttk.Button(self.button_frame, text="OK", 
                                   command=self._on_ok, default=tk.ACTIVE,
                                   style="Primary.TButton")
        self.cancel_button = ttk.Button(self.button_frame, text="Cancel", 
                                       command=self._on_cancel)
        
        # Pack buttons
        self.cancel_button.pack(side=tk.RIGHT, padx=(5, 0))
        self.ok_button.pack(side=tk.RIGHT)
        
        # Bind Enter key to OK button
        self.bind("<Return>", lambda event: self._on_ok())
    
    def _validate(self):
        """
        Validate dialog input.
        
        This method should be overridden by subclasses to validate
        dialog-specific input.
        
        Returns:
            bool: True if input is valid, False otherwise
        """
        return True
    
    def _apply(self):
        """
        Apply dialog changes.
        
        This method should be overridden by subclasses to apply
        dialog-specific changes.
        """
        pass
    
    def _set_initial_focus(self):
        """
        Set the initial focus.
        
        Subclasses can override this to set focus to a specific widget.
        """
        self.initial_focus = self.body_frame
    
    def _on_ok(self, event=None):
        """
        Handle OK button click.
        
        Validates input, applies changes if valid, and closes the dialog.
        
        Args:
            event: Optional event that triggered the OK action
        """
        # Validate the input
        if not self._validate():
            # If validation failed, keep focus on the dialog
            self.initial_focus.focus_set()
            return
        
        # Remove focus to trigger any pending validation
        self.focus_set()
        
        # Apply changes
        self._apply()
        
        # Close the dialog
        self._dismiss(True)
    
    def _on_cancel(self, event=None):
        """
        Handle Cancel button click.
        
        Discards changes and closes the dialog.
        
        Args:
            event: Optional event that triggered the Cancel action
        """
        # Close the dialog without applying changes
        self._dismiss(False)
    
    def _dismiss(self, ok):
        """
        Dismiss the dialog.
        
        Args:
            ok (bool): Whether the dialog was confirmed (True) or cancelled (False)
        """
        # Set the result based on the value of ok
        self.result = ok
        
        # Release the dialog grab and destroy the window
        self.grab_release()
        self.destroy()
    
    def _center_dialog(self):
        """Center the dialog on its parent window."""
        self.update_idletasks()
        
        # Get sizes and positions
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        
        # Calculate position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        # Ensure dialog is visible on screen
        x = max(0, min(x, self.winfo_screenwidth() - dialog_width))
        y = max(0, min(y, self.winfo_screenheight() - dialog_height))
        
        # Set position
        self.geometry(f"+{x}+{y}")
    
    def show(self):
        """
        Show the dialog and return the result.
        
        Returns:
            bool: True if confirmed, False if cancelled
        """
        self.wait_window()
        return self.result


class FormDialog(BaseDialog):
    """
    Base class for form-based dialogs.
    
    This class extends BaseDialog with form-specific functionality
    such as field validation, error highlighting, and form submission.
    """
    
    def __init__(self, parent, title, size=(500, 400), 
                 fields=None, data=None, callback=None):
        """
        Initialize a form dialog.
        
        Args:
            parent (tk.Widget): Parent widget
            title (str): Dialog title
            size (tuple): Default size as (width, height)
            fields (dict): Dictionary of field definitions
            data (dict): Initial data for the fields
            callback (callable): Function to call with form data when submitted
        """
        self.fields = fields or {}
        self.field_widgets = {}
        self.data = data or {}
        self.callback = callback
        self.errors = {}
        
        super().__init__(parent, title, size=size)
    
    def _create_body(self):
        """Create the form body with fields defined in self.fields."""
        # Create a canvas with scrollbar for large forms
        canvas = tk.Canvas(self.body_frame, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.body_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create fields
        row = 0
        for field_name, field_def in self.fields.items():
            field_type = field_def.get('type', 'string')
            label_text = field_def.get('label', field_name.replace('_', ' ').title())
            required = field_def.get('required', False)
            readonly = field_def.get('readonly', False)
            help_text = field_def.get('help', '')
            
            # Add a required indicator if applicable
            if required:
                label_text += " *"
            
            # Create label
            label = ttk.Label(scrollable_frame, text=label_text)
            label.grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
            
            # Create widget based on field type
            widget = self._create_field_widget(scrollable_frame, field_name, field_type, field_def)
            widget.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=5)
            
            # Store the widget for later access
            self.field_widgets[field_name] = widget
            
            # Set initial value if provided
            if field_name in self.data:
                self._set_field_value(widget, field_type, self.data[field_name])
            
            # Make readonly if applicable
            if readonly:
                self._set_field_readonly(widget, field_type)
            
            # Add help text if provided
            if help_text:
                help_label = ttk.Label(scrollable_frame, text=help_text, 
                                      foreground="gray", font=("", 8))
                help_label.grid(row=row+1, column=1, sticky=tk.W, padx=5)
                row += 1
            
            row += 1
        
        # Configure grid
        scrollable_frame.columnconfigure(1, weight=1)
        
        # Set initial focus to the first field
        if self.field_widgets:
            self.initial_focus = next(iter(self.field_widgets.values()))
    
    def _create_field_widget(self, parent, field_name, field_type, field_def):
        """
        Create a widget for a field based on its type.
        
        Args:
            parent: Parent widget
            field_name: Field name
            field_type: Field type
            field_def: Field definition dictionary
            
        Returns:
            The created widget
        """
        if field_type == 'string':
            var = tk.StringVar()
            widget = ttk.Entry(parent, textvariable=var)
            widget.var = var
            return widget
        
        elif field_type == 'text':
            widget = tk.Text(parent, height=5, width=30)
            return widget
        
        elif field_type == 'boolean':
            var = tk.BooleanVar()
            widget = ttk.Checkbutton(parent, variable=var)
            widget.var = var
            return widget
        
        elif field_type == 'choice':
            var = tk.StringVar()
            choices = field_def.get('choices', [])
            widget = ttk.Combobox(parent, textvariable=var, values=choices, state="readonly")
            widget.var = var
            return widget
        
        elif field_type == 'date':
            var = tk.StringVar()
            widget = ttk.Entry(parent, textvariable=var)
            widget.var = var
            # A real implementation would use a date picker here
            return widget
        
        elif field_type == 'number':
            var = tk.StringVar()
            widget = ttk.Spinbox(parent, textvariable=var, from_=field_def.get('min', 0),
                               to=field_def.get('max', 100), increment=field_def.get('step', 1))
            widget.var = var
            return widget
        
        else:
            # Default to string input
            var = tk.StringVar()
            widget = ttk.Entry(parent, textvariable=var)
            widget.var = var
            return widget
    
    def _set_field_value(self, widget, field_type, value):
        """
        Set the value of a field widget.
        
        Args:
            widget: Field widget
            field_type: Field type
            value: Value to set
        """
        if field_type == 'text':
            # Clear existing text and insert new value
            widget.delete(1.0, tk.END)
            if value is not None:
                widget.insert(1.0, str(value))
        elif field_type == 'boolean':
            widget.var.set(bool(value))
        else:
            # For most widgets, setting the StringVar is sufficient
            if hasattr(widget, 'var'):
                widget.var.set(str(value) if value is not None else "")
    
    def _get_field_value(self, widget, field_type):
        """
        Get the value from a field widget.
        
        Args:
            widget: Field widget
            field_type: Field type
            
        Returns:
            The field value
        """
        if field_type == 'text':
            return widget.get(1.0, tk.END).strip()
        elif field_type == 'boolean':
            return widget.var.get()
        elif field_type == 'number':
            try:
                return float(widget.var.get())
            except ValueError:
                return 0
        else:
            # For most widgets, getting the StringVar is sufficient
            if hasattr(widget, 'var'):
                return widget.var.get()
            return None
    
    def _set_field_readonly(self, widget, field_type):
        """
        Set a field widget to readonly.
        
        Args:
            widget: Field widget
            field_type: Field type
        """
        if field_type == 'text':
            widget.configure(state=tk.DISABLED)
        elif field_type == 'boolean':
            widget.configure(state=tk.DISABLED)
        elif field_type == 'choice':
            widget.configure(state="readonly")
        else:
            # For most widgets, disabling the widget is sufficient
            widget.configure(state=tk.DISABLED)
    
    def _validate(self):
        """
        Validate all form fields.
        
        Returns:
            bool: True if all fields are valid, False otherwise
        """
        self.errors = {}
        
        # Validate each field
        for field_name, field_def in self.fields.items():
            field_type = field_def.get('type', 'string')
            required = field_def.get('required', False)
            validator = field_def.get('validator')
            
            widget = self.field_widgets.get(field_name)
            if widget is None:
                continue
            
            value = self._get_field_value(widget, field_type)
            
            # Check required fields
            if required and (value is None or value == ""):
                self.errors[field_name] = "This field is required"
                self._highlight_field_error(widget)
                continue
            
            # Apply custom validator if provided
            if validator and value:
                try:
                    result = validator(value)
                    if result is not True:
                        self.errors[field_name] = result if isinstance(result, str) else "Invalid value"
                        self._highlight_field_error(widget)
                except Exception as e:
                    self.errors[field_name] = str(e)
                    self._highlight_field_error(widget)
        
        return not self.errors
    
    def _highlight_field_error(self, widget):
        """
        Highlight a field with an error.
        
        Args:
            widget: Field widget to highlight
        """
        # In a real implementation, this would set background or border color
        if hasattr(widget, 'configure'):
            widget.configure(background="#ffebee")  # Light red background
    
    def _apply(self):
        """
        Collect form data and pass it to the callback function.
        """
        form_data = {}
        
        # Collect data from each field
        for field_name, field_def in self.fields.items():
            field_type = field_def.get('type', 'string')
            widget = self.field_widgets.get(field_name)
            if widget is None:
                continue
            
            form_data[field_name] = self._get_field_value(widget, field_type)
        
        # Call the callback with the form data
        if self.callback:
            try:
                self.callback(form_data)
            except Exception as e:
                logger.error(f"Error in form callback: {e}")
                raise
