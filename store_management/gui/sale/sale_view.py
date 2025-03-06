# gui/sale/sale_view.py
"""
Sale view implementation for managing sales.
"""
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

import tkinter as tk
import tkinter.messagebox
from tkinter import ttk

from gui.base_view import BaseView
from services.interfaces.sale_service import ISaleService, SaleStatus, PaymentStatus  # Import PaymentStatus


class SearchDialog(tk.Toplevel):
    """Dialog for searching sales."""

    def __init__(self, parent: tk.Widget, columns: List[str], search_callback: Callable):
        """Initialize the search dialog.

        Args:
            parent: Parent widget
            columns: List of column names to search in
            search_callback: Function to call with search parameters
        """
        super().__init__(parent)
        self.title("Search Sales")  # Changed title
        self.geometry("400x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.columns = columns
        self.search_callback = search_callback

        # Create widgets
        self._create_widgets()

        # Center the dialog
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Set focus to search entry
        self.search_entry.focus_set()

        # Bind Enter key to search
        self.bind("<Return>", self._on_search)

    def _create_widgets(self):
        """Create dialog widgets."""
        # Main frame
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Column selection
        ttk.Label(frame, text="Search in:").grid(row=0, column=0, sticky=tk.W, pady=5)

        self.column_var = tk.StringVar(value=self.columns[0] if self.columns else "")
        column_combo = ttk.Combobox(
            frame,
            textvariable=self.column_var,
            values=self.columns,
            state="readonly"
        )
        column_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)

        # Search text
        ttk.Label(frame, text="Search for:").grid(row=1, column=0, sticky=tk.W, pady=5)

        self.search_entry = ttk.Entry(frame, width=30)
        self.search_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)

        # Exact match checkbox
        self.exact_match_var = tk.BooleanVar(value=False)
        exact_match_check = ttk.Checkbutton(
            frame,
            text="Exact match",
            variable=self.exact_match_var
        )
        exact_match_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(
            button_frame,
            text="Search",
            command=self._on_search
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy
        ).pack(side=tk.LEFT, padx=5)

        # Configure grid
        frame.columnconfigure(1, weight=1)

    def _on_search(self, event=None):
        """Handle search button click or Enter key.

        Args:
            event: Event that triggered the search
        """
        column = self.column_var.get()
        search_text = self.search_entry.get()
        exact_match = self.exact_match_var.get()

        if not search_text:
            tk.messagebox.showwarning(
                "Empty Search",
                "Please enter search text."
            )
            return

        self.search_callback(column, search_text, exact_match)
        self.destroy()


