# gui/base/view_mixins.py
"""
Mixins for view classes in the leatherworking application.
Provides reusable functionality for different types of views.
"""


class SearchMixin:
    """Mixin providing search functionality to views."""

    def setup_search(self, search_frame, callback):
        """Set up search functionality for the view."""
        self.search_frame = search_frame
        self.search_frame.set_callback(callback)

    def perform_search(self, search_term):
        """
        Perform a search with the given term.

        Args:
            search_term: The term to search for
        """
        # To be implemented by derived classes
        pass


class FilterMixin:
    """Mixin providing filter functionality to views."""

    def setup_filters(self, filter_frame, callback):
        """Set up filter functionality for the view."""
        self.filter_frame = filter_frame
        self.filter_frame.set_callback(callback)

    def apply_filters(self, filters):
        """
        Apply the given filters to the view.

        Args:
            filters: Dictionary of filters to apply
        """
        # To be implemented by derived classes
        pass


class PaginationMixin:
    """Mixin providing pagination functionality to views."""

    def setup_pagination(self, page_size=20):
        """
        Set up pagination with the given page size.

        Args:
            page_size: Number of items per page
        """
        self.page_size = page_size
        self.current_page = 1
        self.total_pages = 1

    def go_to_page(self, page_number):
        """
        Go to the specified page.

        Args:
            page_number: The page number to go to
        """
        if 1 <= page_number <= self.total_pages:
            self.current_page = page_number
            self.refresh_data()

    def next_page(self):
        """Go to the next page if available."""
        self.go_to_page(self.current_page + 1)

    def previous_page(self):
        """Go to the previous page if available."""
        self.go_to_page(self.current_page - 1)

    def refresh_data(self):
        """Refresh the data based on the current page."""
        # To be implemented by derived classes
        pass


# Add this class to gui/base/view_mixins.py

class SortableMixin:
    """Mixin providing sorting functionality to views."""

    def setup_sorting(self, sortable_columns, default_sort=None):
        """
        Set up sorting functionality for the view.

        Args:
            sortable_columns: List of column names that can be sorted
            default_sort: Default column to sort by, or None for no default sort
        """
        self.sortable_columns = sortable_columns
        self.current_sort_column = default_sort
        self.sort_ascending = True

    def sort_by(self, column_name):
        """
        Sort the data by the specified column.

        Args:
            column_name: The column name to sort by
        """
        if column_name not in self.sortable_columns:
            return

        # If sorting by the same column, toggle sort direction
        if self.current_sort_column == column_name:
            self.sort_ascending = not self.sort_ascending
        else:
            self.current_sort_column = column_name
            self.sort_ascending = True

        self.refresh_data()

    def get_sort_parameters(self):
        """
        Get the current sorting parameters.

        Returns:
            Tuple of (column_name, ascending) or (None, True) if no sorting
        """
        return (self.current_sort_column, self.sort_ascending)


