# relative path: store_management/gui/order/supplier_view.py
"""
Supplier View module for managing supplier information in a tkinter-based GUI application.

This module provides a comprehensive view for managing supplier data, including
functionalities like adding, editing, deleting, searching, and filtering suppliers.
"""

# Correct imports should be:
import csv
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)


class SupplierView(ttk.Frame):
    # Existing methods and initialization code...

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

            # Create a scrollable frame
            canvas = tk.Canvas(search_dialog)
            scrollbar = ttk.Scrollbar(search_dialog, orient='vertical', command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind('<Configure>',
                                  lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
            canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
            canvas.configure(yscrollcommand=scrollbar.set)

            # Add search fields
            for i, field in enumerate(search_fields):
                label = ttk.Label(scrollable_frame, text=field)
                label.grid(row=i, column=0, padx=5, pady=5, sticky='w')

                entry = ttk.Entry(scrollable_frame, width=30)
                entry.grid(row=i, column=1, padx=5, pady=5)
                entry_widgets[self.field_mapping[field]] = entry

            def perform_search():
                """
                Execute the search based on entered criteria.
                """
                try:
                    # Build search conditions
                    search_params = {}
                    for field, widget in entry_widgets.items():
                        value = widget.get().strip()
                        if value:
                            search_params[field] = value

                    # Validate search
                    if not search_params:
                        messagebox.showinfo('Search', 'Please enter at least one search term')
                        return

                    # Execute search through service
                    suppliers = self.supplier_service.search_suppliers(search_params)

                    # Clear existing tree items
                    for item in self.tree.get_children():
                        self.tree.delete(item)

                    # Populate tree with results
                    if suppliers:
                        for supplier in suppliers:
                            values = []
                            for column in self.columns:
                                db_field = self.field_mapping[column]
                                values.append(getattr(supplier, db_field, ""))

                            self.tree.insert('', 'end', values=values)

                    # Close search dialog
                    search_dialog.destroy()

                    # Show result message
                    if not suppliers:
                        messagebox.showinfo('Search', 'No matching suppliers found')

                except Exception as e:
                    error_msg = 'Search failed'
                    logger.error(f'{error_msg}: {str(e)}')
                    messagebox.showerror('Search Error', error_msg)

            # Button frame
            button_frame = ttk.Frame(scrollable_frame)
            button_frame.grid(row=len(search_fields), column=0, columnspan=2, pady=10)

            ttk.Button(button_frame, text='Search', command=perform_search).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text='Cancel', command=search_dialog.destroy).pack(side=tk.LEFT, padx=5)

            # Layout scrollable frame
            canvas.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')

        except Exception as e:
            error_msg = 'Failed to create search dialog'
            logger.error(f'{error_msg}: {str(e)}')
            messagebox.showerror('Dialog Error', error_msg)

    def _show_filter_dialog(self) -> None:
        """
        Open dialog to filter suppliers.
        """
        try:
            filter_dialog = tk.Toplevel(self)
            filter_dialog.title('Filter Suppliers')
            filter_dialog.geometry('400x400')

            # Get filter options from service
            try:
                filter_options = self.supplier_service.get_filter_options()
            except Exception:
                # Fallback filter options if service method isn't available
                filter_options = {
                    'business_type': ['All', 'Manufacturer', 'Wholesaler', 'Distributor', 'Retailer'],
                    'payment_terms': ['All', 'Net 30', 'Net 60', 'Net 90', 'Prepaid'],
                    'country': ['All', 'USA', 'Canada', 'UK', 'Germany', 'France', 'China', 'Japan']
                }

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

                    # Use service to get filtered suppliers
                    suppliers = self.supplier_service.filter_suppliers(criteria)

                    # Clear existing tree items
                    for item in self.tree.get_children():
                        self.tree.delete(item)

                    # Populate tree with filtered results
                    if suppliers:
                        for supplier in suppliers:
                            values = []
                            for column in self.columns:
                                db_field = self.field_mapping[column]
                                values.append(getattr(supplier, db_field, ""))

                            self.tree.insert('', 'end', values=values)

                    # Close filter dialog
                    filter_dialog.destroy()

                    # Show result message
                    if not suppliers:
                        messagebox.showinfo('Filter', 'No suppliers match the selected criteria')

                except Exception as e:
                    error_msg = 'Filter operation failed'
                    logger.error(f'{error_msg}: {str(e)}')
                    messagebox.showerror('Filter Error', error_msg)

            # Button frame
            button_frame = ttk.Frame(filter_dialog)
            button_frame.grid(row=row, column=0, columnspan=2, pady=10)

            ttk.Button(button_frame, text='Apply', command=apply_filters).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text='Reset', command=self._reset_view).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text='Cancel', command=filter_dialog.destroy).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            error_msg = 'Failed to create filter dialog'
            logger.error(f'{error_msg}: {str(e)}')
            messagebox.showerror('Dialog Error', error_msg)

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
            messagebox.showerror('Edit Error', error_msg)

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

            # Get supplier ID (assuming it's the first column value)
            supplier_values = self.tree.item(item)['values']
            company_name = supplier_values[0]  # Using company name as identifier

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

                        # Create update data
                        update_data = {db_column: new_value}

                        # Use service to update supplier
                        result = self.supplier_service.update_supplier(company_name, update_data)

                        if result:
                            # Update treeview
                            self.tree.set(item, column, new_value)

                            # Store for undo
                            self.undo_stack.append(('edit', item, column, current_value, new_value))
                            self.redo_stack.clear()

                        # Close dialog
                        edit_dialog.destroy()

                except Exception as e:
                    error_msg = 'Failed to save edit'
                    logger.error(f'{error_msg}: {str(e)}')
                    messagebox.showerror('Edit Error', error_msg)

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
            messagebox.showerror('Edit Error', error_msg)

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

            try:
                # Delete each selected supplier
                for item in selected_items:
                    # Get supplier details
                    values = self.tree.item(item)['values']
                    company_name = values[0]  # Using company name as identifier

                    # Delete from service
                    if self.supplier_service.delete_supplier(company_name):
                        # Track deleted items for potential undo
                        deleted_items.append((item, values))

                        # Remove from treeview
                        self.tree.delete(item)

                # Update undo/redo stacks
                if deleted_items:
                    self.undo_stack.append(('delete', deleted_items))
                    self.redo_stack.clear()

                # Log success
                logger.info(f'Successfully deleted {len(deleted_items)} suppliers')
                messagebox.showinfo('Success', f'{len(deleted_items)} supplier(s) deleted')

            except Exception as inner_e:
                raise inner_e

        except Exception as e:
            error_msg = 'Failed to delete suppliers'
            logger.error(f'{error_msg}: {str(e)}')
            messagebox.showerror('Delete Error', error_msg)

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

            if action_type == 'edit':
                # Undo edit operation
                _, item, column, old_value, new_value = action

                # Get database column name
                db_column = self.field_mapping[column]

                # Get company name
                company_name = self.tree.item(item)['values'][0]

                # Update via service
                update_data = {db_column: old_value}
                result = self.supplier_service.update_supplier(company_name, update_data)

                if result:
                    # Update treeview
                    self.tree.set(item, column, old_value)

                    # Add to redo stack
                    self.redo_stack.append(('edit', item, column, old_value, new_value))

            elif action_type == 'delete':
                # Undo delete operation
                deleted_items = action[1]
                restored_items = []

                for item, values in deleted_items:
                    # Prepare data for reinsertion
                    data = {}
                    for i, col in enumerate(self.columns):
                        db_field = self.field_mapping[col]
                        try:
                            data[db_field] = values[i]
                        except IndexError:
                            data[db_field] = ""

                    # Create supplier via service
                    result = self.supplier_service.create_supplier(data)

                    if result:
                        # Reinsert into treeview
                        new_item = self.tree.insert('', 'end', values=values)
                        restored_items.append((new_item, values))

                # Add to redo stack
                if restored_items:
                    self.redo_stack.append(('undelete', restored_items))

            elif action_type == 'add':
                # Undo add operation
                data = action[1]
                company_name = data['company_name']

                # Delete via service
                if self.supplier_service.delete_supplier(company_name):
                    # Remove from treeview
                    for item in self.tree.get_children():
                        if self.tree.item(item)['values'][0] == company_name:
                            self.tree.delete(item)
                            break

                    # Add to redo stack
                    self.redo_stack.append(('readd', data))

        except Exception as e:
            error_msg = 'Failed to undo action'
            logger.error(f'{error_msg}: {str(e)}')
            messagebox.showerror('Undo Error', error_msg)

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

            if action_type == 'edit':
                # Redo edit operation
                _, item, column, old_value, new_value = action

                # Get database column name
                db_column = self.field_mapping[column]

                # Get company name
                company_name = self.tree.item(item)['values'][0]

                # Update via service
                update_data = {db_column: new_value}
                result = self.supplier_service.update_supplier(company_name, update_data)

                if result:
                    # Update treeview
                    self.tree.set(item, column, new_value)

                    # Add to undo stack
                    self.undo_stack.append(('edit', item, column, old_value, new_value))

            elif action_type == 'undelete':
                # Redo undelete (which is actually a delete)
                restored_items = action[1]
                deleted_items = []

                for item, values in restored_items:
                    # Delete from service
                    company_name = values[0]
                    if self.supplier_service.delete_supplier(company_name):
                        # Remove from treeview
                        self.tree.delete(item)
                        deleted_items.append((item, values))

                # Add to undo stack
                if deleted_items:
                    self.undo_stack.append(('delete', deleted_items))

            elif action_type == 'readd':
                # Redo add operation
                data = action[1]

                # Create via service
                result = self.supplier_service.create_supplier(data)

                if result:
                    # Insert into treeview
                    values = []
                    for column in self.columns:
                        db_field = self.field_mapping[column]
                        values.append(data.get(db_field, ""))

                    self.tree.insert('', 'end', values=values)

                    # Add to undo stack
                    self.undo_stack.append(('add', data))

        except Exception as e:
            error_msg = 'Failed to redo action'
            logger.error(f'{error_msg}: {str(e)}')
            messagebox.showerror('Redo Error', error_msg)

