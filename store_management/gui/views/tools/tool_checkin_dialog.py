# gui/views/tools/tool_checkin_dialog.py
"""
Dialog for checking in tools in the leatherworking ERP system.

This dialog provides a form interface for checking in tools,
including updating the tool condition and adding notes.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional
from datetime import datetime

from gui.base.base_dialog import BaseDialog
from gui.theme import COLORS
from utils.service_access import with_service


class ToolCheckinDialog(BaseDialog):
    """Dialog for checking in tools."""

    def __init__(self, parent, checkout_id=None):
        """Initialize the tool checkin dialog.

        Args:
            parent: The parent widget
            checkout_id: Optional checkout ID if checking in a specific checkout
        """
        self.checkout_id = checkout_id
        self.logger = logging.getLogger(__name__)

        super().__init__(parent, title="Check In Tool", width=500, height=400)
        self.result = None

    def create_layout(self):
        """Create the dialog layout."""
        # Main frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create form fields
        self.create_form(main_frame)

        # Buttons frame
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=20, pady=10)

        # Add buttons
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Check In", command=self.on_checkin,
                   style="Accent.TButton").pack(side=tk.RIGHT, padx=5)

    def create_form(self, parent):
        """Create form fields for the checkin.

        Args:
            parent: The parent widget
        """
        # Store field variables and widgets
        self.field_vars = {}
        self.field_widgets = {}

        # Create fields with labels in a grid layout
        row = 0

        # If checkout_id is provided, load and display that checkout
        if self.checkout_id:
            self.load_checkout(parent)
        else:
            # Otherwise, show a dropdown to select from checked out tools
            ttk.Label(parent, text="Select Tool:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

            self.field_vars["checkout_id"] = tk.StringVar()
            checkout_combobox = ttk.Combobox(parent, textvariable=self.field_vars["checkout_id"], state="readonly")
            checkout_combobox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
            self.field_widgets["checkout_id"] = checkout_combobox

            # Load checked out tools for the combobox
            self.load_checked_out_tools(checkout_combobox)

            # Add a callback when a tool is selected
            def on_checkout_select(event):
                self.load_checkout_details(parent, row + 1)

            checkout_combobox.bind("<<ComboboxSelected>>", on_checkout_select)

            row += 1

            # Create a frame for checkout details that will be populated when a tool is selected
            self.details_frame = ttk.Frame(parent)
            self.details_frame.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W + tk.E)

        # Configure column weights
        parent.columnconfigure(1, weight=1)

    def load_checkout(self, parent):
        """Load checkout details for the specified checkout ID.

        Args:
            parent: The parent widget
        """
        try:
            with self.get_service("tool_checkout_service") as service:
                checkout = service.get_checkout_by_id(self.checkout_id, include_tool=True)

                if not checkout:
                    messagebox.showerror("Error", f"Checkout record with ID {self.checkout_id} not found")
                    self.on_cancel()
                    return

                # Store checkout information
                self.field_vars["checkout_id"] = tk.StringVar(value=str(checkout.id))

                # Create the checkout info display
                row = 0

                # Tool name
                ttk.Label(parent, text="Tool:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

                tool_name = checkout.tool["name"] if checkout.tool else "Unknown Tool"
                ttk.Label(parent, text=tool_name).grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

                row += 1

                # User
                ttk.Label(parent, text="Checked Out By:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
                ttk.Label(parent, text=checkout.checked_out_by).grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

                row += 1

                # Checkout Date
                ttk.Label(parent, text="Checkout Date:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

                checkout_date = checkout.checked_out_date.strftime("%Y-%m-%d") if checkout.checked_out_date else "N/A"
                ttk.Label(parent, text=checkout_date).grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

                row += 1

                # Condition Before
                ttk.Label(parent, text="Condition Before:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
                ttk.Label(parent, text=checkout.condition_before or "Not recorded").grid(
                    row=row, column=1, padx=5, pady=5, sticky=tk.W)

                row += 1

                # Return Date
                ttk.Label(parent, text="Return Date:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

                self.field_vars["returned_date"] = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))

                date_frame = ttk.Frame(parent)
                date_frame.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

                date_entry = ttk.Entry(date_frame, textvariable=self.field_vars["returned_date"], width=15)
                date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.field_widgets["returned_date"] = date_entry

                ttk.Button(date_frame, text="...", width=3, command=lambda: self.show_date_picker(
                    self.field_vars["returned_date"])).pack(side=tk.LEFT, padx=5)

                row += 1

                # Condition After
                ttk.Label(parent, text="Condition After:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

                self.field_vars["condition_after"] = tk.StringVar()
                condition_combobox = ttk.Combobox(parent, textvariable=self.field_vars["condition_after"],
                                                  state="readonly")
                condition_combobox["values"] = ["Excellent", "Good", "Fair", "Poor"]
                condition_combobox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
                self.field_widgets["condition_after"] = condition_combobox
                condition_combobox.current(0)  # Default to "Excellent"

                row += 1

                # Notes
                ttk.Label(parent, text="Notes:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W + tk.N)

                notes_text = tk.Text(parent, height=3, width=40)
                notes_text.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
                notes_scrollbar = ttk.Scrollbar(parent, command=notes_text.yview)
                notes_scrollbar.grid(row=row, column=2, sticky=tk.N + tk.S)
                notes_text.configure(yscrollcommand=notes_scrollbar.set)

                self.field_widgets["notes"] = notes_text

                # Configure column weights
                parent.columnconfigure(1, weight=1)

        except Exception as e:
            self.logger.error(f"Error loading checkout: {e}")
            messagebox.showerror("Error", f"Failed to load checkout details: {str(e)}")
            self.on_cancel()

    def load_checkout_details(self, parent, start_row):
        """Load details for the selected checkout from the dropdown.

        Args:
            parent: The parent widget
            start_row: The row to start adding details
        """
        # Clear existing details
        for widget in self.details_frame.winfo_children():
            widget.destroy()

        # Get the selected checkout ID
        checkout_id = self.field_vars["checkout_id"].get()
        if not checkout_id:
            return

        try:
            # Convert to integer
            checkout_id = int(checkout_id)

            with self.get_service("tool_checkout_service") as service:
                checkout = service.get_checkout_by_id(checkout_id, include_tool=True)

                if not checkout:
                    messagebox.showerror("Error", f"Checkout record with ID {checkout_id} not found")
                    return

                # Create the checkout info display
                row = 0

                # Tool name
                ttk.Label(self.details_frame, text="Tool:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

                tool_name = checkout.tool["name"] if checkout.tool else "Unknown Tool"
                ttk.Label(self.details_frame, text=tool_name).grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

                row += 1

                # User
                ttk.Label(self.details_frame, text="Checked Out By:").grid(row=row, column=0, padx=5, pady=5,
                                                                           sticky=tk.W)
                ttk.Label(self.details_frame, text=checkout.checked_out_by).grid(
                    row=row, column=1, padx=5, pady=5, sticky=tk.W)

                row += 1

                # Checkout Date
                ttk.Label(self.details_frame, text="Checkout Date:").grid(row=row, column=0, padx=5, pady=5,
                                                                          sticky=tk.W)

                checkout_date = checkout.checked_out_date.strftime("%Y-%m-%d") if checkout.checked_out_date else "N/A"
                ttk.Label(self.details_frame, text=checkout_date).grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

                row += 1

                # Condition Before
                ttk.Label(self.details_frame, text="Condition Before:").grid(row=row, column=0, padx=5, pady=5,
                                                                             sticky=tk.W)
                ttk.Label(self.details_frame, text=checkout.condition_before or "Not recorded").grid(
                    row=row, column=1, padx=5, pady=5, sticky=tk.W)

                row += 1

                # Return Date
                ttk.Label(self.details_frame, text="Return Date:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

                self.field_vars["returned_date"] = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))

                date_frame = ttk.Frame(self.details_frame)
                date_frame.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

                date_entry = ttk.Entry(date_frame, textvariable=self.field_vars["returned_date"], width=15)
                date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.field_widgets["returned_date"] = date_entry

                ttk.Button(date_frame, text="...", width=3, command=lambda: self.show_date_picker(
                    self.field_vars["returned_date"])).pack(side=tk.LEFT, padx=5)

                row += 1

                # Condition After
                ttk.Label(self.details_frame, text="Condition After:").grid(row=row, column=0, padx=5, pady=5,
                                                                            sticky=tk.W)

                self.field_vars["condition_after"] = tk.StringVar()
                condition_combobox = ttk.Combobox(self.details_frame, textvariable=self.field_vars["condition_after"],
                                                  state="readonly")
                condition_combobox["values"] = ["Excellent", "Good", "Fair", "Poor"]
                condition_combobox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
                self.field_widgets["condition_after"] = condition_combobox
                condition_combobox.current(0)  # Default to "Excellent"

                row += 1

                # Notes
                ttk.Label(self.details_frame, text="Notes:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W + tk.N)

                notes_text = tk.Text(self.details_frame, height=3, width=40)
                notes_text.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
                notes_scrollbar = ttk.Scrollbar(self.details_frame, command=notes_text.yview)
                notes_scrollbar.grid(row=row, column=2, sticky=tk.N + tk.S)
                notes_text.configure(yscrollcommand=notes_scrollbar.set)

                self.field_widgets["notes"] = notes_text

                # Configure column weights
                self.details_frame.columnconfigure(1, weight=1)

        except Exception as e:
            self.logger.error(f"Error loading checkout details: {e}")
            messagebox.showerror("Error", f"Failed to load checkout details: {str(e)}")

    @with_service("tool_checkout_service")
    def load_checked_out_tools(self, combobox, service=None):
        """Load checked out tools for the combobox.

        Args:
            combobox: The combobox widget to populate
            service: The tool checkout service injected by the decorator
        """
        try:
            # Get checked out tools
            checkouts = service.get_checked_out_tools(include_overdue=True)

            # Format for combobox
            checkout_options = {}
            checkout_values = []

            for checkout in checkouts:
                tool_name = checkout.tool["name"] if checkout.tool else "Unknown Tool"
                checkout_options[str(checkout.id)] = checkout
                checkout_values.append(f"{tool_name} - {checkout.checked_out_by} (ID: {checkout.id})")

            combobox["values"] = checkout_values

            # Store the mapping of display values to IDs
            self.checkout_displays = {
                f"{checkout.tool['name'] if checkout.tool else 'Unknown Tool'} - {checkout.checked_out_by} (ID: {checkout.id})":
                    str(checkout.id)
                for checkout in checkouts
            }

            # Set up callback to update the checkout_id when selection changes
            def on_checkout_select(event):
                selected = combobox.get()
                if selected in self.checkout_displays:
                    self.field_vars["checkout_id"].set(self.checkout_displays[selected])

            combobox.bind("<<ComboboxSelected>>", on_checkout_select)

        except Exception as e:
            self.logger.error(f"Error loading checked out tools: {e}")
            messagebox.showerror("Error", f"Failed to load checked out tools: {str(e)}")

    def show_date_picker(self, date_var):
        """Show a date picker dialog.

        Args:
            date_var: The StringVar to update with selected date
        """
        from tkcalendar import DateEntry

        # Create a top-level window for the date picker
        top = tk.Toplevel(self.window)
        top.title("Select Date")
        top.transient(self.window)
        top.grab_set()

        # Center the date picker
        top.geometry(f"+{self.window.winfo_rootx() + 50}+{self.window.winfo_rooty() + 50}")

        # Create a date entry widget
        current_date = datetime.now()
        try:
            if date_var.get():
                current_date = datetime.strptime(date_var.get(), "%Y-%m-%d")
        except ValueError:
            pass

        cal = DateEntry(top, width=12, background='darkblue',
                        foreground='white', borderwidth=2,
                        year=current_date.year, month=current_date.month, day=current_date.day)
        cal.pack(padx=10, pady=10)

        # Function to set the date and close the picker
        def set_date():
            date_var.set(cal.get_date().strftime("%Y-%m-%d"))
            top.destroy()

        # Add OK button
        ttk.Button(top, text="OK", command=set_date).pack(pady=5)

    def validate_form(self):
        """Validate form data.

        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        if "checkout_id" not in self.field_vars or not self.field_vars["checkout_id"].get():
            messagebox.showwarning("Missing Information", "Please select a tool to check in")
            return False

        # Validate date formats
        date_fields = ["returned_date"]
        for field in date_fields:
            if field in self.field_vars and self.field_vars[field].get():
                try:
                    datetime.strptime(self.field_vars[field].get(), "%Y-%m-%d")
                except ValueError:
                    messagebox.showwarning("Invalid Date",
                                           f"Please enter a valid date in format YYYY-MM-DD for {field.replace('_', ' ').title()}")
                    return False

        return True

    def collect_form_data(self):
        """Collect form data for saving.

        Returns:
            Dictionary of form data
        """
        # Collect data from field variables
        data = {}

        # Text fields
        for field, var in self.field_vars.items():
            if field not in ["checkout_id"]:  # Skip fields that are not part of the check-in data
                data[field] = var.get()

        # Text widgets
        if "notes" in self.field_widgets:
            data["notes"] = self.field_widgets["notes"].get("1.0", tk.END).strip()

        # Convert empty strings to None for optional fields
        for field in ["notes", "condition_after"]:
            if field in data and data[field] == "":
                data[field] = None

        # Convert dates from string to datetime
        for field in ["returned_date"]:
            if field in data and data[field]:
                try:
                    data[field] = datetime.strptime(data[field], "%Y-%m-%d")
                except ValueError:
                    data[field] = None

        return data

    @with_service("tool_checkout_service")
    def on_checkin(self, service=None):
        """Handle tool check-in.

        Args:
            service: The tool checkout service injected by the decorator
        """
        # Validate form
        if not self.validate_form():
            return

        try:
            # Collect form data
            data = self.collect_form_data()

            # Get checkout_id from form data or instance variable
            checkout_id = int(self.checkout_id or self.field_vars["checkout_id"].get())

            # Check in the tool
            result = service.check_in_tool(checkout_id, data)

            messagebox.showinfo("Success", "Tool checked in successfully")

            # Store result and close dialog
            self.result = result
            self.close()

        except Exception as e:
            self.logger.error(f"Error checking in tool: {e}")
            messagebox.showerror("Error", f"Failed to check in tool: {str(e)}")