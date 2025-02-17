import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import csv
from typing import Dict, List, Optional
import uuid
from datetime import datetime
from pathlib import Path
from database.db_manager import DatabaseManager
from config import DATABASE_PATH, TABLES, COLORS


class ShoppingListView(ttk.Frame):
    def save_table(self):
        """Save current table state"""
        if not self.current_list:
            messagebox.showwarning("Warning", "Please select a shopping list first")
            return

        try:
            # Get file path for saving
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("All files", "*.*")
                ],
                initialfile=f"shopping_list_{self.current_list}"
            )

            if not file_path:
                return

            file_path = Path(file_path)

            # Get current table data
            data = []
            for item in self.tree.get_children():
                values = self.tree.item(item)['values']
                row_data = dict(zip(self.columns, values))
                data.append(row_data)

            if file_path.suffix == '.csv':
                # Save as CSV
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.columns)
                    writer.writeheader()
                    writer.writerows(data)
            else:
                # Save as Excel
                import pandas as pd
                df = pd.DataFrame(data)
                df.to_excel(file_path, index=False)

            messagebox.showinfo("Success", "Shopping list saved successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save shopping list: {str(e)}")

    def load_table(self):
        """Load saved table state"""
        if not self.current_list:
            messagebox.showwarning("Warning", "Please select a shopping list first")
            return

        try:
            # Get file path for loading
            file_path = filedialog.askopenfilename(
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("All files", "*.*")
                ]
            )

            if not file_path:
                return

            file_path = Path(file_path)

            # Create backup before loading
            self.db.connect()
            backup_query = f"CREATE TABLE IF NOT EXISTS shopping_list_{self.current_list}_backup AS SELECT * FROM shopping_list_{self.current_list}"
            self.db.execute_query(backup_query)

            # Clear current table
            clear_query = f"DELETE FROM shopping_list_{self.current_list}"
            self.db.execute_query(clear_query)

            # Load data based on file type
            if file_path.suffix == '.csv':
                # Load from CSV
                import csv
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self.db.insert_record(f"shopping_list_{self.current_list}", row)
            else:
                # Load from Excel
                import pandas as pd
                df = pd.read_excel(file_path)
                for _, row in df.iterrows():
                    self.db.insert_record(f"shopping_list_{self.current_list}", row.to_dict())

            # Refresh view
            self.load_data()
            messagebox.showinfo("Success", "Shopping list loaded successfully")

        except Exception as e:
            # Restore from backup if exists
            try:
                restore_query = f"""
                    DELETE FROM shopping_list_{self.current_list};
                    INSERT INTO shopping_list_{self.current_list} 
                    SELECT * FROM shopping_list_{self.current_list}_backup;
                """
                self.db.execute_query(restore_query)
                self.load_data()
            except:
                pass

            messagebox.showerror("Error", f"Failed to load shopping list: {str(e)}")

        finally:
            try:
                # Drop backup table
                self.db.execute_query(f"DROP TABLE IF EXISTS shopping_list_{self.current_list}_backup")
            except:
                pass
            self.db.disconnect()

    def show_filter_dialog(self):
        """Show filter dialog"""
        if not self.current_list:
            messagebox.showwarning("Warning", "Please select a shopping list first")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Filter Items")
        dialog.transient(self)
        dialog.grab_set()

        # Create main frame
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
                values=self.columns,
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
                    messagebox.showwarning("Warning", "No valid filter conditions")
                    return

                # Build query
                query = f"SELECT * FROM shopping_list_{self.current_list} WHERE "
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
                query += " ORDER BY supplier, article"

                # Execute query
                self.db.connect()
                results = self.db.execute_query(query, tuple(params))

                # Update table
                for item in self.tree.get_children():
                    self.tree.delete(item)

                for row in results:
                    self.tree.insert('', 'end', values=row[:-2])  # Exclude timestamps

                dialog.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Filter error: {str(e)}")
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

    def show_search_dialog(self):
        """Show search dialog"""
        dialog = tk.Toplevel(self)
        dialog.title("Search Items")
        dialog.transient(self)
        dialog.grab_set()

        # Create main frame
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
            text="Supplier",
            value="supplier",
            variable=target_var
        ).pack(anchor='w')
        ttk.Radiobutton(
            main_frame,
            text="Article",
            value="article",
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
                messagebox.showwarning("Warning", "Please enter search text")
                return

            # Clear current selection
            self.tree.selection_remove(*self.tree.selection())
            found = False

            for item in self.tree.get_children():
                values = self.tree.item(item)['values']

                if target_var.get() == "all":
                    text = " ".join(str(v) for v in values)
                else:
                    col_idx = self.columns.index(target_var.get())
                    text = str(values[col_idx])

                if not match_case.get():
                    text = text.lower()
                    search_text = search_text.lower()

                if search_text in text:
                    self.tree.selection_add(item)
                    self.tree.see(item)
                    found = True

            if not found:
                messagebox.showinfo("Info", "No matches found")

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

    def __init__(self, parent):
        super().__init__(parent)
        self.db = DatabaseManager(DATABASE_PATH)

        # Initialize undo/redo stacks
        self.undo_stack = []
        self.redo_stack = []

        # Current shopping list
        self.current_list = None

        # Setup UI components
        self.setup_toolbar()
        self.setup_table_selection()
        self.setup_table()
        self.load_shopping_lists()

    def setup_toolbar(self):
        """Create the toolbar with all buttons"""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Left side buttons
        ttk.Button(toolbar, text="ADD",
                   command=self.show_add_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Search",
                   command=self.show_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Filter",
                   command=self.show_filter_dialog).pack(side=tk.LEFT, padx=2)

        # Right side buttons
        ttk.Button(toolbar, text="Undo", command=self.undo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Redo", command=self.redo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Load", command=self.load_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Reset View",
                   command=self.reset_view).pack(side=tk.RIGHT, padx=2)

    def setup_table_selection(self):
        """Create shopping list selection dropdown"""
        selection_frame = ttk.Frame(self)
        selection_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(selection_frame, text="Select Shopping List:").pack(side=tk.LEFT, padx=5)

        self.list_var = tk.StringVar()
        self.list_combo = ttk.Combobox(selection_frame, textvariable=self.list_var)
        self.list_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(selection_frame, text="New List",
                   command=self.create_new_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(selection_frame, text="Delete List",
                   command=self.delete_list).pack(side=tk.LEFT, padx=5)

        self.list_var.trace('w', self.on_list_select)

    def setup_table(self):
        """Create the main table view"""
        # Create table frame
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(expand=True, fill='both', padx=5, pady=5)

        # Define columns
        self.columns = [
            'supplier', 'unique_id', 'article', 'color', 'amount', 'price', 'notes'
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

        # Bind events
        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<Delete>', self.delete_selected)

    def create_new_list(self):
        """Create a new shopping list"""
        dialog = tk.Toplevel(self)
        dialog.title("Create New Shopping List")
        dialog.transient(self)
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky='nsew')

        # List name entry
        ttk.Label(main_frame, text="List Name:").grid(row=0, column=0, sticky='w')
        name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=name_var).grid(row=0, column=1, sticky='ew')

        def save():
            """Save new shopping list"""
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "List name is required")
                return

            # Check if name exists
            self.db.connect()
            try:
                existing = self.db.execute_query(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (f"shopping_list_{name}",)
                )

                if existing:
                    messagebox.showerror("Error", "List name already exists")
                    return

                # Create new table
                query = f"""
                    CREATE TABLE shopping_list_{name} (
                        supplier TEXT NOT NULL,
                        unique_id TEXT,
                        article TEXT NOT NULL,
                        color TEXT,
                        amount INTEGER NOT NULL,
                        price REAL,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                self.db.execute_query(query)

                # Refresh shopping lists
                self.load_shopping_lists()
                self.list_var.set(name)

                dialog.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to create list: {str(e)}")
            finally:
                self.db.disconnect()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Create",
                   command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel",
                   command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def delete_list(self):
        """Delete current shopping list"""
        if not self.current_list:
            messagebox.showwarning("Warning", "Please select a shopping list")
            return

        if messagebox.askyesno("Confirm Delete",
                               f"Are you sure you want to delete {self.current_list}?"):
            self.db.connect()
            try:
                self.db.execute_query(f"DROP TABLE shopping_list_{self.current_list}")
                self.load_shopping_lists()
                self.current_list = None
                self.list_var.set('')

                # Clear table
                for item in self.tree.get_children():
                    self.tree.delete(item)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete list: {str(e)}")
            finally:
                self.db.disconnect()

    def load_shopping_lists(self):
        """Load available shopping lists"""
        self.db.connect()
        try:
            tables = self.db.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'shopping_list_%'"
            )

            lists = [table[0].replace('shopping_list_', '') for table in tables]
            self.list_combo['values'] = lists

        finally:
            self.db.disconnect()

    def on_list_select(self, *args):
        """Handle shopping list selection"""
        selected = self.list_var.get()
        if selected:
            self.current_list = selected
            self.load_data()
        else:
            self.current_list = None
            # Clear table
            for item in self.tree.get_children():
                self.tree.delete(item)

    def show_add_dialog(self):
        """Show dialog for adding new item to shopping list"""
        if not self.current_list:
            messagebox.showwarning("Warning", "Please select a shopping list")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Add Item to Shopping List")
        dialog.transient(self)
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky='nsew')

        # Get suppliers
        self.db.connect()
        suppliers = self.db.execute_query(
            "SELECT company_name FROM supplier ORDER BY company_name"
        )

        # Get parts and leather items
        parts = self.db.execute_query(
            "SELECT unique_id_parts, name, color FROM sorting_system ORDER BY name"
        )
        leather = self.db.execute_query(
            "SELECT unique_id_leather, name, color FROM shelf ORDER BY name"
        )
        self.db.disconnect()

        # Create fields
        row = 0
        entries = {}

        # Supplier selection
        ttk.Label(main_frame, text="Supplier:").grid(row=row, column=0, sticky='w')
        supplier_var = tk.StringVar()
        supplier_combo = ttk.Combobox(main_frame, textvariable=supplier_var)
        supplier_combo['values'] = ['Add Supplier'] + \
                                   [s[0] for s in suppliers] if suppliers else []
        supplier_combo.grid(row=row, column=1, sticky='ew')
        entries['supplier'] = supplier_var

        def handle_supplier_selection(*args):
            if supplier_var.get() == 'Add Supplier':
                # Call add supplier function
                pass

        supplier_var.trace('w', handle_supplier_selection)

        row += 1

        # Item selection
        ttk.Label(main_frame, text="Item:").grid(row=row, column=0, sticky='w')
        id_var = tk.StringVar()
        id_combo = ttk.Combobox(main_frame, textvariable=id_var)
        id_combo['values'] = ['Add Part', 'Add Leather'] + \
                             [f"{p[0]} - {p[1]}" for p in parts] + \
                             [f"{l[0]} - {l[1]}" for l in leather]
        id_combo.grid(row=row, column=1, sticky='ew')
        entries['unique_id'] = id_var

        # Create remaining fields
        fields = ['amount', 'price', 'notes']
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

        def save():
            """Save item to shopping list"""
            try:
                # Validate required fields
                if not all([entries['supplier'].get(), entries['unique_id'].get(),
                            entries['amount'].get()]):
                    messagebox.showerror("Error",
                                         "Supplier, Item, and Amount are required")
                    return

                # Validate numeric fields
                try:
                    amount = int(entries['amount'].get())
                    price = float(entries['price'].get()) if entries['price'].get() else 0
                except ValueError:
                    messagebox.showerror("Error",
                                         "Amount must be an integer and Price must be a number")
                    return

                # Get item details
                item_id, item_name = entries['unique_id'].get().split(' - ')

                # Get color from database
                self.db.connect()
                if item_id.startswith('L'):
                    color = self.db.execute_query(
                        "SELECT color FROM shelf WHERE unique_id_leather = ?",
                        (item_id,)
                    )[0][0]
                else:
                    color = self.db.execute_query(
                        "SELECT color FROM sorting_system WHERE unique_id_parts = ?",
                        (item_id,)
                    )[0][0]

                # Create item data
                item_data = {
                    'supplier': entries['supplier'].get(),
                    'unique_id': item_id,
                    'article': item_name,
                    'color': color,
                    'amount': amount,
                    'price': price,
                    'notes': entries['notes'].get()
                }

                # Insert into database
                if self.db.insert_record(f"shopping_list_{self.current_list}",
                                         item_data):
                    self.undo_stack.append(('add', item_data))
                    self.redo_stack.clear()
                    self.load_data()
                    dialog.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to add item: {str(e)}")
            finally:
                self.db.disconnect()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row + 1, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Add",
                   command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel",
                   command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def load_data(self):
        """Load data for current shopping list"""
        if not self.current_list:
            return

        self.db.connect()
        try:
            query = f"SELECT * FROM shopping_list_{self.current_list} ORDER BY supplier, article"
            results = self.db.execute_query(query)

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Insert new data
            for row in results:
                self.tree.insert('', 'end', values=row[:-2])  # Exclude timestamps

        finally:
            self.db.disconnect()

    def on_double_click(self, event):
        """Handle double-click on cell"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)

            if column == "#2":  # unique_id column
                return  # Don't allow editing of unique_id

            self.start_cell_edit(item, column)

    def start_cell_edit(self, item, column):
        """Start cell editing"""
        col_num = int(column[1]) - 1
        col_name = self.columns[col_num]
        current_value = self.tree.set(item, col_name)

        # Create edit frame
        frame = ttk.Frame(self.tree)

        # Create edit widget based on column
        if col_name == 'supplier':
            # Get suppliers list
            self.db.connect()
            suppliers = self.db.execute_query(
                "SELECT company_name FROM supplier ORDER BY company_name"
            )
            self.db.disconnect()

            var = tk.StringVar(value=current_value)
            widget = ttk.Combobox(frame, textvariable=var)
            widget['values'] = [s[0] for s in suppliers] if suppliers else []
        else:
            var = tk.StringVar(value=current_value)
            widget = ttk.Entry(frame, textvariable=var)

        widget.pack(fill=tk.BOTH, expand=True)

        # Position frame
        bbox = self.tree.bbox(item, column)
        frame.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])

        def save_edit(event=None):
            """Save the edited value"""
            new_value = var.get()
            if new_value != current_value:
                # Validate numeric fields
                if col_name == 'amount':
                    try:
                        value = int(new_value)
                        if value < 0:
                            messagebox.showerror("Error", "Amount must be non-negative")
                            return
                    except ValueError:
                        messagebox.showerror("Error", "Amount must be a number")
                        return
                elif col_name == 'price':
                    try:
                        value = float(new_value)
                        if value < 0:
                            messagebox.showerror("Error", "Price must be non-negative")
                            return
                    except ValueError:
                        messagebox.showerror("Error", "Price must be a number")
                        return

                # Store for undo
                old_values = {col: self.tree.set(item, col) for col in self.columns}
                self.undo_stack.append(('edit', item, old_values))
                self.redo_stack.clear()

                # Update database
                self.update_record(old_values['unique_id'], col_name, new_value)

                # Update tree
                self.tree.set(item, col_name, new_value)

            frame.destroy()

        def cancel_edit(event=None):
            """Cancel the edit"""
            frame.destroy()

        widget.bind('<Return>', save_edit)
        widget.bind('<Escape>', cancel_edit)
        widget.bind('<FocusOut>', save_edit)
        widget.focus_set()

    def update_record(self, unique_id: str, column: str, value: str):
        """Update record in database"""
        if not self.current_list:
            return

        self.db.connect()
        try:
            success = self.db.update_record(
                f"shopping_list_{self.current_list}",
                {column: value},
                "unique_id = ?",
                (unique_id,)
            )
            if not success:
                messagebox.showerror("Error", "Failed to update database")
        finally:
            self.db.disconnect()

    def delete_selected(self, event=None):
        """Delete selected items"""
        if not self.current_list:
            return

        selected = self.tree.selection()
        if not selected:
            return

        if messagebox.askyesno("Confirm Delete",
                               "Are you sure you want to delete the selected items?"):
            self.db.connect()
            try:
                # Store for undo
                deleted_items = []
                for item in selected:
                    values = {col: self.tree.set(item, col) for col in self.columns}
                    deleted_items.append((item, values))

                    # Delete from database
                    unique_id = values['unique_id']
                    self.db.delete_record(
                        f"shopping_list_{self.current_list}",
                        "unique_id = ?",
                        (unique_id,)
                    )

                    # Delete from tree
                    self.tree.delete(item)

                self.undo_stack.append(('delete', deleted_items))
                self.redo_stack.clear()

            finally:
                self.db.disconnect()

    def sort_column(self, col):
        """Sort table by column"""
        # Get all items
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]

        # Determine sort direction
        reverse = False
        if hasattr(self, '_last_sort') and self._last_sort == (col, False):
            reverse = True

        # Store sort state
        self._last_sort = (col, reverse)

        # Sort items
        try:
            # Try numeric sort for amount and price columns
            if col in ['amount', 'price']:
                l.sort(key=lambda x: float(x[0]) if x[0] else 0, reverse=reverse)
            else:
                l.sort(reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)

        # Rearrange items
        for index, (_, k) in enumerate(l):
            self.tree.move(k, '', index)

        # Update header arrow
        for column in self.columns:
            if column != col:
                self.tree.heading(column, text=column.replace('_', ' ').title())
        arrow = "▼" if reverse else "▲"
        self.tree.heading(col, text=f"{col.replace('_', ' ').title()} {arrow}")

    def undo(self, event=None):
        """Undo last action"""
        if not self.undo_stack:
            return

        action = self.undo_stack.pop()
        action_type = action[0]

        if action_type == 'edit':
            item, old_values = action[1:]
            # Store current values for redo
            current_values = {col: self.tree.set(item, col) for col in self.columns}
            self.redo_stack.append(('edit', item, current_values))

            # Restore old values
            for col, value in old_values.items():
                self.tree.set(item, col, value)
                self.update_record(old_values['unique_id'], col, value)

        elif action_type == 'add':
            data = action[1]
            # Delete added record
            self.db.connect()
            try:
                self.db.delete_record(
                    f"shopping_list_{self.current_list}",
                    "unique_id = ?",
                    (data['unique_id'],)
                )

                # Find and delete tree item
                for item in self.tree.get_children():
                    if self.tree.set(item, 'unique_id') == data['unique_id']:
                        self.tree.delete(item)
                        break

                self.redo_stack.append(('readd', data))

            finally:
                self.db.disconnect()

        elif action_type == 'delete':
            deleted_items = action[1]
            restored_items = []

            self.db.connect()
            try:
                for item_id, values in deleted_items:
                    # Restore to database
                    self.db.insert_record(f"shopping_list_{self.current_list}", values)

                    # Restore to tree
                    new_item = self.tree.insert('', 'end', values=list(values.values()))
                    restored_items.append((new_item, values))

                self.redo_stack.append(('undelete', restored_items))

            finally:
                self.db.disconnect()

    def redo(self, event=None):
        """Redo last undone action"""
        if not self.redo_stack:
            return

        action = self.redo_stack.pop()
        action_type = action[0]

        if action_type == 'edit':
            item, new_values = action[1:]
            # Store current values for undo
            current_values = {col: self.tree.set(item, col) for col in self.columns}
            self.undo_stack.append(('edit', item, current_values))

            # Restore new values
            for col, value in new_values.items():
                self.tree.set(item, col, value)
                self.update_record(new_values['unique_id'], col, value)

        elif action_type == 'readd':
            data = action[1]
            # Re-add the record
            self.db.connect()
            try:
                if self.db.insert_record(f"shopping_list_{self.current_list}", data):
                    # Add to tree
                    item = self.tree.insert('', 'end', values=list(data.values()))
                    self.undo_stack.append(('add', data))

            finally:
                self.db.disconnect()

        elif action_type == 'undelete':
            restored_items = action[1]
            deleted_items = []

            self.db.connect()
            try:
                for item, values in restored_items:
                    # Delete from database
                    self.db.delete_record(
                        f"shopping_list_{self.current_list}",
                        "unique_id = ?",
                        (values['unique_id'],)
                    )

                    # Delete from tree
                    self.tree.delete(item)
                    deleted_items.append((item, values))

                self.undo_stack.append(('delete', deleted_items))

            finally:
                self.db.disconnect()

    def reset_view(self):
        """Reset table to default view"""
        self.load_data()