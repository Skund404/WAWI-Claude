# gui/views/patterns/pattern_export_dialog.py
"""
Dialog for exporting patterns in various formats.

Provides options to export patterns as PDF, SVG, or other formats,
with settings for what components and information to include.
"""

import logging
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Any, Optional

from gui.base.base_dialog import BaseDialog
from gui.theme import COLORS
from gui.utils.service_access import get_service

logger = logging.getLogger(__name__)


class PatternExportDialog(BaseDialog):
    """
    Dialog for exporting patterns in various formats.
    """

    def __init__(self, parent, pattern_id):
        """
        Initialize the pattern export dialog.

        Args:
            parent: The parent widget
            pattern_id: ID of the pattern to export
        """
        self.pattern_id = pattern_id
        self.pattern = None

        # Export options
        self.format_var = None
        self.include_vars = {}
        self.naming_var = None
        self.destination_var = None

        # Call parent constructor
        super().__init__(parent, title="Export Pattern", width=550, height=500)

    def create_layout(self):
        """Create the dialog layout."""
        # Create main content frame
        main_frame = ttk.Frame(self.dialog_frame, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Load pattern data
        self.load_pattern()

        # Create title with pattern name
        title_label = ttk.Label(
            main_frame,
            text=f"Export Pattern: {self.pattern.get('name', '')}",
            font=("TkDefaultFont", 12, "bold")
        )
        title_label.pack(anchor="w", pady=(0, 15))

        # Create options sections
        self.create_format_section(main_frame)
        self.create_include_section(main_frame)
        self.create_naming_section(main_frame)
        self.create_destination_section(main_frame)

        # Create buttons
        button_frame = ttk.Frame(self.dialog_frame)
        button_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        export_btn = ttk.Button(
            button_frame,
            text="Export",
            command=self.on_export
        )
        export_btn.pack(side=tk.RIGHT, padx=(5, 0))

        cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel
        )
        cancel_btn.pack(side=tk.RIGHT)

    def load_pattern(self):
        """Load pattern data from service."""
        try:
            # Get the pattern service
            service = get_service("IPatternService")

            # Get pattern data
            self.pattern = service.get_pattern_by_id(
                self.pattern_id,
                include_components=True,
                include_files=True
            )

            if not self.pattern:
                messagebox.showerror("Error", "Pattern not found.")
                self.on_cancel()
                return
        except Exception as e:
            logger.error(f"Error loading pattern: {str(e)}")
            messagebox.showerror("Error", f"Failed to load pattern: {str(e)}")
            self.on_cancel()

    def create_format_section(self, parent):
        """
        Create the export format section.

        Args:
            parent: The parent widget
        """
        # Create section frame
        section = ttk.LabelFrame(parent, text="Export Format", padding=10)
        section.pack(fill=tk.X, pady=(0, 15))

        # Format selection
        self.format_var = tk.StringVar(value="pdf")

        # PDF option
        pdf_radio = ttk.Radiobutton(
            section,
            text="PDF Document (all components, instructions, and materials list)",
            variable=self.format_var,
            value="pdf"
        )
        pdf_radio.grid(row=0, column=0, sticky="w", pady=2)

        # SVG option
        svg_radio = ttk.Radiobutton(
            section,
            text="SVG Files (separate file for each component)",
            variable=self.format_var,
            value="svg"
        )
        svg_radio.grid(row=1, column=0, sticky="w", pady=2)

        # PNG option
        png_radio = ttk.Radiobutton(
            section,
            text="PNG Images (rasterized pattern pieces)",
            variable=self.format_var,
            value="png"
        )
        png_radio.grid(row=2, column=0, sticky="w", pady=2)

        # ZIP archive option
        zip_radio = ttk.Radiobutton(
            section,
            text="ZIP Archive (all files and formats)",
            variable=self.format_var,
            value="zip"
        )
        zip_radio.grid(row=3, column=0, sticky="w", pady=2)

    def create_include_section(self, parent):
        """
        Create the include options section.

        Args:
            parent: The parent widget
        """
        # Create section frame
        section = ttk.LabelFrame(parent, text="Include in Export", padding=10)
        section.pack(fill=tk.X, pady=(0, 15))

        # Create checkbox grid
        # Column 1
        self.include_vars["components"] = tk.BooleanVar(value=True)
        components_check = ttk.Checkbutton(
            section,
            text="Component Templates",
            variable=self.include_vars["components"]
        )
        components_check.grid(row=0, column=0, sticky="w", padx=(0, 15), pady=2)

        self.include_vars["materials"] = tk.BooleanVar(value=True)
        materials_check = ttk.Checkbutton(
            section,
            text="Materials List",
            variable=self.include_vars["materials"]
        )
        materials_check.grid(row=1, column=0, sticky="w", padx=(0, 15), pady=2)

        self.include_vars["assembly"] = tk.BooleanVar(value=True)
        assembly_check = ttk.Checkbutton(
            section,
            text="Assembly Instructions",
            variable=self.include_vars["assembly"]
        )
        assembly_check.grid(row=2, column=0, sticky="w", padx=(0, 15), pady=2)

        # Column 2
        self.include_vars["dimensions"] = tk.BooleanVar(value=True)
        dimensions_check = ttk.Checkbutton(
            section,
            text="Dimensions",
            variable=self.include_vars["dimensions"]
        )
        dimensions_check.grid(row=0, column=1, sticky="w", pady=2)

        self.include_vars["notes"] = tk.BooleanVar(value=True)
        notes_check = ttk.Checkbutton(
            section,
            text="Notes",
            variable=self.include_vars["notes"]
        )
        notes_check.grid(row=1, column=1, sticky="w", pady=2)

        self.include_vars["attachments"] = tk.BooleanVar(value=True)
        attachments_check = ttk.Checkbutton(
            section,
            text="Attachments & Files",
            variable=self.include_vars["attachments"]
        )
        attachments_check.grid(row=2, column=1, sticky="w", pady=2)

        # Additional options - visible based on format
        self.include_vars["scale_markers"] = tk.BooleanVar(value=True)
        scale_markers_check = ttk.Checkbutton(
            section,
            text="Include scale markers (1cm/1inch squares)",
            variable=self.include_vars["scale_markers"]
        )
        scale_markers_check.grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 2))

        # Create scale frame with entry field
        scale_frame = ttk.Frame(section)
        scale_frame.grid(row=4, column=0, columnspan=2, sticky="w", pady=2)

        ttk.Label(scale_frame, text="Export scale:").pack(side=tk.LEFT)

        self.include_vars["scale"] = tk.StringVar(value="100")
        scale_entry = ttk.Entry(scale_frame, textvariable=self.include_vars["scale"], width=5)
        scale_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(scale_frame, text="% (100% = actual size)").pack(side=tk.LEFT)

    def create_naming_section(self, parent):
        """
        Create the file naming section.

        Args:
            parent: The parent widget
        """
        # Create section frame
        section = ttk.LabelFrame(parent, text="File Naming", padding=10)
        section.pack(fill=tk.X, pady=(0, 15))

        # Naming options
        self.naming_var = tk.StringVar(value="pattern_name")

        # Pattern name option
        name_radio = ttk.Radiobutton(
            section,
            text=f"Pattern name ({self.pattern.get('name', '')})",
            variable=self.naming_var,
            value="pattern_name"
        )
        name_radio.grid(row=0, column=0, sticky="w", pady=2)

        # Pattern name with date option
        date_radio = ttk.Radiobutton(
            section,
            text=f"Pattern name with date ({self.pattern.get('name', '')}_YYYY-MM-DD)",
            variable=self.naming_var,
            value="pattern_name_date"
        )
        date_radio.grid(row=1, column=0, sticky="w", pady=2)

        # Custom name option
        custom_radio = ttk.Radiobutton(
            section,
            text="Custom name:",
            variable=self.naming_var,
            value="custom"
        )
        custom_radio.grid(row=2, column=0, sticky="w", pady=2)

        # Custom name entry
        custom_frame = ttk.Frame(section)
        custom_frame.grid(row=3, column=0, sticky="w", padx=(20, 0), pady=(0, 5))

        self.custom_name_var = tk.StringVar()
        custom_entry = ttk.Entry(custom_frame, textvariable=self.custom_name_var, width=35)
        custom_entry.pack(side=tk.LEFT)

    def create_destination_section(self, parent):
        """
        Create the destination section.

        Args:
            parent: The parent widget
        """
        # Create section frame
        section = ttk.LabelFrame(parent, text="Destination", padding=10)
        section.pack(fill=tk.X)

        # Create destination frame
        dest_frame = ttk.Frame(section)
        dest_frame.pack(fill=tk.X)

        # Destination label
        ttk.Label(dest_frame, text="Export to:").pack(side=tk.LEFT, padx=(0, 5))

        # Destination entry
        self.destination_var = tk.StringVar()
        dest_entry = ttk.Entry(dest_frame, textvariable=self.destination_var, width=40)
        dest_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # Browse button
        browse_btn = ttk.Button(
            dest_frame,
            text="Browse...",
            command=self.on_browse_destination
        )
        browse_btn.pack(side=tk.LEFT)

    def on_browse_destination(self):
        """Handle browse destination button click."""
        # Get selected format
        file_format = self.format_var.get()

        # Set appropriate file extension and dialog options
        if file_format == "pdf":
            file_types = [("PDF Files", "*.pdf"), ("All Files", "*.*")]
            default_ext = ".pdf"
        elif file_format == "svg":
            file_types = [("SVG Files", "*.svg"), ("All Files", "*.*")]
            default_ext = ".svg"
        elif file_format == "png":
            file_types = [("PNG Files", "*.png"), ("All Files", "*.*")]
            default_ext = ".png"
        elif file_format == "zip":
            file_types = [("ZIP Archives", "*.zip"), ("All Files", "*.*")]
            default_ext = ".zip"
        else:
            file_types = [("All Files", "*.*")]
            default_ext = ""

        # For single-file formats, use file save dialog
        if file_format in ["pdf", "zip"]:
            initial_name = self.get_export_filename(default_ext)

            file_path = filedialog.asksaveasfilename(
                title="Save Export As",
                filetypes=file_types,
                defaultextension=default_ext,
                initialfile=initial_name
            )

            if file_path:
                self.destination_var.set(file_path)

        # For multi-file formats, use directory selection
        else:
            directory = filedialog.askdirectory(
                title="Select Export Directory"
            )

            if directory:
                self.destination_var.set(directory)

    def get_export_filename(self, extension):
        """
        Generate export filename based on naming options.

        Args:
            extension: File extension to append

        Returns:
            Generated filename
        """
        # Get pattern name
        pattern_name = self.pattern.get("name", "pattern").replace(" ", "_")

        # Get naming option
        naming_option = self.naming_var.get()

        if naming_option == "pattern_name":
            return f"{pattern_name}{extension}"

        elif naming_option == "pattern_name_date":
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")
            return f"{pattern_name}_{date_str}{extension}"

        elif naming_option == "custom":
            custom_name = self.custom_name_var.get().strip()
            if custom_name:
                # Make sure it has the correct extension
                if not custom_name.endswith(extension):
                    return f"{custom_name}{extension}"
                return custom_name
            else:
                return f"{pattern_name}{extension}"

        # Default fallback
        return f"{pattern_name}{extension}"

    def validate_form(self):
        """
        Validate export options.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check destination
        destination = self.destination_var.get().strip()
        if not destination:
            return False, "Please specify a destination for the export."

        # Check format-specific requirements
        file_format = self.format_var.get()

        if file_format in ["pdf", "zip"]:
            # For single file formats, check if file can be created
            try:
                # Check directory exists
                directory = os.path.dirname(destination)
                if directory and not os.path.exists(directory):
                    return False, f"The directory does not exist: {directory}"

                # Check write permissions by touching the file
                if os.path.exists(destination):
                    if not os.access(destination, os.W_OK):
                        return False, f"Cannot write to the file: {destination}"
            except Exception as e:
                return False, f"Invalid destination path: {str(e)}"
        else:
            # For directory formats, check if directory exists and is writable
            if not os.path.exists(destination):
                return False, f"The directory does not exist: {destination}"

            if not os.path.isdir(destination):
                return False, f"The path is not a directory: {destination}"

            if not os.access(destination, os.W_OK):
                return False, f"Cannot write to the directory: {destination}"

        # Check scale value
        try:
            scale = float(self.include_vars["scale"].get())
            if scale <= 0:
                return False, "Scale must be a positive number."
        except ValueError:
            return False, "Scale must be a valid number."

        # Make sure at least one include option is selected
        if not any([
            self.include_vars["components"].get(),
            self.include_vars["materials"].get(),
            self.include_vars["assembly"].get()
        ]):
            return False, "Please select at least one component to include in the export."

        return True, ""

    def on_export(self):
        """Handle export button click."""
        # Validate form
        valid, error_message = self.validate_form()
        if not valid:
            messagebox.showerror("Export Error", error_message)
            return

        try:
            # Get pattern service
            service = get_service("IPatternService")

            # Prepare export options
            export_options = {
                "format": self.format_var.get(),
                "destination": self.destination_var.get(),
                "include": {
                    "components": self.include_vars["components"].get(),
                    "materials": self.include_vars["materials"].get(),
                    "assembly": self.include_vars["assembly"].get(),
                    "dimensions": self.include_vars["dimensions"].get(),
                    "notes": self.include_vars["notes"].get(),
                    "attachments": self.include_vars["attachments"].get(),
                    "scale_markers": self.include_vars["scale_markers"].get()
                },
                "scale": float(self.include_vars["scale"].get()) / 100.0  # Convert percentage to decimal
            }

            # Set naming option
            naming_option = self.naming_var.get()
            if naming_option == "custom":
                export_options["custom_name"] = self.custom_name_var.get().strip()
            else:
                export_options["naming"] = naming_option

            # Perform export
            result = service.export_pattern(self.pattern_id, export_options)

            if result:
                # Get the exported path(s)
                if isinstance(result, str):
                    exported_path = result
                    message = f"Pattern exported successfully to:\n{exported_path}"
                elif isinstance(result, list):
                    exported_paths = result
                    message = f"Pattern exported successfully. {len(exported_paths)} files created in:\n{os.path.dirname(exported_paths[0])}"
                else:
                    message = "Pattern exported successfully."

                # Show success message with option to open
                if messagebox.askyesno("Export Complete", message + "\n\nWould you like to open the exported file(s)?"):
                    self.open_export_result(result)

                # Set dialog result and close
                self.result = "ok"
                self.close()
            else:
                messagebox.showerror("Export Error", "Failed to export pattern.")
        except Exception as e:
            logger.error(f"Error exporting pattern: {str(e)}")
            messagebox.showerror("Export Error", f"Failed to export pattern: {str(e)}")

    def open_export_result(self, result):
        """
        Open exported file(s) with system default application.

        Args:
            result: The export result (path or list of paths)
        """
        try:
            import subprocess
            import platform

            # Function to open a single file
            def open_file(path):
                if platform.system() == "Windows":
                    os.startfile(path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.call(["open", path])
                else:  # Linux
                    subprocess.call(["xdg-open", path])

            # Open single file or first file from list
            if isinstance(result, str):
                open_file(result)
            elif isinstance(result, list) and result:
                # If it's a directory export, open the directory
                directory = os.path.dirname(result[0])
                open_file(directory)

        except Exception as e:
            logger.error(f"Error opening export: {str(e)}")
            messagebox.showerror("Error", f"Failed to open exported file(s): {str(e)}")