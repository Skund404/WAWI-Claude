# utils/validators/order_validator.py
"""
Validators for sale-related data.
"""
import json
import logging
from typing import Any, Dict, List

import pandas as pd
from pathlib import Path

from .data_sanitizer import DataSanitizer


class OrderValidator:
    """
    Utility class for validating and processing sale-related data.
    """

    @classmethod
    def validate_order_data(cls, order_data: Dict[str, Any]) -> bool:
        """
        Validate sale data against a set of predefined rules.

        Args:
            order_data (Dict[str, Any]): Order data to validate

        Returns:
            bool: True if sale data is valid, False otherwise
        """
        # Sanitize input data first
        sanitized_data = DataSanitizer.sanitize_dict(order_data)

        # Validate required fields
        required_fields = ['customer_name', 'total_amount', 'order_date']
        for field in required_fields:
            if not sanitized_data.get(field):
                logging.warning(f"Missing required field: {field}")
                return False

        # Additional specific validations
        try:
            # Validate total amount is positive
            if sanitized_data.get('total_amount', 0) <= 0:
                logging.warning("Total amount must be positive")
                return False

            # Validate customer name length
            if len(sanitized_data.get('customer_name', '')) < 2:
                logging.warning("Customer name too short")
                return False

            return True
        except Exception as e:
            logging.error(f"Order validation error: {str(e)}")
            return False

    @classmethod
    def import_orders_from_csv(cls, filepath: str) -> List[Dict[str, Any]]:
        """
        Import and validate orders from a CSV file.

        Args:
            filepath (str): Path to the CSV file

        Returns:
            List[Dict[str, Any]]: List of validated orders
        """
        try:
            # Read CSV file
            df = pd.read_csv(filepath)

            # Validate and convert to list of dictionaries
            valid_orders = []
            for _, row in df.iterrows():
                order_data = row.to_dict()

                # Sanitize and validate each sale
                if cls.validate_order_data(order_data):
                    valid_orders.append(order_data)
                else:
                    logging.warning(f"Skipping invalid sale: {order_data}")

            return valid_orders

        except Exception as e:
            logging.error(f"Error importing orders: {str(e)}")
            return []

    @classmethod
    def export_orders_to_json(cls, orders: List[Dict[str, Any]], filepath: str) -> bool:
        """
        Export validated orders to a JSON file.

        Args:
            orders (List[Dict[str, Any]]): List of orders to export
            filepath (str): Path to save the JSON file

        Returns:
            bool: True if export was successful, False otherwise
        """
        try:
            # Validate each sale before export
            valid_orders = [
                order for order in orders
                if cls.validate_order_data(order)
            ]

            # Write to JSON file
            with open(filepath, 'w') as f:
                json.dump(valid_orders, f, indent=4)

            return True
        except Exception as e:
            logging.error(f"Error exporting orders: {str(e)}")
            return False