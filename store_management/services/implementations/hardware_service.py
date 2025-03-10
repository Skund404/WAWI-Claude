from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from database.repositories.hardware_repository import HardwareRepository
from database.repositories.supplier_repository import SupplierRepository
from database.repositories.inventory_repository import InventoryRepository
from database.repositories.material_repository import MaterialRepository

from database.models.enums import HardwareType, HardwareMaterial, HardwareFinish, InventoryStatus, TransactionType

from services.base_service import BaseService
from services.implementations.material_service import MaterialService
from services.exceptions import ValidationError, NotFoundError
from services.dto.material_dto import HardwareDTO

from di.inject import inject


class HardwareService(MaterialService):
    """Implementation of the hardware service interface."""

    @inject
    def __init__(self, session: Session,
                 hardware_repository: Optional[HardwareRepository] = None,
                 material_repository: Optional[MaterialRepository] = None,
                 supplier_repository: Optional[SupplierRepository] = None,
                 inventory_repository: Optional[InventoryRepository] = None):
        """Initialize the hardware service."""
        super().__init__(session)
        self.hardware_repository = hardware_repository or HardwareRepository(session)
        self.material_repository = material_repository or MaterialRepository(session)
        self.supplier_repository = supplier_repository or SupplierRepository(session)
        self.inventory_repository = inventory_repository or InventoryRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, hardware_id: int) -> Dict[str, Any]:
        """Get hardware by ID."""
        try:
            hardware = self.hardware_repository.get_by_id(hardware_id)
            if not hardware:
                raise NotFoundError(f"Hardware with ID {hardware_id} not found")
            return HardwareDTO.from_model(hardware, include_inventory=True, include_supplier=True).to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving hardware {hardware_id}: {str(e)}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all hardware materials, optionally filtered."""
        try:
            # Ensure only hardware materials are returned
            if not filters:
                filters = {}
            filters['material_type'] = 'HARDWARE'

            hardware_items = self.hardware_repository.get_all(filters=filters)
            return [HardwareDTO.from_model(hardware).to_dict() for hardware in hardware_items]
        except Exception as e:
            self.logger.error(f"Error retrieving hardware materials: {str(e)}")
            raise

    def create(self, hardware_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new hardware material."""
        try:
            # Validate hardware data
            self._validate_hardware_data(hardware_data)

            # Set material type to HARDWARE
            hardware_data['material_type'] = 'HARDWARE'

            # Create hardware material
            with self.transaction():
                hardware = self.hardware_repository.create(hardware_data)

                # Create inventory entry if not exists
                inventory_data = {
                    'item_type': 'material',
                    'item_id': hardware.id,
                    'quantity': hardware_data.get('initial_quantity', 0),
                    'status': InventoryStatus.IN_STOCK.value if hardware_data.get('initial_quantity',
                                                                                  0) > 0 else InventoryStatus.OUT_OF_STOCK.value,
                    'storage_location': hardware_data.get('storage_location', '')
                }
                self.inventory_repository.create(inventory_data)

                return HardwareDTO.from_model(hardware, include_inventory=True, include_supplier=True).to_dict()
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creating hardware material: {str(e)}")
            raise

    def update(self, hardware_id: int, hardware_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing hardware material."""
        try:
            # Check if hardware exists
            hardware = self.hardware_repository.get_by_id(hardware_id)
            if not hardware:
                raise NotFoundError(f"Hardware with ID {hardware_id} not found")

            # Validate hardware data
            self._validate_hardware_data(hardware_data, update=True)

            # Update hardware
            with self.transaction():
                updated_hardware = self.hardware_repository.update(hardware_id, hardware_data)
                return HardwareDTO.from_model(updated_hardware, include_inventory=True, include_supplier=True).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating hardware {hardware_id}: {str(e)}")
            raise

    def get_by_type(self, hardware_type: str) -> List[Dict[str, Any]]:
        """Get hardware materials by type."""
        try:
            # Validate hardware type
            if not hasattr(HardwareType, hardware_type):
                raise ValidationError(f"Invalid hardware type: {hardware_type}")

            hardware_items = self.hardware_repository.get_by_hardware_type(hardware_type)
            return [HardwareDTO.from_model(hardware).to_dict() for hardware in hardware_items]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving hardware materials by type '{hardware_type}': {str(e)}")
            raise

    def get_by_material(self, hardware_material: str) -> List[Dict[str, Any]]:
        """Get hardware by material type (brass, steel, etc.)."""
        try:
            # Validate hardware material
            if not hasattr(HardwareMaterial, hardware_material):
                raise ValidationError(f"Invalid hardware material: {hardware_material}")

            hardware_items = self.hardware_repository.get_by_hardware_material(hardware_material)
            return [HardwareDTO.from_model(hardware).to_dict() for hardware in hardware_items]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving hardware by material '{hardware_material}': {str(e)}")
            raise

    def get_by_finish(self, finish: str) -> List[Dict[str, Any]]:
        """Get hardware by finish type."""
        try:
            # Validate hardware finish
            if not hasattr(HardwareFinish, finish):
                raise ValidationError(f"Invalid hardware finish: {finish}")

            hardware_items = self.hardware_repository.get_by_finish(finish)
            return [HardwareDTO.from_model(hardware).to_dict() for hardware in hardware_items]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving hardware by finish '{finish}': {str(e)}")
            raise

    def _validate_hardware_data(self, hardware_data: Dict[str, Any], update: bool = False) -> None:
        """Validate hardware data.

        Args:
            hardware_data: Hardware data to validate
            update: Whether this is for an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Call parent validator for basic material validation
        self._validate_material_data(hardware_data, update)

        # Validate hardware-specific fields
        if 'hardware_type' in hardware_data and hardware_data['hardware_type']:
            hardware_type = hardware_data['hardware_type']
            if not hasattr(HardwareType, hardware_type):
                raise ValidationError(f"Invalid hardware type: {hardware_type}")

        if 'hardware_material' in hardware_data and hardware_data['hardware_material']:
            hardware_material = hardware_data['hardware_material']
            if not hasattr(HardwareMaterial, hardware_material):
                raise ValidationError(f"Invalid hardware material: {hardware_material}")

        if 'finish' in hardware_data and hardware_data['finish']:
            finish = hardware_data['finish']
            if not hasattr(HardwareFinish, finish):
                raise ValidationError(f"Invalid hardware finish: {finish}")