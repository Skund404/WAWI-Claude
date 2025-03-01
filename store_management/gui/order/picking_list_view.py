# gui/order/picking_list_view.py
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Any, Dict, List, Optional

from gui.base_view import BaseView
from services.interfaces.picking_list_service import IPickingListService, PickingListStatus
from services.interfaces.project_service import IProjectService
from services.interfaces.order_service import IOrderService


class PickingListView(BaseView):
    """View for managing picking lists."""

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the picking list view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Picking List View")

        # Get services
        self.picking_list_service = self.get_service(IPickingListService)
        self.project_service = self.get_service(IProjectService)
        self.order_service = self.get_service(IOrderService)

        # Initialize UI
        self._setup_ui()

        # Load initial data
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

    def _load_data(self):
        """Load picking lists data."""
        try:
            # Clear existing items
            for item in self.lists_tree.get_children():
                self.lists_tree.delete(item)

            # Get picking lists from service
            picking_lists = self.picking_list_service.get_all_picking_lists()

            # Apply status filter if needed
            status = self.status_var.get()
            if status != "All":
                picking_lists = [pl for pl in picking_lists if pl.get("status") == status]

            # Populate treeview
            for picking_list in picking_lists:
                self.lists_tree.insert("", tk.END, values=(
                    picking_list["id"],
                    picking_list["name"],
                    picking_list["status"],
                    len(picking_list.get("items", [])),
                    self._format_priority(picking_list.get("priority", 0))
                ))

            self.logger.info(f"Loaded {len(picking_lists)} picking lists")

        except Exception as e:
            self.logger.error(f"Error loading picking lists: {str(e)}")
            messagebox.showerror("Error", f"Failed to load picking lists: {str(e)}")

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

    def _on_list_select(self, event=None):
        """Handle picking list selection."""
        # Get selected item
        selection = self.lists_tree.selection()
        if not selection:
            # Clear details and disable
            self._clear_details()
            self._toggle_details(False)
            return

        # Get picking list ID
        picking_list_id = self.lists_tree.item(selection[0], "values")[0]

        try:
            # Load picking list details
            picking_list = self.picking_list_service.get_picking_list(int(picking_list_id))

            # Populate details form
            self._populate_details(picking_list)

            # Enable details section
            self._toggle_details(True)

        except Exception as e:
            self.logger.error(f"Error loading picking list details: {str(e)}")
            messagebox.showerror("Error", f"Failed to load picking list details: {str(e)}")

    def _populate_details(self, picking_list: Dict[str, Any]):
        """Populate picking list details."""
        # Update header info
        self.current_picking_list_id = picking_list["id"]

        # Update form fields
        self.list_name_var.set(picking_list["name"])
        self.list_status_var.set(picking_list["status"])
        self.list_priority_var.set(f"{picking_list['priority']} ({self._format_priority(picking_list['priority'])})")
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
            location = "Unknown"
            if "storage_location" in item and item["storage_location"]:
                loc = item["storage_location"]
                location_parts = []
                if loc.get("section"):
                    location_parts.append(loc["section"])
                if loc.get("shelf"):
                    location_parts.append(f"Shelf {loc['shelf']}")
                if loc.get("bin"):
                    location_parts.append(f"Bin {loc['bin']}")
                if location_parts:
                    location = " - ".join(location_parts)
                else:
                    location = loc.get("name", "Unknown")

            # Insert item
            self.items_tree.insert("", tk.END, values=(
                item["id"],
                item["item_type"],
                item["name"],
                item["quantity_required"],
                item["quantity_picked"],
                item["unit"],
                location,
                status
            ))

    def _clear_details(self):
        """Clear picking list details."""
        self.current_picking_list_id = None

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
            # Create dialog
            dialog = tk.Toplevel(self)
            dialog.title("New Picking List")
            dialog.geometry("500x400")
            dialog.transient(self)
            dialog.grab_set()

            # Create form
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
                orders = self.order_service.get_all_orders()
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
                    result = self.picking_list_service.create_picking_list(picking_list_data)
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
                """Create picking list from order."""
                try:
                    # Check if order selected
                    order_str = order_var.get()
                    if not order_str:
                        messagebox.showerror("Error", "Please select an order")
                        return

                    # Extract order ID
                    order_id = int(order_str.split(':')[0])

                    # Generate picking list
                    result = self.picking_list_service.generate_picking_list_from_order(order_id)
                    if result:
                        messagebox.showinfo("Success", "Picking list generated from order successfully")
                        dialog.destroy()
                        self.on_refresh()

                except Exception as e:
                    self.logger.error(f"Error generating picking list from order: {str(e)}")
                    messagebox.showerror("Error", f"Failed to generate picking list: {str(e)}")

            ttk.Button(button_frame, text="Create Empty List", command=create_empty).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Generate from Project", command=create_from_project).pack(side=tk.LEFT,
                                                                                                     padx=5)
            ttk.Button(button_frame, text="Generate from Order", command=create_from_order).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

        except Exception as e:
            self.logger.error(f"Error opening create picking list dialog: {str(e)}")
            messagebox.showerror("Error", f"Failed to open create dialog: {str(e)}")

    def _save_picking_list(self):
        """Save picking list changes."""
        try:
            # Check if picking list is selected
            if not hasattr(self, 'current_picking_list_id') or not self.current_picking_list_id:
                return

            # Extract priority number from combo value
            priority_str = self.list_priority_var.get().split(' ')[0]
            try:
                priority = int(priority_str)
            except ValueError:
                priority = 0

            # Create update data
            update_data = {
                "name": self.list_name_var.get().strip(),
                "status": self.list_status_var.get(),
                "priority": priority,
                "assigned_to": self.list_assigned_var.get().strip(),
                "notes": self.list_notes_text.get("1.0", tk.END).strip()
            }

            # Update picking list
            result = self.picking_list_service.update_picking_list(self.current_picking_list_id, update_data)
            if result:
                messagebox.showinfo("Success", "Picking list updated successfully")
                self.on_refresh()

        except Exception as e:
            self.logger.error(f"Error saving picking list: {str(e)}")
            messagebox.showerror("Error", f"Failed to save picking list: {str(e)}")

    def _delete_picking_list(self):
        """Delete the selected picking list."""
        try:
            # Get selected item
            selection = self.lists_tree.selection()
            if not selection:
                messagebox.showinfo("Info", "Please select a picking list to delete")
                return

            # Get picking list ID
            picking_list_id = int(self.lists_tree.item(selection[0], "values")[0])
            picking_list_name = self.lists_tree.item(selection[0], "values")[1]

            # Confirm deletion
            if not messagebox.askyesno("Confirm",
                                       f"Are you sure you want to delete picking list '{picking_list_name}'?"):
                return

            # Delete picking list
            result = self.picking_list_service.delete_picking_list(picking_list_id)
            if result:
                messagebox.showinfo("Success", "Picking list deleted successfully")
                self.on_refresh()

        except Exception as e:
            self.logger.error(f"Error deleting picking list: {str(e)}")
            messagebox.showerror("Error", f"Failed to delete picking list: {str(e)}")

    def _add_item(self):
        """Add an item to the picking list."""
        try:
            # Check if picking list is selected
            if not hasattr(self, 'current_picking_list_id') or not self.current_picking_list_id:
                messagebox.showinfo("Info", "Please select a picking list first")
                return

            # Create dialog
            dialog = tk.Toplevel(self)
            dialog.title("Add Item")
            dialog.geometry("500x350")
            dialog.transient(self)
            dialog.grab_set()

            # Create form
            form_frame = ttk.Frame(dialog, padding=10)
            form_frame.pack(fill=tk.BOTH, expand=True)

            # Form fields
            ttk.Label(form_frame, text="Item Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            type_var = tk.StringVar(value="leather")
            type_combo = ttk.Combobox(form_frame, textvariable=type_var,
                                      values=["leather", "hardware", "thread", "adhesive", "dye", "other"], width=20)
            type_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

            ttk.Label(form_frame, text="Name:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
            name_var = tk.StringVar()
            name_entry = ttk.Entry(form_frame, textvariable=name_var, width=40)
            name_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

            ttk.Label(form_frame, text="Description:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
            description_var = tk.StringVar()
            description_entry = ttk.Entry(form_frame, textvariable=description_var, width=40)
            description_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

            ttk.Label(form_frame, text="Quantity Required:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
            quantity_var = tk.DoubleVar(value=1.0)
            quantity_entry = ttk.Spinbox(form_frame, from_=0.1, to=9999, increment=0.1, textvariable=quantity_var,
                                         width=10)
            quantity_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

            ttk.Label(form_frame, text="Unit:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
            unit_var = tk.StringVar(value="piece")
            unit_combo = ttk.Combobox(form_frame, textvariable=unit_var,
                                      values=["piece", "meter", "sq_meter", "sq_foot", "gram", "ml", "yard", "inch",
                                              "foot"], width=20)
            unit_combo.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)

            ttk.Label(form_frame, text="Notes:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
            notes_text = tk.Text(form_frame, height=3, width=40)
            notes_text.grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)

            # Buttons
            button_frame = ttk.Frame(form_frame)
            button_frame.grid(row=6, column=0, columnspan=2, pady=10)

            def add_item():
                """Add item to picking list."""
                try:
                    # Validate fields
                    if not name_var.get().strip():
                        messagebox.showerror("Error", "Item name is required")
                        return

                    # Create item data
                    item_data = {
                        "item_type": type_var.get(),
                        "name": name_var.get().strip(),
                        "description": description_var.get().strip(),
                        "quantity_required": float(quantity_var.get()),
                        "unit": unit_var.get(),
                        "notes": notes_text.get("1.0", tk.END).strip()
                    }

                    # Add item to picking list
                    result = self.picking_list_service.add_item_to_picking_list(self.current_picking_list_id, item_data)
                    if result:
                        messagebox.showinfo("Success", "Item added successfully")
                        dialog.destroy()

                        # Refresh picking list details
                        self._on_list_select()

                except Exception as e:
                    self.logger.error(f"Error adding item: {str(e)}")
                    messagebox.showerror("Error", f"Failed to add item: {str(e)}")

            ttk.Button(button_frame, text="Add Item", command=add_item).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            self.logger.error(f"Error opening add item dialog: {str(e)}")
            messagebox.showerror("Error", f"Failed to open add item dialog: {str(e)}")

    def _edit_item(self, event=None):
        """Edit a picking list item."""
        try:
            # Get selected item
            selection = self.items_tree.selection()
            if not selection:
                return

            # Get item ID
            item_id = int(self.items_tree.item(selection[0], "values")[0])

            # Get picking list to find the item
            picking_list = self.picking_list_service.get_picking_list(self.current_picking_list_id)
            item = next((i for i in picking_list.get("items", []) if i["id"] == item_id), None)

            if not item:
                messagebox.showerror("Error", f"Item with ID {item_id} not found")
                return

            # Create dialog
            dialog = tk.Toplevel(self)
            dialog.title("Edit Item")
            dialog.geometry("500x400")
            dialog.transient(self)
            dialog.grab_set()

            # Create form
            form_frame = ttk.Frame(dialog, padding=10)
            form_frame.pack(fill=tk.BOTH, expand=True)

            # Form fields
            ttk.Label(form_frame, text="Item Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            type_var = tk.StringVar(value=item.get("item_type", "leather"))
            type_combo = ttk.Combobox(form_frame, textvariable=type_var,
                                      values=["leather", "hardware", "thread", "adhesive", "dye", "other"], width=20)
            type_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

            ttk.Label(form_frame, text="Name:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
            name_var = tk.StringVar(value=item.get("name", ""))
            name_entry = ttk.Entry(form_frame, textvariable=name_var, width=40)
            name_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

            ttk.Label(form_frame, text="Description:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
            description_var = tk.StringVar(value=item.get("description", ""))
            description_entry = ttk.Entry(form_frame, textvariable=description_var, width=40)
            description_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

            ttk.Label(form_frame, text="Quantity Required:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
            quantity_var = tk.DoubleVar(value=item.get("quantity_required", 1.0))
            quantity_entry = ttk.Spinbox(form_frame, from_=0.1, to=9999, increment=0.1, textvariable=quantity_var,
                                         width=10)
            quantity_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

            ttk.Label(form_frame, text="Quantity Picked:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
            picked_var = tk.DoubleVar(value=item.get("quantity_picked", 0.0))
            picked_entry = ttk.Spinbox(form_frame, from_=0, to=9999, increment=0.1, textvariable=picked_var, width=10)
            picked_entry.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)

            ttk.Label(form_frame, text="Unit:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
            unit_var = tk.StringVar(value=item.get("unit", "piece"))
            unit_combo = ttk.Combobox(form_frame, textvariable=unit_var,
                                      values=["piece", "meter", "sq_meter", "sq_foot", "gram", "ml", "yard", "inch",
                                              "foot"], width=20)
            unit_combo.grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)

            ttk.Label(form_frame, text="Picked:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
            is_picked_var = tk.BooleanVar(value=item.get("is_picked", False))
            is_picked_check = ttk.Checkbutton(form_frame, variable=is_picked_var)
            is_picked_check.grid(row=6, column=1, sticky=tk.W, padx=5, pady=5)

            ttk.Label(form_frame, text="Notes:").grid(row=7, column=0, sticky=tk.W, padx=5, pady=5)
            notes_text = tk.Text(form_frame, height=3, width=40)
            notes_text.insert("1.0", item.get("notes", ""))
            notes_text.grid(row=7, column=1, sticky=tk.W, padx=5, pady=5)

            # Buttons
            button_frame = ttk.Frame(form_frame)
            button_frame.grid(row=8, column=0, columnspan=2, pady=10)

            def save_item():
                """Save item changes."""
                try:
                    # Validate fields
                    if not name_var.get().strip():
                        messagebox.showerror("Error", "Item name is required")
                        return

                    # Create update data
                    item_data = {
                        "item_type": type_var.get(),
                        "name": name_var.get().strip(),
                        "description": description_var.get().strip(),
                        "quantity_required": float(quantity_var.get()),
                        "quantity_picked": float(picked_var.get()),
                        "unit": unit_var.get(),
                        "is_picked": is_picked_var.get(),
                        "notes": notes_text.get("1.0", tk.END).strip()
                    }

                    # Update item
                    result = self.picking_list_service.update_picking_list_item(item_id, item_data)
                    if result:
                        messagebox.showinfo("Success", "Item updated successfully")
                        dialog.destroy()

                        # Refresh picking list details
                        self._on_list_select()

                except Exception as e:
                    self.logger.error(f"Error updating item: {str(e)}")
                    messagebox.showerror("Error", f"Failed to update item: {str(e)}")

            ttk.Button(button_frame, text="Save Changes", command=save_item).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            self.logger.error(f"Error opening edit item dialog: {str(e)}")
            messagebox.showerror("Error", f"Failed to open edit item dialog: {str(e)}")

    def _remove_item(self):
        """Remove an item from the picking list."""
        try:
            # Get selected item
            selection = self.items_tree.selection()
            if not selection:
                messagebox.showinfo("Info", "Please select an item to remove")
                return

            # Get item ID
            item_id = int(self.items_tree.item(selection[0], "values")[0])
            item_name = self.items_tree.item(selection[0], "values")[2]

            # Confirm deletion
            if not messagebox.askyesno("Confirm", f"Are you sure you want to remove item '{item_name}'?"):
                return

            # Remove item
            result = self.picking_list_service.remove_item_from_picking_list(item_id)
            if result:
                messagebox.showinfo("Success", "Item removed successfully")

                # Refresh picking list details
                self._on_list_select()

        except Exception as e:
            self.logger.error(f"Error removing item: {str(e)}")
            messagebox.showerror("Error", f"Failed to remove item: {str(e)}")

    def _mark_item_picked(self):
        """Mark an item as picked."""
        try:
            # Get selected item
            selection = self.items_tree.selection()
            if not selection:
                messagebox.showinfo("Info", "Please select an item to mark as picked")
                return

            # Get item ID
            item_id = int(self.items_tree.item(selection[0], "values")[0])
            item_name = self.items_tree.item(selection[0], "values")[2]

            # Get required quantity
            quantity_required = float(self.items_tree.item(selection[0], "values")[3])

            # Create dialog for quantity input
            dialog = tk.Toplevel(self)
            dialog.title(f"Mark Item as Picked: {item_name}")
            dialog.geometry("400x200")
            dialog.transient(self)