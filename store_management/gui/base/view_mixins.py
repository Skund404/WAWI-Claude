"""
Mixins for view functionality.
Provides reusable behaviors that can be added to views.
"""
import logging
import csv
import tkinter as tk
from tkinter import ttk, filedialog
import os
import json
from typing import Any, Dict, List, Optional, Callable, Tuple

logger = logging.getLogger(__name__)


class SearchMixin:
    """
    Mixin providing search functionality for views.
    
    This mixin provides methods for adding and handling search fields
    and functionality in views.
    """
    
    def _setup_search(self, parent: tk.Widget, callback: Optional[Callable] = None):
        """
        Set up a search field with options.
        
        Args:
            parent: Parent widget for the search components
            callback: Optional callback for search execution
        
        Returns:
            ttk.Frame: The search frame
        """
        # Create search frame
        search_frame = ttk.Frame(parent)
        
        # Create search components
        search_label = ttk.Label(search_frame, text="Search:")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        
        # Add search button
        search_button = ttk.Button(
            search_frame, 
            text="Search",
            command=lambda: self._perform_search(callback) if callback else self._perform_search(self._internal_search)
        )
        
        # Add clear button
        clear_button = ttk.Button(
            search_frame, 
            text="Clear",
            command=self._clear_search
        )
        
        # Pack components
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        search_button.pack(side=tk.LEFT, padx=(0, 5))
        clear_button.pack(side=tk.LEFT)
        
        # Bind Enter key to search
        self.search_entry.bind("<Return>", 
                              lambda event: self._perform_search(callback) if callback else self._perform_search(self._internal_search))
        
        return search_frame
    
    def _perform_search(self, callback: Optional[Callable] = None):
        """
        Execute the search.
        
        Args:
            callback: Optional callback function for search execution
        """
        query = self.search_var.get().strip()
        if not query:
            # If search is empty, clear filters
            self._clear_search()
            return
        
        logger.debug(f"Performing search with query: {query}")
        
        try:
            if callback:
                results = callback(query)
            else:
                results = self._internal_search(query)
            
            if results is not None:
                # Update UI with search results
                self.set_status(f"Found {len(results)} results for '{query}'")
            else:
                self.set_status(f"Search executed for '{query}'")
        except Exception as e:
            logger.error(f"Error performing search: {e}")
            self.handle_error(e, f"Error searching for '{query}'")
    
    def _clear_search(self):
        """Clear the search and reset the view."""
        self.search_var.set("")
        self.set_status("Search cleared")
        
        # Refresh the view
        if hasattr(self, 'on_refresh'):
            self.on_refresh()
    
    def _internal_search(self, query: str) -> List[Any]:
        """
        Internal search implementation to be overridden by subclasses.
        
        Args:
            query: Search query string
            
        Returns:
            List of search results
        """
        logger.debug(f"Base internal search called with query: {query}")
        return []


