# gui/views/tools/tool_maintenance_dialog.py
"""
Dialog for adding, editing, and viewing tool maintenance records.

This dialog provides a form interface for recording tool maintenance activities,
including maintenance type, date, cost, and other related information.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from gui.base.base_dialog import BaseDialog
from gui.theme import COLORS
from utils.service_access import with_service


class ToolMaintenanceDialog(BaseDialog):
    """Dialog for managing tool maintenance records."""

    def __init__(self, parent, tool_id=None, maintenance_id=None, readonly=False):
        """Initialize the tool maintenance dialog.

        Args:
            parent: The parent widget
            tool_id: Optional tool ID when creating a new maintenance record for a specific tool
            maintenance_id: Optional maintenance record ID when editing an existing record
            readonly: Whether the dialog should be read-only
        """
        self.tool_id = tool_id
        self.maintenance_id = maintenance_id
        self.readonly = readonly
        self.logger = logging.getLogger(__name__)

        # Set title based on mode
        if readonly:
            title = "View Maintenance Record"
        elif maintenance_id:
            title = "Edit Maintenance Record"
        else:
            title = "Add Maintenance Record"

        super().__init__(parent, title=title, width=600, height=550)
        self.result = None

    def create_layout(self):
        """Create the dialog layout."""
        # Main frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create a canvas with scrollbar for the form
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.form_frame = ttk.Frame(canvas)

        # Configure canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create a window in the canvas for the form frame
        canvas_window = canvas.create_window((0, 0), window=self.form_frame, anchor="nw")

        # Configure canvas to adjust the window when the size of form_frame changes
        def configure_canvas(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Adjust the width of the window to match the canvas width
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())

        self.form_frame.bind("<Configure>", configure_canvas)

        # Create form fields
        self.create_form()

        # Load data if editing or viewing
        if self.maintenance_id:
            self.load_maintenance_record()

        # Buttons frame
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=20, pady=10)

        # Add buttons based on mode
        if self.readonly:
            ttk.Button(button_frame, text="Close", command=self.on_cancel).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="Edit", command=self.on_edit).pack(side=tk.RIGHT, padx=5)
        else:
            ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="Save", command=self.on_save, style="Accent.TButton").pack(side=tk.RIGHT,
                                                                                                     padx=5)

    def create_form(self):
        """Create form fields for the maintenance record."""
        # Store field variables and widgets
        self.field_vars = {}
        self.field_widgets = {}

        # Create fields with labels in a grid layout
        row = 0

        # Tool selection (only for new records without a tool_id)
        if not self.maintenance_id and not self.tool_id:
            ttk.Label(self.form_frame, text="Tool:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

            self.field_vars["tool_id"] = tk.StringVar()
            tool_combobox = ttk.Combobox(self.form_frame, textvariable=self.field_vars["tool_id"], state="readonly")
            tool_combobox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
            self.field_widgets["tool_id"] = tool_combobox

            # Load tools for the combobox
            self.load_tool_options(tool_combobox)

            row += 1
        elif self.tool_id or self.maintenance_id:
            # Show tool name as a label for existing records or when tool_id is provided
            ttk.Label(self.form_frame, text="Tool:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

            self.field_vars["tool_name"] = tk.StringVar()
            tool_label = ttk.Label(self.form_frame, textvariable=self.field_vars["tool_name"])
            tool_label.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

            if self.tool_id:
                # Load tool name
                self.load_tool_name(self.tool_id)

            row += 1

        # Maintenance Type
        ttk.Label(self.form_frame, text="Maintenance Type:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        self.field_vars["maintenance_type"] = tk.StringVar()
        type_combobox = ttk.Combobox(self.form_frame, textvariable=self.field_vars["maintenance_type"],
                                     state="readonly" if not self.readonly else "disabled")
        type_combobox["values"] = [
            "Routine", "Repair", "Calibration", "Inspection", "Part Replacement", "Other"
        ]
        type_combobox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
        self.field_widgets["maintenance_type"] = type_combobox

        row += 1

        # Date
        ttk.Label(self.form_frame, text="Date:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        date_frame = ttk.Frame(self.form_frame)
        date_frame.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        self.field_vars["maintenance_date"] = tk.StringVar()
        date_entry = ttk.Entry(date_frame, textvariable=self.field_vars["maintenance_date"],
                               state="normal" if not self.readonly else "readonly", width=15)
        date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.field_widgets["maintenance_date"] = date_entry

        if not self.readonly:
            ttk.Button(date_frame, text="...", width=3, command=lambda: self.show_date_picker(
                self.field_vars["maintenance_date"])).pack(side=tk.LEFT, padx=5)

        # Set default date to today
        if not self.maintenance_id:
            self.field_vars["maintenance_date"].set(datetime.now().strftime("%Y-%m-%d"))

        row += 1

        # Performed By
        ttk.Label(self.form_frame, text="Performed By:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        self.field_vars["performed_by"] = tk.StringVar()
        performed_by_entry = ttk.Entry(self.form_frame, textvariable=self.field_vars["performed_by"],
                                       state="normal" if not self.readonly else "readonly")
        performed_by_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
        self.field_widgets["performed_by"] = performed_by_entry

        row += 1

        # Cost
        ttk.Label(self.form_frame, text="Cost:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        cost_frame = ttk.Frame(self.form_frame)
        cost_frame.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        ttk.Label(cost_frame, text="$").pack(side=tk.LEFT)

        self.field_vars["cost"] = tk.StringVar()
        cost_entry = ttk.Entry(cost_frame, textvariable=self.field_vars["cost"], width=10,
                               state="normal" if not self.readonly else "readonly")
        cost_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.field_widgets["cost"] = cost_entry

        row += 1

        # Status
        ttk.Label(self.form_frame, text="Status:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        self.field_vars["status"] = tk.StringVar()
        status_combobox = ttk.Combobox(self.form_frame, textvariable=self.field_vars["status"],
                                       state="readonly" if not self.readonly else "disabled")
        status_combobox["values"] = ["Scheduled", "In Progress", "Completed", "Cancelled", "Delayed"]
        status_combobox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
        self.field_widgets["status"] = status_combobox

        # Set default status to Completed
        if not self.maintenance_id:
            self.field_vars["status"].set("Completed")

        row += 1

        # Next Maintenance Date
        ttk.Label(self.form_frame, text="Next Maintenance:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        next_date_frame = ttk.Frame(self.form_frame)
        next_date_frame.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        self.field_vars["next_maintenance_date"] = tk.StringVar()
        next_date_entry = ttk.Entry(next_date_frame, textvariable=self.field_vars["next_maintenance_date"],
                                    state="normal" if not self.readonly else "readonly", width=15)
        next_date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.field_widgets["next_maintenance_date"] = next_date_entry

        if not self.readonly:
            ttk.Button(next_date_frame, text="...", width=3, command=lambda: self.show_date_picker(
                self.field_vars["next_maintenance_date"])).pack(side=tk.LEFT, padx=5)

        row += 1

        # Set next maintenance interval (days)
        ttk.Label(self.form_frame, text="Interval (days):").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        self.field_vars["maintenance_interval"] = tk.StringVar()
        interval_entry = ttk.Entry(self.form_frame, textvariable=self.field_vars["maintenance_interval"],
                                   state="normal" if not self.readonly else "readonly", width=10)
        interval_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
        self.field_widgets["maintenance_interval"] = interval_entry

        # Button to calculate next date
        if not self.readonly:
            ttk.Button(self.form_frame, text="Calculate Next Date",
                       command=self.calculate_next_date).grid(row=row, column=1, padx=5, pady=5, sticky=tk.E)

        row += 1

        # Maintenance Details
        ttk.Label(self.form_frame, text="Details:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W + tk.N)

        self.field_vars["details"] = tk.StringVar()
        details_text = tk.Text(self.form_frame, height=5, width=40)
        details_text.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
        details_scrollbar = ttk.Scrollbar(self.form_frame, command=details_text.yview)
        details_scrollbar.grid(row=row, column=2, sticky=tk.N + tk.S)
        details_text.configure(yscrollcommand=details_scrollbar.set)

        if self.readonly:
            details_text.config(state="disabled")

        self.field_widgets["details"] = details_text

        row += 1

        # Parts Used
        ttk.Label(self.form_frame, text="Parts Used:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W + tk.N)

        self.field_vars["parts_used"] = tk.StringVar()
        parts_text = tk.Text(self.form_frame, height=3, width=40)
        parts_text.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
        parts_scrollbar = ttk.Scrollbar(self.form_frame, command=parts_text.yview)
        parts_scrollbar.grid(row=row, column=2, sticky=tk.N + tk.S)
        parts_text.configure(yscrollcommand=parts_scrollbar.set)

        if self.readonly:
            parts_text.config(state="disabled")

        self.field_widgets["parts_used"] = parts_text

        # Configure column weights
        self.form_frame.columnconfigure(1, weight=1)

    @with_service("tool_service")
    def load_tool_options(self, combobox, service=None):
        """Load tool options for the combobox.

        Args:
            combobox: The combobox widget to populate
            service: The tool service injected by the decorator
        """
        try:
            # Get all tools
            tools = service.get_tools(limit=100)

            # Format for combobox
            tool_options = {}
            tool_values = []

            for tool in tools:
                tool_options[str(tool.id)] = tool.name
                tool_values.append(f"{tool.name} (ID: {tool.id})")

            combobox["values"] = tool_values

            # Store the mapping of display values to IDs
            self.tool_options = tool_options
            self.tool_displays = {f"{name} (ID: {id})": id for id, name in tool_options.items()}

            # Set up callback to update the tool_id when selection changes
            def on_tool_select(event):
                selected = combobox.get()
                if selected in self.tool_displays:
                    self.field_vars["tool_id"].set(self.tool_displays[selected])

            combobox.bind("<<ComboboxSelected>>", on_tool_select)

        except Exception as e:
            self.logger.error(f"Error loading tool options: {e}")
            messagebox.showerror("Error", f"Failed to load tool options: {str(e)}")

    @with_service("tool_service")
    def load_tool_name(self, tool_id, service=None):
        """Load tool name for display.

        Args:
            tool_id: The ID of the tool
            service: The tool service injected by the decorator
        """
        try:
            # Get tool
            tool = service.get_tool_by_id(tool_id)

            if tool:
                self.field_vars["tool_name"].set(tool.name)
                # Store tool_id for saving
                self.field_vars["tool_id"] = tk.StringVar(value=str(tool_id))
            else:
                self.field_vars["tool_name"].set("Unknown Tool")

        except Exception as e:
            self.logger.error(f"Error loading tool name: {e}")
            self.field_vars["tool_name"].set("Error loading tool")

    @with_service("tool_maintenance_service")
    def load_maintenance_record(self, service=None):
        """Load maintenance record data for editing or viewing.

        Args:
            service: The tool maintenance service injected by the decorator
        """
        try:
            # Get maintenance record
            record = service.get_maintenance_record_by_id(self.maintenance_id, include_tool=True)

            if not record:
                messagebox.showerror("Error", f"Maintenance record with ID {self.maintenance_id} not found")
                self.on_cancel()
                return

            # Set tool name
            if hasattr(record, "tool") and record.tool:
                self.field_vars["tool_name"].set(record.tool.name)
                self.field_vars["tool_id"] = tk.StringVar(value=str(record.tool_id))

            # Set field values
            if hasattr(record, "maintenance_type"):
                self.field_vars["maintenance_type"].set(record.maintenance_type.capitalize()
                                                        if hasattr(record.maintenance_type, "capitalize") else "")

            if hasattr(record, "maintenance_date") and record.maintenance_date:
                self.field_vars["maintenance_date"].set(record.maintenance_date.strftime("%Y-%m-%d"))

            if hasattr(record, "performed_by"):
                self.field_vars["performed_by"].set(record.performed_by or "")

            if hasattr(record, "cost"):
                self.field_vars["cost"].set(str(record.cost) if record.cost is not None else "")

            if hasattr(record, "status"):
                self.field_vars["status"].set(record.status.capitalize()
                                              if hasattr(record.status, "capitalize") else "")

            if hasattr(record, "next_maintenance_date") and record.next_maintenance_date:
                self.field_vars["next_maintenance_date"].set(record.next_maintenance_date.strftime("%Y-%m-%d"))

            if hasattr(record, "maintenance_interval"):
                self.field_vars["maintenance_interval"].set(str(record.maintenance_interval or ""))

            # Set text widgets
            if hasattr(record, "details"):
                details_widget = self.field_widgets["details"]
                details_widget.delete("1.0", tk.END)
                details_widget.insert("1.0", record.details or "")

            if hasattr(record, "parts_used"):
                parts_widget = self.field_widgets["parts_used"]
                parts_widget.delete("1.0", tk.END)
                parts_widget.insert("1.0", record.parts_used or "")

        except Exception as e:
            self.logger.error(f"Error loading maintenance record: {e}")
            messagebox.showerror("Error", f"Failed to load maintenance record: {str(e)}")
            self.on_cancel()

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

    def calculate_next_date(self):
        """Calculate the next maintenance date based on the current date and interval."""
        try:
            # Get current date
            date_str = self.field_vars["maintenance_date"].get()
            if not date_str:
                messagebox.showwarning("Missing Date", "Please enter a maintenance date first")
                return

            # Get interval
            interval_str = self.field_vars["maintenance_interval"].get()
            if not interval_str:
                messagebox.showwarning("Missing Interval", "Please enter a maintenance interval in days")
                return

            # Parse date and interval
            date = datetime.strptime(date_str, "%Y-%m-%d")
            interval = int(interval_str)

            # Calculate next date
            next_date = date + timedelta(days=interval)

            # Set next date
            self.field_vars["next_maintenance_date"].set(next_date.strftime("%Y-%m-%d"))

        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Invalid date or interval: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error calculating next date: {e}")
            messagebox.showerror("Error", f"Failed to calculate next date: {str(e)}")

    def validate_form(self):
        """Validate form data.

        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        required_fields = ["maintenance_type", "maintenance_date", "status"]

        # Add tool_id if not editing
        if not self.maintenance_id and not self.tool_id:
            required_fields.append("tool_id")

        # Check each required field
        for field in required_fields:
            if field not in self.field_vars or not self.field_vars[field].get():
                messagebox.showwarning("Missing Information",
                                       f"Please enter a value for {field.replace('_', ' ').title()}")
                return False

        # Validate date format
        date_fields = ["maintenance_date", "next_maintenance_date"]
        for field in date_fields:
            if field in self.field_vars and self.field_vars[field].get():
                try:
                    datetime.strptime(self.field_vars[field].get(), "%Y-%m-%d")
                except ValueError:
                    messagebox.showwarning("Invalid Date",
                                           f"Please enter a valid date in format YYYY-MM-DD for {field.replace('_', ' ').title()}")
                    return False

        # Validate numeric fields
        if self.field_vars["cost"].get():
            try:
                cost = float(self.field_vars["cost"].get())
                if cost < 0:
                    messagebox.showwarning("Invalid Cost", "Cost cannot be negative")
                    return False
            except ValueError:
                messagebox.showwarning("Invalid Cost", "Please enter a valid number for Cost")
                return False

        if self.field_vars["maintenance_interval"].get():
            try:
                interval = int(self.field_vars["maintenance_interval"].get())
                if interval < 0:
                    messagebox.showwarning("Invalid Interval", "Maintenance interval cannot be negative")
                    return False
            except ValueError:
                messagebox.showwarning("Invalid Interval", "Please enter a valid number for Maintenance Interval")
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
            if field not in ["details", "parts_used"]:  # These are handled separately
                data[field] = var.get()

        # Text widgets
        data["details"] = self.field_widgets["details"].get("1.0", tk.END).strip()
        data["parts_used"] = self.field_widgets["parts_used"].get("1.0", tk.END).strip()

        # Convert numeric fields
        if data.get("cost"):
            try:
                data["cost"] = float(data["cost"])
            except ValueError:
                data["cost"] = None

        if data.get("maintenance_interval"):
            try:
                data["maintenance_interval"] = int(data["maintenance_interval"])
            except ValueError:
                data["maintenance_interval"] = None

        # Convert dates
        date_fields = ["maintenance_date", "next_maintenance_date"]
        for field in date_fields:
            if data.get(field):
                try:
                    data[field] = datetime.strptime(data[field], "%Y-%m-%d")
                except ValueError:
                    data[field] = None

        # Convert tool_id to integer
        if data.get("tool_id"):
            try:
                data["tool_id"] = int(data["tool_id"])
            except ValueError:
                data["tool_id"] = None

        return data

    @with_service("tool_maintenance_service")
    def on_save(self, service=None):
        """Save the maintenance record.

        Args:
            service: The tool maintenance service injected by the decorator
        """
        # Validate form
        if not self.validate_form():
            return

        try:
            # Collect form data
            data = self.collect_form_data()

            # Save record
            if self.maintenance_id:
                # Update existing record
                result = service.update_maintenance_record(self.maintenance_id, data)
                messagebox.showinfo("Success", "Maintenance record updated successfully")
            else:
                # Create new record
                result = service.create_maintenance_record(data)
                messagebox.showinfo("Success", "Maintenance record created successfully")

            # Store result and close dialog
            self.result = result
            self.close()

        except Exception as e:
            self.logger.error(f"Error saving maintenance record: {e}")
            messagebox.showerror("Error", f"Failed to save maintenance record: {str(e)}")

    def on_edit(self):
        """Switch from view mode to edit mode."""
        # Create a new dialog in edit mode
        dialog = ToolMaintenanceDialog(self.parent, maintenance_id=self.maintenance_id, readonly=False)

        # Close this dialog
        self.close()