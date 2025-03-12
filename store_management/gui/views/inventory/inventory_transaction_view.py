# gui/views/inventory/inventory_transaction_view.py
"""
Inventory Transaction View.
Displays a history of inventory transactions with filtering and sorting.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional
import datetime

from database.models.enums import TransactionType
from gui.base.base_list_view import BaseListView
from gui.utils.service_access import with_service


class InventoryTransactionView(BaseListView):
    """View for displaying inventory transaction history."""

    def __init__(
            self,
            parent,
            inventory_id: Optional[int] = None,
            item_id: Optional[int] = None,
            item_type: Optional[str] = None
    ):
        """
        Initialize the inventory transaction view.

        Args:
            parent: The parent widget
            inventory_id: Optional ID of inventory to filter by
            item_id: Optional ID of item to filter by
            item_type: Optional type of item to filter by
        """
        super().__init__(parent)
        self.title = "Inventory Transactions"
        self.service_name = "IInventoryService"

        # Store filter parameters
        self.inventory_id = inventory_id
        self.item_id = item_id
        self.item_type = item_type

        # Set predefined filter criteria
        if self.inventory_id:
            self.filter_criteria = {"inventory_id": self.inventory_id}
        elif self.item_id and self.item_type:
            self.filter_criteria = {"item_id": self.item_id, "item_type": self.item_type}

        # Configure columns
        self.columns = [
            ("id", "ID", 60),
            ("item_name", "Item", 200),
            ("transaction_type", "Type", 120),
            ("quantity", "Quantity", 80),
            ("transaction_date", "Date", 150),
            ("user", "User", 100),
            ("reference", "Reference", 150),
            ("storage_location", "Location", 150),
            ("notes", "Notes", 200)
        ]

        # Configure search fields
        self.search_fields = [
            {"name": "item_name", "label": "Item Name", "type": "text", "width": 20},
            {"name": "transaction_type", "label": "Type", "type": "select",
             "options": [e.value for e in TransactionType], "width": 15},
            {"name": "date_from", "label": "From Date", "type": "date", "width": 15},
            {"name": "date_to", "label": "To Date", "type": "date", "width": 15},
            {"name": "storage_location", "label": "Location", "type": "text", "width": 15}
        ]

    def build(self):
        """Build the transaction view."""
        super().build()

        # Add additional buttons to the action buttons area if not in filtered mode
        if not self.inventory_id and not (self.item_id and self.item_type):
            self.add_report_action(self.action_buttons)

    def add_report_action(self, parent):
        """
        Add report action button.

        Args:
            parent: The parent widget for the button
        """
        # Add button to generate transaction report
        btn_report = ttk.Button(
            parent,
            text="Generate Report",
            command=self.generate_transaction_report)
        btn_report.pack(side=tk.LEFT, padx=5)

    def extract_item_values(self, item):
        """
        Extract values from a transaction item for display in the treeview.

        Args:
            item: The transaction item to extract values from

        Returns:
            List of values corresponding to treeview columns
        """
        # For DTO objects
        if hasattr(item, "id"):
            # Get item name
            item_name = ""
            if hasattr(item, "inventory") and item.inventory:
                if hasattr(item.inventory, "item_name"):
                    item_name = item.inventory.item_name
                elif hasattr(item.inventory, "related_item") and hasattr(item.inventory.related_item, "name"):
                    item_name = item.inventory.related_item.name
            elif hasattr(item, "item_name"):
                item_name = item.item_name

            # Format transaction date
            transaction_date = ""
            if hasattr(item, "transaction_date"):
                if isinstance(item.transaction_date, datetime.datetime):
                    transaction_date = item.transaction_date.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    transaction_date = str(item.transaction_date)

            return [
                item.id,
                item_name,
                getattr(item, "transaction_type", ""),
                getattr(item, "quantity", 0),
                transaction_date,
                getattr(item, "user", ""),
                getattr(item, "reference", ""),
                getattr(item, "storage_location", ""),
                getattr(item, "notes", "")
            ]

        # For dictionary data
        elif isinstance(item, dict):
            # Get item name
            item_name = item.get("item_name", "")
            if not item_name and "inventory" in item and item["inventory"]:
                inventory = item["inventory"]
                if isinstance(inventory, dict):
                    if "item_name" in inventory:
                        item_name = inventory["item_name"]
                    elif "related_item" in inventory and inventory["related_item"]:
                        related = inventory["related_item"]
                        if isinstance(related, dict) and "name" in related:
                            item_name = related["name"]

            # Format transaction date
            transaction_date = item.get("transaction_date", "")
            if transaction_date and isinstance(transaction_date, datetime.datetime):
                transaction_date = transaction_date.strftime("%Y-%m-%d %H:%M:%S")

            return [
                item.get("id", ""),
                item_name,
                item.get("transaction_type", ""),
                item.get("quantity", 0),
                transaction_date,
                item.get("user", ""),
                item.get("reference", ""),
                item.get("storage_location", ""),
                item.get("notes", "")
            ]

        # Unknown data type
        return [str(item)] + [""] * (len(self.columns) - 1)

    def on_view(self):
        """Handle view transaction action."""
        if not self.selected_item:
            return

        self.logger.info(f"Opening view transaction dialog for ID {self.selected_item}")

        try:
            transaction_id = int(self.selected_item)
            self.view_transaction_details(transaction_id)
        except Exception as e:
            self.logger.error(f"Error opening transaction details: {str(e)}")
            self.show_error("Error", f"Could not open transaction details: {str(e)}")

    def on_add(self):
        """Handle add transaction action."""
        self.logger.info("Add transaction not directly supported")
        self.show_info(
            "Information",
            "New transactions are created through inventory adjustments.\n\n"
            "Please use the Inventory view to make adjustments."
        )

    def on_edit(self):
        """Handle edit transaction action."""
        self.logger.info("Edit transaction not supported")
        self.show_info(
            "Information",
            "Transactions cannot be edited after creation for audit purposes."
        )

    def on_delete(self):
        """Handle delete transaction action."""
        self.logger.info("Delete transaction not supported")
        self.show_info(
            "Information",
            "Transactions cannot be deleted for audit purposes."
        )

    def view_transaction_details(self, transaction_id):
        """
        View details of a specific transaction.

        Args:
            transaction_id: ID of the transaction to view
        """
        try:
            service = self.get_service(self.service_name)
            transaction = service.get_transaction_by_id(transaction_id)

            if not transaction:
                self.show_error("Error", f"Could not retrieve transaction details for ID {transaction_id}")
                return

            # Create dialog
            dialog = tk.Toplevel(self.frame)
            dialog.title(f"Transaction Details - ID: {transaction_id}")
            dialog.geometry("600x500")
            dialog.transient(self.frame)
            dialog.grab_set()

            # Create content frame
            content = ttk.Frame(dialog, padding=20)
            content.pack(fill=tk.BOTH, expand=True)

            # Create details view
            self.create_transaction_details_view(content, transaction)

            # Add buttons
            btn_frame = ttk.Frame(dialog, padding=10)
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

            ttk.Button(
                btn_frame,
                text="Close",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)

            # Add print button
            ttk.Button(
                btn_frame,
                text="Print",
                command=lambda: self.print_transaction(transaction_id)
            ).pack(side=tk.RIGHT, padx=5)

            # Center the dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'+{x}+{y}')

        except Exception as e:
            self.logger.error(f"Error opening transaction details: {str(e)}")
            self.show_error("Error", f"Could not display transaction details: {str(e)}")

    def create_transaction_details_view(self, parent, transaction):
        """
        Create the transaction details view.

        Args:
            parent: The parent widget
            transaction: The transaction data
        """
        # Create header with transaction type
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        transaction_type = getattr(transaction, "transaction_type", "Unknown Transaction")

        ttk.Label(
            header_frame,
            text=f"Transaction: {transaction_type}",
            font=("Helvetica", 16, "bold")
        ).pack(side=tk.LEFT)

        # Create details frame
        details_frame = ttk.LabelFrame(parent, text="Transaction Details")
        details_frame.pack(fill=tk.X, pady=10)

        # Grid layout for details
        details_grid = ttk.Frame(details_frame, padding=10)
        details_grid.pack(fill=tk.X)

        # Row 1
        ttk.Label(details_grid, text="Transaction ID:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(details_grid, text=str(getattr(transaction, "id", ""))).grid(row=0, column=1, sticky="w", padx=5,
                                                                               pady=2)

        ttk.Label(details_grid, text="Date:").grid(row=0, column=2, sticky="w", padx=5, pady=2)

        # Format transaction date
        transaction_date = getattr(transaction, "transaction_date", "")
        if transaction_date and isinstance(transaction_date, datetime.datetime):
            transaction_date = transaction_date.strftime("%Y-%m-%d %H:%M:%S")

        ttk.Label(details_grid, text=str(transaction_date)).grid(row=0, column=3, sticky="w", padx=5, pady=2)

        # Row 2
        ttk.Label(details_grid, text="Quantity:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(details_grid, text=str(getattr(transaction, "quantity", 0))).grid(row=1, column=1, sticky="w", padx=5,
                                                                                    pady=2)

        ttk.Label(details_grid, text="User:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        ttk.Label(details_grid, text=str(getattr(transaction, "user", ""))).grid(row=1, column=3, sticky="w", padx=5,
                                                                                 pady=2)

        # Row 3
        ttk.Label(details_grid, text="Reference:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Label(details_grid, text=str(getattr(transaction, "reference", ""))).grid(row=2, column=1, sticky="w",
                                                                                      padx=5, pady=2)

        ttk.Label(details_grid, text="Location:").grid(row=2, column=2, sticky="w", padx=5, pady=2)
        ttk.Label(details_grid, text=str(getattr(transaction, "storage_location", ""))).grid(row=2, column=3,
                                                                                             sticky="w", padx=5, pady=2)

        # Notes
        notes_frame = ttk.LabelFrame(parent, text="Notes")
        notes_frame.pack(fill=tk.X, pady=10)

        notes_text = tk.Text(notes_frame, height=4, wrap=tk.WORD)
        notes_text.insert("1.0", getattr(transaction, "notes", ""))
        notes_text.config(state="disabled")  # Make read-only
        notes_text.pack(fill=tk.X, padx=10, pady=10)

        # Item information section
        if hasattr(transaction, "inventory") and transaction.inventory:
            item_frame = ttk.LabelFrame(parent, text="Inventory Item Information")
            item_frame.pack(fill=tk.X, pady=10)

            item_grid = ttk.Frame(item_frame, padding=10)
            item_grid.pack(fill=tk.X)

            inventory = transaction.inventory

            # Get item name
            item_name = ""
            if hasattr(inventory, "item_name"):
                item_name = inventory.item_name
            elif hasattr(inventory, "related_item") and hasattr(inventory.related_item, "name"):
                item_name = inventory.related_item.name

            # Row 1
            ttk.Label(item_grid, text="Inventory ID:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(item_grid, text=str(getattr(inventory, "id", ""))).grid(row=0, column=1, sticky="w", padx=5,
                                                                              pady=2)

            ttk.Label(item_grid, text="Item Type:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
            ttk.Label(item_grid, text=str(getattr(inventory, "item_type", "")).capitalize()).grid(row=0, column=3,
                                                                                                  sticky="w", padx=5,
                                                                                                  pady=2)

            # Row 2
            ttk.Label(item_grid, text="Item Name:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(item_grid, text=item_name).grid(row=1, column=1, sticky="w", padx=5, pady=2)

            ttk.Label(item_grid, text="Status:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
            ttk.Label(item_grid, text=str(getattr(inventory, "status", ""))).grid(row=1, column=3, sticky="w", padx=5,
                                                                                  pady=2)

            # Row 3
            ttk.Label(item_grid, text="Current Quantity:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(item_grid, text=str(getattr(inventory, "quantity", 0))).grid(row=2, column=1, sticky="w", padx=5,
                                                                                   pady=2)

            ttk.Label(item_grid, text="Current Location:").grid(row=2, column=2, sticky="w", padx=5, pady=2)
            ttk.Label(item_grid, text=str(getattr(inventory, "storage_location", ""))).grid(row=2, column=3, sticky="w",
                                                                                            padx=5, pady=2)

    def print_transaction(self, transaction_id):
        """
        Print the transaction details.

        Args:
            transaction_id: ID of the transaction to print
        """
        self.logger.info(f"Printing transaction {transaction_id}")

        # In a real application, this would generate a printable document
        # For this demonstration, we'll just show a message
        messagebox.showinfo(
            "Print Transaction",
            f"Printing transaction {transaction_id}...\n\n"
            "In a real application, this would generate a printable document."
        )

    def generate_transaction_report(self):
        """Generate a transaction report."""
        self.logger.info("Opening transaction report dialog")

        try:
            # Create dialog
            dialog = tk.Toplevel(self.frame)
            dialog.title("Generate Transaction Report")
            dialog.geometry("500x400")
            dialog.transient(self.frame)
            dialog.grab_set()

            # Create content frame
            content = ttk.Frame(dialog, padding=20)
            content.pack(fill=tk.BOTH, expand=True)

            # Add instructions
            ttk.Label(
                content,
                text="Transaction Report Generator",
                font=("Helvetica", 14, "bold")
            ).pack(pady=(0, 10))

            ttk.Label(
                content,
                text="Generate a report of inventory transactions.",
                wraplength=450
            ).pack(pady=5)

            # Report type section
            report_frame = ttk.LabelFrame(content, text="Report Type")
            report_frame.pack(fill=tk.X, pady=10)

            report_grid = ttk.Frame(report_frame, padding=10)
            report_grid.pack(fill=tk.X)

            report_type_var = tk.StringVar(value="SUMMARY")

            ttk.Radiobutton(
                report_grid,
                text="Summary Report",
                variable=report_type_var,
                value="SUMMARY"
            ).grid(row=0, column=0, sticky="w", padx=5)

            ttk.Radiobutton(
                report_grid,
                text="Detailed Report",
                variable=report_type_var,
                value="DETAILED"
            ).grid(row=0, column=1, sticky="w", padx=5)

            ttk.Radiobutton(
                report_grid,
                text="Audit Report",
                variable=report_type_var,
                value="AUDIT"
            ).grid(row=1, column=0, sticky="w", padx=5)

            # Filters section
            filters_frame = ttk.LabelFrame(content, text="Date Range")
            filters_frame.pack(fill=tk.X, pady=10)

            filters_grid = ttk.Frame(filters_frame, padding=10)
            filters_grid.pack(fill=tk.X)

            # Date range
            ttk.Label(filters_grid, text="From Date:").grid(row=0, column=0, sticky="w", padx=5, pady=2)

            from_date_var = tk.StringVar()
            from_date_entry = ttk.Entry(
                filters_grid,
                textvariable=from_date_var,
                width=15
            )
            from_date_entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)

            # Add calendar button
            ttk.Button(
                filters_grid,
                text="...",
                width=3,
                command=lambda: self.show_calendar(from_date_var)
            ).grid(row=0, column=2, sticky="w")

            ttk.Label(filters_grid, text="To Date:").grid(row=1, column=0, sticky="w", padx=5, pady=2)

            to_date_var = tk.StringVar()
            to_date_entry = ttk.Entry(
                filters_grid,
                textvariable=to_date_var,
                width=15
            )
            to_date_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)

            # Add calendar button
            ttk.Button(
                filters_grid,
                text="...",
                width=3,
                command=lambda: self.show_calendar(to_date_var)
            ).grid(row=1, column=2, sticky="w")

            # Additional filters
            add_filters_frame = ttk.LabelFrame(content, text="Additional Filters")
            add_filters_frame.pack(fill=tk.X, pady=10)

            add_filters_grid = ttk.Frame(add_filters_frame, padding=10)
            add_filters_grid.pack(fill=tk.X)

            # Transaction type
            ttk.Label(add_filters_grid, text="Transaction Type:").grid(row=0, column=0, sticky="w", padx=5, pady=2)

            transaction_type_var = tk.StringVar(value="ALL")
            transaction_type_combo = ttk.Combobox(
                add_filters_grid,
                textvariable=transaction_type_var,
                values=["ALL"] + [e.value for e in TransactionType],
                state="readonly",
                width=15
            )
            transaction_type_combo.grid(row=0, column=1, sticky="w", padx=5, pady=2)

            # Item type
            ttk.Label(add_filters_grid, text="Item Type:").grid(row=0, column=2, sticky="w", padx=5, pady=2)

            item_type_var = tk.StringVar(value="ALL")
            item_type_combo = ttk.Combobox(
                add_filters_grid,
                textvariable=item_type_var,
                values=["ALL", "material", "product", "tool"],
                state="readonly",
                width=15
            )
            item_type_combo.grid(row=0, column=3, sticky="w", padx=5, pady=2)

            # Format options
            format_frame = ttk.LabelFrame(content, text="Output Format")
            format_frame.pack(fill=tk.X, pady=10)

            format_grid = ttk.Frame(format_frame, padding=10)
            format_grid.pack(fill=tk.X)

            format_var = tk.StringVar(value="PDF")

            ttk.Radiobutton(
                format_grid,
                text="PDF Document",
                variable=format_var,
                value="PDF"
            ).grid(row=0, column=0, sticky="w", padx=5)

            ttk.Radiobutton(
                format_grid,
                text="Excel Spreadsheet",
                variable=format_var,
                value="EXCEL"
            ).grid(row=0, column=1, sticky="w", padx=5)

            ttk.Radiobutton(
                format_grid,
                text="CSV File",
                variable=format_var,
                value="CSV"
            ).grid(row=0, column=2, sticky="w", padx=5)

            # Buttons
            btn_frame = ttk.Frame(dialog, padding=10)
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

            ttk.Button(
                btn_frame,
                text="Cancel",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)

            def generate_report():
                try:
                    # Get the filter values
                    report_type = report_type_var.get()
                    from_date = from_date_var.get() or None
                    to_date = to_date_var.get() or None
                    transaction_type = None if transaction_type_var.get() == "ALL" else transaction_type_var.get()
                    item_type = None if item_type_var.get() == "ALL" else item_type_var.get()

                    # Get the format
                    output_format = format_var.get()

                    # Generate the report
                    service = self.get_service(self.service_name)

                    # Show a confirmation that report is being generated
                    dialog.destroy()
                    messagebox.showinfo(
                        "Report Generation",
                        f"The {report_type} transaction report is being generated in {output_format} format.\n\n"
                        "It will be saved to the reports directory."
                    )

                    # In a real application, this would call the service to generate the report
                    # For this demonstration, we'll just log the parameters
                    self.logger.info(
                        f"Generating transaction report with: "
                        f"type={report_type}, format={output_format}, "
                        f"from_date={from_date}, to_date={to_date}, "
                        f"transaction_type={transaction_type}, item_type={item_type}"
                    )

                except Exception as e:
                    self.logger.error(f"Error generating transaction report: {str(e)}")
                    messagebox.showerror("Error", f"Could not generate report: {str(e)}")

            ttk.Button(
                btn_frame,
                text="Generate",
                command=generate_report
            ).pack(side=tk.RIGHT, padx=5)

            # Center the dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'+{x}+{y}')

        except Exception as e:
            self.logger.error(f"Error opening report dialog: {str(e)}")
            self.show_error("Error", f"Could not open report dialog: {str(e)}")

    def show_calendar(self, date_var):
        """
        Show a calendar for date selection.

        Args:
            date_var: The StringVar to update with selected date
        """
        # In a real application, this would show a calendar widget
        # For this demonstration, we'll just show a message with date format example
        messagebox.showinfo(
            "Date Selection",
            "In a real application, this would show a calendar picker.\n\n"
            "Please enter date in format: YYYY-MM-DD"
        )

    def get_items(self, service, offset, limit):
        """
        Get transaction items with filtering.

        Args:
            service: The service to use
            offset: Pagination offset
            limit: Page size

        Returns:
            List of transaction items
        """
        # Apply special filtering for inventory_id or item_id+item_type
        if self.inventory_id:
            return service.get_transactions_by_inventory(
                inventory_id=self.inventory_id,
                offset=offset,
                limit=limit,
                sort_column=self.sort_column,
                sort_direction=self.sort_direction,
                **{k: v for k, v in self.filter_criteria.items() if k != "inventory_id"}
            )
        elif self.item_id and self.item_type:
            return service.get_transactions_by_item(
                item_id=self.item_id,
                item_type=self.item_type,
                offset=offset,
                limit=limit,
                sort_column=self.sort_column,
                sort_direction=self.sort_direction,
                **{k: v for k, v in self.filter_criteria.items() if k not in ["item_id", "item_type"]}
            )
        else:
            # Regular filtering
            return service.get_transactions(
                offset=offset,
                limit=limit,
                sort_column=self.sort_column,
                sort_direction=self.sort_direction,
                **self.filter_criteria
            )

    def get_total_count(self, service):
        """
        Get the total count of transaction items.

        Args:
            service: The service to use

        Returns:
            The total count of items
        """
        # Apply special filtering for inventory_id or item_id+item_type
        if self.inventory_id:
            return service.get_transaction_count_by_inventory(
                inventory_id=self.inventory_id,
                **{k: v for k, v in self.filter_criteria.items() if k != "inventory_id"}
            )
        elif self.item_id and self.item_type:
            return service.get_transaction_count_by_item(
                item_id=self.item_id,
                item_type=self.item_type,
                **{k: v for k, v in self.filter_criteria.items() if k not in ["item_id", "item_type"]}
            )
        else:
            # Regular filtering
            return service.get_transaction_count(**self.filter_criteria)