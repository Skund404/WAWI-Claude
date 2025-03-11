# gui/views/tools/tool_checkout_dialog.py
"""
Dialog for checking out tools in the leatherworking ERP system.

This dialog provides a form interface for checking out tools to users,
including selecting the tool, user, due date, and project.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from gui.base.base_dialog import BaseDialog
from gui.theme import COLORS
from utils.service_access import with_service


class ToolCheckoutDialog(BaseDialog):
    """Dialog for checking out tools."""

    def __init__(self, parent, tool_id=None):
        """Initialize the tool checkout dialog.

        Args:
            parent: The parent widget
            tool_id: Optional tool ID if checking out a specific tool
        """
        self.tool_id = tool_id
        self.logger = logging.getLogger(__name__)

        super().__init__(parent, title="Check Out Tool", width=500, height=400)
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
        ttk.Button(button_frame, text="Check Out", command=self.on_checkout,
                   style="Accent.TButton").pack(side=tk.RIGHT, padx=5)

    def create_form(self, parent):
        """Create form fields for the checkout.

        Args:
            parent: The parent widget
        """
        # Store field variables and widgets
        self.field_vars = {}
        self.field_widgets = {}

        # Create fields with labels in a grid layout
        row = 0

        # Tool selection (only if tool_id is not provided)
        if not self.tool_id:
            ttk.Label(parent, text="Tool:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

            self.field_vars["tool_id"] = tk.StringVar()
            tool_combobox = ttk.Combobox(parent, textvariable=self.field_vars["tool_id"], state="readonly")
            tool_combobox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
            self.field_widgets["tool_id"] = tool_combobox

            # Load tools for the combobox
            self.load_available_tools(tool_combobox)

            row += 1
        else:
            # Show tool name as a label for existing records or when tool_id is provided
            ttk.Label(parent, text="Tool:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

            self.field_vars["tool_name"] = tk.StringVar()
            tool_label = ttk.Label(parent, textvariable=self.field_vars["tool_name"])
            tool_label.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

            # Store tool_id
            self.field_vars["tool_id"] = tk.StringVar(value=str(self.tool_id))

            # Load tool name
            self.load_tool_name(self.tool_id)

            row += 1

        # User
        ttk.Label(parent, text="Checked Out By:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        self.field_vars["checked_out_by"] = tk.StringVar()
        checked_out_by_entry = ttk.Entry(parent, textvariable=self.field_vars["checked_out_by"])
        checked_out_by_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
        self.field_widgets["checked_out_by"] = checked_out_by_entry

        row += 1

        # Checkout Date
        ttk.Label(parent, text="Checkout Date:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        date_frame = ttk.Frame(parent)
        date_frame.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        self.field_vars["checked_out_date"] = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = ttk.Entry(date_frame, textvariable=self.field_vars["checked_out_date"], width=15)
        date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.field_widgets["checked_out_date"] = date_entry

        ttk.Button(date_frame, text="...", width=3, command=lambda: self.show_date_picker(
            self.field_vars["checked_out_date"])).pack(side=tk.LEFT, padx=5)

        row += 1

        # Due Date
        ttk.Label(parent, text="Due Date:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        due_date_frame = ttk.Frame(parent)
        due_date_frame.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        # Default due date is a week from today
        default_due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        self.field_vars["due_date"] = tk.StringVar(value=default_due_date)
        due_date_entry = ttk.Entry(due_date_frame, textvariable=self.field_vars["due_date"], width=15)
        due_date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.field_widgets["due_date"] = due_date_entry

        ttk.Button(due_date_frame, text="...", width=3, command=lambda: self.show_date_picker(
            self.field_vars["due_date"])).pack(side=tk.LEFT, padx=5)

        row += 1

        # Project (optional)
        ttk.Label(parent, text="Project:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        self.field_vars["project_id"] = tk.StringVar()
        project_combobox = ttk.Combobox(parent, textvariable=self.field_vars["project_id"], state="readonly")
        project_combobox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
        self.field_widgets["project_id"] = project_combobox

        # Load projects for the combobox
        self.load_active_projects(project_combobox)

        row += 1

        # Condition Before
        ttk.Label(parent, text="Condition:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        self.field_vars["condition_before"] = tk.StringVar()
        condition_combobox = ttk.Combobox(parent, textvariable=self.field_vars["condition_before"], state="readonly")
        condition_combobox["values"] = ["Excellent", "Good", "Fair", "Poor"]
        condition_combobox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
        self.field_widgets["condition_before"] = condition_combobox
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

    @with_service("tool_service")
    def load_available_tools(self, combobox, service=None):
        """Load available tools for the combobox.

        Args:
            combobox: The combobox widget to populate
            service: The tool service injected by the decorator
        """
        try:
            # Get available tools (not checked out or damaged)
            tools = service.get_tools(
                criteria={"status": "IN_STOCK"},
                limit=100
            )

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
            self.logger.error(f"Error loading available tools: {e}")
            messagebox.showerror("Error", f"Failed to load available tools: {str(e)}")

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
            else:
                self.field_vars["tool_name"].set("Unknown Tool")

        except Exception as e:
            self.logger.error(f"Error loading tool name: {e}")
            self.field_vars["tool_name"].set("Error loading tool")

    @with_service("project_service")
    def load_active_projects(self, combobox, service=None):
        """Load active projects for the combobox.

        Args:
            combobox: The combobox widget to populate
            service: The project service injected by the decorator
        """
        try:
            # Get active projects
            projects = service.get_projects(
                criteria={"status__in": ["IN_PROGRESS", "PLANNED"]},
                limit=100
            )

            # Format for combobox
            project_options = {}
            project_values = ["(None)"]  # Always include a "None" option

            for project in projects:
                project_options[str(project.id)] = project.name
                project_values.append(f"{project.name} (ID: {project.id})")

            combobox["values"] = project_values

            # Store the mapping of display values to IDs
            self.project_options = project_options
            self.project_displays = {f"{name} (ID: {id})": id for id, name in project_options.items()}
            self.project_displays["(None)"] = ""  # Map "None" option to empty string

            # Set up callback to update the project_id when selection changes
            def on_project_select(event):
                selected = combobox.get()
                if selected in self.project_displays:
                    self.field_vars["project_id"].set(self.project_displays[selected])

            combobox.bind("<<ComboboxSelected>>", on_project_select)

            # Default to "(None)"
            combobox.current(0)

        except Exception as e:
            self.logger.error(f"Error loading active projects: {e}")
            messagebox.showerror("Error", f"Failed to load active projects: {str(e)}")

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
        required_fields = ["tool_id", "checked_out_by"]

        for field in required_fields:
            if field not in self.field_vars or not self.field_vars[field].get():
                messagebox.showwarning("Missing Information",
                                       f"Please select a value for {field.replace('_', ' ').title()}")
                return False

        # Validate date formats
        date_fields = ["checked_out_date", "due_date"]
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
            if field != "tool_name":  # Skip display-only fields
                data[field] = var.get()

        # Text widgets
        data["notes"] = self.field_widgets["notes"].get("1.0", tk.END).strip()

        # Convert empty strings to None for optional fields
        for field in ["project_id", "notes"]:
            if field in data and data[field] == "":
                data[field] = None

        # Convert string IDs to integers
        for field in ["tool_id", "project_id"]:
            if field in data and data[field]:
                try:
                    data[field] = int(data[field])
                except ValueError:
                    data[field] = None

        # Convert dates from string to datetime
        for field in ["checked_out_date", "due_date"]:
            if field in data and data[field]:
                try:
                    data[field] = datetime.strptime(data[field], "%Y-%m-%d")
                except ValueError:
                    data[field] = None

        return data

    @with_service("tool_checkout_service")
    def on_checkout(self, service=None):
        """Handle tool checkout.

        Args:
            service: The tool checkout service injected by the decorator
        """
        # Validate form
        if not self.validate_form():
            return

        try:
            # Collect form data
            data = self.collect_form_data()

            # Get tool_id from form data
            tool_id = data.pop("tool_id")

            # Checkout the tool
            result = service.checkout_tool(tool_id, data)

            messagebox.showinfo("Success", "Tool checked out successfully")

            # Store result and close dialog
            self.result = result
            self.close()

        except Exception as e:
            self.logger.error(f"Error checking out tool: {e}")
            messagebox.showerror("Error", f"Failed to check out tool: {str(e)}")