import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import csv
from store_management.utils.logger import logger
from typing import Dict, List, Optional
import uuid
from datetime import datetime
from pathlib import Path

from store_management.config import TABLES, COLORS
from store_management.database.db_manager import DatabaseManager
from store_management.config import get_database_path



class ShoppingListView(ttk.Frame):

    def _setup_caching(self):
        """Setup caching for frequently accessed data"""
        self.supplier_cache = {}
        self.parts_cache = {}
        self.cache_timeout = 300  # 5 minutes

    def refresh_cache(self):
        """Refresh cached data"""
        self.db.connect()
        try:
            # Cache suppliers
            suppliers = self.db.execute_query(
                "SELECT company_name FROM supplier ORDER BY company_name"
            )
            self.supplier_cache = {
                'data': suppliers,
                'timestamp': datetime.now()
            }

            # Cache parts
            parts = self.db.execute_query(
                "SELECT unique_id_parts, name, color FROM sorting_system ORDER BY name"
            )
            self.parts_cache = {
                'data': parts,
                'timestamp': datetime.now()
            }
        finally:
            self.db.disconnect()

    def get_data_chunks(self, table, chunk_size=1000):
        """Get data in chunks to handle large datasets"""
        offset = 0
        while True:
            query = f"""
                SELECT * FROM {table}
                ORDER BY supplier, article
                LIMIT {chunk_size} OFFSET {offset}
            """
            results = self.db.execute_query(query)
            if not results:
                break
            yield results
            offset += chunk_size

    def get_suppliers(self):
        """Get suppliers with caching"""
        now = datetime.now()
        if (not self.supplier_cache or
                (now - self.supplier_cache['timestamp']).seconds > self.cache_timeout):
            self.refresh_cache()
        return self.supplier_cache['data']

    def batch_update(self, table: str, updates: List[Dict]):
        """Perform batch updates"""
        self.db.connect()
        try:
            self.db.begin_transaction()
            for update in updates:
                self.db.update_record(table, update['data'], update['condition'], update['params'])
            self.db.commit_transaction()
        except Exception as e:
            self.db.rollback_transaction()
            raise e
        finally:
            self.db.disconnect()

    def update_tree_batch(self, rows):
        """Update tree with batch of rows"""
        for row in rows:
            self.tree.insert('', 'end', values=row[:-2])  # Exclude timestamps

    def show_loading(self):
        """Show loading indicator"""
        self.loading_label = ttk.Label(self, text="Loading...")
        self.loading_label.pack()
        self.update_idletasks()

    def hide_loading(self):
        """Hide loading indicator"""
        if hasattr(self, 'loading_label'):
            self.loading_label.destroy()

    def cleanup(self):
        """Cleanup resources"""
        self.supplier_cache.clear()
        self.parts_cache.clear()

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

    def update_shopping_list_tables(self):
        """Update existing shopping list tables to include status and urgency columns"""
        self.db.connect()
        try:
            # Get all shopping list tables
            tables = self.db.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'shopping_list_%'"
            )

            for table in tables:
                table_name = table[0]

                # Check if status column exists
                columns = self.db.execute_query(f"PRAGMA table_info({table_name})")
                column_names = [col[1] for col in columns]

                # Add status column if it doesn't exist
                if 'status' not in column_names:
                    self.db.execute_query(
                        f"ALTER TABLE {table_name} ADD COLUMN status TEXT DEFAULT 'not ordered'"
                    )
                    logger.info(f"Added status column to {table_name}")

                # Add urgency column if it doesn't exist
                if 'urgency' not in column_names:
                    self.db.execute_query(
                        f"ALTER TABLE {table_name} ADD COLUMN urgency TEXT DEFAULT 'None'"
                    )
                    logger.info(f"Added urgency column to {table_name}")

        except Exception as e:
            logger.error(f"Failed to update shopping list tables: {str(e)}")
            raise
        finally:
            self.db.disconnect()

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
        # Initialize ttk.Frame first
        super().__init__(parent)
        self.db = DatabaseManager(get_database_path())


        # Setup caching
        self._setup_caching()

        # Initialize undo/redo stacks
        self.undo_stack = []
        self.redo_stack = []

        # Current shopping list
        self.current_list = None

        # Setup UI components in correct order
        self.setup_table_selection()  # Setup top table first
        self.setup_toolbar()  # Then toolbar
        self.setup_table()  # Then bottom table
        self.load_shopping_lists()  # Finally load data

    def setup_toolbar(self):
        """Create the toolbar with all buttons (except New List, Delete List, and Add Item)"""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Left side buttons (Search and Filter)
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
        """Create shopping list selection table view"""
        # Create list frame with label
        list_frame = ttk.LabelFrame(self, text="Shopping Lists")
        list_frame.pack(fill=tk.X, padx=5, pady=5)

        # Top button frame for New List and Delete List
        top_button_frame = ttk.Frame(list_frame)
        top_button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(top_button_frame, text="New List",
                   command=self.create_new_list).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_button_frame, text="Delete List",
                   command=self.delete_list).pack(side=tk.LEFT, padx=2)

        # Create list tree components
        self.list_tree_frame = ttk.Frame(list_frame)
        self.list_tree_frame.pack(expand=True, fill='both', padx=5, pady=5)

        # Define columns for list selection
        self.list_columns = ['name', 'supplier', 'status', 'urgency', 'notes']

        # Create scrollbars for list selection
        list_vsb = ttk.Scrollbar(self.list_tree_frame, orient="vertical")
        list_hsb = ttk.Scrollbar(self.list_tree_frame, orient="horizontal")

        # Create list selection treeview
        self.list_tree = ttk.Treeview(
            self.list_tree_frame,
            columns=self.list_columns,
            show='headings',
            selectmode='browse',  # Only allow single selection
            height=5,  # Show 5 rows by default
            yscrollcommand=list_vsb.set,
            xscrollcommand=list_hsb.set
        )

        # Configure scrollbars
        list_vsb.configure(command=self.list_tree.yview)
        list_hsb.configure(command=self.list_tree.xview)

        # Setup headers and columns for list selection
        for col in self.list_columns:
            self.list_tree.heading(col, text=col.title())
            # Adjust column widths based on content
            if col == 'supplier':
                width = 200
            elif col in ['status', 'urgency', 'name']:
                width = 100
            else:
                width = 150
            self.list_tree.column(col, width=width, minwidth=50)

        # Configure urgency color tags
        self.list_tree.tag_configure('urgency_green', background='#90EE90')  # Light green
        self.list_tree.tag_configure('urgency_yellow', background='#FFFFE0')  # Light yellow
        self.list_tree.tag_configure('urgency_red', background='#FFB6C1')  # Light red

        # Grid layout for list selection
        self.list_tree.grid(row=0, column=0, sticky='nsew')
        list_vsb.grid(row=0, column=1, sticky='ns')
        list_hsb.grid(row=1, column=0, sticky='ew')

        # Configure grid weights for list selection
        self.list_tree_frame.grid_columnconfigure(0, weight=1)
        self.list_tree_frame.grid_rowconfigure(0, weight=1)

        # Bottom button frame for Add Item
        bottom_button_frame = ttk.Frame(list_frame)
        bottom_button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(bottom_button_frame, text="Add Item to List",
                   command=self.show_add_dialog).pack(side=tk.LEFT, padx=2)

        # Bind selection event
        self.list_tree.bind('<<TreeviewSelect>>', self.on_list_select)

    def setup_table(self):
        """Create the main table view"""
        # Create table frame
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(expand=True, fill='both', padx=5, pady=5)

        # Define columns
        self.columns = [
            'supplier', 'unique_id', 'article', 'color', 'amount', 'price', 'notes'
        ]

        # Create treeview with scrollbars
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=self.columns,
            show='headings',
            selectmode='extended'
        )
        self.tree.focus_set()  # Set focus to the Treeview

        # Setup scrollbars
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

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

        # Custom event handlers
        def on_delete(event):
            from store_management.utils.logger import logger
            logger.debug("Delete key pressed")
            self.delete_selected(event)
            return 'break'

        def on_return(event):
            from store_management.utils.logger import logger
            logger.debug("Return key pressed")
            selected = self.tree.selection()
            if selected:
                logger.debug(f"Selected item: {selected}")
                self.start_cell_edit(selected[0], '#2')
            return 'break'

        def on_escape(event):
            from store_management.utils.logger import logger
            logger.debug("Escape key pressed")
            self.tree.selection_remove(self.tree.selection())
            return 'break'

        def on_key_press(event):
            from store_management.utils.logger import logger
            logger.debug(f"Key pressed: {event.keysym}")

        # Bind events
        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<Delete>', on_delete)
        self.tree.bind('<Return>', on_return)
        self.tree.bind('<Escape>', on_escape)
        self.tree.bind('<Key>', on_key_press)

    def handle_return(self, event=None):
        """Handle Return key press - typically used for editing or confirming selection"""
        selected = self.tree.selection()
        if selected:
            # Start editing the second column (unique_id)
            self.start_cell_edit(selected[0], '#2')

    def handle_escape(self, event=None):
        """Handle Escape key press - typically used to clear selection"""
        self.tree.selection_remove(self.tree.selection())

    def create_new_list(self):
        """Create a new shopping list with supplier selection"""
        dialog = tk.Toplevel(self)
        dialog.title("Create New Shopping List")
        dialog.transient(self)
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky='nsew')

        # Get suppliers from database
        self.db.connect()
        try:
            suppliers = self.db.execute_query(
                "SELECT company_name FROM supplier ORDER BY company_name"
            )
        except Exception as e:
            suppliers = []
            logger.error(f"Failed to fetch suppliers: {e}")
        finally:
            self.db.disconnect()

        # Supplier selection
        row = 0
        # Add name field
        ttk.Label(main_frame, text="List Name:").grid(row=row, column=0, sticky='w', pady=2)
        name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=name_var).grid(row=row, column=1, sticky='ew', pady=2)

        row += 1
        ttk.Label(main_frame, text="Supplier:").grid(row=row, column=0, sticky='w', pady=2)
        supplier_var = tk.StringVar()
        supplier_combo = ttk.Combobox(main_frame, textvariable=supplier_var)
        supplier_combo['values'] = ['➕ Add New Supplier'] + [s[0] for s in suppliers]
        supplier_combo.grid(row=row, column=1, sticky='ew', pady=2)

        row += 1
        # Status dropdown
        ttk.Label(main_frame, text="Status:").grid(row=row, column=0, sticky='w', pady=2)
        status_var = tk.StringVar(value="not ordered")
        status_combo = ttk.Combobox(main_frame, textvariable=status_var, state='readonly')
        status_combo['values'] = ["not ordered", "ordered", "template"]
        status_combo.grid(row=row, column=1, sticky='ew', pady=2)

        row += 1
        # Urgency dropdown
        ttk.Label(main_frame, text="Urgency:").grid(row=row, column=0, sticky='w', pady=2)
        urgency_var = tk.StringVar(value="None")
        urgency_combo = ttk.Combobox(main_frame, textvariable=urgency_var, state='readonly')
        urgency_combo['values'] = ["None", "Green", "Yellow", "Red"]
        urgency_combo.grid(row=row, column=1, sticky='ew', pady=2)

        row += 1
        # Notes field
        ttk.Label(main_frame, text="Notes:").grid(row=row, column=0, sticky='w', pady=2)
        notes_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=notes_var).grid(row=row, column=1, sticky='ew', pady=2)

        def save():
            """Save new shopping list"""
            try:
                supplier = supplier_var.get()
                if supplier == '➕ Add New Supplier' or not supplier:
                    messagebox.showerror("Error", "Please select a supplier")
                    return

                # Validate input values
                status = status_var.get()
                urgency = urgency_var.get()
                notes = notes_var.get()
                list_name = name_var.get().strip() or supplier

                logger.info(f"Attempting to create shopping list:")
                logger.info(f"Supplier: {supplier}")
                logger.info(f"Name: {list_name}")
                logger.info(f"Status: {status}")
                logger.info(f"Urgency: {urgency}")
                logger.info(f"Notes: {notes}")

                self.db.connect()
                try:
                    # Validate urgency value
                    valid_urgencies = ["None", "Green", "Yellow", "Red"]
                    if urgency not in valid_urgencies:
                        raise ValueError(f"Invalid urgency value: {urgency}")

                    # Generate a unique table name
                    base_table_name = f"shopping_list_{supplier}"
                    table_name = base_table_name
                    counter = 1

                    # Check if table exists and generate a unique name
                    while self.db.execute_query(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
                            (table_name,)
                    ):
                        table_name = f"{base_table_name}_{counter}"
                        counter += 1

                    # Create table with all necessary columns
                    query = f"""
                        CREATE TABLE {table_name} (
                            supplier TEXT NOT NULL,
                            unique_id TEXT,
                            article TEXT NOT NULL,
                            color TEXT,
                            amount INTEGER NOT NULL DEFAULT 0,
                            price REAL DEFAULT 0,
                            notes TEXT DEFAULT '',
                            name TEXT DEFAULT '',
                            status TEXT DEFAULT 'not ordered',
                            urgency TEXT DEFAULT 'None',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            CHECK (urgency IN ('None', 'Green', 'Yellow', 'Red'))
                        )
                    """
                    self.db.execute_query(query)

                    # Insert initial metadata row
                    metadata = {
                        'supplier': supplier,
                        'unique_id': 'META',
                        'article': 'Metadata',
                        'status': status,
                        'urgency': urgency,
                        'amount': 0,
                        'color': '',
                        'price': 0,
                        'notes': notes,
                        'name': list_name
                    }

                    # Attempt to insert metadata
                    try:
                        self.db.insert_record(table_name, metadata)
                        logger.info(f"Metadata inserted successfully for {table_name}")
                        logger.info(f"Metadata details: {metadata}")
                    except Exception as insert_e:
                        logger.error(f"Failed to insert metadata: {insert_e}")
                        raise

                    # Refresh shopping lists
                    self.load_shopping_lists()
                    dialog.destroy()

                except Exception as e:
                    logger.error(f"List creation failed: {str(e)}")
                    # Convert exception to user-friendly message
                    error_message = str(e)
                    if "CHECK constraint failed" in error_message:
                        error_message = "Invalid urgency value. Please select a valid urgency."
                    messagebox.showerror("Error", f"Failed to create list: {error_message}")
                finally:
                    self.db.disconnect()

            except Exception as overall_e:
                logger.error(f"Unexpected error in save method: {overall_e}")
                messagebox.showerror("Unexpected Error", str(overall_e))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row + 1, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Create", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)

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

                # Clear table
                for item in self.tree.get_children():
                    self.tree.delete(item)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete list: {str(e)}")
            finally:
                self.db.disconnect()

    def load_shopping_lists(self):
        """Load available shopping lists with metadata and apply urgency colors"""
        self.db.connect()
        try:
            # Clear existing items
            for item in self.list_tree.get_children():
                self.list_tree.delete(item)

            # Get all shopping list tables
            tables = self.db.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'shopping_list_%'"
            )

            for table in tables:
                table_name = table[0]

                # Get metadata from the special metadata row
                metadata_query = f"""
                    SELECT 
                        supplier, 
                        status, 
                        urgency, 
                        name,
                        notes
                    FROM {table_name} 
                    WHERE unique_id = 'META'
                    LIMIT 1
                """
                try:
                    metadata = self.db.execute_query(metadata_query)

                    if not metadata:
                        logger.warning(f"No metadata found for table {table_name}")
                        continue

                    supplier = metadata[0][0] or 'Unknown'
                    status = metadata[0][1] or 'not ordered'
                    urgency = metadata[0][2] or 'None'
                    name = metadata[0][3] or table_name.replace('shopping_list_', '')
                    notes = metadata[0][4] or ''

                    # Sanitize urgency value
                    if urgency not in ['None', 'Green', 'Yellow', 'Red']:
                        logger.warning(f"Invalid urgency value for {table_name}: {urgency}")
                        urgency = 'None'

                    # Insert into tree with metadata
                    item = self.list_tree.insert('', 'end', values=(name, supplier, status, urgency, notes))

                    # Apply urgency color
                    if urgency == 'Green':
                        self.list_tree.item(item, tags=('urgency_green',))
                    elif urgency == 'Yellow':
                        self.list_tree.item(item, tags=('urgency_yellow',))
                    elif urgency == 'Red':
                        self.list_tree.item(item, tags=('urgency_red',))

                except Exception as e:
                    logger.error(f"Error processing table {table_name}: {e}")

        except Exception as e:
            logger.error(f"Failed to load shopping lists: {e}")
            messagebox.showerror("Error", f"Failed to load shopping lists: {e}")
        finally:
            self.db.disconnect()

    def on_list_select(self, event):
        """Handle shopping list selection"""
        # Log the event details
        logger.info("on_list_select method called")

        # Get the selected items from the list tree
        selected = self.list_tree.selection()

        # Log the selected items
        logger.info(f"Selected items: {selected}")

        # Clear the lower table view regardless of selection
        for item in self.tree.get_children():
            self.tree.delete(item)

        if selected:
            # Get the list values from the selected item
            values = self.list_tree.item(selected[0])['values']
            logger.info(f"Selected list values: {values}")

            if values:
                # Get the name and supplier (first two columns)
                name = values[0]  # Name
                supplier = values[1]  # Supplier

                logger.info(f"Attempting to select list - Name: {name}, Supplier: {supplier}")

                # Find the corresponding table name
                self.db.connect()
                try:
                    # Find tables that match the supplier
                    tables = self.db.execute_query(
                        """
                        SELECT name FROM sqlite_master 
                        WHERE type='table' 
                        AND name LIKE 'shopping_list_%'
                        """)

                    logger.info(f"Found {len(tables)} shopping list tables:")
                    for table in tables:
                        logger.info(f"Table: {table[0]}")

                    # Find the matching table by checking its metadata
                    matching_table = None
                    for table in tables:
                        table_name = table[0]
                        try:
                            # Fetch metadata for this table
                            metadata = self.db.execute_query(
                                f"SELECT name, supplier FROM {table_name} WHERE unique_id = 'META'"
                            )

                            logger.info(f"Checking table {table_name}")
                            logger.info(f"Metadata found: {metadata}")

                            # Check if metadata matches the selected list
                            if metadata and metadata[0][0] == name and metadata[0][1] == supplier:
                                matching_table = table_name
                                break
                        except Exception as meta_e:
                            logger.error(f"Error checking metadata for {table_name}: {meta_e}")

                    if matching_table:
                        # Set the current list to the full table name
                        self.current_list = matching_table.replace('shopping_list_', '')
                        logger.info(f"Selected list: {self.current_list}")

                        # Load data for the selected list
                        self.load_data()
                    else:
                        logger.warning("No matching table found")
                        logger.warning(f"Searched for Name: {name}, Supplier: {supplier}")
                        self.current_list = None

                        # Ensure the lower table is cleared
                        for item in self.tree.get_children():
                            self.tree.delete(item)
                except Exception as e:
                    logger.error(f"Error selecting list: {e}")
                    self.current_list = None

                    # Ensure the lower table is cleared
                    for item in self.tree.get_children():
                        self.tree.delete(item)
                finally:
                    self.db.disconnect()
        else:
            # No selection - ensure current list is None and lower table is cleared
            self.current_list = None
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
        """Load data with optimized UI updates"""
        # Log the current list being loaded
        logger.info(f"Loading data for current list: {self.current_list}")

        if not self.current_list:
            logger.warning("No current list selected")
            # Clear the tree view
            for item in self.tree.get_children():
                self.tree.delete(item)
            return

        # Show loading indicator
        self.show_loading()

        try:
            # Clear existing items efficiently
            for item in self.tree.get_children():
                self.tree.delete(item)

            self.db.connect()

            # Construct the full table name
            full_table_name = f"shopping_list_{self.current_list}"

            # Verify table exists
            tables = self.db.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
                (full_table_name,)
            )

            if not tables:
                logger.error(f"Table {full_table_name} does not exist")
                return

            # Query to get all rows except the metadata row
            query = f"""
                SELECT * FROM {full_table_name} 
                WHERE unique_id != 'META'
                ORDER BY supplier, article
            """

            # Execute query and fetch results
            results = self.db.execute_query(query)

            logger.info(f"Found {len(results)} items in the list")

            # Update tree with results
            for row in results:
                # Exclude last two columns (timestamps)
                self.tree.insert('', 'end', values=row[:-2])

        except Exception as e:
            logger.error(f"Error loading data: {e}")
            messagebox.showerror("Error", f"Failed to load shopping list: {e}")
        finally:
            # Always hide loading and disconnect
            self.hide_loading()
            self.db.disconnect()

    def on_double_click(self, event):
        """Handle double-click on cell"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            item = self.tree.identify_row(event.y)
            column = self.tree.identify_column(event.x)
            col_num = int(column[1:]) - 1  # Get column index (remove '#')
            col_name = self.columns[col_num]  # Get column name

            print(f"Clicked column: {col_name} (index {col_num})")  # Debugging line

            if col_name in ('unique_id', 'article', 'color'):  # Disallow editing these columns
                return

            self.start_cell_edit(item, column)

    def start_cell_edit(self, item, column):
        """Start cell editing"""
        print(f"start_cell_edit called! item={item}, column={column}")  # Debugging line
        from store_management.utils.logger import logger

        logger.debug(f"Start cell edit: item={item}, column={column}")

        # Prevent editing metadata row
        unique_id = self.tree.set(item, 'unique_id')
        if unique_id == 'META':
            logger.warning("Attempted to edit metadata row")
            return

        # Get column name and current value
        col_num = int(column[1:]) - 1
        col_name = self.columns[col_num]
        current_value = self.tree.set(item, col_name)
        logger.debug(f"Editing column: {col_name}, current value: {current_value}")

        # Create edit frame
        frame = ttk.Frame(self.tree)

        # Special handling for specific columns
        if col_name == 'supplier':
            # Get suppliers list
            self.db.connect()
            try:
                suppliers = self.db.execute_query(
                    "SELECT company_name FROM supplier ORDER BY company_name"
                )
                suppliers = [s[0] for s in suppliers] if suppliers else []
            except Exception as e:
                logger.error(f"Error fetching suppliers: {e}")
                suppliers = []
            finally:
                self.db.disconnect()

            # Create combobox
            entry = ttk.Combobox(frame, values=suppliers)
            entry.set(current_value)
        elif col_name in ['amount', 'price']:
            # Numeric entry with validation
            entry = ttk.Entry(frame, validate='key')
            entry.insert(0, current_value)
            entry['validatecommand'] = (entry.register(self.validate_numeric), '%P')
        else:
            # Standard entry for other columns
            entry = ttk.Entry(frame)
            entry.insert(0, current_value)

        entry.select_range(0, tk.END)
        entry.pack(fill=tk.BOTH, expand=True)

        def save_edit(event=None):
            """Save the edited value"""
            new_value = entry.get()
            if new_value != current_value:
                # Store for undo
                old_values = {col: self.tree.set(item, col) for col in self.columns}
                self.undo_stack.append(('edit', item, old_values))
                self.redo_stack.clear()

                # Update database
                unique_id = self.tree.set(item, 'unique_id')
                self.update_record(unique_id, col_name, new_value)

                # Update tree
                self.tree.set(item, col_name, new_value)

            frame.destroy()

        def cancel_edit(event=None):
            """Cancel the edit"""
            frame.destroy()

        entry.bind('<Return>', save_edit)
        entry.bind('<Escape>', cancel_edit)
        entry.bind('<FocusOut>', save_edit)
        entry.focus_set()

    def validate_numeric(self, value):
        """Validate numeric input for amount and price"""
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False

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
        from store_management.utils.logger import logger

        logger.debug("Delete_selected method called")

        # Add logging to check current list state
        logger.debug(f"Current list before deletion: {self.current_list}")

        selected = self.tree.selection()
        logger.debug(f"Selected items: {selected}")

        # If no current list, check if we can derive it from the list selection
        if not self.current_list:
            list_selected = self.list_tree.selection()
            if list_selected:
                values = self.list_tree.item(list_selected[0])['values']
                if values:
                    # Reconstruct current list name
                    name = values[0]
                    supplier = values[1]
                    # Attempt to find the correct table name
                    self.db.connect()
                    try:
                        tables = self.db.execute_query(
                            """
                            SELECT name FROM sqlite_master 
                            WHERE type='table' 
                            AND name LIKE 'shopping_list_%'
                            """
                        )

                        # Find the matching table
                        for table in tables:
                            table_name = table[0]
                            metadata = self.db.execute_query(
                                f"SELECT name, supplier FROM {table_name} WHERE unique_id = 'META'"
                            )
                            if metadata and metadata[0][0] == name and metadata[0][1] == supplier:
                                self.current_list = table_name.replace('shopping_list_', '')
                                break
                    except Exception as e:
                        logger.error(f"Error finding current list: {e}")
                    finally:
                        self.db.disconnect()

        if not self.current_list:
            messagebox.showwarning("Warning", "Please select a shopping list first")
            return

        if not selected:
            logger.debug("No items selected")
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
                    logger.debug(f"Deleting item with unique_id: {unique_id}")

                    # Prevent deletion of metadata row
                    if unique_id == 'META':
                        logger.warning("Attempted to delete metadata row")
                        continue

                    self.db.delete_record(
                        f"shopping_list_{self.current_list}",
                        "unique_id = ?",
                        (unique_id,)
                    )

                    # Delete from tree
                    self.tree.delete(item)

                # Only append to undo stack if items were actually deleted
                if deleted_items:
                    self.undo_stack.append(('delete', deleted_items))
                    self.redo_stack.clear()

            except Exception as e:
                logger.error(f"Error in delete_selected: {e}")
                messagebox.showerror("Error", f"Failed to delete items: {str(e)}")
            finally:
                self.db.disconnect()

            # Reload data to ensure view is up to date
            self.load_data()



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