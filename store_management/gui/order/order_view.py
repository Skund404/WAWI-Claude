# Path: store_management/gui/order/order_view.py
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
from typing import List, Dict, Any, Optional

from application import Application
from gui.base_view import BaseView
from services.interfaces.order_service import IOrderService
from services.interfaces.supplier_service import ISupplierService


class OrderView(BaseView):
    """
    Comprehensive view for managing orders with:
    - Treeview for listing orders
    - Detailed order information display
    - Actions for creating, editing, and managing orders
    """

    def __init__(self, parent: tk.Widget, app: Application):
        """
        Initialize the Order View.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)

        # Resolve services
        self.order_service = self.get_service(IOrderService)
        self.supplier_service = self.get_service(ISupplierService)

        # Setup UI components
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI components."""
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Create toolbar
        self.create_toolbar()

        # Create order list treeview
        self.create_order_list()

        # Create order details view
        self.create_order_details()

    def create_toolbar(self):
        """Create toolbar with order management actions."""
        toolbar_frame = ttk.Frame(self)
        toolbar_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)

        # Add buttons
        add_btn = ttk.Button(toolbar_frame, text="Add Order", command=self.show_add_order_dialog)
        add_btn.pack(side=tk.LEFT,
                     padx=2)

        edit_btn = ttk.Button(toolbar_frame, text="Edit Order", command=self._edit_order)
        edit_btn.pack(side=tk.LEFT, padx=2)

        delete_btn = ttk.Button(toolbar_frame, text="Delete Order", command=self.delete_order)
        delete_btn.pack(side=tk.LEFT, padx=2)

        search_btn = ttk.Button(toolbar_frame, text="Search", command=self._show_search_dialog)
        search_btn.pack(side=tk.LEFT, padx=2)

    def create_order_list(self):
        """Create treeview to display list of orders."""
        # Create frame for order list
        list_frame = ttk.Frame(self)
        list_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)

        # Scrollbars
        list_scroll_y = ttk.Scrollbar(list_frame)
        list_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        list_scroll_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
        list_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview for orders
        self.order_tree = ttk.Treeview(
            list_frame,
            yscrollcommand=list_scroll_y.set,
            xscrollcommand=list_scroll_x.set,
            columns=('ID', 'Order Number', 'Supplier', 'Date', 'Total Amount', 'Status')
        )
        self.order_tree.pack(expand=True, fill=tk.BOTH)

        # Configure scrollbars
        list_scroll_y.config(command=self.order_tree.yview)
        list_scroll_x.config(command=self.order_tree.xview)

        # Configure columns
        self.order_tree.column('#0', width=0, stretch=tk.NO)
        self.order_tree.column('ID', anchor=tk.CENTER, width=50)
        self.order_tree.column('Order Number', anchor=tk.W, width=100)
        self.order_tree.column('Supplier', anchor=tk.W, width=150)
        self.order_tree.column('Date', anchor=tk.CENTER, width=100)
        self.order_tree.column('Total Amount', anchor=tk.E, width=100)
        self.order_tree.column('Status', anchor=tk.CENTER, width=100)

        # Headings
        self.order_tree.heading('#0', text='', anchor=tk.CENTER)
        self.order_tree.heading('ID', text='ID', anchor=tk.CENTER)
        self.order_tree.heading('Order Number', text='Order Number', anchor=tk.W)
        self.order_tree.heading('Supplier', text='Supplier', anchor=tk.W)
        self.order_tree.heading('Date', text='Date', anchor=tk.CENTER)
        self.order_tree.heading('Total Amount', text='Total Amount', anchor=tk.E)
        self.order_tree.heading('Status', text='Status', anchor=tk.CENTER)

        # Bind selection event
        self.order_tree.bind('<<TreeviewSelect>>', self._on_order_select)

    def create_order_details(self):
        """Create detailed view for selected order."""
        # Create details frame
        details_frame = ttk.LabelFrame(self, text="Order Details")
        details_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)

        # Create text widget for order details
        self.details_text = tk.Text(details_frame, height=10, wrap=tk.WORD)
        self.details_text.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        self.details_text.config(state=tk.DISABLED)

    def load_data(self):
        """Load orders from the order service."""
        try:
            # Clear existing items
            self.order_tree.delete(*self.order_tree.get_children())

            # Retrieve orders
            orders = self.order_service.get_all_orders()

            # Populate treeview
            for order in orders:
                self.order_tree.insert('', 'end', values=(
                    order.get('id', 'N/A'),
                    order.get('order_number', 'N/A'),
                    order.get('supplier_name', 'N/A'),
                    order.get('order_date', 'N/A'),
                    order.get('total_amount', 'N/A'),
                    order.get('status', 'N/A')
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load orders: {str(e)}")

    def show_add_order_dialog(self):
        """Show dialog to add a new order."""
        from store_management.gui.order.order_dialog import AddOrderDialog

        # Get suppliers for the dialog
        try:
            suppliers = self.supplier_service.get_all_suppliers()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load suppliers: {str(e)}")
            return

        # Create and show add order dialog
        dialog = AddOrderDialog(
            self,
            self._save_new_order,
            suppliers=suppliers,
            title="Add New Order"
        )

    def _save_new_order(self, order_data: Dict[str, Any]):
        """
        Save a new order.

        Args:
            order_data: Dictionary containing order information
        """
        try:
            # Call order service to create order
            result = self.order_service.create_order(order_data)

            if result:
                messagebox.showinfo("Success", "Order created successfully")
                # Refresh order list
                self.load_data()
            else:
                messagebox.showerror("Error", "Failed to create order")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create order: {str(e)}")

    def _on_order_select(self, event=None):
        """
        Handle order selection in treeview.

        Args:
            event: Tkinter event (optional)
        """
        selected_items = self.order_tree.selection()
        if not selected_items:
            # Clear details if no selection
            self.details_text.config(state=tk.NORMAL)
            self.details_text.delete(1.0, tk.END)
            self.details_text.config(state=tk.DISABLED)
            return

        # Get selected order ID
        order_id = self.order_tree.item(selected_items[0])['values'][0]
        self._load_order_details(order_id)

    def _load_order_details(self, order_id):
        """
        Load details for a specific order.

        Args:
            order_id: ID of the order to load details for
        """
        try:
            # Retrieve order details
            order = self.order_service.get_order_by_id(order_id)

            if not order:
                messagebox.showinfo("Order Not Found", f"No order found with ID {order_id}")
                return

            # Update details text
            self.details_text.config(state=tk.NORMAL)
            self.details_text.delete(1.0, tk.END)

            # Display order details
            for key, value in order.items():
                self.details_text.insert(tk.END, f"{key.replace('_', ' ').title()}: {value}\n")

            self.details_text.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load order details: {str(e)}")

    def _edit_order(self):
        """Edit the selected order."""
        selected_items = self.order_tree.selection()
        if not selected_items:
            messagebox.showwarning("Edit Order", "Please select an order to edit.")
            return

        # Get selected order ID
        order_id = self.order_tree.item(selected_items[0])['values'][0]

        try:
            # Retrieve order details
            order = self.order_service.get_order_by_id(order_id)

            if not order:
                messagebox.showwarning("Edit Order", "Could not retrieve order details.")
                return

            # Get suppliers for the dialog
            suppliers = self.supplier_service.get_all_suppliers()

            # Create and show edit order dialog
            from store_management.gui.order.order_dialog import AddOrderDialog
            dialog = AddOrderDialog(
                self,
                self._save_edited_order,
                existing_data=order,
                suppliers=suppliers,
                title="Edit Order"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load order for editing: {str(e)}")

    def _save_edited_order(self, order_data: Dict[str, Any]):
        """
        Save edited order details.

        Args:
            order_data: Updated order information
        """
        try:
            # Call order service to update order
            result = self.order_service.update_order(order_data)

            if result:
                messagebox.showinfo("Success", "Order updated successfully")
                # Refresh order list
                self.load_data()
            else:
                messagebox.showerror("Error", "Failed to update order")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update order: {str(e)}")

    def delete_order(self):
        """Delete the selected order."""
        selected_items = self.order_tree.selection()
        if not selected_items:
            messagebox.showwarning("Delete Order", "Please select an order to delete.")
            return

        # Get selected order ID
        order_id = self.order_tree.item(selected_items[0])['values'][0]

        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete order {order_id}?"
        )

        if confirm:
            try:
                # Call order service to delete order
                result = self.order_service.delete_order(order_id)

                if result:
                    messagebox.showinfo("Success", "Order deleted successfully")
                    # Refresh order list
                    self.load_data()
                else:
                    messagebox.showerror("Error", "Failed to delete order")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete order: {str(e)}")

    def _show_search_dialog(self):
        """Show search dialog for orders."""
        messagebox.showinfo("Search", "Order search functionality not implemented yet.")

    def save(self):
        """Save current view data."""
        messagebox.showinfo("Save", "Save functionality not implemented yet.")

    def undo(self):
        """Undo the last action."""
        messagebox.showinfo("Undo", "Undo functionality not implemented yet.")

    def redo(self):
        """Redo the last undone action."""
        messagebox.showinfo("Redo", "Redo functionality not implemented yet.")

    def cleanup(self):
        """Perform cleanup when view is closed."""
        # Any necessary cleanup operations
        pass