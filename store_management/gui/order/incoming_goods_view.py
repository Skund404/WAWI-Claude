# Add these imports at the top of the file
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional, Any
import uuid
import sqlite3  # Add this import
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)

from store_management.database.db_manager import DatabaseManager
from store_management.config import TABLES, COLORS
from store_management.utils.validators import OrderValidator, DataSanitizer
from store_management.utils.exporters import OrderExporter, OrderImporter
from store_management.utils.backup import DatabaseBackup
from store_management.utils.notifications import StatusNotification
from store_management.config import get_database_path



class IncomingGoodsView(ttk.Frame):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # Initialize database manager
        self.db = DatabaseManager(get_database_path())

        # Initialize utilities
        self.backup = DatabaseBackup(get_database_path())
        self.notifications = StatusNotification(self)

        # Initialize undo/redo stacks
        self.undo_stack = []
        self.redo_stack = []

        # Current selected order
        self.current_order = None

        # Track modified state
        self.modified = False

        # Setup UI components
        self.create_ui()

        # Load initial data
        self.load_data()

        # Bind events
        self.bind_events()



    def create_ui(self):
        """Create the complete user interface"""
        # Create main layout
        self.create_toolbar()
        self.create_main_content()
        self.create_status_bar()

    def create_toolbar(self):
        """Create the main toolbar"""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Left side buttons
        left_frame = ttk.Frame(toolbar)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Button(
            left_frame,
            text="ADD Order",
            command=self.show_add_order_dialog
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            left_frame,
            text="Search",
            command=self.show_search_dialog
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            left_frame,
            text="Filter",
            command=self.show_filter_dialog
        ).pack(side=tk.LEFT, padx=2)

        # Center buttons
        center_frame = ttk.Frame(toolbar)
        center_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20)

        ttk.Button(
            center_frame,
            text="Finish Order & Add to Storage",
            command=self.finish_order
        ).pack(side=tk.LEFT)

        # Right side buttons
        right_frame = ttk.Frame(toolbar)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Import/Export buttons
        ttk.Button(
            right_frame,
            text="Export",
            command=self.show_export_dialog
        ).pack(side=tk.RIGHT, padx=2)

        ttk.Button(
            right_frame,
            text="Import",
            command=self.show_import_dialog
        ).pack(side=tk.RIGHT, padx=2)

        ttk.Separator(
            right_frame,
            orient=tk.VERTICAL
        ).pack(side=tk.RIGHT, padx=5, fill=tk.Y)

        # Standard buttons
        ttk.Button(
            right_frame,
            text="Undo",
            command=self.undo
        ).pack(side=tk.RIGHT, padx=2)

        ttk.Button(
            right_frame,
            text="Redo",
            command=self.redo
        ).pack(side=tk.RIGHT, padx=2)

        ttk.Button(
            right_frame,
            text="Save",
            command=self.save_changes
        ).pack(side=tk.RIGHT, padx=2)

        ttk.Button(
            right_frame,
            text="Reset View",
            command=self.reset_view
        ).pack(side=tk.RIGHT, padx=2)

    def create_main_content(self):
        """Create the main content area"""
        # Create container for both tables
        self.paned_window = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned_window.pack(expand=True, fill='both', padx=5, pady=5)

        # Create frames for tables
        orders_frame = ttk.LabelFrame(self.paned_window, text="Orders")
        details_frame = ttk.LabelFrame(self.paned_window, text="Order Details")

        self.paned_window.add(orders_frame, weight=1)
        self.paned_window.add(details_frame, weight=1)

        # Create orders table
        self.create_orders_table(orders_frame)

        # Create details table
        self.create_details_table(details_frame)

    def create_orders_table(self, parent):
        """Create the orders table"""
        # Define columns
        self.orders_columns = [
            'order_number',
            'supplier',
            'date_of_order',
            'status',
            'payed',
            'total_amount'
        ]

        # Create treeview with scrollbars
        table_frame = ttk.Frame(parent)
        table_frame.pack(expand=True, fill='both', padx=5, pady=5)

        self.orders_tree = self.create_treeview(
            table_frame,
            self.orders_columns,
            self.on_order_select
        )

    def create_details_table(self, parent):
        """Create the order details table with Add Item button"""
        # Create frame for button and table
        details_frame = ttk.Frame(parent)
        details_frame.pack(expand=True, fill='both', padx=5, pady=5)

        # Add Item button frame
        button_frame = ttk.Frame(details_frame)
        button_frame.pack(fill='x', pady=(0, 5))

        ttk.Button(
            button_frame,
            text="Add Item",
            command=self.show_add_item_dialog
        ).pack(side=tk.LEFT, padx=2)

        # Define columns
        self.details_columns = [
            'article',
            'unique_id',
            'price',
            'amount',
            'total',
            'notes'
        ]

        # Create treeview with scrollbars
        table_frame = ttk.Frame(details_frame)
        table_frame.pack(expand=True, fill='both')

        self.details_tree = self.create_treeview(
            table_frame,
            self.details_columns
        )

    def show_add_item_dialog(self):
        """Show dialog for adding an item to the order"""
        if not self.current_order:
            self.notifications.show_warning("Please select an order first")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Add Item to Order")
        dialog.transient(self)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill='both', expand=True)

        # Article Selection Section
        ttk.Label(main_frame, text="Article:").pack(anchor='w')

        def get_combined_items():
            """Get list of items from both shelf and sorting system"""
            try:
                self.db.connect()

                # Get shelf items
                shelf_items = self.db.execute_query(
                    "SELECT name, unique_id_leather FROM shelf ORDER BY name"
                )

                # Get sorting system items
                sorting_items = self.db.execute_query(
                    "SELECT name, unique_id_parts FROM sorting_system ORDER BY name"
                )

                # Combine items with special options at top
                items = ["+ Add New Sorting System Part", "+ Add New Shelf Part"]

                # Add existing items with their sources
                if shelf_items:
                    items.extend([f"{item[0]} (Shelf)" for item in shelf_items])
                if sorting_items:
                    items.extend([f"{item[0]} (Parts)" for item in sorting_items])

                # Store mapping of display names to IDs
                self.item_id_mapping = {}
                for item in shelf_items:
                    self.item_id_mapping[f"{item[0]} (Shelf)"] = ('shelf', item[1])
                for item in sorting_items:
                    self.item_id_mapping[f"{item[0]} (Parts)"] = ('sorting', item[1])

                return items

            except Exception as e:
                self.notifications.show_error(f"Failed to fetch items: {str(e)}")
                return ["+ Add New Sorting System Part", "+ Add New Shelf Part"]
            finally:
                self.db.disconnect()

        def on_article_select(event):
            """Handle article selection"""
            selected = article_combo.get()

            if selected == "+ Add New Sorting System Part":
                dialog.destroy()
                # Show sorting system add dialog
                from store_management.gui.sorting_system_view import SortingSystemView
                SortingSystemView.show_add_part_dialog(self)
                # Reopen this dialog after adding
                self.show_add_item_dialog()

            elif selected == "+ Add New Shelf Part":
                dialog.destroy()
                # Show shelf add dialog
                from store_management.gui.shelf_view import ShelfView
                ShelfView.show_add_leather_dialog(self)
                # Reopen this dialog after adding
                self.show_add_item_dialog()

            else:
                # Update unique ID when an existing item is selected
                if selected in self.item_id_mapping:
                    source, unique_id = self.item_id_mapping[selected]
                    unique_id_var.set(unique_id)

                    # Clear and disable unique ID field
                    unique_id_entry.configure(state='readonly')

        article_var = tk.StringVar()
        article_combo = ttk.Combobox(
            main_frame,
            textvariable=article_var,
            values=get_combined_items(),
            state='readonly'
        )
        article_combo.pack(fill='x', pady=5)
        article_combo.bind('<<ComboboxSelected>>', on_article_select)

        # Unique ID field
        ttk.Label(main_frame, text="Unique ID:").pack(anchor='w')
        unique_id_var = tk.StringVar()
        unique_id_entry = ttk.Entry(
            main_frame,
            textvariable=unique_id_var,
            state='readonly'
        )
        unique_id_entry.pack(fill='x', pady=5)

        # Price field
        ttk.Label(main_frame, text="Price:").pack(anchor='w')
        price_var = tk.StringVar(value="0.0")
        price_entry = ttk.Entry(main_frame, textvariable=price_var)
        price_entry.pack(fill='x', pady=5)

        # Amount field
        ttk.Label(main_frame, text="Amount:").pack(anchor='w')
        amount_var = tk.StringVar(value="1")
        amount_spinbox = ttk.Spinbox(
            main_frame,
            from_=1,
            to=1000,
            textvariable=amount_var
        )
        amount_spinbox.pack(fill='x', pady=5)

        # Notes field
        ttk.Label(main_frame, text="Notes:").pack(anchor='w')
        notes_var = tk.StringVar()
        notes_entry = ttk.Entry(main_frame, textvariable=notes_var)
        notes_entry.pack(fill='x', pady=5)

        def add_item():
            """Add item to order details"""
            if not article_var.get() or article_var.get() in ["+ Add New Sorting System Part", "+ Add New Shelf Part"]:
                self.notifications.show_error("Please select an article")
                return

            try:
                price = float(price_var.get())
                amount = int(amount_var.get())

                if price < 0:
                    self.notifications.show_error("Price must be non-negative")
                    return
                if amount < 1:
                    self.notifications.show_error("Amount must be at least 1")
                    return

                # Calculate total
                total = price * amount

                # Create item data
                article_name = article_var.get().split(" (")[0]  # Remove the (Shelf)/(Parts) suffix
                item_data = {
                    'article': article_name,
                    'unique_id': unique_id_var.get(),
                    'price': price,
                    'amount': amount,
                    'total': total,
                    'notes': notes_var.get()
                }

                # Insert into database
                table_name = f"order_details_{self.current_order}"
                self.db.connect()
                if self.db.insert_record(table_name, item_data):
                    # Refresh details view
                    self.load_order_details(self.current_order)
                    dialog.destroy()
                    self.notifications.show_success("Item added successfully")
                else:
                    raise Exception("Failed to add item to database")

            except ValueError as e:
                self.notifications.show_error("Invalid price or amount value")
            except Exception as e:
                self.notifications.show_error(f"Failed to add item: {str(e)}")
            finally:
                self.db.disconnect()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(
            button_frame,
            text="Add",
            command=add_item
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

    def create_treeview(self, parent, columns, select_callback=None):
        """Create a treeview with scrollbars"""
        # Create scrollbars
        vsb = ttk.Scrollbar(parent, orient="vertical")
        hsb = ttk.Scrollbar(parent, orient="horizontal")

        # Create treeview
        tree = ttk.Treeview(
            parent,
            columns=columns,
            show='headings',
            selectmode='extended',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        # Configure scrollbars
        vsb.configure(command=tree.yview)
        hsb.configure(command=tree.xview)

        # Setup headings and columns
        for col in columns:
            tree.heading(
                col,
                text=col.replace('_', ' ').title(),
                command=lambda c=col: self.sort_column(tree, c)
            )

            # Set column width based on content type
            if col in ['notes', 'article']:
                width = 200
            elif col in ['unique_id', 'order_number']:
                width = 150
            else:
                width = 100

            tree.column(col, width=width, minwidth=50)

        # Grid layout
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        # Bind events
        tree.bind('<Double-1>', lambda e: self.on_double_click(tree, e))
        tree.bind('<Delete>', lambda e: self.delete_selected(tree))

        if select_callback:
            tree.bind('<<TreeviewSelect>>', select_callback)

        return tree

    def create_status_bar(self):
        """Create the status bar"""
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Status label
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Order count
        self.order_count = ttk.Label(status_frame, text="Orders: 0")
        self.order_count.pack(side=tk.RIGHT, padx=5)

    def show_add_order_dialog(self):
        """Show dialog for adding a new order"""
        dialog = tk.Toplevel(self)
        dialog.title("Add New Order")
        dialog.transient(self)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill='both', expand=True)

        # Create input fields
        fields = {}

        # Order Number (user input)
        ttk.Label(main_frame, text="Order Number:").pack(anchor='w')
        order_number = tk.StringVar()
        ttk.Entry(main_frame, textvariable=order_number).pack(fill='x', pady=5)
        fields['order_number'] = order_number

        # Supplier Selection
        ttk.Label(main_frame, text="Supplier:").pack(anchor='w')

        def get_suppliers():
            """Get list of suppliers from database with 'Add New Supplier' option"""
            try:
                self.db.connect()
                query = f"SELECT company_name FROM supplier ORDER BY company_name"
                results = self.db.execute_query(query)
                # Add the "Add New Supplier" option at the top
                suppliers = ["+ Add New Supplier"]
                suppliers.extend([result[0] for result in results] if results else [])
                return suppliers
            except Exception as e:
                self.notifications.show_error(f"Failed to fetch suppliers: {str(e)}")
                return ["+ Add New Supplier"]  # Return at least the add option
            finally:
                self.db.disconnect()

        def on_supplier_select(event):
            """Handle supplier selection"""
            if supplier_combo.get() == "+ Add New Supplier":
                # Create add supplier dialog
                add_dialog = tk.Toplevel(dialog)
                add_dialog.title("Add New Supplier")
                add_dialog.transient(dialog)
                add_dialog.grab_set()

                # Add supplier frame
                add_frame = ttk.Frame(add_dialog, padding="10")
                add_frame.pack(fill='both', expand=True)

                ttk.Label(add_frame, text="Company Name:").pack(anchor='w')
                new_supplier = tk.StringVar()
                ttk.Entry(add_frame, textvariable=new_supplier).pack(fill='x', pady=5)

                def save_supplier():
                    company_name = new_supplier.get().strip()
                    if not company_name:
                        self.notifications.show_warning("Please enter a company name")
                        return

                    try:
                        self.db.connect()
                        # Check if supplier exists
                        exists = self.db.execute_query(
                            f"SELECT company_name FROM supplier WHERE company_name = ?",
                            (company_name,)
                        )

                        if exists:
                            self.notifications.show_warning("Supplier already exists")
                            return

                        # Insert new supplier
                        supplier_data = {
                            'company_name': company_name,
                            'date_added': datetime.now().strftime('%Y-%m-%d')
                        }

                        if self.db.insert_record('supplier', supplier_data):
                            # Update supplier list and select new supplier
                            suppliers = get_suppliers()
                            supplier_combo['values'] = suppliers
                            supplier_combo.set(company_name)
                            add_dialog.destroy()
                            self.notifications.show_success("Supplier added successfully")
                        else:
                            raise Exception("Failed to add supplier")

                    except Exception as e:
                        self.notifications.show_error(f"Failed to add supplier: {str(e)}")
                    finally:
                        self.db.disconnect()

                # Add supplier dialog buttons
                button_frame = ttk.Frame(add_frame)
                button_frame.pack(fill='x', pady=10)

                ttk.Button(
                    button_frame,
                    text="Save",
                    command=save_supplier
                ).pack(side=tk.LEFT, padx=5)

                ttk.Button(
                    button_frame,
                    text="Cancel",
                    command=lambda: [add_dialog.destroy(), supplier_combo.set('')]
                ).pack(side=tk.LEFT, padx=5)

        supplier = tk.StringVar()
        supplier_combo = ttk.Combobox(
            main_frame,
            textvariable=supplier,
            values=get_suppliers(),
            state='readonly'
        )
        supplier_combo.pack(fill='x', pady=5)
        supplier_combo.bind('<<ComboboxSelected>>', on_supplier_select)
        fields['supplier'] = supplier

        # Date
        ttk.Label(main_frame, text="Date of Order:").pack(anchor='w')
        date = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ttk.Entry(main_frame, textvariable=date).pack(fill='x', pady=5)
        fields['date_of_order'] = date

        # Status
        ttk.Label(main_frame, text="Status:").pack(anchor='w')
        status = tk.StringVar(value='ordered')
        status_combo = ttk.Combobox(main_frame, textvariable=status)
        status_combo['values'] = ['ordered', 'being processed', 'shipped',
                                  'received', 'returned', 'partially returned', 'completed']
        status_combo.pack(fill='x', pady=5)
        fields['status'] = status

        # Payment Status
        ttk.Label(main_frame, text="Payment Status:").pack(anchor='w')
        payed = tk.StringVar(value='no')
        payment_combo = ttk.Combobox(main_frame, textvariable=payed)
        payment_combo['values'] = ['yes', 'no']
        payment_combo.pack(fill='x', pady=5)
        fields['payed'] = payed

        # Total Amount
        ttk.Label(main_frame, text="Total Amount:").pack(anchor='w')
        total_amount = tk.StringVar(value='0.0')
        total_entry = ttk.Entry(main_frame, textvariable=total_amount)
        total_entry.pack(fill='x', pady=5)
        fields['total_amount'] = total_amount

        def validate_fields():
            """Validate input fields"""
            if not order_number.get().strip():
                self.notifications.show_error("Please enter an order number")
                return False

            if not supplier.get() or supplier.get() == "+ Add New Supplier":
                self.notifications.show_error("Please select a supplier")
                return False

            try:
                amount = float(total_amount.get())
                if amount < 0:
                    self.notifications.show_error("Total amount must be non-negative")
                    return False
            except ValueError:
                self.notifications.show_error("Total amount must be a valid number")
                return False

            try:
                datetime.strptime(date.get(), '%Y-%m-%d')
            except ValueError:
                self.notifications.show_error("Invalid date format (YYYY-MM-DD)")
                return False

            return True

        def create_order():
            """Handle order creation"""
            if not validate_fields():
                return

            try:
                # Create order data
                order_data = {
                    'order_number': order_number.get().strip(),
                    'supplier': supplier.get(),
                    'date_of_order': date.get(),
                    'status': status.get(),
                    'payed': payed.get(),
                    'total_amount': float(total_amount.get())
                }

                # Create backup before adding
                self.backup.create_backup('add_order')

                # Insert order
                self.db.connect()
                if self.db.insert_record('orders', order_data):
                    # Create details table
                    table_name = f"order_details_{order_data['order_number']}"
                    self.create_order_details_table(table_name)

                    # Refresh view
                    self.load_data()

                    # Show details dialog
                    dialog.destroy()
                    self.show_order_details_dialog(order_data, table_name)

                    self.notifications.show_success("Order created successfully")

            except Exception as e:
                self.notifications.show_error(f"Failed to create order: {str(e)}")
                # Attempt to restore from backup
                self.backup.restore_backup()
            finally:
                self.db.disconnect()

        # Main dialog buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(
            button_frame,
            text="Create",
            command=create_order
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

    def create_order_details_table(self, table_name: str):
        """Create table for order details"""
        logging.info(f"Creating order details table: {table_name}")
        query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                article TEXT NOT NULL,
                unique_id TEXT,
                price REAL NOT NULL,
                amount INTEGER NOT NULL,
                total REAL NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        try:
            self.db.execute_query(query)
            logging.info(f"Successfully created table: {table_name}")
        except Exception as e:
            logging.error(f"Error creating order details table: {str(e)}")
            raise

    def bind_events(self):
        """Bind global events"""
        # Keyboard shortcuts
        self.bind_all('<Control-z>', self.undo)
        self.bind_all('<Control-y>', self.redo)
        self.bind_all('<Control-s>', self.save_changes)
        self.bind_all('<F5>', self.reset_view)
        self.bind_all('<Delete>', lambda e: self.delete_selected(self.get_focused_tree()))

    def get_focused_tree(self):
        """Get the currently focused treeview"""
        focus = self.focus_get()
        if focus == self.orders_tree:
            return self.orders_tree
        elif focus == self.details_tree:
            return self.details_tree
        return None

    def on_order_select(self, event):
        """Handle selection in orders table"""
        selection = self.orders_tree.selection()
        if not selection:
            return

        # Get selected order number
        item = selection[0]
        values = self.orders_tree.item(item)['values']
        order_number = values[0]  # order_number is first column

        # Load order details
        self.load_order_details(order_number)
        self.current_order = order_number

    def load_data(self):
        """Load orders data"""
        try:
            self.db.connect()
            query = """
                SELECT 
                    order_number, supplier, date_of_order, 
                    status, payed, total_amount
                FROM orders 
                ORDER BY date_of_order DESC
            """
            results = self.db.execute_query(query)

            # Clear existing items
            for item in self.orders_tree.get_children():
                self.orders_tree.delete(item)

            # Insert data
            for row in results:
                self.orders_tree.insert('', 'end', values=row)

            # Update order count
            self.order_count.configure(text=f"Orders: {len(results)}")

        except Exception as e:
            self.notifications.show_error(f"Failed to load orders: {str(e)}")
        finally:
            self.db.disconnect()

    def load_order_details(self, order_number: str):
        """Load details for selected order"""
        try:
            # Clear existing items
            for item in self.details_tree.get_children():
                self.details_tree.delete(item)

            self.db.connect()
            # Find details table
            table_name = f"order_details_{order_number}"
            if self.table_exists(table_name):
                query = f"""
                    SELECT 
                        article, unique_id, price, 
                        amount, total, notes
                    FROM {table_name}
                """
                details = self.db.execute_query(query)

                # Insert data
                for row in details:
                    self.details_tree.insert('', 'end', values=row)

        except Exception as e:
            self.notifications.show_error(f"Failed to load order details: {str(e)}")
        finally:
            self.db.disconnect()

    def finish_order(self):
        """Process completed order and update inventory"""
        if not self.current_order:
            self.notifications.show_warning("Please select an order")
            return

        try:
            self.db.connect()
            # Check order status
            order = self.db.execute_query(
                "SELECT status FROM orders WHERE order_number = ?",
                (self.current_order,)
            )

            if not order or order[0][0] == 'completed':
                self.notifications.show_warning("Invalid order or already completed")
                return

            # Create backup
            self.backup.create_backup('complete_order')

            # Get order details
            table_name = f"order_details_{self.current_order}"
            details = self.db.execute_query(f"SELECT * FROM {table_name}")

            if not details:
                self.notifications.show_warning("No items in order")
                return

            # Update inventory
            for row in details:
                unique_id = row[1]  # unique_id column
                amount = row[3]  # amount column

                if not unique_id:  # Skip non-inventory items
                    continue

                if unique_id.startswith('L'):
                    # Update leather inventory
                    self.update_leather_inventory(unique_id, amount)
                else:
                    # Update parts inventory
                    self.update_parts_inventory(unique_id, amount)

            # Update order status
            self.db.update_record(
                TABLES['ORDERS'],
                {'status': 'completed'},
                "order_number = ?",
                (self.current_order,)
            )

            # Refresh views
            self.load_data()
            if self.current_order:
                self.load_order_details(self.current_order)

            self.notifications.show_success("Order processed successfully")

        except Exception as e:
            self.notifications.show_error(f"Failed to process order: {str(e)}")
            # Attempt to restore from backup
            self.backup.restore_latest()
        finally:
            self.db.disconnect()

    def update_leather_inventory(self, unique_id: str, amount: int):
        """Update leather inventory"""
        current = self.db.execute_query(
            "SELECT amount FROM shelf WHERE unique_id_leather = ?",
            (unique_id,)
        )

        if current:
            new_amount = current[0][0] + amount
            self.db.update_record(
                'shelf',
                {'amount': new_amount},
                "unique_id_leather = ?",
                (unique_id,)
            )

    def update_parts_inventory(self, unique_id: str, amount: int):
        """Update parts inventory"""
        current = self.db.execute_query(
            "SELECT in_storage FROM sorting_system WHERE unique_id_parts = ?",
            (unique_id,)
        )

        if current:
            new_amount = current[0][0] + amount
            self.db.update_record(
                'sorting_system',
                {'in_storage': new_amount},
                "unique_id_parts = ?",
                (unique_id,)
            )

    def show_export_dialog(self):
        """Show dialog for exporting orders"""
        if not self.current_order:
            self.notifications.show_warning("Please select an order to export")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Export Order")
        dialog.transient(self)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill='both', expand=True)

        # Export format selection
        ttk.Label(main_frame, text="Export Format:").pack(anchor='w')
        format_var = tk.StringVar(value="excel")
        ttk.Radiobutton(
            main_frame,
            text="Excel",
            value="excel",
            variable=format_var
        ).pack(anchor='w')
        ttk.Radiobutton(
            main_frame,
            text="CSV",
            value="csv",
            variable=format_var
        ).pack(anchor='w')

        def export():
            """Handle export"""
            try:
                # Get order data
                self.db.connect()
                order = self.db.execute_query(
                    "SELECT * FROM orders WHERE order_number = ?",
                    (self.current_order,)
                )[0]

                # Get order details
                table_name = f"order_details_{self.current_order}"
                details = self.db.execute_query(f"SELECT * FROM {table_name}")

                # Prepare export data
                export_data = {
                    'order': dict(zip(self.orders_columns, order)),
                    'details': [dict(zip(self.details_columns, detail)) for detail in details]
                }

                # Get export path
                file_format = format_var.get()
                filetypes = [("Excel files", "*.xlsx")] if file_format == "excel" \
                    else [("CSV files", "*.csv")]

                filepath = filedialog.asksaveasfilename(
                    defaultextension=f".{file_format}",
                    filetypes=filetypes,
                    initialfile=f"order_{self.current_order}"
                )

                if not filepath:
                    return

                filepath = Path(filepath)

                # Export data
                if file_format == "excel":
                    success = OrderExporter.export_to_excel(export_data, filepath)
                else:
                    success = OrderExporter.export_to_csv(export_data, filepath)

                # Always create JSON backup
                OrderExporter.export_to_json(
                    export_data,
                    filepath.with_suffix('.json')
                )

                if success:
                    self.notifications.show_success("Order exported successfully")
                    dialog.destroy()
                else:
                    self.notifications.show_error("Failed to export order")

            except Exception as e:
                self.notifications.show_error(f"Export error: {str(e)}")
            finally:
                self.db.disconnect()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(
            button_frame,
            text="Export",
            command=export
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

    def show_import_dialog(self):
        """Show dialog for importing orders"""
        dialog = tk.Toplevel(self)
        dialog.title("Import Order")
        dialog.transient(self)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill='both', expand=True)

        # Import format selection
        ttk.Label(main_frame, text="Import Format:").pack(anchor='w')
        format_var = tk.StringVar(value="excel")
        ttk.Radiobutton(
            main_frame,
            text="Excel",
            value="excel",
            variable=format_var
        ).pack(anchor='w')
        ttk.Radiobutton(
            main_frame,
            text="CSV",
            value="csv",
            variable=format_var
        ).pack(anchor='w')

        def import_data():
            """Handle import"""
            try:
                # Get import file
                file_format = format_var.get()
                filetypes = [("Excel files", "*.xlsx")] if file_format == "excel" \
                    else [("CSV files", "*.csv")]

                filepath = filedialog.askopenfilename(
                    filetypes=filetypes
                )

                if not filepath:
                    return

                filepath = Path(filepath)

                # Create backup before import
                self.backup.create_backup('import_order')

                # Import data
                if file_format == "excel":
                    data = OrderImporter.import_from_excel(filepath)
                else:
                    data = OrderImporter.import_from_csv(filepath)

                if not data:
                    self.notifications.show_error("Failed to import order")
                    return

                # Validate data
                valid, error = OrderValidator.validate_order(data['order'])
                if not valid:
                    self.notifications.show_error(f"Invalid order data: {error}")
                    return

                # Insert order
                self.db.connect()
                if self.db.insert_record(TABLES['ORDERS'], data['order']):
                    # Create and populate details table
                    order_number = data['order']['order_number']
                    table_name = f"order_details_{order_number}"

                    self.create_order_details_table(table_name)

                    for detail in data['details']:
                        self.db.insert_record(table_name, detail)

                    # Refresh view
                    self.load_data()
                    self.notifications.show_success("Order imported successfully")
                    dialog.destroy()

            except Exception as e:
                self.notifications.show_error(f"Import error: {str(e)}")
                # Attempt to restore from backup
                self.backup.restore_latest()
            finally:
                self.db.disconnect()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(
            button_frame,
            text="Import",
            command=import_data
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

    def show_search_dialog(self):
        """Show search dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Search Orders")
        dialog.transient(self)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill='both', expand=True)

        # Search options
        ttk.Label(main_frame, text="Search in:").pack(anchor='w')
        target_var = tk.StringVar(value="all")
        ttk.Radiobutton(
            main_frame,
            text="All Fields",
            value="all",
            variable=target_var
        ).pack(anchor='w')
        ttk.Radiobutton(
            main_frame,
            text="Order Number",
            value="order_number",
            variable=target_var
        ).pack(anchor='w')
        ttk.Radiobutton(
            main_frame,
            text="Supplier",
            value="supplier",
            variable=target_var
        ).pack(anchor='w')

        # Search text
        ttk.Label(main_frame, text="Search for:").pack(anchor='w', pady=(10, 0))
        search_var = tk.StringVar()
        ttk.Entry(
            main_frame,
            textvariable=search_var
        ).pack(fill='x', pady=5)

        # Match case option
        match_case = tk.BooleanVar()
        ttk.Checkbutton(
            main_frame,
            text="Match case",
            variable=match_case
        ).pack(anchor='w')

        def search():
            """Perform search"""
            search_text = search_var.get()
            if not search_text:
                self.notifications.show_warning("Please enter search text")
                return

            # Clear current selection
            self.orders_tree.selection_remove(*self.orders_tree.selection())
            found = False

            for item in self.orders_tree.get_children():
                values = self.orders_tree.item(item)['values']

                if target_var.get() == "all":
                    text = " ".join(str(v) for v in values)
                else:
                    col_idx = self.orders_columns.index(target_var.get())
                    text = str(values[col_idx])

                if not match_case.get():
                    text = text.lower()
                    search_text = search_text.lower()

                if search_text in text:
                    self.orders_tree.selection_add(item)
                    self.orders_tree.see(item)
                    found = True

            if not found:
                self.notifications.show_info("No matches found")

            dialog.destroy()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(
            button_frame,
            text="Search",
            command=search
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

    def show_filter_dialog(self):
        """Show filter dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Filter Orders")
        dialog.transient(self)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill='both', expand=True)

        # Filter conditions frame
        conditions_frame = ttk.LabelFrame(main_frame, text="Filter Conditions")
        conditions_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # List to store filter conditions
        conditions = []

        def add_condition():
            """Add new filter condition"""
            condition_frame = ttk.Frame(conditions_frame)
            condition_frame.pack(fill='x', pady=2)

            # Column selection
            column_var = tk.StringVar()
            column_combo = ttk.Combobox(
                condition_frame,
                values=self.orders_columns,
                textvariable=column_var,
                width=15
            )
            column_combo.pack(side=tk.LEFT, padx=2)

            # Operator selection
            operator_var = tk.StringVar()
            operator_combo = ttk.Combobox(
                condition_frame,
                values=['equals', 'contains', 'greater than', 'less than'],
                textvariable=operator_var,
                width=10
            )
            operator_combo.pack(side=tk.LEFT, padx=2)

            # Value entry
            value_var = tk.StringVar()
            value_entry = ttk.Entry(
                condition_frame,
                textvariable=value_var,
                width=20
            )
            value_entry.pack(side=tk.LEFT, padx=2)

            # Remove button
            def remove_condition():
                conditions.remove((column_var, operator_var, value_var))
                condition_frame.destroy()

            ttk.Button(
                condition_frame,
                text="×",
                width=3,
                command=remove_condition
            ).pack(side=tk.LEFT, padx=2)

            conditions.append((column_var, operator_var, value_var))

        # Add initial condition
        add_condition()

        # Add condition button
        ttk.Button(
            main_frame,
            text="Add Condition",
            command=add_condition
        ).pack(pady=10)

        def apply_filters():
            """Apply filter conditions"""
            try:
                filter_conditions = []
                for column_var, operator_var, value_var in conditions:
                    if all([column_var.get(), operator_var.get(), value_var.get()]):
                        filter_conditions.append({
                            'column': column_var.get(),
                            'operator': operator_var.get(),
                            'value': value_var.get()
                        })

                if not filter_conditions:
                    self.notifications.show_warning("No valid filter conditions")
                    return

                # Build query
                query = "SELECT * FROM orders WHERE "
                params = []
                clauses = []

                for condition in filter_conditions:
                    column = condition['column']
                    operator = condition['operator']
                    value = condition['value']

                    if operator == 'equals':
                        clauses.append(f"{column} = ?")
                        params.append(value)
                    elif operator == 'contains':
                        clauses.append(f"{column} LIKE ?")
                        params.append(f"%{value}%")
                    elif operator == 'greater than':
                        clauses.append(f"{column} > ?")
                        params.append(value)
                    elif operator == 'less than':
                        clauses.append(f"{column} < ?")
                        params.append(value)

                query += " AND ".join(clauses)

                # Execute query
                self.db.connect()
                results = self.db.execute_query(query, tuple(params))

                # Update table
                for item in self.orders_tree.get_children():
                    self.orders_tree.delete(item)

                for row in results:
                    self.orders_tree.insert('', 'end', values=row[:-2])

                dialog.destroy()

            except Exception as e:
                self.notifications.show_error(f"Filter error: {str(e)}")
            finally:
                self.db.disconnect()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(
            button_frame,
            text="Apply",
            command=apply_filters
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

    def sort_column(self, tree, col):
        """Sort treeview column"""
        # Get current items
        items = [(tree.set(k, col), k) for k in tree.get_children('')]

        # Determine sort direction
        reverse = False
        if hasattr(tree, '_last_sort') and tree._last_sort == (col, False):
            reverse = True

        # Store sort state
        tree._last_sort = (col, reverse)

        # Sort items
        try:
            # Try numeric sort for appropriate columns
            if col in ['amount', 'price', 'total', 'total_amount']:
                items.sort(key=lambda x: float(x[0]) if x[0] else 0, reverse=reverse)
            elif col == 'date_of_order':
                items.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'), reverse=reverse)
            else:
                items.sort(reverse=reverse)
        except ValueError:
            items.sort(reverse=reverse)

        # Rearrange items
        for index, (_, k) in enumerate(items):
            tree.move(k, '', index)

        # Update header arrow
        for column in tree['columns']:
            if column != col:
                tree.heading(column, text=column.replace('_', ' ').title())
        arrow = "▼" if reverse else "▲"
        tree.heading(col, text=f"{col.replace('_', ' ').title()} {arrow}")

    def delete_selected(self, tree):
        """Delete selected items"""
        if not tree:
            return

        selected = tree.selection()
        if not selected:
            return

        if not messagebox.askyesno("Confirm Delete",
                                   "Are you sure you want to delete the selected items?"):
            return

        try:
            # Create backup
            self.backup.create_backup('delete_items')

            self.db.connect()
            deleted_items = []

            for item in selected:
                values = tree.item(item)['values']

                if tree == self.orders_tree:
                    # Delete order and its details
                    order_number = values[0]
                    self.db.delete_record(
                        TABLES['ORDERS'],
                        "order_number = ?",
                        (order_number,)
                    )

                    # Drop details table
                    table_name = f"order_details_{order_number}"
                    if self.table_exists(table_name):
                        self.db.execute_query(f"DROP TABLE {table_name}")

                elif tree == self.details_tree and self.current_order:
                    # Delete detail item
                    table_name = f"order_details_{self.current_order}"
                    unique_id = values[1]  # unique_id column
                    self.db.delete_record(
                        table_name,
                        "unique_id = ?",
                        (unique_id,)
                    )

                deleted_items.append((item, values))
                tree.delete(item)

            # Add to undo stack
            self.undo_stack.append(('delete', tree, deleted_items))
            self.redo_stack.clear()

            self.notifications.show_success("Items deleted successfully")

        except Exception as e:
            self.notifications.show_error(f"Delete error: {str(e)}")
            # Attempt to restore from backup
            self.backup.restore_latest()
        finally:
            self.db.disconnect()

    def undo(self, event=None):
        """Undo last action"""
        if not self.undo_stack:
            return

        action = self.undo_stack.pop()
        action_type = action[0]

        try:
            self.db.connect()

            if action_type == 'edit':
                tree, item, old_values = action[1:]
                # Store current values for redo
                current_values = tree.item(item)['values']
                self.redo_stack.append(('edit', tree, item, current_values))

                # Restore old values
                tree.item(item, values=old_values)

                # Update database
                if tree == self.orders_tree:
                    self.db.update_record(
                        TABLES['ORDERS'],
                        dict(zip(self.orders_columns, old_values)),
                        "order_number = ?",
                        (old_values[0],)
                    )
                elif tree == self.details_tree and self.current_order:
                    table_name = f"order_details_{self.current_order}"
                    self.db.update_record(
                        table_name,
                        dict(zip(self.details_columns, old_values)),
                        "unique_id = ?",
                        (old_values[1],)
                    )

            elif action_type == 'add':
                tree, values = action[1:]
                # Remove added item
                for item in tree.get_children():
                    if tree.item(item)['values'] == values:
                        tree.delete(item)
                        break

                # Remove from database
                if tree == self.orders_tree:
                    self.db.delete_record(
                        TABLES['ORDERS'],
                        "order_number = ?",
                        (values[0],)
                    )
                elif tree == self.details_tree and self.current_order:
                    table_name = f"order_details_{self.current_order}"
                    self.db.delete_record(
                        table_name,
                        "unique_id = ?",
                        (values[1],)
                    )

                self.redo_stack.append(('readd', tree, values))

            elif action_type == 'delete':
                tree, deleted_items = action[1:]
                restored_items = []

                for item_id, values in deleted_items:
                    # Restore to tree
                    new_item = tree.insert('', 'end', values=values)
                    restored_items.append((new_item, values))

                    # Restore to database
                    if tree == self.orders_tree:
                        self.db.insert_record(
                            TABLES['ORDERS'],
                            dict(zip(self.orders_columns, values))
                        )
                    elif tree == self.details_tree and self.current_order:
                        table_name = f"order_details_{self.current_order}"
                        self.db.insert_record(
                            table_name,
                            dict(zip(self.details_columns, values))
                        )

                self.redo_stack.append(('undelete', tree, restored_items))

        except Exception as e:
            self.notifications.show_error(f"Undo error: {str(e)}")
        finally:
            self.db.disconnect()

    def redo(self, event=None):
        """Redo last undone action"""
        if not self.redo_stack:
            return

        action = self.redo_stack.pop()
        action_type = action[0]

        try:
            self.db.connect()

            if action_type == 'edit':
                tree, item, new_values = action[1:]
                # Store current values for undo
                current_values = tree.item(item)['values']
                self.undo_stack.append(('edit', tree, item, current_values))

                # Restore new values
                tree.item(item, values=new_values)

                # Update database
                if tree == self.orders_tree:
                    self.db.update_record(
                        TABLES['ORDERS'],
                        dict(zip(self.orders_columns, new_values)),
                        "order_number = ?",
                        (new_values[0],)
                    )
                elif tree == self.details_tree and self.current_order:
                    table_name = f"order_details_{self.current_order}"
                    self.db.update_record(
                        table_name,
                        dict(zip(self.details_columns, new_values)),
                        "unique_id = ?",
                        (new_values[1],)
                    )

            elif action_type == 'readd':
                tree, values = action[1:]
                # Re-add item
                tree.insert('', 'end', values=values)

                # Add to database
                if tree == self.orders_tree:
                    self.db.insert_record(
                        TABLES['ORDERS'],
                        dict(zip(self.orders_columns, values))
                    )
                elif tree == self.details_tree and self.current_order:
                    table_name = f"order_details_{self.current_order}"
                    self.db.insert_record(
                        table_name,
                        dict(zip(self.details_columns, values))
                    )

                self.undo_stack.append(('add', tree, values))

            elif action_type == 'undelete':
                tree, restored_items = action[1:]
                deleted_items = []

                for item, values in restored_items:
                    # Remove from tree
                    tree.delete(item)
                    deleted_items.append((item, values))

                    # Remove from database
                    if tree == self.orders_tree:
                        self.db.delete_record(
                            TABLES['ORDERS'],
                            "order_number = ?",
                            (values[0],)
                        )
                    elif tree == self.details_tree and self.current_order:
                        table_name = f"order_details_{self.current_order}"
                        self.db.delete_record(
                            table_name,
                            "unique_id = ?",
                            (values[1],)
                        )

                self.undo_stack.append(('delete', tree, deleted_items))

        except Exception as e:
            self.notifications.show_error(f"Redo error: {str(e)}")
        finally:
            self.db.disconnect()

    def save_changes(self, event=None):
        """Save all changes"""
        try:
            self.db.connect()
            self.db.commit()
            self.notifications.show_success("Changes saved successfully")
            self.modified = False
        except Exception as e:
            self.notifications.show_error(f"Save error: {str(e)}")
        finally:
            self.db.disconnect()

    def reset_view(self, event=None):
        """Reset view to default state"""
        self.load_data()
        if self.current_order:
            self.load_order_details(self.current_order)
        self.notifications.show_info("View reset to default state")

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        result = self.db.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return bool(result)

    def on_double_click(self, tree, event):
        """Handle double-click on cell"""
        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = tree.identify_column(event.x)
        item = tree.identify_row(event.y)

        if not item:
            return

        # Get column name
        col_num = int(column[1]) - 1
        col_name = tree['columns'][col_num]

        # Don't allow editing of certain columns
        if tree == self.orders_tree and col_name in ['total_amount']:
            return
        elif tree == self.details_tree and col_name in ['total']:
            return

        self.start_cell_edit(tree, item, column)

    def start_cell_edit(self, tree, item, column):
        """Start cell editing"""
        # Get column details
        col_num = int(column[1]) - 1
        col_name = tree['columns'][col_num]
        current_value = tree.set(item, col_name)

        # Create edit frame
        frame = ttk.Frame(tree)

        # Create appropriate edit widget
        if col_name == 'status':
            var = tk.StringVar(value=current_value)
            widget = ttk.Combobox(frame, textvariable=var)
            widget['values'] = [
                'ordered', 'being processed', 'shipped',
                'received', 'returned', 'partially returned', 'completed'
            ]
        elif col_name == 'payed':
            var = tk.StringVar(value=current_value)
            widget = ttk.Combobox(frame, textvariable=var)
            widget['values'] = ['yes', 'no']
        elif col_name == 'date_of_order':
            var = tk.StringVar(value=current_value)
            widget = ttk.Entry(frame, textvariable=var)
            # You could add a date picker here
        else:
            var = tk.StringVar(value=current_value)
            widget = ttk.Entry(frame, textvariable=var)

        widget.pack(fill=tk.BOTH, expand=True)

        # Position frame
        bbox = tree.bbox(item, column)
        frame.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])

        def save_edit(event=None):
            """Save the edited value"""
            new_value = var.get().strip()

            if new_value == current_value:
                frame.destroy()
                return

            try:
                # Validate new value
                if col_name in ['price', 'amount', 'total_amount']:
                    try:
                        value = float(new_value)
                        if value < 0:
                            raise ValueError("Value must be non-negative")
                    except ValueError as e:
                        self.notifications.show_error(str(e))
                        return
                elif col_name == 'date_of_order':
                    try:
                        datetime.strptime(new_value, '%Y-%m-%d')
                    except ValueError:
                        self.notifications.show_error("Invalid date format (YYYY-MM-DD)")
                        return

                # Store for undo
                old_values = tree.item(item)['values']
                self.undo_stack.append(('edit', tree, item, old_values))
                self.redo_stack.clear()

                # Update tree
                values = list(tree.item(item)['values'])
                values[col_num] = new_value
                tree.item(item, values=values)

                # Update database
                self.db.connect()
                if tree == self.orders_tree:
                    self.db.update_record(
                        TABLES['ORDERS'],
                        {col_name: new_value},
                        "order_number = ?",
                        (values[0],)
                    )
                elif tree == self.details_tree and self.current_order:
                    table_name = f"order_details_{self.current_order}"

                    # Update total if price or amount changed
                    if col_name in ['price', 'amount']:
                        price = float(values[2])  # price column
                        amount = int(values[3])  # amount column
                        total = price * amount
                        values[4] = total  # total column
                        tree.item(item, values=values)

                        self.db.update_record(
                            table_name,
                            {
                                col_name: new_value,
                                'total': total
                            },
                            "unique_id = ?",
                            (values[1],)
                        )
                    else:
                        self.db.update_record(
                            table_name,
                            {col_name: new_value},
                            "unique_id = ?",
                            (values[1],)
                        )

                self.modified = True

            except Exception as e:
                self.notifications.show_error(f"Edit error: {str(e)}")
            finally:
                self.db.disconnect()
                frame.destroy()

        def cancel_edit(event=None):
            """Cancel the edit"""
            frame.destroy()

        # Bind events
        widget.bind('<Return>', save_edit)
        widget.bind('<Escape>', cancel_edit)
        widget.bind('<FocusOut>', save_edit)
        widget.focus_set()

    def cleanup(self):
        """Cleanup resources"""
        # Check for unsaved changes
        if self.modified:
            if messagebox.askyesno("Save Changes",
                                   "There are unsaved changes. Would you like to save them?"):
                self.save_changes()

        # Cleanup database connection
        if hasattr(self, 'db'):
            self.db.disconnect()