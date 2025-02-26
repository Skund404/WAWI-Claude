# gui/inventory/hardware_inventory.py
"""
View for managing hardware inventory in a leatherworking store management system.
Provides functionality to view, add, edit, and delete hardware items used in leatherworking.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional, Tuple, Type

from gui.base_view import BaseView
from services.interfaces.material_service import IMaterialService, MaterialType

# Configure logger
logger = logging.getLogger(__name__)


class HardwareInventoryView(BaseView):
    """
    View for displaying and managing hardware inventory.

    Provides a tabular interface for viewing hardware items (buckles, clasps, rivets, etc.),
    with functionality to add, edit, and delete entries. Includes search and filter capabilities.
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the Hardware Inventory View.

        Args:
            parent (tk.Widget): Parent widget
            app (Any): Application context providing access to services
        """
        super().__init__(parent, app)

        self._material_service = None
        self._selected_hardware_id = None

        self._search_var = tk.StringVar()
        self._hardware_type_filter_var = tk.StringVar(value="All")

        # Initialize UI components
        self._create_ui()
        self._load_data()

        logger.info("Hardware inventory view initialized")

    def get_service(self, service_type: Type) -> Any:
        """
        Retrieve a service from the dependency container.

        Args:
            service_type (Type): Service interface to retrieve

        Returns:
            Any: Service implementation instance
        """
        try:
            return self._app.get_service(service_type)
        except Exception as e:
            logger.error(f"Failed to get service {service_type.__name__}: {str(e)}")
            raise

    @property
    def material_service(self) -> IMaterialService:
        """
        Lazy-loaded material service property.

        Returns:
            IMaterialService: Material service instance
        """
        if self._material_service is None:
            self._material_service = self.get_service(IMaterialService)
        return self._material_service

    def _create_ui(self) -> None:
        """Create and configure UI components."""
        # Configure frame layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Toolbar frame
        toolbar_frame = ttk.Frame(self, padding="5")
        toolbar_frame.grid(row=0, column=0, sticky="ew")

        # Hardware type filter
        ttk.Label(toolbar_frame, text="Hardware Type:").pack(side=tk.LEFT, padx=(0, 5))
        hardware_types = ["All", "Buckle", "Clasp", "Rivet", "Snap", "D-Ring", "O-Ring",
                          "Zipper", "Button", "Magnetic Closure", "Other"]
        type_filter = ttk.Combobox(toolbar_frame, textvariable=self._hardware_type_filter_var,
                                   values=hardware_types, width=15, state="readonly")
        type_filter.pack(side=tk.LEFT, padx=(0, 10))
        type_filter.bind("<<ComboboxSelected>>", lambda e: self._load_data())

        # Search bar
        ttk.Label(toolbar_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        search_entry = ttk.Entry(toolbar_frame, textvariable=self._search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        search_entry.bind("<Return>", self._on_search)

        ttk.Button(toolbar_frame, text="Search", command=self._on_search).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="Reset", command=self._reset_search).pack(side=tk.LEFT, padx=(0, 10))

        # Action buttons
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        ttk.Button(toolbar_frame, text="Add Hardware", command=self._add_hardware).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="Edit", command=self._edit_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="Delete", command=self._delete_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="Refresh", command=self._load_data).pack(side=tk.LEFT, padx=(0, 5))

        # Treeview for data display
        self.tree = ttk.Treeview(self, columns=(
            "id", "name", "hardware_type", "material", "finish", "size",
            "quantity", "price", "supplier", "location"
        ), show="headings")

        # Configure column headings
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("hardware_type", text="Type")
        self.tree.heading("material", text="Material")
        self.tree.heading("finish", text="Finish")
        self.tree.heading("size", text="Size")
        self.tree.heading("quantity", text="Quantity")
        self.tree.heading("price", text="Price ($)")
        self.tree.heading("supplier", text="Supplier")
        self.tree.heading("location", text="Storage Location")

        # Configure column widths
        self.tree.column("id", width=50, stretch=False)
        self.tree.column("name", width=150)
        self.tree.column("hardware_type", width=100)
        self.tree.column("material", width=100)
        self.tree.column("finish", width=100)
        self.tree.column("size", width=80)
        self.tree.column("quantity", width=80, anchor=tk.E)
        self.tree.column("price", width=80, anchor=tk.E)
        self.tree.column("supplier", width=120)
        self.tree.column("location", width=120)

        # Setup scrollbars
        y_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        x_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        # Grid layout
        self.tree.grid(row=1, column=0, sticky="nsew")
        y_scrollbar.grid(row=1, column=1, sticky="ns")
        x_scrollbar.grid(row=2, column=0, sticky="ew")

        # Bind events
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=2, sticky="ew")

        self.status_var.set("Ready")

    def _load_data(self) -> None:
        """
        Load hardware data from the material service and populate the treeview.
        """
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            # Get hardware materials from service
            # Using MaterialType.HARDWARE to filter only hardware items
            hardware_items = self.material_service.list_materials(material_type=MaterialType.HARDWARE)

            if not hardware_items:
                self.status_var.set("No hardware items found")
                logger.info("No hardware items found")
                return

            # Apply type filter if selected
            type_filter = self._hardware_type_filter_var.get()
            if type_filter != "All":
                hardware_items = [item for item in hardware_items
                                  if item.get("hardware_type", "") == type_filter]

            # Populate treeview
            for item in hardware_items:
                self.tree.insert("", tk.END, values=(
                    item.get("id", ""),
                    item.get("name", ""),
                    item.get("hardware_type", ""),
                    item.get("material", ""),
                    item.get("finish", ""),
                    item.get("size", ""),
                    item.get("quantity", 0),
                    f"${item.get('price_per_unit', 0):.2f}",
                    item.get("supplier_name", ""),
                    item.get("storage_location", "")
                ))

            # Update status
            self.status_var.set(f"Loaded {len(hardware_items)} hardware items")
            logger.info(f"Loaded {len(hardware_items)} hardware items")

        except Exception as e:
            error_message = f"Error loading hardware items: {str(e)}"
            self.show_error("Data Loading Error", error_message)
            logger.error(error_message, exc_info=True)
            self.status_var.set("Error loading data")

    def _on_search(self, event=None) -> None:
        """
        Handle search functionality.

        Args:
            event: Event triggering the search (optional)
        """
        search_term = self._search_var.get().strip().lower()

        if not search_term:
            self._load_data()
            return

        try:
            # Get all hardware items and filter locally
            hardware_items = self.material_service.list_materials(material_type=MaterialType.HARDWARE)

            # Apply type filter if selected
            type_filter = self._hardware_type_filter_var.get()
            if type_filter != "All":
                hardware_items = [item for item in hardware_items
                                  if item.get("hardware_type", "") == type_filter]

            # Filter items based on search term
            filtered_items = []
            for item in hardware_items:
                # Check if the search term appears in any of the key fields
                for field in ["name", "hardware_type", "material", "finish", "supplier_name"]:
                    value = str(item.get(field, "")).lower()
                    if search_term in value:
                        filtered_items.append(item)
                        break

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Populate treeview with filtered items
            for item in filtered_items:
                self.tree.insert("", tk.END, values=(
                    item.get("id", ""),
                    item.get("name", ""),
                    item.get("hardware_type", ""),
                    item.get("material", ""),
                    item.get("finish", ""),
                    item.get("size", ""),
                    item.get("quantity", 0),
                    f"${item.get('price_per_unit', 0):.2f}",
                    item.get("supplier_name", ""),
                    item.get("storage_location", "")
                ))

            # Update status
            self.status_var.set(f"Found {len(filtered_items)} hardware items matching '{search_term}'")

        except Exception as e:
            error_message = f"Error searching hardware items: {str(e)}"
            self.show_error("Search Error", error_message)
            logger.error(error_message, exc_info=True)
            self.status_var.set("Error during search")

    def _reset_search(self) -> None:
        """Reset search field and hardware type filter."""
        self._search_var.set("")
        self._hardware_type_filter_var.set("All")
        self._load_data()

    def _on_select(self, event=None) -> None:
        """
        Handle selection of an item in the treeview.

        Args:
            event: Selection event
        """
        selected_items = self.tree.selection()
        if not selected_items:
            self._selected_hardware_id = None
            return

        # Get the first selected item
        item = selected_items[0]
        values = self.tree.item(item, "values")

        if values:
            self._selected_hardware_id = values[0]  # ID is the first column

    def _on_double_click(self, event=None) -> None:
        """
        Handle double-click on a treeview item.

        Args:
            event: Double-click event
        """
        self._edit_selected()

    def _add_hardware(self) -> None:
        """
        Show dialog to add a new hardware item.
        """
        # In a real implementation, this would open a dialog window
        # For now, we'll just show a placeholder message
        self.show_info("Add Hardware", "Hardware entry dialog would open here.")
        logger.info("Add hardware functionality called")

    def _edit_selected(self) -> None:
        """
        Show dialog to edit the selected hardware item.
        """
        if not self._selected_hardware_id:
            self.show_warning("Warning", "Please select a hardware item to edit.")
            return

        # In a real implementation, this would open a dialog window
        # For now, we'll just show a placeholder message
        self.show_info("Edit Hardware", f"Hardware editing dialog would open here for ID: {self._selected_hardware_id}")
        logger.info(f"Edit hardware called for ID: {self._selected_hardware_id}")

    def _delete_selected(self) -> None:
        """
        Delete the selected hardware item after confirmation.
        """
        if not self._selected_hardware_id:
            self.show_warning("Warning", "Please select a hardware item to delete.")
            return

        # Confirm deletion
        if not messagebox.askyesno("Confirm Deletion",
                                   "Are you sure you want to delete this hardware item?\n"
                                   "This action cannot be undone."):
            return

        try:
            # Delete hardware through service
            result = self.material_service.delete_material(self._selected_hardware_id)

            if result:
                self.show_info("Success", "Hardware item deleted successfully!")
                self._selected_hardware_id = None
                self._load_data()  # Refresh the view
            else:
                self.show_error("Error", "Failed to delete hardware item.")

        except Exception as e:
            error_message = f"Error deleting hardware item: {str(e)}"
            self.show_error("Delete Error", error_message)
            logger.error(error_message, exc_info=True)