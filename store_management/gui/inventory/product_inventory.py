# gui/inventory/product_inventory.py
"""
Product inventory view implementation for managing products.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple, Type

import tkinter as tk
import tkinter.messagebox
from tkinter import ttk

from gui.base_view import BaseView
from services.interfaces.storage_service import IStorageService


class ProductInventoryView(BaseView):
    """View for managing product inventory."""

    def __init__(self, parent: tk.Widget, app: Any):
        """Initialize the Product Inventory View.

        Args:
            parent (tk.Widget): Parent widget
            app (Any): Application context providing access to services
        """
        super().__init__(parent, app)
        self._logger = logging.getLogger(self.__class__.__module__)
        self._logger.info("Initializing Product Inventory View")

        # Set up the layout
        self._setup_ui()

        # Load initial data
        self._load_data()

    def debug_model_registration(self):
        """
        Debug method to investigate model registration issues.
        """
        try:
            from database.models.base import Base

            # Get registered models
            registered_models = Base.debug_registered_models()

            # Log each registered model
            for model_name in registered_models:
                self._logger.info(f"Registered Model: {model_name}")

        except Exception as e:
            self._logger.error(f"Error debugging model registration: {str(e)}")

    def _setup_ui(self):
        """Set up the UI components."""
        # Main layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Toolbar
        self.rowconfigure(1, weight=1)  # Content

        # Create toolbar
        toolbar = ttk.Frame(self, padding=(5, 5, 5, 5))
        toolbar.grid(row=0, column=0, sticky="ew")

        ttk.Button(toolbar, text="New", command=self.on_new).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Edit", command=self.on_edit).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Delete", command=self.on_delete).pack(side=tk.LEFT, padx=5)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(toolbar, text="Refresh", command=self.on_refresh).pack(side=tk.LEFT, padx=5)

        # Search frame (right side of toolbar)
        search_frame = ttk.Frame(toolbar)
        search_frame.pack(side=tk.RIGHT)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        search_entry.bind("<Return>", self._on_search)

        ttk.Button(search_frame, text="Search", command=self._on_search).pack(side=tk.LEFT)

        # Create content area
        content = ttk.Frame(self, padding=5)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        # Create treeview for product inventory
        self.tree = ttk.Treeview(
            content,
            columns=("id", "name", "category", "price", "stock", "location"),
            show="headings",
            selectmode="browse"
        )

        # Configure column headings
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("category", text="Category")
        self.tree.heading("price", text="Price")
        self.tree.heading("stock", text="In Stock")
        self.tree.heading("location", text="Location")

        # Configure column widths
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("name", width=200)
        self.tree.column("category", width=100)
        self.tree.column("price", width=80, anchor="e")
        self.tree.column("stock", width=80, anchor="center")
        self.tree.column("location", width=100)

        # Add scrollbars
        vsb = ttk.Scrollbar(content, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(content, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout for treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Bind events
        self.tree.bind("<Double-1>", self.on_edit)

    def _load_data(self):
        """Load product inventory data."""
        try:
            storage_service = self.get_service(IStorageService)

            # Get products and storage locations
            products = storage_service.get_all_storage_locations()

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Add products to the treeview
            for product in products:
                # Assuming product contains these fields
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        product.get("id", ""),
                        product.get("name", ""),
                        product.get("category", ""),
                        f"${product.get('price', 0):.2f}",
                        product.get("quantity_available", 0),
                        product.get("storage_location", "")
                    )
                )

            self._logger.info(f"Loaded {len(products)} products")

        except Exception as e:
            self._logger.error(f"Error loading product inventory: {str(e)}")
            self.show_error("Data Load Error", f"Failed to load product inventory: {str(e)}")

    def _on_search(self, event=None):
        """Handle search functionality.

        Args:
            event: The event that triggered the search (optional)
        """
        search_text = self.search_var.get().strip()
        if not search_text:
            # If search is empty, reload all data
            self._load_data()
            return

        try:
            storage_service = self.get_service(IStorageService)

            # Search products
            # Note: Assuming the service has search functionality
            products = storage_service.search_products(search_text)

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Add products to the treeview
            for product in products:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        product.get("id", ""),
                        product.get("name", ""),
                        product.get("category", ""),
                        f"${product.get('price', 0):.2f}",
                        product.get("quantity_available", 0),
                        product.get("storage_location", "")
                    )
                )

            self._logger.info(f"Found {len(products)} matching products")

        except Exception as e:
            self._logger.error(f"Error searching product inventory: {str(e)}")
            self.show_error("Search Error", f"Failed to search product inventory: {str(e)}")

    def on_new(self):
        """Handle creating a new product."""
        self._logger.info("Create new product")
        # This would be implemented to open a dialog for creating a new product
        self.show_message("Product creation not implemented yet", message_type="info")

    def on_edit(self, event=None):
        """Handle editing an existing product."""
        selection = self.tree.selection()
        if not selection:
            self.show_message("Please select a product to edit", message_type="info")
            return

        # Get selected item ID
        item_id = self.tree.item(selection[0], "values")[0]
        self._logger.info(f"Edit product ID: {item_id}")

        # This would be implemented to open a dialog for editing a product
        self.show_message("Product editing not implemented yet", message_type="info")

    def on_delete(self):
        """Handle deleting a product."""
        selection = self.tree.selection()
        if not selection:
            self.show_message("Please select a product to delete", message_type="info")
            return

        # Get selected item ID and name
        values = self.tree.item(selection[0], "values")
        item_id = values[0]
        item_name = values[1]

        # Confirm deletion
        confirm = self.show_message(
            f"Are you sure you want to delete the product '{item_name}'?",
            message_type="question"
        )

        if confirm:
            self._logger.info(f"Delete product ID: {item_id}, Name: {item_name}")
            # This would be implemented to delete the product
            self.show_message("Product deletion not implemented yet", message_type="info")

    def on_refresh(self):
        """Refresh the inventory view."""
        self._load_data()