# Path: store_management/gui/recipe/recipe_view.py
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
from typing import List, Dict, Any, Optional
from datetime import datetime

from store_management.application import Application
from store_management.gui.base_view import BaseView
from store_management.services.interfaces.recipe_service import IRecipeService
from store_management.services.interfaces.inventory_service import IInventoryService


class RecipeView(BaseView):
    """View for managing recipes with comprehensive functionality."""

    def __init__(self, parent: tk.Widget, app: Application):
        """
        Initialize the recipe view.

        Args:
            parent: Parent widget
            app: Application instance for dependency management
        """
        super().__init__(parent, app)

        # Resolve required services
        self.recipe_service = self.get_service(IRecipeService)
        self.inventory_service = self.get_service(IInventoryService)

        # Setup UI components
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI components for the recipe view."""
        # Create main layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Create toolbar
        self.create_toolbar()

        # Create recipes treeview
        self.create_recipes_treeview()

        # Create details view
        self.create_details_view()

        # Create info view
        self.create_info_view()

        # Create items view
        self.create_items_view()

    def create_toolbar(self):
        """Create the toolbar with action buttons."""
        toolbar_frame = ttk.Frame(self)
        toolbar_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)

        # Add buttons for common recipe actions
        add_btn = ttk.Button(toolbar_frame, text="Add Recipe", command=self.show_add_recipe_dialog)
        add_btn.pack(side=tk.LEFT, padx=2)

        edit_btn = ttk.Button(toolbar_frame, text="Edit Recipe", command=self.edit_recipe)
        edit_btn.pack(side=tk.LEFT, padx=2)

        delete_btn = ttk.Button(toolbar_frame, text="Delete Recipe", command=self.delete_recipe)
        delete_btn.pack(side=tk.LEFT, padx=2)

    def create_recipes_treeview(self):
        """Create the treeview for displaying recipes."""
        # Create treeview frame
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)

        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview
        self.recipe_tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
            columns=('ID', 'Name', 'Description', 'Product', 'Created At')
        )
        self.recipe_tree.pack(expand=True, fill=tk.BOTH)

        # Configure scrollbars
        tree_scroll_y.config(command=self.recipe_tree.yview)
        tree_scroll_x.config(command=self.recipe_tree.xview)

        # Configure columns
        self.recipe_tree.column('#0', width=0, stretch=tk.NO)
        self.recipe_tree.column('ID', anchor=tk.CENTER, width=50)
        self.recipe_tree.column('Name', anchor=tk.W, width=150)
        self.recipe_tree.column('Description', anchor=tk.W, width=200)
        self.recipe_tree.column('Product', anchor=tk.W, width=100)
        self.recipe_tree.column('Created At', anchor=tk.CENTER, width=100)

        # Headings
        self.recipe_tree.heading('#0', text='', anchor=tk.CENTER)
        self.recipe_tree.heading('ID', text='ID', anchor=tk.CENTER)
        self.recipe_tree.heading('Name', text='Name', anchor=tk.W)
        self.recipe_tree.heading('Description', text='Description', anchor=tk.W)
        self.recipe_tree.heading('Product', text='Product', anchor=tk.W)
        self.recipe_tree.heading('Created At', text='Created At', anchor=tk.CENTER)

        # Bind selection event
        self.recipe_tree.bind('<<TreeviewSelect>>', self.on_recipe_select)

    def create_details_view(self):
        """Create the recipe details view."""
        details_frame = ttk.LabelFrame(self, text="Recipe Details")
        details_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)

        # Placeholder for detailed recipe information
        self.details_text = tk.Text(details_frame, height=5, wrap=tk.WORD)
        self.details_text.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        self.details_text.config(state=tk.DISABLED)

    def create_info_view(self):
        """Create the recipe info view."""
        info_frame = ttk.LabelFrame(self, text="Recipe Information")
        info_frame.grid(row=3, column=0, sticky='ew', padx=5, pady=5)

        # Placeholders for additional recipe information
        self.info_text = tk.Text(info_frame, height=3, wrap=tk.WORD)
        self.info_text.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        self.info_text.config(state=tk.DISABLED)

    def create_items_view(self):
        """Create the recipe items view."""
        items_frame = ttk.LabelFrame(self, text="Recipe Items")
        items_frame.grid(row=4, column=0, sticky='ew', padx=5, pady=5)

        # Create treeview for recipe items
        self.items_tree = ttk.Treeview(
            items_frame,
            columns=('Item', 'Quantity', 'Type'),
            show='headings'
        )
        self.items_tree.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Configure columns
        self.items_tree.column('Item', anchor=tk.W, width=200)
        self.items_tree.column('Quantity', anchor=tk.CENTER, width=100)
        self.items_tree.column('Type', anchor=tk.W, width=100)

        # Headings
        self.items_tree.heading('Item', text='Item')
        self.items_tree.heading('Quantity', text='Quantity')
        self.items_tree.heading('Type', text='Type')

    def on_recipe_select(self, event=None):
        """Handle recipe selection in treeview."""
        selected_item = self.recipe_tree.selection()
        if not selected_item:
            return

        # Retrieve recipe ID from selected item
        recipe_id = self.recipe_tree.item(selected_item[0])['values'][0]
        self.load_recipe_details(recipe_id)

    def load_recipe_details(self, recipe_id):
        """
        Load details for a specific recipe.

        Args:
            recipe_id: ID of the recipe to load
        """
        try:
            # Retrieve recipe details from service
            recipe = self.recipe_service.get_recipe_by_id(recipe_id)

            if not recipe:
                messagebox.showinfo("Recipe Not Found", f"No recipe found with ID {recipe_id}")
                return

            # Update details text
            self.details_text.config(state=tk.NORMAL)
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(tk.END, f"Recipe Name: {recipe.get('name', 'N/A')}\n")
            self.details_text.insert(tk.END, f"Description: {recipe.get('description', 'N/A')}\n")
            self.details_text.config(state=tk.DISABLED)

            # Update items tree
            self.items_tree.delete(*self.items_tree.get_children())
            recipe_items = recipe.get('items', [])
            for item in recipe_items:
                self.items_tree.insert('', 'end', values=(
                    item.get('name', 'N/A'),
                    item.get('quantity', 'N/A'),
                    item.get('type', 'N/A')
                ))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load recipe details: {str(e)}")

    def show_add_recipe_dialog(self):
        """Show dialog for adding a new recipe."""
        # Placeholder for add recipe dialog
        messagebox.showinfo("Add Recipe", "Add recipe functionality not implemented yet.")

    def edit_recipe(self):
        """Edit the selected recipe."""
        selected_item = self.recipe_tree.selection()
        if not selected_item:
            messagebox.showwarning("Edit Recipe", "Please select a recipe to edit.")
            return

        recipe_id = self.recipe_tree.item(selected_item[0])['values'][0]
        # Placeholder for edit recipe dialog
        messagebox.showinfo("Edit Recipe", f"Edit recipe {recipe_id} functionality not implemented yet.")

    def delete_recipe(self):
        """Delete the selected recipe."""
        selected_item = self.recipe_tree.selection()
        if not selected_item:
            messagebox.showwarning("Delete Recipe", "Please select a recipe to delete.")
            return

        recipe_id = self.recipe_tree.item(selected_item[0])['values'][0]
        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete recipe {recipe_id}?")

        if confirm:
            # Placeholder for delete recipe logic
            messagebox.showinfo("Delete Recipe", f"Delete recipe {recipe_id} functionality not implemented yet.")

    def load_data(self):
        """Load recipe data from service."""
        try:
            # Retrieve recipes from service
            recipes = self.recipe_service.get_all_recipes()

            # Clear existing items
            self.recipe_tree.delete(*self.recipe_tree.get_children())

            # Populate treeview
            for recipe in recipes:
                self.recipe_tree.insert('', 'end', values=(
                    recipe.get('id', 'N/A'),
                    recipe.get('name', 'N/A'),
                    recipe.get('description', 'N/A'),
                    recipe.get('product_name', 'N/A'),
                    recipe.get('created_at', 'N/A')
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load recipes: {str(e)}")

    def cleanup(self):
        """Perform cleanup when view is closed."""
        # Any necessary cleanup operations
        pass