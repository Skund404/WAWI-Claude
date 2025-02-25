# supplier_view.py
"""
Supplier View module for managing supplier information in a tkinter-based GUI application.

This module provides a comprehensive view for managing supplier data, including 
functionalities like adding, editing, deleting, searching, and filtering suppliers.
"""

import csv
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any

from di.core import inject
from services.interfaces import MaterialService
from utils.database import DatabaseManager, DatabaseError
from utils.error_handler import ErrorHandler
from utils.decorators import check_database_connection

# Configure logging
logger = logging.getLogger(__name__)


class SupplierView(ttk.Frame):
    """
    A tkinter Frame subclass for managing supplier information.

    Provides a comprehensive interface for viewing, editing, and managing
    supplier data with search, filter, and export capabilities.

    Attributes:
        db (DatabaseManager): Database connection manager
        field_mapping (Dict[str, str]): Mapping between display and database column names
        reverse_mapping (Dict[str, str]): Reverse mapping of field names
        tree (ttk.Treeview): Main table view for displaying suppliers
        columns (List[str]): List of column names
        undo_stack (List[Tuple]): Stack for undo operations
        redo_stack (List[Tuple]): Stack for redo operations
    """

    @inject(MaterialService)
    def __init__(self, parent: tk.Tk):
        """
        Initialize the SupplierView.

        Args:
            parent (tk.Tk): The parent tkinter window or frame
        """
        try:
            super().__init__(parent)

            # Database connection
            self.db = DatabaseManager(self._get_database_path())

            # Field mappings
            self.field_mapping = {
                'Company Name': 'company_name',
                'Contact Person': 'contact_person',
                'Phone Number': 'phone_number',
                'Email Address': 'email_address',
                'Website': 'website',
                'Street Address': 'street_address',
                'City': 'city',
                'State/Province': 'state_province',
                'Postal Code': 'postal_code',
                'Country': 'country',
                'Tax ID': 'tax_id',
                'Business Type': 'business_type',
                'Payment Terms': 'payment_terms',
                'Currency': 'currency',
                'Bank Details': 'bank_details',
                'Products Offered': 'products_offered',
                'Lead Time': 'lead_time',
                'Last Order Date': 'last_order_date',
                'Notes': 'notes'
            }
            self.reverse_mapping = {v: k for k, v in self.field_mapping.items()}

            # Undo/Redo stacks
            self.undo_stack: List[Tuple] = []
            self.redo_stack: List[Tuple] = []

            # Sorting flag
            self._sort_reverse = False

            # Setup UI components
            self._setup_toolbar()
            self._setup_table()
            self._load_data()

            logger.info('SupplierView initialized successfully')

        except Exception as init_error:
            logger.error(f'Supplier View Initialization Error: {init_error}')
            ErrorHandler.show_error(
                'Initialization Error',
                'Failed to initialize Supplier View',
                init_error
            )
            raise

    def _get_database_path(self) -> str:
        """
        Retrieve the database path.

        Returns:
            str: Path to the database
        """
        # This is a placeholder. In a real application,
        # this would come from a configuration file or environment variable
        return 'suppliers.db'

    def _setup_toolbar(self) -> None:
        """
        Create the toolbar with action buttons.
        """
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Left frame buttons
        left_frame = ttk.Frame(toolbar)
        left_frame.pack(side=tk.LEFT, fill=tk.X)
        ttk.Button(left_frame, text='ADD', command=self._show_add_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_frame, text='Search', command=self._show_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_frame, text='Filter', command=self._show_filter_dialog).pack(side=tk.LEFT, padx=2)

        # Right frame buttons
        right_frame = ttk.Frame(toolbar)
        right_frame.pack(side=tk.RIGHT, fill=tk.X)
        ttk.Button(right_frame, text='Save', command=self._save_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(right_frame, text='Load', command=self._load_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(right_frame, text='Undo', command=self._undo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(right_frame, text='Redo', command=self._redo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(right_frame, text='Reset View', command=self._reset_view).pack(side=tk.RIGHT, padx=2)

    def _setup_table(self) -> None:
        """
        Create the main table view for displaying suppliers.
        """
        table_frame = ttk.Frame(self)
        table_frame.pack(expand=True, fill='both', padx=5, pady=5)

        # Columns
        self.columns = list(self.field_mapping.keys())

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient='vertical')
        hsb = ttk.Scrollbar(table_frame, orient='horizontal')

        # Treeview
        self.tree = ttk.Treeview(
            table_frame,
            columns=self.columns,
            show='headings',
            selectmode='extended',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        # Configure scrollbars
        vsb.configure(command=self.tree.yview)
        hsb.configure(command=self.tree.xview)

        # Configure columns
        for col in self.columns:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_column(c))

            # Set column widths based on content
            if col in ['Notes', 'Products Offered', 'Bank Details']:
                width = 200
            elif col in ['Street Address', 'Email Address', 'Website']:
                width = 150
            else:
                width = 100

            self.tree.column(col, width=width, minwidth=50)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        # Bind events
        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Delete>', self._delete_selected)

    @check_database_connection
    def _load_data(self) -> None:
        """
        Load supplier data from the database and populate the treeview.

        Raises:
            DatabaseError: If the supplier table does not exist
        """
        try:
            logger.debug('Loading supplier data')

            # Ensure database connection
            if not self.db or not self.db.conn:
                self.db.connect()

            # Check table existence
            if not self.db.table_exists('SUPPLIER'):
                raise DatabaseError("Supplier table does not exist")

            # Fetch all suppliers
            query = "SELECT * FROM SUPPLIER"
            results = self.db.execute_query(query)

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Populate treeview
            if results:
                for row in results:
                    self.tree.insert('', 'end', values=row)
                logger.info(f'Loaded {len(results)} suppliers')
            else:
                logger.info('No suppliers found in database')

        except Exception as e:
            error_msg = f'Failed to load supplier data: {str(e)}'
            logger.error(error_msg)
            ErrorHandler.show_error('Load Error', error_msg, e)
            raise

    def _load_table(self) -> None:
        """
        Alias for load_data method to maintain existing interface.
        """
        self._load_data()

    def _reset_view(self) -> None:
        """
        Reset the view to show all suppliers.
        """
        try:
            logger.debug('Resetting view')
            self._load_data()
            logger.info('View reset successfully')
        except Exception as e:
            error_msg = 'Failed to reset view'
            logger.error(f'{error_msg}: {str(e)}')
            ErrorHandler.show_error('Reset Error', error_msg, e)

    def _show_add_dialog(self) -> None:
        """
        Open dialog to add a new supplier.
        """
        try:
            add_dialog = tk.Toplevel(self)
            add_dialog.title('Add New Supplier')
            add_dialog.geometry('400x600')

            # Create a scrollable frame
            canvas = tk.Canvas(add_dialog)
            scrollbar = ttk.Scrollbar(add_dialog, orient='vertical', command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            # Configure canvas and scrollbar
            scrollable_frame.bind('<Configure>',
                                  lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
            canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
            canvas.configure(yscrollcommand=scrollbar.set)

            # Entry widgets for each field
            entry_widgets = {}
            for i, (display_name, db_field) in enumerate(self.field_mapping.items()):
                label = ttk.Label(scrollable_frame, text=display_name)
                label.grid(row=i, column=0, padx=5, pady=5, sticky='w')

                entry = ttk.Entry(scrollable_frame, width=40)
                entry.grid(row=i, column=1, padx=5, pady=5)
                entry_widgets[db_field] = entry

            def save_supplier():
                """
                Save the new supplier to the database.
                """
                try:
                    # Collect data from entry widgets
                    data = {field: widget.get().strip() for field, widget in entry_widgets.items()}

                    # Validate required fields
                    if not data['company_name']:
                        messagebox.showerror('Error', 'Company Name is required')
                        return

                    # Connect to database
                    self.db.connect()

                    # Insert record
                    if self.db.insert_record('SUPPLIER', data):
                        # Update undo/redo stacks
                        self.undo_stack.append(('add', data))
                        self.redo_stack.clear()

                        # Refresh data
                        self._load_data()

                        # Close dialog
                        add_dialog.destroy()
                        messagebox.showinfo('Success', 'Supplier added successfully')
                    else:
                        raise DatabaseError('Failed to add supplier')

                except Exception as e:
                    error_msg = f'Failed to add supplier: {str(e)}'
                    logger.error(error_msg)
                    ErrorHandler.show_error('Add Error', error_msg, e)
                finally:
                    self.db.disconnect()

            # Button frame
            button_frame = ttk.Frame(scrollable_frame)
            button_frame.grid(row=len(self.field_mapping), column=0, columnspan=2, pady=10)

            ttk.Button(button_frame, text='Save', command=save_supplier).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text='Cancel', command=add_dialog.destroy).pack(side=tk.LEFT, padx=5)

            # Layout scrollable frame
            canvas.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')

        except Exception as e:
            error_msg = 'Failed to create add dialog'
            logger.error(f'{error_msg}: {str(e)}')
            ErrorHandler.show_error('Dialog Error', error_msg, e)

    def _show_search_dialog(self) -> None:
        """
        Open dialog to search suppliers.
        """
        try:
            search_dialog = tk.Toplevel(self)
            search_dialog.title('Search Suppliers')
            search_dialog.geometry('400x300')

            # Search fields
            search_fields = list(self.field_mapping.keys())
            entry_widgets = {}

            for i, field in enumerate(search_fields):
                label = ttk.Label(search_dialog, text=field.replace('_', ' ').title())
                label.grid(row=i, column=0, padx=5, pady=5, sticky='w')

                entry = ttk.Entry(search_dialog, width=30)
                entry.grid(row=i, column=1, padx=5, pady=5)
                entry_widgets[self.field_mapping[field]] = entry

            def perform_search():
                """
                Execute the search based on entered criteria.
                """
                try:
                    # Build search conditions
                    conditions = []
                    params = []
                    for field, widget in entry_widgets.items():
                        value = widget.get().strip()
                        if value:
                            conditions.append(f'{field} LIKE ?')
                            params.append(f'%{value}%')

                    # Validate search
                    if not conditions:
                        messagebox.showinfo('Search', 'Please enter at least one search term')
                        return

                    # Connect to database
                    self.db.connect()

                    # Construct query
                    query = "SELECT * FROM SUPPLIER"
                    if conditions:
                        query += ' WHERE ' + ' AND '.join(conditions)

                    # Execute search
                    results = self.db.execute_query(query, tuple(params))

                    # Clear existing tree items
                    for item in self.tree.get_children():
                        self.tree.delete(item)

                    # Populate tree with results
                    for row in results:
                        self.tree.insert('', 'end', values=row)

                    # Close search dialog
                    search_dialog.destroy()

                    # Show result message
                    if not results:
                        messagebox.showinfo('Search', 'No matching suppliers found')

                except Exception as e:
                    error_msg = 'Search failed'
                    logger.error(f'{error_msg}: {str(e)}')
                    ErrorHandler.show_error('Search Error', error_msg, e)

        except Exception as e:
            error_msg = 'Failed to create search dialog'
            logger.error(f'{error_msg}: {str(e)}')
            ErrorHandler.show_error('Dialog Error', error_msg, e)

    def _show_filter_dialog(self) -> None:
        """
        Open dialog to filter suppliers.
        """
        try:
            filter_dialog = tk.Toplevel(self)
            filter_dialog.title('Filter Suppliers')
            filter_dialog.geometry('400x400')

            # Predefined filter options
            filter_options = {
                'business_type': ['All', 'Manufacturer', 'Wholesaler', 'Distributor', 'Retailer'],
                'payment_terms': ['All', 'Net 30', 'Net 60', 'Net 90', 'Prepaid'],
                'country': ['All']
            }

            # Dynamically fetch countries from database
            try:
                self.db.connect()
                query = "SELECT DISTINCT country FROM SUPPLIER WHERE country IS NOT NULL"
                countries = self.db.execute_query(query)
                if countries:
                    filter_options['country'].extend([country[0] for country in countries])
            except Exception as e:
                logger.error(f'Failed to fetch countries: {e}')
            finally:
                self.db.disconnect()

            # Filter widgets
            filter_widgets = {}
            row = 0
            for field, options in filter_options.items():
                label = ttk.Label(filter_dialog, text=field.replace('_', ' ').title())
                label.grid(row=row, column=0, padx=5, pady=5, sticky='w')

                combo = ttk.Combobox(
                    filter_dialog,
                    values=options,
                    state='readonly',
                    width=30
                )
                combo.set('All')
                combo.grid(row=row, column=1, padx=5, pady=5)
                filter_widgets[field] = combo
                row += 1

            def apply_filters():
                """
                Apply selected filters to the supplier view.
                """
                try:
                    # Collect filter criteria
                    criteria = {}
                    for field, widget in filter_widgets.items():
                        value = widget.get()
                        if value and value != 'All':
                            criteria[field] = value

                    # Construct query
                    query = "SELECT * FROM SUPPLIER"
                    params = []

                    if criteria:
                        conditions = []
                        for field, value in criteria.items():
                            conditions.append(f'{field} = ?')
                            params.append(value)
                        query += ' WHERE ' + ' AND '.join(conditions)

                    # Connect to database
                    self.db.connect()
                    results = self.db.execute_query(query, tuple(params))

                    # Clear existing tree items
                    for item in self.tree.get_children():
                        self.tree.delete(item)

                    # Populate tree with filtered results
                    for row in results:
                        self.tree.insert('', 'end', values=row)

                    # Close filter dialog
                    filter_dialog.destroy()

                    # Show result message
                    if not results:
                        messagebox.showinfo('Filter', 'No suppliers match the selected criteria')

                except Exception as e:
                    error_msg = 'Filter operation failed'
                    logger.error(f'{error_msg}: {str(e)}')
                    ErrorHandler.show_error('Filter Error', error_msg, e)
                finally:
                    self.db.disconnect()

            def reset_filters():
                """
                Reset all filter selections to default.
                """
                try:
                    # Reset all filter widgets to 'All'
                    for widget in filter_widgets.values():
                        widget.set('All')

                    # Reload original data
                    self._load_data()
                except Exception as e:
                    error_msg = 'Failed to reset filters'
                    logger.error(f'{error_msg}: {str(e)}')
                    ErrorHandler.show_error('Reset Error', error_msg, e)

            # Button frame
            button_frame = ttk.Frame(filter_dialog)
            button_frame.grid(row=row, column=0, columnspan=2, pady=10)

            ttk.Button(button_frame, text='Apply', command=apply_filters).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text='Reset', command=reset_filters).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text='Cancel', command=filter_dialog.destroy).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            error_msg = 'Failed to create filter dialog'
            logger.error(f'{error_msg}: {str(e)}')
            ErrorHandler.show_error('Dialog Error', error_msg, e)

    def _on_double_click(self, event: tk.Event) -> None:
        """
        Handle double-click event for editing a cell.

        Args:
            event (tk.Event): The double-click event
        """
        try:
            # Get selected item
            selected_item = self.tree.selection()
            if not selected_item:
                return

            item = selected_item[0]

            # Identify the clicked column
            column = self.tree.identify_column(event.x)
            column_id = int(column[1]) - 1

            # Ensure column is valid
            if 0 <= column_id < len(self.columns):
                self._start_cell_edit(item, self.columns[column_id])

        except Exception as e:
            error_msg = 'Failed to handle double-click'
            logger.error(f'{error_msg}: {str(e)}')
            ErrorHandler.show_error('Edit Error', error_msg, e)

    def _start_cell_edit(self, item: str, column: str) -> None:
        """
        Start editing a specific cell.

        Args:
            item (str): Treeview item identifier
            column (str): Column to edit
        """
        try:
            # Get current value
            current_value = self.tree.set(item, column)

            # Create edit dialog
            edit_dialog = tk.Toplevel(self)
            edit_dialog.title(f'Edit {column}')

            # Position dialog near the cell
            x, y, _, _ = self.tree.bbox(item, column)
            edit_dialog.geometry(
                f'+{x + self.winfo_rootx()}+{y + self.winfo_rooty()}'
            )

            # Create entry widget
            entry = ttk.Entry(edit_dialog)
            entry.insert(0, current_value)
            entry.pack(padx=5, pady=5)
            entry.focus_set()

            def save_edit(event=None):
                """
                Save the edited cell value.
                """
                try:
                    new_value = entry.get()

                    # Only update if value changed
                    if new_value != current_value:
                        # Get database column name
                        db_column = self.field_mapping[column]

                        # Connect to database
                        self.db.connect()

                        # Prepare update data
                        data = {db_column: new_value}
                        company_name = self.tree.item(item)['values'][0]

                        # Update record
                        if self.db.update_record(
                                'SUPPLIER',
                                data,
                                'company_name = ?',
                                (company_name,)
                        ):
                            # Update treeview
                            self.tree.set(item, column, new_value)

                            # Update undo/redo stacks
                            self.undo_stack.append(('edit', item, column, current_value, new_value))
                            self.redo_stack.clear()

                        # Close dialog
                        edit_dialog.destroy()

                except Exception as e:
                    error_msg = 'Failed to save edit'
                    logger.error(f'{error_msg}: {str(e)}')
                    ErrorHandler.show_error('Edit Error', error_msg, e)
                finally:
                    self.db.disconnect()

            def cancel_edit(event=None):
                """
                Cancel cell editing.
                """
                edit_dialog.destroy()

            # Bind events
            entry.bind('<Return>', save_edit)
            entry.bind('<Escape>', cancel_edit)

            # Create button frame
            button_frame = ttk.Frame(edit_dialog)
            button_frame.pack(fill=tk.X, padx=5, pady=5)

            ttk.Button(button_frame, text='Save', command=save_edit).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text='Cancel', command=cancel_edit).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            error_msg = 'Failed to start cell edit'
            logger.error(f'{error_msg}: {str(e)}')
            ErrorHandler.show_error('Edit Error', error_msg, e)

    def _delete_selected(self, event: Optional[tk.Event] = None) -> None:
        """
        Delete selected supplier(s).

        Args:
            event (Optional[tk.Event]): Optional delete key event
        """
        try:
            # Get selected items
            selected_items = self.tree.selection()

            # Check if any items are selected
            if not selected_items:
                logger.debug('No items selected for deletion')
                messagebox.showinfo('Delete', 'No suppliers selected')
                return

            # Confirm deletion
            if not messagebox.askyesno(
                    'Confirm Delete',
                    f'Are you sure you want to delete {len(selected_items)} supplier(s)?'
            ):
                return

            logger.debug(f'Attempting to delete {len(selected_items)} suppliers')

            # Prepare for deletion tracking
            deleted_items = []

            # Start database transaction
            self.db.begin_transaction()

            try:
                # Delete each selected supplier
                for item in selected_items:
                    # Get supplier details
                    values = self.tree.item(item)['values']

                    # Delete from database
                    if self.db.delete_record(
                            'SUPPLIER',
                            'company_name = ?',
                            (values[0],)
                    ):
                        # Track deleted items for potential undo
                        deleted_items.append((item, values))

                        # Remove from treeview
                        self.tree.delete(item)

                # Commit transaction
                self.db.commit_transaction()

                # Update undo/redo stacks
                self.undo_stack.append(('delete', deleted_items))
                self.redo_stack.clear()

                # Log success
                logger.info(f'Successfully deleted {len(deleted_items)} suppliers')
                messagebox.showinfo('Success', f'{len(deleted_items)} supplier(s) deleted')

            except Exception as inner_e:
                # Rollback transaction on error
                self.db.rollback_transaction()
                raise inner_e

        except Exception as e:
            error_msg = 'Failed to delete suppliers'
            logger.error(f'{error_msg}: {str(e)}')
            ErrorHandler.show_error('Delete Error', error_msg, e)

    def _sort_column(self, column: str) -> None:
        """
        Sort the treeview by the specified column.

        Args:
            column (str): Column to sort
        """
        try:
            logger.debug(f'Sorting by column: {column}')

            # Get all items with their values for the specified column
            items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]

            # Sort items
            items.sort(reverse=getattr(self, '_sort_reverse', False))

            # Rearrange items in the treeview
            for index, (_, item) in enumerate(items):
                self.tree.move(item, '', index)

            # Toggle sort direction
            self._sort_reverse = not getattr(self, '_sort_reverse', False)

            # Update column headings to show sort direction
            for col in self.columns:
                if col == column:
                    # Add triangle indicator
                    indicator = '▼' if self._sort_reverse else '▲'
                    self.tree.heading(
                        col,
                        text=f"{col.replace('_', ' ').title()} {indicator}"
                    )
                else:
                    # Reset other column headings
                    self.tree.heading(
                        col,
                        text=col.replace('_', ' ').title()
                    )

        except Exception as e:
            error_msg = f'Failed to sort column: {column}'
            logger.error(f'{error_msg}: {str(e)}')
            ErrorHandler.show_error('Sort Error', error_msg, e)

    def _undo(self) -> None:
        """
        Undo the last action.
        """
        try:
            # Check if undo stack is empty
            if not self.undo_stack:
                return

            # Get last action
            action = self.undo_stack.pop()
            action_type = action[0]

            # Connect to database
            self.db.connect()

            try:
                if action_type == 'edit':
                    # Undo edit operation
                    _, item, column, old_value, new_value = action

                    # Get database column name
                    db_column = self.field_mapping[column]

                    # Update record with old value
                    data = {db_column: old_value}
                    if self.db.update_record(
                            'SUPPLIER',
                            data,
                            'company_name = ?',
                            (self.tree.item(item)['values'][0],)
                    ):
                        # Update treeview
                        self.tree.set(item, column, old_value)

                        # Add to redo stack
                        self.redo_stack.append(('edit', item, column, old_value, new_value))

                elif action_type == 'delete':
                    # Undo delete operation
                    deleted_items = action[1]
                    restored_items = []

                    for _, values in deleted_items:
                        # Prepare data for reinsertion
                        data = dict(zip(self.columns, values))

                        # Reinsert into database
                        if self.db.insert_record('SUPPLIER', data):
                            # Reinsert into treeview
                            new_item = self.tree.insert('', 'end', values=values)
                            restored_items.append((new_item, values))

                    # Add to redo stack
                    self.redo_stack.append(('undelete', restored_items))

                elif action_type == 'add':
                    # Undo add operation
                    data = action[1]
                    company_name = data['company_name']

                    # Delete from database
                    if self.db.delete_record('SUPPLIER', 'company_name = ?', (company_name,)):
                        # Remove from treeview
                        for item in self.tree.get_children():
                            if self.tree.item(item)['values'][0] == company_name:
                                self.tree.delete(item)
                                break

                    # Add to redo stack
                    self.redo_stack.append(('readd', data))

            except Exception as inner_e:
                # Rollback on error
                self.db.rollback_transaction()
                raise inner_e

        except Exception as e:
            error_msg = 'Failed to undo action'
            logger.error(f'{error_msg}: {str(e)}')
            ErrorHandler.show_error('Undo Error', error_msg, e)
        finally:
            # Ensure database connection is closed
            self.db.disconnect()

    def _redo(self) -> None:
        """
        Redo the last undone action.
        """
        try:
            # Check if redo stack is empty
            if not self.redo_stack:
                return

            # Get last action
            action = self.redo_stack.pop()
            action_type = action[0]

            # Connect to database
            self.db.connect()

            try:
                if action_type == 'edit':
                    # Redo edit operation
                    _, item, column, old_value, new_value = action

                    # Get database column name
                    db_column = self.field_mapping[column]

                    # Update record with new value
                    data = {db_column: new_value}
                    if self.db.update_record(
                            'SUPPLIER',
                            data,
                            'company_name = ?',
                            (self.tree.item(item)['values'][0],)
                    ):
                        # Update treeview
                        self.tree.set(item, column, new_value)

                        # Add to undo stack
                        self.undo_stack.append(('edit', item, column, old_value, new_value))

                elif action_type == 'undelete':
                    # Redo undelete (which is actually a delete)
                    restored_items = action[1]
                    deleted_items = []

                    for item, values in restored_items:
                        # Delete from database
                        if self.db.delete_record('SUPPLIER', 'company_name = ?', (values[0],)):
                            # Remove from treeview
                            self.tree.delete(item)
                            deleted_items.append((item, values))

                    # Add to undo stack
                    self.undo_stack.append(('delete', deleted_items))

                elif action_type == 'readd':
                    # Redo add operation
                    data = action[1]

                    # Insert record into database
                    if self.db.insert_record('SUPPLIER', data):
                        # Insert into treeview
                        values = [data.get(col, '') for col in self.columns]
                        self.tree.insert('', 'end', values=values)

                        # Add to undo stack
                        self.undo_stack.append(('add', data))

            except Exception as inner_e:
                # Rollback on error
                self.db.rollback_transaction()
                raise inner_e

        except Exception as e:
            error_msg = 'Failed to redo action'
            logger.error(f'{error_msg}: {str(e)}')
            ErrorHandler.show_error('Redo Error', error_msg, e)
        finally:
            # Ensure database connection is closed
            self.db.disconnect()

    def _save_table(self) -> None:
        """
        Save the current table data to a file.
        Supports CSV and Excel formats.
        """
        try:
            # Prompt for file save location
            file_path = filedialog.asksaveasfilename(
                defaultextension='.csv',
                filetypes=[
                    ('CSV files', '*.csv'),
                    ('Excel files', '*.xlsx'),
                    ('All files', '*.*')
                ]
            )

            if not file_path:
                return

            # Prepare data
            data = [self.columns]
            for item in self.tree.get_children():
                data.append(self.tree.item(item)['values'])

            # Save based on file extension
            if file_path.endswith('.csv'):
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(data)
            elif file_path.endswith('.xlsx'):
                df = pd.DataFrame(data[1:], columns=data[0])
                df.to_excel(file_path, index=False)

            logger.info(f'Table saved to: {file_path}')
            messagebox.showinfo('Success', 'Table saved successfully')

        except Exception as e:
            error_msg = 'Failed to save table'
            logger.error(f'{error_msg}: {str(e)}')
            ErrorHandler.show_error('Save Error', error_msg, e)

    @classmethod
    def create_view(cls, parent: tk.Tk) -> 'SupplierView':
        """
        Class method to create and return a SupplierView instance.

        Args:
            parent (tk.Tk): The parent tkinter window

        Returns:
            SupplierView: An instance of the SupplierView
        """
        return cls(parent)

def main():
    """
    Main function to demonstrate SupplierView usage.
    """
    # Create main window
    root = tk.Tk()
    root.title("Supplier Management System")
    root.geometry("1200x800")

    # Create SupplierView
    supplier_view = SupplierView.create_view(root)
    supplier_view.pack(fill=tk.BOTH, expand=True)

    # Start the application
    root.mainloop()

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('supplier_view.log'),
            logging.StreamHandler()
        ]
    )

    # Run the main application
    main()
