from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from database.repositories.supplies_repository import SuppliesRepository
from database.repositories.supplier_repository import SupplierRepository
from database.repositories.inventory_repository import InventoryRepository
from database.repositories.material_repository import MaterialRepository

from database.models.enums import MaterialType, InventoryStatus, TransactionType

from services.base_service import BaseService
from services.implementations.material_service import MaterialService
from services.exceptions import ValidationError, NotFoundError
from services.dto.material_dto import SuppliesDTO

from di.core import inject


class SuppliesService(MaterialService):
    """Implementation of the supplies service interface."""

    @inject
    def __init__(self, session: Session,
                 supplies_repository: Optional[SuppliesRepository] = None,
                 material_repository: Optional[MaterialRepository] = None,
                 supplier_repository: Optional[SupplierRepository] = None,
                 inventory_repository: Optional[InventoryRepository] = None):
        """Initialize the supplies service."""
        super().__init__(session)
        self.supplies_repository = supplies_repository or SuppliesRepository(session)
        self.material_repository = material_repository or MaterialRepository(session)
        self.supplier_repository = supplier_repository or SupplierRepository(session)
        self.inventory_repository = inventory_repository or InventoryRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, supplies_id: int) -> Dict[str, Any]:
        """Get supplies by ID."""
        try:
            supplies = self.supplies_repository.get_by_id(supplies_id)
            if not supplies:
                raise NotFoundError(f"Supplies with ID {supplies_id} not found")
            return SuppliesDTO.from_model(supplies, include_inventory=True, include_supplier=True).to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving supplies {supplies_id}: {str(e)}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all supplies materials, optionally filtered."""
        try:
            # Ensure only supplies materials are returned
            if not filters:
                filters = {}
            filters['material_type'] = 'SUPPLIES'

            supplies_items = self.supplies_repository.get_all(filters=filters)
            return [SuppliesDTO.from_model(supplies).to_dict() for supplies in supplies_items]
        except Exception as e:
            self.logger.error(f"Error retrieving supplies materials: {str(e)}")
            raise

    def create(self, supplies_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new supplies material."""
        try:
            # Validate supplies data
            self._validate_supplies_data(supplies_data)

            # Set material type to SUPPLIES
            supplies_data['material_type'] = 'SUPPLIES'

            # Create supplies material
            with self.transaction():
                supplies = self.supplies_repository.create(supplies_data)

                # Create inventory entry if not exists
                inventory_data = {
                    'item_type': 'material',
                    'item_id': supplies.id,
                    'quantity': supplies_data.get('initial_quantity', 0),
                    'status': InventoryStatus.IN_STOCK.value if supplies_data.get('initial_quantity',
                                                                                  0) > 0 else InventoryStatus.OUT_OF_STOCK.value,
                    'storage_location': supplies_data.get('storage_location', '')
                }
                self.inventory_repository.create(inventory_data)

                return SuppliesDTO.from_model(supplies, include_inventory=True, include_supplier=True).to_dict()
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creating supplies material: {str(e)}")
            raise

    def update(self, supplies_id: int, supplies_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing supplies material."""
        try:
            # Check if supplies exists
            supplies = self.supplies_repository.get_by_id(supplies_id)
            if not supplies:
                raise NotFoundError(f"Supplies with ID {supplies_id} not found")

            # Validate supplies data
            self._validate_supplies_data(supplies_data, update=True)

            # Update supplies
            with self.transaction():
                updated_supplies = self.supplies_repository.update(supplies_id, supplies_data)
                return SuppliesDTO.from_model(updated_supplies, include_inventory=True, include_supplier=True).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating supplies {supplies_id}: {str(e)}")
            raise

    def get_by_type(self, supplies_type: str) -> List[Dict[str, Any]]:
        """Get supplies materials by type (thread, adhesive, etc.)."""
        try:
            supplies_items = self.supplies_repository.get_by_supplies_type(supplies_type)
            return [SuppliesDTO.from_model(supplies).to_dict() for supplies in supplies_items]
        except Exception as e:
            self.logger.error(f"Error retrieving supplies materials by type '{supplies_type}': {str(e)}")
            raise

    def get_by_color(self, color: str) -> List[Dict[str, Any]]:
        """Get supplies by color."""
        try:
            supplies_items = self.supplies_repository.get_by_color(color)
            return [SuppliesDTO.from_model(supplies).to_dict() for supplies in supplies_items]
        except Exception as e:
            self.logger.error(f"Error retrieving supplies by color '{color}': {str(e)}")
            raise

    def get_threads(self) -> List[Dict[str, Any]]:
        """Get all thread supplies."""
        try:
            threads = self.supplies_repository.get_by_supplies_type('thread')
            return [SuppliesDTO.from_model(thread).to_dict() for thread in threads]
        except Exception as e:
            self.logger.error(f"Error retrieving thread supplies: {str(e)}")
            raise

    def get_adhesives(self) -> List[Dict[str, Any]]:
        """Get all adhesive supplies."""
        try:
            adhesives = self.supplies_repository.get_by_supplies_type('adhesive')
            return [SuppliesDTO.from_model(adhesive).to_dict() for adhesive in adhesives]
        except Exception as e:
            self.logger.error(f"Error retrieving adhesive supplies: {str(e)}")
            raise

    def get_dyes(self) -> List[Dict[str, Any]]:
        """Get all dye supplies."""
        try:
            dyes = self.supplies_repository.get_by_supplies_type('dye')
            return [SuppliesDTO.from_model(dye).to_dict() for dye in dyes]
        except Exception as e:
            self.logger.error(f"Error retrieving dye supplies: {str(e)}")
            raise

    def get_finishes(self) -> List[Dict[str, Any]]:
        """Get all finish supplies."""
        try:
            finishes = self.supplies_repository.get_by_supplies_type('finish')
            return [SuppliesDTO.from_model(finish).to_dict() for finish in finishes]
        except Exception as e:
            self.logger.error(f"Error retrieving finish supplies: {str(e)}")
            raise

    def _validate_supplies_data(self, supplies_data: Dict[str, Any], update: bool = False) -> None:
        """Validate supplies data.

        Args:
            supplies_data: Supplies data to validate
            update: Whether this is for an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Call parent validator for basic material validation
        self._validate_material_data(supplies_data, update)

        # Validate supplies-specific fields
        if 'supplies_type' in supplies_data and supplies_data['supplies_type'] is not None:
            # This is a free-form field, but we can do basic validation
            valid_types = ['thread', 'adhesive', 'dye', 'finish', 'edge_paint', 'wax', 'conditioning']
            supplies_type = supplies_data['supplies_type'].lower()

            if supplies_type not in valid_types and not update:
                self.logger.warning(
                    f"Supplies type '{supplies_type}' is not one of the common types: {', '.join(valid_types)}")

        if 'thickness' in supplies_data and supplies_data['thickness'] is not None:
            thickness = supplies_data['thickness']
            if not isinstance(thickness, (str, int, float)):
                raise ValidationError("Thickness must be a string, integer or float")

        if 'color' in supplies_data and supplies_data['color'] is not None:
            if not isinstance(supplies_data['color'], str):
                raise ValidationError("Color must be a string")