"""Recipe View using SQLAlchemy ORM."""

import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from typing import Optional
from datetime import datetime

from store_management.database.sqlalchemy.models import (
    Recipe, RecipeItem, Part, Leather
)
from store_management.database.sqlalchemy.manager import DatabaseManagerSQLAlchemy


class RecipeView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.db = DatabaseManagerSQLAlchemy()

        # Initialize undo/redo stacks
        self.undo_stack = []
        self.redo_stack = []

        # Current recipe
        self.current_recipe_id = None

        # Create UI components
        self.create_ui()

        # Load initial data
        self.load_data()

    def create_ui(self):
        """Create the user interface"""
        # Create toolbar
        self.create_toolbar()

        # Create main content area
        self.create_main_content()

        # Create status bar
        self.create_status_bar()

    def create_toolbar(self):
        """Create the toolbar with action buttons"""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Left side buttons
        left_frame = ttk.Frame(toolbar)
        left_frame.pack(side=tk.LEFT)

        ttk.Button(
            left_frame,
            text="ADD Recipe",
            command=self.show_add_recipe_dialog
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            left_frame,
            text="ADD Item to Recipe",
            command=self.show_add_item_dialog
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

        # Right side buttons
        right_frame = ttk.Frame(toolbar)
        right_frame.pack(side=tk.RIGHT)

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

    def create_main_content(self):
        """Create both table views"""
        # Create container for both tables
        tables_frame = ttk.Frame(self)
        tables_frame.pack(expand=True, fill='both', padx=5, pady=5)

        # Setup INDEX table
        index_frame = ttk.LabelFrame(tables_frame, text="Recipe Index")
        index_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.index_columns = [
            'unique_id', 'name', 'type', 'collection', 'color', 'pattern_id', 'notes'
        ]

        self.index_tree = self.create_treeview(
            index_frame,
            self.index_columns,
            self.on_index_select
        )

        # Setup Recipe Details table
        details_frame = ttk.LabelFrame(tables_frame, text="Recipe Details")
        details_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.details_columns = [
            'unique_id', 'name', 'color', 'amount', 'size',
            'in_storage', 'notes'
        ]

        self.details_tree = self.create_treeview(
            details_frame,
            self.details_columns
        )

        # Configure warning colors for low storage
        self.details_tree.tag_configure('low_storage', background='#FFB6C1')

    def create_treeview(self, parent, columns, select_callback=None):
        """Create a treeview with scrollbars"""
        # Create frame for treeview and scrollbars
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
            width = 200 if col in ['notes', 'name'] else 100
            tree.column(col, width=width, minwidth=50)

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

    def create_status_bar(self):
        """Create the status bar"""
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Status label
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Recipe count
        self.recipe_count = ttk.Label(status_frame, text="Recipes: 0")
        self.recipe_count.pack(side=tk.RIGHT, padx=5)

    def load_data(self):
        """Load recipe data from database"""
        try:
            with self.db.session_scope() as session:
                # Get all recipes
                recipes = session.query(Recipe).order_by(Recipe.name).all()

                # Clear existing items
                for item in self.index_tree.get_children():
                    self.index_tree.delete(item)

                # Insert recipes
                for recipe in recipes:
                    values = [
                        recipe.unique_id,
                        recipe.name,
                        recipe.type,
                        recipe.collection,
                        recipe.color,
                        recipe.pattern_id,
                        recipe.notes
                    ]
                    self.index_tree.insert('', 'end', values=values)

                # Update recipe count
                self.recipe_count.configure(text=f"Recipes: {len(recipes)}")

        except SQLAlchemyError as e:
            messagebox.showerror("Error", f"Failed to load recipes: {str(e)}")

    def on_index_select(self, event):
        """Handle selection in recipe index"""
        selection = self.index_tree.selection()
        if not selection:
            return

        try:
            with self.db.session_scope() as session:
                # Get selected recipe unique_id
                recipe_id = self.index_tree.item(selection[0])['values'][0]

                # Find recipe
                recipe = session.query(Recipe) \
                    .filter(Recipe.unique_id == recipe_id) \
                    .first()

                if recipe:
                    self.current_recipe_id = recipe.id
                    self.load_recipe_details(recipe.id)
                else:
                    self.current_recipe_id = None
                    # Clear details table
                    for item in self.details_tree.get_children():
                        self.details_tree.delete(item)

        except SQLAlchemyError as e:
            messagebox.showerror("Error", f"Failed to select recipe: {str(e)}")

    def load_recipe_details(self, recipe_id: int):
        """Load details for selected recipe"""
        try:
            with self.db.session_scope() as session:
                # Clear existing items
                for item in self.details_tree.get_children():
                    self.details_tree.delete(item)

                # Get recipe items with parts and leather
                recipe_items = session.query(RecipeItem) \
                    .filter(RecipeItem.recipe_id == recipe_id) \
                    .outerjoin(RecipeItem.part) \
                    .outerjoin(RecipeItem.leather) \
                    .all()

                for item in recipe_items:
                    if item.part:
                        values = [
                            item.part.unique_id,
                            item.part.name,
                            item.part.color,
                            item.amount,
                            item.size,
                            item.part.in_storage,
                            item.notes
                        ]
                        tree_item = self.details_tree.insert('', 'end', values=values)

                        # Add warning tag if stock is low
                        if item.part.in_storage <= item.part.warning_threshold:
                            self.details_tree.item(tree_item, tags=('low_storage',))

                    elif item.leather:
                        values = [
                            item.leather.unique_id,
                            item.leather.name,
                            item.leather.color,
                            item.amount,
                            item.size,
                            None,  # No in_storage for leather
                            item.notes
                        ]
                        self.details_tree.insert('', 'end', values=values)

        except SQLAlchemyError as e:
            messagebox.showerror("Error", f"Failed to load recipe details: {str(e)}")

    def show_add_recipe_dialog(self):
        """Show dialog for adding new recipe"""
        dialog = tk.Toplevel(self)
        dialog.title("Add New Recipe")
        dialog.transient(self)
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Entry fields
        fields = [
            ('name', 'Recipe Name', True),
            ('type', 'Type', False),
            ('collection', 'Collection', False),
            ('color', 'Color', False),
            ('pattern_id', 'Pattern ID', False),
            ('notes', 'Notes', False)
        ]

        entries = {}
        for i, (field, label, required) in enumerate(fields):
            ttk.Label(main_frame, text=f"{label}:").grid(
                row=i, column=0, sticky='w', padx=5, pady=2
            )
            entries[field] = ttk.Entry(main_frame, width=40)
            entries[field].grid(
                row=i, column=1, sticky='ew', padx=5, pady=2
            )

            if required:
                ttk.Label(main_frame, text="*", foreground="red").grid(
                    row=i, column=2, sticky='w'
                )

        def save():
            """Save new recipe"""
            try:
                # Validate required fields
                if not entries['name'].get().strip():
                    messagebox.showerror("Error", "Recipe Name is required")
                    return

                # Collect data
                data = {
                    field: entries[field].get().strip()
                    for field, _, _ in fields
                }

                # Generate unique ID
                import uuid
                prefix = ''.join(word[0].upper() for word in data['name'].split()[:2])
                data['unique_id'] = f"R{prefix}{str(uuid.uuid4())[:8]}"

                with self.db.session_scope() as session:
                    # Create recipe
                    recipe = Recipe(**data)
                    session.add(recipe)
                    session.commit()

                    # Add to undo stack
                    self.undo_stack.append(('add_recipe', recipe.id))
                    self.redo_stack.clear()

                    # Refresh view
                    self.load_data()
                    dialog.destroy()

            except SQLAlchemyError as e:
                messagebox.showerror("Error", f"Failed to add recipe: {str(e)}")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(fields), column=0, columnspan=3, pady=10)

        ttk.Button(button_frame, text="Save", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel",
                   command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Configure grid
        main_frame.columnconfigure(1, weight=1)

    def show_add_item_dialog(self):
        """Show dialog for adding item to recipe"""
        if not self.current_recipe_id:
            messagebox.showwarning("Warning", "Please select a recipe first")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Add Item to Recipe")
        dialog.transient(self)
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Get available items
        with self.db.session_scope() as session:
            parts = session.query(Part.unique_id, Part.name, Part.in_storage).all()
            leathers = session.query(Leather.unique_id, Leather.name).all()

        # Create items list for combobox
        items = ['+ Add New Part', '+ Add New Leather']
        items.extend([f"{p[1]} ({p[0]}) - Stock: {p[2]}" for p in parts])
        items.extend([f"{l[1]} ({l[0]})" for l in leathers])

        # Create fields
        ttk.Label(main_frame, text="Item:").grid(row=0, column=0, sticky='w')
        item_var = tk.StringVar()
        item_combo = ttk.Combobox(main_frame, textvariable=item_var, values=items)
        item_combo.grid(row=0, column=1, sticky='ew')

        ttk.Label(main_frame, text="Amount:").grid(row=1, column=0, sticky='w')
        amount_var = tk.StringVar(value="1")
        ttk.Spinbox(main_frame, from_=1, to=1000,
                    textvariable=amount_var).grid(row=1, column=1, sticky='ew')

        ttk.Label(main_frame, text="Size:").grid(row=2, column=0, sticky='w')
        size_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=size_var).grid(row=2, column=1, sticky='ew')

        ttk.Label(main_frame, text="Notes:").grid(row=3, column=0, sticky='w')
        notes_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=notes_var).grid(row=3, column=1, sticky='ew')

        def save():
            """Save new recipe item"""
            try:
                item_text = item_var.get()
                if item_text.startswith('+ Add New'):
                    if 'Part' in item_text:
                        dialog.destroy()
                        self.show_add_part_dialog(self)
                    else:
                        dialog.destroy()
                        self.show_add_leather_dialog(self)
                    return

                # Get unique_id from selected item
                unique_id = item_text.split('(')[1].split(')')[0]

                # Validate amount
                try:
                    amount = int(amount_var.get())
                    if amount <= 0:
                        raise ValueError("Amount must be positive")
                except ValueError as e:
                    messagebox.showerror("Error", str(e))
                    return

                # Validate size if provided
                size = size_var.get().strip()
                if size:
                    try:
                        size = float(size)
                        if size <= 0:
                            raise ValueError("Size must be positive")
                    except ValueError as e:
                        messagebox.showerror("Error", "Invalid size value")
                        return

                with self.db.session_scope() as session:
                    # Create basic item data
                    item_data = {
                        'recipe_id': self.current_recipe_id,
                        'amount': amount,
                        'size': size if size else None,
                        'notes': notes_var.get().strip()
                    }

                    # Link to part or leather based on unique_id
                    if unique_id.startswith('P'):
                        part = session.query(Part) \
                            .filter(Part.unique_id == unique_id) \
                            .first()
                        if part:
                            item_data['part_id'] = part.id
                    else:
                        leather = session.query(Leather) \
                            .filter(Leather.unique_id == unique_id) \
                            .first()
                        if leather:
                            item_data['leather_id'] = leather.id

                    # Create and add item
                    recipe_item = RecipeItem(**item_data)
                    session.add(recipe_item)
                    session.commit()

                    # Add to undo stack
                    self.undo_stack.append(('add_item', recipe_item.id))
                    self.redo_stack.clear()

                    # Refresh recipe details
                    self.load_recipe_details(self.current_recipe_id)
                    dialog.destroy()

            except SQLAlchemyError as e:
                messagebox.showerror("Error", f"Failed to add item: {str(e)}")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Add", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel",
                   command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Configure grid
        main_frame.columnconfigure(1, weight=1)

    def show_search_dialog(self):
        """Show search dialog"""
        # Implement search dialog similar to previous views
        pass

    def show_filter_dialog(self):
        """Show filter dialog"""
        # Implement filter dialog similar to previous views
        pass

    def delete_selected(self, tree):
        """Delete selected items"""
        selected = tree.selection()
        if not selected:
            return

        if not messagebox.askyesno("Confirm Delete",
                                   "Are you sure you want to delete the selected items?"):
            return

        try:
            with self.db.session_scope() as session:
                if tree == self.index_tree:
                    # Deleting recipes
                    for item_id in selected:
                        recipe_id = tree.item(item_id)['values'][0]  # unique_id
                        recipe = session.query(Recipe) \
                            .filter(Recipe.unique_id == recipe_id) \
                            .first()

                        if recipe:
                            # Store for undo
                            recipe_data = {
                                column.name: getattr(recipe, column.name)
                                for column in Recipe.__table__.columns
                            }
                            items_data = [{
                                column.name: getattr(item, column.name)
                                for column in RecipeItem.__table__.columns
                            } for item in recipe.recipe_items]

                            session.delete(recipe)
                            self.undo_stack.append(('delete_recipe', recipe_data, items_data))

                else:
                    # Deleting recipe items
                    for item_id in selected:
                        unique_id = tree.item(item_id)['values'][0]  # unique_id column

                        item = session.query(RecipeItem) \
                            .filter(RecipeItem.recipe_id == self.current_recipe_id) \
                            .filter(
                            (RecipeItem.part.has(Part.unique_id == unique_id)) |
                            (RecipeItem.leather.has(Leather.unique_id == unique_id))
                        ).first()

                        if item:
                            # Store for undo
                            item_data = {
                                column.name: getattr(item, column.name)
                                for column in RecipeItem.__table__.columns
                            }
                            session.delete(item)
                            self.undo_stack.append(('delete_item', item_data))

                session.commit()
                self.redo_stack.clear()

                # Refresh views
                if tree == self.index_tree:
                    self.load_data()
                    self.current_recipe_id = None
                else:
                    self.load_recipe_details(self.current_recipe_id)

        except SQLAlchemyError as e:
            messagebox.showerror("Error", f"Failed to delete items: {str(e)}")

    def undo(self, event=None):
        """Undo last action"""
        if not self.undo_stack:
            return

        action = self.undo_stack.pop()
        action_type = action[0]

        try:
            with self.db.session_scope() as session:
                if action_type == 'add_recipe':
                    recipe_id = action[1]
                    recipe = session.query(Recipe).get(recipe_id)
                    if recipe:
                        # Store for redo
                        recipe_data = {
                            column.name: getattr(recipe, column.name)
                            for column in Recipe.__table__.columns
                        }
                        session.delete(recipe)
                        self.redo_stack.append(('readd_recipe', recipe_data))

                elif action_type == 'add_item':
                    item_id = action[1]
                    item = session.query(RecipeItem).get(item_id)
                    if item:
                        # Store for redo
                        item_data = {
                            column.name: getattr(item, column.name)
                            for column in RecipeItem.__table__.columns
                        }
                        session.delete(item)
                        self.redo_stack.append(('readd_item', item_data))

                elif action_type == 'delete_recipe':
                    recipe_data, items_data = action[1:]
                    # Recreate recipe
                    recipe = Recipe(**recipe_data)
                    session.add(recipe)
                    session.flush()  # Get new recipe ID

                    # Recreate items
                    for item_data in items_data:
                        item_data['recipe_id'] = recipe.id
                        item = RecipeItem(**item_data)
                        session.add(item)

                    self.redo_stack.append(('redelete_recipe', recipe.id))

                elif action_type == 'delete_item':
                    item_data = action[1]
                    item = RecipeItem(**item_data)
                    session.add(item)
                    self.redo_stack.append(('redelete_item', item.id))

                session.commit()

                # Refresh views
                self.load_data()
                if self.current_recipe_id:
                    self.load_recipe_details(self.current_recipe_id)

        except SQLAlchemyError as e:
            messagebox.showerror("Error", f"Undo failed: {str(e)}")

    def redo(self, event=None):
        """Redo last undone action"""
        if not self.redo_stack:
            return

        action = self.redo_stack.pop()
        action_type = action[0]

        try:
            with self.db.session_scope() as session:
                if action_type == 'readd_recipe':
                    recipe_data = action[1]
                    recipe = Recipe(**recipe_data)
                    session.add(recipe)
                    session.flush()
                    self.undo_stack.append(('add_recipe', recipe.id))

                elif action_type == 'readd_item':
                    item_data = action[1]
                    item = RecipeItem(**item_data)
                    session.add(item)
                    session.flush()
                    self.undo_stack.append(('add_item', item.id))

                elif action_type == 'redelete_recipe':
                    recipe_id = action[1]
                    recipe = session.query(Recipe).get(recipe_id)
                    if recipe:
                        recipe_data = {
                            column.name: getattr(recipe, column.name)
                            for column in Recipe.__table__.columns
                        }
                        items_data = [{
                            column.name: getattr(item, column.name)
                            for column in RecipeItem.__table__.columns
                        } for item in recipe.recipe_items]

                        session.delete(recipe)
                        self.undo_stack.append(('delete_recipe', recipe_data, items_data))

                elif action_type == 'redelete_item':
                    item_id = action[1]
                    item = session.query(RecipeItem).get(item_id)
                    if item:
                        item_data = {
                            column.name: getattr(item, column.name)
                            for column in RecipeItem.__table__.columns
                        }
                        session.delete(item)
                        self.undo_stack.append(('delete_item', item_data))

                session.commit()

                # Refresh views
                self.load_data()
                if self.current_recipe_id:
                    self.load_recipe_details(self.current_recipe_id)

        except SQLAlchemyError as e:
            messagebox.showerror("Error", f"Redo failed: {str(e)}")

    def sort_column(self, tree, col):
        """Sort treeview column"""
        pass  # Implement sorting similar to previous views