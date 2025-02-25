# Relative path: store_management/utils/order_exporter.py

"""
Order Exporter Module

Provides functionality for exporting order data to various file formats
including Excel, CSV, and JSON.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

import pandas as pd

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService

# Configure logger
logger = logging.getLogger(__name__)


class OrderExporter:
    """
    Utility class for exporting order data to various file formats.

    This class provides static methods to export order data to Excel, CSV, and JSON formats.
    All methods return a boolean indicating success or failure of the export operation.
    """

    @staticmethod
    def export_to_excel(data: Dict[str, Any], filepath: Path) -> bool:
        """
        Export order data to Excel format with multiple sheets.

        Args:
            data (Dict[str, Any]): Dictionary containing order data with 'order' and 'details' keys
            filepath (Path): Path where the Excel file should be saved

        Returns:
            bool: True if export was successful, False otherwise

        Raises:
            ValueError: If data dictionary doesn't contain required keys
        """
        if 'order' not in data or 'details' not in data:
            logger.error("Export failed: Data missing required 'order' or 'details' keys")
            raise ValueError("Data must contain 'order' and 'details' keys")

        try:
            with pd.ExcelWriter(filepath) as writer:
                # Create and write order data sheet
                order_df = pd.DataFrame([data['order']])
                order_df.to_excel(writer, sheet_name='Order', index=False)

                # Create and write order details sheet
                details_df = pd.DataFrame(data['details'])
                details_df.to_excel(writer, sheet_name='Details', index=False)

                # Format the Excel file for better readability
                workbook = writer.book
                for sheet in writer.sheets.values():
                    for col in range(len(sheet.dimensions)):
                        sheet.column_dimensions[chr(65 + col)].auto_size = True

            logger.info(f"Successfully exported order data to Excel: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to export order data to Excel: {e}")
            return False

    @staticmethod
    def export_to_csv(data: Dict[str, Any], filepath: Path) -> bool:
        """
        Export order data to CSV format (creates two files: one for order and one for details).

        Args:
            data (Dict[str, Any]): Dictionary containing order data with 'order' and 'details' keys
            filepath (Path): Base path for the CSV files

        Returns:
            bool: True if export was successful, False otherwise

        Raises:
            ValueError: If data dictionary doesn't contain required keys
        """
        if 'order' not in data or 'details' not in data:
            logger.error("Export failed: Data missing required 'order' or 'details' keys")
            raise ValueError("Data must contain 'order' and 'details' keys")

        try:
            # Export main order data
            order_df = pd.DataFrame([data['order']])
            order_filepath = filepath.with_suffix('.order.csv')
            order_df.to_csv(order_filepath, index=False)

            # Export order details data
            details_df = pd.DataFrame(data['details'])
            details_filepath = filepath.with_suffix('.details.csv')
            details_df.to_csv(details_filepath, index=False)

            logger.info(f"Successfully exported order data to CSV files: {order_filepath} and {details_filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to export order data to CSV: {e}")
            return False

    @staticmethod
    def export_to_json(data: Dict[str, Any], filepath: Path) -> bool:
        """
        Export order data to JSON format.

        Args:
            data (Dict[str, Any]): Dictionary containing order data
            filepath (Path): Path where the JSON file should be saved

        Returns:
            bool: True if export was successful, False otherwise
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"Successfully exported order data to JSON: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to export order data to JSON: {e}")
            return False