class ExportMixin:
    """Mixin providing data export functionality to views."""

    def setup_export(self, exportable_columns=None):
        """
        Set up export functionality for the view.

        Args:
            exportable_columns: List of column names that can be exported,
                                or None to export all columns
        """
        self.exportable_columns = exportable_columns

    def export_data(self, file_path, format_type='csv'):
        """
        Export the current data to a file.

        Args:
            file_path: Path to save the exported file
            format_type: Format to export ('csv', 'excel', 'json', etc.)

        Returns:
            Boolean indicating success or failure
        """
        # Get the data to export
        data = self.get_data_for_export()

        if not data:
            return False

        try:
            if format_type.lower() == 'csv':
                self._export_to_csv(data, file_path)
            elif format_type.lower() == 'excel':
                self._export_to_excel(data, file_path)
            elif format_type.lower() == 'json':
                self._export_to_json(data, file_path)
            else:
                # Unsupported format
                return False

            return True
        except Exception as e:
            # Log the error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error exporting data: {str(e)}")
            return False

    def get_data_for_export(self):
        """
        Get the data to be exported.

        Returns:
            List of dictionaries representing the data
        """
        # To be implemented by derived classes
        return []

    def _export_to_csv(self, data, file_path):
        """Export data to CSV file."""
        import csv

        # Get field names
        if not data:
            return

        field_names = list(data[0].keys())

        # Filter fields if exportable_columns is set
        if self.exportable_columns:
            field_names = [f for f in field_names if f in self.exportable_columns]

        # Write CSV file
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=field_names)
            writer.writeheader()

            for row in data:
                # Filter the row to only include exportable columns
                if self.exportable_columns:
                    filtered_row = {k: v for k, v in row.items() if k in self.exportable_columns}
                    writer.writerow(filtered_row)
                else:
                    writer.writerow(row)

    def _export_to_excel(self, data, file_path):
        """Export data to Excel file."""
        try:
            import pandas as pd

            # Convert data to DataFrame
            df = pd.DataFrame(data)

            # Filter columns if needed
            if self.exportable_columns:
                df = df[[col for col in self.exportable_columns if col in df.columns]]

            # Export to Excel
            df.to_excel(file_path, index=False)
        except ImportError:
            # Pandas not available, fall back to CSV
            import os
            base_name = os.path.splitext(file_path)[0]
            self._export_to_csv(data, f"{base_name}.csv")

    def _export_to_json(self, data, file_path):
        """Export data to JSON file."""
        import json

        # Filter data if exportable_columns is set
        if self.exportable_columns:
            filtered_data = []
            for row in data:
                filtered_row = {k: v for k, v in row.items() if k in self.exportable_columns}
                filtered_data.append(filtered_row)
            data = filtered_data

        # Write JSON file
        with open(file_path, 'w') as jsonfile:
            json.dump(data, jsonfile, indent=4)


class UndoRedoMixin:
    """Mixin providing undo/redo functionality to views."""

    def setup_undo_redo(self, max_history=20):
        """
        Set up undo/redo functionality for the view.

        Args:
            max_history: Maximum number of actions to keep in history
        """
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = max_history

    def record_action(self, action_data, description=""):
        """
        Record an action for potential undo.

        Args:
            action_data: Data needed to undo/redo the action
            description: Human-readable description of the action
        """
        # Clear redo stack when a new action is recorded
        self.redo_stack = []

        # Create action record
        action = {
            "data": action_data,
            "description": description
        }

        # Add to undo stack
        self.undo_stack.append(action)

        # Trim stack if it exceeds max history
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

    def can_undo(self):
        """Check if undo operation is available."""
        return len(self.undo_stack) > 0

    def can_redo(self):
        """Check if redo operation is available."""
        return len(self.redo_stack) > 0

    def undo(self):
        """
        Perform undo operation.

        Returns:
            Boolean indicating success or failure
        """
        if not self.can_undo():
            return False

        # Pop the last action from undo stack
        action = self.undo_stack.pop()

        # Add to redo stack
        self.redo_stack.append(action)

        # Perform the undo operation
        success = self._execute_undo(action["data"])

        # If undo failed, restore stacks
        if not success:
            self.undo_stack.append(self.redo_stack.pop())

        return success

    def redo(self):
        """
        Perform redo operation.

        Returns:
            Boolean indicating success or failure
        """
        if not self.can_redo():
            return False

        # Pop the last action from redo stack
        action = self.redo_stack.pop()

        # Add to undo stack
        self.undo_stack.append(action)

        # Perform the redo operation
        success = self._execute_redo(action["data"])

        # If redo failed, restore stacks
        if not success:
            self.redo_stack.append(self.undo_stack.pop())

        return success

    def _execute_undo(self, action_data):
        """
        Execute the undo operation.

        Args:
            action_data: Data needed to perform the undo

        Returns:
            Boolean indicating success or failure
        """
        # To be implemented by derived classes
        return False

    def _execute_redo(self, action_data):
        """
        Execute the redo operation.

        Args:
            action_data: Data needed to perform the redo

        Returns:
            Boolean indicating success or failure
        """
        # To be implemented by derived classes
        return False

    def get_undo_description(self):
        """Get description of the action that would be undone."""
        if not self.can_undo():
            return ""
        return self.undo_stack[-1]["description"]

    def get_redo_description(self):
        """Get description of the action that would be redone."""
        if not self.can_redo():
            return ""
        return self.redo_stack[-1]["description"]


