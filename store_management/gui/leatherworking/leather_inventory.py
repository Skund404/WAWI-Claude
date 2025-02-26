# gui/leatherworking/leather_inventory.py
"""
LeatherInventoryView module for displaying and managing leather inventory.
Provides a GUI interface for viewing, adding, updating, and tracking leather materials.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import logging
from typing import Any, Dict, List, Optional, Tuple

from gui.base_view import BaseView
from gui.leatherworking.leather_dialog import LeatherDetailsDialog
from services.interfaces.material_service import IMaterialService, MaterialType
from services.interfaces.project_service import IProjectService
from di.core import inject

# Configure logger
logger = logging.getLogger(__name__)


class LeatherInventoryView(BaseView):
    """View for managing and displaying leather inventory."""

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the Leather Inventory View.

        Args:
            parent (tk.Widget): Parent widget
            app (Any): Application context
        """
        super().__init__(parent, app)
        self.title = "Leather Inventory"

        # Get services
        self.material_service = self.get_service(IMaterialService)
        self.project_service = self.get_service(IProjectService)

        # UI components
        self.tree = None
        self.search_var = None
        self.filter_var = None
        self.status_label = None

        # Setup UI
        self.setup_ui()

        # Load initial data
        self.load_data()

        logger.info("LeatherInventoryView initialized")

    def setup_ui(self) -> None:
        """Set up the user interface components."""
        # Implementation of the required abstract method
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create and arrange UI widgets."""
        # Top frame for controls
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Search field
        ttk.Label(control_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(control_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        search_entry.bind("<Return>", lambda e: self._search_leather())

        ttk.Button(control_frame, text="Search", command=self._search_leather).pack(side=tk.LEFT, padx=(0, 10))

        # Filter by leather type
        ttk.Label(control_frame, text="Filter Type:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_var = tk.StringVar(value="All")
        leather_types = ["All"] + [t.name for t in MaterialType if t != MaterialType.LEATHER]
        type_combo = ttk.Combobox(control_frame, textvariable=self.filter_var, values=leather_types, width=15)
        type_combo.pack(side=tk.LEFT, padx=(0, 10))
        type_combo.bind("<<ComboboxSelected>>", lambda e: self.load_data())

        # Buttons
        ttk.Button(control_frame, text="Add Leather", command=self._add_leather).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Edit", command=self._edit_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Delete", command=self._delete_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Refresh", command=self.load_data).pack(side=tk.LEFT, padx=2)

        # Create treeview for leather inventory
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("id", "name", "type", "color", "thickness", "size", "quantity", "cost", "supplier")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        # Configure columns
        self.tree.column("id", width=50, minwidth=50)
        self.tree.column("name", width=150, minwidth=100)
        self.tree.column("type", width=100, minwidth=80)
        self.tree.column("color", width=100, minwidth=80)
        self.tree.column("thickness", width=80, minwidth=60)
        self.tree.column("size", width=80, minwidth=60)
        self.tree.column("quantity", width=80, minwidth=60)
        self.tree.column("cost", width=80, minwidth=60)
        self.tree.column("supplier", width=120, minwidth=100)

        # Configure headings
        for col in columns:
            self.tree.heading(col, text=col.capitalize(), command=lambda _col=col: self._sort_by_column(_col))

        # Add scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Position elements
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind events
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Status bar
        self.status_label = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def load_data(self) -> None:
        """Load leather inventory data from the database."""
        try:
            # Clear existing data
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Get filter value
            filter_type = self.filter_var.get() if hasattr(self, 'filter_var') and self.filter_var else "All"

            # Get data from service
            if filter_type == "All":
                materials = self.material_service.list_materials(MaterialType.LEATHER)
            else:
                try:
                    material_type = MaterialType[filter_type]
                    materials = self.material_service.list_materials(material_type)
                except KeyError:
                    materials = self.material_service.list_materials(MaterialType.LEATHER)

            # Insert data into treeview
            for material in materials:
                values = (
                    material.get('id', ''),
                    material.get('name', ''),
                    material.get('material_type', ''),
                    material.get('color', ''),
                    material.get('thickness', ''),
                    material.get('size', ''),
                    material.get('quantity', 0),
                    f"${material.get('cost_per_unit', 0):.2f}",
                    material.get('supplier_code', '')
                )
                self.tree.insert('', 'end', values=values)

            # Update status
            count = len(materials)
            self.status_label.config(text=f"Loaded {count} leather {'item' if count == 1 else 'items'}")

            logger.info(f"Loaded {count} leather items")

        except Exception as e:
            logger.error(f"Error loading leather inventory: {str(e)}")
            messagebox.showerror("Load Error", "Could not load leather inventory")
            self.status_label.config(text="Error loading data")

    def _search_leather(self) -> None:
        """Search for leather items based on the search term."""
        search_term = self.search_var.get().strip()
        if not search_term:
            self.load_data()
            return

        try:
            # Search using service
            results = self.material_service.search_materials(search_term)

            # Filter for leather only
            leather_results = [item for item in results if item.get('material_type') == MaterialType.LEATHER.value]

            # Clear existing data
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Insert search results
            for material in leather_results:
                values = (
                    material.get('id', ''),
                    material.get('name', ''),
                    material.get('material_type', ''),
                    material.get('color', ''),
                    material.get('thickness', ''),
                    material.get('size', ''),
                    material.get('quantity', 0),
                    f"${material.get('cost_per_unit', 0):.2f}",
                    material.get('supplier_code', '')
                )
                self.tree.insert('', 'end', values=values)

            # Update status
            count = len(leather_results)
            self.status_label.config(text=f"Found {count} {'item' if count == 1 else 'items'} matching '{search_term}'")

            logger.info(f"Found {count} items matching '{search_term}'")

        except Exception as e:
            logger.error(f"Error searching leather: {str(e)}")
            messagebox.showerror("Search Error", f"An error occurred during search: {str(e)}")

    def _sort_by_column(self, column: str) -> None:
        """
        Sort treeview data by the specified column.

        Args:
            column: Column name to sort by
        """
        # Get all items
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]

        # Check if column is numeric
        numeric_columns = {"id", "thickness", "quantity", "size", "cost"}
        if column in numeric_columns:
            # Convert to float for sorting, handling non-numeric values
            items = [(float(value.replace('$', '')) if value and value.replace('$', '').replace('.',
                                                                                                '').isdigit() else 0,
                      item)
                     for value, item in items]

        # Sort items
        items.sort()

        # Rearrange items in treeview
        for index, (_, item) in enumerate(items):
            self.tree.move(item, '', index)

    def _add_leather(self) -> None:
        """Show dialog to add a new leather item."""
        dialog = LeatherDetailsDialog(self, "Add Leather", None)
        self.wait_window(dialog)

        # Refresh data after adding
        self.load_data()

    def _edit_selected(self) -> None:
        """Edit the selected leather item."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select a leather item to edit.")
            return

        # Get the selected item's ID
        item_id = self.tree.item(selected_items[0], 'values')[0]

        try:
            # Get the material data
            material_data = self.material_service.get_material(item_id)

            # Show edit dialog
            dialog = LeatherDetailsDialog(self, "Edit Leather", material_data)
            self.wait_window(dialog)

            # Refresh data after editing
            self.load_data()

        except Exception as e:
            logger.error(f"Error editing leather item: {str(e)}")
            messagebox.showerror("Edit Error", f"Could not edit leather item: {str(e)}")

    def _delete_selected(self) -> None:
        """Delete the selected leather item."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select a leather item to delete.")
            return

        # Get the selected item's ID
        item_id = self.tree.item(selected_items[0], 'values')[0]
        item_name = self.tree.item(selected_items[0], 'values')[1]

        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete '{item_name}'?",
            icon=messagebox.WARNING
        )

        if confirm:
            try:
                # Delete the item
                self.material_service.delete_material(item_id)

                # Refresh data
                self.load_data()

                logger.info(f"Deleted leather item: {item_id} - {item_name}")

            except Exception as e:
                logger.error(f"Error deleting leather item: {str(e)}")
                messagebox.showerror("Delete Error", f"Could not delete leather item: {str(e)}")

    def _on_double_click(self, event: tk.Event) -> None:
        """Handle double-click on an item."""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            self._edit_selected()

    def _on_select(self, event: tk.Event) -> None:
        """Handle selection of an item."""
        # Could be used to update details panel or enable/disable buttons
        pass


class DummyApp:
    """Dummy app class for testing the LeatherInventoryView."""

    def get_service(self, service_type):
        """Dummy implementation of get_service."""
        return None


# For standalone testing
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Leather Inventory")
    root.geometry("800x600")
    app = DummyApp()
    view = LeatherInventoryView(root, app)
    view.pack(fill=tk.BOTH, expand=True)
    root.mainloop()