class FilterMixin:
    """
    Mixin providing filtering functionality for views.
    
    This mixin provides methods for adding and handling filters
    in views.
    """
    
    def _setup_filters(self, parent: tk.Widget, filters: Dict[str, List[str]], 
                      callback: Optional[Callable] = None):
        """
        Set up filter fields with options.
        
        Args:
            parent: Parent widget for the filter components
            filters: Dictionary of filter names to lists of options
            callback: Optional callback for filter changes
        
        Returns:
            ttk.Frame: The filters frame
        """
        # Create filters frame
        filters_frame = ttk.Frame(parent)
        
        # Create filter components for each filter
        self.filter_vars = {}
        
        for i, (filter_name, options) in enumerate(filters.items()):
            # Create label and combobox
            filter_label = ttk.Label(filters_frame, text=f"{filter_name.replace('_', ' ').title()}:")
            filter_var = tk.StringVar()
            filter_var.set("All")  # Default value
            
            # Add "All" option to the beginning
            filter_options = ["All"] + options
            
            filter_combo = ttk.Combobox(
                filters_frame, 
                textvariable=filter_var,
                values=filter_options,
                state="readonly",
                width=15
            )
            
            # Store the variable for later access
            self.filter_vars[filter_name] = filter_var
            
            # Pack components
            filter_label.grid(row=0, column=i*2, padx=(10 if i > 0 else 0, 5), sticky=tk.W)
            filter_combo.grid(row=0, column=i*2 + 1, padx=(0, 10), sticky=tk.W)
            
            # Bind selection event
            filter_combo.bind("<<ComboboxSelected>>", 
                             lambda event, cb=callback: self._apply_filters(cb) if cb else self._apply_filters())
        
        # Add reset button at the end
        reset_button = ttk.Button(
            filters_frame, 
            text="Reset Filters",
            command=lambda: self._reset_filters(callback) if callback else self._reset_filters()
        )
        reset_button.grid(row=0, column=len(filters)*2, padx=(10, 0), sticky=tk.E)
        
        # Configure grid
        filters_frame.columnconfigure(len(filters)*2 + 1, weight=1)
        
        return filters_frame
    
    def _apply_filters(self, callback: Optional[Callable] = None):
        """
        Apply current filters.
        
        Args:
            callback: Optional callback function for filter application
        """
        # Collect current filter values
        filters = {}
        for filter_name, filter_var in self.filter_vars.items():
            value = filter_var.get()
            if value != "All":  # Only include non-default values
                filters[filter_name] = value
        
        logger.debug(f"Applying filters: {filters}")
        
        try:
            if callback:
                results = callback(filters)
            else:
                results = self._internal_apply_filters(filters)
            
            if results is not None:
                # Update UI with filtered results
                self.set_status(f"Applied {len(filters)} filters")
            else:
                self.set_status(f"Filters applied")
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            self.handle_error(e, "Error applying filters")
    
    def _reset_filters(self, callback: Optional[Callable] = None):
        """
        Reset all filters to default values.
        
        Args:
            callback: Optional callback for filter reset
        """
        # Reset all filter variables to "All"
        for filter_var in self.filter_vars.values():
            filter_var.set("All")
        
        logger.debug("Resetting all filters")
        
        # Reapply filters (which will effectively clear them)
        if callback:
            callback({})
        else:
            self._internal_apply_filters({})
        
        self.set_status("Filters reset")
        
        # Refresh the view
        if hasattr(self, 'on_refresh'):
            self.on_refresh()
    
    def _internal_apply_filters(self, filters: Dict[str, str]) -> Optional[List[Any]]:
        """
        Internal filter implementation to be overridden by subclasses.
        
        Args:
            filters: Dictionary of filter names to values
            
        Returns:
            Optionally, a list of filtered results
        """
        logger.debug(f"Base internal apply_filters called with: {filters}")
        return None
    
    def get_active_filters(self) -> Dict[str, str]:
        """
        Get the currently active filters.
        
        Returns:
            Dictionary of active filter names to values
        """
        filters = {}
        for filter_name, filter_var in self.filter_vars.items():
            value = filter_var.get()
            if value != "All":  # Only include non-default values
                filters[filter_name] = value
        return filters


