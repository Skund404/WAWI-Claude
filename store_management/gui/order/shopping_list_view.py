# Path: gui/order/shopping_list_view.py
import logging
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional

from di.core import inject
from gui.base_view import BaseView
from services.interfaces.shopping_list_service import (
    IShoppingListService,
    ShoppingListStatus
)
from services.interfaces.material_service import IMaterialService
from utils.error_handler import ApplicationError


class ShoppingListView(BaseView):
    """
    View for managing shopping lists for leatherworking supplies.
    Implements sophisticated undo/redo functionality and follows base view pattern.
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the shopping list view.

        Args:
            parent: Parent widget
            app: Application instance for accessing services
        """
        super().__init__(parent, app)

        # Get services through dependency injection
        self.shopping_list_service: IShoppingListService = self.get_service(IShoppingListService)
        self.material_service: IMaterialService = self.get_service(IMaterialService)

        # UI Components
        self.lists_tree: Optional[ttk.Treeview] = None
        self.items_tree: Optional[ttk.Treeview] = None
        self.current_list_id: Optional[int] = None

        # Sophisticated Undo/Redo Mechanism
        self._action_stack: List[Dict[str, Any]] = []
        self._redo_stack: List[Dict[str, Any]] = []
        self._max_undo_steps = 50  # Limit undo steps to prevent memory issues

        # Setup the view
        self._setup_view()

    def debug_model_registration(self):
        """
        Debug method to investigate model registration issues.
        """
        try:
            from database.models.base import Base

            # Get registered models
            registered_models = Base.debug_registered_models()

            # Log each registered model
            for model_name in registered_models:
                self._logger.info(f"Registered Model: {model_name}")

        except Exception as e:
            self._logger.error(f"Error debugging model registration: {str(e)}")

    def _setup_view(self):
        """
        Set up the basic view structure for the shopping list.
        """
        # Main layout frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create lists selection section
        lists_frame = ttk.LabelFrame(main_frame, text="Shopping Lists")
        lists_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)

        # Create items section
        items_frame = ttk.LabelFrame(main_frame, text="List Items")
        items_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Setup list selection treeview
        self._create_lists_treeview(lists_frame)

        # Setup items treeview
        self._create_items_treeview(items_frame)

        # Setup toolbar
        self._create_toolbar()

        # Initial data load
        self.on_refresh()

    def _create_lists_treeview(self, parent):
        """
        Create the treeview for shopping lists.

        Args:
            parent: Parent widget for the treeview
        """
        columns = ("id", "name", "date", "status")
        self.lists_tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)

        # Configure columns
        for col in columns:
            self.lists_tree.heading(col, text=col.capitalize())
            self.lists_tree.column(col, width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.lists_tree.yview)
        self.lists_tree.configure(yscrollcommand=scrollbar.set)

        # Pack widgets
        self.lists_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind selection event
        self.lists_tree.bind("<<TreeviewSelect>>", self._on_list_select)
        # Add double-click event for editing
        self.lists_tree.bind("<Double-1>", self.on_edit)

    def _create_items_treeview(self, parent):
        """
        Create the treeview for shopping list items.

        Args:
            parent: Parent widget for the treeview
        """
        columns = ("id", "item", "quantity", "unit", "notes", "priority")
        self.items_tree = ttk.Treeview(parent, columns=columns, show="headings")

        # Configure columns
        for col in columns:
            self.items_tree.heading(col, text=col.capitalize())
            self.items_tree.column(col, width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=scrollbar.set)

        # Pack widgets
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click event for editing
        self.items_tree.bind("<Double-1>", self.show_edit_item_dialog)

    def _create_toolbar(self):
        """
        Create toolbar with action buttons.
        """
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Action buttons
        actions = [
            ("New List", self.on_new),
            ("Edit List", self.on_edit),
            ("Delete List", self.on_delete),
            ("Add Item", self.show_add_item_dialog),
            ("Edit Item", self.show_edit_item_dialog),
            ("Delete Items", self.delete_selected_items),
            ("Refresh", self.on_refresh),
            ("Save", self.on_save),
            ("Undo", self.undo),
            ("Redo", self.redo)
        ]

        for label, command in actions:
            ttk.Button(toolbar, text=label, command=command).pack(side=tk.LEFT, padx=2)

    def _on_list_select(self, event=None):
        """
        Handle shopping list selection.
        """
        selection = self.lists_tree.selection()
        if not selection:
            return

        try:
            self.current_list_id = int(self.lists_tree.item(selection[0], "values")[0])
            self._load_list_items(self.current_list_id)
        except Exception as e:
            self.show_error("Selection Error", f"Could not load list items: {e}")
            logging.error(f"Error selecting shopping list: {e}")

    def _load_list_items(self, list_id: int):
        """
        Load items for a specific shopping list.

        Args:
            list_id: ID of the shopping list to load
        """
        # Clear existing items
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)

        try:
            # Fetch list items using service
            items = self.shopping_list_service.get_list_items(list_id)

            # Populate treeview
            for item in items:
                self.items_tree.insert("", tk.END, values=(
                    item.id,
                    item.name,
                    item.quantity,
                    item.unit,
                    item.notes or "",
                    item.priority
                ))
        except Exception as e:
            self.show_error("Load Error", f"Could not load list items: {e}")
            logging.error(f"Error loading shopping list items: {e}")

    def _record_action(self, action_type: str, details: Dict[str, Any]):
        """
        Record an action for undo/redo functionality.

        Args:
            action_type: Type of action performed
            details: Detailed information about the action
        """
        action = {
            'type': action_type,
            'details': details,
            'timestamp': datetime.now()
        }

        # Add to action stack
        self._action_stack.append(action)

        # Clear redo stack when a new action is performed
        self._redo_stack.clear()

        # Limit the number of undo steps
        if len(self._action_stack) > self._max_undo_steps:
            self._action_stack.pop(0)

    def _prepare_item_update_action(self, list_id: int, original_item: Dict[str, Any], updated_item: Dict[str, Any]) -> \
    Dict[str, Any]:
        """
        Prepare an action details dictionary for item updates.

        Args:
            list_id: ID of the shopping list
            original_item: Original item details
            updated_item: Updated item details

        Returns:
            Dict containing action details for undo/redo
        """
        return {
            'list_id': list_id,
            'item_id': original_item['id'],
            'old_name': original_item['name'],
            'old_quantity': original_item['quantity'],
            'old_unit': original_item['unit'],
            'old_notes': original_item.get('notes', ''),
            'old_priority': original_item.get('priority', 'MEDIUM'),
            'new_name': updated_item.get('name', original_item['name']),
            'new_quantity': updated_item.get('quantity', original_item['quantity']),
            'new_unit': updated_item.get('unit', original_item['unit']),
            'new_notes': updated_item.get('notes', original_item.get('notes', '')),
            'new_priority': updated_item.get('priority', original_item.get('priority', 'MEDIUM')),
            'timestamp': datetime.now()
        }

    def on_new(self):
        """
        Handle creating a new shopping list.
        Supports undo/redo functionality.
        """
        dialog = tk.Toplevel(self)
        dialog.title("New Shopping List")
        dialog.geometry("300x200")
        dialog.transient(self)
        dialog.grab_set()

        # Name input
        ttk.Label(dialog, text="List Name:").pack(pady=(10, 0))
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=30).pack(pady=(5, 10))

        # Status selection
        ttk.Label(dialog, text="Status:").pack()
        status_var = tk.StringVar(value=ShoppingListStatus.DRAFT.name)
        status_combo = ttk.Combobox(
            dialog,
            textvariable=status_var,
            values=[status.name for status in ShoppingListStatus]
        )
        status_combo.pack(pady=(0, 10))

        def save():
            name = name_var.get().strip()
            status = ShoppingListStatus[status_var.get()]

            if not name:
                messagebox.showwarning("Warning", "Please enter a list name")
                return

            try:
                # Create new list using service
                new_list = self.shopping_list_service.create_list(name, status)

                # Record the action for undo/redo
                action_details = {
                    'list_id': new_list.id,
                    'name': name,
                    'status': status,
                    'items': [],  # Placeholder for potential future item tracking
                    'timestamp': datetime.now()
                }
                self._record_action('CREATE_LIST', action_details)

                # Refresh view and close dialog
                self.on_refresh()
                dialog.destroy()
            except Exception as e:
                self.show_error("Creation Error", f"Could not create shopping list: {e}")
                logging.error(f"Error creating shopping list: {e}")

        # Save and Cancel buttons
        ttk.Button(dialog, text="Save", command=save).pack(side=tk.LEFT, padx=20, pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=20, pady=10)

    def on_edit(self, event=None):
        """
        Handle editing the selected shopping list.
        Supports undo/redo functionality.
        """
        # Determine the source of the event (button or double-click)
        if event and event.widget == self.lists_tree:
            # Double-click event on lists tree
            selection = self.lists_tree.selection()
            if not selection:
                return
            self.current_list_id = int(self.lists_tree.item(selection[0], "values")[0])

        if not self.current_list_id:
            self.show_info("Info", "Please select a shopping list to edit")
            return

        try:
            # Fetch current list details
            current_list = self.shopping_list_service.get_list(self.current_list_id)

            # Create edit dialog
            dialog = tk.Toplevel(self)
            dialog.title("Edit Shopping List")
            dialog.geometry("300x200")
            dialog.transient(self)
            dialog.grab_set()

            # Name input
            ttk.Label(dialog, text="List Name:").pack(pady=(10, 0))
            name_var = tk.StringVar(value=current_list.name)
            ttk.Entry(dialog, textvariable=name_var, width=30).pack(pady=(5, 10))

            # Status selection
            ttk.Label(dialog, text="Status:").pack()
            status_var = tk.StringVar(value=current_list.status.name)
            status_combo = ttk.Combobox(
                dialog,
                textvariable=status_var,
                values=[status.name for status in ShoppingListStatus]
            )
            status_combo.pack(pady=(0, 10))

            def save():
                name = name_var.get().strip()
                status = ShoppingListStatus[status_var.get()]

                if not name:
                    messagebox.showwarning("Warning", "Please enter a list name")
                    return

                try:
                    # Prepare undo/redo action details
                    action_details = {
                        'list_id': self.current_list_id,
                        'old_name': current_list.name,
                        'old_status': current_list.status,
                        'new_name': name,
                        'new_status': status,
                        'timestamp': datetime.now()
                    }

                    # Update list using service
                    self.shopping_list_service.update_list(
                        self.current_list_id,
                        name=name,
                        status=status
                    )

                    # Record the action for undo/redo
                    self._record_action('UPDATE_LIST', action_details)

                    self.on_refresh()
                    dialog.destroy()
                except Exception as e:
                    self.show_error("Update Error", f"Could not update shopping list: {e}")
                    logging.error(f"Error updating shopping list: {e}")

            # Save and Cancel buttons
            ttk.Button(dialog, text="Save", command=save).pack(side=tk.LEFT, padx=20, pady=10)
            ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=20, pady=10)

        except Exception as e:
            self.show_error("Fetch Error", f"Could not retrieve list details: {e}")
            logging

    def on_delete(self):
        """
        Handle deleting the selected shopping list.
        Supports undo/redo functionality.
        """
        if not self.current_list_id:
            self.show_info("Info", "Please select a shopping list to delete")
            return

        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this shopping list?"):
            return

        try:
            # Fetch current list details for potential undo
            current_list = self.shopping_list_service.get_list(self.current_list_id)

            # Prepare action details for undo
            action_details = {
                'list_id': self.current_list_id,
                'name': current_list.name,
                'status': current_list.status,
                'items': [],  # Placeholder for potential future item tracking
                'timestamp': datetime.now()
            }

            # Delete list using service
            self.shopping_list_service.delete_list(self.current_list_id)

            # Record the action for undo
            self._record_action('DELETE_LIST', action_details)

            self.current_list_id = None
            self.on_refresh()
        except Exception as e:
            self.show_error("Deletion Error", f"Could not delete shopping list: {e}")
            logging.error(f"Error deleting shopping list: {e}")

    def show_add_item_dialog(self):
        """
        Show dialog for adding an item to the shopping list.
        """
        if not self.current_list_id:
            self.show_info("Info", "Please select a shopping list first")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Add Shopping List Item")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Create form
        form_frame = ttk.Frame(dialog)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(form_frame, text="Item Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=name_var, width=30).grid(row=0, column=1, sticky=tk.W, pady=5)

        ttk.Label(form_frame, text="Quantity:").grid(row=1, column=0, sticky=tk.W, pady=5)
        quantity_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=quantity_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=5)

        ttk.Label(form_frame, text="Unit:").grid(row=2, column=0, sticky=tk.W, pady=5)
        unit_var = tk.StringVar()
        ttk.Combobox(form_frame, textvariable=unit_var, values=["piece", "meter", "sq.m", "kg", "g"]).grid(row=2,
                                                                                                           column=1,
                                                                                                           sticky=tk.W,
                                                                                                           pady=5)

        ttk.Label(form_frame, text="Notes:").grid(row=3, column=0, sticky=tk.W, pady=5)
        notes_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=notes_var, width=30).grid(row=3, column=1, sticky=tk.W, pady=5)

        ttk.Label(form_frame, text="Priority:").grid(row=4, column=0, sticky=tk.W, pady=5)
        priority_var = tk.StringVar(value="MEDIUM")
        ttk.Combobox(form_frame, textvariable=priority_var, values=["LOW", "MEDIUM", "HIGH", "URGENT"]).grid(row=4,
                                                                                                             column=1,
                                                                                                             sticky=tk.W,
                                                                                                             pady=5)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def save_item():
            try:
                name = name_var.get().strip()
                if not name:
                    messagebox.showwarning("Warning", "Please enter an item name")
                    return

                try:
                    quantity = float(quantity_var.get())
                except ValueError:
                    messagebox.showwarning("Warning", "Quantity must be a number")
                    return

                # Add item using service
                new_item = self.shopping_list_service.add_item_to_list(
                    self.current_list_id,
                    name,
                    quantity,
                    unit_var.get(),
                    notes_var.get(),
                    priority_var.get()
                )

                # Prepare action details for undo/redo
                action_details = {
                    'list_id': self.current_list_id,
                    'item_id': new_item.id,
                    'name': name,
                    'quantity': quantity,
                    'unit': unit_var.get(),
                    'notes': notes_var.get(),
                    'priority': priority_var.get(),
                    'timestamp': datetime.now()
                }

                # Record the action for undo/redo
                self._record_action('ADD_ITEM', action_details)

                # Refresh the list items
                self._load_list_items(self.current_list_id)

                dialog.destroy()
            except Exception as e:
                self.show_error("Add Item Error", f"Could not add item: {e}")
                logging.error(f"Error adding shopping list item: {e}")

        ttk.Button(button_frame, text="Save", command=save_item).pack(side=tk.LEFT, padx=20)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=20)

    def show_edit_item_dialog(self, event=None):
        """
        Show dialog for editing a shopping list item.
        Supports undo/redo functionality.
        """
        # If triggered by double-click, get selection from the event widget
        if event and event.widget == self.items_tree:
            selection = self.items_tree.selection()
            if not selection:
                return
        else:
            # If triggered by button, get current selection
            selection = self.items_tree.selection()
            if not selection:
                self.show_info("Info", "Please select an item to edit")
                return

        if not self.current_list_id:
            self.show_info("Info", "No shopping list selected")
            return

        # Get selected item details
        item_values = self.items_tree.item(selection[0], "values")
        item_id = int(item_values[0])

        try:
            # Fetch full item details
            original_item = self.shopping_list_service.get_list_item(item_id)

            # Create edit dialog
            dialog = tk.Toplevel(self)
            dialog.title("Edit Shopping List Item")
            dialog.geometry("400x300")
            dialog.resizable(False, False)
            dialog.transient(self)
            dialog.grab_set()

            # Create form
            form_frame = ttk.Frame(dialog)
            form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Name input
            ttk.Label(form_frame, text="Item Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
            name_var = tk.StringVar(value=original_item.name)
            ttk.Entry(form_frame, textvariable=name_var, width=30).grid(row=0, column=1, sticky=tk.W, pady=5)

            # Quantity input
            ttk.Label(form_frame, text="Quantity:").grid(row=1, column=0, sticky=tk.W, pady=5)
            quantity_var = tk.StringVar(value=str(original_item.quantity))
            ttk.Entry(form_frame, textvariable=quantity_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=5)

            # Unit selection
            ttk.Label(form_frame, text="Unit:").grid(row=2, column=0, sticky=tk.W, pady=5)
            unit_var = tk.StringVar(value=original_item.unit)
            ttk.Combobox(form_frame, textvariable=unit_var, values=["piece", "meter", "sq.m", "kg", "g"]).grid(
                row=2, column=1, sticky=tk.W, pady=5
            )

            # Notes input
            ttk.Label(form_frame, text="Notes:").grid(row=3, column=0, sticky=tk.W, pady=5)
            notes_var = tk.StringVar(value=original_item.notes or '')
            ttk.Entry(form_frame, textvariable=notes_var, width=30).grid(row=3, column=1, sticky=tk.W, pady=5)

            # Priority selection
            ttk.Label(form_frame, text="Priority:").grid(row=4, column=0, sticky=tk.W, pady=5)
            priority_var = tk.StringVar(value=original_item.priority)
            ttk.Combobox(form_frame, textvariable=priority_var, values=["LOW", "MEDIUM", "HIGH", "URGENT"]).grid(
                row=4, column=1, sticky=tk.W, pady=5
            )

            def save_item():
                try:
                    # Validate inputs
                    name = name_var.get().strip()
                    if not name:
                        messagebox.showwarning("Warning", "Please enter an item name")
                        return

                    try:
                        quantity = float(quantity_var.get())
                    except ValueError:
                        messagebox.showwarning("Warning", "Quantity must be a number")
                        return

                    # Prepare update details
                    updated_item_data = {
                        'name': name,
                        'quantity': quantity,
                        'unit': unit_var.get(),
                        'notes': notes_var.get(),
                        'priority': priority_var.get()
                    }

                    # Prepare action details for undo
                    action_details = self._prepare_item_update_action(
                        self.current_list_id,
                        {
                            'id': item_id,
                            'name': original_item.name,
                            'quantity': original_item.quantity,
                            'unit': original_item.unit,
                            'notes': original_item.notes,
                            'priority': original_item.priority
                        },
                        updated_item_data
                    )

                    # Update item using service
                    self.shopping_list_service.update_list_item(
                        item_id,
                        name=name,
                        quantity=quantity,
                        unit=unit_var.get(),
                        notes=notes_var.get(),
                        priority=priority_var.get()
                    )

                    # Record the action for undo/redo
                    self._record_action('UPDATE_ITEM', action_details)

                    # Refresh the list items
                    self._load_list_items(self.current_list_id)

                    # Close dialog
                    dialog.destroy()

                except Exception as e:
                    self.show_error("Update Error", f"Could not update item: {e}")
                    logging.error(f"Error updating shopping list item: {e}")

            # Save and Cancel buttons
            ttk.Button(form_frame, text="Save", command=save_item).grid(row=5, column=0, pady=10)
            ttk.Button(form_frame, text="Cancel", command=dialog.destroy).grid(row=5, column=1, pady=10)

        except Exception as e:
            self.show_error("Fetch Error", f"Could not retrieve item details: {e}")
            logging.error(f"Error fetching shopping list item details: {e}")

    def delete_selected_items(self):
        """
        Delete selected items from the current shopping list.
        Supports undo/redo functionality.
        """
        if not self.current_list_id:
            self.show_info("Info", "Please select a shopping list first")
            return

        selection = self.items_tree.selection()
        if not selection:
            self.show_info("Info", "Please select items to delete")
            return

        if not messagebox.askyesno("Confirm", "Are you sure you want to delete the selected items?"):
            return

        try:
            # Track items for potential undo
            deleted_items = []

            for item in selection:
                item_values = self.items_tree.item(item, "values")
                item_id = int(item_values[0])

                # Get full item details for potential undo
                item_details = self.shopping_list_service.get_list_item(item_id)

                # Remove item from list
                self.shopping_list_service.remove_item_from_list(self.current_list_id, item_id)

                # Store item details for potential undo
                deleted_items.append({
                    'item_id': item_id,
                    'list_id': self.current_list_id,
                    'name': item_details.name,
                    'quantity': item_details.quantity,
                    'unit': item_details.unit,
                    'notes': item_details.notes or '',
                    'priority': item_details.priority,
                    'timestamp': datetime.now()
                })

            # Record the delete action for undo
            self._record_action('REMOVE_ITEM', {
                'list_id': self.current_list_id,
                'items': deleted_items
            })

            # Refresh the list items
            self._load_list_items(self.current_list_id)
        except Exception as e:
            self.show_error("Delete Error", f"Could not delete items: {e}")
            logging.error(f"Error deleting shopping list items: {e}")

    def undo(self):
        """
        Sophisticated undo mechanism that handles multiple action types.
        """
        if not self._action_stack:
            self.show_info("Undo", "No actions to undo")
            return

        # Pop the last action
        last_action = self._action_stack.pop()

        # Add to redo stack
        self._redo_stack.append(last_action)

        # Attempt to undo the action
        if self._undo_action(last_action):
            self.show_info("Undo", f"Undid {last_action['type']} action")
            self.on_refresh()
        else:
            # If undo fails, remove from redo stack
            self._redo_stack.pop()

    def redo(self):
        """
        Sophisticated redo mechanism that handles multiple action types.
        """
        if not self._redo_stack:
            self.show_info("Redo", "No actions to redo")
            return

        # Pop the last undone action
        last_action = self._redo_stack.pop()

        # Add back to action stack
        self._action_stack.append(last_action)

        # Attempt to redo the action
        if self._redo_action(last_action):
            self.show_info("Redo", f"Redid {last_action['type']} action")
            self.on_refresh()
        else:
            # If redo fails, remove from action stack
            self._action_stack.pop()

        def _undo_action(self, action: Dict[str, Any]) -> bool:
            """
            Undo a specific action.

            Args:
                action: Action to undo

            Returns:
                bool: Whether the undo was successful
            """
            action_type = action['type']
            details = action['details']

            try:
                if action_type == 'CREATE_LIST':
                    # Undo list creation by deleting the list
                    self.shopping_list_service.delete_list(details['list_id'])
                    return True

                elif action_type == 'DELETE_LIST':
                    # Undo list deletion by recreating the list
                    recreated_list = self.shopping_list_service.create_list(
                        details['name'],
                        details['status']
                    )
                    # Restore list items if applicable
                    if 'items' in details:
                        for item in details['items']:
                            self.shopping_list_service.add_item_to_list(
                                recreated_list.id,
                                item['name'],
                                item['quantity'],
                                item['unit'],
                                item.get('notes', ''),
                                item.get('priority', 'MEDIUM')
                            )
                    return True

                elif action_type == 'UPDATE_LIST':
                    # Undo list update by reverting to previous state
                    self.shopping_list_service.update_list(
                        details['list_id'],
                        name=details['old_name'],
                        status=details['old_status']
                    )
                    return True

                elif action_type == 'ADD_ITEM':
                    # Undo adding an item by removing it
                    self.shopping_list_service.remove_item_from_list(
                        details['list_id'],
                        details['item_id']
                    )
                    return True

                elif action_type == 'REMOVE_ITEM':
                    # Undo removing an item by adding it back
                    for item in details.get('items', []):
                        self.shopping_list_service.add_item_to_list(
                            item['list_id'],
                            item['name'],
                            item['quantity'],
                            item['unit'],
                            item.get('notes', ''),
                            item.get('priority', 'MEDIUM')
                        )
                    return True

                elif action_type == 'UPDATE_ITEM':
                    # Undo item update by reverting to previous state
                    self.shopping_list_service.update_list_item(
                        details['item_id'],
                        name=details['old_name'],
                        quantity=details['old_quantity'],
                        unit=details['old_unit'],
                        notes=details.get('old_notes', ''),
                        priority=details.get('old_priority', 'MEDIUM')
                    )
                    return True

                elif action_type == 'SAVE_LIST':
                    # Save action typically doesn't need a specific undo
                    return True

                else:
                    logging.warning(f"Unsupported undo action type: {action_type}")
                    return False

            except Exception as e:
                logging.error(f"Error undoing action {action_type}: {e}")
                self.show_error("Undo Error", f"Could not undo action: {e}")
                return False

        def _redo_action(self, action: Dict[str, Any]) -> bool:
            """
            Redo a previously undone action.

            Args:
                action: Action to redo

            Returns:
                bool: Whether the redo was successful
            """
            action_type = action['type']
            details = action['details']

            try:
                if action_type == 'CREATE_LIST':
                    # Redo list creation
                    new_list = self.shopping_list_service.create_list(
                        details['name'],
                        details['status']
                    )
                    # Restore list items if applicable
                    if 'items' in details:
                        for item in details['items']:
                            self.shopping_list_service.add_item_to_list(
                                new_list.id,
                                item['name'],
                                item['quantity'],
                                item['unit'],
                                item.get('notes', ''),
                                item.get('priority', 'MEDIUM')
                            )
                    return True

                elif action_type == 'DELETE_LIST':
                    # Redo list deletion
                    self.shopping_list_service.delete_list(details['list_id'])
                    return True

                elif action_type == 'UPDATE_LIST':
                    # Redo list update
                    self.shopping_list_service.update_list(
                        details['list_id'],
                        name=details['new_name'],
                        status=details['new_status']
                    )
                    return True

                elif action_type == 'ADD_ITEM':
                    # Redo adding an item
                    self.shopping_list_service.add_item_to_list(
                        details['list_id'],
                        details['name'],
                        details['quantity'],
                        details['unit'],
                        details.get('notes', ''),
                        details.get('priority', 'MEDIUM')
                    )
                    return True

                elif action_type == 'REMOVE_ITEM':
                    # Redo removing an item
                    for item in details.get('items', []):
                        self.shopping_list_service.remove_item_from_list(
                            item['list_id'],
                            item['item_id']
                        )
                    return True

                elif action_type == 'UPDATE_ITEM':
                    # Redo item update
                    self.shopping_list_service.update_list_item(
                        details['item_id'],
                        name=details['new_name'],
                        quantity=details['new_quantity'],
                        unit=details['new_unit'],
                        notes=details.get('new_notes', ''),
                        priority=details.get('new_priority', 'MEDIUM')
                    )
                    return True

                elif action_type == 'SAVE_LIST':
                    # Save action typically doesn't need a specific redo
                    return True

                else:
                    logging.warning(f"Unsupported redo action type: {action_type}")
                    return False

            except Exception as e:
                logging.error(f"Error redoing action {action_type}: {e}")
                self.show_error("Redo Error", f"Could not redo action: {e}")
                return False

        def on_save(self):
            """
            Save changes to the current shopping list.
            Captures the current state for potential undo/redo.
            """
            if not self.current_list_id:
                self.show_info("Info", "No list selected to save")
                return

            try:
                # Capture current list state before potential changes
                current_list = self.shopping_list_service.get_list(self.current_list_id)

                # Record the save action for potential future undo
                self._record_action('SAVE_LIST', {
                    'list_id': self.current_list_id,
                    'name': current_list.name,
                    'status': current_list.status,
                    'timestamp': datetime.now()
                })

                self.show_info("Save", "Shopping list saved successfully")
            except Exception as e:
                self.show_error("Save Error", f"Could not save shopping list: {e}")
                logging.error(f"Error saving shopping list: {e}")

        def on_refresh(self):
            """
            Refresh the shopping lists view.
            """
            # Clear existing lists and items
            for tree in [self.lists_tree, self.items_tree]:
                for item in tree.get_children():
                    tree.delete(item)

            try:
                # Load shopping lists from service
                lists = self.shopping_list_service.get_all_lists()

                # Populate lists treeview
                for list_item in lists:
                    self.lists_tree.insert("", tk.END, values=(
                        list_item.id,
                        list_item.name,
                        list_item.created_at.strftime("%Y-%m-%d") if list_item.created_at else "",
                        list_item.status.name if hasattr(list_item, 'status') else ""
                    ))
            except Exception as e:
                self.show_error("Refresh Error", f"Could not refresh shopping lists: {e}")
                logging.error(f"Error refreshing shopping lists: {e}")

# Optional: Add a standalone entry point for testing the view
def main():
    """
    Standalone entry point for testing the ShoppingListView.
    """
    import tkinter as tk
    from di.container import DependencyContainer

    # Create root window
    root = tk.Tk()
    root.title("Shopping List View Test")
    root.geometry("800x600")

    # Create a mock dependency container
    di_container = DependencyContainer()

    # Create the view
    shopping_list_view = ShoppingListView(root, di_container)
    shopping_list_view.pack(fill=tk.BOTH, expand=True)

    # Start the main event loop
    root.mainloop()

if __name__ == "__main__":
    main()