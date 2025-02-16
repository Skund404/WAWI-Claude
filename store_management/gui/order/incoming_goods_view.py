import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional
import uuid
from datetime import datetime

from database.db_manager import DatabaseManager
from config import DATABASE_PATH, TABLES, COLORS


class IncomingGoodsView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.db = DatabaseManager(DATABASE_PATH)

        # Initialize undo/redo stacks
        self.undo_stack = []
        self.redo_stack = []

        # Current selected order
        self.current_order = None

        # Setup UI components
        self.setup_toolbar()
        self.setup_tables()
        self.load_data()

    def setup_toolbar(self):
        """Create the toolbar with all buttons"""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Left side buttons
        ttk.Button(toolbar, text="ADD Order",
                   command=self.show_add_order_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Search",
                   command=self.show_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Filter",
                   command=self.show_filter_dialog).pack(side=tk.LEFT, padx=2)

        # Center buttons
        ttk.Button(toolbar, text="Finish Order & Add to Storage",
                   command=self.finish_order).pack(side=tk.LEFT, padx=20)

        # Right side buttons
        ttk.Button(toolbar, text="Undo", command=self.undo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Redo", command=self.redo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Load", command=self.load_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Reset View",
                   command=self.reset_view).pack(side=tk.RIGHT, padx=2)

    def setup_tables(self):
        """Create both table views"""
        # Create container for both tables
        tables_frame = ttk.Frame(self)
        tables_frame.pack(expand=True, fill='both', padx=5, pady=5)

        # Setup Orders table
        orders_frame = ttk.LabelFrame(tables_frame, text="Orders")
        orders_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.orders_columns = [
            'supplier', 'date_of_order', 'status', 'order_number', 'payed'
        ]

        self.orders_tree = self.create_treeview(
            orders_frame,
            self.orders_columns,
            self.on_order_select
        )

        # Setup Order Details table
        details_frame = ttk.LabelFrame(tables_frame, text="Order Details")
        details_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.details_columns = [
            'article', 'price', 'amount', 'total', 'unique_id', 'notes'
        ]

        self.details_tree = self.create_treeview(
            details_frame,
            self.details_columns
        )

    def create_treeview(self, parent, columns, select_callback=None):
        """Create a treeview with scrollbars"""
        frame = ttk.Frame(parent)
        frame.pack(expand=True, fill='both')

        # Create scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical")
        hsb = ttk.Scrollbar(frame, orient="horizontal")

        # Create treeview
        tree = ttk.Treeview(
            frame,
            columns=columns,
            show='headings',
            selectmode='extended',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        # Configure scrollbars
        vsb.configure(command=tree.yview)
        hsb.configure(command=tree.xview)

        # Setup headers and columns
        for col in columns:
            tree.heading(col, text=col.replace('_', ' ').title(),
                         command=lambda c=col: self.sort_column(tree, c))
            tree.column(col, width=100, minwidth=50)

        # Grid layout
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        # Bind events
        tree.bind('<Double-1>', lambda e: self.on_double_click(tree, e))
        tree.bind('<Delete>', lambda e: self.delete_selected(tree))

        if select_callback:
            tree.bind('<<TreeviewSelect>>', select_callback)

        return tree

    def show_add_order_dialog(self):
        """Show dialog for adding new order"""
        dialog = tk.Toplevel(self)
        dialog.title("Add New Order")
        dialog.transient(self)
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky='nsew')

        # Get suppliers list
        self.db.connect()
        suppliers = self.db.execute_query(
            "SELECT company_name FROM supplier ORDER BY company_name"
        )
        self.db.disconnect()

        # Create fields
        fields = {}

        # Supplier dropdown
        ttk.Label(main_frame, text="Supplier:").grid(row=0, column=0, sticky='w')
        supplier_var = tk.StringVar()
        supplier_combo = ttk.Combobox(main_frame, textvariable=supplier_var)
        supplier_combo['values'] = ['Add New Supplier'] + \
                                   [s[0] for s in suppliers] if suppliers else []
        supplier_combo.grid(row=0, column=1, sticky='ew')
        fields['supplier'] = supplier_var

        def handle_supplier_selection(*args):
            if supplier_var.get() == 'Add New Supplier':
                # Call add supplier function from supplier view
                # To be implemented
                pass

        supplier_var.trace('w', handle_supplier_selection)

        # Date of order
        ttk.Label(main_frame, text="Date of Order:").grid(row=1, column=0, sticky='w')
        date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ttk.Entry(main_frame, textvariable=date_var).grid(row=1, column=1, sticky='ew')
        fields['date_of_order'] = date_var

        # Status dropdown
        ttk.Label(main_frame, text="Status:").grid(row=2, column=0, sticky='w')
        status_var = tk.StringVar(value='ordered')
        status_combo = ttk.Combobox(main_frame, textvariable=status_var)
        status_combo['values'] = ['ordered', 'being processed', 'shipped',
                                  'received', 'returned', 'partially returned']
        status_combo.grid(row=2, column=1, sticky='ew')
        fields['status'] = status_var

        # Order number
        ttk.Label(main_frame, text="Order Number:").grid(row=3, column=0, sticky='w')
        order_num_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=order_num_var).grid(row=3, column=1, sticky='ew')
        fields['order_number'] = order_num_var

        # Payment status
        ttk.Label(main_frame, text="Payed:").grid(row=4, column=0, sticky='w')
        payed_var = tk.StringVar(value='no')
        payed_combo = ttk.Combobox(main_frame, textvariable=payed_var)
        payed_combo['values'] = ['yes', 'no']
        payed_combo.grid(row=4, column=1, sticky='ew')
        fields['payed'] = payed_var

        def validate_and_save():
            """Validate fields and save order"""
            # Validate required fields
            if not all([fields['supplier'].get(), fields['order_number'].get()]):
                messagebox.showerror("Error", "Supplier and Order Number are required")
                return

            # Create order data
            order_data = {
                field: var.get() for field, var in fields.items()
            }

            try:
                self.db.connect()
                # Insert order
                if self.db.insert_record(TABLES['ORDERS'], order_data):
                    # Create order details table
                    table_name = f"{order_data['supplier']}_{order_data['order_number']}"
                    # Ensure unique table name
                    suffix = 1
                    original_name = table_name
                    while self.table_exists(table_name):
                        table_name = f"{original_name}_{suffix}"
                        suffix += 1

                    # Create details table
                    self.create_order_details_table(table_name)

                    # Store for undo
                    self.undo_stack.append(('add_order', order_data, table_name))
                    self.redo_stack.clear()

                    # Refresh data
                    self.load_data()

                    # Show details dialog
                    self.show_order_details_dialog(order_data, table_name)

                    dialog.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to create order: {str(e)}")
            finally:
                self.db.disconnect()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Continue",
                   command=validate_and_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel",
                   command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def create_order_details_table(self, table_name: str):
        """Create table for order details"""
        query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                article TEXT NOT NULL,
                price REAL NOT NULL,
                amount INTEGER NOT NULL,
                total REAL NOT NULL,
                unique_id TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.db.execute_query(query)

    def show_order_details_dialog(self, order_data: Dict, table_name: str):
        """Show dialog for entering order details"""
        dialog = tk.Toplevel(self)
        dialog.title("Order Details")
        dialog.transient(self)
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky='nsew')

        # Create entry fields
        entries = {}

        # Get parts and leather items
        self.db.connect()
        parts = self.db.execute_query(
            "SELECT unique_id_parts, name FROM sorting_system ORDER BY name"
        )
        leather = self.db.execute_query(
            "SELECT unique_id_leather, name FROM shelf ORDER BY name"
        )
        self.db.disconnect()

        # Fields
        row = 0

        # Article selection
        ttk.Label(main_frame, text="Unique ID:").grid(row=row, column=0, sticky='w')
        id_var = tk.StringVar()
        id_combo = ttk.Combobox(main_frame, textvariable=id_var)
        id_combo['values'] = ['Add Part', 'Add Leather'] + \
                             [f"{p[0]} - {p[1]}" for p in parts] + \
                             [f"{l[0]} - {l[1]}" for l in leather]
        id_combo.grid(row=row, column=1, sticky='ew')
        entries['unique_id'] = id_var

        # Other fields
        fields = ['price', 'amount', 'notes']
        for field in fields:
            row += 1
            ttk.Label(main_frame, text=field.title() + ":").grid(
                row=row, column=0, sticky='w'
            )
            var = tk.StringVar()
            ttk.Entry(main_frame, textvariable=var).grid(
                row=row, column=1, sticky='ew'
            )
            entries[field] = var

        # Additional fields
        row += 1
        ttk.Label(main_frame, text="Shipping Cost:").grid(
            row=row, column=0, sticky='w'
        )
        shipping_var = tk.StringVar(value="0.0")
        ttk.Entry(main_frame, textvariable=shipping_var).grid(
            row=row, column=1, sticky='ew'
        )

        row += 1
        ttk.Label(main_frame, text="Discount:").grid(
            row=row, column=0, sticky='w'
        )
        discount_var = tk.StringVar(value="0.0")
        ttk.Entry(main_frame, textvariable=discount_var).grid(
            row=row, column=1, sticky='ew'
        )

        def save_details():
            """Save order details"""
            try:
                # Validate numeric fields
                try:
                    price = float(entries['price'].get())
                    amount = int(entries['amount'].get())
                    shipping = float(shipping_var.get())
                    discount = float(discount_var.get())
                except ValueError:
                    messagebox.showerror(
                        "Error",
                        "Price, Amount, Shipping Cost, and Discount must be numbers"
                    )
                    return

                # Calculate total
                total = price * amount

                # Create details data
                details_data = {
                    'article': id_var.get().split(' - ')[1],
                    'price': price,
                    'amount': amount,
                    'total': total,
                    'unique_id': id_var.get().split(' - ')[0],
                    'notes': entries['notes'].get()
                }

                self.db.connect()
                # Insert details
                if self.db.insert_record(table_name, details_data):
                    # Add shipping and discount rows
                    if float(shipping_var.get()) > 0:
                        shipping_data = {
                            'article': 'Shipping',
                            'price': float(shipping_var.get()),
                            'amount': 1,
                            'total': float(shipping_var.get()),
                            'unique_id': '',
                            'notes': ''
                        }
                        self.db.insert_record(table_name, shipping_data)

                    if float(discount_var.get()) > 0:
                        discount_data = {
                            'article': 'Discount',
                            'price': -float(discount_var.get()),
                            'amount': 1,
                            'total': -float(discount_var.get()),
                            'unique_id': '',
                            'notes': ''
                        }
                        self.db.insert_record(table_name, discount_data)

                    # Calculate and add total row
                    total_query = f"SELECT SUM(total) FROM {table_name}"
                    result = self.db.execute_query(total_query)
                    grand_total = result[0][0] if result else 0

                    total_data = {
                        'article': 'TOTAL',
                        'price': grand_total,
                        'amount': 1,
                        'total': grand_total,
                        'unique_id': '',
                        'notes': ''
                    }
                    self.db.insert_record(table_name, total_data)

                    # Refresh details view
                    self.load_order_details(order_data['order_number'])
                    dialog.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save details: {str(e)}")
            finally:
                self.db.disconnect()

                # Buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=row + 1, column=0, columnspan=2, pady=10)

            ttk.Button(button_frame, text="Add",
                       command=save_details).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel",
                       command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        def finish_order(self):
            """Process completed order and update inventory"""
            if not self.current_order:
                messagebox.showwarning("Warning", "Please select an order")
                return

            # Get current order status
            self.db.connect()
            try:
                order = self.db.execute_query(
                    "SELECT status FROM orders WHERE order_number = ?",
                    (self.current_order,)
                )

                if not order or order[0][0] == 'completed':
                    messagebox.showwarning("Warning", "Invalid order or already completed")
                    return

                # Get order details
                details = self.get_order_details(self.current_order)

                if not details:
                    messagebox.showwarning("Warning", "No items in order")
                    return

                # Update inventory
                for item in details:
                    if not item['unique_id']:  # Skip shipping, discount, total rows
                        continue

                    if item['unique_id'].startswith('L'):  # Leather item
                        self.update_leather_inventory(item)
                    else:  # Part item
                        self.update_part_inventory(item)

                # Update order status
                self.db.update_record(
                    TABLES['ORDERS'],
                    {'status': 'completed'},
                    "order_number = ?",
                    (self.current_order,)
                )

                # Refresh views
                self.load_data()
                messagebox.showinfo("Success", "Order processed and inventory updated")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to process order: {str(e)}")
            finally:
                self.db.disconnect()

        def update_leather_inventory(self, item: Dict):
            """Update leather inventory"""
            current = self.db.execute_query(
                "SELECT amount FROM shelf WHERE unique_id_leather = ?",
                (item['unique_id'],)
            )

            if current:
                new_amount = current[0][0] + item['amount']
                self.db.update_record(
                    'shelf',
                    {'amount': new_amount},
                    "unique_id_leather = ?",
                    (item['unique_id'],)
                )

        def update_part_inventory(self, item: Dict):
            """Update parts inventory"""
            current = self.db.execute_query(
                "SELECT in_storage FROM sorting_system WHERE unique_id_parts = ?",
                (item['unique_id'],)
            )

            if current:
                new_amount = current[0][0] + item['amount']
                self.db.update_record(
                    'sorting_system',
                    {'in_storage': new_amount},
                    "unique_id_parts = ?",
                    (item['unique_id'],)
                )

        def get_order_details(self, order_number: str) -> List[Dict]:
            """Get details for an order"""
            # Find details table name
            table_name = None
            tables = self.db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
            for table in tables:
                if order_number in table[0]:
                    table_name = table[0]
                    break

            if not table_name:
                return []

            # Get details
            details = self.db.execute_query(f"SELECT * FROM {table_name}")
            if not details:
                return []

            return [
                {
                    'unique_id': row[4],
                    'amount': row[2]
                }
                for row in details
                if row[4]  # Only return rows with unique_id
            ]

        def on_order_select(self, event):
            """Handle selection in orders table"""
            selection = self.orders_tree.selection()
            if not selection:
                return

            # Get selected order number
            item = selection[0]
            order_number = self.orders_tree.item(item)['values'][3]  # order_number column

            # Load order details
            self.load_order_details(order_number)
            self.current_order = order_number

        def load_order_details(self, order_number: str):
            """Load details for selected order"""
            # Clear existing items
            for item in self.details_tree.get_children():
                self.details_tree.delete(item)

            # Find details table
            self.db.connect()
            try:
                tables = self.db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
                table_name = None
                for table in tables:
                    if order_number in table[0]:
                        table_name = table[0]
                        break

                if table_name:
                    details = self.db.execute_query(f"SELECT * FROM {table_name}")
                    if details:
                        for row in details:
                            self.details_tree.insert('', 'end', values=row[:-2])

            finally:
                self.db.disconnect()

        def load_data(self):
            """Load data into orders table"""
            self.db.connect()
            try:
                query = "SELECT * FROM orders ORDER BY date_of_order DESC"
                results = self.db.execute_query(query)

                # Clear existing items
                for item in self.orders_tree.get_children():
                    self.orders_tree.delete(item)

                # Insert new data
                for row in results:
                    self.orders_tree.insert('', 'end', values=row[:-2])

            finally:
                self.db.disconnect()

        # ... (Other methods like sort_column, undo/redo, etc. follow the same pattern
        # as in previous views)