class SortableMixin:
    """
    Mixin providing sorting functionality for treeviews.
    
    This mixin provides methods for adding sorting capabilities
    to treeview components.
    """
    
    def _setup_sorting(self, treeview: ttk.Treeview, 
                      columns: List[str], 
                      sort_keys: Optional[Dict[str, Callable]] = None):
        """
        Set up sorting for a treeview.
        
        Args:
            treeview: The treeview to make sortable
            columns: List of column IDs
            sort_keys: Optional dictionary mapping column IDs to key functions
        """
        self.treeview = treeview
        self.sort_columns = columns
        self.sort_keys = sort_keys or {}
        self.sort_reverse = False
        self.sort_column = None
        
        # Add click handlers to column headings
        for col in columns:
            treeview.heading(
                col, 
                command=lambda _col=col: self._sort_column(_col, self.sort_reverse)
            )
    
    def _sort_column(self, column: str, reverse: bool = False):
        """
        Sort the treeview by the specified column.
        
        Args:
            column: Column ID to sort by
            reverse: Whether to sort in reverse order
        """
        logger.debug(f"Sorting by column '{column}', reverse={reverse}")
        
        # Get all items in the treeview
        items = [(self.treeview.set(k, column), k) for k in self.treeview.get_children('')]
        
        # If we're sorting the same column again, reverse the sort order
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = reverse
        
        # Sort the items
        try:
            # Use a specific key function if provided
            if column in self.sort_keys:
                items.sort(key=lambda x: self.sort_keys[column](x[0]), reverse=self.sort_reverse)
            else:
                # Try to convert to number if possible, otherwise sort as string
                items.sort(
                    key=lambda x: self._convert_value(x[0]), 
                    reverse=self.sort_reverse
                )
        except Exception as e:
            logger.error(f"Error sorting column '{column}': {e}")
            # Fall back to string sort
            items.sort(key=lambda x: str(x[0]).lower(), reverse=self.sort_reverse)
        
        # Rearrange items in sorted positions
        for index, (_, item) in enumerate(items):
            self.treeview.move(item, '', index)
        
        # Update column headings
        for col in self.sort_columns:
            # Remove sorting indicator from all columns
            self.treeview.heading(col, text=self.treeview.heading(col, 'text').replace(' ↑', '').replace(' ↓', ''))
        
        # Add sorting indicator to the sorted column
        current_text = self.treeview.heading(column, 'text')
        new_text = f"{current_text} {'↓' if self.sort_reverse else '↑'}"
        self.treeview.heading(column, text=new_text)
    
    def _convert_value(self, value: str) -> Any:
        """
        Convert a value for sorting.
        
        Args:
            value: The value to convert
            
        Returns:
            Converted value appropriate for sorting
        """
        if value == '':
            return ''
        
        # Try to convert to numeric types
        try:
            # Try integer first
            return int(value)
        except (ValueError, TypeError):
            try:
                # Then try float
                return float(value)
            except (ValueError, TypeError):
                # If not numeric, return lowercase string for case-insensitive sort
                return str(value).lower()


