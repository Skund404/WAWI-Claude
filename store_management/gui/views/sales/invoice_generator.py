# gui/views/sales/invoice_generator.py
"""
Invoice generator module for the leatherworking application.

This module provides functionality for generating invoices from sales records,
with customizable templates and output options.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import logging
import os
from typing import Any, Dict, List, Optional

from gui.base.base_dialog import BaseDialog
from gui.theme import COLORS
from gui.utils.service_access import get_service


class InvoiceGenerator(BaseDialog):
    """
    Dialog for generating invoices from sales records.

    This dialog provides options for customizing invoice templates,
    output format, and delivery options.
    """

    def __init__(self, parent, sale_id):
        """
        Initialize the invoice generator dialog.

        Args:
            parent: The parent widget
            sale_id: ID of the sale to generate invoice for
        """
        self.logger = logging.getLogger(__name__)
        self.sale_id = sale_id

        # Initialize base dialog
        super().__init__(
            parent,
            title="Generate Invoice",
            width=600,
            height=500,
            modal=True
        )

        # Initialize services
        self.sales_service = get_service("sales_service")

        # Initialize sale data
        self.sale_data = None
        self.load_sale_data()

        # Initialize result
        self.result = None

    def load_sale_data(self):
        """Load sale data from service."""
        try:
            self.sale_data = self.sales_service.get_sale(
                self.sale_id,
                include_customer=True,
                include_items=True
            )
        except Exception as e:
            self.logger.error(f"Error loading sale data: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to load sale data: {str(e)}")

    def create_layout(self):
        """Create the dialog layout."""
        if not self.sale_data:
            # Show error message if sale data couldn't be loaded
            error_label = ttk.Label(
                self.dialog,
                text="Error: Could not load sale data.",
                foreground="red"
            )
            error_label.pack(padx=20, pady=20)

            # Add close button
            ttk.Button(
                self.dialog,
                text="Close",
                command=self.close
            ).pack(pady=10)

            return

        # Create main container with padding
        container = ttk.Frame(self.dialog)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Create invoice info section
        info_frame = ttk.LabelFrame(container, text="Invoice Information")
        info_frame.pack(fill=tk.X, pady=10)

        # Sale ID and date
        sale_info_frame = ttk.Frame(info_frame)
        sale_info_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(sale_info_frame, text="Sale #:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        sale_id_var = tk.StringVar(value=str(self.sale_data.id))
        sale_id_entry = ttk.Entry(
            sale_info_frame,
            textvariable=sale_id_var,
            state="readonly",
            width=10
        )
        sale_id_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(sale_info_frame, text="Date:", width=8, anchor=tk.E).pack(side=tk.LEFT, padx=(10, 0))

        sale_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if hasattr(self.sale_data, "created_at") and self.sale_data.created_at:
            sale_date = self.sale_data.created_at.strftime("%Y-%m-%d")

        sale_date_var = tk.StringVar(value=sale_date)
        sale_date_entry = ttk.Entry(
            sale_info_frame,
            textvariable=sale_date_var,
            state="readonly",
            width=12
        )
        sale_date_entry.pack(side=tk.LEFT, padx=5)

        # Customer info
        customer_frame = ttk.Frame(info_frame)
        customer_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(customer_frame, text="Customer:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        customer_name = "Unknown"
        if hasattr(self.sale_data, "customer") and self.sale_data.customer:
            if hasattr(self.sale_data.customer, "first_name") and hasattr(self.sale_data.customer, "last_name"):
                customer_name = f"{self.sale_data.customer.first_name} {self.sale_data.customer.last_name}"

        customer_var = tk.StringVar(value=customer_name)
        customer_entry = ttk.Entry(
            customer_frame,
            textvariable=customer_var,
            state="readonly",
            width=40
        )
        customer_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Total amount
        total_frame = ttk.Frame(info_frame)
        total_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(total_frame, text="Total Amount:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        total_amount = "$0.00"
        if hasattr(self.sale_data, "total_amount") and self.sale_data.total_amount is not None:
            total_amount = f"${self.sale_data.total_amount:.2f}"

        total_var = tk.StringVar(value=total_amount)
        total_entry = ttk.Entry(
            total_frame,
            textvariable=total_var,
            state="readonly",
            width=15
        )
        total_entry.pack(side=tk.LEFT, padx=5)

        # Create template options section
        template_frame = ttk.LabelFrame(container, text="Template Options")
        template_frame.pack(fill=tk.X, pady=10)

        # Template selection
        template_selection_frame = ttk.Frame(template_frame)
        template_selection_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(template_selection_frame, text="Template:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        self.template_var = tk.StringVar(value="Standard")

        templates = ["Standard", "Professional", "Minimal", "Detailed"]
        template_combo = ttk.Combobox(
            template_selection_frame,
            textvariable=self.template_var,
            values=templates,
            state="readonly",
            width=20
        )
        template_combo.pack(side=tk.LEFT, padx=5)

        # Logo option
        logo_frame = ttk.Frame(template_frame)
        logo_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(logo_frame, text="Logo:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        self.logo_var = tk.BooleanVar(value=True)
        logo_check = ttk.Checkbutton(
            logo_frame,
            text="Include company logo",
            variable=self.logo_var
        )
        logo_check.pack(side=tk.LEFT, padx=5)

        # Color scheme
        color_frame = ttk.Frame(template_frame)
        color_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(color_frame, text="Color Scheme:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        self.color_var = tk.StringVar(value="Blue")

        colors = ["Blue", "Green", "Gray", "Brown", "Black"]
        color_combo = ttk.Combobox(
            color_frame,
            textvariable=self.color_var,
            values=colors,
            state="readonly",
            width=15
        )
        color_combo.pack(side=tk.LEFT, padx=5)

        # Create output options section
        output_frame = ttk.LabelFrame(container, text="Output Options")
        output_frame.pack(fill=tk.X, pady=10)

        # Format selection
        format_frame = ttk.Frame(output_frame)
        format_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(format_frame, text="Format:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        self.format_var = tk.StringVar(value="PDF")

        formats = ["PDF", "HTML"]
        format_combo = ttk.Combobox(
            format_frame,
            textvariable=self.format_var,
            values=formats,
            state="readonly",
            width=15
        )
        format_combo.pack(side=tk.LEFT, padx=5)

        # Output path
        path_frame = ttk.Frame(output_frame)
        path_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(path_frame, text="Save to:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        # Default output file name
        default_filename = f"Invoice_{self.sale_data.id}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
        self.path_var = tk.StringVar(value=default_filename)

        path_entry = ttk.Entry(
            path_frame,
            textvariable=self.path_var,
            width=40
        )
        path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        browse_button = ttk.Button(
            path_frame,
            text="Browse",
            command=self._browse_output_path
        )
        browse_button.pack(side=tk.LEFT, padx=5)

        # Create additional options section
        options_frame = ttk.LabelFrame(container, text="Additional Options")
        options_frame.pack(fill=tk.X, pady=10)

        # Delivery options
        delivery_frame = ttk.Frame(options_frame)
        delivery_frame.pack(fill=tk.X, padx=10, pady=5)

        self.email_var = tk.BooleanVar(value=False)
        email_check = ttk.Checkbutton(
            delivery_frame,
            text="Email to customer",
            variable=self.email_var
        )
        email_check.pack(side=tk.LEFT, padx=5)

        self.print_var = tk.BooleanVar(value=False)
        print_check = ttk.Checkbutton(
            delivery_frame,
            text="Print automatically",
            variable=self.print_var
        )
        print_check.pack(side=tk.LEFT, padx=20)

        # Invoice notes
        notes_frame = ttk.Frame(options_frame)
        notes_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(notes_frame, text="Notes:", anchor=tk.W).pack(anchor=tk.W)

        self.notes_text = tk.Text(
            notes_frame,
            height=3,
            width=40,
            wrap=tk.WORD
        )
        self.notes_text.pack(fill=tk.X, pady=5)

        # Default notes
        default_notes = "Thank you for your business!"
        self.notes_text.insert("1.0", default_notes)

        # Create buttons
        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Generate",
            style="Accent.TButton",
            command=self.on_ok
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Preview",
            command=self._preview_invoice
        ).pack(side=tk.RIGHT, padx=5)

    def _browse_output_path(self):
        """Browse for output file location."""
        # Determine file extension based on format
        extension = ".pdf" if self.format_var.get() == "PDF" else ".html"

        # Get current filename or create default
        current_path = self.path_var.get()
        if not current_path:
            current_path = f"Invoice_{self.sale_id}_{datetime.datetime.now().strftime('%Y%m%d')}{extension}"

        # Show save dialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=[
                ("PDF files", "*.pdf") if extension == ".pdf" else ("HTML files", "*.html"),
                ("All files", "*.*")
            ],
            initialfile=os.path.basename(current_path)
        )

        if file_path:
            self.path_var.set(file_path)

    def _preview_invoice(self):
        """Preview the invoice before generating."""
        try:
            # Collect options
            options = self._collect_options()

            # Set preview flag
            options["preview"] = True

            # Generate preview
            result = self.sales_service.generate_invoice(
                self.sale_id,
                options
            )

            if result.get("success"):
                # Show preview (this might open a PDF viewer or web browser)
                preview_path = result.get("path")

                if os.path.exists(preview_path):
                    # Open with system default application
                    self._open_with_default_app(preview_path)
                else:
                    messagebox.showwarning(
                        "Preview Error",
                        "Preview file was not created successfully."
                    )
            else:
                messagebox.showwarning(
                    "Preview Error",
                    result.get("message", "Failed to generate preview.")
                )

        except Exception as e:
            self.logger.error(f"Error generating preview: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to generate preview: {str(e)}")

    def _open_with_default_app(self, path):
        """
        Open a file with the default system application.

        Args:
            path: Path to the file to open
        """
        import platform
        import subprocess

        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', path))
            elif platform.system() == 'Windows':  # Windows
                os.startfile(path)
            else:  # Linux and other Unix-like
                subprocess.call(('xdg-open', path))
        except Exception as e:
            self.logger.error(f"Error opening file: {e}", exc_info=True)
            messagebox.showwarning(
                "Open Error",
                f"Could not open the file: {str(e)}"
            )

    def _collect_options(self):
        """
        Collect invoice generation options.

        Returns:
            Dictionary of options
        """
        # Get notes from text widget
        notes = self.notes_text.get("1.0", tk.END).strip()

        # Determine output file extension
        extension = ".pdf" if self.format_var.get() == "PDF" else ".html"

        # Ensure output path has correct extension
        output_path = self.path_var.get()
        if not output_path.lower().endswith(extension.lower()):
            # Replace extension
            output_path = os.path.splitext(output_path)[0] + extension
            self.path_var.set(output_path)

        # Create options dictionary
        options = {
            "template": self.template_var.get(),
            "include_logo": self.logo_var.get(),
            "color_scheme": self.color_var.get(),
            "format": self.format_var.get(),
            "output_path": output_path,
            "email_to_customer": self.email_var.get(),
            "print_automatically": self.print_var.get(),
            "notes": notes
        }

        return options

    def validate_form(self):
        """
        Validate form data.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check output path
        if not self.path_var.get():
            return False, "Please specify an output path."

        # All validations passed
        return True, ""

    def on_ok(self):
        """Handle OK button click."""
        # Validate form
        valid, message = self.validate_form()
        if not valid:
            messagebox.showwarning("Validation Error", message)
            return

        try:
            # Collect options
            options = self._collect_options()

            # Generate invoice
            result = self.sales_service.generate_invoice(
                self.sale_id,
                options
            )

            if result.get("success"):
                # Show success message
                messagebox.showinfo(
                    "Invoice Generated",
                    f"Invoice has been generated and saved to:\n{result.get('path')}"
                )

                # Ask if user wants to open the invoice
                if messagebox.askyesno(
                        "Open Invoice",
                        "Would you like to open the invoice now?"
                ):
                    self._open_with_default_app(result.get('path'))

                # Store result
                self.result = result

                # Close dialog
                self.close()
            else:
                messagebox.showwarning(
                    "Generation Error",
                    result.get("message", "Failed to generate invoice.")
                )

        except Exception as e:
            self.logger.error(f"Error generating invoice: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to generate invoice: {str(e)}")