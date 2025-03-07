# gui/dialogs/import_dialog.py
"""
Import dialog for importing data from various file formats.
"""

import logging
import os
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Any, Dict, List, Optional, Callable, Tuple, Union

from gui.base.base_dialog import BaseDialog
from gui.theme import get_color

logger = logging.getLogger(__name__)


class ImportFormat:
    """Class representing available import formats."""
    CSV = "CSV"
    EXCEL = "Excel"
    JSON = "JSON"

    @classmethod
    def extensions(cls) -> Dict[str, List[str]]:
        """Get file extensions for each format.

        Returns:
            Dict[str, List[str]]: Dictionary mapping formats to file extensions
        """
        return {
            cls.CSV: [".csv"],
            cls.EXCEL: [".xlsx", ".xls"],
            cls.JSON: [".json"]
        }

    @classmethod
    def types(cls) -> List[str]:
        """Get all available import formats.

        Returns:
            List[str]: List of import format names
        """
        return [cls.CSV, cls.EXCEL, cls.JSON]


class ImportDialog(BaseDialog):
    """Dialog for configuring and executing data imports."""

    def __init__(self, parent: tk.Widget, title: str,
                 import_callback: Callable[[str, str, Dict[str, Any]], Any],
                 available_formats: Optional[List[str]] = None,
                 data_description: Optional[str] = None,
                 entity_type: Optional[str] = None,
                 size: tuple = (600, 500)):
        """Initialize the import dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            import_callback: Function to call to perform the import
            available_formats: List of available formats, or None for all
            data_description: Optional description of the data being imported
            entity_type: Optional entity type name for the dialog title
            size: Dialog size (width, height)
        """
        self.import_callback = import_callback
        self.available_formats = available_formats or ImportFormat.types()
        self.data_description = data_description or "data"
        self.entity_type = entity_type

        self.format_var = None
        self.filepath_var = None
        self.options = {}
        self.preview_data = None

        # Customize title if entity type is provided
        if entity_type and "Import" not in title:
            title = f"Import {entity_type}"

        # Set dialog size
        self.width, self.height = size

        super().__init__(parent, title)

    def _create_body(self) -> ttk.Frame:
        """Create the dialog body with import configuration controls.

        Returns:
            ttk.Frame: The dialog body frame
        """
        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create file selection frame
        file_frame = ttk.LabelFrame(body, text="Select File")
        file_frame.pack(fill=tk.X, pady=(0, 10))

        file_inner_frame = ttk.Frame(file_frame)
        file_inner_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(file_inner_frame, text="File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.filepath_var = tk.StringVar()
        filepath_entry = ttk.Entry(file_inner_frame, textvariable=self.filepath_var, width=50)
        filepath_entry.grid(row=0, column=1, sticky=tk.W + tk.E, padx=(0, 5))

        browse_btn = ttk.Button(file_inner_frame, text="Browse...", command=self._browse_filepath)
        browse_btn.grid(row=0, column=2, sticky=tk.W)

        file_inner_frame.columnconfigure(1, weight=1)

        # Create format selection frame (auto-detected, but can be overridden)
        format_frame = ttk.LabelFrame(body, text="File Format")
        format_frame.pack(fill=tk.X, pady=(0, 10))

        format_inner_frame = ttk.Frame(format_frame)
        format_inner_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(format_inner_frame, text="Format:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.format_var = tk.StringVar()
        format_combo = ttk.Combobox(format_inner_frame, textvariable=self.format_var,
                                    values=self.available_formats, state="readonly", width=15)
        format_combo.grid(row=0, column=1, sticky=tk.W)

        format_auto_detect = ttk.Label(format_inner_frame, text="(Auto-detected from file extension)")
        format_auto_detect.grid(row=0, column=2, sticky=tk.W, padx=10)

        # Create options frame for format-specific options
        self.options_frame = ttk.LabelFrame(body, text="Import Options")
        self.options_frame.pack(fill=tk.X, pady=(0, 10))

        # Create preview frame
        preview_frame = ttk.LabelFrame(body, text="Data Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True)

        self.preview_text = tk.Text(preview_frame, wrap=tk.NONE, width=60, height=10)
        self.preview_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Add scrollbars to preview
        y_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_text.yview)
        y_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)

        x_scrollbar = ttk.Scrollbar(body, orient=tk.HORIZONTAL, command=self.preview_text.xview)
        x_scrollbar.pack(fill=tk.X, side=tk.BOTTOM)

        self.preview_text.config(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        self.preview_text.insert(tk.END, "Select a file to see data preview")
        self.preview_text.config(state=tk.DISABLED)  # Make read-only

        # Bind events
        self.format_var.trace_add("write", self._on_format_change)
        self.filepath_var.trace_add("write", self._on_filepath_change)

        return body

    def _create_buttons(self) -> ttk.Frame:
        """Create dialog buttons.

        Returns:
            ttk.Frame: The button frame
        """
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Create preview button
        preview_btn = ttk.Button(
            button_frame,
            text="Refresh Preview",
            command=self._preview_data
        )
        preview_btn.pack(side=tk.LEFT, padx=5)

        # Create Import button
        import_btn = ttk.Button(
            button_frame,
            text="Import",
            command=self._on_ok,
            style="Accent.TButton"
        )
        import_btn.pack(side=tk.RIGHT, padx=5)

        # Create Cancel button
        cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

        return button_frame

    def _browse_filepath(self) -> None:
        """Open file dialog to select import filepath."""
        filetypes = []

        for format_name in self.available_formats:
            extensions = ImportFormat.extensions().get(format_name, [])
            ext_string = " ".join(f"*{ext}" for ext in extensions)
            filetypes.append((f"{format_name} files", ext_string))

        filetypes.append(("All files", "*.*"))

        filepath = filedialog.askopenfilename(
            parent=self,
            title=f"Import {self.data_description}",
            filetypes=filetypes
        )

        if filepath:
            self.filepath_var.set(filepath)
            self._detect_format(filepath)
            self._preview_data()

    def _detect_format(self, filepath: str) -> None:
        """Detect format based on file extension.

        Args:
            filepath: Path to the file
        """
        _, ext = os.path.splitext(filepath.lower())

        for format_name, extensions in ImportFormat.extensions().items():
            if ext in extensions and format_name in self.available_formats:
                self.format_var.set(format_name)
                return

        # If no matching format found, default to first available format
        if self.available_formats:
            self.format_var.set(self.available_formats[0])

    def _on_format_change(self, *args) -> None:
        """Handle format selection change."""
        self._update_options_frame()

    def _on_filepath_change(self, *args) -> None:
        """Handle filepath change."""
        filepath = self.filepath_var.get()
        if filepath and os.path.isfile(filepath):
            self._detect_format(filepath)

    def _update_options_frame(self) -> None:
        """Update options frame with format-specific options."""
        # Clear existing options
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        self.options = {}

        selected_format = self.format_var.get()
        options_frame = ttk.Frame(self.options_frame)
        options_frame.pack(fill=tk.X, padx=10, pady=5)

        if selected_format == ImportFormat.CSV:
            self._create_csv_options(options_frame)
        elif selected_format == ImportFormat.EXCEL:
            self._create_excel_options(options_frame)
        elif selected_format == ImportFormat.JSON:
            self._create_json_options(options_frame)

    def _create_csv_options(self, parent: ttk.Frame) -> None:
        """Create options specific to CSV import.

        Args:
            parent: Parent frame for the options
        """
        # Delimiter options
        delimiter_frame = ttk.Frame(parent)
        delimiter_frame.pack(fill=tk.X, pady=5)

        ttk.Label(delimiter_frame, text="Delimiter:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.options["delimiter"] = tk.StringVar(value=",")
        delimiter_combo = ttk.Combobox(delimiter_frame, textvariable=self.options["delimiter"],
                                       values=[",", ";", "\\t", "|", " "], width=5)
        delimiter_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        # Quote options
        ttk.Label(delimiter_frame, text="Quote character:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))

        self.options["quotechar"] = tk.StringVar(value='"')
        quote_combo = ttk.Combobox(delimiter_frame, textvariable=self.options["quotechar"],
                                   values=['"', "'", "`"], width=5)
        quote_combo.grid(row=0, column=3, sticky=tk.W)

        # Header options
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=5)

        self.options["has_header"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(header_frame, text="First row contains column headers",
                        variable=self.options["has_header"]).grid(row=0, column=0, sticky=tk.W)

        # Encoding options
        encoding_frame = ttk.Frame(parent)
        encoding_frame.pack(fill=tk.X, pady=5)

        ttk.Label(encoding_frame, text="Encoding:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.options["encoding"] = tk.StringVar(value="utf-8")
        encoding_combo = ttk.Combobox(encoding_frame, textvariable=self.options["encoding"],
                                      values=["utf-8", "utf-16", "ascii", "latin-1", "iso-8859-1"], width=10)
        encoding_combo.grid(row=0, column=1, sticky=tk.W)

    def _create_excel_options(self, parent: ttk.Frame) -> None:
        """Create options specific to Excel import.

        Args:
            parent: Parent frame for the options
        """
        # Sheet selection
        sheet_frame = ttk.Frame(parent)
        sheet_frame.pack(fill=tk.X, pady=5)

        ttk.Label(sheet_frame, text="Sheet:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.options["sheet_name"] = tk.StringVar(value="0")  # Default to first sheet
        sheet_entry = ttk.Entry(sheet_frame, textvariable=self.options["sheet_name"], width=20)
        sheet_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 5))

        ttk.Label(sheet_frame, text="(Sheet name or index, 0 = first sheet)").grid(
            row=0, column=2, sticky=tk.W)

        # Header options
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=5)

        self.options["has_header"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(header_frame, text="First row contains column headers",
                        variable=self.options["has_header"]).grid(row=0, column=0, sticky=tk.W, padx=(0, 20))

        # Skip rows option
        skip_frame = ttk.Frame(parent)
        skip_frame.pack(fill=tk.X, pady=5)

        ttk.Label(skip_frame, text="Skip rows:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.options["skiprows"] = tk.StringVar(value="0")
        skip_entry = ttk.Entry(skip_frame, textvariable=self.options["skiprows"], width=5)
        skip_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 5))

        ttk.Label(skip_frame, text="(Number of rows to skip before reading data)").grid(
            row=0, column=2, sticky=tk.W)

    def _create_json_options(self, parent: ttk.Frame) -> None:
        """Create options specific to JSON import.

        Args:
            parent: Parent frame for the options
        """
        # JSON structure options
        structure_frame = ttk.Frame(parent)
        structure_frame.pack(fill=tk.X, pady=5)

        ttk.Label(structure_frame, text="Data structure:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.options["json_structure"] = tk.StringVar(value="array")
        structure_combo = ttk.Combobox(structure_frame, textvariable=self.options["json_structure"],
                                       values=["array", "object"], width=10)
        structure_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 5))

        ttk.Label(structure_frame, text="(array = list of records, object = nested data)").grid(
            row=0, column=2, sticky=tk.W)

        # Root path option
        path_frame = ttk.Frame(parent)
        path_frame.pack(fill=tk.X, pady=5)

        ttk.Label(path_frame, text="Root path:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.options["root_path"] = tk.StringVar(value="")
        path_entry = ttk.Entry(path_frame, textvariable=self.options["root_path"], width=30)
        path_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 5))

        ttk.Label(path_frame, text="(e.g., 'data.items' or leave empty for root)").grid(
            row=0, column=2, sticky=tk.W)

        # Encoding options
        encoding_frame = ttk.Frame(parent)
        encoding_frame.pack(fill=tk.X, pady=5)

        ttk.Label(encoding_frame, text="Encoding:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.options["encoding"] = tk.StringVar(value="utf-8")
        encoding_combo = ttk.Combobox(encoding_frame, textvariable=self.options["encoding"],
                                      values=["utf-8", "utf-16", "ascii", "latin-1"], width=10)
        encoding_combo.grid(row=0, column=1, sticky=tk.W)

    def _preview_data(self) -> None:
        """Load and display a preview of the data."""
        filepath = self.filepath_var.get()

        if not filepath or not os.path.isfile(filepath):
            return

        try:
            # Enable text widget for editing
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)

            # Read first few lines of the file directly
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                preview_lines = []
                for i, line in enumerate(f):
                    if i >= 10:  # Show first 10 lines
                        break
                    preview_lines.append(line)

            self.preview_text.insert(tk.END, ''.join(preview_lines))

            if len(preview_lines) == 10:
                self.preview_text.insert(tk.END, "\n...\n(Showing first 10 lines)")

            # Disable text widget to make it read-only
            self.preview_text.config(state=tk.DISABLED)

        except Exception as e:
            logger.error(f"Error previewing file: {str(e)}")
            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, f"Error previewing file: {str(e)}")
            self.preview_text.config(state=tk.DISABLED)

    def _validate(self) -> bool:
        """Validate import configuration.

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        filepath = self.filepath_var.get()
        if not filepath:
            self.show_error("Error", "Please select a file to import.")
            return False

        if not os.path.isfile(filepath):
            self.show_error("Error", f"File does not exist: {filepath}")
            return False

        # Format-specific validation
        selected_format = self.format_var.get()

        if selected_format == ImportFormat.CSV:
            delimiter = self.options.get("delimiter", tk.StringVar()).get()
            if not delimiter:
                self.show_error("Error", "Delimiter cannot be empty.")
                return False

        elif selected_format == ImportFormat.EXCEL:
            try:
                sheet_name = self.options.get("sheet_name", tk.StringVar()).get()
                if sheet_name.isdigit():
                    sheet_index = int(sheet_name)
                    if sheet_index < 0:
                        raise ValueError("Sheet index must be non-negative")
            except ValueError:
                # Not a number, assume it's a sheet name
                pass

            try:
                skiprows = int(self.options.get("skiprows", tk.StringVar()).get())
                if skiprows < 0:
                    self.show_error("Error", "Skip rows must be a non-negative integer.")
                    return False
            except ValueError:
                self.show_error("Error", "Skip rows must be a valid integer.")
                return False

        return True

    def _apply(self) -> None:
        """Apply the import configuration by calling the import callback."""
        try:
            filepath = self.filepath_var.get()
            format_type = self.format_var.get()

            # Convert option variables to a regular dictionary
            options_dict = {}
            for key, var in self.options.items():
                if isinstance(var, (tk.StringVar, tk.IntVar, tk.DoubleVar, tk.BooleanVar)):
                    options_dict[key] = var.get()

            # Special handling for certain options
            if format_type == ImportFormat.CSV:
                # Handle escaped tab character
                if options_dict.get("delimiter") == "\\t":
                    options_dict["delimiter"] = "\t"

            # Call the import callback
            result = self.import_callback(filepath, format_type, options_dict)

            if result is not None:
                logger.info(f"Successfully imported {self.data_description} from {filepath}")
            else:
                logger.error(f"Failed to import {self.data_description} from {filepath}")
                self.show_error("Import Error", f"Failed to import {self.data_description}.")
        except Exception as e:
            logger.error(f"Error during import: {str(e)}")
            self.show_error("Import Error", f"An error occurred during import: {str(e)}")
            raise

    def show_error(self, title: str, message: str) -> None:
        """Show an error message.

        Args:
            title: Dialog title
            message: Error message
        """
        from tkinter import messagebox
        messagebox.showerror(title, message, parent=self)

    @staticmethod
    def show_dialog(parent: tk.Widget,
                    title: str = "Import Data",
                    entity_type: Optional[str] = None,
                    available_formats: Optional[List[str]] = None,
                    data_description: Optional[str] = None,
                    size: tuple = (600, 500)) -> Optional[Any]:
        """Show an import dialog and return the result.

        Args:
            parent: Parent widget
            title: Dialog title
            entity_type: Optional entity type name
            available_formats: List of available formats, or None for all
            data_description: Optional description of the data being imported
            size: Dialog size (width, height)

        Returns:
            The imported data if successful, None if cancelled or failed
        """
        # Create a variable to hold the result
        import_result = None

        # Define callback
        def on_import(filepath, format_type, options):
            nonlocal import_result
            try:
                # Import the data (simplified for this example)
                if format_type == ImportFormat.CSV:
                    import csv
                    delimiter = options.get('delimiter', ',')
                    if delimiter == '\\t':
                        delimiter = '\t'

                    has_header = options.get('has_header', True)

                    with open(filepath, 'r', newline='', encoding=options.get('encoding', 'utf-8')) as f:
                        if has_header:
                            reader = csv.DictReader(f, delimiter=delimiter)
                            import_result = list(reader)
                        else:
                            reader = csv.reader(f, delimiter=delimiter)
                            rows = list(reader)
                            headers = [f"Column{i + 1}" for i in range(len(rows[0]) if rows else 0)]
                            import_result = [dict(zip(headers, row)) for row in rows]

                elif format_type == ImportFormat.EXCEL:
                    try:
                        import pandas as pd
                        sheet_name = options.get('sheet_name', 0)
                        has_header = options.get('has_header', True)
                        skiprows = int(options.get('skiprows', 0))

                        if sheet_name.isdigit():
                            sheet_name = int(sheet_name)

                        df = pd.read_excel(
                            filepath,
                            sheet_name=sheet_name,
                            header=0 if has_header else None,
                            skiprows=skiprows
                        )

                        if not has_header:
                            df.columns = [f"Column{i + 1}" for i in range(len(df.columns))]

                        import_result = df.to_dict('records')
                    except ImportError:
                        from tkinter import messagebox
                        messagebox.showerror("Import Error", "Pandas is required for Excel import.", parent=parent)
                        return None

                elif format_type == ImportFormat.JSON:
                    import json
                    with open(filepath, 'r', encoding=options.get('encoding', 'utf-8')) as f:
                        data = json.load(f)

                    # Handle different JSON structures
                    json_structure = options.get('json_structure', 'array')
                    root_path = options.get('root_path', '')

                    if root_path:
                        parts = root_path.split('.')
                        for part in parts:
                            if part in data:
                                data = data[part]
                            else:
                                return None

                    if json_structure == 'array':
                        if isinstance(data, list):
                            import_result = data
                        else:
                            from tkinter import messagebox
                            messagebox.showerror("Import Error", "JSON data is not an array.", parent=parent)
                            return None
                    else:  # object
                        if isinstance(data, dict):
                            # Convert to list of key-value pairs
                            import_result = [{"key": k, "value": v} for k, v in data.items()]
                        else:
                            from tkinter import messagebox
                            messagebox.showerror("Import Error", "JSON data is not an object.", parent=parent)
                            return None

                else:
                    from tkinter import messagebox
                    messagebox.showerror("Import Error", f"Import format {format_type} not implemented.", parent=parent)
                    return None

                return import_result

            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Import Error", str(e), parent=parent)
                return None

        # Create and show the dialog
        dialog = ImportDialog(
            parent,
            title=title,
            import_callback=on_import,
            available_formats=available_formats,
            data_description=data_description,
            entity_type=entity_type,
            size=size
        )

        # Return the result (None if cancelled or failed)
        return import_result