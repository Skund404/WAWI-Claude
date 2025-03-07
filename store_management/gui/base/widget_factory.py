"""
Widget factory for creating consistent UI components.
Provides factory methods for commonly used widgets with standard styling.
"""
import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import re

from gui.theme import AppTheme

logger = logging.getLogger(__name__)


class WidgetFactory:
    """
    Factory class for creating standardized UI widgets.
    
    This class provides methods for creating various widgets with
    consistent styling and behavior across the application.
    """
    
    @staticmethod
    def create_label(parent: tk.Widget, text: str, style: str = "TLabel",
                    font: Optional[Tuple] = None, **kwargs) -> ttk.Label:
        """
        Create a standardized label.
        
        Args:
            parent: Parent widget
            text: Label text
            style: Style to apply
            font: Optional font tuple
            **kwargs: Additional keyword arguments
            
        Returns:
            The created label
        """
        label = ttk.Label(parent, text=text, style=style, **kwargs)
        
        if font:
            label.configure(font=font)
        
        return label
    
    @staticmethod
    def create_button(parent: tk.Widget, text: str, command: Callable = None,
                     style: str = "TButton", width: int = None, **kwargs) -> ttk.Button:
        """
        Create a standardized button.
        
        Args:
            parent: Parent widget
            text: Button text
            command: Button command callback
            style: Style to apply
            width: Optional button width
            **kwargs: Additional keyword arguments
            
        Returns:
            The created button
        """
        button = ttk.Button(parent, text=text, command=command, style=style, **kwargs)
        
        if width:
            button.configure(width=width)
        
        return button
    
    @staticmethod
    def create_entry(parent: tk.Widget, textvariable: Optional[tk.StringVar] = None,
                    width: int = 20, style: str = "TEntry", 
                    validate_command: Optional[Callable] = None,
                    **kwargs) -> ttk.Entry:
        """
        Create a standardized entry field.
        
        Args:
            parent: Parent widget
            textvariable: StringVar for the entry
            width: Entry width
            style: Style to apply
            validate_command: Optional validation command
            **kwargs: Additional keyword arguments
            
        Returns:
            The created entry
        """
        if textvariable is None:
            textvariable = tk.StringVar()
        
        entry = ttk.Entry(parent, textvariable=textvariable, width=width, style=style, **kwargs)
        
        if validate_command:
            # Set up validation
            vcmd = parent.register(validate_command)
            entry.configure(validate="key", validatecommand=(vcmd, '%P'))
        
        return entry
    
    @staticmethod
    def create_combobox(parent: tk.Widget, values: List[str],
                       textvariable: Optional[tk.StringVar] = None,
                       state: str = "readonly", width: int = 20,
                       style: str = "TCombobox", **kwargs) -> ttk.Combobox:
        """
        Create a standardized combobox.
        
        Args:
            parent: Parent widget
            values: List of values for the combobox
            textvariable: StringVar for the combobox
            state: Combobox state ("readonly" or "normal")
            width: Combobox width
            style: Style to apply
            **kwargs: Additional keyword arguments
            
        Returns:
            The created combobox
        """
        if textvariable is None:
            textvariable = tk.StringVar()
        
        combobox = ttk.Combobox(
            parent,
            textvariable=textvariable,
            values=values,
            state=state,
            width=width,
            style=style,
            **kwargs
        )
        
        # Set initial value if none is set
        if not textvariable.get() and values:
            textvariable.set(values[0])
        
        return combobox
    
    @staticmethod
    def create_treeview(parent: tk.Widget, columns: List[str],
                       column_widths: Dict[str, int] = None,
                       headings: Dict[str, str] = None,
                       sortable: bool = True,
                       height: int = 10,
                       style: str = "Treeview",
                       **kwargs) -> ttk.Treeview:
        """
        Create a standardized treeview.
        
        Args:
            parent: Parent widget
            columns: List of column IDs
            column_widths: Dictionary of column IDs to widths
            headings: Dictionary of column IDs to heading texts
            sortable: Whether the treeview should be sortable
            height: Number of rows to display
            style: Style to apply
            **kwargs: Additional keyword arguments
            
        Returns:
            The created treeview
        """
        # Create treeview
        treeview = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",  # Don't show the first empty column
            height=height,
            style=style,
            **kwargs
        )
        
        # Default widths and headings if not provided
        if column_widths is None:
            column_widths = {}
        
        if headings is None:
            headings = {col: col.replace('_', ' ').title() for col in columns}
        
        # Configure columns
        for col in columns:
            width = column_widths.get(col, 100)
            heading = headings.get(col, col.replace('_', ' ').title())
            
            treeview.column(col, width=width, anchor="w")
            treeview.heading(col, text=heading)
        
        # Create scrollbars
        vsb = ttk.Scrollbar(parent, orient="vertical", command=treeview.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=treeview.xview)
        treeview.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout for treeview and scrollbars
        treeview.grid(column=0, row=0, sticky="nsew")
        vsb.grid(column=1, row=0, sticky="ns")
        hsb.grid(column=0, row=1, sticky="ew")
        
        # Configure grid weights
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        
        # Make sortable if requested
        if sortable:
            # Setup sorting variables
            treeview.sort_column = None
            treeview.sort_reverse = False
            
            # Add click handlers to column headings
            for col in columns:
                treeview.heading(
                    col, 
                    command=lambda _col=col: WidgetFactory._sort_treeview(treeview, _col)
                )
        
        return treeview
    
    @staticmethod
    def _sort_treeview(treeview: ttk.Treeview, column: str):
        """
        Sort a treeview by the specified column.
        
        Args:
            treeview: The treeview to sort
            column: Column ID to sort by
        """
        # Toggle sort direction if sorting the same column again
        if treeview.sort_column == column:
            treeview.sort_reverse = not treeview.sort_reverse
        else:
            treeview.sort_column = column
            treeview.sort_reverse = False
        
        # Get all items
        items = [(treeview.set(k, column), k) for k in treeview.get_children('')]
        
        # Sort items
        try:
            # Try to convert to number if possible
            items.sort(
                key=lambda x: WidgetFactory._convert_value(x[0]), 
                reverse=treeview.sort_reverse
            )
        except Exception:
            # Fall back to string sort
            items.sort(key=lambda x: str(x[0]).lower(), reverse=treeview.sort_reverse)
        
        # Rearrange items
        for index, (_, item) in enumerate(items):
            treeview.move(item, '', index)
        
        # Update column headings
        for col in treeview["columns"]:
            # Remove sorting indicator from all columns
            current_text = treeview.heading(col, "text")
            new_text = re.sub(r' [↑↓]$', '', current_text)
            treeview.heading(col, text=new_text)
        
        # Add sorting indicator to the sorted column
        current_text = treeview.heading(column, "text")
        new_text = f"{current_text} {'↓' if treeview.sort_reverse else '↑'}"
        treeview.heading(column, text=new_text)
    
    @staticmethod
    def _convert_value(value: str) -> Any:
        """
        Convert a value for sorting.
        
        Args:
            value: The value to convert
            
        Returns:
            Converted value appropriate for sorting
        """
        if value == '':
            return ''
        
        # Try to convert to numeric types
        try:
            # Try integer first
            return int(value)
        except (ValueError, TypeError):
            try:
                # Then try float
                return float(value)
            except (ValueError, TypeError):
                # If not numeric, return lowercase string for case-insensitive sort
                return str(value).lower()
    
    @staticmethod
    def create_notebook(parent: tk.Widget, style: str = "TNotebook", **kwargs) -> ttk.Notebook:
        """
        Create a standardized notebook.
        
        Args:
            parent: Parent widget
            style: Style to apply
            **kwargs: Additional keyword arguments
            
        Returns:
            The created notebook
        """
        notebook = ttk.Notebook(parent, style=style, **kwargs)
        return notebook
    
    @staticmethod
    def create_frame(parent: tk.Widget, style: str = "TFrame", padding: int = 10,
                    borderwidth: int = 0, relief: str = "flat", **kwargs) -> ttk.Frame:
        """
        Create a standardized frame.
        
        Args:
            parent: Parent widget
            style: Style to apply
            padding: Frame padding
            borderwidth: Frame border width
            relief: Frame relief style
            **kwargs: Additional keyword arguments
            
        Returns:
            The created frame
        """
        frame = ttk.Frame(
            parent,
            style=style,
            padding=padding,
            borderwidth=borderwidth,
            relief=relief,
            **kwargs
        )
        return frame
    
    @staticmethod
    def create_scrolled_frame(parent: tk.Widget, style: str = "TFrame",
                             padding: int = 10, **kwargs) -> Tuple[ttk.Frame, ttk.Frame]:
        """
        Create a scrollable frame.
        
        Args:
            parent: Parent widget
            style: Style to apply
            padding: Frame padding
            **kwargs: Additional keyword arguments
            
        Returns:
            Tuple of (container_frame, scrollable_frame)
        """
        # Create a container frame
        container = ttk.Frame(parent)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        # Create the scrollable frame
        scrollable_frame = ttk.Frame(canvas, style=style, padding=padding, **kwargs)
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Create window in canvas for the frame
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Configure canvas to resize with container
        def configure_canvas(event):
            # Update the width of the canvas window
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", configure_canvas)
        
        # Configure canvas to use scrollbar
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Bind mousewheel events for scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        scrollable_frame.bind_all("<MouseWheel>", _on_mousewheel)
        
        return container, scrollable_frame
    
    @staticmethod
    def create_separator(parent: tk.Widget, orient: str = "horizontal",
                        **kwargs) -> ttk.Separator:
        """
        Create a standardized separator.
        
        Args:
            parent: Parent widget
            orient: Orientation ("horizontal" or "vertical")
            **kwargs: Additional keyword arguments
            
        Returns:
            The created separator
        """
        separator = ttk.Separator(parent, orient=orient, **kwargs)
        return separator
    
    @staticmethod
    def create_checkbox(parent: tk.Widget, text: str, variable: Optional[tk.BooleanVar] = None,
                       command: Optional[Callable] = None, style: str = "TCheckbutton",
                       **kwargs) -> ttk.Checkbutton:
        """
        Create a standardized checkbox.
        
        Args:
            parent: Parent widget
            text: Checkbox text
            variable: BooleanVar for the checkbox
            command: Command to execute when the checkbox is toggled
            style: Style to apply
            **kwargs: Additional keyword arguments
            
        Returns:
            The created checkbox
        """
        if variable is None:
            variable = tk.BooleanVar()
        
        checkbox = ttk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            command=command,
            style=style,
            **kwargs
        )
        
        return checkbox
    
    @staticmethod
    def create_radio_button(parent: tk.Widget, text: str, variable: Optional[tk.Variable] = None,
                           value: Any = None, command: Optional[Callable] = None,
                           style: str = "TRadiobutton", **kwargs) -> ttk.Radiobutton:
        """
        Create a standardized radio button.
        
        Args:
            parent: Parent widget
            text: Radio button text
            variable: Variable for the radio button
            value: Value for the radio button
            command: Command to execute when the radio button is selected
            style: Style to apply
            **kwargs: Additional keyword arguments
            
        Returns:
            The created radio button
        """
        if variable is None:
            variable = tk.StringVar()
        
        radio_button = ttk.Radiobutton(
            parent,
            text=text,
            variable=variable,
            value=value,
            command=command,
            style=style,
            **kwargs
        )
        
        return radio_button
    
    @staticmethod
    def create_spinbox(parent: tk.Widget, from_: int = 0, to: int = 100,
                      textvariable: Optional[tk.StringVar] = None,
                      width: int = 5, style: str = "TSpinbox",
                      **kwargs) -> ttk.Spinbox:
        """
        Create a standardized spinbox.
        
        Args:
            parent: Parent widget
            from_: Minimum value
            to: Maximum value
            textvariable: StringVar for the spinbox
            width: Spinbox width
            style: Style to apply
            **kwargs: Additional keyword arguments
            
        Returns:
            The created spinbox
        """
        if textvariable is None:
            textvariable = tk.StringVar(value=str(from_))
        
        spinbox = ttk.Spinbox(
            parent,
            from_=from_,
            to=to,
            textvariable=textvariable,
            width=width,
            style=style,
            **kwargs
        )
        
        return spinbox
    
    @staticmethod
    def create_progressbar(parent: tk.Widget, mode: str = "determinate",
                          length: int = 100, style: str = "TProgressbar",
                          **kwargs) -> ttk.Progressbar:
        """
        Create a standardized progressbar.
        
        Args:
            parent: Parent widget
            mode: Progressbar mode ("determinate" or "indeterminate")
            length: Progressbar length
            style: Style to apply
            **kwargs: Additional keyword arguments
            
        Returns:
            The created progressbar
        """
        progressbar = ttk.Progressbar(
            parent,
            mode=mode,
            length=length,
            style=style,
            **kwargs
        )
        
        return progressbar
    
    @staticmethod
    def create_scale(parent: tk.Widget, from_: int = 0, to: int = 100,
                    orient: str = "horizontal", variable: Optional[tk.DoubleVar] = None,
                    command: Optional[Callable] = None, style: str = "TScale",
                    **kwargs) -> ttk.Scale:
        """
        Create a standardized scale.
        
        Args:
            parent: Parent widget
            from_: Minimum value
            to: Maximum value
            orient: Orientation ("horizontal" or "vertical")
            variable: DoubleVar for the scale
            command: Command to execute when the scale is adjusted
            style: Style to apply
            **kwargs: Additional keyword arguments
            
        Returns:
            The created scale
        """
        if variable is None:
            variable = tk.DoubleVar(value=from_)
        
        scale = ttk.Scale(
            parent,
            from_=from_,
            to=to,
            orient=orient,
            variable=variable,
            command=command,
            style=style,
            **kwargs
        )
        
        return scale
    
    @staticmethod
    def create_text(parent: tk.Widget, width: int = 40, height: int = 10,
                   wrap: str = "word", **kwargs) -> tk.Text:
        """
        Create a standardized text widget.
        
        Args:
            parent: Parent widget
            width: Text widget width in characters
            height: Text widget height in lines
            wrap: Text wrapping mode ("none", "char", or "word")
            **kwargs: Additional keyword arguments
            
        Returns:
            The created text widget
        """
        text = tk.Text(
            parent,
            width=width,
            height=height,
            wrap=wrap,
            **kwargs
        )
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        
        # Place widgets
        text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure grid weights
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        
        return text
    
    @staticmethod
    def create_status_indicator(parent: tk.Widget, text: str, status: str,
                              width: int = 15, **kwargs) -> ttk.Label:
        """
        Create a status indicator label.
        
        Args:
            parent: Parent widget
            text: Status text
            status: Status type ("success", "warning", "danger", "info")
            width: Label width
            **kwargs: Additional keyword arguments
            
        Returns:
            The created label
        """
        # Map status to style
        status_styles = {
            "success": "Success.TLabel",
            "warning": "Warning.TLabel",
            "danger": "Danger.TLabel",
            "info": "Info.TLabel",
        }
        
        style = status_styles.get(status.lower(), "TLabel")
        
        label = ttk.Label(
            parent,
            text=text,
            style=style,
            width=width,
            anchor="center",
            **kwargs
        )
        
        return label
    
    @staticmethod
    def create_tab(notebook: ttk.Notebook, title: str, padding: int = 10) -> ttk.Frame:
        """
        Create a tab in a notebook.
        
        Args:
            notebook: Notebook widget
            title: Tab title
            padding: Tab content padding
            
        Returns:
            The created frame for the tab
        """
        frame = ttk.Frame(notebook, padding=padding)
        notebook.add(frame, text=title)
        return frame
    
    @staticmethod
    def create_toolbar(parent: tk.Widget, padding: int = 5) -> ttk.Frame:
        """
        Create a toolbar frame.
        
        Args:
            parent: Parent widget
            padding: Toolbar padding
            
        Returns:
            The created toolbar frame
        """
        toolbar = ttk.Frame(parent, style="Toolbar.TFrame", padding=padding)
        return toolbar
    
    @staticmethod
    def create_header(parent: tk.Widget, text: str, 
                     level: int = 1, padding: int = 10) -> ttk.Label:
        """
        Create a header label.
        
        Args:
            parent: Parent widget
            text: Header text
            level: Header level (1-3)
            padding: Header padding
            
        Returns:
            The created header label
        """
        # Map header level to style and font
        header_styles = {
            1: ("Heading.TLabel", AppTheme.FONTS["heading"]),
            2: ("Subheading.TLabel", AppTheme.FONTS["subheading"]),
            3: ("TLabel", AppTheme.FONTS["body"]),
        }
        
        style, font = header_styles.get(level, ("TLabel", AppTheme.FONTS["body"]))
        
        header = ttk.Label(
            parent,
            text=text,
            style=style,
            font=font,
            padding=padding
        )
        
        return header
    
    @staticmethod
    def create_search_bar(parent: tk.Widget, callback: Callable[[str], None], 
                         width: int = 25) -> Tuple[ttk.Frame, tk.StringVar]:
        """
        Create a search bar with a search button.
        
        Args:
            parent: Parent widget
            callback: Function to call with the search text
            width: Entry width
            
        Returns:
            Tuple of (search_frame, search_var)
        """
        # Create search frame
        search_frame = ttk.Frame(parent)
        
        # Create search components
        search_label = ttk.Label(search_frame, text="Search:")
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=width, style="Search.TEntry")
        
        # Add search button
        search_button = ttk.Button(
            search_frame, 
            text="Search",
            command=lambda: callback(search_var.get().strip())
        )
        
        # Add clear button
        clear_button = ttk.Button(
            search_frame, 
            text="Clear",
            command=lambda: [search_var.set(""), callback("")]
        )
        
        # Pack components
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        search_button.pack(side=tk.LEFT, padx=(0, 5))
        clear_button.pack(side=tk.LEFT)
        
        # Bind Enter key to search
        search_entry.bind("<Return>", lambda event: callback(search_var.get().strip()))
        
        return search_frame, search_var
    
    @staticmethod
    def create_filter_bar(parent: tk.Widget, filters: Dict[str, List[str]], 
                        callback: Callable[[Dict[str, str]], None]) -> Tuple[ttk.Frame, Dict[str, tk.StringVar]]:
        """
        Create a filter bar with multiple filter controls.
        
        Args:
            parent: Parent widget
            filters: Dictionary of filter names to lists of options
            callback: Function to call with the filter values
            
        Returns:
            Tuple of (filter_frame, filter_vars)
        """
        # Create filter frame
        filter_frame = ttk.Frame(parent)
        
        # Create filter components for each filter
        filter_vars = {}
        
        for i, (filter_name, options) in enumerate(filters.items()):
            # Create label and combobox
            filter_label = ttk.Label(filter_frame, text=f"{filter_name.replace('_', ' ').title()}:")
            filter_var = tk.StringVar()
            filter_var.set("All")  # Default value
            
            # Add "All" option to the beginning
            filter_options = ["All"] + options
            
            filter_combo = ttk.Combobox(
                filter_frame, 
                textvariable=filter_var,
                values=filter_options,
                state="readonly",
                width=15
            )
            
            # Store the variable for later access
            filter_vars[filter_name] = filter_var
            
            # Pack components
            filter_label.grid(row=0, column=i*2, padx=(10 if i > 0 else 0, 5), sticky=tk.W)
            filter_combo.grid(row=0, column=i*2 + 1, padx=(0, 10), sticky=tk.W)
            
            # Create callback wrapper
            def on_filter_change(event=None, fvars=filter_vars):
                # Collect current filter values (excluding "All")
                active_filters = {}
                for fname, fvar in fvars.items():
                    value = fvar.get()
                    if value != "All":
                        active_filters[fname] = value
                
                # Call the callback with the active filters
                callback(active_filters)
            
            # Bind selection event
            filter_combo.bind("<<ComboboxSelected>>", on_filter_change)
        
        # Add reset button at the end
        reset_button = ttk.Button(
            filter_frame, 
            text="Reset Filters",
            command=lambda: [var.set("All") for var in filter_vars.values()] + [callback({})]
        )
        reset_button.grid(row=0, column=len(filters)*2, padx=(10, 0), sticky=tk.E)
        
        # Configure grid
        filter_frame.columnconfigure(len(filters)*2 + 1, weight=1)
        
        return filter_frame, filter_vars