# gui/dialogs/export_dialog.py
"""
Export dialog for exporting data to various file formats.
"""

import logging
import os
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Any, Dict, List, Optional, Callable, Union

from gui.base.base_dialog import BaseDialog
from gui.theme import get_color

logger = logging.getLogger(__name__)


class ExportFormat:
    """Class representing available export formats."""
    CSV = "CSV"
    EXCEL = "Excel"
    JSON = "JSON"
    HTML = "HTML"
    PDF = "PDF"
    TEXT = "Text"

    @classmethod
    def extensions(cls) -> Dict[str, str]:
        """Get file extensions for each format.

        Returns:
            Dict[str, str]: Dictionary mapping formats to file extensions
        """
        return {
            cls.CSV: ".csv",
            cls.EXCEL: ".xlsx",
            cls.JSON: ".json",
            cls.HTML: ".html",
            cls.PDF: ".pdf",
            cls.TEXT: ".txt"
        }

    @classmethod
    def types(cls) -> List[str]:
        """Get all available export formats.

        Returns:
            List[str]: List of export format names
        """
        return [cls.CSV, cls.EXCEL, cls.JSON, cls.HTML, cls.PDF, cls.TEXT]


class ExportDialog(BaseDialog):
    """Dialog for configuring and executing data exports."""

    def __init__(self, parent: tk.Widget, title: str,
                 data: Union[List[Dict[str, Any]], None],
                 export_callback: Callable[[str, str, Dict[str, Any]], bool],
                 available_formats: Optional[List[str]] = None,
                 data_description: Optional[str] = None,
                 entity_type: Optional[str] = None,
                 size: tuple = (600, 500)):
        """Initialize the export dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            data: Data to export, or None if callback handles data retrieval
            export_callback: Function to call to perform the export
            available_formats: List of available formats, or None for all
            data_description: Optional description of the data being exported
            entity_type: Optional entity type name for the dialog title
            size: Dialog size (width, height)
        """
        self.data = data
        self.export_callback = export_callback
        self.available_formats = available_formats or ExportFormat.types()
        self.data_description = data_description or "data"
        self.entity_type = entity_type

        self.format_var = None
        self.filepath_var = None
        self.options = {}

        # Customize title if entity type is provided
        if entity_type and "Export" not in title:
            title = f"Export {entity_type}"

        # Set dialog size
        self.width, self.height = size

        super().__init__(parent, title)

    def _create_body(self) -> ttk.Frame:
        """Create the dialog body with export configuration controls.

        Returns:
            ttk.Frame: The dialog body frame
        """
        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create format selection frame
        format_frame = ttk.LabelFrame(body, text="Export Format")
        format_frame.pack(fill=tk.X, pady=(0, 10))

        # Format options
        self.format_var = tk.StringVar(value=self.available_formats[0] if self.available_formats else "")
        format_option_frame = ttk.Frame(format_frame)
        format_option_frame.pack(fill=tk.X, padx=10, pady=5)

        for i, format_type in enumerate(self.available_formats):
            ttk.Radiobutton(format_option_frame, text=format_type, variable=self.format_var,
                            value=format_type, command=self._on_format_change).grid(
                row=i // 3, column=i % 3, sticky=tk.W, padx=10, pady=5)

        # Create filepath selection frame
        filepath_frame = ttk.LabelFrame(body, text="Save Location")
        filepath_frame.pack(fill=tk.X, pady=(0, 10))

        filepath_inner_frame = ttk.Frame(filepath_frame)
        filepath_inner_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(filepath_inner_frame, text="File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.filepath_var = tk.StringVar()
        filepath_entry = ttk.Entry(filepath_inner_frame, textvariable=self.filepath_var, width=50)
        filepath_entry.grid(row=0, column=1, sticky=tk.W + tk.E, padx=(0, 5))

        browse_btn = ttk.Button(filepath_inner_frame, text="Browse...", command=self._browse_filepath)
        browse_btn.grid(row=0, column=2, sticky=tk.W)

        filepath_inner_frame.columnconfigure(1, weight=1)

        # Create options frame for format-specific options
        self.options_frame = ttk.LabelFrame(body, text="Export Options")
        self.options_frame.pack(fill=tk.BOTH, expand=True)

        # Initialize with options for the first format
        self._update_options_frame()

        return body

    def _create_buttons(self) -> ttk.Frame:
        """Create dialog buttons.

        Returns:
            ttk.Frame: The button frame
        """
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Create Export button
        export_btn = ttk.Button(
            button_frame,
            text="Export",
            command=self._on_ok,
            style="Accent.TButton"
        )
        export_btn.pack(side=tk.RIGHT, padx=5)

        # Create Cancel button
        cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

        return button_frame

    def _on_format_change(self) -> None:
        """Handle format selection change."""
        self._update_options_frame()
        self._update_default_filepath()

    def _update_options_frame(self) -> None:
        """Update options frame with format-specific options."""
        # Clear existing options
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        self.options = {}

        selected_format = self.format_var.get()
        options_frame = ttk.Frame(self.options_frame)
        options_frame.pack(fill=tk.X, padx=10, pady=5)

        if selected_format == ExportFormat.CSV:
            self._create_csv_options(options_frame)
        elif selected_format == ExportFormat.EXCEL:
            self._create_excel_options(options_frame)
        elif selected_format == ExportFormat.JSON:
            self._create_json_options(options_frame)
        elif selected_format == ExportFormat.HTML:
            self._create_html_options(options_frame)
        elif selected_format == ExportFormat.PDF:
            self._create_pdf_options(options_frame)

    def _create_csv_options(self, parent: ttk.Frame) -> None:
        """Create options specific to CSV export.

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

        # Include headers option
        self.options["include_headers"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="Include column headers",
                        variable=self.options["include_headers"]).pack(anchor=tk.W, pady=5)

        # Encoding options
        encoding_frame = ttk.Frame(parent)
        encoding_frame.pack(fill=tk.X, pady=5)

        ttk.Label(encoding_frame, text="Encoding:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.options["encoding"] = tk.StringVar(value="utf-8")
        encoding_combo = ttk.Combobox(encoding_frame, textvariable=self.options["encoding"],
                                      values=["utf-8", "utf-16", "ascii", "latin-1", "iso-8859-1"], width=10)
        encoding_combo.grid(row=0, column=1, sticky=tk.W)

    def _create_excel_options(self, parent: ttk.Frame) -> None:
        """Create options specific to Excel export.

        Args:
            parent: Parent frame for the options
        """
        # Sheet name option
        sheet_frame = ttk.Frame(parent)
        sheet_frame.pack(fill=tk.X, pady=5)

        ttk.Label(sheet_frame, text="Sheet name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.options["sheet_name"] = tk.StringVar(value="Sheet1")
        sheet_entry = ttk.Entry(sheet_frame, textvariable=self.options["sheet_name"], width=20)
        sheet_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        # Include formatting option
        self.options["include_formatting"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="Include basic formatting (headers, column widths)",
                        variable=self.options["include_formatting"]).pack(anchor=tk.W, pady=5)

        # Include totals row
        self.options["include_totals"] = tk.BooleanVar(value=False)
        ttk.Checkbutton(parent, text="Include totals row",
                        variable=self.options["include_totals"]).pack(anchor=tk.W, pady=5)

        # Create table
        self.options["create_table"] = tk.BooleanVar(value=False)
        ttk.Checkbutton(parent, text="Create Excel table",
                        variable=self.options["create_table"]).pack(anchor=tk.W, pady=5)

    def _create_json_options(self, parent: ttk.Frame) -> None:
        """Create options specific to JSON export.

        Args:
            parent: Parent frame for the options
        """
        # Indentation option
        indent_frame = ttk.Frame(parent)
        indent_frame.pack(fill=tk.X, pady=5)

        ttk.Label(indent_frame, text="Indentation:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.options["indent"] = tk.IntVar(value=2)
        indent_combo = ttk.Combobox(indent_frame, textvariable=self.options["indent"],
                                    values=[0, 2, 4], width=5)
        indent_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        # Format options
        format_frame = ttk.Frame(parent)
        format_frame.pack(fill=tk.X, pady=5)

        ttk.Label(format_frame, text="Format:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.options["format"] = tk.StringVar(value="records")
        format_combo = ttk.Combobox(format_frame, textvariable=self.options["format"],
                                    values=["records", "split", "index", "columns", "values"], width=10)
        format_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 5))

        # Format descriptions
        ttk.Label(format_frame, text="(records: list of objects, split: keys and values, ...)").grid(
            row=0, column=2, sticky=tk.W)

        # Date format
        date_frame = ttk.Frame(parent)
        date_frame.pack(fill=tk.X, pady=5)

        ttk.Label(date_frame, text="Date format:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.options["date_format"] = tk.StringVar(value="iso")
        date_combo = ttk.Combobox(date_frame, textvariable=self.options["date_format"],
                                  values=["iso", "epoch", "string"], width=10)
        date_combo.grid(row=0, column=1, sticky=tk.W)

    def _create_html_options(self, parent: ttk.Frame) -> None:
        """Create options specific to HTML export.

        Args:
            parent: Parent frame for the options
        """
        # Table styling options
        self.options["include_styling"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="Include basic table styling",
                        variable=self.options["include_styling"]).pack(anchor=tk.W, pady=5)

        # Complete HTML document
        self.options["complete_document"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="Create complete HTML document (includes head, body, etc.)",
                        variable=self.options["complete_document"]).pack(anchor=tk.W, pady=5)

        # Include table caption
        caption_frame = ttk.Frame(parent)
        caption_frame.pack(fill=tk.X, pady=5)

        self.options["include_caption"] = tk.BooleanVar(value=False)
        ttk.Checkbutton(caption_frame, text="Include table caption:",
                        variable=self.options["include_caption"]).grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.options["caption_text"] = tk.StringVar(value=f"Exported {self.data_description}")
        caption_entry = ttk.Entry(caption_frame, textvariable=self.options["caption_text"], width=30)
        caption_entry.grid(row=0, column=1, sticky=tk.W)

    def _create_pdf_options(self, parent: ttk.Frame) -> None:
        """Create options specific to PDF export.

        Args:
            parent: Parent frame for the options
        """
        # Page orientation
        orientation_frame = ttk.Frame(parent)
        orientation_frame.pack(fill=tk.X, pady=5)

        ttk.Label(orientation_frame, text="Page orientation:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.options["orientation"] = tk.StringVar(value="portrait")
        ttk.Radiobutton(orientation_frame, text="Portrait", variable=self.options["orientation"],
                        value="portrait").grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        ttk.Radiobutton(orientation_frame, text="Landscape", variable=self.options["orientation"],
                        value="landscape").grid(row=0, column=2, sticky=tk.W)

        # Page size
        size_frame = ttk.Frame(parent)
        size_frame.pack(fill=tk.X, pady=5)

        ttk.Label(size_frame, text="Page size:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.options["page_size"] = tk.StringVar(value="A4")
        size_combo = ttk.Combobox(size_frame, textvariable=self.options["page_size"],
                                  values=["A4", "Letter", "Legal", "Ledger", "A3"], width=10)
        size_combo.grid(row=0, column=1, sticky=tk.W)

        # Include title
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill=tk.X, pady=5)

        self.options["include_title"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(title_frame, text="Include title:",
                        variable=self.options["include_title"]).grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.options["title_text"] = tk.StringVar(value=f"Exported {self.data_description.title()}")
        title_entry = ttk.Entry(title_frame, textvariable=self.options["title_text"], width=30)
        title_entry.grid(row=0, column=1, sticky=tk.W)

        # Include page numbers
        self.options["include_page_numbers"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="Include page numbers",
                        variable=self.options["include_page_numbers"]).pack(anchor=tk.W, pady=5)

        # Include date
        self.options["include_date"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="Include export date",
                        variable=self.options["include_date"]).pack(anchor=tk.W, pady=5)

    def _browse_filepath(self) -> None:
        """Open file dialog to select export filepath."""
        selected_format = self.format_var.get()
        extension = ExportFormat.extensions().get(selected_format, ".txt")

        filetypes = []
        if selected_format == ExportFormat.CSV:
            filetypes = [("CSV files", "*.csv"), ("All files", "*.*")]
        elif selected_format == ExportFormat.EXCEL:
            filetypes = [("Excel files", "*.xlsx"), ("All files", "*.*")]
        elif selected_format == ExportFormat.JSON:
            filetypes = [("JSON files", "*.json"), ("All files", "*.*")]
        elif selected_format == ExportFormat.HTML:
            filetypes = [("HTML files", "*.html"), ("All files", "*.*")]
        elif selected_format == ExportFormat.PDF:
            filetypes = [("PDF files", "*.pdf"), ("All files", "*.*")]
        elif selected_format == ExportFormat.TEXT:
            filetypes = [("Text files", "*.txt"), ("All files", "*.*")]

        filepath = filedialog.asksaveasfilename(
            parent=self,
            title=f"Export {self.data_description} as {selected_format}",
            defaultextension=extension,
            filetypes=filetypes
        )

        if filepath:
            self.filepath_var.set(filepath)

    def _update_default_filepath(self) -> None:
        """Update default filepath based on selected format."""
        current_path = self.filepath_var.get()
        selected_format = self.format_var.get()
        extension = ExportFormat.extensions().get(selected_format, ".txt")

        if not current_path:
            # Set a default filename based on data description
            filename = f"exported_{self.data_description.lower().replace(' ', '_')}{extension}"
            self.filepath_var.set(filename)
        else:
            # Change file extension if format changed
            base_path, _ = os.path.splitext(current_path)
            self.filepath_var.set(f"{base_path}{extension}")

    def _validate(self) -> bool:
        """Validate export configuration.

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        filepath = self.filepath_var.get()
        if not filepath:
            self.show_error("Error", "Please specify a file path.")
            return False

        # Check if directory exists
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            self.show_error("Error", f"Directory does not exist: {directory}")
            return False

        # Validate format-specific options
        selected_format = self.format_var.get()

        if selected_format == ExportFormat.CSV:
            delimiter = self.options.get("delimiter", tk.StringVar()).get()
            if not delimiter:
                self.show_error("Error", "Delimiter cannot be empty.")
                return False

        return True

    def _apply(self) -> None:
        """Apply the export configuration by calling the export callback."""
        try:
            filepath = self.filepath_var.get()
            format_type = self.format_var.get()

            # Convert option variables to a regular dictionary
            options_dict = {}
            for key, var in self.options.items():
                if isinstance(var, (tk.StringVar, tk.IntVar, tk.DoubleVar, tk.BooleanVar)):
                    options_dict[key] = var.get()

            # Call the export callback
            success = self.export_callback(filepath, format_type, options_dict)

            if success:
                logger.info(f"Successfully exported {self.data_description} to {filepath}")
            else:
                logger.error(f"Failed to export {self.data_description} to {filepath}")
                self.show_error("Export Error", f"Failed to export {self.data_description}.")
        except Exception as e:
            logger.error(f"Error during export: {str(e)}")
            self.show_error("Export Error", f"An error occurred during export: {str(e)}")
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
                    data: Union[List[Dict[str, Any]], None],
                    title: str = "Export Data",
                    entity_type: Optional[str] = None,
                    available_formats: Optional[List[str]] = None,
                    data_description: Optional[str] = None,
                    size: tuple = (600, 500)) -> Optional[bool]:
        """Show an export dialog and return the result.

        Args:
            parent: Parent widget
            data: Data to export, or None if callback handles data retrieval
            title: Dialog title
            entity_type: Optional entity type name
            available_formats: List of available formats, or None for all
            data_description: Optional description of the data being exported
            size: Dialog size (width, height)

        Returns:
            True if export was successful, False if failed, None if cancelled
        """
        # Create a variable to hold the result
        export_result = None

        # Define callback
        def on_export(filepath, format_type, options):
            nonlocal export_result
            try:
                # Perform the export (simplified for this example)
                if data is not None:
                    # Export using provided data
                    if format_type == ExportFormat.CSV:
                        import csv
                        with open(filepath, 'w', newline='', encoding=options.get('encoding', 'utf-8')) as f:
                            writer = csv.DictWriter(f, fieldnames=data[0].keys() if data else [])
                            writer.writeheader()
                            writer.writerows(data)
                        export_result = True
                    elif format_type == ExportFormat.EXCEL:
                        try:
                            import pandas as pd
                            df = pd.DataFrame(data)
                            df.to_excel(filepath, index=False)
                            export_result = True
                        except ImportError:
                            messagebox.showerror("Export Error", "Pandas is required for Excel export.", parent=parent)
                            export_result = False
                    elif format_type == ExportFormat.JSON:
                        import json
                        with open(filepath, 'w', encoding=options.get('encoding', 'utf-8')) as f:
                            json.dump(data, f, indent=options.get('indent', 2))
                        export_result = True
                    else:
                        messagebox.showerror("Export Error", f"Export format {format_type} not implemented.",
                                             parent=parent)
                        export_result = False
                else:
                    # In a real implementation, you would call an external function here
                    messagebox.showinfo("Export", "Export would be handled by callback in real implementation.",
                                        parent=parent)
                    export_result = True

                return export_result
            except Exception as e:
                messagebox.showerror("Export Error", str(e), parent=parent)
                export_result = False
                return False

        # Create and show the dialog
        dialog = ExportDialog(
            parent,
            title=title,
            data=data,
            export_callback=on_export,
            available_formats=available_formats,
            data_description=data_description,
            entity_type=entity_type,
            size=size
        )

        # Return the result (None if cancelled)
        return export_result