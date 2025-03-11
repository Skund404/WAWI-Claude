# gui/views/patterns/print_dialog.py
"""
Print dialog for printing patterns.

Provides options for printing patterns with various settings for
paper size, orientation, scaling, and components to include.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Optional

from gui.base.base_dialog import BaseDialog
from gui.theme import COLORS
from gui.utils.service_access import get_service

logger = logging.getLogger(__name__)


class PrintDialog(BaseDialog):
    """
    Dialog for printing patterns with customizable options.
    """

    def __init__(self, parent, pattern_id):
        """
        Initialize the print dialog.

        Args:
            parent: The parent widget
            pattern_id: ID of the pattern to print
        """
        self.pattern_id = pattern_id
        self.pattern = None

        # Print options
        self.paper_size_var = None
        self.orientation_var = None
        self.scale_var = None
        self.include_vars = {}
        self.print_options = {}

        # Call parent constructor
        super().__init__(parent, title="Print Pattern", width=550, height=550)

    def create_layout(self):
        """Create the dialog layout."""
        # Create main content frame with scrollbar for larger dialogs
        container = ttk.Frame(self.dialog_frame)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Add scrollbar
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)

        main_frame = ttk.Frame(canvas)

        # Configure scrolling
        main_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Load pattern data
        self.load_pattern()

        # Create title with pattern name
        title_label = ttk.Label(
            main_frame,
            text=f"Print Pattern: {self.pattern.get('name', '')}",
            font=("TkDefaultFont", 12, "bold")
        )
        title_label.pack(anchor="w", pady=(0, 15))

        # Create options sections
        self.create_paper_section(main_frame)
        self.create_scaling_section(main_frame)
        self.create_include_section(main_frame)
        self.create_print_options_section(main_frame)

        # Create buttons
        button_frame = ttk.Frame(self.dialog_frame)
        button_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        preview_btn = ttk.Button(
            button_frame,
            text="Print Preview",
            command=self.on_preview
        )
        preview_btn.pack(side=tk.LEFT)

        print_btn = ttk.Button(
            button_frame,
            text="Print",
            command=self.on_print
        )
        print_btn.pack(side=tk.RIGHT, padx=(5, 0))

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

    def create_paper_section(self, parent):
        """
        Create the paper options section.

        Args:
            parent: The parent widget
        """
        # Create section frame
        section = ttk.LabelFrame(parent, text="Paper Options", padding=10)
        section.pack(fill=tk.X, pady=(0, 15))

        # Paper size
        paper_frame = ttk.Frame(section)
        paper_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(paper_frame, text="Paper Size:").pack(side=tk.LEFT, padx=(0, 10))

        self.paper_size_var = tk.StringVar(value="a4")
        paper_combo = ttk.Combobox(paper_frame, textvariable=self.paper_size_var, width=20)
        paper_combo.pack(side=tk.LEFT)

        # Paper size options
        paper_sizes = [
            "A4 (210 × 297 mm)",
            "US Letter (8.5 × 11 in)",
            "A3 (297 × 420 mm)",
            "US Tabloid (11 × 17 in)",
            "A5 (148 × 210 mm)",
            "A2 (420 × 594 mm)",
            "Custom"
        ]
        paper_combo["values"] = paper_sizes

        # Custom size frame (hidden initially)
        self.custom_size_frame = ttk.Frame(section)

        # Add width and height fields for custom size
        ttk.Label(self.custom_size_frame, text="Width:").grid(row=0, column=0, padx=(20, 5))
        self.custom_width_var = tk.StringVar()
        width_entry = ttk.Entry(self.custom_size_frame, textvariable=self.custom_width_var, width=6)
        width_entry.grid(row=0, column=1, padx=(0, 5))

        ttk.Label(self.custom_size_frame, text="Height:").grid(row=0, column=2, padx=(10, 5))
        self.custom_height_var = tk.StringVar()
        height_entry = ttk.Entry(self.custom_size_frame, textvariable=self.custom_height_var, width=6)
        height_entry.grid(row=0, column=3, padx=(0, 5))

        # Units dropdown
        self.custom_units_var = tk.StringVar(value="mm")
        units_combo = ttk.Combobox(self.custom_size_frame, textvariable=self.custom_units_var, width=6)
        units_combo["values"] = ["mm", "cm", "in"]
        units_combo.grid(row=0, column=4, padx=(0, 5))

        # Show custom size frame when "Custom" is selected
        def on_paper_size_change(*args):
            if self.paper_size_var.get() == "Custom":
                self.custom_size_frame.pack(fill=tk.X, pady=5)
            else:
                self.custom_size_frame.pack_forget()

        self.paper_size_var.trace_add("write", on_paper_size_change)

        # Orientation
        orientation_frame = ttk.Frame(section)
        orientation_frame.pack(fill=tk.X)

        ttk.Label(orientation_frame, text="Orientation:").pack(side=tk.LEFT, padx=(0, 10))

        self.orientation_var = tk.StringVar(value="portrait")

        portrait_radio = ttk.Radiobutton(
            orientation_frame,
            text="Portrait",
            variable=self.orientation_var,
            value="portrait"
        )
        portrait_radio.pack(side=tk.LEFT, padx=(0, 15))

        landscape_radio = ttk.Radiobutton(
            orientation_frame,
            text="Landscape",
            variable=self.orientation_var,
            value="landscape"
        )
        landscape_radio.pack(side=tk.LEFT)

    def create_scaling_section(self, parent):
        """
        Create the scaling options section.

        Args:
            parent: The parent widget
        """
        # Create section frame
        section = ttk.LabelFrame(parent, text="Scaling", padding=10)
        section.pack(fill=tk.X, pady=(0, 15))

        # Scaling options
        self.scale_var = tk.StringVar(value="actual_size")

        # Actual size option
        actual_radio = ttk.Radiobutton(
            section,
            text="Actual Size (100%)",
            variable=self.scale_var,
            value="actual_size"
        )
        actual_radio.grid(row=0, column=0, sticky="w", pady=2)

        # Fit to page option
        fit_radio = ttk.Radiobutton(
            section,
            text="Fit to Page",
            variable=self.scale_var,
            value="fit_to_page"
        )
        fit_radio.grid(row=1, column=0, sticky="w", pady=2)

        # Custom scale option
        custom_radio = ttk.Radiobutton(
            section,
            text="Custom Scale:",
            variable=self.scale_var,
            value="custom_scale"
        )
        custom_radio.grid(row=2, column=0, sticky="w", pady=2)

        # Custom scale entry
        custom_frame = ttk.Frame(section)
        custom_frame.grid(row=3, column=0, sticky="w", padx=(20, 0), pady=2)

        self.custom_scale_var = tk.StringVar(value="100")
        scale_entry = ttk.Entry(custom_frame, textvariable=self.custom_scale_var, width=5)
        scale_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(custom_frame, text="% (100% = actual size)").pack(side=tk.LEFT)

        # Scale markers
        scale_markers_frame = ttk.Frame(section)
        scale_markers_frame.grid(row=4, column=0, sticky="w", pady=(10, 0))

        self.include_scale_markers_var = tk.BooleanVar(value=True)
        scale_markers_check = ttk.Checkbutton(
            scale_markers_frame,
            text="Include scale markers (1cm/1inch squares)",
            variable=self.include_scale_markers_var
        )
        scale_markers_check.pack(anchor="w")

    def create_include_section(self, parent):
        """
        Create the include options section.

        Args:
            parent: The parent widget
        """
        # Create section frame
        section = ttk.LabelFrame(parent, text="Include in Printout", padding=10)
        section.pack(fill=tk.X, pady=(0, 15))

        # Create component selection
        ttk.Label(section, text="Select components to print:").pack(anchor="w", pady=(0, 5))

        # Component list frame with scrollbar
        list_frame = ttk.Frame(section)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create component list with checkboxes
        components_canvas = tk.Canvas(list_frame, height=100)
        components_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=components_canvas.yview)

        components_frame = ttk.Frame(components_canvas)

        # Configure scrolling
        components_frame.bind(
            "<Configure>",
            lambda e: components_canvas.configure(scrollregion=components_canvas.bbox("all"))
        )

        components_canvas.create_window((0, 0), window=components_frame, anchor="nw")
        components_canvas.configure(yscrollcommand=components_scrollbar.set)

        # Pack canvas and scrollbar
        components_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        components_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add checkboxes for components
        self.component_vars = {}

        for i, component in enumerate(self.pattern.get("components", [])):
            var = tk.BooleanVar(value=True)
            self.component_vars[component.get("id")] = var

            checkbox = ttk.Checkbutton(
                components_frame,
                text=f"{component.get('name', 'Unknown')} ({component.get('type', '').replace('_', ' ').title()})",
                variable=var
            )
            checkbox.grid(row=i, column=0, sticky="w", pady=1)

        # If no components, show message
        if not self.pattern.get("components", []):
            ttk.Label(
                components_frame,
                text="No components found for this pattern.",
                foreground=COLORS["text_secondary"]
            ).grid(row=0, column=0, sticky="w", pady=5)

        # Additional include options
        options_frame = ttk.Frame(section)
        options_frame.pack(fill=tk.X, pady=(10, 0))

        # Column 1
        col1 = ttk.Frame(options_frame)
        col1.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

        self.include_vars["materials"] = tk.BooleanVar(value=True)
        materials_check = ttk.Checkbutton(
            col1,
            text="Materials List",
            variable=self.include_vars["materials"]
        )
        materials_check.pack(anchor="w", pady=2)

        self.include_vars["dimensions"] = tk.BooleanVar(value=True)
        dimensions_check = ttk.Checkbutton(
            col1,
            text="Dimensions",
            variable=self.include_vars["dimensions"]
        )
        dimensions_check.pack(anchor="w", pady=2)

        # Column 2
        col2 = ttk.Frame(options_frame)
        col2.pack(side=tk.LEFT, fill=tk.Y)

        self.include_vars["notes"] = tk.BooleanVar(value=True)
        notes_check = ttk.Checkbutton(
            col2,
            text="Notes",
            variable=self.include_vars["notes"]
        )
        notes_check.pack(anchor="w", pady=2)

        self.include_vars["instructions"] = tk.BooleanVar(value=True)
        instructions_check = ttk.Checkbutton(
            col2,
            text="Instructions",
            variable=self.include_vars["instructions"]
        )
        instructions_check.pack(anchor="w", pady=2)

    def create_print_options_section(self, parent):
        """
        Create the print options section.

        Args:
            parent: The parent widget
        """
        # Create section frame
        section = ttk.LabelFrame(parent, text="Print Options", padding=10)
        section.pack(fill=tk.X)

        # Print options checkboxes
        self.print_options["collate"] = tk.BooleanVar(value=True)
        collate_check = ttk.Checkbutton(
            section,
            text="Collate copies",
            variable=self.print_options["collate"]
        )
        collate_check.grid(row=0, column=0, sticky="w", pady=2, padx=(0, 20))

        self.print_options["center"] = tk.BooleanVar(value=True)
        center_check = ttk.Checkbutton(
            section,
            text="Center on page",
            variable=self.print_options["center"]
        )
        center_check.grid(row=0, column=1, sticky="w", pady=2)

        self.print_options["print_to_file"] = tk.BooleanVar(value=False)
        file_check = ttk.Checkbutton(
            section,
            text="Print to PDF file",
            variable=self.print_options["print_to_file"]
        )
        file_check.grid(row=1, column=0, sticky="w", pady=2, padx=(0, 20))

        self.print_options["grayscale"] = tk.BooleanVar(value=False)
        grayscale_check = ttk.Checkbutton(
            section,
            text="Print in grayscale",
            variable=self.print_options["grayscale"]
        )
        grayscale_check.grid(row=1, column=1, sticky="w", pady=2)

        # Copies
        copies_frame = ttk.Frame(section)
        copies_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))

        ttk.Label(copies_frame, text="Copies:").pack(side=tk.LEFT, padx=(0, 5))

        self.copies_var = tk.StringVar(value="1")
        copies_spinbox = ttk.Spinbox(
            copies_frame,
            from_=1,
            to=100,
            textvariable=self.copies_var,
            width=3
        )
        copies_spinbox.pack(side=tk.LEFT)

    def validate_form(self):
        """
        Validate print options.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if at least one component is selected
        if self.pattern.get("components", []) and not any(var.get() for var in self.component_vars.values()):
            return False, "Please select at least one component to print."

        # Validate custom scale if selected
        if self.scale_var.get() == "custom_scale":
            try:
                scale = float(self.custom_scale_var.get())
                if scale <= 0:
                    return False, "Scale must be a positive number."
            except ValueError:
                return False, "Scale must be a valid number."

        # Validate custom paper size if selected
        if self.paper_size_var.get() == "Custom":
            try:
                width = float(self.custom_width_var.get())
                height = float(self.custom_height_var.get())
                if width <= 0 or height <= 0:
                    return False, "Paper dimensions must be positive numbers."
            except ValueError:
                return False, "Paper dimensions must be valid numbers."

        # Validate copies
        try:
            copies = int(self.copies_var.get())
            if copies <= 0:
                return False, "Number of copies must be a positive integer."
        except ValueError:
            return False, "Number of copies must be a valid integer."

        return True, ""

    def get_print_options(self):
        """
        Collect all print options into a dictionary.

        Returns:
            Dictionary of print options
        """
        options = {}

        # Paper options
        options["paper_size"] = self.paper_size_var.get()
        if options["paper_size"] == "Custom":
            options["custom_paper"] = {
                "width": float(self.custom_width_var.get()),
                "height": float(self.custom_height_var.get()),
                "units": self.custom_units_var.get()
            }

        options["orientation"] = self.orientation_var.get()

        # Scaling options
        options["scaling"] = self.scale_var.get()
        if options["scaling"] == "custom_scale":
            options["scale_percentage"] = float(self.custom_scale_var.get())

        options["scale_markers"] = self.include_scale_markers_var.get()

        # Components to include
        options["components"] = [
            int(comp_id) for comp_id, var in self.component_vars.items()
            if var.get()
        ]

        # Include options
        options["include"] = {
            key: var.get() for key, var in self.include_vars.items()
        }

        # Print options
        options["print_options"] = {
            key: var.get() for key, var in self.print_options.items()
        }

        # Copies
        options["copies"] = int(self.copies_var.get())

        return options

    def on_preview(self):
        """Handle print preview button click."""
        # Validate form
        valid, error_message = self.validate_form()
        if not valid:
            messagebox.showerror("Print Error", error_message)
            return

        try:
            # Get pattern service
            service = get_service("IPatternService")

            # Get print options
            options = self.get_print_options()
            options["preview_only"] = True

            # Generate preview
            result = service.print_pattern(self.pattern_id, options)

            if result:
                # Show preview window
                self.show_preview(result)
            else:
                messagebox.showerror("Preview Error", "Failed to generate print preview.")
        except Exception as e:
            logger.error(f"Error generating print preview: {str(e)}")
            messagebox.showerror("Preview Error", f"Failed to generate print preview: {str(e)}")

    def show_preview(self, preview_data):
        """
        Show print preview in a new window.

        Args:
            preview_data: The preview data
        """
        # Create preview window
        preview_window = tk.Toplevel(self.dialog)
        preview_window.title(f"Print Preview - {self.pattern.get('name', '')}")
        preview_window.geometry("800x600")
        preview_window.minsize(600, 400)

        # Create toolbar
        toolbar = ttk.Frame(preview_window)
        toolbar.pack(fill=tk.X, padx=10, pady=10)

        # Page navigation
        ttk.Button(
            toolbar,
            text="Previous Page",
            command=lambda: self.preview_prev_page()
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Next Page",
            command=lambda: self.preview_next_page()
        ).pack(side=tk.LEFT)

        # Page indicator
        self.preview_page_var = tk.StringVar(value="Page 1 of 1")
        ttk.Label(
            toolbar,
            textvariable=self.preview_page_var
        ).pack(side=tk.LEFT, padx=15)

        # Zoom controls
        ttk.Label(toolbar, text="Zoom:").pack(side=tk.LEFT, padx=(15, 5))

        self.preview_zoom_var = tk.StringVar(value="100%")
        zoom_combo = ttk.Combobox(
            toolbar,
            textvariable=self.preview_zoom_var,
            width=5,
            values=["50%", "75%", "100%", "125%", "150%", "200%"]
        )
        zoom_combo.pack(side=tk.LEFT)

        # Print button
        ttk.Button(
            toolbar,
            text="Print",
            command=self.on_print
        ).pack(side=tk.RIGHT)

        # Preview area with scrollbars
        preview_frame = ttk.Frame(preview_window)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Add canvas and scrollbars for preview
        h_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL)
        v_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL)

        preview_canvas = tk.Canvas(
            preview_frame,
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set,
            bg="white"
        )

        h_scrollbar.config(command=preview_canvas.xview)
        v_scrollbar.config(command=preview_canvas.yview)

        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Store preview data for later use
        self.preview_data = preview_data
        self.preview_canvas = preview_canvas
        self.current_page = 0
        self.total_pages = len(preview_data.get("pages", []))

        # Update page indicator
        self.preview_page_var.set(f"Page 1 of {self.total_pages}")

        # Display first page
        self.display_preview_page(0)

        # Bind zoom change
        zoom_combo.bind("<<ComboboxSelected>>", lambda e: self.update_preview_zoom())

    def display_preview_page(self, page_index):
        """
        Display a specific page in the preview.

        Args:
            page_index: The index of the page to display
        """
        # Clear canvas
        self.preview_canvas.delete("all")

        # Check if page exists
        if not self.preview_data or "pages" not in self.preview_data:
            return

        pages = self.preview_data.get("pages", [])
        if page_index < 0 or page_index >= len(pages):
            return

        # Get page data
        page = pages[page_index]

        # Get zoom level
        zoom_str = self.preview_zoom_var.get().rstrip("%")
        try:
            zoom = float(zoom_str) / 100.0
        except ValueError:
            zoom = 1.0

        # Calculate dimensions
        page_width = page.get("width", 210) * zoom
        page_height = page.get("height", 297) * zoom

        # Configure canvas scrollregion
        padding = 20  # Padding around the page
        self.preview_canvas.configure(
            scrollregion=(0, 0, page_width + 2 * padding, page_height + 2 * padding)
        )

        # Draw page background with shadow
        shadow_offset = 5
        self.preview_canvas.create_rectangle(
            padding + shadow_offset,
            padding + shadow_offset,
            padding + page_width + shadow_offset,
            padding + page_height + shadow_offset,
            fill="#CCCCCC",
            outline=""
        )

        self.preview_canvas.create_rectangle(
            padding,
            padding,
            padding + page_width,
            padding + page_height,
            fill="white",
            outline="#999999"
        )

        # Draw page content
        # This is a placeholder - in a real application, you would render actual content
        # For now, we'll just show a representation of the content
        content_items = page.get("items", [])

        for item in content_items:
            item_type = item.get("type", "")

            if item_type == "component":
                # Draw component outline
                x = padding + item.get("x", 0) * zoom
                y = padding + item.get("y", 0) * zoom
                width = item.get("width", 50) * zoom
                height = item.get("height", 50) * zoom
                name = item.get("name", "Component")

                self.preview_canvas.create_rectangle(
                    x, y, x + width, y + height,
                    outline="#000000",
                    width=1
                )

                self.preview_canvas.create_text(
                    x + width / 2,
                    y + height / 2,
                    text=name,
                    font=("TkDefaultFont", int(10 * zoom))
                )

            elif item_type == "text":
                # Draw text
                x = padding + item.get("x", 0) * zoom
                y = padding + item.get("y", 0) * zoom
                text = item.get("text", "")

                self.preview_canvas.create_text(
                    x, y,
                    text=text,
                    font=("TkDefaultFont", int(10 * zoom)),
                    anchor="nw"
                )

            elif item_type == "line":
                # Draw line
                x1 = padding + item.get("x1", 0) * zoom
                y1 = padding + item.get("y1", 0) * zoom
                x2 = padding + item.get("x2", 0) * zoom
                y2 = padding + item.get("y2", 0) * zoom

                self.preview_canvas.create_line(
                    x1, y1, x2, y2,
                    fill="#000000",
                    width=1
                )

    def preview_next_page(self):
        """Go to next page in preview."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.display_preview_page(self.current_page)
            self.preview_page_var.set(f"Page {self.current_page + 1} of {self.total_pages}")

    def preview_prev_page(self):
        """Go to previous page in preview."""
        if self.current_page > 0:
            self.current_page -= 1
            self.display_preview_page(self.current_page)
            self.preview_page_var.set(f"Page {self.current_page + 1} of {self.total_pages}")

    def update_preview_zoom(self):
        """Update preview zoom level."""
        # Redisplay current page with new zoom
        self.display_preview_page(self.current_page)

    def on_print(self):
        """Handle print button click."""
        # Validate form
        valid, error_message = self.validate_form()
        if not valid:
            messagebox.showerror("Print Error", error_message)
            return

        try:
            # Get pattern service
            service = get_service("IPatternService")

            # Get print options
            options = self.get_print_options()

            # Perform print
            result = service.print_pattern(self.pattern_id, options)

            if result:
                if options["print_options"].get("print_to_file"):
                    # If printing to file, show success with file path
                    file_path = result.get("file_path", "")
                    messagebox.showinfo(
                        "Print Complete",
                        f"Pattern has been exported to PDF:\n{file_path}"
                    )
                else:
                    # Normal printing
                    messagebox.showinfo(
                        "Print Complete",
                        "Pattern has been sent to the printer."
                    )

                # Set dialog result and close
                self.result = "ok"
                self.close()
            else:
                messagebox.showerror("Print Error", "Failed to print pattern.")
        except Exception as e:
            logger.error(f"Error printing pattern: {str(e)}")
            messagebox.showerror("Print Error", f"Failed to print pattern: {str(e)}")