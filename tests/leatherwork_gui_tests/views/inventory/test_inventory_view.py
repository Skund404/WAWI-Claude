# tests/leatherwork_gui_tests/views/inventory/test_inventory_view.py
"""
Unit tests for the InventoryView class in the Leatherworking ERP.
"""

import unittest
import tkinter as tk
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    '..', '..', '..', '..', 'store_management'
))
sys.path.insert(0, project_root)

# Now import the required classes
from gui.views.inventory.inventory_view import InventoryView
from gui.utils.navigation_service import NavigationService
from gui.utils.error_manager import ErrorManager
from database.models.enums import InventoryStatus, StorageLocationType


class TestInventoryView(unittest.TestCase):
    """
    Test suite for the InventoryView class.
    Covers various view functionalities and interactions.
    """

    def setUp(self):
        """
        Set up the test environment before each test method.
        Creates a root Tkinter window and initializes the InventoryView.
        """
        # Create a root window
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window

        # Create the InventoryView instance
        self.view = InventoryView(self.root)

    def tearDown(self):
        """
        Clean up the test environment after each test method.
        Destroys the root window and the view.
        """
        # Destroy the view and root window
        self.view.destroy()
        self.root.destroy()

    def test_init(self):
        """
        Test the initialization of the InventoryView.
        Verifies basic attributes and configuration.
        """
        # Check basic attributes
        self.assertEqual(self.view.title, "Inventory Management")
        self.assertEqual(self.view.service_name, "IInventoryService")

        # Verify columns configuration
        expected_columns = [
            ("id", "ID", 60),
            ("item_type", "Type", 100),
            ("item_name", "Item", 200),
            ("item_specifics", "Details", 150),
            ("storage_location", "Location", 150),
            ("quantity", "Quantity", 80),
            ("status", "Status", 100),
            ("last_updated", "Last Updated", 150),
            ("last_transaction", "Last Transaction", 150)
        ]
        self.assertEqual(self.view.columns, expected_columns)

        # Verify search fields
        self.assertEqual(len(self.view.search_fields), 4)
        search_field_names = [field['name'] for field in self.view.search_fields]
        self.assertListEqual(
            search_field_names,
            ['item_name', 'item_type', 'status', 'storage_location']
        )

    @patch('gui.utils.error_manager.ErrorManager.handle_exception')
    def test_get_search_params_error_handling(self, mock_handle_exception):
        """
        Test error handling in get_search_params method.
        Ensures exceptions are handled gracefully.
        """
        # Create a mock search frame that raises an exception
        mock_search_frame = Mock()
        mock_search_frame.get_search_criteria.side_effect = Exception("Test error")

        # Temporarily set a mock search frame
        self.view.search_frame = mock_search_frame

        # Call the method
        result = self.view.get_search_params()

        # Verify exception is handled and an empty dict is returned
        self.assertEqual(result, {})
        mock_handle_exception.assert_called_once()

    @patch('gui.utils.navigation_service.NavigationService.navigate_to_view')
    def test_open_storage_view(self, mock_navigate):
        """
        Test opening the storage view through NavigationService.
        """
        # Call the method
        self.view.open_storage_view()

        # Verify navigation service was called with correct parameters
        mock_navigate.assert_called_once_with(self.view, "storage")

    @patch('gui.utils.error_manager.ErrorManager.handle_exception')
    @patch('gui.utils.navigation_service.NavigationService.navigate_to_view')
    def test_open_storage_view_error_handling(self, mock_navigate, mock_handle_exception):
        """
        Test error handling when opening storage view fails.
        """
        # Make navigation service raise an exception
        mock_navigate.side_effect = Exception("Navigation error")

        # Call the method
        self.view.open_storage_view()

        # Verify exception is handled
        mock_handle_exception.assert_called_once()

    @patch('gui.utils.navigation_service.NavigationService.navigate_to_view')
    def test_view_transactions(self, mock_navigate):
        """
        Test viewing inventory transactions.
        """
        # Set a selected item
        self.view.selected_item = "123"

        # Call the method
        self.view.view_transactions()

        # Verify navigation service was called with correct parameters
        mock_navigate.assert_called_once_with(
            self.view,
            "inventory_transactions",
            {
                "inventory_id": 123,
                "title": "Transactions for Inventory #123"
            }
        )

    @patch('gui.utils.error_manager.ErrorManager.show_validation_error')
    def test_view_transactions_no_selection(self, mock_show_validation):
        """
        Test behavior when no item is selected for viewing transactions.
        """
        # Clear selected item
        self.view.selected_item = None

        # Call the method
        self.view.view_transactions()

        # No navigation should occur
        # Verify no validation error is shown
        mock_show_validation.assert_not_called()

    @patch('gui.utils.navigation_service.NavigationService.navigate_to_entity_details')
    def test_on_view(self, mock_navigate):
        """
        Test viewing inventory item details.
        """
        # Set a selected item
        self.view.selected_item = "456"

        # Call the method
        self.view.on_view()

        # Verify navigation service was called with correct parameters
        mock_navigate.assert_called_once_with(
            self.view,
            "inventory",
            456,
            readonly=True
        )

    def test_add_inventory_actions(self):
        """
        Test adding inventory-specific action buttons.
        """
        # Create a mock parent widget
        parent = Mock()

        # Call the method
        self.view.add_inventory_actions(parent)

        # Verify buttons were created and packed
        self.assertIsNotNone(parent.method_calls)

        # Check button texts in method calls
        button_texts = [
            call[1][0].cget('text')
            for call in parent.method_calls
            if hasattr(call[1][0], 'cget')
        ]
        expected_texts = ["Storage Locations", "Inventory Check", "Generate Report"]
        for text in expected_texts:
            self.assertIn(text, button_texts)

    def test_on_select(self):
        """
        Test item selection handling.
        """
        # Create mock buttons
        mock_btn_adjust = Mock()
        mock_btn_transactions = Mock()
        mock_btn_move = Mock()

        # Assign mock buttons
        self.view.btn_adjust = mock_btn_adjust
        self.view.btn_transactions = mock_btn_transactions
        self.view.btn_move = mock_btn_move

        # Test with an item selected
        self.view.selected_item = "789"
        self.view.on_select()

        # Verify buttons are enabled
        mock_btn_adjust.config.assert_called_with(state=tk.NORMAL)
        mock_btn_transactions.config.assert_called_with(state=tk.NORMAL)
        mock_btn_move.config.assert_called_with(state=tk.NORMAL)

        # Test with no item selected
        self.view.selected_item = None
        self.view.on_select()

        # Verify buttons are disabled
        mock_btn_adjust.config.assert_called_with(state=tk.DISABLED)
        mock_btn_transactions.config.assert_called_with(state=tk.DISABLED)
        mock_btn_move.config.assert_called_with(state=tk.DISABLED)

    @patch('gui.utils.error_manager.ErrorManager.show_validation_error')
    def test_move_location_validation(self, mock_show_validation):
        """
        Test location move validation.
        """
        # Clear selected item
        self.view.selected_item = None

        # Call move location method
        self.view.move_location()

        # Verify validation error is shown
        mock_show_validation.assert_called_once_with("Please select an inventory item to move.")


if __name__ == '__main__':
    unittest.main()