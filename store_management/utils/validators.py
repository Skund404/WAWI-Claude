from typing import Dict, Any, Tuple, Optional
from datetime import datetime
import re


class OrderValidator:
    """Validator for order-related data"""

    @staticmethod
    def validate_order(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate order data"""
        required_fields = ['supplier', 'order_number', 'date_of_order', 'status']

        # Check required fields
        for field in required_fields:
            if not data.get(field):
                return False, f"{field.replace('_', ' ').title()} is required"

        # Validate date format
        try:
            datetime.strptime(data['date_of_order'], '%Y-%m-%d')
        except ValueError:
            return False, "Invalid date format. Use YYYY-MM-DD"

        # Validate status
        valid_statuses = [
            'ordered', 'being processed', 'shipped',
            'received', 'returned', 'partially returned', 'completed'
        ]
        if data['status'] not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"

        # Validate payment status
        if data.get('payed') and data['payed'] not in ['yes', 'no']:
            return False, "Payment status must be 'yes' or 'no'"

        return True, None

    @staticmethod
    def validate_order_details(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate order details data"""
        required_fields = ['article', 'price', 'amount']

        # Check required fields
        for field in required_fields:
            if field not in data:
                return False, f"{field.replace('_', ' ').title()} is required"

        # Validate numeric fields
        try:
            price = float(data['price'])
            if price < 0:
                return False, "Price must be non-negative"
        except ValueError:
            return False, "Price must be a number"

        try:
            amount = int(data['amount'])
            if amount <= 0:
                return False, "Amount must be positive"
        except ValueError:
            return False, "Amount must be a whole number"

        return True, None


class DataSanitizer:
    """Sanitizer for input data"""

    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize string input"""
        # Remove any potentially dangerous characters
        return re.sub(r'[<>"\'/\\]', '', value.strip())

    @staticmethod
    def sanitize_numeric(value: str) -> str:
        """Sanitize numeric input"""
        return re.sub(r'[^0-9.-]', '', value)

    @staticmethod
    def sanitize_identifier(value: str) -> str:
        """Sanitize database identifiers"""
        return re.sub(r'[^a-zA-Z0-9_]', '_', value)

    @staticmethod
    def sanitize_order_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize order data"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                if key in ['price', 'amount', 'total']:
                    sanitized[key] = DataSanitizer.sanitize_numeric(value)
                else:
                    sanitized[key] = DataSanitizer.sanitize_string(value)
            else:
                sanitized[key] = value
        return sanitized