# gui/inventory/product_inventory.py
"""
View for managing finished product inventory in a leatherworking store management system.
Provides functionality to view, add, edit, and delete finished leatherwork products ready for sale.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional, Tuple, Type

from gui.base_view import BaseView
from services.interfaces.storage_service import IStorageService

# Configure logger
logger = logging.getLogger(__name__)


class ProductInventoryView(BaseView):
    """
    View for displaying and managing finished product inventory.

    Provides a tabular interface for viewing finished leatherwork products (wallets, bags, etc.),
    with functionality to add, edit, and delete entries. Includes search and filter capabilities.
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the Product Inventory View.

        Args:
            parent (tk.Widget): Parent widget
            app (Any): Application context providing access to services
        """
        super().__init__(parent, app)

        self._storage_service = None
        self._selected_product_id = None

        self._search_var = tk.StringVar()
        self._product_type_filter_var = tk.StringVar(value="All")

        # Initialize UI components
        self._create_ui()
        self._load_data()

        logger.info("Product inventory view initialized")

    def get_service(self, service_type: Type) -> Any:
        """Get a service from the application.

        Args:
            service_type (Type): The service interface type to retrieve

        Returns:
            Any: The service instance
        """
        return self.app.get_service(service_type)

    @property
    def storage_service(self) -> IStorageService:
        """
        Lazy-loaded storage service property.

        Returns:
            IStorageService: Storage service instance
        """
        if self._storage_service is None:
            self._storage_service = self.get_service(IStorageService)
        return self._storage_service

    def _create_ui(self) -> None:
        """Create and configure UI components."""
        # Configure frame layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Toolbar frame
        toolbar_frame = ttk.Frame(self, padding="5")
        toolbar_frame.grid(row=0, column=0, sticky="ew")

        # Product type filter
        ttk.Label(toolbar_frame, text="Product Type:").pack(side=tk.LEFT, padx=(0, 5))
        product_types = ["All", "Wallet", "Bag", "Belt", "Watch Strap", "Notebook Cover",
                         "Phone Case", "Key Holder", "Card Holder", "Custom", "Other"]
        type_filter = ttk.Combobox(toolbar_frame, textvariable=self._product_type_filter_var,
                                   values=product_types, width=15, state="readonly")
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
        ttk.Button(toolbar_frame, text="Add Product", command=self._add_product).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="Edit", command=self._edit_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="Delete", command=self._delete_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="Refresh", command=self._load_data).pack(side=tk.LEFT, padx=(0, 5))

        # Treeview for data display
        self.tree = ttk.Treeview(self, columns=(
            "id", "name", "product_type", "price", "quantity", "leather_type",
            "color", "creation_date", "description", "location"
        ), show="headings")

        # Configure column headings
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Product Name")
        self.tree.heading("product_type", text="Type")
        self.tree.heading("price", text="Price ($)")
        self.tree.heading("quantity", text="Quantity")
        self.tree.heading("leather_type", text="Leather Type")
        self.tree.heading("color", text="Color")
        self.tree.heading("creation_date", text="Created")
        self.tree.heading("description", text="Description")
        self.tree.heading("location", text="Storage Location")

        # Configure column widths
        self.tree.column("id", width=50, stretch=False)
        self.tree.column("name", width=150)
        self.tree.column("product_type", width=100)
        self.tree.column("price", width=80, anchor=tk.E)
        self.tree.column("quantity", width=80, anchor=tk.E)
        self.tree.column("leather_type", width=100)
        self.tree.column("color", width=80)
        self.tree.column("creation_date", width=100)
        self.tree.column("description", width=200)
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
        Load product data from the storage service and populate the treeview.
        """
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            # Get products from service
            # In a real implementation, this would use a dedicated product service
            # For now, we'll use the storage service as a placeholder
            products = self.storage_service.get_all_storage_locations()

            if not products:
                self.status_var.set("No products found")
                logger.info("No products found")
                return

            # Apply type filter if selected
            type_filter = self._product_type_filter_var.get()
            if type_filter != "All":
                products = [product for product in products
                            if product.get("product_type", "") == type_filter]

            # Populate treeview
            for product in products:
                self.tree.insert("", tk.END, values=(
                    product.get("id", ""),
                    product.get("name", ""),
                    product.get("product_type", ""),
                    f"${product.get('price', 0):.2f}",
                    product.get("quantity", 0),
                    product.get("leather_type", ""),
                    product.get("color", ""),
                    product.get("creation_date", ""),
                    product.get("description", ""),
                    product.get("location", "")
                ))

            # Update status
            self.status_var.set(f"Loaded {len(products)} products")
            logger.info(f"Loaded {len(products)} products")

        except Exception as e:
            error_message = f"Error loading products: {str(e)}"
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
            # Get all products and filter locally
            products = self.storage_service.get_all_storage_locations()

            # Apply type filter if selected
            type_filter = self._product_type_filter_var.get()
            if type_filter != "All":
                products = [product for product in products
                            if product.get("product_type", "") == type_filter]

            # Filter products based on search term
            filtered_products = []
            for product in products:
                # Check if the search term appears in any of the key fields
                for field in ["name", "product_type", "leather_type", "color", "description"]:
                    value = str(product.get(field, "")).lower()
                    if search_term in value:
                        filtered_products.append(product)
                        break

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Populate treeview with filtered products
            for product in filtered_products:
                self.tree.insert("", tk.END, values=(
                    product.get("id", ""),
                    product.get("name", ""),
                    product.get("product_type", ""),
                    f"${product.get('price', 0):.2f}",
                    product.get("quantity", 0),
                    product.get("leather_type", ""),
                    product.get("color", ""),
                    product.get("creation_date", ""),
                    product.get("description", ""),
                    product.get("location", "")
                ))

            # Update status
            self.status_var.set(f"Found {len(filtered_products)} products matching '{search_term}'")

        except Exception as e:
            error_message = f"Error searching products: {str(e)}"
            self.show_error("Search Error", error_message)
            logger.error(error_message, exc_info=True)
            self.status_var.set("Error during search")

    def _reset_search(self) -> None:
        """Reset search field and product type filter."""
        self._search_var.set("")
        self._product_type_filter_var.set("All")
        self._load_data()

    def _on_select(self, event=None) -> None:
        """
        Handle selection of an item in the treeview.

        Args:
            event: Selection event
        """
        selected_items = self.tree.selection()
        if not selected_items:
            self._selected_product_id = None
            return

        # Get the first selected item
        item = selected_items[0]
        values = self.tree.item(item, "values")

        if values:
            self._selected_product_id = values[0]  # ID is the first column

    def _on_double_click(self, event=None) -> None:
        """
        Handle double-click on a treeview item.

        Args:
            event: Double-click event
        """
        self._edit_selected()

    def _add_product(self) -> None:
        """
        Show dialog to add a new product.
        """
        # In a real implementation, this would open a dialog window
        # For now, we'll just show a placeholder message
        self.show_info("Add Product", "Product entry dialog would open here.")
        logger.info("Add product functionality called")

    def _edit_selected(self) -> None:
        """
        Show dialog to edit the selected product.
        """
        if not self._selected_product_id:
            self.show_warning("Warning", "Please select a product to edit.")
            return

        # In a real implementation, this would open a dialog window
        # For now, we'll just show a placeholder message
        self.show_info("Edit Product", f"Product editing dialog would open here for ID: {self._selected_product_id}")
        logger.info(f"Edit product called for ID: {self._selected_product_id}")

    def _delete_selected(self) -> None:
        """
        Delete the selected product after confirmation.
        """
        if not self._selected_product_id:
            self.show_warning("Warning", "Please select a product to delete.")
            return

        # Confirm deletion
        if not messagebox.askyesno("Confirm Deletion",
                                   "Are you sure you want to delete this product?\n"
                                   "This action cannot be undone."):
            return

        try:
            # Delete product through service
            result = self.storage_service.delete_storage_location(self._selected_product_id)

            if result:
                self.show_info("Success", "Product deleted successfully!")
                self._selected_product_id = None
                self._load_data()  # Refresh the view
            else:
                self.show_error("Error", "Failed to delete product.")

        except Exception as e:
            error_message = f"Error deleting product: {str(e)}"
            self.show_error("Delete Error", error_message)
            logger.error(error_message, exc_info=True)