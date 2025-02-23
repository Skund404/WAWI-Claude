import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database.sqlalchemy.session import SessionLocal
from database.sqlalchemy.models_file import Storage, Product
from gui.dialogs.add_dialog import AddDialog
from gui.dialogs.search_dialog import SearchDialog
from gui.dialogs.filter_dialog import FilterDialog
from utils.error_handler import handle_error
from utils.logger import log_action


class SortingSystemView(ttk.Frame):
    def __init__(self, parent, session_factory=SessionLocal):
        """
        Initialize the Sorting System View with SQLAlchemy integration

        Args:
            parent (tk.Widget): Parent widget
            session_factory (callable): SQLAlchemy session factory
        """
        super().__init__(parent)
        self.session_factory = session_factory

        # Undo/Redo stacks for tracking changes
        self.undo_stack = []
        self.redo_stack = []

        # Setup UI components
        self.setup_toolbar()
        self.setup_table()
        self.load_data()

    def setup_toolbar(self):
        """Create the toolbar with all buttons"""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Left side buttons
        ttk.Button(toolbar, text="ADD", command=self.show_add_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Search", command=self.show_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Filter", command=self.show_filter_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Batch Update", command=self.show_batch_update_dialog).pack(side=tk.LEFT, padx=2)

        # Right side buttons
        ttk.Button(toolbar, text="Undo", command=self.undo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Redo", command=self.redo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Load", command=self.load_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Reset View", command=self.reset_view).pack(side=tk.RIGHT, padx=2)

    def setup_table(self):
        """Create the main table view"""
        # Create table frame
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(expand=True, fill='both', padx=5, pady=5)

        # Define columns
        self.columns = [
            'id', 'unique_id', 'name', 'amount', 'warning_threshold', 'bin', 'notes'
        ]

        # Create scrollbars
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal")

        # Create treeview
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=self.columns,
            show='headings',
            selectmode='extended',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        # Configure scrollbars
        vsb.configure(command=self.tree.yview)
        hsb.configure(command=self.tree.xview)

        # Setup headers and columns
        for col in self.columns:
            self.tree.heading(col, text=col.replace('_', ' ').title(),
                              command=lambda c=col: self.sort_column(c))
            self.tree.column(col, width=100, minwidth=50)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

        # Configure warning levels
        self.tree.tag_configure('critical_stock', background='#ff8080')  # Dark red
        self.tree.tag_configure('low_stock', background='#ffcccc')  # Light red
        self.tree.tag_configure('warning_stock', background='#ffe6cc')  # Orange

        # Bind events
        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<Delete>', self.delete_selected)
        self.tree.bind('<Return>', self.handle_return)
        self.tree.bind('<Escape>', self.handle_escape)

    def load_data(self):
        """Load data from database into table"""
        session = self.session_factory()
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Query storage with associated product information
            storages = session.execute(
                select(Storage)
                .options(joinedload(Storage.product))
                .order_by(Storage.bin)
            ).scalars().all()

            # Insert new data
            for storage in storages:
                # Prepare row values
                row_values = [
                    storage.id,
                    storage.product.unique_id if storage.product else '',
                    storage.product.name if storage.product else '',
                    storage.amount,
                    storage.warning_threshold,
                    storage.bin,
                    storage.notes
                ]

                # Insert row
                item = self.tree.insert('', 'end', values=row_values)

                # Apply warning tags based on stock levels
                warning_tag = self.get_warning_tag(storage.amount, storage.warning_threshold)
                if warning_tag:
                    self.tree.item(item, tags=(warning_tag,))

        except Exception as e:
            handle_error(f"Error loading sorting system data: {e}")
            messagebox.showerror("Database Error", str(e))
        finally:
            session.close()

    def get_warning_tag(self, amount: int, warning_threshold: int) -> str:
        """
        Determine the warning level tag based on stock level

        Args:
            amount (int): Current stock level
            warning_threshold (int): Warning threshold level

        Returns:
            str: Warning tag level or empty string if no warning
        """
        try:
            amount = int(amount)
            warning_threshold = int(warning_threshold)

            if amount <= warning_threshold * 0.5:  # Below 50% of threshold
                return 'critical_stock'
            elif amount <= warning_threshold * 0.75:  # Below 75% of threshold
                return 'low_stock'
            elif amount <= warning_threshold:  # At or below threshold
                return 'warning_stock'
            return ''
        except (ValueError, TypeError):
            # If either value can't be converted to int, return no warning
            return ''

    def show_add_dialog(self):
        """Show dialog for adding a new storage item"""
        dialog = AddDialog(
            self,
            title="Add Storage Item",
            columns=[
                ('unique_id', 'Unique ID', False),
                ('name', 'Product Name', True),
                ('amount', 'Amount', True),
                ('warning_threshold', 'Warning Threshold', True),
                ('bin', 'Bin Location', True),
                ('notes', 'Notes', False)
            ],
            on_submit=self.save_new_item
        )
        dialog.grab_set()  # Ensure dialog is modal

    def save_new_item(self, data: Dict):
        """
        Save a new storage item to the database

        Args:
            data (Dict): Dictionary of item data
        """
        session = self.session_factory()
        try:
            # First, check if product exists or create new
            product = session.execute(
                select(Product).where(Product.name == data['name'])
            ).scalar_one_or_none()

            if not product:
                # Create new product if not exists
                product = Product(
                    unique_id=data.get('unique_id') or self.generate_unique_id(data['name']),
                    name=data['name']
                )
                session.add(product)

            # Create new storage item
            storage = Storage(
                product=product,
                amount=int(data['amount']),
                warning_threshold=int(data['warning_threshold']),
                bin=data['bin'],
                notes=data.get('notes')
            )
            session.add(storage)

            # Commit transaction
            session.commit()

            # Log action
            log_action(f"Added storage item: {product.name}")

            # Refresh view
            self.load_data()

            messagebox.showinfo("Success", f"Storage item for {product.name} added successfully")

        except Exception as e:
            session.rollback()
            handle_error(f"Error saving storage item: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            session.close()

    def generate_unique_id(self, name: str) -> str:
        """
        Generate a unique product ID based on the name

        Args:
            name (str): Product name

        Returns:
            str: Generated unique ID
        """
        import uuid

        # Use first two letters of name and add a UUID suffix
        prefix = ''.join(word[0].upper() for word in name.split()[:2])
        unique_id = f"{prefix}-{str(uuid.uuid4())[:8].upper()}"
        return unique_id

    def on_double_click(self, event):
        """
        Handle double-click event for cell editing

        Args:
            event (tk.Event): Tkinter event object
        """
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)

            # Skip editing for ID column
            col_index = int(column[1:]) - 1
            if self.columns[col_index] == 'id':
                return

            self.start_cell_edit(item, column)

    def start_cell_edit(self, item, column):
        """
        Start inline cell editing

        Args:
            item (str): Treeview item identifier
            column (str): Column identifier
        """
        # Implement cell editing logic similar to the previous implementation
        # This will require adapting the previous implementation to work with SQLAlchemy
        pass

    def delete_selected(self, event=None):
        """Delete selected storage items"""
        selected = self.tree.selection()
        if not selected:
            return

        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected items?"):
            return

        session = self.session_factory()
        try:
            # Track deleted items for potential undo
            deleted_items = []

            for item in selected:
                # Get storage ID
                storage_id = self.tree.set(item, 'id')

                # Fetch the storage item
                storage = session.get(Storage, int(storage_id))

                if storage:
                    # Track for potential undo
                    deleted_items.append({
                        'id': storage.id,
                        'product_id': storage.product_id,
                        'amount': storage.amount,
                        'warning_threshold': storage.warning_threshold,
                        'bin': storage.bin,
                        'notes': storage.notes
                    })

                    # Delete the storage item
                    session.delete(storage)

            # Commit transaction
            session.commit()

            # Remove from treeview
            for item in selected:
                self.tree.delete(item)

            # Add to undo stack
            self.undo_stack.append(('delete', deleted_items))
            self.redo_stack.clear()

            log_action(f"Deleted {len(selected)} storage items")
            messagebox.showinfo("Success", f"Deleted {len(selected)} items")

        except Exception as e:
            session.rollback()
            handle_error(f"Error deleting storage items: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            session.close()

    def undo(self):
        """Undo the last action"""
        if not self.undo_stack:
            return

        action_type, data = self.undo_stack.pop()
        session = self.session_factory()

        try:
            if action_type == 'delete':
                # Restore deleted items
                restored_items = []
                for item_data in data:
                    # Recreate storage item
                    storage = Storage(
                        id=item_data['id'],
                        product_id=item_data['product_id'],
                        amount=item_data['amount'],
                        warning_threshold=item_data['warning_threshold'],
                        bin=item_data['bin'],
                        notes=item_data['notes']
                    )
                    session.add(storage)
                    restored_items.append(storage)

                # Commit and reload
                session.commit()
                self.load_data()

                # Add to redo stack
                self.redo_stack.append(('undelete', restored_items))

        except Exception as e:
            session.rollback()
            handle_error(f"Undo error: {e}")
            messagebox.showerror("Undo Error", str(e))
        finally:
            session.close()

    def redo(self):
        """Redo the last undone action"""
        if not self.redo_stack:
            return

        action_type, data = self.redo_stack.pop()
        session = self.session_factory()

        try:
            if action_type == 'undelete':
                # Delete the previously restored items
                for storage in data:
                    session.delete(storage)

                session.commit()
                self.load_data()

                # Add back to undo stack
                self.undo_stack.append(('delete', [
                    {
                        'id': item.id,
                        'product_id': item.product_id,
                        'amount': item.amount,
                        'warning_threshold': item.warning_threshold,
                        'bin': item.bin,
                        'notes': item.notes
                    } for item in data
                ]))

        except Exception as e:
            session.rollback()
            handle_error(f"Redo error: {e}")
            messagebox.showerror("Redo Error", str(e))
        finally:
            session.close()
