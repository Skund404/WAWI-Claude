# gui/views/projects/picking_list_view.py
"""
Picking list view for managing material requirements for projects.

This view provides an interface for creating, viewing, and processing
picking lists for materials needed in a project.
"""

import datetime
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional, Tuple

from database.models.enums import InventoryStatus, PickingListStatus
from gui.base.base_view import BaseView
from gui.theme import COLORS, get_status_style
from gui.utils.event_bus import publish
from gui.utils.service_access import get_service
from gui.widgets.status_badge import StatusBadge


class PickingListView(BaseView):
    """
    View for displaying and managing picking lists for materials.
    """

    def __init__(self, parent, **kwargs):
        """Initialize the picking list view.

        Args:
            parent: The parent widget
            **kwargs: Additional arguments including:
                picking_list_id: ID of the picking list to view/edit
                project_id: ID of the project (to create a new picking list)
                readonly: Whether the view should be read-only
        """
        super().__init__(parent)
        self.title = "Picking List"
        self.icon = "📋"
        self.logger = logging.getLogger(__name__)

        # Store view parameters
        self.picking_list_id = kwargs.get("picking_list_id")
        self.project_id = kwargs.get("project_id")
        self.readonly = kwargs.get("readonly", False)

        if not self.picking_list_id and not self.project_id:
            messagebox.showerror("Error", "Either a picking list ID or project ID is required")
            self.on_back()
            return

        # Initialize services
        self.project_service = get_service("project_service")
        self.picking_list_service = get_service("picking_list_service")
        self.inventory_service = get_service("inventory_service")

        # Build the view
        self.build()

        # Load data if viewing an existing picking list
        if self.picking_list_id:
            self.load_picking_list()
        elif self.project_id:
            # Create new picking list for the project
            self.create_new_picking_list()

    def build(self):
        """Build the picking list view."""
        super().build()

        # Create main frame
        main_frame = ttk.Frame(self.content_frame, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create info section and item list
        self.create_info_section(main_frame)
        self.create_item_list(main_frame)
        self.create_actions_section(main_frame)

    def _add_default_action_buttons(self):
        """Add default action buttons to the header."""
        actions_frame = ttk.Frame(self.header)
        actions_frame.pack(side=tk.RIGHT, padx=10)

        if not self.readonly:
            ttk.Button(
                actions_frame,
                text="Save",
                command=self.on_save
            ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            actions_frame,
            text="Back",
            command=self.on_back
        ).pack(side=tk.RIGHT, padx=5)

        # Add print button
        ttk.Button(
            actions_frame,
            text="Print",
            command=self.on_print
        ).pack(side=tk.RIGHT, padx=5)

    def create_info_section(self, parent):
        """Create the info section with picking list details.

        Args:
            parent: The parent widget
        """
        info_frame = ttk.LabelFrame(parent, text="Picking List Information")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        # Left column with basic info
        left_frame = ttk.Frame(info_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Right column with status and progress
        right_frame = ttk.Frame(info_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left column content
        ttk.Label(left_frame, text="Picking List ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.id_label = ttk.Label(left_frame, text="New")
        self.id_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(left_frame, text="Project:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.project_label = ttk.Label(left_frame, text="")
        self.project_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(left_frame, text="Created:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.created_label = ttk.Label(left_frame, text="")
        self.created_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(left_frame, text="Due Date:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.due_date_var = tk.StringVar()

        due_date_frame = ttk.Frame(left_frame)
        due_date_frame.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)

        self.due_date_entry = ttk.Entry(due_date_frame, textvariable=self.due_date_var, width=12)
        self.due_date_entry.pack(side=tk.LEFT)

        if not self.readonly:
            ttk.Button(
                due_date_frame,
                text="...",
                width=2,
                command=lambda: self.show_date_picker(self.due_date_var)
            ).pack(side=tk.LEFT, padx=(5, 0))

        # Right column content
        ttk.Label(right_frame, text="Status:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)

        status_frame = ttk.Frame(right_frame)
        status_frame.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        self.status_var = tk.StringVar(value="draft")

        # Only show status combobox if not readonly
        if not self.readonly:
            self.status_combo = ttk.Combobox(status_frame, textvariable=self.status_var, width=15, state="readonly")
            status_values = [s.value.replace("_", " ").title() for s in PickingListStatus]
            self.status_combo["values"] = status_values
            self.status_combo.pack(side=tk.LEFT)
            self.status_combo.bind("<<ComboboxSelected>>", self.on_status_change)

        self.status_badge = StatusBadge(status_frame, "Draft", "draft")
        self.status_badge.pack(side=tk.LEFT, padx=(10 if not self.readonly else 0, 0))

        # Progress
        ttk.Label(right_frame, text="Progress:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)

        progress_frame = ttk.Frame(right_frame)
        progress_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            orient=tk.HORIZONTAL,
            length=200,
            mode='determinate',
            variable=self.progress_var
        )
        self.progress_bar.pack(side=tk.LEFT)

        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack(side=tk.LEFT, padx=(5, 0))

        # Assigned to
        ttk.Label(right_frame, text="Assigned To:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.assigned_to_var = tk.StringVar()
        self.assigned_to_entry = ttk.Entry(right_frame, textvariable=self.assigned_to_var, width=20)
        self.assigned_to_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        self.assigned_to_entry.configure(state=tk.NORMAL if not self.readonly else "readonly")

        # Notes
        ttk.Label(right_frame, text="Notes:").grid(row=3, column=0, sticky=tk.NW, padx=5, pady=2)
        self.notes_text = tk.Text(right_frame, width=25, height=3)
        self.notes_text.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
        self.notes_text.configure(state=tk.NORMAL if not self.readonly else tk.DISABLED)

    def create_item_list(self, parent):
        """Create the item list section.

        Args:
            parent: The parent widget
        """
        items_frame = ttk.LabelFrame(parent, text="Materials to Pick")
        items_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create toolbar for the item list
        toolbar = ttk.Frame(items_frame)
        toolbar.pack(fill=tk.X, padx=10, pady=(10, 5))

        if not self.readonly:
            ttk.Button(
                toolbar,
                text="Add Item",
                command=self.on_add_item
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                toolbar,
                text="Remove Item",
                command=self.on_remove_item
            ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            toolbar,
            text="Check Availability",
            command=self.on_check_availability
        ).pack(side=tk.LEFT, padx=5)

        # Filter options
        ttk.Label(toolbar, text="Show:").pack(side=tk.RIGHT, padx=(0, 5))
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(toolbar, textvariable=self.filter_var, width=15, state="readonly")
        filter_combo["values"] = ["All", "Pending", "Picked", "Out of Stock"]
        filter_combo.pack(side=tk.RIGHT, padx=5)
        filter_combo.bind("<<ComboboxSelected>>", self.on_filter_change)

        # Create treeview for items
        columns = (
            "id", "material", "type", "quantity_needed", "quantity_picked",
            "unit", "location", "status", "notes"
        )

        self.items_tree = ttk.Treeview(items_frame, columns=columns, show="headings", height=10)

        self.items_tree.heading("id", text="ID")
        self.items_tree.heading("material", text="Material")
        self.items_tree.heading("type", text="Type")
        self.items_tree.heading("quantity_needed", text="Needed")
        self.items_tree.heading("quantity_picked", text="Picked")
        self.items_tree.heading("unit", text="Unit")
        self.items_tree.heading("location", text="Location")
        self.items_tree.heading("status", text="Status")
        self.items_tree.heading("notes", text="Notes")

        self.items_tree.column("id", width=50, minwidth=50)
        self.items_tree.column("material", width=200, minwidth=150)
        self.items_tree.column("type", width=100, minwidth=100)
        self.items_tree.column("quantity_needed", width=80, minwidth=80)
        self.items_tree.column("quantity_picked", width=80, minwidth=80)
        self.items_tree.column("unit", width=80, minwidth=80)
        self.items_tree.column("location", width=120, minwidth=100)
        self.items_tree.column("status", width=100, minwidth=100)
        self.items_tree.column("notes", width=150, minwidth=100)

        # Add vertical scrollbar
        scrollbar = ttk.Scrollbar(items_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=scrollbar.set)

        # Pack tree and scrollbar
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=5)

        # Bind double click to edit quantities
        self.items_tree.bind("<Double-1>", self.on_edit_item)

    def create_actions_section(self, parent):
        """Create the actions section.

        Args:
            parent: The parent widget
        """
        actions_frame = ttk.Frame(parent)
        actions_frame.pack(fill=tk.X, pady=(0, 10))

        # Create action buttons based on status
        if not self.readonly:
            self.start_picking_btn = ttk.Button(
                actions_frame,
                text="Start Picking",
                command=self.on_start_picking
            )
            self.start_picking_btn.pack(side=tk.LEFT, padx=5)

            self.complete_picking_btn = ttk.Button(
                actions_frame,
                text="Complete Picking",
                command=self.on_complete_picking,
                state=tk.DISABLED
            )
            self.complete_picking_btn.pack(side=tk.LEFT, padx=5)

            self.cancel_picking_btn = ttk.Button(
                actions_frame,
                text="Cancel Picking List",
                command=self.on_cancel_picking
            )
            self.cancel_picking_btn.pack(side=tk.LEFT, padx=5)

        # Summary section
        summary_frame = ttk.LabelFrame(parent, text="Summary")
        summary_frame.pack(fill=tk.X, pady=(0, 10))

        summary_grid = ttk.Frame(summary_frame)
        summary_grid.pack(fill=tk.X, padx=10, pady=5)

        # Item counts
        ttk.Label(summary_grid, text="Total Items:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.total_items_label = ttk.Label(summary_grid, text="0")
        self.total_items_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(summary_grid, text="Picked Items:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.picked_items_label = ttk.Label(summary_grid, text="0")
        self.picked_items_label.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)

        ttk.Label(summary_grid, text="Pending Items:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=2)
        self.pending_items_label = ttk.Label(summary_grid, text="0")
        self.pending_items_label.grid(row=0, column=5, sticky=tk.W, padx=5, pady=2)

        ttk.Label(summary_grid, text="Out of Stock:").grid(row=0, column=6, sticky=tk.W, padx=5, pady=2)
        self.out_of_stock_label = ttk.Label(summary_grid, text="0")
        self.out_of_stock_label.grid(row=0, column=7, sticky=tk.W, padx=5, pady=2)

    def load_picking_list(self):
        """Load picking list data from the service."""
        try:
            # Get picking list data from service
            picking_list = self.picking_list_service.get_picking_list(
                self.picking_list_id,
                include_items=True,
                include_project=True
            )

            if not picking_list:
                messagebox.showerror("Error", f"Picking list not found with ID {self.picking_list_id}")
                self.on_back()
                return

            # Update title
            self.title = f"Picking List #{picking_list.id}" + (" (View Only)" if self.readonly else "")
            title_label = self.header.winfo_children()[0]
            if isinstance(title_label, ttk.Label):
                title_label.configure(text=self.title)

            # Update project ID
            self.project_id = picking_list.project_id if hasattr(picking_list, 'project_id') else None

            # Populate info section
            self.id_label.configure(text=str(picking_list.id))

            # Project info
            project_name = "Unknown Project"
            if hasattr(picking_list, 'project') and picking_list.project:
                project = picking_list.project
                project_name = project.name if hasattr(project, 'name') else "Unknown Project"
            self.project_label.configure(text=project_name)

            # Creation date
            created_at = "N/A"
            if hasattr(picking_list, 'created_at') and picking_list.created_at:
                created_at = picking_list.created_at.strftime("%Y-%m-%d %H:%M")
            self.created_label.configure(text=created_at)

            # Due date
            if hasattr(picking_list, 'due_date') and picking_list.due_date:
                self.due_date_var.set(picking_list.due_date.strftime("%Y-%m-%d"))

            # Status
            status_value = "draft"
            if hasattr(picking_list, 'status') and picking_list.status:
                status_value = picking_list.status.value
                status_display = picking_list.status.value.replace("_", " ").title()

                # Update status variable
                self.status_var.set(status_value)

                # Update status badge
                self.status_badge.set_text(status_display, status_value)

            # Progress
            progress = 0
            if hasattr(picking_list, 'progress') and picking_list.progress is not None:
                progress = picking_list.progress
            self.progress_var.set(progress)
            self.progress_label.configure(text=f"{progress}%")

            # Assigned to
            if hasattr(picking_list, 'assigned_to') and picking_list.assigned_to:
                self.assigned_to_var.set(picking_list.assigned_to)

            # Notes
            if hasattr(picking_list, 'notes') and picking_list.notes:
                self.notes_text.delete("1.0", tk.END)
                self.notes_text.insert("1.0", picking_list.notes)

            # Populate items
            if hasattr(picking_list, 'items') and picking_list.items:
                self.update_items_list(picking_list.items)

            # Update action buttons based on status
            self.update_action_buttons(status_value)

        except Exception as e:
            self.logger.error(f"Error loading picking list: {e}")
            messagebox.showerror("Error", f"Failed to load picking list: {str(e)}")

    def create_new_picking_list(self):
        """Create a new picking list for the project."""
        try:
            # Create new picking list
            picking_list = self.picking_list_service.create_picking_list(self.project_id)

            # Update ID
            self.picking_list_id = picking_list.id

            # Load the newly created picking list
            self.load_picking_list()

        except Exception as e:
            self.logger.error(f"Error creating picking list: {e}")
            messagebox.showerror("Error", f"Failed to create picking list: {str(e)}")
            self.on_back()

    def update_items_list(self, items):
        """Update the items list in the treeview.

        Args:
            items: List of picking list items
        """
        # Clear existing items
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)

        # Insert items
        total_count = 0
        picked_count = 0
        pending_count = 0
        out_of_stock_count = 0

        for item in items:
            # Skip if filtered out
            if not self.should_show_item(item):
                continue

            # Extract item values
            item_id = item.id if hasattr(item, 'id') else "N/A"

            material_name = "Unknown Material"
            if hasattr(item, 'material') and item.material:
                material_name = item.material.name if hasattr(item.material, 'name') else "Unknown Material"

            material_type = "Unknown"
            if hasattr(item, 'material') and item.material and hasattr(item.material, 'type') and item.material.type:
                material_type = item.material.type.value.replace("_", " ").title()

            quantity_needed = item.quantity_ordered if hasattr(item, 'quantity_ordered') else 0
            quantity_picked = item.quantity_picked if hasattr(item, 'quantity_picked') else 0

            unit = "pc"
            if hasattr(item, 'unit') and item.unit:
                unit = item.unit

            location = "Unknown"
            if hasattr(item, 'storage_location') and item.storage_location:
                location = item.storage_location

            # Determine status
            if quantity_picked >= quantity_needed:
                status = "Picked"
                picked_count += 1
            elif hasattr(item, 'available') and item.available is not None and item.available < quantity_needed:
                status = "Out of Stock"
                out_of_stock_count += 1
            else:
                status = "Pending"
                pending_count += 1

            notes = item.notes if hasattr(item, 'notes') else ""

            # Insert into treeview
            item_id_str = str(item_id)
            self.items_tree.insert(
                '', 'end',
                iid=item_id_str,
                values=(
                    item_id,
                    material_name,
                    material_type,
                    quantity_needed,
                    quantity_picked,
                    unit,
                    location,
                    status,
                    notes
                )
            )

            # Apply status styling
            if status == "Picked":
                self.items_tree.tag_configure("picked", background=COLORS["success_light"])
                self.items_tree.item(item_id_str, tags=("picked",))
            elif status == "Out of Stock":
                self.items_tree.tag_configure("out_of_stock", background=COLORS["error_light"])
                self.items_tree.item(item_id_str, tags=("out_of_stock",))

            total_count += 1

        # Update summary
        self.total_items_label.configure(text=str(total_count))
        self.picked_items_label.configure(text=str(picked_count))
        self.pending_items_label.configure(text=str(pending_count))
        self.out_of_stock_label.configure(text=str(out_of_stock_count))

        # Update progress
        if total_count > 0:
            progress = int((picked_count / total_count) * 100)
            self.progress_var.set(progress)
            self.progress_label.configure(text=f"{progress}%")

    def should_show_item(self, item):
        """Check if an item should be shown based on the current filter.

        Args:
            item: The item to check

        Returns:
            True if the item should be shown, False otherwise
        """
        filter_value = self.filter_var.get()

        if filter_value == "All":
            return True

        quantity_needed = item.quantity_ordered if hasattr(item, 'quantity_ordered') else 0
        quantity_picked = item.quantity_picked if hasattr(item, 'quantity_picked') else 0

        if filter_value == "Picked" and quantity_picked >= quantity_needed:
            return True
        elif filter_value == "Pending" and quantity_picked < quantity_needed:
            available = True
            if hasattr(item, 'available') and item.available is not None:
                available = item.available >= (quantity_needed - quantity_picked)
            return available
        elif filter_value == "Out of Stock":
            if hasattr(item, 'available') and item.available is not None:
                return item.available < (quantity_needed - quantity_picked)

        return False

    def update_action_buttons(self, status):
        """Update action buttons based on the current status.

        Args:
            status: Current picking list status
        """
        if self.readonly:
            return

        # Enable/disable buttons based on status
        if status == "draft":
            self.start_picking_btn.configure(state=tk.NORMAL)
            self.complete_picking_btn.configure(state=tk.DISABLED)
            self.cancel_picking_btn.configure(state=tk.NORMAL)
        elif status == "in_progress":
            self.start_picking_btn.configure(state=tk.DISABLED)
            self.complete_picking_btn.configure(state=tk.NORMAL)
            self.cancel_picking_btn.configure(state=tk.NORMAL)
        elif status in ["completed", "cancelled"]:
            self.start_picking_btn.configure(state=tk.DISABLED)
            self.complete_picking_btn.configure(state=tk.DISABLED)
            self.cancel_picking_btn.configure(state=tk.DISABLED)
        else:
            self.start_picking_btn.configure(state=tk.NORMAL)
            self.complete_picking_btn.configure(state=tk.NORMAL)
            self.cancel_picking_btn.configure(state=tk.NORMAL)

    def on_status_change(self, event):
        """Handle status change from combobox.

        Args:
            event: Combobox selection event
        """
        status_value = self.status_var.get().lower().replace(" ", "_")
        status_display = self.status_var.get()

        # Update status badge
        self.status_badge.set_text(status_display, status_value)

        # Update action buttons
        self.update_action_buttons(status_value)

    def on_filter_change(self, event):
        """Handle filter change.

        Args:
            event: Combobox selection event
        """
        # Reload picking list with new filter
        self.load_picking_list()

    def on_add_item(self):
        """Handle add item button click."""
        # Create add item dialog
        dialog = tk.Toplevel(self)
        dialog.title("Add Material to Picking List")
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.grab_set()

        # Create search frame
        search_frame = ttk.Frame(dialog, padding=5)
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)

        # Material type filter
        ttk.Label(search_frame, text="Type:").pack(side=tk.LEFT, padx=(10, 5))
        type_var = tk.StringVar(value="All")
        type_combo = ttk.Combobox(search_frame, textvariable=type_var, width=15, state="readonly")
        type_combo["values"] = ["All", "Leather", "Hardware", "Thread", "Adhesive", "Other"]
        type_combo.pack(side=tk.LEFT, padx=5)

        material_service = get_service("material_service")

        def search_materials():
            """Search materials based on criteria."""
            search_text = search_var.get()
            material_type = type_var.get() if type_var.get() != "All" else None

            try:
                # Get materials from service
                materials = material_service.search_materials(
                    search_text=search_text,
                    material_type=material_type
                )

                # Clear existing items
                for item in materials_tree.get_children():
                    materials_tree.delete(item)

                # Insert materials
                for material in materials:
                    material_id = material.id if hasattr(material, 'id') else "N/A"
                    name = material.name if hasattr(material, 'name') else "Unnamed"

                    type_str = "Unknown"
                    if hasattr(material, 'type') and material.type:
                        type_str = material.type.value.replace("_", " ").title()

                    # Get inventory status
                    inventory_status = "Unknown"
                    quantity_available = 0

                    if hasattr(material, 'inventory') and material.inventory:
                        inventory = material.inventory
                        status = inventory.status.value if hasattr(inventory,
                                                                   'status') and inventory.status else "unknown"
                        inventory_status = status.replace("_", " ").title()
                        quantity_available = inventory.quantity if hasattr(inventory, 'quantity') else 0

                    unit = "pc"
                    if hasattr(material, 'unit') and material.unit:
                        unit = material.unit.value

                    materials_tree.insert(
                        '', 'end',
                        iid=material_id,
                        values=(material_id, name, type_str, inventory_status, quantity_available, unit)
                    )

            except Exception as e:
                self.logger.error(f"Error searching materials: {e}")
                messagebox.showerror("Search Error", f"Failed to search materials: {str(e)}", parent=dialog)

        ttk.Button(
            search_frame,
            text="Search",
            command=search_materials
        ).pack(side=tk.LEFT, padx=5)

        # Create materials treeview
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("id", "name", "type", "status", "available", "unit")
        materials_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)

        materials_tree.heading("id", text="ID")
        materials_tree.heading("name", text="Name")
        materials_tree.heading("type", text="Type")
        materials_tree.heading("status", text="Status")
        materials_tree.heading("available", text="Available")
        materials_tree.heading("unit", text="Unit")

        materials_tree.column("id", width=50)
        materials_tree.column("name", width=200)
        materials_tree.column("type", width=100)
        materials_tree.column("status", width=100)
        materials_tree.column("available", width=80)
        materials_tree.column("unit", width=80)

        materials_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=materials_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        materials_tree.configure(yscrollcommand=scrollbar.set)

        # Quantity frame
        quantity_frame = ttk.LabelFrame(dialog, text="Quantity")
        quantity_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(quantity_frame, text="Quantity:").grid(row=0, column=0, padx=5, pady=5)
        quantity_var = tk.StringVar(value="1")
        quantity_spin = ttk.Spinbox(quantity_frame, from_=0.1, to=1000, increment=0.1, textvariable=quantity_var)
        quantity_spin.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(quantity_frame, text="Notes:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.N)
        notes_text = tk.Text(quantity_frame, width=30, height=3)
        notes_text.grid(row=1, column=1, padx=5, pady=5)

        # Handle material selection
        def add_selected_material():
            """Add the selected material to the picking list."""
            selected_id = materials_tree.focus()
            if not selected_id:
                messagebox.showwarning("No Selection", "Please select a material to add.", parent=dialog)
                return

            # Get material data
            material_data = materials_tree.item(selected_id, "values")
            material_id = material_data[0]
            material_name = material_data[1]

            # Check if already added
            items = self.items_tree.get_children()
            for item_id in items:
                item_values = self.items_tree.item(item_id, "values")
                if item_values[1] == material_name:
                    messagebox.showwarning(
                        "Already Added",
                        f"Material '{material_name}' is already in this picking list.",
                        parent=dialog
                    )
                    return

            # Get quantity
            try:
                quantity = float(quantity_var.get())
                if quantity <= 0:
                    messagebox.showwarning("Invalid Quantity", "Quantity must be greater than zero.", parent=dialog)
                    return
            except ValueError:
                messagebox.showwarning("Invalid Quantity", "Quantity must be a number.", parent=dialog)
                return

            # Get notes
            notes = notes_text.get("1.0", tk.END).strip()

            try:
                # Add material to picking list
                result = self.picking_list_service.add_item_to_picking_list(
                    self.picking_list_id,
                    material_id,
                    quantity,
                    material_data[5],  # unit
                    notes
                )

                if result:
                    # Reload picking list
                    self.load_picking_list()

                    # Close dialog
                    dialog.destroy()

                    # Show success message
                    messagebox.showinfo("Success", f"Material '{material_name}' added to picking list.")

            except Exception as e:
                self.logger.error(f"Error adding material: {e}")
                messagebox.showerror("Error", f"Failed to add material: {str(e)}", parent=dialog)

        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="Add Material",
            command=add_selected_material
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        # Initial search
        search_materials()

        # Set focus to search entry
        search_entry.focus_set()

    def on_edit_item(self, event):
        """Handle item double-click to edit quantities.

        Args:
            event: Double-click event
        """
        if self.readonly:
            return

        # Get the item
        region = self.items_tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        # Get the clicked item and column
        item_id = self.items_tree.identify_row(event.y)
        column = self.items_tree.identify_column(event.x)

        # Only allow editing quantity_picked
        if column != "#5":  # quantity_picked
            return

        # Get current values
        values = self.items_tree.item(item_id, "values")
        material_name = values[1]
        quantity_needed = float(values[3])
        current_quantity = float(values[4])
        unit = values[5]

        # Create edit dialog
        dialog = tk.Toplevel(self)
        dialog.title(f"Update Picked Quantity: {material_name}")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()

        # Create form
        ttk.Label(dialog, text="Material:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        ttk.Label(dialog, text=material_name).grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)

        ttk.Label(dialog, text="Quantity Needed:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        ttk.Label(dialog, text=f"{quantity_needed} {unit}").grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)

        ttk.Label(dialog, text="Quantity Picked:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        quantity_var = tk.StringVar(value=str(current_quantity))
        quantity_spin = ttk.Spinbox(
            dialog,
            from_=0,
            to=quantity_needed * 2,  # Allow up to 2x needed for flexibility
            increment=0.1,
            textvariable=quantity_var
        )
        quantity_spin.grid(row=2, column=1, padx=10, pady=5, sticky=tk.W)

        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        def update_quantity():
            """Update the picked quantity."""
            try:
                quantity = float(quantity_var.get())
                if quantity < 0:
                    messagebox.showwarning("Invalid Quantity", "Quantity must be a positive number.", parent=dialog)
                    return

                # Update the quantity in the service
                result = self.picking_list_service.update_item_quantity(
                    self.picking_list_id,
                    int(item_id),
                    quantity
                )

                if result:
                    # Reload picking list
                    self.load_picking_list()

                    # Close dialog
                    dialog.destroy()

            except ValueError:
                messagebox.showwarning("Invalid Quantity", "Quantity must be a number.", parent=dialog)
            except Exception as e:
                self.logger.error(f"Error updating quantity: {e}")
                messagebox.showerror("Error", f"Failed to update quantity: {str(e)}", parent=dialog)

        ttk.Button(
            button_frame,
            text="Update",
            command=update_quantity
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

        # Set focus to quantity spinner
        quantity_spin.focus_set()

    def on_remove_item(self):
        """Handle remove item button click."""
        selected_id = self.items_tree.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select an item to remove.")
            return

        # Get item name
        values = self.items_tree.item(selected_id, "values")
        material_name = values[1]

        # Confirm removal
        if not messagebox.askyesno(
                "Confirm Remove",
                f"Are you sure you want to remove {material_name} from the picking list?"
        ):
            return

        try:
            # Remove item from picking list
            result = self.picking_list_service.remove_item_from_picking_list(
                self.picking_list_id,
                int(selected_id)
            )

            if result:
                # Reload picking list
                self.load_picking_list()

                # Show success message
                messagebox.showinfo("Success", f"Material '{material_name}' has been removed from the picking list.")

        except Exception as e:
            self.logger.error(f"Error removing item: {e}")
            messagebox.showerror("Remove Error", f"Failed to remove item: {str(e)}")

    def on_check_availability(self):
        """Handle check availability button click."""
        if not self.items_tree.get_children():
            messagebox.showinfo("No Items", "There are no items in this picking list to check.")
            return

        try:
            # Check availability for all items
            result = self.picking_list_service.check_items_availability(self.picking_list_id)

            if result:
                # Reload picking list to show updated availability
                self.load_picking_list()

                # Show summary
                available_count = sum(1 for item in result.values() if item.get("status") == "available")
                limited_count = sum(1 for item in result.values() if item.get("status") == "limited")
                unavailable_count = sum(1 for item in result.values() if item.get("status") == "unavailable")

                message = f"Material availability checked.\n\n"
                message += f"Available: {available_count}\n"
                message += f"Limited: {limited_count}\n"
                message += f"Not Available: {unavailable_count}"

                if unavailable_count > 0:
                    message += "\n\nSome materials are not available in sufficient quantity. Consider creating a purchase order."

                messagebox.showinfo("Availability Check", message)

        except Exception as e:
            self.logger.error(f"Error checking availability: {e}")
            messagebox.showerror("Check Error", f"Failed to check availability: {str(e)}")

    def on_start_picking(self):
        """Handle start picking button click."""
        try:
            # Update status to in_progress
            result = self.picking_list_service.update_picking_list_status(
                self.picking_list_id,
                "in_progress"
            )

            if result:
                # Update status variable and display
                self.status_var.set("in_progress")
                self.status_badge.set_text("In Progress", "in_progress")

                # Update action buttons
                self.update_action_buttons("in_progress")

                # Show success message
                messagebox.showinfo("Success", "Picking has started. Update item quantities as you pick them.")

        except Exception as e:
            self.logger.error(f"Error starting picking: {e}")
            messagebox.showerror("Error", f"Failed to start picking: {str(e)}")

    def on_complete_picking(self):
        """Handle complete picking button click."""
        # Check if all items are picked
        items = self.items_tree.get_children()
        pending_items = []

        for item_id in items:
            values = self.items_tree.item(item_id, "values")
            material_name = values[1]
            quantity_needed = float(values[3])
            quantity_picked = float(values[4])

            if quantity_picked < quantity_needed:
                pending_items.append(material_name)

        # Warn if there are pending items
        if pending_items and not messagebox.askyesno(
                "Incomplete Picking",
                f"There are {len(pending_items)} items not fully picked. Are you sure you want to complete the picking list?"
        ):
            return

        try:
            # Update status to completed
            result = self.picking_list_service.update_picking_list_status(
                self.picking_list_id,
                "completed"
            )

            if result:
                # Update status variable and display
                self.status_var.set("completed")
                self.status_badge.set_text("Completed", "completed")

                # Update action buttons
                self.update_action_buttons("completed")

                # Show success message
                messagebox.showinfo("Success", "Picking list has been marked as completed.")

                # Publish event
                publish("picking_list_completed", {
                    "picking_list_id": self.picking_list_id,
                    "project_id": self.project_id
                })

        except Exception as e:
            self.logger.error(f"Error completing picking: {e}")
            messagebox.showerror("Error", f"Failed to complete picking: {str(e)}")

    def on_cancel_picking(self):
        """Handle cancel picking list button click."""
        if not messagebox.askyesno(
                "Confirm Cancel",
                "Are you sure you want to cancel this picking list? This action cannot be undone."
        ):
            return

        try:
            # Update status to cancelled
            result = self.picking_list_service.update_picking_list_status(
                self.picking_list_id,
                "cancelled"
            )

            if result:
                # Update status variable and display
                self.status_var.set("cancelled")
                self.status_badge.set_text("Cancelled", "cancelled")

                # Update action buttons
                self.update_action_buttons("cancelled")

                # Show success message
                messagebox.showinfo("Success", "Picking list has been cancelled.")

                # Publish event
                publish("picking_list_cancelled", {
                    "picking_list_id": self.picking_list_id,
                    "project_id": self.project_id
                })

        except Exception as e:
            self.logger.error(f"Error cancelling picking: {e}")
            messagebox.showerror("Error", f"Failed to cancel picking: {str(e)}")

    def on_save(self):
        """Handle save button click."""
        try:
            # Collect data
            status = self.status_var.get().lower().replace(" ", "_")
            assigned_to = self.assigned_to_var.get()
            notes = self.notes_text.get("1.0", tk.END).strip()
            due_date = None

            if self.due_date_var.get():
                try:
                    due_date = datetime.datetime.strptime(self.due_date_var.get(), "%Y-%m-%d")
                except ValueError:
                    messagebox.showwarning("Invalid Date", "Due date must be in YYYY-MM-DD format.")
                    return

            # Save picking list
            result = self.picking_list_service.update_picking_list(
                self.picking_list_id,
                {
                    "status": status,
                    "assigned_to": assigned_to,
                    "notes": notes,
                    "due_date": due_date
                }
            )

            if result:
                # Show success message
                messagebox.showinfo("Success", "Picking list has been saved.")

                # Reload picking list
                self.load_picking_list()

        except Exception as e:
            self.logger.error(f"Error saving picking list: {e}")
            messagebox.showerror("Save Error", f"Failed to save picking list: {str(e)}")

    def on_back(self):
        """Handle back button click."""
        if self.project_id:
            self.parent.master.show_view(
                "project_details",
                view_data={"project_id": self.project_id}
            )
        else:
            self.parent.master.show_view("project_list")

    def on_print(self):
        """Handle print button click."""
        try:
            # Generate and print picking list
            result = self.picking_list_service.print_picking_list(self.picking_list_id)

            if result:
                messagebox.showinfo("Print", "Picking list has been sent to the printer.")

        except Exception as e:
            self.logger.error(f"Error printing picking list: {e}")
            messagebox.showerror("Print Error", f"Failed to print picking list: {str(e)}")

    def show_date_picker(self, date_var):
        """Show a date picker dialog.

        Args:
            date_var: The StringVar to update with selected date
        """
        current_date = datetime.date.today()

        # Try to parse current value
        if date_var.get():
            try:
                current_date = datetime.datetime.strptime(date_var.get(), "%Y-%m-%d").date()
            except ValueError:
                pass

        # Create calendar dialog
        dialog = tk.Toplevel(self)
        dialog.title("Select Date")
        dialog.geometry("300x280")
        dialog.transient(self)
        dialog.grab_set()

        # Calendar year and month selection
        cal_header = ttk.Frame(dialog)
        cal_header.pack(fill=tk.X, padx=10, pady=5)

        # Year selection
        ttk.Label(cal_header, text="Year:").pack(side=tk.LEFT, padx=(0, 5))
        year_var = tk.StringVar(value=str(current_date.year))
        year_spin = ttk.Spinbox(
            cal_header,
            from_=2000,
            to=2100,
            textvariable=year_var,
            width=5
        )
        year_spin.pack(side=tk.LEFT, padx=5)

        # Month selection
        ttk.Label(cal_header, text="Month:").pack(side=tk.LEFT, padx=(10, 5))
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        month_var = tk.StringVar(value=months[current_date.month - 1])
        month_combo = ttk.Combobox(
            cal_header,
            textvariable=month_var,
            values=months,
            width=10,
            state="readonly"
        )
        month_combo.pack(side=tk.LEFT, padx=5)

        # Calendar frame
        cal_frame = ttk.Frame(dialog, padding=5)
        cal_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Day of week headers
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            ttk.Label(
                cal_frame,
                text=day,
                width=3,
                anchor=tk.CENTER,
                font=("TkDefaultFont", 9, "bold")
            ).grid(row=0, column=i, padx=2, pady=2)

        # Day buttons
        day_buttons = []
        for row in range(6):
            for col in range(7):
                btn = ttk.Button(
                    cal_frame,
                    text="",
                    width=3,
                    style="Calendar.TButton"
                )
                btn.grid(row=row + 1, column=col, padx=2, pady=2)
                day_buttons.append(btn)

        # Selected date
        selected_date = None

        # Update calendar when month/year changes
        def update_calendar():
            """Update the calendar display based on selected month and year."""
            nonlocal selected_date

            # Get year and month
            year = int(year_var.get())
            month = months.index(month_var.get()) + 1

            # Get first day of month and number of days
            first_day = datetime.date(year, month, 1)
            if month == 12:
                last_day = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                last_day = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

            # Get day of week for first day (0 = Monday, 6 = Sunday)
            first_weekday = first_day.weekday()

            # Clear all buttons
            for btn in day_buttons:
                btn.configure(text="", state=tk.DISABLED)

            # Fill in days
            for day in range(1, last_day.day + 1):
                index = first_weekday + day - 1

                day_buttons[index].configure(
                    text=str(day),
                    state=tk.NORMAL,
                    command=lambda d=day: select_day(d)
                )

                # Highlight current date if it matches
                this_date = datetime.date(year, month, day)

                if this_date == current_date:
                    day_buttons[index].configure(style="Calendar.Accent.TButton")
                else:
                    day_buttons[index].configure(style="Calendar.TButton")

                # Highlight selected date
                if selected_date and this_date == selected_date:
                    day_buttons[index].configure(style="Calendar.Selected.TButton")

        # Select day
        def select_day(day):
            """Select a day in the calendar.

            Args:
                day: The day number to select
            """
            nonlocal selected_date

            # Get year and month
            year = int(year_var.get())
            month = months.index(month_var.get()) + 1

            # Create date object
            selected_date = datetime.date(year, month, day)

            # Update calendar to highlight selected date
            update_calendar()

        # Navigate to previous/next month
        def prev_month():
            """Go to previous month."""
            month_idx = months.index(month_var.get())
            year = int(year_var.get())

            if month_idx == 0:
                # December of previous year
                month_var.set(months[11])
                year_var.set(str(year - 1))
            else:
                # Previous month
                month_var.set(months[month_idx - 1])

            update_calendar()

        def next_month():
            """Go to next month."""
            month_idx = months.index(month_var.get())
            year = int(year_var.get())

            if month_idx == 11:
                # January of next year
                month_var.set(months[0])
                year_var.set(str(year + 1))
            else:
                # Next month
                month_var.set(months[month_idx + 1])

            update_calendar()

        # Navigation buttons
        nav_frame = ttk.Frame(dialog)
        nav_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(
            nav_frame,
            text="◀",
            width=3,
            command=prev_month
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            nav_frame,
            text="▶",
            width=3,
            command=next_month
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            nav_frame,
            text="Today",
            command=lambda: (
                year_var.set(str(datetime.date.today().year)),
                month_var.set(months[datetime.date.today().month - 1]),
                update_calendar()
            )
        ).pack(side=tk.LEFT, padx=5)

        # OK/Cancel buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def on_ok():
            """Handle OK button click."""
            if selected_date:
                date_var.set(selected_date.strftime("%Y-%m-%d"))
            dialog.destroy()

        ttk.Button(
            button_frame,
            text="OK",
            command=on_ok
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        # Bind month and year changes
        month_combo.bind("<<ComboboxSelected>>", lambda e: update_calendar())
        year_spin.bind("<Return>", lambda e: update_calendar())
        year_spin.bind("<FocusOut>", lambda e: update_calendar())

        # Define calendar button styles
        style = ttk.Style()
        style.configure("Calendar.TButton", width=3, padding=1)
        style.configure("Calendar.Accent.TButton", background=COLORS["primary_light"])
        style.configure("Calendar.Selected.TButton", background=COLORS["primary"])

        # Initialize calendar
        update_calendar()

    def refresh(self):
        """Refresh the view."""
        if self.picking_list_id:
            self.load_picking_list()