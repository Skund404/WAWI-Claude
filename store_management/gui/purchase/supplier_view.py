# relative path: store_management/gui/sale/supplier_view.py
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

from gui.base_view import BaseView
from services.interfaces.supplier_service import ISupplierService, SupplierStatus

# Configure logging
logger = logging.getLogger(__name__)


class SupplierView(BaseView):
    """View for managing suppliers in the leatherworking application."""

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the supplier view.

        Args:
            parent: Parent widget
            app: Application instance with dependency container
        """
        super().__init__(parent, app)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Supplier View")

        # Initialize undo/redo stacks
        self.undo_stack = []
        self.redo_stack = []

        # Get supplier service
        self.supplier_service = self.get_service(ISupplierService)

        # Define column to DB field mapping
        self.field_mapping = {
            "Company": "name",
            "Contact": "contact",
            "Email": "email",
            "Phone": "phone",
            "Status": "status",
            "Rating": "rating",
            "Address": "address",
            "Notes": "notes"
        }

        # Define columns to display
        self.columns = ["Company", "Contact", "Email", "Phone", "Status", "Rating"]

        # Set up the UI
        self._setup_ui()

        # Load initial data
        self._load_data()

    def _setup_ui(self):
        """Set up the user interface."""
        # Create main layout
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # Add buttons
        ttk.Button(toolbar, text="New", command=self.on_new).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Edit", command=self.on_edit).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Delete", command=self.on_delete).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Search", command=self._show_search_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Filter", command=self._show_filter_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Refresh", command=self.on_refresh).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Undo", command=self._undo).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Redo", command=self._redo).pack(side=tk.LEFT, padx=5)

        # Add export/import buttons
        ttk.Button(toolbar, text="Export", command=self._export_data).pack(side=tk.RIGHT, padx=5)
        ttk.Button(toolbar, text="Import", command=self._import_data).pack(side=tk.RIGHT, padx=5)

        # Create treeview for suppliers
        self.tree = ttk.Treeview(main_frame, columns=self.columns, show="headings", selectmode="browse")

        # Configure columns
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind events
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Delete>", self._delete_selected)
        self.bind("<Control-z>", lambda e: self._undo())
        self.bind("<Control-y>", lambda e: self._redo())

    def _load_data(self):
        """Load supplier data."""
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Get suppliers from service
            suppliers = self.supplier_service.get_all_suppliers()

            # Populate treeview
            for supplier in suppliers:
                values = []
                for column in self.columns:
                    db_field = self.field_mapping[column]
                    values.append(supplier.get(db_field, ""))

                self.tree.insert("", tk.END, values=values)

            self.logger.info(f"Loaded {len(suppliers)} suppliers")

        except Exception as e:
            self.logger.error(f"Error loading suppliers: {str(e)}")
            messagebox.showerror("Error", f"Failed to load suppliers: {str(e)}")

    def on_new(self):
        """Handle creating a new supplier."""
        try:
            # Create dialog
            dialog = tk.Toplevel(self)
            dialog.title("New Supplier")
            dialog.geometry("500x400")
            dialog.transient(self)
            dialog.grab_set()

            # Create form
            form_frame = ttk.Frame(dialog, padding=10)
            form_frame.pack(fill=tk.BOTH, expand=True)

            # Form fields
            row = 0
            entries = {}

            for column in self.columns:
                ttk.Label(form_frame, text=column).grid(row=row, column=0, sticky=tk.W, pady=5)
                entry = ttk.Entry(form_frame, width=40)
                entry.grid(row=row, column=1, sticky=tk.W, pady=5)
                entries[self.field_mapping[column]] = entry
                row += 1

            # Additional fields
            ttk.Label(form_frame, text="Address").grid(row=row, column=0, sticky=tk.W, pady=5)
            address_entry = ttk.Entry(form_frame, width=40)
            address_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
            entries["address"] = address_entry
            row += 1

            ttk.Label(form_frame, text="Notes").grid(row=row, column=0, sticky=tk.W, pady=5)
            notes_text = tk.Text(form_frame, height=4, width=40)
            notes_text.grid(row=row, column=1, sticky=tk.W, pady=5)
            row += 1

            # Status combobox
            status_idx = self.columns.index("Status") if "Status" in self.columns else -1
            if status_idx >= 0:
                status_entry = entries[self.field_mapping["Status"]]
                status_entry.destroy()  # Remove the entry widget

                status_combo = ttk.Combobox(form_frame, values=[s.name for s in SupplierStatus], width=38)
                status_combo.set(SupplierStatus.ACTIVE.name)
                status_combo.grid(row=status_idx, column=1, sticky=tk.W, pady=5)
                entries[self.field_mapping["Status"]] = status_combo

            # Buttons
            button_frame = ttk.Frame(form_frame)
            button_frame.grid(row=row, column=0, columnspan=2, pady=10)

            def save_supplier():
                try:
                    # Validate form
                    supplier_data = {}
                    for field, widget in entries.items():
                        if hasattr(widget, "get"):
                            value = widget.get().strip()
                            supplier_data[field] = value

                    # Get notes
                    supplier_data["notes"] = notes_text.get("1.0", tk.END).strip()

                    # Validate required fields
                    if not supplier_data.get("name"):
                        messagebox.showerror("Error", "Supplier name is required")
                        return

                    # Save supplier
                    result = self.supplier_service.create_supplier(supplier_data)

                    if result:
                        messagebox.showinfo("Success", "Supplier created successfully")

                        # Add to undo stack
                        self.undo_stack.append(("add", supplier_data))
                        self.redo_stack.clear()

                        # Close dialog
                        dialog.destroy()

                        # Refresh view
                        self.on_refresh()

                except Exception as e:
                    self.logger.error(f"Error creating supplier: {str(e)}")
                    messagebox.showerror("Error", f"Failed to create supplier: {str(e)}")

            ttk.Button(button_frame, text="Save", command=save_supplier).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            self.logger.error(f"Error creating new supplier dialog: {str(e)}")
            messagebox.showerror("Error", f"Failed to open new supplier dialog: {str(e)}")

    def on_edit(self, event=None):
        """Handle editing a supplier."""
        try:
            # Get selected item
            selected_id = self.tree.selection()
            if not selected_id:
                messagebox.showinfo("Info", "Please select a supplier to edit")
                return

            # Get supplier values
            values = self.tree.item(selected_id[0], "values")
            if not values:
                return

            # Find supplier by name
            supplier_name = values[0]

            # Get supplier details
            suppliers = self.supplier_service.get_all_suppliers()
            supplier = next((s for s in suppliers if s["name"] == supplier_name), None)

            if not supplier:
                messagebox.showerror("Error", f"Supplier '{supplier_name}' not found")
                return

            # Create dialog
            dialog = tk.Toplevel(self)
            dialog.title(f"Edit Supplier: {supplier_name}")
            dialog.geometry("500x400")
            dialog.transient(self)
            dialog.grab_set()

            # Create form
            form_frame = ttk.Frame(dialog, padding=10)
            form_frame.pack(fill=tk.BOTH, expand=True)

            # Form fields
            row = 0
            entries = {}

            for column in self.columns:
                ttk.Label(form_frame, text=column).grid(row=row, column=0, sticky=tk.W, pady=5)
                entry = ttk.Entry(form_frame, width=40)
                entry.insert(0, supplier.get(self.field_mapping[column], ""))
                entry.grid(row=row, column=1, sticky=tk.W, pady=5)
                entries[self.field_mapping[column]] = entry
                row += 1

            # Additional fields
            ttk.Label(form_frame, text="Address").grid(row=row, column=0, sticky=tk.W, pady=5)
            address_entry = ttk.Entry(form_frame, width=40)
            address_entry.insert(0, supplier.get("address", ""))
            address_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
            entries["address"] = address_entry
            row += 1

            ttk.Label(form_frame, text="Notes").grid(row=row, column=0, sticky=tk.W, pady=5)
            notes_text = tk.Text(form_frame, height=4, width=40)
            notes_text.insert("1.0", supplier.get("notes", ""))
            notes_text.grid(row=row, column=1, sticky=tk.W, pady=5)
            row += 1

            # Status combobox
            status_idx = self.columns.index("Status") if "Status" in self.columns else -1
            if status_idx >= 0:
                status_entry = entries[self.field_mapping["Status"]]
                status_entry.destroy()  # Remove the entry widget

                status_combo = ttk.Combobox(form_frame, values=[s.name for s in SupplierStatus], width=38)
                status_combo.set(supplier.get("status", SupplierStatus.ACTIVE.name))
                status_combo.grid(row=status_idx, column=1, sticky=tk.W, pady=5)
                entries[self.field_mapping["Status"]] = status_combo

            # Buttons
            button_frame = ttk.Frame(form_frame)
            button_frame.grid(row=row, column=0, columnspan=2, pady=10)

            def save_supplier():
                try:
                    # Validate form
                    supplier_data = {}
                    for field, widget in entries.items():
                        if hasattr(widget, "get"):
                            value = widget.get().strip()
                            supplier_data[field] = value

                    # Get notes
                    supplier_data["notes"] = notes_text.get("1.0", tk.END).strip()

                    # Validate required fields
                    if not supplier_data.get("name"):
                        messagebox.showerror("Error", "Supplier name is required")
                        return

                    # Save supplier
                    result = self.supplier_service.update_supplier(supplier["id"], supplier_data)

                    if result:
                        messagebox.showinfo("Success", "Supplier updated successfully")

                        # Close dialog
                        dialog.destroy()

                        # Refresh view
                        self.on_refresh()

                except Exception as e:
                    self.logger.error(f"Error updating supplier: {str(e)}")
                    messagebox.showerror("Error", f"Failed to update supplier: {str(e)}")

            ttk.Button(button_frame, text="Save", command=save_supplier).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            self.logger.error(f"Error editing supplier: {str(e)}")
            messagebox.showerror("Error", f"Failed to edit supplier: {str(e)}")

    def on_delete(self):
        """Handle deleting suppliers (alias for _delete_selected)."""
        self._delete_selected()

    def on_refresh(self):
        """Refresh the supplier view."""
        self._load_data()

    def on_save(self):
        """Empty implementation for interface consistency."""
        pass

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

                    # Get all suppliers and filter manually
                    all_suppliers = self.supplier_service.get_all_suppliers()

                    # Filter suppliers based on search params
                    filtered_suppliers = []
                    for supplier in all_suppliers:
                        match = True
                        for field, search_term in search_params.items():
                            if field not in supplier or search_term.lower() not in str(supplier[field]).lower():
                                match = False
                                break
                        if match:
                            filtered_suppliers.append(supplier)

                    # Clear existing tree items
                    for item in self.tree.get_children():
                        self.tree.delete(item)

                    # Populate tree with results
                    for supplier in filtered_suppliers:
                        values = []
                        for column in self.columns:
                            values.append(supplier.get(self.field_mapping[column], ""))
                        self.tree.insert('', 'end', values=values)

                    # Close search dialog
                    search_dialog.destroy()

                    # Show result message
                    if not filtered_suppliers:
                        messagebox.showinfo('Search', 'No matching suppliers found')
                    else:
                        self.logger.info(f"Search found {len(filtered_suppliers)} suppliers")

                except Exception as e:
                    error_msg = 'Search failed'
                    self.logger.error(f'{error_msg}: {str(e)}')
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
            self.logger.error(f'{error_msg}: {str(e)}')
            messagebox.showerror('Dialog Error', error_msg)

    def _show_filter_dialog(self) -> None:
        """
        Open dialog to filter suppliers.
        """
        try:
            filter_dialog = tk.Toplevel(self)
            filter_dialog.title('Filter Suppliers')
            filter_dialog.geometry('400x400')

            # Define filter options
            filter_options = {
                'status': ['All'] + [s.name for s in SupplierStatus],
                'rating': ['All', '1+', '2+', '3+', '4+', '5']
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

                    # Get all suppliers
                    all_suppliers = self.supplier_service.get_all_suppliers()

                    # Filter based on criteria
                    filtered_suppliers = []
                    for supplier in all_suppliers:
                        match = True

                        # Check status filter
                        if 'status' in criteria and supplier.get('status') != criteria['status']:
                            match = False

                        # Check rating filter
                        if 'rating' in criteria:
                            min_rating = float(criteria['rating'].replace('+', ''))
                            supplier_rating = 0
                            try:
                                supplier_rating = float(supplier.get('rating', 0))
                            except (ValueError, TypeError):
                                pass

                            if supplier_rating < min_rating:
                                match = False

                        if match:
                            filtered_suppliers.append(supplier)

                    # Clear existing tree items
                    for item in self.tree.get_children():
                        self.tree.delete(item)

                    # Populate tree with filtered results
                    for supplier in filtered_suppliers:
                        values = []
                        for column in self.columns:
                            values.append(supplier.get(self.field_mapping[column], ""))
                        self.tree.insert('', 'end', values=values)

                    # Close filter dialog
                    filter_dialog.destroy()

                    # Show result message
                    if not filtered_suppliers:
                        messagebox.showinfo('Filter', 'No suppliers match the selected criteria')
                    else:
                        self.logger.info(f"Filter found {len(filtered_suppliers)} suppliers")

                except Exception as e:
                    error_msg = 'Filter operation failed'
                    self.logger.error(f'{error_msg}: {str(e)}')
                    messagebox.showerror('Filter Error', error_msg)

            # Button frame
            button_frame = ttk.Frame(filter_dialog)
            button_frame.grid(row=row, column=0, columnspan=2, pady=10)

            ttk.Button(button_frame, text='Apply', command=apply_filters).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text='Reset', command=self._reset_view).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text='Cancel', command=filter_dialog.destroy).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            error_msg = 'Failed to create filter dialog'
            self.logger.error(f'{error_msg}: {str(e)}')
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
            column_idx = int(column[1:]) - 1

            # Get column name
            if 0 <= column_idx < len(self.columns):
                column_name = self.columns[column_idx]
                self._start_cell_edit(item, column_name)

        except Exception as e:
            error_msg = 'Failed to handle double-click'
            self.logger.error(f'{error_msg}: {str(e)}')
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

            # Get supplier name (first column)
            supplier_values = self.tree.item(item)['values']
            supplier_name = supplier_values[0]  # Using name as identifier

            # Find supplier by name
            suppliers = self.supplier_service.get_all_suppliers()
            supplier = next((s for s in suppliers if s["name"] == supplier_name), None)

            if not supplier:
                messagebox.showerror("Error", f"Supplier '{supplier_name}' not found")
                return

            # Create edit dialog
            edit_dialog = tk.Toplevel(self)
            edit_dialog.title(f'Edit {column}')

            # Position dialog near the cell
            x, y, _, _ = self.tree.bbox(item, column)
            edit_dialog.geometry(
                f'+{x + self.winfo_rootx()}+{y + self.winfo_rooty()}'
            )

            # Create widget based on column type
            field = self.field_mapping[column]

            # Status dropdown for status column
            if field == "status":
                widget = ttk.Combobox(edit_dialog, values=[s.name for s in SupplierStatus], width=20)
                widget.set(current_value)
            else:
                # Regular entry for other columns
                widget = ttk.Entry(edit_dialog, width=30)
                widget.insert(0, current_value)

            widget.pack(padx=5, pady=5)
            widget.focus_set()

            def save_edit(event=None):
                """
                Save the edited cell value.
                """
                try:
                    new_value = widget.get()

                    # Only update if value changed
                    if new_value != current_value:
                        # Create update data
                        update_data = {field: new_value}

                        # Use service to update supplier
                        result = self.supplier_service.update_supplier(supplier["id"], update_data)

                        if result:
                            # Update treeview
                            self.tree.set(item, column, new_value)

                            # Store for undo
                            self.undo_stack.append(('edit', item, column, current_value, new_value, supplier["id"]))
                            self.redo_stack.clear()

                            self.logger.info(f"Updated {column} for supplier {supplier_name}")

                        # Close dialog
                        edit_dialog.destroy()

                except Exception as e:
                    error_msg = 'Failed to save edit'
                    self.logger.error(f'{error_msg}: {str(e)}')
                    messagebox.showerror('Edit Error', error_msg)

            def cancel_edit(event=None):
                """
                Cancel cell editing.
                """
                edit_dialog.destroy()

            # Bind events
            if hasattr(widget, "bind"):
                widget.bind('<Return>', save_edit)
                widget.bind('<Escape>', cancel_edit)

            # Create button frame
            button_frame = ttk.Frame(edit_dialog)
            button_frame.pack(fill=tk.X, padx=5, pady=5)

            ttk.Button(button_frame, text='Save', command=save_edit).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text='Cancel', command=cancel_edit).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            error_msg = 'Failed to start cell edit'
            self.logger.error(f'{error_msg}: {str(e)}')
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
                self.logger.debug('No items selected for deletion')
                messagebox.showinfo('Delete', 'No suppliers selected')
                return

            # Confirm deletion
            if not messagebox.askyesno(
                    'Confirm Delete',
                    f'Are you sure you want to delete {len(selected_items)} supplier(s)?'
            ):
                return

            self.logger.debug(f'Attempting to delete {len(selected_items)} suppliers')

            # Prepare for deletion tracking
            deleted_items = []

            try:
                # Delete each selected supplier
                for item in selected_items:
                    # Get supplier details
                    values = self.tree.item(item)['values']
                    supplier_name = values[0]  # Using name as identifier

                    # Find supplier by name
                    suppliers = self.supplier_service.get_all_suppliers()
                    supplier = next((s for s in suppliers if s["name"] == supplier_name), None)

                    if not supplier:
                        messagebox.showerror("Error", f"Supplier '{supplier_name}' not found")
                        continue

                    # Delete from service
                    if self.supplier_service.delete_supplier(supplier["id"]):
                        # Track deleted items for potential undo
                        deleted_items.append((item, values, supplier))

                        # Remove from treeview
                        self.tree.delete(item)

                # Update undo/redo stacks
                if deleted_items:
                    self.undo_stack.append(('delete', deleted_items))
                    self.redo_stack.clear()

                # Log success
                self.logger.info(f'Successfully deleted {len(deleted_items)} suppliers')
                messagebox.showinfo('Success', f'{len(deleted_items)} supplier(s) deleted')

            except Exception as inner_e:
                raise inner_e

        except Exception as e:
            error_msg = 'Failed to delete suppliers'
            self.logger.error(f'{error_msg}: {str(e)}')
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
                _, item, column, old_value, new_value, supplier_id = action

                # Get database column name
                field = self.field_mapping[column]

                # Update via service
                update_data = {field: old_value}
                result = self.supplier_service.update_supplier(supplier_id, update_data)

                if result:
                    # Update treeview
                    self.tree.set(item, column, old_value)

                    # Add to redo stack
                    self.redo_stack.append(('edit', item, column, old_value, new_value, supplier_id))

                    self.logger.info(f"Undid edit of {column}")

            elif action_type == 'delete':
                # Undo delete operation
                deleted_items = action[1]
                restored_items = []

                for item, values, supplier in deleted_items:
                    # Create supplier via service
                    result = self.supplier_service.create_supplier(supplier)

                    if result:
                        # Reinsert into treeview
                        new_item = self.tree.insert('', 'end', values=values)
                        restored_items.append((new_item, values, supplier))

                # Add to redo stack
                if restored_items:
                    self.redo_stack.append(('undelete', restored_items))

                    self.logger.info(f"Restored {len(restored_items)} suppliers")

            elif action_type == 'add':
                # Undo add operation
                supplier = action[1]

                # Delete via service
                if self.supplier_service.delete_supplier(supplier["id"]):
                    # Remove from treeview
                    for item in self.tree.get_children():
                        if self.tree.item(item)['values'][0] == supplier["name"]:
                            self.tree.delete(item)
                            break

                    # Add to redo stack
                    self.redo_stack.append(('readd', supplier))

                    self.logger.info(f"Undid addition of supplier {supplier['name']}")

        except Exception as e:
            error_msg = 'Failed to undo action'
            self.logger.error(f'{error_msg}: {str(e)}')
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
                _, item, column, old_value, new_value, supplier_id = action

                # Get database column name
                field = self.field_mapping[column]

                # Update via service
                update_data = {field: new_value}
                result = self.supplier_service.update_supplier(supplier_id, update_data)

                if result:
                    # Update treeview
                    self.tree.set(item, column, new_value)

                    # Add to undo stack
                    self.undo_stack.append(('edit', item, column, old_value, new_value, supplier_id))

                    self.logger.info(f"Redid edit of {column}")

            elif action_type == 'undelete':
                # Redo undelete (which is actually a delete)
                restored_items = action[1]
                deleted_items = []

                for item, values, supplier in restored_items:
                    # Delete from service
                    if self.supplier_service.delete_supplier(supplier["id"]):
                        # Remove from treeview
                        self.tree.delete(item)
                        deleted_items.append((item, values, supplier))

                # Add to undo stack
                if deleted_items:
                    self.undo_stack.append(('delete', deleted_items))

                    self.logger.info(f"Re-deleted {len(deleted_items)} suppliers")

            elif action_type == 'readd':
                # Redo add operation
                supplier = action[1]

                # Create via service
                result = self.supplier_service.create_supplier(supplier)

                if result:
                    # Insert into treeview
                    values = []
                    for column in self.columns:
                        values.append(supplier.get(self.field_mapping[column], ""))

                    self.tree.insert('', 'end', values=values)

                    # Add to undo stack
                    self.undo_stack.append(('add', supplier))

                    self.logger.info(f"Readded supplier {supplier['name']}")

        except Exception as e:
            error_msg = 'Failed to redo action'
            self.logger.error(f'{error_msg}: {str(e)}')
            messagebox.showerror('Redo Error', error_msg)

    def _reset_view(self):
        """Reset view to show all suppliers."""
        self._load_data()

    def _export_data(self):
        """Export suppliers to CSV or Excel."""
        try:
            # Ask for file path
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("All files", "*.*")
                ],
                title="Export Suppliers"
            )

            if not file_path:
                return

            # Get all suppliers
            suppliers = self.supplier_service.get_all_suppliers()

            # Format data for export
            export_data = []
            for supplier in suppliers:
                row = {}
                for key, field in self.field_mapping.items():
                    row[key] = supplier.get(field, "")
                export_data.append(row)

            # Export based on file extension
            if file_path.endswith(".xlsx"):
                # Export to Excel
                df = pd.DataFrame(export_data)
                df.to_excel(file_path, index=False)
            else:
                # Export to CSV
                df = pd.DataFrame(export_data)
                df.to_csv(file_path, index=False)

            self.logger.info(f"Exported {len(suppliers)} suppliers to {file_path}")
            messagebox.showinfo("Export", f"Successfully exported {len(suppliers)} suppliers to {file_path}")

        except Exception as e:
            error_msg = "Failed to export data"
            self.logger.error(f"{error_msg}: {str(e)}")
            messagebox.showerror("Export Error", error_msg)

    def _import_data(self):
        """Import suppliers from CSV or Excel."""
        try:
            # Ask for file path
            file_path = filedialog.askopenfilename(
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("All files", "*.*")
                ],
                title="Import Suppliers"
            )

            if not file_path:
                return

            # Read file based on extension
            if file_path.endswith(".xlsx"):
                # Import from Excel
                df = pd.read_excel(file_path)
            else:
                # Import from CSV
                df = pd.read_csv(file_path)

            # Convert to list of dicts
            records = df.to_dict(orient="records")

            # Map column names to database fields
            imported = 0
            updated = 0
            errors = 0

            for record in records:
                try:
                    # Map fields
                    supplier_data = {}
                    for column, value in record.items():
                        if column in self.field_mapping.values():
                            # Direct field mapping
                            supplier_data[column] = value
                        elif column in self.field_mapping:
                            # Column name is in keys
                            field = self.field_mapping[column]
                            supplier_data[field] = value

                    # Validate required fields
                    if not supplier_data.get("name"):
                        self.logger.warning(f"Skipping record without name: {record}")
                        errors += 1
                        continue

                    # Check if supplier exists
                    existing_suppliers = self.supplier_service.get_all_suppliers()
                    existing = next((s for s in existing_suppliers if s["name"] == supplier_data["name"]), None)

                    if existing:
                        # Update existing supplier
                        result = self.supplier_service.update_supplier(existing["id"], supplier_data)
                        if result:
                            updated += 1
                    else:
                        # Create new supplier
                        result = self.supplier_service.create_supplier(supplier_data)
                        if result:
                            imported += 1

                except Exception as record_error:
                    self.logger.error(f"Error importing record: {record}. Error: {str(record_error)}")
                    errors += 1

            # Refresh view
            self._load_data()

            # Show summary
            summary = f"Import complete:\n- {imported} suppliers added\n- {updated} suppliers updated"
            if errors > 0:
                summary += f"\n- {errors} errors encountered"

            self.logger.info(summary)
            messagebox.showinfo("Import", summary)

        except Exception as e:
            error_msg = "Failed to import data"
            self.logger.error(f"{error_msg}: {str(e)}")
            messagebox.showerror("Import Error", error_msg)