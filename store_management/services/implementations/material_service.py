# services/implementations/material_service.py
# Implementation of the material service interface

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from database.repositories.material_repository import MaterialRepository
from database.repositories.inventory_repository import InventoryRepository
from database.models.enums import InventoryStatus, TransactionType, MaterialType
from services.base_service import BaseService
from services.exceptions import ValidationError, NotFoundError
from services.dto.material_dto import MaterialDTO

from di.inject import inject


class MaterialService(BaseService):
    """Implementation of the material service interface."""

    @inject
    def __init__(self, session: Session, material_repository: Optional[MaterialRepository] = None,
                 inventory_repository: Optional[InventoryRepository] = None):
        """Initialize the material service.

        Args:
            session: SQLAlchemy database session
            material_repository: Optional MaterialRepository instance
            inventory_repository: Optional InventoryRepository instance
        """
        super().__init__(session)
        self.material_repository = material_repository or MaterialRepository(session)
        self.inventory_repository = inventory_repository or InventoryRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, material_id: int) -> Dict[str, Any]:
        """Get material by ID.

        Args:
            material_id: ID of the material to retrieve

        Returns:
            Dict representing the material

        Raises:
            NotFoundError: If material not found
        """
        try:
            material = self.material_repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")
            return MaterialDTO.from_model(material).to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving material {material_id}: {str(e)}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all materials, optionally filtered.

        Args:
            filters: Optional filters to apply

        Returns:
            List of dicts representing materials
        """
        try:
            materials = self.material_repository.get_all(filters)
            return [MaterialDTO.from_model(material).to_dict() for material in materials]
        except Exception as e:
            self.logger.error(f"Error retrieving materials: {str(e)}")
            raise

    def create(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new material.

        Args:
            material_data: Dict containing material properties

        Returns:
            Dict representing the created material

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate material data
            self._validate_material_data(material_data)

            # Create material
            with self.transaction():
                material = self.material_repository.create(material_data)

                # Create inventory entry if not exists
                inventory_data = {
                    'item_type': 'material',
                    'item_id': material.id,
                    'quantity': material_data.get('initial_quantity', 0),
                    'status': InventoryStatus.IN_STOCK.value if material_data.get('initial_quantity',
                                                                                  0) > 0 else InventoryStatus.OUT_OF_STOCK.value,
                    'storage_location': material_data.get('storage_location', '')
                }
                self.inventory_repository.create(inventory_data)

                # Convert to DTO and return
                return MaterialDTO.from_model(material).to_dict()
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creating material: {str(e)}")
            raise

    def update(self, material_id: int, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing material.

        Args:
            material_id: ID of the material to update
            material_data: Dict containing updated material properties

        Returns:
            Dict representing the updated material

        Raises:
            NotFoundError: If material not found
            ValidationError: If validation fails
        """
        try:
            # Check if material exists
            material = self.material_repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Validate material data
            self._validate_material_data(material_data, update=True)

            # Update material
            with self.transaction():
                updated_material = self.material_repository.update(material_id, material_data)
                return MaterialDTO.from_model(updated_material).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating material {material_id}: {str(e)}")
            raise

    def delete(self, material_id: int) -> bool:
        """Delete a material by ID.

        Args:
            material_id: ID of the material to delete

        Returns:
            True if successful

        Raises:
            NotFoundError: If material not found
        """
        try:
            # Check if material exists
            material = self.material_repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Check if material is used in any components
            if material.components:
                raise ValidationError(f"Cannot delete material {material_id} as it is used in components")

            # Delete material
            with self.transaction():
                # Delete inventory entries first
                inventory_entries = self.inventory_repository.get_by_item(item_type='material', item_id=material_id)
                for entry in inventory_entries:
                    self.inventory_repository.delete(entry.id)

                # Then delete material
                self.material_repository.delete(material_id)
                return True
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting material {material_id}: {str(e)}")
            raise

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for materials by name or other properties.

        Args:
            query: Search query string

        Returns:
            List of materials matching the search query
        """
        try:
            materials = self.material_repository.search(query)
            return [MaterialDTO.from_model(material).to_dict() for material in materials]
        except Exception as e:
            self.logger.error(f"Error searching materials with query '{query}': {str(e)}")
            raise

    def get_inventory_status(self, material_id: int) -> Dict[str, Any]:
        """Get inventory status for a material.

        Args:
            material_id: ID of the material

        Returns:
            Dict with inventory status information

        Raises:
            NotFoundError: If material not found
        """
        try:
            # Check if material exists
            material = self.material_repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Get inventory entry
            inventory = self.inventory_repository.get_by_item(item_type='material', item_id=material_id)
            if not inventory:
                raise NotFoundError(f"Inventory entry for material {material_id} not found")

            return self._to_dict(inventory)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting inventory status for material {material_id}: {str(e)}")
            raise

    def adjust_inventory(self, material_id: int, quantity: float, reason: str) -> Dict[str, Any]:
        """Adjust inventory for a material.

        Args:
            material_id: ID of the material
            quantity: Quantity to adjust (positive for increase, negative for decrease)
            reason: Reason for adjustment

        Returns:
            Dict representing the inventory status

        Raises:
            NotFoundError: If material not found
            ValidationError: If validation fails
        """
        try:
            # Check if material exists
            material = self.material_repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Get inventory entry
            inventory = self.inventory_repository.get_by_item(item_type='material', item_id=material_id)
            if not inventory:
                raise NotFoundError(f"Inventory entry for material {material_id} not found")

            # Validate quantity
            if inventory.quantity + quantity < 0:
                raise ValidationError(f"Cannot reduce inventory below zero")

            # Update inventory
            with self.transaction():
                transaction_type = TransactionType.USAGE.value if quantity < 0 else TransactionType.RESTOCK.value

                new_quantity = inventory.quantity + quantity
                inventory_data = {
                    'quantity': new_quantity,
                    'status': self._determine_inventory_status(new_quantity)
                }
                updated_inventory = self.inventory_repository.update(inventory.id, inventory_data)

                # Log transaction
                transaction_data = {
                    'item_type': 'material',
                    'item_id': material_id,
                    'quantity': abs(quantity),
                    'type': transaction_type,
                    'notes': reason
                }
                self.inventory_repository.create_transaction(transaction_data)

                return self._to_dict(updated_inventory)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error adjusting inventory for material {material_id}: {str(e)}")
            raise

    def get_by_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get materials by supplier ID.

        Args:
            supplier_id: ID of the supplier

        Returns:
            List of materials from the specified supplier
        """
        try:
            materials = self.material_repository.get_by_supplier(supplier_id)
            return [MaterialDTO.from_model(material).to_dict() for material in materials]
        except Exception as e:
            self.logger.error(f"Error retrieving materials for supplier {supplier_id}: {str(e)}")
            raise

    def get_low_stock(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get materials with low stock levels.

        Args:
            threshold: Optional threshold for what's considered "low stock"

        Returns:
            List of materials with low stock
        """
        try:
            materials = self.material_repository.get_low_stock(threshold)
            return [MaterialDTO.from_model(material).to_dict() for material in materials]
        except Exception as e:
            self.logger.error(f"Error retrieving low stock materials: {str(e)}")
            raise

    def get_materials_by_type(self, material_type: str) -> List[Dict[str, Any]]:
        """Get materials by type.

        Args:
            material_type: Type of materials to retrieve

        Returns:
            List of materials of the specified type
        """
        try:
            # Validate material type
            self._validate_enum_value(MaterialType, material_type, "material_type")

            materials = self.material_repository.get_by_type(material_type)
            return [MaterialDTO.from_model(material).to_dict() for material in materials]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving materials by type {material_type}: {str(e)}")
            raise

    # Helper methods

    def _validate_material_data(self, data: Dict[str, Any], update: bool = False) -> None:
        """Validate material data.

        Args:
            data: Material data to validate
            update: Whether this is an update operation

        Raises:
            ValidationError: If validation fails
        """
        required_fields = ['name', 'material_type', 'unit']
        self._validate_required_fields(data, required_fields, update)

        # Validate material type
        if 'material_type' in data:
            self._validate_enum_value(MaterialType, data['material_type'], "material_type")

    def _determine_inventory_status(self, quantity: float) -> str:
        """Determine inventory status based on quantity.

        Args:
            quantity: Current inventory quantity

        Returns:
            Inventory status string
        """
        if quantity <= 0:
            return InventoryStatus.OUT_OF_STOCK.value
        elif quantity < 5:  # This threshold could be configurable
            return InventoryStatus.LOW_STOCK.value
        else:
            return InventoryStatus.IN_STOCK.value