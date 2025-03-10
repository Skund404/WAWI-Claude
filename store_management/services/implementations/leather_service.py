from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from database.repositories.leather_repository import LeatherRepository
from database.repositories.supplier_repository import SupplierRepository
from database.repositories.inventory_repository import InventoryRepository
from database.repositories.material_repository import MaterialRepository

from database.models.enums import LeatherType, LeatherFinish, InventoryStatus, TransactionType

from services.base_service import BaseService
from services.implementations.material_service import MaterialService
from services.exceptions import ValidationError, NotFoundError
from services.dto.material_dto import LeatherDTO

from di.inject import inject


class LeatherService(MaterialService):
    """Implementation of the leather service interface."""

    @inject
    def __init__(self, session: Session,
                 leather_repository: Optional[LeatherRepository] = None,
                 material_repository: Optional[MaterialRepository] = None,
                 supplier_repository: Optional[SupplierRepository] = None,
                 inventory_repository: Optional[InventoryRepository] = None):
        """Initialize the leather service."""
        super().__init__(session)
        self.leather_repository = leather_repository or LeatherRepository(session)
        self.material_repository = material_repository or MaterialRepository(session)
        self.supplier_repository = supplier_repository or SupplierRepository(session)
        self.inventory_repository = inventory_repository or InventoryRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, leather_id: int) -> Dict[str, Any]:
        """Get leather by ID."""
        try:
            leather = self.leather_repository.get_by_id(leather_id)
            if not leather:
                raise NotFoundError(f"Leather with ID {leather_id} not found")
            return LeatherDTO.from_model(leather, include_inventory=True, include_supplier=True).to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving leather {leather_id}: {str(e)}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all leather materials, optionally filtered."""
        try:
            # Ensure only leather materials are returned
            if not filters:
                filters = {}
            filters['material_type'] = 'LEATHER'

            leathers = self.leather_repository.get_all(filters=filters)
            return [LeatherDTO.from_model(leather).to_dict() for leather in leathers]
        except Exception as e:
            self.logger.error(f"Error retrieving leather materials: {str(e)}")
            raise

    def create(self, leather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new leather material."""
        try:
            # Validate leather data
            self._validate_leather_data(leather_data)

            # Set material type to LEATHER
            leather_data['material_type'] = 'LEATHER'

            # Create leather material
            with self.transaction():
                leather = self.leather_repository.create(leather_data)

                # Create inventory entry if not exists
                inventory_data = {
                    'item_type': 'material',
                    'item_id': leather.id,
                    'quantity': leather_data.get('initial_quantity', 0),
                    'status': InventoryStatus.IN_STOCK.value if leather_data.get('initial_quantity',
                                                                                 0) > 0 else InventoryStatus.OUT_OF_STOCK.value,
                    'storage_location': leather_data.get('storage_location', '')
                }
                self.inventory_repository.create(inventory_data)

                return LeatherDTO.from_model(leather, include_inventory=True, include_supplier=True).to_dict()
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creating leather material: {str(e)}")
            raise

    def update(self, leather_id: int, leather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing leather material."""
        try:
            # Check if leather exists
            leather = self.leather_repository.get_by_id(leather_id)
            if not leather:
                raise NotFoundError(f"Leather with ID {leather_id} not found")

            # Validate leather data
            self._validate_leather_data(leather_data, update=True)

            # Update leather
            with self.transaction():
                updated_leather = self.leather_repository.update(leather_id, leather_data)
                return LeatherDTO.from_model(updated_leather, include_inventory=True, include_supplier=True).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating leather {leather_id}: {str(e)}")
            raise

    def get_by_type(self, leather_type: str) -> List[Dict[str, Any]]:
        """Get leather materials by type."""
        try:
            # Validate leather type
            if not hasattr(LeatherType, leather_type):
                raise ValidationError(f"Invalid leather type: {leather_type}")

            leathers = self.leather_repository.get_by_leather_type(leather_type)
            return [LeatherDTO.from_model(leather).to_dict() for leather in leathers]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving leather materials by type '{leather_type}': {str(e)}")
            raise

    def get_by_finish(self, finish: str) -> List[Dict[str, Any]]:
        """Get leather materials by finish."""
        try:
            # Validate leather finish
            if not hasattr(LeatherFinish, finish):
                raise ValidationError(f"Invalid leather finish: {finish}")

            leathers = self.leather_repository.get_by_finish(finish)
            return [LeatherDTO.from_model(leather).to_dict() for leather in leathers]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving leather materials by finish '{finish}': {str(e)}")
            raise

    def get_by_thickness_range(self, min_thickness: float, max_thickness: float) -> List[Dict[str, Any]]:
        """Get leather materials within a thickness range."""
        try:
            # Validate thickness range
            if min_thickness < 0 or max_thickness < 0:
                raise ValidationError("Thickness values cannot be negative")

            if min_thickness > max_thickness:
                raise ValidationError("Minimum thickness cannot be greater than maximum thickness")

            leathers = self.leather_repository.get_by_thickness_range(min_thickness, max_thickness)
            return [LeatherDTO.from_model(leather).to_dict() for leather in leathers]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving leather materials by thickness range: {str(e)}")
            raise

    def calculate_area_remaining(self, leather_id: int) -> Dict[str, Any]:
        """Calculate the remaining area of a leather hide."""
        try:
            # Check if leather exists
            leather = self.leather_repository.get_by_id(leather_id)
            if not leather:
                raise NotFoundError(f"Leather with ID {leather_id} not found")

            # Get inventory status
            inventory = self.inventory_repository.get_by_item('material', leather_id)
            if not inventory:
                return {
                    'leather_id': leather_id,
                    'original_area': getattr(leather, 'area', 0),
                    'used_area': 0,
                    'remaining_area': getattr(leather, 'area', 0),
                    'remaining_percentage': 100.0,
                    'is_full_hide': getattr(leather, 'is_full_hide', False)
                }

            # Calculate used area based on transactions
            transactions = inventory.transactions if hasattr(inventory, 'transactions') else []

            used_area = 0
            for transaction in transactions:
                if transaction.transaction_type == TransactionType.USAGE.value:
                    used_area += transaction.quantity

            # Calculate remaining area
            original_area = getattr(leather, 'area', 0)
            remaining_area = inventory.quantity
            remaining_percentage = (remaining_area / original_area * 100) if original_area > 0 else 0

            return {
                'leather_id': leather_id,
                'leather_name': leather.name,
                'original_area': original_area,
                'used_area': used_area,
                'remaining_area': remaining_area,
                'remaining_percentage': remaining_percentage,
                'is_full_hide': getattr(leather, 'is_full_hide', False),
                'unit': getattr(leather, 'unit', None)
            }
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error calculating area for leather {leather_id}: {str(e)}")
            raise

    def _validate_leather_data(self, leather_data: Dict[str, Any], update: bool = False) -> None:
        """Validate leather data.

        Args:
            leather_data: Leather data to validate
            update: Whether this is for an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Call parent validator for basic material validation
        self._validate_material_data(leather_data, update)

        # Validate leather-specific fields
        if 'leather_type' in leather_data and leather_data['leather_type']:
            leather_type = leather_data['leather_type']
            if not hasattr(LeatherType, leather_type):
                raise ValidationError(f"Invalid leather type: {leather_type}")

        if 'leather_finish' in leather_data and leather_data['leather_finish']:
            leather_finish = leather_data['leather_finish']
            if not hasattr(LeatherFinish, leather_finish):
                raise ValidationError(f"Invalid leather finish: {leather_finish}")

        if 'thickness' in leather_data:
            thickness = leather_data['thickness']
            if thickness is not None and thickness < 0:
                raise ValidationError("Thickness cannot be negative")

        if 'area' in leather_data:
            area = leather_data['area']
            if area is not None and area <= 0:
                raise ValidationError("Area must be positive")