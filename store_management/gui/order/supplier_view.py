import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import csv
import pandas as pd

# Update the import for DatabaseManager
from database.db_manager import DatabaseManager

# Update the import for config
from config import DATABASE_PATH, TABLES, COLORS


class SupplierView(ttk.Frame):
    def load_data(self):
        """Load supplier data from the database and populate the treeview"""
        try:
            # Clear existing items in the treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Connect to the database
            self.db.connect()

            # Print out the table name to verify
            print(f"Attempting to load from table: {TABLES['SUPPLIER']}")

            # Fetch all suppliers
            query = f"SELECT * FROM {TABLES['SUPPLIER']}"

            try:
                results = self.db.execute_query(query)
            except Exception as query_error:
                # More detailed error information
                print(f"Query Error: {query_error}")
                # Check if table exists
                table_check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
                existing_tables = self.db.execute_query(table_check_query, (TABLES['SUPPLIER'],))
                print(f"Table exists: {bool(existing_tables)}")

                # List all tables in the database
                list_tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
                tables = self.db.execute_query(list_tables_query)
                print("Existing tables:")
                for table in tables:
                    print(table[0])

                raise

            # Populate treeview
            if results:
                for row in results:
                    self.tree.insert("", "end", values=row)
            else:
                print("No results found in the supplier table")

        except Exception as e:
            # Capture the full error details
            import traceback
            error_details = traceback.format_exc()
            messagebox.showerror("Load Error", f"Failed to load suppliers: {e}\n\nDetails: {error_details}")

        finally:
            # Always disconnect from the database
            self.db.disconnect()
    def delete_selected(self, event=None):
        """Delete selected supplier(s) from the treeview and database"""
        # Get selected items
        selected_items = self.tree.selection()

        if not selected_items:
            messagebox.showinfo("Delete", "No suppliers selected")
            return

        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {len(selected_items)} supplier(s)?"):
            try:
                self.db.connect()

                # Store deleted items for potential undo
                deleted_items = []

                for item in selected_items:
                    # Get the values of the selected item
                    values = self.tree.item(item)['values']

                    # Delete from database
                    self.db.delete_record(
                        TABLES['SUPPLIER'],
                        "company_name = ?",
                        (values[0],)  # Using company name as unique identifier
                    )

                    # Store for potential undo
                    deleted_items.append((item, values))

                    # Remove from treeview
                    self.tree.delete(item)

                # Add to undo stack
                self.undo_stack.append(("delete", deleted_items))
                self.redo_stack.clear()

                messagebox.showinfo("Success", f"{len(selected_items)} supplier(s) deleted")

            except Exception as e:
                messagebox.showerror("Delete Error", f"Failed to delete supplier(s): {str(e)}")

            finally:
                self.db.disconnect()
    def on_double_click(self, event):
        """Handle double-click event on a tree item"""
        # Get the selected item
        selected_item = self.tree.selection()

        if not selected_item:
            return

        # Get the values of the selected row
        values = self.tree.item(selected_item[0])['values']

        # Create a dialog to edit the selected supplier
        try:
            # Create a dialog window for editing the supplier
            edit_dialog = tk.Toplevel(self)
            edit_dialog.title("Edit Supplier")
            edit_dialog.geometry("400x600")

            # Create entry fields for supplier information
            fields = [
                "Company Name", "Contact Person", "Phone Number",
                "Email Address", "Website", "Street Address",
                "City", "State/Province", "Postal Code", "Country",
                "Tax ID", "Business Type", "Payment Terms",
                "Currency", "Bank Details", "Products Offered",
                "Lead Time", "Notes"
            ]

            # Dictionary to store entry widgets
            entry_widgets = {}

            # Create labels and entry fields, pre-filled with existing data
            for i, field in enumerate(fields):
                label = ttk.Label(edit_dialog, text=field)
                label.grid(row=i, column=0, padx=5, pady=5, sticky="w")

                entry = ttk.Entry(edit_dialog, width=40)
                entry.grid(row=i, column=1, padx=5, pady=5)

                # Convert field name to column name
                col_name = field.lower().replace(" ", "_")

                # Find the index of this column
                try:
                    col_index = self.columns.index(col_name)
                    # Pre-fill with existing value
                    entry.insert(0, str(values[col_index]) if col_index < len(values) else '')
                except ValueError:
                    pass

                entry_widgets[col_name] = entry

            # Save button
            def save_changes():
                # Collect updated data
                updated_data = {}
                for key, widget in entry_widgets.items():
                    updated_data[key] = widget.get()

                try:
                    self.db.connect()

                    # Store old values for undo
                    old_values = values

                    # Update database
                    if self.db.update_record(
                            TABLES['SUPPLIER'],
                            updated_data,
                            "company_name = ?",
                            (old_values[0],)
                    ):
                        # Update treeview
                        updated_row = [updated_data.get(col, '') for col in self.columns]
                        self.tree.item(selected_item[0], values=updated_row)

                        # Add to undo stack
                        self.undo_stack.append(("edit", selected_item[0], old_values))
                        self.redo_stack.clear()

                        # Close dialog
                        edit_dialog.destroy()
                        messagebox.showinfo("Success", "Supplier updated successfully")
                    else:
                        messagebox.showerror("Error", "Failed to update supplier")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update supplier: {str(e)}")
                finally:
                    self.db.disconnect()

            # Cancel button
            def cancel_dialog():
                edit_dialog.destroy()

            # Buttons frame
            buttons_frame = ttk.Frame(edit_dialog)
            buttons_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)

            save_btn = ttk.Button(buttons_frame, text="Save", command=save_changes)
            save_btn.pack(side=tk.LEFT, padx=5)

            cancel_btn = ttk.Button(buttons_frame, text="Cancel", command=cancel_dialog)
            cancel_btn.pack(side=tk.LEFT, padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open edit dialog: {str(e)}")
    def reset_view(self):
        """Reset the view by reloading data and clearing any existing filters or selections"""
        # Clear current treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Reload data from database
        self.load_data()
    def save_table(self):
        """Save the current supplier table data to a file"""
        try:
            # Open file dialog to choose save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ]
            )

            if not file_path:
                return  # User cancelled save

            # Collect data from treeview
            data = []
            # Add headers
            data.append(self.columns)

            # Add row data
            for item in self.tree.get_children():
                data.append(self.tree.item(item)['values'])

            # Determine file type and save accordingly
            if file_path.endswith('.csv'):
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    csv_writer = csv.writer(csvfile)
                    csv_writer.writerows(data)

            elif file_path.endswith('.xlsx'):
                import pandas as pd
                df = pd.DataFrame(data[1:], columns=data[0])
                df.to_excel(file_path, index=False)

            else:
                # Fallback to text file
                with open(file_path, 'w', encoding='utf-8') as txtfile:
                    for row in data:
                        txtfile.write('\t'.join(str(cell) for cell in row) + '\n')

            # Log the action
            self.db.connect()
            self.db.log_action(
                TABLES['SUPPLIER'],
                'export',
                f'Export to {file_path}',
                {'total_records': len(data) - 1}
            )
            self.db.disconnect()

            # Show success message
            messagebox.showinfo("Success", f"Supplier data saved to {file_path}")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save table: {str(e)}")
    def show_filter_dialog(self):
        """Open a dialog to filter suppliers"""
        try:
            # Create a filter dialog window
            filter_dialog = tk.Toplevel(self)
            filter_dialog.title("Filter Suppliers")
            filter_dialog.geometry("400x500")

            # Filter criteria frame
            filter_frame = ttk.Frame(filter_dialog)
            filter_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

            # Define filter options
            filter_options = {
                'Business Type': ['All', 'Manufacturer', 'Wholesaler', 'Distributor', 'Retailer'],
                'Payment Terms': ['All', 'Net 30', 'Net 60', 'COD', 'Net 90'],
                'Country': ['All'],  # This could be dynamically populated
                'Lead Time': ['All', '1-7 days', '7-14 days', '14-30 days', '30+ days']
            }

            # Populate countries dynamically
            try:
                self.db.connect()
                country_query = f"SELECT DISTINCT country FROM {TABLES['SUPPLIER']}"
                countries = self.db.execute_query(country_query)
                if countries:
                    filter_options['Country'].extend([country[0] for country in countries if country[0]])
            except Exception as e:
                print(f"Error fetching countries: {e}")
            finally:
                self.db.disconnect()

            # Combo boxes for filtering
            filter_widgets = {}
            for i, (label_text, options) in enumerate(filter_options.items()):
                # Label
                label = ttk.Label(filter_frame, text=label_text)
                label.grid(row=i, column=0, padx=5, pady=5, sticky="w")

                # Combobox
                combo = ttk.Combobox(filter_frame, values=options, state="readonly", width=30)
                combo.set('All')  # Default selection
                combo.grid(row=i, column=1, padx=5, pady=5)

                filter_widgets[label_text.lower().replace(" ", "_")] = combo

            def apply_filter():
                # Collect filter criteria
                filter_criteria = {}
                for key, widget in filter_widgets.items():
                    value = widget.get()
                    if value != 'All':
                        filter_criteria[key] = value

                # Clear current treeview
                for item in self.tree.get_children():
                    self.tree.delete(item)

                try:
                    self.db.connect()

                    # Construct dynamic SQL query
                    where_clauses = []
                    params = []
                    for key, value in filter_criteria.items():
                        where_clauses.append(f"{key} = ?")
                        params.append(value)

                    # Base query
                    query = f"SELECT * FROM {TABLES['SUPPLIER']}"

                    # Add WHERE clause if filter criteria exist
                    if where_clauses:
                        query += " WHERE " + " AND ".join(where_clauses)

                    # Execute filter
                    results = self.db.execute_query(query, tuple(params))

                    # Populate treeview with results
                    if results:
                        for row in results:
                            self.tree.insert("", "end", values=row)

                        messagebox.showinfo("Filter Results",
                                            f"Found {len(results)} matching suppliers")
                    else:
                        messagebox.showinfo("Filter Results", "No suppliers found")

                except Exception as e:
                    messagebox.showerror("Filter Error", str(e))
                finally:
                    self.db.disconnect()

            # Reset filter method
            def reset_filter():
                # Reset all combo boxes to 'All'
                for widget in filter_widgets.values():
                    widget.set('All')

                # Reload all data
                self.load_data()

            # Buttons frame
            button_frame = ttk.Frame(filter_dialog)
            button_frame.pack(pady=10)

            apply_btn = ttk.Button(button_frame, text="Apply Filter", command=apply_filter)
            apply_btn.pack(side=tk.LEFT, padx=5)

            reset_btn = ttk.Button(button_frame, text="Reset", command=reset_filter)
            reset_btn.pack(side=tk.LEFT, padx=5)

            cancel_btn = ttk.Button(button_frame, text="Cancel",
                                    command=filter_dialog.destroy)
            cancel_btn.pack(side=tk.LEFT, padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open filter dialog: {str(e)}")
    def show_add_dialog(self):
        """Open a dialog to add a new supplier"""
        try:
            # Create a dialog window for adding a new supplier
            add_dialog = tk.Toplevel(self)
            add_dialog.title("Add New Supplier")
            add_dialog.geometry("400x600")

            # Create entry fields for supplier information
            fields = [
                "Company Name", "Contact Person", "Phone Number",
                "Email Address", "Website", "Street Address",
                "City", "State/Province", "Postal Code", "Country",
                "Tax ID", "Business Type", "Payment Terms",
                "Currency", "Bank Details", "Products Offered",
                "Lead Time", "Notes"
            ]

            # Dictionary to store entry widgets
            entry_widgets = {}

            # Create labels and entry fields
            for i, field in enumerate(fields):
                label = ttk.Label(add_dialog, text=field)
                label.grid(row=i, column=0, padx=5, pady=5, sticky="w")

                entry = ttk.Entry(add_dialog, width=40)
                entry.grid(row=i, column=1, padx=5, pady=5)

                entry_widgets[field.lower().replace(" ", "_")] = entry

            # Save button
            def save_supplier():
                # Collect data from entry widgets
                supplier_data = {}
                for key, widget in entry_widgets.items():
                    supplier_data[key] = widget.get()

                try:
                    # Attempt to insert the new supplier into the database
                    self.db.connect()
                    if self.db.insert_record(TABLES['SUPPLIER'], supplier_data):
                        # Add to the treeview
                        self.tree.insert("", "end", values=[supplier_data.get(col, '') for col in self.columns])

                        # Add to undo stack
                        self.undo_stack.append(("add", supplier_data))
                        self.redo_stack.clear()

                        # Close the dialog
                        add_dialog.destroy()
                        messagebox.showinfo("Success", "Supplier added successfully")
                    else:
                        messagebox.showerror("Error", "Failed to add supplier")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to add supplier: {str(e)}")
                finally:
                    self.db.disconnect()

            # Cancel button
            def cancel_dialog():
                add_dialog.destroy()

            # Buttons frame
            buttons_frame = ttk.Frame(add_dialog)
            buttons_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)

            save_btn = ttk.Button(buttons_frame, text="Save", command=save_supplier)
            save_btn.pack(side=tk.LEFT, padx=5)

            cancel_btn = ttk.Button(buttons_frame, text="Cancel", command=cancel_dialog)
            cancel_btn.pack(side=tk.LEFT, padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open add supplier dialog: {str(e)}")
    def show_search_dialog(self):
        """Open a dialog to search for suppliers"""
        try:
            # Create a search dialog window
            search_dialog = tk.Toplevel(self)
            search_dialog.title("Search Suppliers")
            search_dialog.geometry("400x300")

            # Search criteria frame
            search_frame = ttk.Frame(search_dialog)
            search_frame.pack(padx=10, pady=10, fill=tk.X)

            # Search fields
            search_fields = [
                "Company Name", "Contact Person", "Phone Number",
                "Email Address", "City", "Country", "Business Type"
            ]

            # Create search entry widgets
            search_widgets = {}
            for i, field in enumerate(search_fields):
                label = ttk.Label(search_frame, text=field)
                label.grid(row=i // 2, column=(i % 2) * 2, padx=5, pady=5, sticky="w")

                entry = ttk.Entry(search_frame, width=30)
                entry.grid(row=i // 2, column=(i % 2) * 2 + 1, padx=5, pady=5)

                search_widgets[field.lower().replace(" ", "_")] = entry

            def perform_search():
                # Collect search criteria
                search_criteria = {}
                for key, widget in search_widgets.items():
                    value = widget.get().strip()
                    if value:
                        search_criteria[key] = value

                # Clear current treeview
                for item in self.tree.get_children():
                    self.tree.delete(item)

                try:
                    self.db.connect()

                    # Construct dynamic SQL query
                    where_clauses = []
                    params = []
                    for key, value in search_criteria.items():
                        # Use LIKE for partial matches
                        where_clauses.append(f"{key} LIKE ?")
                        params.append(f"%{value}%")

                    # Base query
                    query = f"SELECT * FROM {TABLES['SUPPLIER']}"

                    # Add WHERE clause if search criteria exist
                    if where_clauses:
                        query += " WHERE " + " AND ".join(where_clauses)

                    # Execute search
                    results = self.db.execute_query(query, tuple(params))

                    # Populate treeview with results
                    if results:
                        for row in results:
                            self.tree.insert("", "end", values=row)

                        messagebox.showinfo("Search Results",
                                            f"Found {len(results)} matching suppliers")
                    else:
                        messagebox.showinfo("Search Results", "No suppliers found")

                except Exception as e:
                    messagebox.showerror("Search Error", str(e))
                finally:
                    self.db.disconnect()

            # Search and Cancel buttons
            button_frame = ttk.Frame(search_dialog)
            button_frame.pack(pady=10)

            search_btn = ttk.Button(button_frame, text="Search", command=perform_search)
            search_btn.pack(side=tk.LEFT, padx=5)

            cancel_btn = ttk.Button(button_frame, text="Cancel",
                                    command=search_dialog.destroy)
            cancel_btn.pack(side=tk.LEFT, padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open search dialog: {str(e)}")
    def __init__(self, parent):
        super().__init__(parent)
        self.db = DatabaseManager(DATABASE_PATH)

        # Initialize undo/redo stacks
        self.undo_stack = []
        self.redo_stack = []

        # Setup UI components
        self.setup_toolbar()
        self.setup_table()
        self.load_data()

    def load_table(self):
        """Alias for load_data method"""
        self.load_data()
    def setup_toolbar(self):
        """Create the toolbar with all buttons"""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Left side buttons
        ttk.Button(toolbar, text="ADD", command=self.show_add_dialog).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(toolbar, text="Search", command=self.show_search_dialog).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(toolbar, text="Filter", command=self.show_filter_dialog).pack(
            side=tk.LEFT, padx=2
        )

        # Right side buttons
        ttk.Button(toolbar, text="Undo", command=self.undo).pack(
            side=tk.RIGHT, padx=2
        )
        ttk.Button(toolbar, text="Redo", command=self.redo).pack(
            side=tk.RIGHT, padx=2
        )
        ttk.Button(toolbar, text="Save", command=self.save_table).pack(
            side=tk.RIGHT, padx=2
        )
        ttk.Button(toolbar, text="Load", command=self.load_table).pack(
            side=tk.RIGHT, padx=2
        )
        ttk.Button(toolbar, text="Reset View", command=self.reset_view).pack(
            side=tk.RIGHT, padx=2
        )

    def setup_table(self):
        """Create the main table view"""
        # Define columns
        self.columns = [
            "company_name",
            "contact_person",
            "phone_number",
            "email_address",
            "website",
            "street_address",
            "city",
            "state_province",
            "postal_code",
            "country",
            "tax_id",
            "business_type",
            "payment_terms",
            "currency",
            "bank_details",
            "products_offered",
            "lead_time",
            "last_order_date",
            "notes",
        ]

        # Create table frame
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(expand=True, fill="both", padx=5, pady=5)

        # Create scrollbars
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal")

        # Create treeview
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=self.columns,
            show="headings",
            selectmode="extended",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
        )

        # Configure scrollbars
        vsb.configure(command=self.tree.yview)
        hsb.configure(command=self.tree.xview)

        # Setup headers and columns
        for col in self.columns:
            self.tree.heading(
                col,
                text=col.replace("_", " ").title(),
                command=lambda c=col: self.sort_column(c),
            )

            # Set column width based on content type
            if col in ["notes", "products_offered", "bank_details"]:
                width = 200
            elif col in ["street_address", "email_address", "website"]:
                width = 150
            else:
                width = 100

            self.tree.column(col, width=width, minwidth=50)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Configure grid weights
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

        # Bind events
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Delete>", self.delete_selected)

    def undo(self, event=None):
        """Undo last action"""
        if not self.undo_stack:
            return

        action = self.undo_stack.pop()
        action_type = action[0]

        try:
            self.db.connect()

            if action_type == "edit":
                item, old_values = action[1:]
                # Store current values for redo
                current_values = self.tree.item(item)["values"]
                self.redo_stack.append(("edit", item, current_values))

                # Restore old values
                self.tree.item(item, values=old_values)

                # Update database
                self.db.update_record(
                    TABLES["SUPPLIER"],
                    dict(zip(self.columns, old_values)),
                    "company_name = ?",
                    (old_values[0],),
                )

            elif action_type == "add":
                data = action[1]
                # Delete added supplier
                self.db.delete_record(
                    TABLES["SUPPLIER"],
                    "company_name = ?",
                    (data["company_name"],),
                )

                # Remove from tree
                for item in self.tree.get_children():
                    if self.tree.set(item, "company_name") == data["company_name"]:
                        self.tree.delete(item)
                        break

                self.redo_stack.append(("readd", data))

            elif action_type == "delete":
                deleted_items = action[1]
                restored_items = []

                for item_id, values in deleted_items:
                    # Restore to database
                    self.db.insert_record(
                        TABLES["SUPPLIER"], dict(zip(self.columns, values))
                    )

                    # Restore to tree
                    new_item = self.tree.insert("", "end", values=values)
                    restored_items.append((new_item, values))

                self.redo_stack.append(("undelete", restored_items))

            elif action_type == "undelete":
                restored_items = action[1]
                deleted_items = []

                for item, values in restored_items:
                    # Delete from database
                    self.db.delete_record(
                        TABLES["SUPPLIER"],
                        "company_name = ?",
                        (values[0],),
                    )

                    # Delete from tree
                    self.tree.delete(item)
                    deleted_items.append((item, values))

                self.undo_stack.append(("delete", deleted_items))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to undo: {str(e)}")
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

            if action_type == "edit":
                item, new_values = action[1:]
                # Store current values for undo
                current_values = self.tree.item(item)["values"]
                self.undo_stack.append(("edit", item, current_values))

                # Restore new values
                self.tree.item(item, values=new_values)

                # Update database
                self.db.update_record(
                    TABLES["SUPPLIER"],
                    dict(zip(self.columns, new_values)),
                    "company_name = ?",
                    (new_values[0],),
                )

            elif action_type == "readd":
                data = action[1]
                # Re-add the supplier
                if self.db.insert_record(TABLES["SUPPLIER"], data):
                    # Add to tree
                    self.tree.insert(
                        "", "end", values=[data[col] for col in self.columns]
                    )
                    self.undo_stack.append(("add", data))

            elif action_type == "undelete":
                restored_items = action[1]
                deleted_items = []

                for item, values in restored_items:
                    # Delete from database
                    self.db.delete_record(
                        TABLES["SUPPLIER"],
                        "company_name = ?",
                        (values[0],),
                    )

                    # Delete from tree
                    self.tree.delete(item)
                    deleted_items.append((item, values))

                self.undo_stack.append(("delete", deleted_items))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to redo: {str(e)}")
        finally:
            self.db.disconnect()
