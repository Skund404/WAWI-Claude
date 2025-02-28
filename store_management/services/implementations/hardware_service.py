# services/implementations/hardware_service.py
"""
Hardware service implementation for managing hardware inventory.
"""
import logging
from typing import Any, Dict, List, Optional

from database.models.hardware import Hardware, HardwareFinish, HardwareMaterial, HardwareType
from database.repositories.hardware_repository import HardwareRepository
from database.sqlalchemy.session import get_db_session
from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.hardware_service import IHardwareService
from utils.circular_import_resolver import lazy_import, resolve_lazy_import
from utils.error_handler import ApplicationError


class HardwareService(BaseService[Hardware], IHardwareService):
    """Service for managing hardware inventory in the leatherworking store.

    Provides methods for creating, retrieving, updating, and deleting
    hardware items used in leatherworking projects.
    """

    def __init__(self, hardware_repository: Optional[HardwareRepository] = None):
        """Initialize the hardware service.

        Args:
            hardware_repository (Optional[HardwareRepository], optional):
            Repository for hardware data access. If not provided, a new one will be created.
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)

        if hardware_repository is None:
            session = get_db_session()
            hardware_repository = HardwareRepository(session)

        self.repository = hardware_repository

    def create_hardware(self, hardware_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new hardware item.

        Args:
            hardware_data: Dictionary with hardware data

        Returns:
            Dict[str, Any]: Created hardware item data

        Raises:
            ValidationError: If hardware data is invalid
        """
        self.logger.info("Creating new hardware item")

        # Validate required fields
        required_fields = ['name', 'type', 'material', 'finish', 'quantity']
        for field in required_fields:
            if field not in hardware_data:
                raise ValidationError(f"Missing required field: {field}")

        try:
            # Convert enum strings to enum values
            if isinstance(hardware_data.get('type'), str):
                hardware_data['type'] = HardwareType[hardware_data['type']]

            if isinstance(hardware_data.get('material'), str):
                hardware_data['material'] = HardwareMaterial[hardware_data['material']]

            if isinstance(hardware_data.get('finish'), str):
                hardware_data['finish'] = HardwareFinish[hardware_data['finish']]

            # Create hardware in repository
            hardware = self.repository.create(hardware_data)

            return self._convert_to_dict(hardware)
        except (KeyError, ValueError) as e:
            self.logger.error(f"Failed to create hardware: {str(e)}")
            raise ValidationError(f"Invalid hardware data: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error creating hardware: {str(e)}")
            raise ApplicationError(f"Failed to create hardware: {str(e)}")

    def update_hardware(self, hardware_id: int, hardware_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing hardware item.

        Args:
            hardware_id: ID of the hardware to update
            hardware_data: Dictionary with updated hardware data

        Returns:
            Dict[str, Any]: Updated hardware item data

        Raises:
            NotFoundError: If hardware with given ID doesn't exist
            ValidationError: If hardware data is invalid
        """
        self.logger.info(f"Updating hardware item with ID {hardware_id}")

        # Check if hardware exists
        hardware = self.repository.get_by_id(hardware_id)
        if not hardware:
            raise NotFoundError(f"Hardware with ID {hardware_id} not found")

        try:
            # Convert enum strings to enum values if present
            if 'type' in hardware_data and isinstance(hardware_data['type'], str):
                hardware_data['type'] = HardwareType[hardware_data['type']]

            if 'material' in hardware_data and isinstance(hardware_data['material'], str):
                hardware_data['material'] = HardwareMaterial[hardware_data['material']]

            if 'finish' in hardware_data and isinstance(hardware_data['finish'], str):
                hardware_data['finish'] = HardwareFinish[hardware_data['finish']]

            # Update hardware in repository
            hardware = self.repository.update(hardware_id, hardware_data)

            return self._convert_to_dict(hardware)
        except (KeyError, ValueError) as e:
            self.logger.error(f"Failed to update hardware: {str(e)}")
            raise ValidationError(f"Invalid hardware data: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error updating hardware: {str(e)}")
            raise ApplicationError(f"Failed to update hardware: {str(e)}")

    def get_hardware_by_id(self, hardware_id: int) -> Dict[str, Any]:
        """Get a hardware item by ID.

        Args:
            hardware_id: ID of the hardware to retrieve

        Returns:
            Dict[str, Any]: Hardware item data

        Raises:
            NotFoundError: If hardware with given ID doesn't exist
        """
        self.logger.info(f"Getting hardware item with ID {hardware_id}")

        hardware = self.repository.get_by_id(hardware_id)
        if not hardware:
            raise NotFoundError(f"Hardware with ID {hardware_id} not found")

        return self._convert_to_dict(hardware)

    def get_all_hardware(self, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """Get all hardware items.

        Args:
            include_deleted: Whether to include deleted hardware items

        Returns:
            List[Dict[str, Any]]: List of hardware items
        """
        self.logger.info("Getting all hardware items")

        hardware_list = self.repository.get_all(include_deleted=include_deleted)

        return [self._convert_to_dict(h) for h in hardware_list]

    def search_hardware(self, search_term: str, **filters) -> List[Dict[str, Any]]:
        """Search for hardware items.

        Args:
            search_term: Term to search for
            **filters: Additional filters

        Returns:
            List[Dict[str, Any]]: List of matching hardware items
        """
        self.logger.info(f"Searching hardware items with term '{search_term}'")

        # Convert enum filter strings to enum values
        for key, value in filters.items():
            if key == 'type' and isinstance(value, str):
                try:
                    filters[key] = HardwareType[value]
                except KeyError:
                    # Skip invalid filter
                    del filters[key]
            elif key == 'material' and isinstance(value, str):
                try:
                    filters[key] = HardwareMaterial[value]
                except KeyError:
                    # Skip invalid filter
                    del filters[key]
            elif key == 'finish' and isinstance(value, str):
                try:
                    filters[key] = HardwareFinish[value]
                except KeyError:
                    # Skip invalid filter
                    del filters[key]

        hardware_list = self.repository.search(search_term, **filters)

        return [self._convert_to_dict(h) for h in hardware_list]

    def delete_hardware(self, hardware_id: int, hard_delete: bool = False) -> bool:
        """Delete a hardware item.

        Args:
            hardware_id: ID of the hardware to delete
            hard_delete: Whether to permanently delete the item

        Returns:
            bool: True if successful

        Raises:
            NotFoundError: If hardware with given ID doesn't exist
        """
        self.logger.info(f"Deleting hardware item with ID {hardware_id}")

        # Check if hardware exists
        hardware = self.repository.get_by_id(hardware_id)
        if not hardware:
            raise NotFoundError(f"Hardware with ID {hardware_id} not found")

        success = self.repository.delete(hardware_id, hard_delete=hard_delete)

        return success

    def _convert_to_dict(self, hardware: Hardware) -> Dict[str, Any]:
        """Convert Hardware model to dictionary.

        Args:
            hardware: Hardware model instance

        Returns:
            Dict[str, Any]: Dictionary representation of hardware
        """

        # Safely handle enum values
        def safe_enum_value(enum_obj):
            if enum_obj is None:
                return None
            return enum_obj.name

        return {
            'id': hardware.id,
            'name': hardware.name,
            'type': safe_enum_value(hardware.type),
            'material': safe_enum_value(hardware.material),
            'finish': safe_enum_value(hardware.finish),
            'description': hardware.description,
            'quantity': hardware.quantity,
            'unit_price': hardware.unit_price,
            'supplier_id': hardware.supplier_id,
            'dimensions': hardware.dimensions,
            'weight': hardware.weight,
            'reorder_point': hardware.reorder_point,
            'reorder_quantity': hardware.reorder_quantity,
            'notes': hardware.notes,
            'created_at': hardware.created_at,
            'updated_at': hardware.updated_at,
            'is_deleted': hardware.is_deleted if hasattr(hardware, 'is_deleted') else False
        }

    @staticmethod
    def safe_enum_value(enum_val):
        """Helper method to safely convert enum to string.

        Args:
            enum_val: Enum value or None

        Returns:
            str or None: String representation of enum or None
        """
        if enum_val is None:
            return None
        return enum_val.name