class ExportMixin:
    """
    Mixin providing export functionality for views.
    
    This mixin provides methods for exporting data to various
    formats such as CSV, Excel, and JSON.
    """
    
    def _setup_export(self, parent: tk.Widget, data_callback: Callable[[], List[Dict[str, Any]]]):
        """
        Set up export functionality.
        
        Args:
            parent: Parent widget for the export button
            data_callback: Function that returns the data to export
            
        Returns:
            ttk.Button: The export button
        """
        # Create export button
        export_button = ttk.Button(
            parent,
            text="Export",
            command=lambda: self._show_export_dialog(data_callback)
        )
        
        return export_button
    
    def _show_export_dialog(self, data_callback: Callable[[], List[Dict[str, Any]]]):
        """
        Show the export dialog.
        
        Args:
            data_callback: Function that returns the data to export
        """
        # Create a top-level dialog
        dialog = tk.Toplevel(self)
        dialog.title("Export Data")
        dialog.geometry("300x200")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        dialog.bind("<Escape>", lambda event: dialog.destroy())
        
        # Create export options frame
        options_frame = ttk.Frame(dialog, padding=10)
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create format selection
        format_label = ttk.Label(options_frame, text="Export Format:")
        format_label.pack(anchor=tk.W, pady=(0, 5))
        
        format_var = tk.StringVar(value="csv")
        
        csv_radio = ttk.Radiobutton(
            options_frame,
            text="CSV",
            variable=format_var,
            value="csv"
        )
        csv_radio.pack(anchor=tk.W, padx=(20, 0))
        
        excel_radio = ttk.Radiobutton(
            options_frame,
            text="Excel (XLSX)",
            variable=format_var,
            value="xlsx"
        )
        excel_radio.pack(anchor=tk.W, padx=(20, 0))
        
        json_radio = ttk.Radiobutton(
            options_frame,
            text="JSON",
            variable=format_var,
            value="json"
        )
        json_radio.pack(anchor=tk.W, padx=(20, 0))
        
        # Create buttons frame
        buttons_frame = ttk.Frame(dialog, padding=(10, 10, 10, 10))
        buttons_frame.pack(fill=tk.X)
        
        # Create export and cancel buttons
        cancel_button = ttk.Button(
            buttons_frame,
            text="Cancel",
            command=dialog.destroy
        )
        cancel_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        export_button = ttk.Button(
            buttons_frame,
            text="Export",
            command=lambda: self._export_data(format_var.get(), data_callback, dialog)
        )
        export_button.pack(side=tk.RIGHT)
        
        # Center the dialog
        self._center_window(dialog)
    
    def _export_data(self, format_type: str, data_callback: Callable[[], List[Dict[str, Any]]], 
                    dialog: Optional[tk.Toplevel] = None):
        """
        Export data to the specified format.
        
        Args:
            format_type: The format type (csv, xlsx, json)
            data_callback: Function that returns the data to export
            dialog: Optional dialog to destroy after export
        """
        logger.debug(f"Exporting data to format: {format_type}")
        
        # Get the data to export
        try:
            data = data_callback()
            if not data:
                self.set_status("No data to export")
                return
        except Exception as e:
            logger.error(f"Error getting data for export: {e}")
            self.handle_error(e, "Error preparing data for export")
            return
        
        # Determine file extension and file type
        if format_type == "csv":
            file_types = [("CSV files", "*.csv"), ("All files", "*.*")]
            default_ext = ".csv"
        elif format_type == "xlsx":
            file_types = [("Excel files", "*.xlsx"), ("All files", "*.*")]
            default_ext = ".xlsx"
        elif format_type == "json":
            file_types = [("JSON files", "*.json"), ("All files", "*.*")]
            default_ext = ".json"
        else:
            logger.error(f"Unsupported export format: {format_type}")
            self.show_error("Export Error", f"Unsupported export format: {format_type}")
            return
        
        # Ask for the file location
        filename = filedialog.asksaveasfilename(
            defaultextension=default_ext,
            filetypes=file_types,
            title="Export Data"
        )
        
        if not filename:
            return  # User cancelled
        
        # Close the dialog if provided
        if dialog:
            dialog.destroy()
        
        # Export the data based on the format
        try:
            if format_type == "csv":
                self._export_to_csv(data, filename)
            elif format_type == "xlsx":
                self._export_to_xlsx(data, filename)
            elif format_type == "json":
                self._export_to_json(data, filename)
            
            self.set_status(f"Data exported to {filename}")
            self.show_info("Export Complete", f"Data has been exported to {filename}")
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            self.handle_error(e, "Error exporting data")
    
    def _export_to_csv(self, data: List[Dict[str, Any]], filepath: str):
        """
        Export data to a CSV file.
        
        Args:
            data: List of dictionaries containing the data
            filepath: Path to save the CSV file
        """
        if not data:
            return
        
        # Get fieldnames from the first item
        fieldnames = list(data[0].keys())
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    
    def _export_to_xlsx(self, data: List[Dict[str, Any]], filepath: str):
        """
        Export data to an Excel file.
        
        Args:
            data: List of dictionaries containing the data
            filepath: Path to save the Excel file
        """
        try:
            import pandas as pd
            
            # Convert data to DataFrame
            df = pd.DataFrame(data)
            
            # Write to Excel
            df.to_excel(filepath, index=False)
            
        except ImportError:
            logger.error("Pandas is required for Excel export")
            self.show_error("Export Error", 
                           "Pandas is required for Excel export. Please install it using pip.")
            raise
    
    def _export_to_json(self, data: List[Dict[str, Any]], filepath: str):
        """
        Export data to a JSON file.
        
        Args:
            data: List of dictionaries containing the data
            filepath: Path to save the JSON file
        """
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, default=str)
    
    def _center_window(self, window: tk.Toplevel):
        """
        Center a window on its parent.
        
        Args:
            window: The window to center
        """
        window.update_idletasks()
        
        # Get sizes and positions
        parent_width = self.winfo_width()
        parent_height = self.winfo_height()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        
        window_width = window.winfo_width()
        window_height = window.winfo_height()
        
        # Calculate position
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        # Ensure window is visible on screen
        x = max(0, min(x, window.winfo_screenwidth() - window_width))
        y = max(0, min(y, window.winfo_screenheight() - window_height))
        
        # Set position
        window.geometry(f"+{x}+{y}")


