


# gui/sale/picking_list_view.py
import logging
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox, filedialog
from typing import Any, Dict, List, Optional
import os
import csv

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from gui.base_view import BaseView
from services.interfaces.picking_list_service import IPickingListService
from database.models.picking_list import PickingListStatus
from services.interfaces.project_service import IProjectService
from services.interfaces.sale_service import ISaleService

from utils.error_handler import ApplicationError, NotFoundError, ValidationError


class PickingListView(BaseView):
    """View for managing picking lists."""

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the Picking List View.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)

        # Initialize logger
        self.logger = logging.getLogger(__name__)

        # Services
        self.picking_list_service: Optional[IPickingListService] = None
        self.project_service: Optional[IProjectService] = None
        self.order_service: Optional[ISaleService] = None

        # UI Components
        self.lists_tree: Optional[ttk.Treeview] = None
        self.items_tree: Optional[ttk.Treeview] = None
        self.status_var: Optional[tk.StringVar] = None

        # Current state
        self.current_picking_list: Optional[Dict[str, Any]] = None
        self.current_picking_list_id: Optional[int] = None

        # Setup the view
        self._setup_ui()

        # Initial data load
        self._load_data()

    def _setup_ui(self):
        """Set up the user interface."""
        # Create main layout
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create paned window to split screen
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Left side - picking lists
        self.lists_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.lists_frame, weight=1)

        # Right side - picking list details
        self.details_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.details_frame, weight=2)

        # Set up list frame
        self._setup_lists_frame()

        # Set up details frame
        self._setup_details_frame()

        # Set up sorting
        self._setup_sorting()

        # Set up search
        self._setup_search()

    def _setup_lists_frame(self):
        """Set up the lists frame with picking list selection."""
        # Toolbar
        toolbar = ttk.Frame(self.lists_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # Add buttons
        ttk.Button(toolbar, text="New", command=self._create_picking_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Delete", command=self._delete_picking_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Refresh", command=self.on_refresh).pack(side=tk.LEFT, padx=5)

        # Filter by status
        ttk.Label(toolbar, text="Status:").pack(side=tk.LEFT, padx=(20, 5))
        self.status_var = tk.StringVar(value="All")
        status_values = ["All"] + [status.name for status in PickingListStatus]
        self.status_combo = ttk.Combobox(toolbar, textvariable=self.status_var, values=status_values, width=15)
        self.status_combo.pack(side=tk.LEFT, padx=5)
        self.status_combo.bind("<<ComboboxSelected>>", self._filter_lists)

        # Create treeview for picking lists
        columns = ("id", "name", "status", "items", "priority")
        self.lists_tree = ttk.Treeview(self.lists_frame, columns=columns, show="headings", selectmode="browse")

        # Configure columns
        self.lists_tree.heading("id", text="ID")
        self.lists_tree.heading("name", text="Name")
        self.lists_tree.heading("status", text="Status")
        self.lists_tree.heading("items", text="Items")
        self.lists_tree.heading("priority", text="Priority")

        # Column widths
        self.lists_tree.column("id", width=40, stretch=False)
        self.lists_tree.column("name", width=180)
        self.lists_tree.column("status", width=100)
        self.lists_tree.column("items", width=60, anchor=tk.CENTER)
        self.lists_tree.column("priority", width=60, anchor=tk.CENTER)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.lists_frame, orient=tk.VERTICAL, command=self.lists_tree.yview)
        self.lists_tree.configure(yscrollcommand=scrollbar.set)

        # Pack
        self.lists_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind selection event
        self.lists_tree.bind("<<TreeviewSelect>>", self._on_list_select)

    def _setup_details_frame(self):
        """Set up the details frame with picking list items."""
        # Details header
        self.details_header = ttk.Frame(self.details_frame)
        self.details_header.pack(fill=tk.X, pady=(0, 10))

        # List info
        self.list_info_frame = ttk.LabelFrame(self.details_header, text="Picking List Information")
        self.list_info_frame.pack(fill=tk.X, pady=5)

        # List info grid
        info_grid = ttk.Frame(self.list_info_frame)
        info_grid.pack(fill=tk.X, padx=10, pady=10)

        # List name
        ttk.Label(info_grid, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.list_name_var = tk.StringVar()
        self.list_name_entry = ttk.Entry(info_grid, textvariable=self.list_name_var, width=40)
        self.list_name_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        # List status
        ttk.Label(info_grid, text="Status:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.list_status_var = tk.StringVar()
        status_values = [status.name for status in PickingListStatus]
        self.list_status_combo = ttk.Combobox(info_grid, textvariable=self.list_status_var, values=status_values,
                                              width=15)
        self.list_status_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        # List priority
        ttk.Label(info_grid, text="Priority:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.list_priority_var = tk.StringVar()
        priority_values = ["0 (Normal)", "1 (High)", "2 (Urgent)"]
        self.list_priority_combo = ttk.Combobox(info_grid, textvariable=self.list_priority_var, values=priority_values,
                                                width=15)
        self.list_priority_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # Assigned to
        ttk.Label(info_grid, text="Assigned To:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.list_assigned_var = tk.StringVar()
        self.list_assigned_entry = ttk.Entry(info_grid, textvariable=self.list_assigned_var, width=20)
        self.list_assigned_entry.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)

        # Notes
        ttk.Label(info_grid, text="Notes:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.list_notes_text = tk.Text(info_grid, height=2, width=60)
        self.list_notes_text.grid(row=2, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)

        # Save button
        self.save_button = ttk.Button(info_grid, text="Save Changes", command=self._save_picking_list)
        self.save_button.grid(row=3, column=3, sticky=tk.E, padx=5, pady=5)

        # Items toolbar
        items_toolbar = ttk.Frame(self.details_frame)
        items_toolbar.pack(fill=tk.X, pady=(10, 5))

        ttk.Label(items_toolbar, text="Items").pack(side=tk.LEFT)
        ttk.Button(items_toolbar, text="Add Item", command=self._add_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(items_toolbar, text="Remove Item", command=self._remove_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(items_toolbar, text="Mark Picked", command=self._mark_item_picked).pack(side=tk.LEFT, padx=5)
        ttk.Button(items_toolbar, text="Batch Operations", command=self._show_batch_operations).pack(side=tk.LEFT,
                                                                                                     padx=5)

        # Add the new Bulk Import button
        ttk.Button(items_toolbar, text="Bulk Import", command=self._import_items_from_file).pack(side=tk.LEFT, padx=5)

        ttk.Button(items_toolbar, text="Print List", command=self._print_picking_list).pack(side=tk.RIGHT, padx=5)

        # Create treeview for items
        columns = ("id", "type", "name", "required", "picked", "unit", "location", "status")
        self.items_tree = ttk.Treeview(self.details_frame, columns=columns, show="headings", selectmode="browse")

        # Configure columns
        self.items_tree.heading("id", text="ID")
        self.items_tree.heading("type", text="Type")
        self.items_tree.heading("name", text="Item")
        self.items_tree.heading("required", text="Required")
        self.items_tree.heading("picked", text="Picked")
        self.items_tree.heading("unit", text="Unit")
        self.items_tree.heading("location", text="Location")
        self.items_tree.heading("status", text="Status")

        # Column widths
        self.items_tree.column("id", width=40, stretch=False)
        self.items_tree.column("type", width=80)
        self.items_tree.column("name", width=200)
        self.items_tree.column("required", width=70, anchor=tk.CENTER)
        self.items_tree.column("picked", width=70, anchor=tk.CENTER)
        self.items_tree.column("unit", width=60, anchor=tk.CENTER)
        self.items_tree.column("location", width=120)
        self.items_tree.column("status", width=80, anchor=tk.CENTER)

        # Add scrollbar
        items_scrollbar = ttk.Scrollbar(self.details_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=items_scrollbar.set)

        # Pack
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        items_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click event for editing items
        self.items_tree.bind("<Double-1>", self._edit_item)

        # Initially disable details section
        self._toggle_details(False)

    def _setup_sorting(self):
        """Set up sorting capability for the items treeview."""
        # Track sort column and direction
        self.sort_by = None
        self.sort_ascending = True

        # Configure all column headings to trigger sort
        for col in self.items_tree["columns"]:
            self.items_tree.heading(col, command=lambda _col=col: self._sort_column(_col))

    def _sort_column(self, column):
        """Sort the items treeview by the specified column."""
        try:
            items = [(self.items_tree.set(item, column), item) for item in self.items_tree.get_children('')]

            # If clicking the same column, reverse the sort direction
            if self.sort_by == column:
                self.sort_ascending = not self.sort_ascending
            else:
                self.sort_ascending = True
                self.sort_by = column

            # Store the sort indicators in the headings
            for col in self.items_tree["columns"]:
                # Remove existing sort indicators
                text = self.items_tree.heading(col)["text"]
                if text.endswith(" ▲") or text.endswith(" ▼"):
                    text = text[:-2]
                self.items_tree.heading(col, text=text)

            # Add sort indicator to current column
            current_text = self.items_tree.heading(column)["text"]
            direction_indicator = " ▲" if self.sort_ascending else " ▼"
            self.items_tree.heading(column, text=current_text + direction_indicator)

            # Convert to appropriate types before sorting
            def convert_value(value, col=column):
                if col in ("required", "picked"):
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return 0.0
                elif col == "id":
                    try:
                        return int(value)
                    except (ValueError, TypeError):
                        return 0
                return str(value).lower()

            # Sort the items
            items.sort(key=lambda x: convert_value(x[0]), reverse=not self.sort_ascending)

            # Rearrange items in sorted positions
            for index, (_, item) in enumerate(items):
                self.items_tree.move(item, '', index)

        except Exception as e:
            self.logger.error(f"Error sorting column: {str(e)}")

    def _setup_search(self):
        """Set up search functionality for the items list."""
        # Create search frame
        search_frame = ttk.Frame(self.details_header)
        search_frame.pack(fill=tk.X, pady=5)

        # Create search entry and button
        ttk.Label(search_frame, text="Search Items:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(search_frame, text="Search", command=self._search_items).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Clear", command=self._clear_search).pack(side=tk.LEFT, padx=5)

        # Add status filter
        ttk.Label(search_frame, text="Status:").pack(side=tk.LEFT, padx=(20, 5))
        self.item_status_var = tk.StringVar(value="All")
        item_status_combo = ttk.Combobox(search_frame, textvariable=self.item_status_var,
                                         values=["All", "Pending", "Picked"], width=10, state="readonly")
        item_status_combo.pack(side=tk.LEFT, padx=5)
        item_status_combo.bind("<<ComboboxSelected>>", lambda e: self._search_items())

        # Bind Enter key for search
        search_entry.bind("<Return>", lambda e: self._search_items())

    def _load_data(self):
        """
        Load picking lists data from the service.
        """
        try:
            # Clear existing items
            for i in self.lists_tree.get_children():
                self.lists_tree.delete(i)

            # Retrieve picking lists
            if not self.picking_list_service:
                self.picking_list_service = self.app.get_service(IPickingListService)

            # Fetch lists
            picking_lists = self.picking_list_service.get_all()

            # Populate treeview
            for pl in picking_lists:
                # Make sure we have all required fields with fallbacks
                list_id = pl.get('id', 0)
                name = pl.get('name', 'Unnamed List')
                status = pl.get('status', PickingListStatus.DRAFT.name)
                # Calculate the number of items if available
                items_count = len(pl.get('items', []))
                # Default priority is normal (0)
                priority = self._format_priority(pl.get('priority', 0))

                self.lists_tree.insert('', 'end', values=(
                    list_id,
                    name,
                    status,
                    items_count,
                    priority
                ))

            logging.info(f"Loaded {len(picking_lists)} picking lists")

        except Exception as e:
            logging.exception("Error loading picking lists")
            messagebox.showerror("Load Error", str(e))

    def _format_priority(self, priority: int) -> str:
        """Format priority as string."""
        if priority == 0:
            return "Normal"
        elif priority == 1:
            return "High"
        elif priority == 2:
            return "Urgent"
        else:
            return str(priority)

    def _filter_lists(self, event=None):
        """Filter picking lists by status."""
        self._load_data()

    def on_refresh(self):
        """
        Refresh the picking lists view.
        """
        self._load_data()

    def _on_list_select(self, event=None):
        """
        Handle picking list selection.

        Args:
            event: Optional event that triggered the selection
        """
        try:
            # Get the selected item
            selected_item = self.lists_tree.selection()
            if not selected_item:
                # Clear previous data
                self._clear_details()
                # Disable details section
                self._toggle_details(False)
                return

            # Get the list ID from the selected item
            list_id = self.lists_tree.item(selected_item[0], 'values')[0]

            # Enable details section
            self._toggle_details(True)

            # Clear previous items
            for i in self.items_tree.get_children():
                self.items_tree.delete(i)

            # Fetch list details from service
            if not self.picking_list_service:
                self.picking_list_service = self.app.get_service(IPickingListService)

            # Retrieve picking list details with ID
            picking_list = self.picking_list_service.get_picking_list(int(list_id))

            # Store the current picking list data
            self.current_picking_list = picking_list
            self.current_picking_list_id = picking_list['id']

            # Populate details
            self._populate_details(picking_list)

            logging.info(f"Selected picking list: {picking_list['name']}")

        except Exception as e:
            logging.exception(f"Error selecting picking list: {e}")
            messagebox.showerror("Selection Error", str(e))

    def _populate_details(self, picking_list: Dict[str, Any]):
        """Populate picking list details."""
        # Update header info
        self.current_picking_list_id = picking_list["id"]

        # Update form fields
        self.list_name_var.set(picking_list["name"])
        self.list_status_var.set(picking_list["status"])

        # Handle priority in a more robust way
        priority = picking_list.get('priority', 0)
        priority_text = f"{priority} ({self._format_priority(priority)})"
        self.list_priority_var.set(priority_text)

        self.list_assigned_var.set(picking_list.get("assigned_to", ""))

        # Update notes
        self.list_notes_text.delete("1.0", tk.END)
        self.list_notes_text.insert("1.0", picking_list.get("notes", ""))

        # Clear items
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)

        # Populate items
        for item in picking_list.get("items", []):
            # Determine status
            status = "Picked" if item.get("is_picked") else "Pending"

            # Format location
            location = item.get("storage_location", "Unknown")
            if isinstance(location, dict):
                location_parts = []
                if location.get("section"):
                    location_parts.append(location["section"])
                if location.get("shelf"):
                    location_parts.append(f"Shelf {location['shelf']}")
                if location.get("bin"):
                    location_parts.append(f"Bin {location['bin']}")
                if location_parts:
                    location = " - ".join(location_parts)
                else:
                    location = location.get("name", "Unknown")

            # Insert item
            self.items_tree.insert("", tk.END, values=(
                item["id"],
                item.get("item_type", "Unknown"),
                item["name"],
                item["required_quantity"],
                item.get("picked_quantity", 0),
                item["unit"],
                location,
                status
            ))

    def _clear_details(self):
        """Clear picking list details."""
        self.current_picking_list_id = None
        self.current_picking_list = None

        # Clear form fields
        self.list_name_var.set("")
        self.list_status_var.set("")
        self.list_priority_var.set("")
        self.list_assigned_var.set("")

        # Clear notes
        self.list_notes_text.delete("1.0", tk.END)

        # Clear items
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)

    def _toggle_details(self, enable: bool):
        """Enable or disable details section."""
        state = "normal" if enable else "disabled"

        # Update form fields
        self.list_name_entry.config(state=state)
        self.list_status_combo.config(state=state)
        self.list_priority_combo.config(state=state)
        self.list_assigned_entry.config(state=state)
        self.list_notes_text.config(state=state)

        # Update buttons
        self.save_button.config(state=state)

    def _create_picking_list(self):
        """Create a new picking list."""
        try:
            # Check if services are available
            if not self.picking_list_service:
                self.picking_list_service = self.app.get_service(IPickingListService)

            if not self.project_service:
                self.project_service = self.app.get_service(IProjectService)

            if not self.order_service:
                self.order_service = self.app.get_service(ISaleService)

            # Create dialog
            dialog = tk.Toplevel(self)
            dialog.title("Create New Picking List")
            dialog.geometry("500x400")
            dialog.transient(self)
            dialog.grab_set()

            # Create form frame
            form_frame = ttk.Frame(dialog, padding=10)
            form_frame.pack(fill=tk.BOTH, expand=True)

            # Basic info section
            basic_frame = ttk.LabelFrame(form_frame, text="Basic Information")
            basic_frame.pack(fill=tk.X, pady=10)

            basic_grid = ttk.Frame(basic_frame)
            basic_grid.pack(fill=tk.X, padx=10, pady=10)

            # Name
            ttk.Label(basic_grid, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            name_var = tk.StringVar()
            name_entry = ttk.Entry(basic_grid, textvariable=name_var, width=40)
            name_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

            # Status
            ttk.Label(basic_grid, text="Status:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
            status_var = tk.StringVar(value=PickingListStatus.DRAFT.name)
            status_combo = ttk.Combobox(basic_grid, textvariable=status_var,
                                        values=[s.name for s in PickingListStatus], width=20)
            status_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

            # Priority
            ttk.Label(basic_grid, text="Priority:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
            priority_var = tk.StringVar(value="0 (Normal)")
            priority_combo = ttk.Combobox(basic_grid, textvariable=priority_var,
                                          values=["0 (Normal)", "1 (High)", "2 (Urgent)"], width=20)
            priority_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

            # Assigned To
            ttk.Label(basic_grid, text="Assigned To:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
            assigned_var = tk.StringVar()
            assigned_entry = ttk.Entry(basic_grid, textvariable=assigned_var, width=40)
            assigned_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

            # Notes
            ttk.Label(basic_grid, text="Notes:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
            notes_text = tk.Text(basic_grid, height=3, width=40)
            notes_text.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)

            # Generation section
            gen_frame = ttk.LabelFrame(form_frame, text="Generate From")
            gen_frame.pack(fill=tk.X, pady=10)

            gen_grid = ttk.Frame(gen_frame)
            gen_grid.pack(fill=tk.X, padx=10, pady=10)

            # Project selection
            ttk.Label(gen_grid, text="Project:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            project_var = tk.StringVar()

            # Get projects
            projects = []
            try:
                projects = self.project_service.get_all_projects()
            except Exception as e:
                self.logger.error(f"Error loading projects: {str(e)}")

            project_combo = ttk.Combobox(gen_grid, textvariable=project_var,
                                         values=[f"{p['id']}: {p['name']}" for p in projects], width=40)
            project_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

            # OR label
            ttk.Label(gen_grid, text="OR").grid(row=1, column=0, columnspan=2, pady=5)

            # Order selection
            ttk.Label(gen_grid, text="Order:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
            order_var = tk.StringVar()

            # Get orders
            orders = []
            try:
                orders = self.order_service.get_all_sales()
            except Exception as e:
                self.logger.error(f"Error loading orders: {str(e)}")

            order_combo = ttk.Combobox(gen_grid, textvariable=order_var,
                                       values=[f"{o['id']}: {o.get('reference_number', 'Order ' + str(o['id']))}" for o
                                               in orders], width=40)
            order_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

            # Buttons
            button_frame = ttk.Frame(form_frame)
            button_frame.pack(fill=tk.X, pady=10)

            def create_empty():
                """Create empty picking list."""
                try:
                    # Validate name
                    if not name_var.get().strip():
                        messagebox.showerror("Error", "Picking list name is required")
                        return

                    # Extract priority number from combo value
                    priority_str = priority_var.get().split(' ')[0]
                    try:
                        priority = int(priority_str)
                    except ValueError:
                        priority = 0

                    # Create data
                    picking_list_data = {
                        "name": name_var.get().strip(),
                        "status": status_var.get(),
                        "priority": priority,
                        "assigned_to": assigned_var.get().strip(),
                        "notes": notes_text.get("1.0", tk.END).strip()
                    }

                    # Create picking list
                    result = self.picking_list_service.create_list(picking_list_data)
                    if result:
                        messagebox.showinfo("Success", "Picking list created successfully")
                        dialog.destroy()
                        self.on_refresh()

                except Exception as e:
                    self.logger.error(f"Error creating picking list: {str(e)}")
                    messagebox.showerror("Error", f"Failed to create picking list: {str(e)}")

            def create_from_project():
                """Create picking list from project."""
                try:
                    # Check if project selected
                    project_str = project_var.get()
                    if not project_str:
                        messagebox.showerror("Error", "Please select a project")
                        return

                    # Extract project ID
                    project_id = int(project_str.split(':')[0])

                    # Generate picking list
                    result = self.picking_list_service.generate_picking_list_from_project(project_id)
                    if result:
                        messagebox.showinfo("Success", "Picking list generated from project successfully")
                        dialog.destroy()
                        self.on_refresh()

                except Exception as e:
                    self.logger.error(f"Error generating picking list from project: {str(e)}")
                    messagebox.showerror("Error", f"Failed to generate picking list: {str(e)}")

            def create_from_order():
                """Create picking list from sale."""
                try:
                    # Check if sale selected
                    order_str = order_var.get()
                    if not order_str:
                        messagebox.showerror("Error", "Please select an sale")
                        return

                    # Extract sale ID
                    order_id = int(order_str.split(':')[0])

                    # Generate picking list
                    result = self.picking_list_service.generate_picking_list_from_order(order_id)
                    if result:
                        messagebox.showinfo("Success", "Picking list generated from sale successfully")
                        dialog.destroy()
                        self.on_refresh()

                except Exception as e:
                    self.logger.error(f"Error generating picking list from sale: {str(e)}")
                    messagebox.showerror("Error", f"Failed to generate picking list: {str(e)}")

            # Create the buttons that were missing in the original implementation
            ttk.Button(button_frame, text="Create Empty List", command=create_empty).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Generate from Project", command=create_from_project).pack(side=tk.LEFT,
                                                                                                     padx=5)
            ttk.Button(button_frame, text="Generate from Order", command=create_from_order).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

        except Exception as e:
            self.logger.error(f"Error opening create picking list dialog: {str(e)}")
            messagebox.showerror("Error", f"Failed to open create dialog: {str(e)}")

    def _print_picking_list(self):
        """Print or export the current picking list."""
        try:
            # Check if picking list is selected
            if not hasattr(self, 'current_picking_list_id') or not self.current_picking_list_id:
                messagebox.showinfo("Info", "Please select a picking list first")
                return

            # Get picking list data
            picking_list = self.picking_list_service.get_picking_list(self.current_picking_list_id)

            # Ask for export format
            export_dialog = tk.Toplevel(self)
            export_dialog.title("Export Picking List")
            export_dialog.geometry("400x300")
            export_dialog.transient(self)
            export_dialog.grab_set()

            # Create main frame
            main_frame = ttk.Frame(export_dialog, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Format selection
            format_frame = ttk.LabelFrame(main_frame, text="Export Format")
            format_frame.pack(fill=tk.X, pady=10)

            format_var = tk.StringVar(value="text")
            ttk.Radiobutton(format_frame, text="Text File (.txt)", variable=format_var, value="text").pack(anchor=tk.W,
                                                                                                           padx=10,
                                                                                                           pady=5)
            ttk.Radiobutton(format_frame, text="CSV File (.csv)", variable=format_var, value="csv").pack(anchor=tk.W,
                                                                                                         padx=10,
                                                                                                         pady=5)
            ttk.Radiobutton(format_frame, text="Print to Printer", variable=format_var, value="print").pack(anchor=tk.W,
                                                                                                            padx=10,
                                                                                                            pady=5)

            # Options frame
            options_frame = ttk.LabelFrame(main_frame, text="Options")
            options_frame.pack(fill=tk.X, pady=10)

            include_notes_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(options_frame, text="Include Notes", variable=include_notes_var).pack(anchor=tk.W, padx=10,
                                                                                                  pady=5)

            include_locations_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(options_frame, text="Include Storage Locations", variable=include_locations_var).pack(
                anchor=tk.W, padx=10, pady=5)

            # Buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=10)

            def on_export():
                export_format = format_var.get()
                include_notes = include_notes_var.get()
                include_locations = include_locations_var.get()

                if export_format == "print":
                    self._print_to_printer(picking_list, include_notes, include_locations)
                else:
                    # Get file path
                    file_extensions = {
                        "text": ".txt",
                        "csv": ".csv"
                    }
                    file_types = {
                        "text": [("Text files", "*.txt")],
                        "csv": [("CSV files", "*.csv")]
                    }

                    file_path = filedialog.asksaveasfilename(
                        defaultextension=file_extensions[export_format],
                        filetypes=file_types[export_format],
                        title="Save Picking List"
                    )

                    if not file_path:
                        return  # User cancelled

                    # Export based on format
                    if export_format == "text":
                        self._export_picking_list_txt(picking_list, file_path, include_notes, include_locations)
                    elif export_format == "csv":
                        self._export_picking_list_csv(picking_list, file_path, include_notes, include_locations)

                    messagebox.showinfo("Success", f"Picking list exported to {file_path}")

                export_dialog.destroy()

            ttk.Button(button_frame, text="Export", command=on_export).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=export_dialog.destroy).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            self.logger.error(f"Error exporting picking list: {str(e)}")
            messagebox.showerror("Error", f"Failed to export picking list: {str(e)}")


    def _export_picking_list_txt(self, picking_list, file_path, include_notes=True, include_locations=True):
        """
        Export picking list to a text file.

        Args:
            picking_list: The picking list data
            file_path: Path to save the file
            include_notes: Whether to include notes
            include_locations: Whether to include storage locations
        """
        try:
            with open(file_path, 'w') as f:
                # Header
                f.write(f"PICKING LIST: {picking_list['name']}\n")
                f.write(f"Status: {picking_list['status']}\n")
                if 'priority' in picking_list:
                    f.write(f"Priority: {self._format_priority(picking_list.get('priority', 0))}\n")
                if 'assigned_to' in picking_list and picking_list['assigned_to']:
                    f.write(f"Assigned To: {picking_list.get('assigned_to', '')}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 80 + "\n\n")

                if include_notes and picking_list.get('notes'):
                    f.write("NOTES:\n")
                    f.write(picking_list['notes'] + "\n\n")

                # Items table
                f.write("ITEMS:\n")
                header = f"{'ID':<5} {'Type':<12} {'Item':<30} {'Required':<10} {'Picked':<10} {'Unit':<8}"
                if include_locations:
                    header += f" {'Location':<20}"
                header += f" {'Status':<10}\n"
                f.write(header)
                f.write("-" * (110 if include_locations else 90) + "\n")

                for item in picking_list.get('items', []):
                    location = "Unknown"
                    if include_locations and item.get("storage_location"):
                        location = item["storage_location"]

                    status = "Picked" if item.get("is_picked") else "Pending"

                    line = f"{item['id']:<5} {item.get('item_type', 'Unknown'):<12} {item['name'][:28]:<30} "
                    line += f"{item['required_quantity']:<10.2f} {item.get('picked_quantity', 0):<10.2f} {item['unit']:<8}"

                    if include_locations:
                        line += f" {location[:18]:<20}"

                    line += f" {status:<10}\n"
                    f.write(line)

                    if include_notes:
                        if item.get('description'):
                            f.write(f"    Description: {item['description']}\n")
                        if item.get('notes'):
                            f.write(f"    Notes: {item['notes']}\n")

                    f.write("\n")

        except Exception as e:
            logging.exception(f"Error exporting to text: {e}")
            raise


    def _export_picking_list_csv(self, picking_list, file_path, include_notes=True, include_locations=True):
        """
        Export picking list to a CSV file.

        Args:
            picking_list: The picking list data
            file_path: Path to save the file
            include_notes: Whether to include notes
            include_locations: Whether to include storage locations
        """
        try:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)

                # Header metadata
                writer.writerow(['Picking List', picking_list['name']])
                writer.writerow(['Status', picking_list['status']])
                writer.writerow(['Priority', self._format_priority(picking_list.get('priority', 0))])
                writer.writerow(['Assigned To', picking_list.get('assigned_to', '')])
                writer.writerow(['Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])

                if include_notes and picking_list.get('notes'):
                    writer.writerow(['Notes', picking_list['notes']])

                writer.writerow([])  # Empty row for spacing

                # Items table header
                header = ['ID', 'Type', 'Item']
                if include_notes:
                    header.append('Description')
                header.extend(['Required', 'Picked', 'Unit'])
                if include_locations:
                    header.append('Location')
                header.append('Status')
                if include_notes:
                    header.append('Notes')

                writer.writerow(header)

                # Items data
                for item in picking_list.get('items', []):
                    # Format location
                    location = "Unknown"
                    if include_locations and item.get("storage_location"):
                        location = item["storage_location"]

                    status = "Picked" if item.get("is_picked") else "Pending"

                    row = [
                        item['id'],
                        item.get('item_type', 'Unknown'),
                        item['name']
                    ]

                    if include_notes:
                        row.append(item.get('description', ''))

                    row.extend([
                        item['required_quantity'],
                        item.get('picked_quantity', 0),
                        item['unit']
                    ])

                    if include_locations:
                        row.append(location)

                    row.append(status)

                    if include_notes:
                        row.append(item.get('notes', ''))

                    writer.writerow(row)

        except Exception as e:
            logging.exception(f"Error exporting to CSV: {e}")
            raise


    def _print_to_printer(self, picking_list, include_notes=True, include_locations=True):
        """
        Print the picking list to a physical printer.

        Args:
            picking_list: The picking list data
            include_notes: Whether to include notes
            include_locations: Whether to include storage locations
        """
        try:
            # Create temporary file for printing
            import tempfile
            import os
            import subprocess

            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
                temp_path = temp_file.name

            # Export to text file
            self._export_picking_list_txt(picking_list, temp_path, include_notes, include_locations)

            # Try to print using platform-specific commands
            if os.name == 'nt':  # Windows
                try:
                    os.startfile(temp_path, 'print')
                    messagebox.showinfo("Success", "Picking list sent to default printer")
                except Exception as e:
                    self.logger.error(f"Error printing on Windows: {str(e)}")
                    messagebox.showerror("Printing Error",
                                         "Could not send to printer automatically. The file has been saved temporarily, please print it manually.")
                    os.startfile(temp_path, 'open')
            else:  # Unix/Linux/Mac
                try:
                    subprocess.call(['lpr', temp_path])
                    messagebox.showinfo("Success", "Picking list sent to default printer")
                except Exception as e:
                    self.logger.error(f"Error printing on Unix: {str(e)}")
                    messagebox.showerror("Printing Error",
                                         "Could not send to printer. Please check your printer configuration.")

            # Clean up temp file (after a delay to ensure printing completes)
            def cleanup_temp_file():
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except Exception as e:
                    self.logger.error(f"Error removing temporary file: {str(e)}")

            # Schedule cleanup after 60 seconds
            self.after(60000, cleanup_temp_file)

        except Exception as e:
            self.logger.error(f"Error in print to printer: {str(e)}")
            messagebox.showerror("Error", f"Failed to print: {str(e)}")


    def _search_items(self):
        """Search for items in the current picking list."""
        try:
            # Get search query
            query = self.search_var.get().lower()

            # Get status filter
            status_filter = self.item_status_var.get()

            # Clear highlighting in treeview
            for item_id in self.items_tree.get_children():
                self.items_tree.item(item_id, tags=())

            # If no query and status filter is All, just reset the view
            if not query and status_filter == "All":
                return

            # For all items in the tree
            for item_id in self.items_tree.get_children():
                item_values = self.items_tree.item(item_id, "values")
                item_text = " ".join(str(v) for v in item_values).lower()

                # Apply status filter
                if status_filter != "All":
                    item_status = item_values[7]  # Status column
                    if status_filter == "Pending" and item_status != "Pending":
                        self.items_tree.item(item_id, tags=("hidden",))
                        continue
                    if status_filter == "Picked" and item_status != "Picked":
                        self.items_tree.item(item_id, tags=("hidden",))
                        continue

                # Apply text search if query exists
                if query and query not in item_text:
                    self.items_tree.item(item_id, tags=("hidden",))
                else:
                    # If item matches, apply match tag
                    if query:
                        self.items_tree.item(item_id, tags=("match",))
                    else:
                        self.items_tree.item(item_id, tags=())

            # Configure tag appearance
            self.items_tree.tag_configure("hidden", background="light grey")
            self.items_tree.tag_configure("match", background="light green")

        except Exception as e:
            self.logger.error(f"Error searching items: {str(e)}")


    def _clear_search(self):
        """Clear the search and reset the items view."""
        self.search_var.set("")
        self.item_status_var.set("All")

        # Clear all tags
        for item_id in self.items_tree.get_children():
            self.items_tree.item(item_id, tags=())


    def _show_batch_operations(self):
        """Show batch operations dialog for managing multiple items at once."""
        try:
            # Check if a picking list is selected
            if not hasattr(self, 'current_picking_list_id') or not self.current_picking_list_id:
                messagebox.showinfo("Batch Operations", "Please select a picking list first.")
                return

            # Get the current picking list
            picking_list = self.picking_list_service.get_picking_list(self.current_picking_list_id)

            # Create the dialog
            dialog = tk.Toplevel(self)
            dialog.title(f"Batch Operations: {picking_list['name']}")
            dialog.geometry("700x500")
            dialog.transient(self)
            dialog.grab_set()

            # Create main frame
            main_frame = ttk.Frame(dialog, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Create toolbar
            toolbar = ttk.Frame(main_frame)
            toolbar.pack(fill=tk.X, pady=(0, 10))

            # Filter options
            ttk.Label(toolbar, text="Filter:").pack(side=tk.LEFT, padx=(0, 5))
            filter_var = tk.StringVar(value="all")
            ttk.Radiobutton(toolbar, text="All", variable=filter_var, value="all").pack(side=tk.LEFT, padx=5)
            ttk.Radiobutton(toolbar, text="Pending", variable=filter_var, value="pending").pack(side=tk.LEFT, padx=5)
            ttk.Radiobutton(toolbar, text="Picked", variable=filter_var, value="picked").pack(side=tk.LEFT, padx=5)

            # Search field
            search_frame = ttk.Frame(toolbar)
            search_frame.pack(side=tk.RIGHT)

            ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
            search_var = tk.StringVar()
            search_entry = ttk.Entry(search_frame, textvariable=search_var, width=20)
            search_entry.pack(side=tk.LEFT, padx=5)

            # Create items treeview
            columns = ("select", "id", "type", "name", "required", "picked", "unit", "location", "status")
            tree = ttk.Treeview(main_frame, columns=columns, show="headings", selectmode="browse")

            # Configure columns
            tree.heading("select", text="")
            tree.heading("id", text="ID")
            tree.heading("type", text="Type")
            tree.heading("name", text="Item")
            tree.heading("required", text="Required")
            tree.heading("picked", text="Picked")
            tree.heading("unit", text="Unit")
            tree.heading("location", text="Location")
            tree.heading("status", text="Status")

            # Column widths
            tree.column("select", width=30, stretch=False)
            tree.column("id", width=40, stretch=False)
            tree.column("type", width=80)
            tree.column("name", width=200)
            tree.column("required", width=70, anchor=tk.CENTER)
            tree.column("picked", width=70, anchor=tk.CENTER)
            tree.column("unit", width=60, anchor=tk.CENTER)
            tree.column("location", width=120)
            tree.column("status", width=80, anchor=tk.CENTER)

            # Add scrollbar
            scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)

            # Pack
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Selection tracking
            selection_vars = {}

            # Populate items function
            def populate_items():
                # Clear tree
                for item in tree.get_children():
                    tree.delete(item)

                # Get filter value
                filter_value = filter_var.get()

                # Get search text
                search_text = search_var.get().lower()

                # Reset selection vars
                selection_vars.clear()

                # Populate treeview
                for item in picking_list.get("items", []):
                    # Apply filter
                    if filter_value == "pending" and item.get("is_picked", False):
                        continue
                    if filter_value == "picked" and not item.get("is_picked", False):
                        continue

                    # Apply search
                    if search_text and search_text not in item["name"].lower() and search_text not in item.get("item_type",
                                                                                                               "").lower():
                        continue

                    # Format location
                    location = "Unknown"
                    if item.get("storage_location"):
                        location = item["storage_location"]

                    status = "Picked" if item.get("is_picked") else "Pending"

                    # Create selection variable
                    selection_var = tk.BooleanVar(value=False)
                    selection_vars[item["id"]] = selection_var

                    # Insert item with selection checkbox
                    tree.insert("", tk.END, values=(
                        "",  # Will be replaced with checkbox
                        item["id"],
                        item.get("item_type", "Unknown"),
                        item["name"],
                        item["required_quantity"],
                        item.get("picked_quantity", 0),
                        item["unit"],
                        location,
                        status
                    ))

                # Add checkboxes
                for i, row_id in enumerate(tree.get_children()):
                    item_id = int(tree.item(row_id)["values"][1])

                    # Create a frame for the checkbox
                    chk_frame = ttk.Frame(tree)
                    chk = ttk.Checkbutton(chk_frame, variable=selection_vars[item_id],
                                          command=lambda: update_selected_count())
                    chk.pack(side=tk.TOP, anchor=tk.CENTER)

                    # Place the frame in the tree
                    tree.window_configure(row_id, column=0, window=chk_frame)

            # Initialize with current data
            populate_items()

            # Create batch actions frame
            actions_frame = ttk.LabelFrame(main_frame, text="Batch Actions")
            actions_frame.pack(fill=tk.X, pady=10)

            # Selection info
            selection_frame = ttk.Frame(actions_frame)
            selection_frame.pack(fill=tk.X, padx=10, pady=5)

            selected_count_var = tk.StringVar(value="0 items selected")
            ttk.Label(selection_frame, textvariable=selected_count_var).pack(side=tk.LEFT, padx=5)

            # Select all/none buttons
            ttk.Button(selection_frame, text="Select All", command=lambda: select_all(True)).pack(side=tk.LEFT, padx=5)
            ttk.Button(selection_frame, text="Select None", command=lambda: select_all(False)).pack(side=tk.LEFT, padx=5)

            def select_all(value: bool):
                """Select all or none."""
                for var in selection_vars.values():
                    var.set(value)
                update_selected_count()

            def update_selected_count():
                """Update the selected count text."""
                count = sum(1 for var in selection_vars.values() if var.get())
                selected_count_var.set(f"{count} items selected")

            # Batch mark as picked
            pick_frame = ttk.Frame(actions_frame)
            pick_frame.pack(fill=tk.X, padx=10, pady=5)

            ttk.Button(pick_frame, text="Mark Selected as Picked",
                       command=lambda: batch_mark_picked()).pack(side=tk.LEFT, padx=5)

            ttk.Label(pick_frame, text="Quantity:").pack(side=tk.LEFT, padx=(20, 5))
            batch_quantity_var = tk.StringVar(value="full")
            ttk.Radiobutton(pick_frame, text="Full Amount", variable=batch_quantity_var, value="full").pack(side=tk.LEFT,
                                                                                                            padx=5)
            ttk.Radiobutton(pick_frame, text="Custom", variable=batch_quantity_var, value="custom").pack(side=tk.LEFT,
                                                                                                         padx=5)

            custom_quantity_var = tk.DoubleVar(value=1.0)
            custom_spinbox = ttk.Spinbox(pick_frame, from_=0.1, to=9999.9, increment=0.1,
                                         textvariable=custom_quantity_var, width=8)
            custom_spinbox.pack(side=tk.LEFT, padx=5)

            # Notes for batch operations
            notes_frame = ttk.Frame(actions_frame)
            notes_frame.pack(fill=tk.X, padx=10, pady=5)

            ttk.Label(notes_frame, text="Batch Notes:").pack(side=tk.LEFT, padx=(0, 5))
            batch_notes_var = tk.StringVar()
            ttk.Entry(notes_frame, textvariable=batch_notes_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True,
                                                                                padx=5)

            def batch_mark_picked():
                """Mark selected items as picked."""
                # Get selected items
                selected_ids = [item_id for item_id, var in selection_vars.items() if var.get()]

                if not selected_ids:
                    messagebox.showinfo("Info", "No items selected")
                    return

                # Confirm action
                if not messagebox.askyesno("Confirm", f"Mark {len(selected_ids)} items as picked?"):
                    return

                try:
                    # For each selected item
                    updates = []
                    for item_id in selected_ids:
                        # Find the item in the picking list
                        item = next((i for i in picking_list["items"] if i["id"] == item_id), None)
                        if not item:
                            continue

                        # Determine quantity
                        if batch_quantity_var.get() == "full":
                            quantity = item["required_quantity"]
                        else:
                            quantity = float(custom_quantity_var.get())

                        # Create update data
                        update_data = {
                            "picked_quantity": quantity,
                            "is_picked": True,
                            "notes": batch_notes_var.get().strip()
                        }

                        # Add to updates list
                        updates.append((item_id, update_data))

                    # Apply all updates
                    for item_id, update_data in updates:
                        self.picking_list_service.update_picking_list_item(item_id, update_data)

                    messagebox.showinfo("Success", f"{len(updates)} items marked as picked")

                    # Refresh dialog
                    populate_items()

                    # Check if all items are picked and ask to update list status
                    picking_list_updated = self.picking_list_service.get_picking_list(self.current_picking_list_id)
                    all_picked = all(item.get("is_picked", False) for item in picking_list_updated.get("items", []))

                    if all_picked and picking_list_updated.get("status") != PickingListStatus.COMPLETED.name:
                        if messagebox.askyesno("Complete Picking List",
                                               "All items have been picked. Mark the picking list as completed?"):
                            self.picking_list_service.update_list(
                                self.current_picking_list_id,
                                {"status": PickingListStatus.COMPLETED.name}
                            )
                            # Refresh main view after dialog closes
                            dialog.protocol("WM_DELETE_WINDOW", lambda: [dialog.destroy(), self.on_refresh()])

                except Exception as e:
                    self.logger.error(f"Error in batch mark as picked: {str(e)}")
                    messagebox.showerror("Error", f"Failed to update items: {str(e)}")

            # Button frame
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=10)

            ttk.Button(button_frame, text="Refresh", command=populate_items).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

            # Bind search update
            def on_search_change(*args):
                populate_items()

            search_var.trace_add("write", on_search_change)

            # Bind filter update
            def on_filter_change(*args):
                populate_items()

            filter_var.trace_add("write", on_filter_change)

        except Exception as e:
            self.logger.error(f"Error showing batch operations: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def _delete_list(self):
        """Compatibility method that forwards to _delete_picking_list."""
        self.logger.info("_delete_list called, forwarding to _delete_picking_list")
        return self._delete_picking_list()

    def _delete_picking_list(self):
        """Delete the selected picking list."""
        try:
            # Check if a list is selected
            selected_item = self.lists_tree.selection()
            if not selected_item:
                messagebox.showinfo("Delete", "Please select a picking list to delete")
                return

            # Get the list ID
            list_id = int(self.lists_tree.item(selected_item[0], "values")[0])

            # Confirm deletion
            list_name = self.lists_tree.item(selected_item[0], "values")[1]
            if not messagebox.askyesno("Confirm Delete",
                                       f"Are you sure you want to delete picking list '{list_name}'?"):
                return

            # Delete the list
            if not self.picking_list_service:
                self.picking_list_service = self.app.get_service(IPickingListService)

            if self.picking_list_service.delete_list(list_id):
                # Reset UI
                self._clear_details()
                self._toggle_details(False)
                self.current_picking_list_id = None

                # Remove from treeview
                self.lists_tree.delete(selected_item)

                # Show success message
                messagebox.showinfo("Success", f"Picking list '{list_name}' has been deleted")
                self.logger.info(f"Deleted picking list {list_id}: {list_name}")

        except Exception as e:
            self.logger.error(f"Error deleting picking list: {str(e)}")
            messagebox.showerror("Delete Error", f"Failed to delete picking list: {str(e)}")

    def _save_picking_list(self):
        """Save changes to the current picking list."""
        try:
            # Check if a picking list is selected
            if not hasattr(self, 'current_picking_list_id') or not self.current_picking_list_id:
                messagebox.showinfo("Save", "No picking list selected")
                return

            # Get form data
            name = self.list_name_var.get().strip()
            status = self.list_status_var.get()

            # Get priority (extract number from format like "0 (Normal)")
            priority_text = self.list_priority_var.get()
            try:
                priority = int(priority_text.split(' ')[0])
            except (ValueError, IndexError):
                priority = 0

            assigned_to = self.list_assigned_var.get().strip()
            notes = self.list_notes_text.get("1.0", tk.END).strip()

            # Validate required fields
            if not name:
                messagebox.showerror("Validation Error", "Picking list name is required")
                return

            # Create update data
            update_data = {
                "name": name,
                "status": status,
                "priority": priority,
                "assigned_to": assigned_to,
                "notes": notes
            }

            # Update the picking list
            if not self.picking_list_service:
                self.picking_list_service = self.app.get_service(IPickingListService)

            updated_list = self.picking_list_service.update_list(self.current_picking_list_id, update_data)

            if updated_list:
                # Update treeview item
                for item_id in self.lists_tree.get_children():
                    if int(self.lists_tree.item(item_id, "values")[0]) == self.current_picking_list_id:
                        self.lists_tree.item(item_id, values=(
                            updated_list["id"],
                            updated_list["name"],
                            updated_list["status"],
                            len(updated_list.get("items", [])),
                            self._format_priority(updated_list.get("priority", 0))
                        ))
                        break

                # Show success message
                messagebox.showinfo("Success", "Picking list updated successfully")
                self.logger.info(f"Updated picking list {self.current_picking_list_id}")

        except Exception as e:
            self.logger.error(f"Error saving picking list: {str(e)}")
            messagebox.showerror("Save Error", f"Failed to save picking list: {str(e)}")

    def _add_item(self):
        """Add an item to the current picking list."""
        try:
            # Check if a picking list is selected
            if not hasattr(self, 'current_picking_list_id') or not self.current_picking_list_id:
                messagebox.showinfo("Add Item", "Please select a picking list first")
                return

            # Create dialog
            dialog = tk.Toplevel(self)
            dialog.title("Add Picking List Item")
            dialog.geometry("600x450")
            dialog.transient(self)
            dialog.grab_set()

            # Create form frame
            form_frame = ttk.Frame(dialog, padding=10)
            form_frame.pack(fill=tk.BOTH, expand=True)

            # Item info section
            item_frame = ttk.LabelFrame(form_frame, text="Item Information")
            item_frame.pack(fill=tk.X, pady=10)

            item_grid = ttk.Frame(item_frame)
            item_grid.pack(fill=tk.X, padx=10, pady=10)

            # Item name
            ttk.Label(item_grid, text="Item Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            name_var = tk.StringVar()
            name_entry = ttk.Entry(item_grid, textvariable=name_var, width=40)
            name_entry.grid(row=0, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)

            # Item type
            ttk.Label(item_grid, text="Item Type:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
            type_var = tk.StringVar(value="Material")
            type_combo = ttk.Combobox(item_grid, textvariable=type_var,
                                      values=["Material", "Hardware", "Leather", "Tool", "Other"], width=15)
            type_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

            # Required quantity
            ttk.Label(item_grid, text="Required Quantity:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
            quantity_var = tk.DoubleVar(value=1.0)
            quantity_spinbox = ttk.Spinbox(item_grid, from_=0.1, to=9999.9, increment=0.1,
                                           textvariable=quantity_var, width=10)
            quantity_spinbox.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)

            # Unit
            ttk.Label(item_grid, text="Unit:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
            unit_var = tk.StringVar(value="pcs")
            unit_combo = ttk.Combobox(item_grid, textvariable=unit_var,
                                      values=["pcs", "m", "cm", "mm", "kg", "g", "oz", "lb"], width=10)
            unit_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

            # Storage location
            ttk.Label(item_grid, text="Storage Location:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
            location_var = tk.StringVar()
            location_entry = ttk.Entry(item_grid, textvariable=location_var, width=40)
            location_entry.grid(row=3, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)

            # Description and notes
            description_frame = ttk.LabelFrame(form_frame, text="Details")
            description_frame.pack(fill=tk.BOTH, expand=True, pady=10)

            details_grid = ttk.Frame(description_frame)
            details_grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Description
            ttk.Label(details_grid, text="Description:").grid(row=0, column=0, sticky=tk.NW, padx=5, pady=5)
            description_text = tk.Text(details_grid, height=3, width=50)
            description_text.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

            # Notes
            ttk.Label(details_grid, text="Notes:").grid(row=1, column=0, sticky=tk.NW, padx=5, pady=5)
            notes_text = tk.Text(details_grid, height=3, width=50)
            notes_text.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

            # Buttons
            button_frame = ttk.Frame(form_frame)
            button_frame.pack(fill=tk.X, pady=10)

            def save_item():
                """Save the new item."""
                try:
                    # Validate required fields
                    if not name_var.get().strip():
                        messagebox.showerror("Validation Error", "Item name is required")
                        return

                    # Create item data
                    item_data = {
                        "name": name_var.get().strip(),
                        "item_type": type_var.get(),
                        "required_quantity": float(quantity_var.get()),
                        "unit": unit_var.get(),
                        "storage_location": location_var.get().strip(),
                        "description": description_text.get("1.0", tk.END).strip(),
                        "notes": notes_text.get("1.0", tk.END).strip(),
                        "is_picked": False,
                        "picked_quantity": 0
                    }

                    # Save to service
                    if not self.picking_list_service:
                        self.picking_list_service = self.app.get_service(IPickingListService)

                    result = self.picking_list_service.add_item_to_list(self.current_picking_list_id, item_data)

                    if result:
                        # Update picking list
                        self._on_list_select()

                        # Show success message
                        messagebox.showinfo("Success", "Item added successfully")
                        dialog.destroy()

                except Exception as e:
                    self.logger.error(f"Error adding item: {str(e)}")
                    messagebox.showerror("Error", f"Failed to add item: {str(e)}")

            ttk.Button(button_frame, text="Add Item", command=save_item).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

            # Focus name field
            name_entry.focus_set()

        except Exception as e:
            self.logger.error(f"Error creating add item dialog: {str(e)}")
            messagebox.showerror("Error", f"Failed to open add item dialog: {str(e)}")

    def _remove_item(self):
        """Remove the selected item from the current picking list."""
        try:
            # Check if a picking list is selected
            if not hasattr(self, 'current_picking_list_id') or not self.current_picking_list_id:
                messagebox.showinfo("Remove Item", "Please select a picking list first")
                return

            # Check if an item is selected
            selected_item = self.items_tree.selection()
            if not selected_item:
                messagebox.showinfo("Remove Item", "Please select an item to remove")
                return

            # Get the item ID
            item_id = int(self.items_tree.item(selected_item[0], "values")[0])
            item_name = self.items_tree.item(selected_item[0], "values")[2]  # Name is in the third column

            # Confirm deletion
            if not messagebox.askyesno("Confirm Remove", f"Are you sure you want to remove item '{item_name}'?"):
                return

            # Remove the item
            if not self.picking_list_service:
                self.picking_list_service = self.app.get_service(IPickingListService)

            if self.picking_list_service.remove_item_from_list(self.current_picking_list_id, item_id):
                # Remove from treeview
                self.items_tree.delete(selected_item)

                # Show success message
                messagebox.showinfo("Success", f"Item '{item_name}' has been removed")
                self.logger.info(f"Removed item {item_id} from picking list {self.current_picking_list_id}")

        except Exception as e:
            self.logger.error(f"Error removing item: {str(e)}")
            messagebox.showerror("Error", f"Failed to remove item: {str(e)}")

    def _mark_item_picked(self):
        """Mark the selected item as picked."""
        try:
            # Check if a picking list is selected
            if not hasattr(self, 'current_picking_list_id') or not self.current_picking_list_id:
                messagebox.showinfo("Mark Picked", "Please select a picking list first")
                return

            # Check if an item is selected
            selected_item = self.items_tree.selection()
            if not selected_item:
                messagebox.showinfo("Mark Picked", "Please select an item to mark as picked")
                return

            # Get item data
            item_values = self.items_tree.item(selected_item[0], "values")
            item_id = int(item_values[0])
            item_name = item_values[2]  # Name is in the third column
            required_qty = float(item_values[3])  # Required quantity is in the fourth column
            current_status = item_values[7]  # Status is in the eighth column

            # Check if already picked
            if current_status == "Picked":
                if not messagebox.askyesno("Already Picked",
                                           f"Item '{item_name}' is already marked as picked. Do you want to update the quantity?"):
                    return

            # Ask for quantity
            qty_dialog = tk.Toplevel(self)
            qty_dialog.title("Pick Quantity")
            qty_dialog.transient(self)
            qty_dialog.grab_set()

            # Set up the dialog
            ttk.Label(qty_dialog, text=f"Picking quantity for: {item_name}").pack(padx=10, pady=10)

            qty_frame = ttk.Frame(qty_dialog)
            qty_frame.pack(padx=10, pady=10)

            ttk.Label(qty_frame, text="Required:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            ttk.Label(qty_frame, text=str(required_qty)).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

            ttk.Label(qty_frame, text="Quantity Picked:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
            picked_qty_var = tk.DoubleVar(value=required_qty)  # Default to required quantity
            picked_qty_spinbox = ttk.Spinbox(qty_frame, from_=0.1, to=9999.9, increment=0.1,
                                             textvariable=picked_qty_var, width=10)
            picked_qty_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

            # Notes
            ttk.Label(qty_dialog, text="Notes:").pack(anchor=tk.W, padx=10)
            notes_text = tk.Text(qty_dialog, height=3, width=40)
            notes_text.pack(fill=tk.X, padx=10, pady=5)

            # Buttons
            button_frame = ttk.Frame(qty_dialog)
            button_frame.pack(fill=tk.X, pady=10)

            def save_picked():
                """Save the picked quantity."""
                try:
                    # Get quantity
                    picked_qty = float(picked_qty_var.get())

                    # Validate quantity
                    if picked_qty <= 0:
                        messagebox.showerror("Validation Error", "Picked quantity must be greater than zero")
                        return

                    # Create update data
                    update_data = {
                        "picked_quantity": picked_qty,
                        "is_picked": True,
                        "notes": notes_text.get("1.0", tk.END).strip()
                    }

                    # Save the changes
                    if not self.picking_list_service:
                        self.picking_list_service = self.app.get_service(IPickingListService)

                    if self.picking_list_service.update_picking_list_item(item_id, update_data):
                        # Update treeview
                        self.items_tree.item(selected_item, values=(
                            item_values[0],  # ID
                            item_values[1],  # Type
                            item_values[2],  # Name
                            item_values[3],  # Required
                            picked_qty,  # Picked - updated
                            item_values[5],  # Unit
                            item_values[6],  # Location
                            "Picked"  # Status - updated
                        ))

                        # Close dialog
                        qty_dialog.destroy()

                        # Check if all items are picked and ask to update list status
                        all_picked = True
                        for child in self.items_tree.get_children():
                            if self.items_tree.item(child, "values")[7] != "Picked":
                                all_picked = False
                                break

                        if all_picked:
                            if messagebox.askyesno("Complete Picking List",
                                                   "All items have been picked. Mark the picking list as completed?"):
                                self.picking_list_service.update_list(
                                    self.current_picking_list_id,
                                    {"status": PickingListStatus.COMPLETED.name}
                                )
                                # Update the list status in the treeview
                                for list_item in self.lists_tree.get_children():
                                    if int(self.lists_tree.item(list_item, "values")[
                                               0]) == self.current_picking_list_id:
                                        values = list(self.lists_tree.item(list_item, "values"))
                                        values[2] = PickingListStatus.COMPLETED.name
                                        self.lists_tree.item(list_item, values=values)
                                        break

                        # Show success message
                        messagebox.showinfo("Success", f"Item '{item_name}' marked as picked")
                        self.logger.info(
                            f"Marked item {item_id} as picked in picking list {self.current_picking_list_id}")

                except Exception as e:
                    self.logger.error(f"Error marking item as picked: {str(e)}")
                    messagebox.showerror("Error", f"Failed to mark item as picked: {str(e)}")

            ttk.Button(button_frame, text="Save", command=save_picked).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=qty_dialog.destroy).pack(side=tk.LEFT, padx=5)

            # Set focus to quantity spinbox
            picked_qty_spinbox.focus_set()

        except Exception as e:
            self.logger.error(f"Error in mark item picked: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def _import_items_from_file(self):
        """Import items for the current picking list from a file."""
        try:
            # Check if a picking list is selected
            if not hasattr(self, 'current_picking_list_id') or not self.current_picking_list_id:
                messagebox.showinfo("Import Items", "Please select a picking list first")
                return

            # Ask for file
            file_types = [
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx;*.xls"),
                ("All files", "*.*")
            ]

            file_path = filedialog.askopenfilename(
                title="Select File to Import",
                filetypes=file_types
            )

            if not file_path:
                return  # User cancelled

            # Determine file type
            if file_path.lower().endswith(('.xlsx', '.xls')):
                if not PANDAS_AVAILABLE:
                    messagebox.showerror("Import Error",
                                         "Excel import requires pandas library. Please install pandas or use CSV format.")
                    return
                self._import_from_excel(file_path)
            elif file_path.lower().endswith('.csv'):
                self._import_from_csv(file_path)
            else:
                messagebox.showerror("Import Error", "Unsupported file format. Please use CSV or Excel.")

        except Exception as e:
            self.logger.error(f"Error importing items from file: {str(e)}")
            messagebox.showerror("Import Error", f"Failed to import items: {str(e)}")

    def _import_from_csv(self, file_path):
        """Import items from CSV file."""
        try:
            imported_items = []

            with open(file_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)

                if not reader.fieldnames:
                    messagebox.showerror("Import Error", "CSV file has no headers")
                    return

                # Check required columns
                required_columns = ['name', 'quantity', 'unit']
                missing_columns = [col for col in required_columns if col not in reader.fieldnames]

                if missing_columns:
                    messagebox.showerror("Import Error",
                                         f"CSV file is missing required columns: {', '.join(missing_columns)}")
                    return

                # Process rows
                for row in reader:
                    item = {
                        'name': row.get('name', '').strip(),
                        'required_quantity': float(row.get('quantity', 0)),
                        'unit': row.get('unit', 'pcs').strip(),
                        'item_type': row.get('type', 'Material').strip(),
                        'storage_location': row.get('location', '').strip(),
                        'description': row.get('description', '').strip(),
                        'notes': row.get('notes', '').strip(),
                        'is_picked': False,
                        'picked_quantity': 0
                    }

                    # Validate required fields
                    if not item['name']:
                        continue  # Skip items without name

                    imported_items.append(item)

            # Confirm import
            if not imported_items:
                messagebox.showinfo("Import Result", "No valid items found in the file")
                return

            if not messagebox.askyesno("Confirm Import",
                                       f"Found {len(imported_items)} items to import. Continue?"):
                return

            # Add items to picking list
            if not self.picking_list_service:
                self.picking_list_service = self.app.get_service(IPickingListService)

            successful_imports = 0
            for item in imported_items:
                try:
                    if self.picking_list_service.add_item_to_list(self.current_picking_list_id, item):
                        successful_imports += 1
                except Exception as e:
                    self.logger.error(f"Error importing item {item['name']}: {str(e)}")

            # Refresh view
            self._on_list_select()

            # Show result
            messagebox.showinfo("Import Complete",
                                f"Successfully imported {successful_imports} of {len(imported_items)} items")

        except Exception as e:
            self.logger.error(f"Error importing from CSV: {str(e)}")
            messagebox.showerror("Import Error", f"Failed to import from CSV: {str(e)}")

    def _import_from_excel(self, file_path):
        """Import items from Excel file."""
        try:
            import pandas as pd

            # Read Excel file
            df = pd.read_excel(file_path)

            # Check required columns
            required_columns = ['name', 'quantity', 'unit']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                messagebox.showerror("Import Error",
                                     f"Excel file is missing required columns: {', '.join(missing_columns)}")
                return

            # Process rows
            imported_items = []
            for _, row in df.iterrows():
                try:
                    item = {
                        'name': str(row.get('name', '')).strip(),
                        'required_quantity': float(row.get('quantity', 0)),
                        'unit': str(row.get('unit', 'pcs')).strip(),
                        'item_type': str(row.get('type', 'Material')).strip(),
                        'storage_location': str(row.get('location', '')).strip(),
                        'description': str(row.get('description', '')).strip(),
                        'notes': str(row.get('notes', '')).strip(),
                        'is_picked': False,
                        'picked_quantity': 0
                    }

                    # Validate required fields
                    if not item['name'] or pd.isna(row.get('name')):
                        continue  # Skip items without name

                    imported_items.append(item)
                except Exception as e:
                    self.logger.error(f"Error processing Excel row: {str(e)}")

            # Confirm import
            if not imported_items:
                messagebox.showinfo("Import Result", "No valid items found in the file")
                return

            if not messagebox.askyesno("Confirm Import",
                                       f"Found {len(imported_items)} items to import. Continue?"):
                return

            # Add items to picking list
            if not self.picking_list_service:
                self.picking_list_service = self.app.get_service(IPickingListService)

            successful_imports = 0
            for item in imported_items:
                try:
                    if self.picking_list_service.add_item_to_list(self.current_picking_list_id, item):
                        successful_imports += 1
                except Exception as e:
                    self.logger.error(f"Error importing item {item['name']}: {str(e)}")

            # Refresh view
            self._on_list_select()

            # Show result
            messagebox.showinfo("Import Complete",
                                f"Successfully imported {successful_imports} of {len(imported_items)} items")

        except Exception as e:
            self.logger.error(f"Error importing from Excel: {str(e)}")
            messagebox.showerror("Import Error", f"Failed to import from Excel: {str(e)}")

    def _edit_item(self, event=None):
        """
        Edit the selected picking list item.

        Args:
            event: Optional event that triggered the edit action
        """
        try:
            # Check if a picking list is selected
            if not hasattr(self, 'current_picking_list_id') or not self.current_picking_list_id:
                messagebox.showinfo("Edit Item", "Please select a picking list first")
                return

            # Check if an item is selected
            selected_item = self.items_tree.selection()
            if not selected_item:
                messagebox.showinfo("Edit Item", "Please select an item to edit")
                return

            # Get the item ID
            item_id = int(self.items_tree.item(selected_item[0], "values")[0])

            # Find the item in the current picking list
            if not self.picking_list_service:
                self.picking_list_service = self.app.get_service(IPickingListService)

            # Get the current picking list with updated data
            picking_list = self.picking_list_service.get_picking_list(self.current_picking_list_id)

            # Find the item in the list
            item = next((i for i in picking_list.get("items", []) if i["id"] == item_id), None)

            if not item:
                messagebox.showerror("Error", f"Item with ID {item_id} not found in picking list")
                return

            # Create dialog
            dialog = tk.Toplevel(self)
            dialog.title("Edit Picking List Item")
            dialog.geometry("600x450")
            dialog.transient(self)
            dialog.grab_set()

            # Create form frame
            form_frame = ttk.Frame(dialog, padding=10)
            form_frame.pack(fill=tk.BOTH, expand=True)

            # Item info section
            item_frame = ttk.LabelFrame(form_frame, text="Item Information")
            item_frame.pack(fill=tk.X, pady=10)

            item_grid = ttk.Frame(item_frame)
            item_grid.pack(fill=tk.X, padx=10, pady=10)

            # Item name
            ttk.Label(item_grid, text="Item Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            name_var = tk.StringVar(value=item["name"])
            name_entry = ttk.Entry(item_grid, textvariable=name_var, width=40)
            name_entry.grid(row=0, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)

            # Item type
            ttk.Label(item_grid, text="Item Type:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
            type_var = tk.StringVar(value=item.get("item_type", "Material"))
            type_combo = ttk.Combobox(item_grid, textvariable=type_var,
                                      values=["Material", "Hardware", "Leather", "Tool", "Other"], width=15)
            type_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

            # Required quantity
            ttk.Label(item_grid, text="Required Quantity:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
            quantity_var = tk.DoubleVar(value=item["required_quantity"])
            quantity_spinbox = ttk.Spinbox(item_grid, from_=0.1, to=9999.9, increment=0.1,
                                           textvariable=quantity_var, width=10)
            quantity_spinbox.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)

            # Picked quantity
            ttk.Label(item_grid, text="Picked Quantity:").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
            picked_var = tk.DoubleVar(value=item.get("picked_quantity", 0))
            picked_spinbox = ttk.Spinbox(item_grid, from_=0, to=9999.9, increment=0.1,
                                         textvariable=picked_var, width=10)
            picked_spinbox.grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)

            # Unit
            ttk.Label(item_grid, text="Unit:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
            unit_var = tk.StringVar(value=item["unit"])
            unit_combo = ttk.Combobox(item_grid, textvariable=unit_var,
                                      values=["pcs", "m", "cm", "mm", "kg", "g", "oz", "lb"], width=10)
            unit_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

            # Storage location
            ttk.Label(item_grid, text="Storage Location:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
            location_var = tk.StringVar(value=item.get("storage_location", ""))
            location_entry = ttk.Entry(item_grid, textvariable=location_var, width=40)
            location_entry.grid(row=3, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)

            # Status
            ttk.Label(item_grid, text="Status:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
            status_var = tk.BooleanVar(value=item.get("is_picked", False))
            status_check = ttk.Checkbutton(item_grid, text="Picked", variable=status_var)
            status_check.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)

            # Description and notes
            description_frame = ttk.LabelFrame(form_frame, text="Details")
            description_frame.pack(fill=tk.BOTH, expand=True, pady=10)

            details_grid = ttk.Frame(description_frame)
            details_grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Description
            ttk.Label(details_grid, text="Description:").grid(row=0, column=0, sticky=tk.NW, padx=5, pady=5)
            description_text = tk.Text(details_grid, height=3, width=50)
            description_text.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
            if item.get("description"):
                description_text.insert("1.0", item["description"])

            # Notes
            ttk.Label(details_grid, text="Notes:").grid(row=1, column=0, sticky=tk.NW, padx=5, pady=5)
            notes_text = tk.Text(details_grid, height=3, width=50)
            notes_text.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
            if item.get("notes"):
                notes_text.insert("1.0", item["notes"])

            # Buttons
            button_frame = ttk.Frame(form_frame)
            button_frame.pack(fill=tk.X, pady=10)

            def save_item():
                """Save the edited item."""
                try:
                    # Validate required fields
                    if not name_var.get().strip():
                        messagebox.showerror("Validation Error", "Item name is required")
                        return

                    # Create update data
                    item_data = {
                        "name": name_var.get().strip(),
                        "item_type": type_var.get(),
                        "required_quantity": float(quantity_var.get()),
                        "picked_quantity": float(picked_var.get()),
                        "unit": unit_var.get(),
                        "storage_location": location_var.get().strip(),
                        "description": description_text.get("1.0", tk.END).strip(),
                        "notes": notes_text.get("1.0", tk.END).strip(),
                        "is_picked": status_var.get()
                    }

                    # Update the item
                    if self.picking_list_service.update_picking_list_item(item_id, item_data):
                        # Update the picking list view
                        self._on_list_select()

                        # Show success message
                        messagebox.showinfo("Success", "Item updated successfully")
                        dialog.destroy()

                except Exception as e:
                    self.logger.error(f"Error updating item: {str(e)}")
                    messagebox.showerror("Error", f"Failed to update item: {str(e)}")

            ttk.Button(button_frame, text="Save Changes", command=save_item).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

            # Focus name field
            name_entry.focus_set()

        except Exception as e:
            self.logger.error(f"Error opening edit item dialog: {str(e)}")
            messagebox.showerror("Error", f"Failed to open edit dialog: {str(e)}")