class ValidationMixin:
    """Mixin providing form validation functionality to views."""

    def setup_validation(self):
        """Set up validation for the view."""
        self.validation_errors = {}
        self.field_validators = {}

    def add_validator(self, field_name, validator_func, error_message):
        """
        Add a validator function for a field.

        Args:
            field_name: Name of the field to validate
            validator_func: Function that takes a value and returns True if valid
            error_message: Message to display if validation fails
        """
        if field_name not in self.field_validators:
            self.field_validators[field_name] = []

        self.field_validators[field_name].append({
            "func": validator_func,
            "message": error_message
        })

    def validate_field(self, field_name, value):
        """
        Validate a single field.

        Args:
            field_name: Name of the field to validate
            value: Value to validate

        Returns:
            Tuple of (valid, error_message)
        """
        # Clear previous errors for this field
        if field_name in self.validation_errors:
            del self.validation_errors[field_name]

        # If no validators for this field, it's valid
        if field_name not in self.field_validators:
            return True, ""

        # Run each validator
        for validator in self.field_validators[field_name]:
            try:
                is_valid = validator["func"](value)
                if not is_valid:
                    self.validation_errors[field_name] = validator["message"]
                    return False, validator["message"]
            except Exception as e:
                # If validator raises an exception, field is invalid
                error_message = f"Validation error: {str(e)}"
                self.validation_errors[field_name] = error_message
                return False, error_message

        # All validators passed
        return True, ""

    def validate_all(self, data_dict):
        """
        Validate all fields in the data dictionary.

        Args:
            data_dict: Dictionary of field values to validate

        Returns:
            Boolean indicating if all fields are valid
        """
        # Clear all previous errors
        self.validation_errors = {}

        # Check each field with validators
        all_valid = True

        for field_name, validators in self.field_validators.items():
            # Skip if field is not in data
            if field_name not in data_dict:
                continue

            # Get field value
            value = data_dict[field_name]

            # Validate field
            valid, _ = self.validate_field(field_name, value)

            if not valid:
                all_valid = False

        return all_valid

    def get_validation_error(self, field_name):
        """
        Get validation error message for a field.

        Args:
            field_name: Name of the field

        Returns:
            Error message or empty string if no error
        """
        return self.validation_errors.get(field_name, "")

    def has_errors(self):
        """Check if there are any validation errors."""
        return len(self.validation_errors) > 0

    def get_all_errors(self):
        """Get all validation errors."""
        return self.validation_errors

    # Common validators that can be used with add_validator

    @staticmethod
    def required_validator(value):
        """Validate that a value is not empty."""
        if value is None:
            return False
        if isinstance(value, str) and value.strip() == "":
            return False
        return True

    @staticmethod
    def min_length_validator(min_length):
        """Create a validator for minimum string length."""

        def validator(value):
            if not isinstance(value, str):
                return False
            return len(value.strip()) >= min_length

        return validator

    @staticmethod
    def max_length_validator(max_length):
        """Create a validator for maximum string length."""

        def validator(value):
            if not isinstance(value, str):
                return True  # Non-strings don't apply
            return len(value) <= max_length

        return validator

    @staticmethod
    def number_range_validator(min_val=None, max_val=None):
        """Create a validator for number range."""

        def validator(value):
            try:
                num_value = float(value)
                if min_val is not None and num_value < min_val:
                    return False
                if max_val is not None and num_value > max_val:
                    return False
                return True
            except (ValueError, TypeError):
                return False

        return validator

    @staticmethod
    def email_validator(value):
        """Validate email format."""
        import re
        if not isinstance(value, str):
            return False
        # Simple email pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, value) is not None