class SaleView(BaseView):
    """View for managing sales."""

    def __init__(self, parent: tk.Widget, app: Any):
        """Initialize the sale view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)
        self.logger = logging.getLogger("gui.sale.sale_view")
        self.logger.info("Initializing Sale View")

        self._selected_sale_id = None  # Changed _selected_order_id to _selected_sale_id

        self._setup_ui()
        self._load_sales()  # Changed _load_orders to _load_sales

    def _setup_ui(self):
        """Set up the user interface components."""
        # Create main layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Toolbar
        self.rowconfigure(1, weight=1)  # Content

        # Create toolbar
        toolbar = ttk.Frame(self, padding=(5, 5, 5, 5))
        toolbar.grid(row=0, column=0, sticky="ew")
        self._create_toolbar(toolbar)

        # Create content frame with split panes
        content = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        content.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Sale list frame
        sales_frame = ttk.Frame(content, padding=5)  # Changed orders_frame to sales_frame
        content.add(sales_frame, weight=1)

        # Sale details frame
        details_frame = ttk.Frame(content, padding=5)
        content.add(details_frame, weight=1)

        # Setup sale list treeview
        sales_frame.columnconfigure(0, weight=1)  # Changed orders_frame to sales_frame
        sales_frame.rowconfigure(0, weight=0)  # Label
        sales_frame.rowconfigure(1, weight=1)  # Treeview

        ttk.Label(sales_frame, text="Sales", font=("TkDefaultFont", 12, "bold")).grid(  # Changed orders_frame to sales_frame
            row=0, column=0, sticky="w", padx=5, pady=(0, 5)
        )

        # Create sales treeview
        self.sales_tree = ttk.Treeview(  # Changed orders_tree to sales_tree
            sales_frame,  # Changed orders_frame to sales_frame
            columns=("id", "reference", "date", "status", "amount"),
            show="headings",
            selectmode="browse"
        )
        self.sales_tree.grid(row=1, column=0, sticky="nsew")  # Changed orders_tree to sales_tree

        # Configure treeview columns
        self.sales_tree.heading("id", text="ID")  # Changed orders_tree to sales_tree
        self.sales_tree.heading("reference", text="Reference")  # Changed orders_tree to sales_tree
        self.sales_tree.heading("date", text="Date")  # Changed orders_tree to sales_tree
        self.sales_tree.heading("status", text="Status")  # Changed orders_tree to sales_tree
        self.sales_tree.heading("amount", text="Amount")  # Changed orders_tree to sales_tree

        self.sales_tree.column("id", width=50, anchor="center")  # Changed orders_tree to sales_tree
        self.sales_tree.column("reference", width=100)  # Changed orders_tree to sales_tree
        self.sales_tree.column("date", width=100, anchor="center")  # Changed orders_tree to sales_tree
        self.sales_tree.column("status", width=100, anchor="center")  # Changed orders_tree to sales_tree
        self.sales_tree.column("amount", width=100, anchor="e")  # Changed orders_tree to sales_tree

        # Add scrollbar to treeview
        sales_scrollbar = ttk.Scrollbar(  # Changed orders_scrollbar to sales_scrollbar
            sales_frame,  # Changed orders_frame to sales_frame
            orient=tk.VERTICAL,
            command=self.sales_tree.yview  # Changed orders_tree to sales_tree
        )
        sales_scrollbar.grid(row=1, column=1, sticky="ns")  # Changed orders_scrollbar to sales_scrollbar
        self.sales_tree.configure(yscrollcommand=sales_scrollbar.set)  # Changed orders_tree to sales_tree

        # Bind selection event
        self.sales_tree.bind("<<TreeviewSelect>>", self._on_sale_select)  # Changed orders_tree to sales_tree, _on_order_select to _on_sale_select
        self.sales_tree.bind("<Double-1>", self._on_sale_double_click)  # Changed orders_tree to sales_tree, _on_order_double_click to _on_sale_double_click

        # Setup filter combobox
        filter_frame = ttk.Frame(sales_frame)  # Changed orders_frame to sales_frame
        filter_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        ttk.Label(filter_frame, text="Filter by status:").pack(side=tk.LEFT, padx=(0, 5))

        self.status_filter = ttk.Combobox(
            filter_frame,
            values=["All"] + [s.name for s in SaleStatus],
            state="readonly",
            width=15
        )
        self.status_filter.set("All")
        self.status_filter.pack(side=tk.LEFT)
        self.status_filter.bind("<<ComboboxSelected>>", self._on_status_filter)

        # Setup sale details frame
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=0)  # Label
        details_frame.rowconfigure(1, weight=1)  # Notebook

        ttk.Label(details_frame, text="Sale Details", font=("TkDefaultFont", 12, "bold")).grid(
            row=0, column=0, sticky="w", padx=5, pady=(0, 5)
        )

        # Create details notebook
        self.details_notebook = ttk.Notebook(details_frame)
        self.details_notebook.grid(row=1, column=0, sticky="nsew")

        # General tab
        general_tab = ttk.Frame(self.details_notebook, padding=10)
        self.details_notebook.add(general_tab, text="General")

        # Items tab
        items_tab = ttk.Frame(self.details_notebook, padding=10)
        self.details_notebook.add(items_tab, text="Items")

        # Create form in general tab
        general_tab.columnconfigure(1, weight=1)

        row = 0
        for label_text in ["Sale ID:", "Reference:", "Customer:", "Date:", "Status:", "Payment Status:",
                           "Total Amount:"]:
            ttk.Label(general_tab, text=label_text).grid(
                row=row, column=0, sticky="w", padx=(0, 10), pady=5
            )
            value_label = ttk.Label(general_tab, text="")
            value_label.grid(row=row, column=1, sticky="w", padx=5, pady=5)
            setattr(self, f"_{label_text.lower().replace(' ', '_').replace(':', '')}_label", value_label)
            row += 1

        # Notes field
        ttk.Label(general_tab, text="Notes:").grid(
            row=row, column=0, sticky="nw", padx=(0, 10), pady=5
        )

        self._notes_text = tk.Text(general_tab, height=5, width=30, wrap=tk.WORD)
        self._notes_text.grid(row=row, column=1, sticky="nsew", padx=5, pady=5)

        # Add scrollbar to notes
        notes_scrollbar = ttk.Scrollbar(
            general_tab,
            orient=tk.VERTICAL,
            command=self._notes_text.yview
        )
        notes_scrollbar.grid(row=row, column=2, sticky="ns")
        self._notes_text.configure(yscrollcommand=notes_scrollbar.set)

        row += 1
        general_tab.rowconfigure(row, weight=1)  # Push everything up

        # Create items treeview in items tab
        items_tab.columnconfigure(0, weight=1)
        items_tab.rowconfigure(0, weight=1)

        self.items_tree = ttk.Treeview(
            items_tab,
            columns=("id", "product", "quantity", "price", "total"),
            show="headings",
            selectmode="browse"
        )
        self.items_tree.grid(row=0, column=0, sticky="nsew")

        # Configure treeview columns
        self.items_tree.heading("id", text="ID")
        self.items_tree.heading("product", text="Product")
        self.items_tree.heading("quantity", text="Quantity")
        self.items_tree.heading("price", text="Unit Price")
        self.items_tree.heading("total", text="Total")

        self.items_tree.column("id", width=50, anchor="center")
        self.items_tree.column("product", width=200)
        self.items_tree.column("quantity", width=100, anchor="center")
        self.items_tree.column("price", width=100, anchor="e")
        self.items_tree.column("total", width=100, anchor="e")

        # Add scrollbar to treeview
        items_scrollbar = ttk.Scrollbar(
            items_tab,
            orient=tk.VERTICAL,
            command=self.items_tree.yview
        )
        items_scrollbar.grid(row=0, column=1, sticky="ns")
        self.items_tree.configure(yscrollcommand=items_scrollbar.set)

        # Toolbar for items
        items_toolbar = ttk.Frame(items_tab)
        items_toolbar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        ttk.Button(
            items_toolbar,
            text="Add Item",
            command=self._on_add_item
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            items_toolbar,
            text="Edit Item",
            command=self._on_edit_item
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            items_toolbar,
            text="Remove Item",
            command=self._on_remove_item
        ).pack(side=tk.LEFT, padx=5)

    def _create_toolbar(self, parent):
        """Create toolbar with action buttons.

        Args:
            parent: Parent widget for the toolbar
        """
        # New sale button
        new_button = ttk.Button(
            parent,
            text="New Sale",  # Changed text
            command=self._on_new_sale  # Changed command
        )
        new_button.pack(side=tk.LEFT, padx=(0, 5))

        # Edit sale button
        edit_button = ttk.Button(
            parent,
            text="Edit Sale",  # Changed text
            command=self._on_edit_sale  # Changed command
        )
        edit_button.pack(side=tk.LEFT, padx=5)

        # Delete sale button
        delete_button = ttk.Button(
            parent,
            text="Delete Sale",  # Changed text
            command=self._on_delete_sale  # Changed command
        )
        delete_button.pack(side=tk.LEFT, padx=5)

        # Separator
        ttk.Separator(parent, orient=tk.VERTICAL).pack(
            side=tk.LEFT, padx=10, fill=tk.Y
        )

        # Search button
        search_button = ttk.Button(
            parent,
            text="Search",
            command=self._on_search
        )
        search_button.pack(side=tk.LEFT, padx=5)

        # Reset button
        reset_button = ttk.Button(
            parent,
            text="Reset",
            command=self._on_reset
        )
        reset_button.pack(side=tk.LEFT, padx=5)

    def _load_sales(self):  # Changed _load_orders to _load_sales
        """Load sales from the database."""
        try:
            sale_service = self.get_service(ISaleService)
            sales = sale_service.get_all_sales()  # Changed order_service to sale_service

            # Clear treeview
            for item in self.sales_tree.get_children():  # Changed orders_tree to sales_tree
                self.sales_tree.delete(item)  # Changed orders_tree to sales_tree

            # Populate treeview
            for sale in sales:
                # Ensure sale is dict-like
                sale_dict = sale
                if not hasattr(sale, 'get'):
                    # Try to convert to dict if it's an object
                    if hasattr(sale, '__dict__'):
                        sale_dict = {k: v for k, v in sale.__dict__.items() if not k.startswith('_')}
                    else:
                        # Default empty dict
                        sale_dict = {}

                self.sales_tree.insert(  # Changed orders_tree to sales_tree
                    "",
                    "end",
                    values=(
                        sale_dict.get("id", ""),
                        sale_dict.get("reference_number", ""),
                        sale_dict.get("sale_date", ""),  # Changed order_date to sale_date
                        sale_dict.get("status", ""),
                        f"${sale_dict.get('total_amount', 0):.2f}"
                    )
                )
        except Exception as e:
            self.logger.error(f"Error loading sales: {str(e)}")  # Changed orders to sales
            self.show_error("Load Error", f"Failed to load sales: {str(e)}")  # Changed orders to sales

    def _load_sale_details(self, sale_id: int):  # Changed _load_order_details to _load_sale_details
        """Load details for the selected sale.

        Args:
            sale_id: ID of the sale to load details for
        """
        try:
            sale_service = self.get_service(ISaleService)
            sale = sale_service.get_sale_by_id(sale_id)  # Changed order_service to sale_service

            if not sale:
                return

            # Update general tab labels
            self._sale_id_label.config(text=str(sale.get("id", "")))  # Changed order_id to sale_id
            self._reference_label.config(text=sale.get("reference_number", ""))
            self._customer_label.config(text=sale.get("customer_name", ""))
            self._date_label.config(text=sale.get("sale_date", ""))  # Changed order_date to sale_date
            self._status_label.config(text=sale.get("status", ""))
            self._payment_status_label.config(text=sale.get("payment_status", ""))
            self._total_amount_label.config(text=f"${sale.get('total_amount', 0):.2f}")

            # Update notes
            self._notes_text.delete(1.0, tk.END)
            self._notes_text.insert(tk.END, sale.get("notes", ""))

            # Load sale items
            self._load_sale_items(sale_id)  # Changed load_order_items to load_sale_items
        except Exception as e:
            self.logger.error(f"Error loading sale details: {str(e)}")  # Changed order to sale
            self.show_error("Load Error", f"Failed to load sale details: {str(e)}")  # Changed order to sale

    def _load_sale_items(self, sale_id: int):  # Changed _load_order_items to _load_sale_items
        """Load items for the selected sale.

        Args:
            sale_id: ID of the sale to load items for
        """
        try:
            sale_service = self.get_service(ISaleService)
            #items = sale_service.get_sale_items(sale_id)  # Assuming you have a get_sale_items function
            sale = sale_service.get_sale_by_id(sale_id, include_items=True)

            # Clear treeview
            for item in self.items_tree.get_children():
                self.items_tree.delete(item)

            if sale and 'items' in sale:
                items = sale['items']
                # Populate treeview
                for item in items:
                    self.items_tree.insert(
                        "",
                        "end",
                        values=(
                            item.get("id", ""),
                            item.get("product_name", ""),
                            item.get("quantity", 0),
                            f"${item.get('unit_price', 0):.2f}",
                            f"${item.get('quantity', 0) * item.get('unit_price', 0):.2f}"
                        )
                    )
        except Exception as e:
            self.logger.error(f"Error loading sale items: {str(e)}")  # Changed order to sale
            self.show_error("Load Error", f"Failed to load sale items: {str(e)}")  # Changed order to sale

    def _on_sale_select(self, event=None):  # Changed _on_order_select to _on_sale_select
        """Handle sale selection in treeview."""
        selection = self.sales_tree.selection()  # Changed orders_tree to sales_tree
        if not selection:
            return

        item = selection[0]
        values = self.sales_tree.item(item, "values")  # Changed orders_tree to sales_tree
        if not values:
            return

        sale_id = int(values[0])  # Changed order_id to sale_id
        self._selected_sale_id = sale_id  # Changed _selected_order_id to _selected_sale_id
        self._load_sale_details(sale_id)  # Changed _load_order_details to _load_sale_details

    def _on_sale_double_click(self, event=None):  # Changed _on_order_double_click to _on_sale_double_click
        """Handle double-click on an sale to edit it."""
        self._on_edit_sale()  # Changed _on_edit_order to _on_edit_sale

    def _on_new_sale(self):  # Changed _on_new_order to _on_new_sale
        """Handle new sale button click."""
        # Open new sale dialog
        pass

    def _on_edit_sale(self):  # Changed _on_edit_order to _on_edit_sale
        """Handle edit sale button click."""
        if not self._selected_sale_id:  # Changed _selected_order_id to _selected_sale_id
            self.show_info("No Selection", "Please select an sale to edit.")
            return

        # Open edit sale dialog
        pass

    def _on_delete_sale(self):  # Changed _on_delete_order to _on_delete_sale
        """Handle delete sale button click."""
        if not self._selected_sale_id:  # Changed _selected_order_id to _selected_sale_id
            self.show_info("No Selection", "Please select an sale to delete.")
            return

        if not self.confirm("Confirm Delete", "Are you sure you want to delete this sale?"):
            return

        try:
            sale_service = self.get_service(ISaleService)
            success = sale_service.delete_sale(self._selected_sale_id)  # Changed order_service to sale_service, _selected_order_id to _selected_sale_id

            if success:
                self.show_info("Success", "Sale deleted successfully.")  # Changed order to sale
                self._selected_sale_id = None  # Changed _selected_order_id to _selected_sale_id
                self._load_sales()  # Changed _load_orders to _load_sales
            else:
                self.show_error("Delete Error", "Failed to delete sale.")  # Changed order to sale
        except Exception as e:
            self.logger.error(f"Error deleting sale: {str(e)}")  # Changed order to sale
            self.show_error("Delete Error", f"Failed to delete sale: {str(e)}")  # Changed order to sale

    def _on_search(self):
        """Handle search button click."""
        columns = ["id", "reference", "customer", "status"]
        SearchDialog(self, columns, self._perform_search)

    def _perform_search(self, field: str, search_text: str, exact_match: bool):
        """Perform search based on criteria.

        Args:
            field: Field to search in
            search_text: Text to search for
            exact_match: Whether to perform exact matching
        """
        try:
            sale_service = self.get_service(ISaleService) # Change order_service to sale_service
            sales = sale_service.search_sales(search_text) # Remove field parameter.

            # Clear treeview
            for item in self.sales_tree.get_children():
                self.sales_tree.delete(item)

            # Populate treeview
            for sale in sales:
                self.sales_tree.insert(
                    "",
                    "end",
                    values=(
                        sale.get("id", ""),
                        sale.get("reference_number", ""),
                        sale.get("sale_date", ""),
                        sale.get("status", ""),
                        f"${sale.get('total_amount', 0):.2f}"
                    )
                )
        except Exception as e:
            self.logger.error(f"Error searching sales: {str(e)}")
            self.show_error("Search Error", f"Failed to search sales: {str(e)}")

    def _on_status_filter(self, event=None):
        """Handle status filter selection."""
        status = self.status_filter.get()

        try:
            sale_service = self.get_service(ISaleService)

            if status == "All":
                sales, _ = sale_service.get_all_sales()
            else:
                # Convert string status to enum
                try:
                    status_enum = SaleStatus[status]
                except KeyError:
                    self.show_error("Filter Error", f"Invalid status: {status}")
                    return
                sales, _ = sale_service.get_all_sales(status=status_enum)  # Pass SaleStatus enum

            # Clear treeview
            for item in self.sales_tree.get_children():
                self.sales_tree.delete(item)

            # Populate treeview
            for sale in sales:
                self.sales_tree.insert(
                    "",
                    "end",
                    values=(
                        sale.get("id", ""),
                        sale.get("reference_number", ""),
                        sale.get("sale_date", ""),
                        sale.get("status", ""),
                        f"${sale.get('total_amount', 0):.2f}"
                    )
                )
        except Exception as e:
            self.logger.error(f"Error filtering sales: {str(e)}")
            self.show_error("Filter Error", f"Failed to filter sales: {str(e)}")

    def _on_reset(self):
        """Handle reset button click to clear all filters and reload sales."""
        self.status_filter.set("All")
        self._load_sales()

    def _on_add_item(self):
        """Handle add item button click."""
        if not self._selected_sale_id:
            self.show_info("No Sale Selected", "Please select a sale first.")
            return

        # Open add item dialog
        pass

    def _on_edit_item(self):
        """Handle edit item button click."""
        selection = self.items_tree.selection()
        if not selection:
            self.show_info("No Selection", "Please select an item to edit.")
            return

        # Open edit item dialog
        pass

    def _on_remove_item(self):
        """Handle remove item button click."""
        selection = self.items_tree.selection()
        if not selection:
            self.show_info("No Selection", "Please select an item to remove.")
            return

        item = selection[0]
        values = self.items_tree.item(item, "values")
        if not values:
            return

        item_id = int(values[0])

        if not self.confirm("Confirm Remove", "Are you sure you want to remove this item?"):
            return

        try:
            sale_service = self.get_service(ISaleService)
            success = sale_service.remove_sale_item(self._selected_sale_id, item_id)  # Changed order to sale, _selected_order_id to _selected_sale_id

            if success:
                self.show_info("Success", "Item removed successfully.")
                self._load_sale_items(self._selected_sale_id)  # Changed _load_order_items to _load_sale_items, _selected_order_id to _selected_sale_id
                # Reload sale to update totals
                self._load_sale_details(self._selected_sale_id)  # Changed _load_order_details to _load_sale_details, _selected_order_id to _selected_sale_id
            else:
                self.show_error("Remove Error", "Failed to remove item.")
        except Exception as e:
            self.logger.error(f"Error removing item: {str(e)}")
            self.show_error("Remove Error", f"Failed to remove item: {str(e)}")

    def sale_service(self, service: ISaleService):  # Changed order_service to sale_service
        """Set the sale service.

        Args:
            service (ISaleService): The sale service instance
        """
        self._sale_service = service  # Changed _order_service to _sale_service