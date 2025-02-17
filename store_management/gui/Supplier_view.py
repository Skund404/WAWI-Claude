# gui/supplier_view.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import csv
import pandas as pd

# Update imports to use absolute paths from project root
from database.db_manager import DatabaseManager
from utils.logger import logger, log_error
from utils.error_handler import ErrorHandler, check_database_connection, DatabaseError
from config import DATABASE_PATH, TABLES, COLORS


class supplierView(ttk.Frame):
    def handle_return(self, event=None):
        """Handle Return key press"""
        pass

    def handle_escape(self, event=None):
        """Handle Escape key press"""
        pass
    def show_search_dialog(self):
        """Open dialog to search suppliers"""
        try:
            search_dialog = tk.Toplevel(self)
            search_dialog.title("Search Suppliers")
            search_dialog.geometry("400x300")

            # Create search fields
            search_fields = ["company_name", "contact_person", "email_address", "phone_number"]
            entry_widgets = {}

            for i, field in enumerate(search_fields):
                label = ttk.Label(search_dialog, text=field.replace("_", " ").title())
                label.grid(row=i, column=0, padx=5, pady=5, sticky="w")

                entry = ttk.Entry(search_dialog, width=30)
                entry.grid(row=i, column=1, padx=5, pady=5)
                entry_widgets[field] = entry

            def perform_search():
                try:
                    # Build search conditions
                    conditions = []
                    params = []
                    for field, widget in entry_widgets.items():
                        value = widget.get().strip()
                        if value:
                            conditions.append(f"{field} LIKE ?")
                            params.append(f"%{value}%")

                    if not conditions:
                        messagebox.showinfo("Search", "Please enter at least one search term")
                        return

                    # Execute search
                    self.db.connect()
                    query = f"SELECT * FROM {TABLES['SUPPLIER']}"
                    if conditions:
                        query += " WHERE " + " AND ".join(conditions)

                    results = self.db.execute_query(query, tuple(params))

                    # Update view
                    for item in self.tree.get_children():
                        self.tree.delete(item)

                    for row in results:
                        self.tree.insert("", "end", values=row)

                    search_dialog.destroy()

                    if not results:
                        messagebox.showinfo("Search", "No matching suppliers found")

                except Exception as e:
                    error_msg = "Search failed"
                    log_error(e, error_msg)
                    ErrorHandler.show_error("Search Error", error_msg, e)
                finally:
                    self.db.disconnect()

            # Button frame
            button_frame = ttk.Frame(search_dialog)
            button_frame.grid(row=len(search_fields), column=0, columnspan=2, pady=10)

            ttk.Button(button_frame, text="Search", command=perform_search).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=search_dialog.destroy).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            error_msg = "Failed to create search dialog"
            log_error(e, error_msg)
            ErrorHandler.show_error("Dialog Error", error_msg, e)

    def show_filter_dialog(self):
        """Open dialog to filter suppliers"""
        try:
            filter_dialog = tk.Toplevel(self)
            filter_dialog.title("Filter Suppliers")
            filter_dialog.geometry("400x400")

            # Filter options
            filter_options = {
                'business_type': ['All', 'Manufacturer', 'Wholesaler', 'Distributor', 'Retailer'],
                'payment_terms': ['All', 'Net 30', 'Net 60', 'Net 90', 'Prepaid'],
                'country': ['All']
            }

            # Get unique countries from database
            try:
                self.db.connect()
                query = f"SELECT DISTINCT country FROM {TABLES['SUPPLIER']} WHERE country IS NOT NULL"
                countries = self.db.execute_query(query)
                if countries:
                    filter_options['country'].extend([country[0] for country in countries])
            except Exception as e:
                logger.error(f"Failed to fetch countries: {e}")
            finally:
                self.db.disconnect()

            # Create filter widgets
            filter_widgets = {}
            row = 0
            for field, options in filter_options.items():
                label = ttk.Label(filter_dialog, text=field.replace("_", " ").title())
                label.grid(row=row, column=0, padx=5, pady=5, sticky="w")

                combo = ttk.Combobox(filter_dialog, values=options, state="readonly", width=30)
                combo.set('All')
                combo.grid(row=row, column=1, padx=5, pady=5)

                filter_widgets[field] = combo
                row += 1

            def apply_filters():
                try:
                    criteria = {}
                    for field, widget in filter_widgets.items():
                        value = widget.get()
                        if value and value != 'All':
                            criteria[field] = value

                    query = f"SELECT * FROM {TABLES['SUPPLIER']}"
                    params = []

                    if criteria:
                        conditions = []
                        for field, value in criteria.items():
                            conditions.append(f"{field} = ?")
                            params.append(value)
                        query += " WHERE " + " AND ".join(conditions)

                    self.db.connect()
                    results = self.db.execute_query(query, tuple(params))

                    # Update view
                    for item in self.tree.get_children():
                        self.tree.delete(item)

                    for row in results:
                        self.tree.insert("", "end", values=row)

                    filter_dialog.destroy()

                    if not results:
                        messagebox.showinfo("Filter", "No suppliers match the selected criteria")

                except Exception as e:
                    error_msg = "Filter operation failed"
                    log_error(e, error_msg)
                    ErrorHandler.show_error("Filter Error", error_msg, e)
                finally:
                    self.db.disconnect()

            def reset_filters():
                try:
                    # Reset all combo boxes
                    for widget in filter_widgets.values():
                        widget.set('All')
                    # Reload all data
                    self.load_data()
                except Exception as e:
                    error_msg = "Failed to reset filters"
                    log_error(e, error_msg)
                    ErrorHandler.show_error("Reset Error", error_msg, e)

            # Button frame
            button_frame = ttk.Frame(filter_dialog)
            button_frame.grid(row=row, column=0, columnspan=2, pady=10)

            ttk.Button(button_frame, text="Apply", command=apply_filters).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Reset", command=reset_filters).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=filter_dialog.destroy).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            error_msg = "Failed to create filter dialog"
            log_error(e, error_msg)
            ErrorHandler.show_error("Dialog Error", error_msg, e)

    @check_database_connection
    def save_table(self):
        """Save the current table data to a file"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("All files", "*.*")
                ]
            )

            if not file_path:
                return

            # Collect data
            data = [self.columns]  # Headers
            for item in self.tree.get_children():
                data.append(self.tree.item(item)['values'])

            # Save based on file type
            if file_path.endswith('.csv'):
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(data)
            elif file_path.endswith('.xlsx'):
                df = pd.DataFrame(data[1:], columns=data[0])
                df.to_excel(file_path, index=False)

            logger.info(f"Table saved to: {file_path}")
            messagebox.showinfo("Success", "Table saved successfully")

        except Exception as e:
            error_msg = "Failed to save table"
            log_error(e, error_msg)
            ErrorHandler.show_error("Save Error", error_msg, e)

    def __init__(self, parent):
        try:
            super().__init__(parent)

            # Explicitly connect to the database
            self.db = DatabaseManager(DATABASE_PATH)
            self.db.connect()  # Explicitly call connect method

            # Initialize undo/redo stacks
            self.undo_stack = []
            self.redo_stack = []

            # Setup UI components
            self.setup_toolbar()
            self.setup_table()

            # Load data with error handling
            self.load_data()

            logger.info("SupplierView initialized successfully")

        except Exception as init_error:
            logger.error(f"Supplier View Initialization Error: {init_error}")
            ErrorHandler.show_error("Initialization Error",
                                    "Failed to initialize Supplier View",
                                    init_error)
            raise

    def setup_toolbar(self):
        """Create the toolbar with all buttons"""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Left side buttons (ADD, Search, Filter)
        left_frame = ttk.Frame(toolbar)
        left_frame.pack(side=tk.LEFT, fill=tk.X)

        ttk.Button(left_frame, text="ADD",
                   command=self.show_add_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_frame, text="Search",
                   command=self.show_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_frame, text="Filter",
                   command=self.show_filter_dialog).pack(side=tk.LEFT, padx=2)

        # Right side buttons (Save, Load, Undo, Redo, Reset View)
        right_frame = ttk.Frame(toolbar)
        right_frame.pack(side=tk.RIGHT, fill=tk.X)

        ttk.Button(right_frame, text="Save",
                   command=self.save_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(right_frame, text="Load",
                   command=self.load_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(right_frame, text="Undo",
                   command=self.undo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(right_frame, text="Redo",
                   command=self.redo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(right_frame, text="Reset View",
                   command=self.reset_view).pack(side=tk.RIGHT, padx=2)

    def setup_table(self):
        """Create the main table view"""
        # Create table frame
        table_frame = ttk.Frame(self)
        table_frame.pack(expand=True, fill='both', padx=5, pady=5)

        # Define columns
        self.columns = [
            "Company Name", "Contact Person", "Phone Number",
            "Email Address", "Website", "Street Address",
            "City", "State/Province", "Postal Code", "Country",
            "Tax ID", "Business Type", "Payment Terms",
            "Currency", "Bank Details", "Products Offered",
            "Lead Time", "Last Order Date", "Notes"
        ]

        # Create scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")

        # Create treeview
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

        # Setup columns
        for col in self.columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_column(c))

            # Set column widths
            if col in ["Notes", "Products Offered", "Bank Details"]:
                width = 200
            elif col in ["Street Address", "Email Address", "Website"]:
                width = 150
            else:
                width = 100

            self.tree.column(col, width=width, minwidth=50)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        # Bind events
        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<Delete>', self.delete_selected)

    @check_database_connection
    def load_data(self):
        """Load supplier data from the database and populate the treeview"""
        try:
            logger.debug("Loading supplier data")

            # Verify database connection
            if not self.db or not self.db.conn:
                self.db.connect()

            # Verify table exists and has correct structure
            if not self.db.table_exists(TABLES['SUPPLIER']):
                raise DatabaseError(f"Table {TABLES['SUPPLIER']} does not exist")

            # Fetch all suppliers
            query = f"SELECT * FROM {TABLES['SUPPLIER']}"
            results = self.db.execute_query(query)

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Populate treeview
            if results:
                for row in results:
                    self.tree.insert("", "end", values=row)
                logger.info(f"Loaded {len(results)} suppliers")
            else:
                logger.info("No suppliers found in database")

        except Exception as e:
            error_msg = f"Failed to load supplier data: {str(e)}"
            logger.error(error_msg)
            ErrorHandler.show_error("Load Error", error_msg, e)
            raise

    def load_table(self):
        """Alias for load_data method"""
        self.load_data()

    def reset_view(self):
        """Reset the view to show all suppliers"""
        try:
            logger.debug("Resetting view")
            self.load_data()
            logger.info("View reset successfully")
        except Exception as e:
            error_msg = "Failed to reset view"
            log_error(e, error_msg)
            ErrorHandler.show_error("Reset Error", error_msg, e)

    def show_add_dialog(self):
        """Open dialog to add a new supplier"""
        try:
            add_dialog = tk.Toplevel(self)
            add_dialog.title("Add New Supplier")
            add_dialog.geometry("400x600")

            # Create scrollable frame
            canvas = tk.Canvas(add_dialog)
            scrollbar = ttk.Scrollbar(add_dialog, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            # Entry widgets
            entry_widgets = {}
            for i, field in enumerate(self.columns):
                label = ttk.Label(scrollable_frame, text=field.replace("_", " ").title())
                label.grid(row=i, column=0, padx=5, pady=5, sticky="w")

                entry = ttk.Entry(scrollable_frame, width=40)
                entry.grid(row=i, column=1, padx=5, pady=5)
                entry_widgets[field] = entry

            def save_supplier():
                try:
                    # Collect data
                    data = {field: widget.get() for field, widget in entry_widgets.items()}

                    # Validate required fields
                    if not data['company_name']:
                        raise ValueError("Company Name is required")

                    # Save to database
                    self.db.connect()
                    if self.db.insert_record(TABLES['SUPPLIER'], data):
                        self.tree.insert("", "end", values=[data[col] for col in self.columns])
                        add_dialog.destroy()
                        self.load_data()  # Refresh view
                        messagebox.showinfo("Success", "Supplier added successfully")
                    else:
                        raise DatabaseError("Failed to add supplier")

                except Exception as e:
                    error_msg = "Failed to add supplier"
                    log_error(e, error_msg)
                    ErrorHandler.show_error("Add Error", error_msg, e)
                finally:
                    self.db.disconnect()

            # Buttons
            button_frame = ttk.Frame(scrollable_frame)
            button_frame.grid(row=len(self.columns), column=0, columnspan=2, pady=10)

            ttk.Button(button_frame, text="Save", command=save_supplier).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=add_dialog.destroy).pack(side=tk.LEFT, padx=5)

            # Pack the canvas and scrollbar
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

        except Exception as e:
            error_msg = "Failed to create add dialog"
            log_error(e, error_msg)
            ErrorHandler.show_error("Dialog Error", error_msg, e)

    @check_database_connection
    def delete_selected(self, event=None):
        """Delete selected supplier(s)"""
        try:
            selected_items = self.tree.selection()

            if not selected_items:
                logger.debug("No items selected for deletion")
                messagebox.showinfo("Delete", "No suppliers selected")
                return

            if not messagebox.askyesno("Confirm Delete",
                                       f"Are you sure you want to delete {len(selected_items)} supplier(s)?"):
                return

            logger.debug(f"Attempting to delete {len(selected_items)} suppliers")

            deleted_items = []
            self.db.begin_transaction()

            try:
                for item in selected_items:
                    values = self.tree.item(item)['values']
                    if self.db.delete_record(
                            TABLES['SUPPLIER'],
                            "company_name = ?",
                            (values[0],)
                    ):
                        deleted_items.append((item, values))
                        self.tree.delete(item)

                self.db.commit_transaction()
                self.undo_stack.append(("delete", deleted_items))
                self.redo_stack.clear()

                logger.info(f"Successfully deleted {len(deleted_items)} suppliers")
                messagebox.showinfo("Success", f"{len(deleted_items)} supplier(s) deleted")

            except Exception as e:
                self.db.rollback_transaction()
                raise e

        except Exception as e:
            error_msg = "Failed to delete suppliers"
            log_error(e, error_msg)
            ErrorHandler.show_error("Delete Error", error_msg, e)

    def on_double_click(self, event):
        """Handle double-click event for editing"""
        try:
            selected_item = self.tree.selection()
            if not selected_item:
                return

            item = selected_item[0]
            column = self.tree.identify_column(event.x)
            column_id = int(column[1]) - 1  # Column numbers start at 1

            if column_id >= 0 and column_id < len(self.columns):
                self.start_cell_edit(item, self.columns[column_id])

        except Exception as e:
            error_msg = "Failed to handle double-click"
            log_error(e, error_msg)
            ErrorHandler.show_error("Edit Error", error_msg, e)

    def start_cell_edit(self, item, column):
        """Start editing a cell"""
        try:
            current_value = self.tree.set(item, column)

            # Create edit dialog
            edit_dialog = tk.Toplevel(self)
            edit_dialog.title(f"Edit {column.replace('_', ' ').title()}")

            # Position dialog near the cell
            x, y, _, _ = self.tree.bbox(item, column)
            edit_dialog.geometry(f"+{x + self.winfo_rootx()}+{y + self.winfo_rooty()}")

            # Entry widget
            entry = ttk.Entry(edit_dialog)
            entry.insert(0, current_value)
            entry.pack(padx=5, pady=5)
            entry.focus_set()

            def save_edit(event=None):
                try:
                    new_value = entry.get()
                    if new_value != current_value:
                        # Update database
                        self.db.connect()
                        data = {column: new_value}
                        if self.db.update_record(
                                TABLES['SUPPLIER'],
                                data,
                                "company_name = ?",
                                (self.tree.item(item)['values'][0],)
                        ):
                            # Update treeview
                            self.tree.set(item, column, new_value)
                            # Add to undo stack
                            self.undo_stack.append(("edit", item, column, current_value, new_value))
                            self.redo_stack.clear()
                    edit_dialog.destroy()

                except Exception as e:
                    error_msg = "Failed to save edit"
                    log_error(e, error_msg)
                    ErrorHandler.show_error("Edit Error", error_msg, e)
                finally:
                    self.db.disconnect()

            def cancel_edit(event=None):
                edit_dialog.destroy()

            # Bind events
            entry.bind('<Return>', save_edit)
            entry.bind('<Escape>', cancel_edit)

            # Buttons
            button_frame = ttk.Frame(edit_dialog)
            button_frame.pack(fill=tk.X, padx=5, pady=5)

            ttk.Button(button_frame, text="Save", command=save_edit).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=cancel_edit).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            error_msg = "Failed to start cell edit"
            log_error(e, error_msg)
            ErrorHandler.show_error("Edit Error", error_msg, e)

    def undo(self):
        """Undo last action"""
        try:
            if not self.undo_stack:
                return

            action = self.undo_stack.pop()
            action_type = action[0]

            self.db.connect()

            if action_type == "edit":
                item, column, old_value, new_value = action[1:]
                # Revert to old value
                data = {column: old_value}
                if self.db.update_record(
                        TABLES['SUPPLIER'],
                        data,
                        "company_name = ?",
                        (self.tree.item(item)['values'][0],)
                ):
                    self.tree.set(item, column, old_value)
                    self.redo_stack.append(("edit", item, column, old_value, new_value))

            elif action_type == "delete":
                deleted_items = action[1]
                restored_items = []

                for item, values in deleted_items:
                    data = dict(zip(self.columns, values))
                    if self.db.insert_record(TABLES['SUPPLIER'], data):
                        new_item = self.tree.insert("", "end", values=values)
                        restored_items.append((new_item, values))

                self.redo_stack.append(("undelete", restored_items))

            elif action_type == "add":
                company_name = action[1]['company_name']
                if self.db.delete_record(TABLES['SUPPLIER'], "company_name = ?", (company_name,)):
                    for item in self.tree.get_children():
                        if self.tree.item(item)['values'][0] == company_name:
                            self.tree.delete(item)
                            break
                    self.redo_stack.append(("readd", action[1]))

        except Exception as e:
            error_msg = "Failed to undo action"
            log_error(e, error_msg)
            ErrorHandler.show_error("Undo Error", error_msg, e)
        finally:
            self.db.disconnect()

    def redo(self):
        """Redo last undone action"""
        try:
            if not self.redo_stack:
                return

            action = self.redo_stack.pop()
            action_type = action[0]

            self.db.connect()

            if action_type == "edit":
                item, column, old_value, new_value = action[1:]
                # Restore new value
                data = {column: new_value}
                if self.db.update_record(
                        TABLES['SUPPLIER'],
                        data,
                        "company_name = ?",
                        (self.tree.item(item)['values'][0],)
                ):
                    self.tree.set(item, column, new_value)
                    self.undo_stack.append(("edit", item, column, old_value, new_value))

            elif action_type == "undelete":
                restored_items = action[1]
                deleted_items = []

                for item, values in restored_items:
                    if self.db.delete_record(
                            TABLES['SUPPLIER'],
                            "company_name = ?",
                            (values[0],)
                    ):
                        self.tree.delete(item)
                        deleted_items.append((item, values))

                self.undo_stack.append(("delete", deleted_items))

            elif action_type == "readd":
                data = action[1]
                if self.db.insert_record(TABLES['SUPPLIER'], data):
                    values = [data[col] for col in self.columns]
                    self.tree.insert("", "end", values=values)
                    self.undo_stack.append(("add", data))

        except Exception as e:
            error_msg = "Failed to redo action"
            log_error(e, error_msg)
            ErrorHandler.show_error("Redo Error", error_msg, e)
        finally:
            self.db.disconnect()

    def sort_column(self, column):
        """Sort tree contents when a column header is clicked"""
        try:
            logger.debug(f"Sorting by column: {column}")

            items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]
            items.sort(reverse=getattr(self, "_sort_reverse", False))

            for index, (_, item) in enumerate(items):
                self.tree.move(item, '', index)

            self._sort_reverse = not getattr(self, "_sort_reverse", False)

            # Update header with sort indicator
            for col in self.columns:
                if col == column:
                    indicator = "▼" if self._sort_reverse else "▲"
                    self.tree.heading(col, text=f"{col.replace('_', ' ').title()} {indicator}")
                else:
                    self.tree.heading(col, text=col.replace('_', ' ').title())

        except Exception as e:
            error_msg = f"Failed to sort column: {column}"
            log_error(e, error_msg)
            ErrorHandler.show_error("Sort Error", error_msg, e)
