# relative path: store_management/services/implementations/hardware_service.py
"""
Hardware Service Implementation for the Leatherworking Store Management application.

Provides comprehensive functionality for managing hardware inventory.
"""

from typing import Any, List, Dict, Optional
import logging

from services.base_service import BaseService, ValidationError, NotFoundError
from services.interfaces.hardware_service import IHardwareService
from database.models.hardware import Hardware, HardwareType, HardwareMaterial, HardwareFinish
from database.repositories.hardware_repository import HardwareRepository
from database.sqlalchemy.session import get_db_session
from utils.error_handler import ApplicationError


class HardwareService(BaseService[Hardware], IHardwareService):
    """
    Service for managing hardware inventory in the leatherworking store.

    Provides methods for creating, retrieving, updating, and deleting
    hardware items used in leatherworking projects.
    """

    def __init__(self, hardware_repository: Optional[HardwareRepository] = None):
        """
        Initialize the hardware service.

        Args:
            hardware_repository (Optional[HardwareRepository], optional):
            Repository for hardware data access. If not provided, a new one will be created.
        """
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Use provided repository or create a new one
        self._repository = hardware_repository or HardwareRepository(get_db_session())

    def _validate_enum_input(self, enum_class, value: Any) -> Any:
        """
        Validate and convert enum input.

        Args:
            enum_class: Enum class to validate against
            value: Input value to validate

        Returns:
            Validated enum value

        Raises:
            ValidationError: If input cannot be converted to enum
        """
        if value is None:
            return None

        try:
            # If it's already an enum, return it
            if isinstance(value, enum_class):
                return value

            # Try converting string to enum
            if isinstance(value, str):
                try:
                    # First try exact match (enum name)
                    return enum_class[value.upper()]
                except KeyError:
                    # If exact match fails, try value-based matching
                    return enum_class(value)
        except (ValueError, KeyError) as e:
            raise ValidationError(f"Invalid {enum_class.__name__}: {value}") from e

    def _sanitize_hardware_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize and validate hardware data before creating or updating.

        Args:
            data (Dict[str, Any]): Raw hardware data

        Returns:
            Dict[str, Any]: Sanitized and validated hardware data
        """
        sanitized_data = {}

        # Validate and convert enum fields
        enum_fields = [
            ('hardware_type', HardwareType),
            ('material', HardwareMaterial),
            ('finish', HardwareFinish)
        ]

        for field, enum_class in enum_fields:
            if field in data:
                sanitized_data[field] = self._validate_enum_input(enum_class, data[field])

        # Numeric field validations
        numeric_fields = {
            'quantity': int,
            'price': float,
            'size': float,
            'minimum_stock_level': int
        }

        for field, converter in numeric_fields.items():
            if field in data:
                try:
                    value = converter(data[field])
                    if value < 0:
                        raise ValidationError(f"{field.replace('_', ' ').title()} cannot be negative")
                    sanitized_data[field] = value
                except ValueError:
                    raise ValidationError(f"Invalid {field.replace('_', ' ')}: {data[field]}")

        # String fields
        string_fields = [
            'name', 'description', 'supplier_id',
            'corrosion_resistance', 'load_capacity'
        ]
        for field in string_fields:
            if field in data:
                sanitized_data[field] = str(data[field]).strip() or None

        return sanitized_data

    def create_hardware(self, hardware_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new hardware item.

        Args:
            hardware_data: Hardware data dictionary

        Returns:
            Dict: Created hardware data
        """
        try:
            # Validate and sanitize input data
            sanitized_data = self._sanitize_hardware_data(hardware_data)

            # Ensure required fields are present
            required_fields = ['name', 'hardware_type', 'material', 'quantity', 'price']
            for field in required_fields:
                if field not in sanitized_data:
                    raise ValidationError(f"Missing required field: {field}")

            # Create hardware item
            hardware = self.create(sanitized_data)
            return self._convert_to_dict(hardware)
        except (ValidationError, ApplicationError) as e:
            self.logger.error(f"Error creating hardware: {e}")
            raise

    def update_hardware(self, hardware_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing hardware item.

        Args:
            hardware_id: ID of the hardware to update
            updates: Data to update

        Returns:
            Dict: Updated hardware data
        """
        try:
            # Validate and sanitize input data
            sanitized_updates = self._sanitize_hardware_data(updates)

            # Update hardware item
            hardware = self.update(hardware_id, sanitized_updates)
            return self._convert_to_dict(hardware)
        except (ValidationError, ApplicationError) as e:
            self.logger.error(f"Error updating hardware: {e}")
            raise

    def get_hardware_by_id(self, hardware_id: int) -> Optional[Dict[str, Any]]:
        """Get hardware item by ID.

        Args:
            hardware_id: ID of the hardware to retrieve

        Returns:
            Dict or None: Hardware data if found
        """
        try:
            hardware = self.get_by_id(hardware_id)
            return self._convert_to_dict(hardware)
        except NotFoundError:
            return None

    def get_all_hardware(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all hardware items with optional filtering.

        Args:
            filters: Optional filtering criteria

        Returns:
            List of hardware items as dictionaries
        """
        hardware_list = self.get_all(filters=filters)
        return [self._convert_to_dict(h) for h in hardware_list]

    def search_hardware(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search hardware items.

        Args:
            query: Search query string
            filters: Optional additional filtering criteria

        Returns:
            List of matching hardware items as dictionaries
        """
        try:
            # Prepare search filters
            search_filters = filters or {}
            search_filters['search_query'] = query

            # Perform search
            hardware_items = self.search(query, search_filters)
            return [self._convert_to_dict(item) for item in hardware_items]
        except Exception as e:
            self.logger.error(f"Error searching hardware items: {e}")
            return []

    def delete_hardware(self, hardware_id: int) -> bool:
        """Delete a hardware item.

        Args:
            hardware_id: ID of the hardware to delete

        Returns:
            bool: True if successful
        """
        return self.delete(hardware_id)

    def _convert_to_dict(self, hardware: Hardware) -> Dict[str, Any]:
        """Convert Hardware model to dictionary.

        Args:
            hardware: Hardware model instance

        Returns:
            Dict representation of the hardware
        """
        if not hardware:
            return None

        # Safely extract enum values
        def safe_enum_value(enum_val):
            return enum_val.value if enum_val is not None else None

        return {
            'id': hardware.id,
            'name': hardware.name,
            'description': getattr(hardware, 'description', ''),
            'type': safe_enum_value(getattr(hardware, 'hardware_type', None)),
            'material': safe_enum_value(getattr(hardware, 'material', None)),
            'finish': safe_enum_value(getattr(hardware, 'finish', None)),
            'quantity': getattr(hardware, 'quantity', 0),
            'unit_price': getattr(hardware, 'price', 0.0),
            'supplier_id': getattr(hardware, 'supplier_id', None),
            'created_at': getattr(hardware, 'created_at', None),
            'updated_at': getattr(hardware, 'updated_at', None),
            'size': getattr(hardware, 'size', None),
            'minimum_stock_level': getattr(hardware, 'minimum_stock_level', None),
            'corrosion_resistance': getattr(hardware, 'corrosion_resistance', None),
            'load_capacity': getattr(hardware, 'load_capacity', None)
        }

    def validate_data(
            self,
            data: Dict[str, Any],
            required_fields: Optional[List[str]] = None
    ) -> None:
        """
        Validate hardware item data with specific rules.

        Args:
            data (Dict[str, Any]): Data to validate
            required_fields (Optional[List[str]], optional): List of required fields

        Raises:
            ValidationError: If validation fails
        """
        # Call parent validation method
        super().validate_data(data, required_fields)

        # Additional hardware-specific validations
        if 'quantity' in data:
            try:
                quantity = float(data['quantity'])
                if quantity < 0:
                    raise ValidationError("Quantity cannot be negative")
            except ValueError:
                raise ValidationError("Quantity must be a valid number")

        if 'unit_price' in data:
            try:
                unit_price = float(data['unit_price'])
                if unit_price < 0:
                    raise ValidationError("Unit price cannot be negative")
            except ValueError:
                raise ValidationError("Unit price must be a valid number")