class UndoRedoMixin:
    """
    Mixin providing undo/redo functionality for views.
    
    This mixin provides enhanced undo/redo capabilities
    with support for transaction grouping and descriptions.
    """
    
    def __init__(self):
        """Initialize the undo/redo mixin."""
        # Initialize undo/redo stacks
        self._undo_stack = []
        self._redo_stack = []
        
        # Track current transaction
        self._current_transaction = None
        self._has_unsaved_changes = False
    
    def begin_transaction(self, description: str = "Unnamed transaction"):
        """
        Begin a new transaction for grouping multiple actions.
        
        Args:
            description: Description of the transaction
        """
        logger.debug(f"Beginning transaction: {description}")
        
        # End any existing transaction
        if self._current_transaction:
            self.end_transaction()
        
        # Create a new transaction
        self._current_transaction = {
            'description': description,
            'actions': []
        }
    
    def add_to_transaction(self, undo_action: Callable, redo_action: Callable):
        """
        Add an action to the current transaction.
        
        Args:
            undo_action: Function to undo the action
            redo_action: Function to redo the action
        """
        if not self._current_transaction:
            # If no transaction is active, create one
            self.begin_transaction()
        
        # Add the action to the current transaction
        self._current_transaction['actions'].append((undo_action, redo_action))
    
    def end_transaction(self):
        """
        End the current transaction and add it to the undo stack.
        """
        if not self._current_transaction:
            return
        
        # Only add the transaction if it has actions
        if self._current_transaction['actions']:
            logger.debug(f"Ending transaction with {len(self._current_transaction['actions'])} actions: "
                        f"{self._current_transaction['description']}")
            
            # Add to undo stack
            self._undo_stack.append(self._current_transaction)
            
            # Clear redo stack
            self._redo_stack.clear()
            
            # Mark changes as unsaved
            self._has_unsaved_changes = True
        else:
            logger.debug(f"Ending empty transaction: {self._current_transaction['description']}")
        
        # Clear current transaction
        self._current_transaction = None
    
    def add_undo_action(self, undo_action: Callable, redo_action: Callable, 
                       description: str = "Unnamed action"):
        """
        Add a standalone action to the undo stack.
        
        Args:
            undo_action: Function to undo the action
            redo_action: Function to redo the action
            description: Description of the action
        """
        logger.debug(f"Adding standalone action: {description}")
        
        # Create a transaction for this action
        transaction = {
            'description': description,
            'actions': [(undo_action, redo_action)]
        }
        
        # Add to undo stack
        self._undo_stack.append(transaction)
        
        # Clear redo stack
        self._redo_stack.clear()
        
        # Mark changes as unsaved
        self._has_unsaved_changes = True
    
    def undo(self, event=None):
        """
        Undo the last transaction.
        
        Args:
            event: Optional event that triggered the undo
        """
        if not self._undo_stack:
            logger.debug("Nothing to undo")
            self.set_status("Nothing to undo")
            return
        
        # Get the transaction to undo
        transaction = self._undo_stack.pop()
        logger.debug(f"Undoing transaction: {transaction['description']}")
        
        try:
            # Execute undo actions in reverse order
            for undo_action, redo_action in reversed(transaction['actions']):
                undo_action()
            
            # Add to redo stack
            self._redo_stack.append(transaction)
            
            # Update status
            self.set_status(f"Undid: {transaction['description']}")
        except Exception as e:
            logger.error(f"Error during undo: {e}")
            self.handle_error(e, "Error during undo")
            
            # Push the transaction back onto the undo stack
            self._undo_stack.append(transaction)
    
    def redo(self, event=None):
        """
        Redo the last undone transaction.
        
        Args:
            event: Optional event that triggered the redo
        """
        if not self._redo_stack:
            logger.debug("Nothing to redo")
            self.set_status("Nothing to redo")
            return
        
        # Get the transaction to redo
        transaction = self._redo_stack.pop()
        logger.debug(f"Redoing transaction: {transaction['description']}")
        
        try:
            # Execute redo actions in forward order
            for undo_action, redo_action in transaction['actions']:
                redo_action()
            
            # Add back to undo stack
            self._undo_stack.append(transaction)
            
            # Update status
            self.set_status(f"Redid: {transaction['description']}")
        except Exception as e:
            logger.error(f"Error during redo: {e}")
            self.handle_error(e, "Error during redo")
            
            # Push the transaction back onto the redo stack
            self._redo_stack.append(transaction)
    
    def clear_history(self):
        """Clear undo/redo history."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._current_transaction = None
        self._has_unsaved_changes = False


class ValidationMixin:
    """
    Mixin providing form validation functionality.
    
    This mixin provides methods for validating form inputs
    with various validation rules and error handling.
    """
    
    def __init__(self):
        """Initialize the validation mixin."""
        # Dictionary to store validation rules
        self._validation_rules = {}
        
        # Dictionary to store validation errors
        self._validation_errors = {}
        
        # Dictionary to store field widgets
        self._field_widgets = {}
    
    def add_validation_rule(self, field_name: str, validator: Callable[[Any], bool], 
                           error_message: str):
        """
        Add a validation rule for a field.
        
        Args:
            field_name: Name of the field to validate
            validator: Function that returns True if valid, False otherwise
            error_message: Error message to display if validation fails
        """
        if field_name not in self._validation_rules:
            self._validation_rules[field_name] = []
        
        self._validation_rules[field_name].append((validator, error_message))
    
    def register_field(self, field_name: str, widget: tk.Widget, 
                      value_getter: Optional[Callable[[], Any]] = None):
        """
        Register a field for validation.
        
        Args:
            field_name: Name of the field
            widget: The field widget
            value_getter: Optional function to get the field value
        """
        self._field_widgets[field_name] = (widget, value_getter)
    
    def validate_fields(self) -> bool:
        """
        Validate all registered fields.
        
        Returns:
            bool: True if all fields are valid, False otherwise
        """
        # Clear previous errors
        self._validation_errors = {}
        
        # Validate each field
        for field_name, (widget, value_getter) in self._field_widgets.items():
            # Skip if no validation rules for this field
            if field_name not in self._validation_rules:
                continue
            
            # Get the field value
            if value_getter:
                value = value_getter()
            elif hasattr(widget, 'get'):
                value = widget.get()
            elif hasattr(widget, 'var'):
                value = widget.var.get()
            else:
                logger.warning(f"Cannot get value for field: {field_name}")
                continue
            
            # Validate the field
            for validator, error_message in self._validation_rules[field_name]:
                try:
                    if not validator(value):
                        self._validation_errors[field_name] = error_message
                        self._highlight_field_error(widget)
                        break
                except Exception as e:
                    logger.error(f"Error validating field {field_name}: {e}")
                    self._validation_errors[field_name] = f"Validation error: {str(e)}"
                    self._highlight_field_error(widget)
                    break
        
        return not self._validation_errors
    
    def _highlight_field_error(self, widget: tk.Widget):
        """
        Highlight a field with an error.
        
        Args:
            widget: Field widget to highlight
        """
        # Implementation depends on the widget type
        try:
            if isinstance(widget, ttk.Entry) or isinstance(widget, ttk.Combobox):
                widget.state(['invalid'])
            elif isinstance(widget, tk.Entry) or isinstance(widget, tk.Text):
                widget.config(background="#ffebee")  # Light red
        except Exception as e:
            logger.error(f"Error highlighting field: {e}")
    
    def clear_validation_errors(self):
        """Clear validation errors and field highlighting."""
        self._validation_errors = {}
        
        # Clear field highlighting
        for field_name, (widget, _) in self._field_widgets.items():
            try:
                if isinstance(widget, ttk.Entry) or isinstance(widget, ttk.Combobox):
                    widget.state(['!invalid'])
                elif isinstance(widget, tk.Entry) or isinstance(widget, tk.Text):
                    widget.config(background="white")
            except Exception as e:
                logger.error(f"Error clearing field highlighting: {e}")
    
    def get_validation_errors(self) -> Dict[str, str]:
        """
        Get current validation errors.
        
        Returns:
            Dictionary of field names to error messages
        """
        return self._validation_errors
