# Path: store_management/gui/shopping_list/shopping_list_view.py
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
from typing import List, Dict, Any, Optional
from datetime import datetime

from store_management.application import Application
from store_management.gui.base_view import BaseView
from store_management.services.interfaces.shopping_list_service import IShoppingListService


class ShoppingListView(BaseView):
    """View for managing shopping lists"""

    def __init__(self, parent: tk.Widget, app: Application):
        """
        Initialize the shopping list view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)

        # Resolve shopping list service
        self.shopping_list_service = self.get_service(IShoppingListService)

        # Setup UI components
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI components."""
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Create toolbar
        self.create_toolbar()

        # Create shopping lists treeview
        self.create_lists_treeview()

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

        # Add buttons
        add_list_btn = ttk.Button(toolbar_frame, text="Add List", command=self.show_add_list_dialog)
        add_list_btn.pack(side=tk.LEFT, padx=2)

        add_item_btn = ttk.Button(toolbar_frame, text="Add Item", command=self.show_add_item_dialog)
        add_item_btn.pack(side=tk.LEFT, padx=2)

        delete_btn = ttk.Button(toolbar_frame, text="Delete", command=self.delete_list)
        delete_btn.pack(side=tk.LEFT, padx=2)

        search_btn = ttk.Button(toolbar_frame, text="Search", command=self.show_search_dialog)
        search_btn.pack(side=tk.LEFT, padx=2)

    def create_lists_treeview(self):
        """Create the treeview for displaying shopping lists."""
        # Create frame for lists
        lists_frame = ttk.Frame(self)
        lists_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)

        # Scrollbars
        lists_scroll_y = ttk.Scrollbar(lists_frame)
        lists_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        lists_scroll_x = ttk.Scrollbar(lists_frame, orient=tk.HORIZONTAL)
        lists_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview for shopping lists
        self.lists_tree = ttk.Treeview(
            lists_frame,
            yscrollcommand=lists_scroll_y.set,
            xscrollcommand=lists_scroll_x.set,
            columns
            =('ID', 'Name', 'Created Date', 'Total Estimated Cost', 'Status')
        )
        self.lists_tree.pack(expand=True, fill=tk.BOTH)

        # Configure scrollbars
        lists_scroll_y.config(command=self.lists_tree.yview)
        lists_scroll_x.config(command=self.lists_tree.xview)

        # Configure columns
        self.lists_tree.column('#0', width=0, stretch=tk.NO)
        self.lists_tree.column('ID', anchor=tk.CENTER, width=50)
        self.lists_tree.column('Name', anchor=tk.W, width=200)
        self.lists_tree.column('Created Date', anchor=tk.CENTER, width=100)
        self.lists_tree.column('Total Estimated Cost', anchor=tk.E, width=150)
        self.lists_tree.column('Status', anchor=tk.CENTER, width=100)

        # Headings
        self.lists_tree.heading('#0', text='', anchor=tk.CENTER)
        self.lists_tree.heading('ID', text='ID', anchor=tk.CENTER)
        self.lists_tree.heading('Name', text='Name', anchor=tk.W)
        self.lists_tree.heading('Created Date', text='Created Date', anchor=tk.CENTER)
        self.lists_tree.heading('Total Estimated Cost', text='Total Cost', anchor=tk.E)
        self.lists_tree.heading('Status', text='Status', anchor=tk.CENTER)

        # Bind selection event
        self.lists_tree.bind('<<TreeviewSelect>>', self.on_list_select)

    def create_details_view(self):
        """Create the shopping list details view."""
        details_frame = ttk.LabelFrame(self, text="List Details")
        details_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)

        # Create text widget for list details
        self.details_text = tk.Text(details_frame, height=5, wrap=tk.WORD)
        self.details_text.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        self.details_text.config(state=tk.DISABLED)

    def create_info_view(self):
        """Create the shopping list info view."""
        info_frame = ttk.LabelFrame(self, text="List Information")
        info_frame.grid(row=3, column=0, sticky='ew', padx=5, pady=5)

        # Create text widget for additional information
        self.info_text = tk.Text(info_frame, height=3, wrap=tk.WORD)
        self.info_text.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        self.info_text.config(state=tk.DISABLED)

    def create_items_view(self):
        """Create the shopping list items view."""
        items_frame = ttk.LabelFrame(self, text="List Items")
        items_frame.grid(row=4, column=0, sticky='ew', padx=5, pady=5)

        # Scrollbars
        items_scroll_y = ttk.Scrollbar(items_frame)
        items_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        items_scroll_x = ttk.Scrollbar(items_frame, orient=tk.HORIZONTAL)
        items_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview for list items
        self.items_tree = ttk.Treeview(
            items_frame,
            yscrollcommand=items_scroll_y.set,
            xscrollcommand=items_scroll_x.set,
            columns=('ID', 'Item', 'Quantity', 'Estimated Price', 'Purchased', 'Supplier')
        )
        self.items_tree.pack(expand=True, fill=tk.BOTH)

        # Configure scrollbars
        items_scroll_y.config(command=self.items_tree.yview)
        items_scroll_x.config(command=self.items_tree.xview)

        # Configure columns
        self.items_tree.column('#0', width=0, stretch=tk.NO)
        self.items_tree.column('ID', anchor=tk.CENTER, width=50)
        self.items_tree.column('Item', anchor=tk.W, width=200)
        self.items_tree.column('Quantity', anchor=tk.CENTER, width=100)
        self.items_tree.column('Estimated Price', anchor=tk.E, width=100)
        self.items_tree.column('Purchased', anchor=tk.CENTER, width=100)
        self.items_tree.column('Supplier', anchor=tk.W, width=150)

        # Headings
        self.items_tree.heading('#0', text='', anchor=tk.CENTER)
        self.items_tree.heading('ID', text='ID', anchor=tk.CENTER)
        self.items_tree.heading('Item', text='Item', anchor=tk.W)
        self.items_tree.heading('Quantity', text='Quantity', anchor=tk.CENTER)
        self.items_tree.heading('Estimated Price', text='Est. Price', anchor=tk.E)
        self.items_tree.heading('Purchased', text='Purchased', anchor=tk.CENTER)
        self.items_tree.heading('Supplier', text='Supplier', anchor=tk.W)

    def load_data(self):
        """Load shopping list data from service."""
        try:
            # Clear existing items
            self.lists_tree.delete(*self.lists_tree.get_children())

            # Retrieve shopping lists
            shopping_lists = self.shopping_list_service.get_all_shopping_lists()

            # Populate treeview
            for shop_list in shopping_lists:
                self.lists_tree.insert('', 'end', values=(
                    shop_list.get('id', 'N/A'),
                    shop_list.get('name', 'N/A'),
                    shop_list.get('created_at', 'N/A'),
                    shop_list.get('total_estimated_cost', 'N/A'),
                    shop_list.get('status', 'N/A')
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load shopping lists: {str(e)}")

    def on_list_select(self, event=None):
        """
        Handle shopping list selection.

        Args:
            event: Tkinter event (optional)
        """
        selected_items = self.lists_tree.selection()
        if not selected_items:
            # Clear details if no selection
            self.details_text.config(state=tk.NORMAL)
            self.details_text.delete(1.0, tk.END)
            self.details_text.config(state=tk.DISABLED)

            self.items_tree.delete(*self.items_tree.get_children())
            return

        # Get selected list ID
        list_id = self.lists_tree.item(selected_items[0])['values'][0]
        self.load_list_details(list_id)

    def load_list_details(self, list_id):
        """
        Load details for a specific shopping list.

        Args:
            list_id: ID of the shopping list to load
        """
        try:
            # Retrieve shopping list details
            shopping_list = self.shopping_list_service.get_shopping_list_by_id(list_id)

            if not shopping_list:
                messagebox.showinfo("List Not Found", f"No shopping list found with ID {list_id}")
                return

            # Update details text
            self.details_text.config(state=tk.NORMAL)
            self.details_text.delete(1.0, tk.END)

            # Display list details
            for key, value in shopping_list.items():
                if key != 'items':  # Exclude items as they'll be in separate treeview
                    self.details_text.insert(tk.END, f"{key.replace('_', ' ').title()}: {value}\n")

            self.details_text.config(state=tk.DISABLED)

            # Update items treeview
            self.items_tree.delete(*self.items_tree.get_children())
            list_items = shopping_list.get('items', [])
            for item in list_items:
                self.items_tree.insert('', 'end', values=(
                    item.get('id', 'N/A'),
                    item.get('name', 'N/A'),
                    item.get('quantity', 'N/A'),
                    item.get('estimated_price', 'N/A'),
                    'Yes' if item.get('is_purchased', False) else 'No',
                    item.get('supplier_name', 'N/A')
                ))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load shopping list details: {str(e)}")

    def show_add_list_dialog(self):
        """Show dialog for creating a new shopping list."""
        # Placeholder for add list dialog
        from store_management.gui.dialogs.add_dialog import AddDialog

        # Define fields for shopping list creation
        fields = [
            ('name', 'List Name', True, 'string'),
            ('description', 'Description', False, 'text'),
            ('priority', 'Priority', False, 'string'),
        ]

        def save_list(data):
            try:
                result = self.shopping_list_service.create_shopping_list(data)
                if result:
                    messagebox.showinfo("Success", "Shopping list created successfully")
                    self.load_data()
                else:
                    messagebox.showerror("Error", "Failed to create shopping list")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create shopping list: {str(e)}")

        dialog = AddDialog(
            self,
            save_list,
            fields,
            title="Create Shopping List"
        )

    def show_add_item_dialog(self):
        """Show dialog for adding an item to the shopping list."""
        selected_lists = self.lists_tree.selection()
        if not selected_lists:
            messagebox.showwarning("Add Item", "Please select a shopping list first.")
            return

        list_id = self.lists_tree.item(selected_lists[0])['values'][0]

        # Placeholder for add item dialog
        from store_management.gui.dialogs.add_dialog import AddDialog

        # Define fields for shopping list item
        fields = [
            ('name', 'Item Name', True, 'string'),
            ('quantity', 'Quantity', True, 'float'),
            ('estimated_price', 'Estimated Price', True, 'float'),
            ('supplier_name', 'Supplier', False, 'string'),
            ('notes', 'Notes', False, 'text')
        ]

        def save_item(data):
            try:
                result = self.shopping_list_service.add_item_to_list(list_id, data)
                if result:
                    messagebox.showinfo("Success", "Item added successfully")
                    # Reload list details to show new item
                    self.load_list_details(list_id)
                else:
                    messagebox.showerror("Error", "Failed to add item")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add item: {str(e)}")

        dialog = AddDialog(
            self,
            save_item,
            fields,
            title="Add Shopping List Item"
        )

    def show_mark_purchased_dialog(self):
        """Show dialog for marking an item as purchased."""
        selected_items = self.items_tree.selection()
        if not selected_items:
            messagebox.showwarning("Mark Purchased", "Please select an item to mark as purchased.")
            return

        item_id = self.items_tree.item(selected_items[0])['values'][0]

        # Placeholder for mark purchased dialog
        from store_management.gui.dialogs.add_dialog import AddDialog

        # Define fields for purchase details
        fields = [
            ('purchase_date', 'Purchase Date', True, 'string'),
            ('actual_price', 'Actual Price', True, 'float'),
            ('notes', 'Notes', False, 'text')
        ]

        def save_purchase_details(data):
            try:
                result = self.shopping_list_service.mark_item_purchased(item_id, data)
                if result:
                    messagebox.showinfo("Success", "Item marked as purchased")
                    # Reload current list details to reflect changes
                    selected_lists = self.lists_tree.selection()
                    if selected_lists:
                        list_id = self.lists_tree.item(selected_lists[0])['values'][0]
                        self.load_list_details(list_id)
                else:
                    messagebox.showerror("Error", "Failed to mark item as purchased")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to mark item: {str(e)}")

        dialog = AddDialog(
            self,
            save_purchase_details,
            fields,
            title="Mark Item Purchased"
        )

    def remove_item(self):
        """Remove selected item from the shopping list."""
        selected_items = self.items_tree.selection()
        if not selected_items:
            messagebox.showwarning("Remove Item", "Please select an item to remove.")
            return

        item_id = self.items_tree.item(selected_items[0])['values'][0]
        selected_lists = self.lists_tree.selection()

        if not selected_lists:
            messagebox.showwarning("Remove Item", "Please select a shopping list first.")
            return

        list_id = self.lists_tree.item(selected_lists[0])['values'][0]

        confirm = messagebox.askyesno(
            "Confirm Removal",
            f"Are you sure you want to remove this item from the shopping list?"
        )

        if confirm:
            try:
                result = self.shopping_list_service.remove_item_from_list(list_id, item_id)
                if result:
                    messagebox.showinfo("Success", "Item removed successfully")
                    # Reload list details
                    self.load_list_details(list_id)
                else:
                    messagebox.showerror("Error", "Failed to remove item")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove item: {str(e)}")

    def delete_list(self):
        """Delete the selected shopping list."""
        selected_lists = self.lists_tree.selection()
        if not selected_lists:
            messagebox.showwarning("Delete List", "Please select a shopping list to delete.")
            return

        list_id = self.lists_tree.item(selected_lists[0])['values'][0]

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete this shopping list?"
        )

        if confirm:
            try:
                result = self.shopping_list_service.delete_shopping_list(list_id)
                if result:
                    messagebox.showinfo("Success", "Shopping list deleted successfully")
                    # Refresh list view
                    self.load_data()
                else:
                    messagebox.showerror("Error", "Failed to delete shopping list")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete shopping list: {str(e)}")

    def show_search_dialog(self):
        """Show search dialog for shopping lists."""
        from store_management.gui.dialogs.search_dialog import SearchDialog

        def perform_search(search_term):
            try:
                # Clear existing items
                self.lists_tree.delete(*self.lists_tree.get_children())

                # Perform search
                results = self.shopping_list_service.search_shopping_lists(search_term)

                # Populate treeview with search results
                for shop_list in results:
                    self.lists_tree.insert('', 'end', values=(
                        shop_list.get('id', 'N/A'),
                        shop_list.get('name', 'N/A'),
                        shop_list.get('created_at', 'N/A'),
                        shop_list.get('total_estimated_cost', 'N/A'),
                        shop_list.get('status', 'N/A')
                    ))
            except Exception as e:
                messagebox.showerror("Search Error", f"Failed to search shopping lists: {str(e)}")

        SearchDialog(
            self,
            perform_search,
            columns=['Name', 'Description'],
            title="Search Shopping Lists"
        )

    def save(self):
        """Save current view data."""
        try:
            # Implement save logic for shopping lists
            # This might involve saving unsaved items or synchronizing with service
            selected_lists = self.lists_tree.selection()
            if selected_lists:
                list_id = self.lists_tree.item(selected_lists[0])['values'][0]
                self.shopping_list_service.save_shopping_list(list_id)
                messagebox.showinfo("Save", "Shopping list saved successfully")
            else:
                messagebox.showwarning("Save", "Please select a shopping list to save")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save shopping list: {str(e)}")

    def undo(self):
        """Undo the last action."""
        try:
            # Implement undo logic
            # This might involve calling an undo method on the shopping list service
            result = self.shopping_list_service.undo_last_action()
            if result:
                messagebox.showinfo("Undo", "Last action undone successfully")
                # Refresh view
                self.load_data()
            else:
                messagebox.showinfo("Undo", "No actions to undo")
        except Exception as e:
            messagebox.showerror("Undo Error", f"Failed to undo last action: {str(e)}")

    def redo(self):
        """Redo the last undone action."""
        try:
            # Implement redo logic
            # This might involve calling a redo method on the shopping list service
            result = self.shopping_list_service.redo_last_action()
            if result:
                messagebox.showinfo("Redo", "Last action redone successfully")
                # Refresh view
                self.load_data()
            else:
                messagebox.showinfo("Redo", "No actions to redo")
        except Exception as e:
            messagebox.showerror("Redo Error", f"Failed to redo last action: {str(e)}")

    def cleanup(self):
        """Perform cleanup when view is closed."""
        # Any necessary cleanup operations
        # This might include:
        # - Saving any unsaved data
        # - Clearing cached data
        # - Releasing resources
        try:
            # Optional: save any unsaved changes
            self.save()
        except Exception as e:
            # Log or handle any errors during cleanup
            messagebox.showerror("Cleanup Error", f"Error during view cleanup: {str(e)}")