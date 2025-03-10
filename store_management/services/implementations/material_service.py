# services/implementations/material_service.py
from typing import List, Optional, Dict, Any, Type, cast
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from database.repositories.material_repository import MaterialRepository
from database.repositories.inventory_repository import InventoryRepository
from database.models.material import Material
from database.models.enums import InventoryStatus, TransactionType, MaterialType
from services.base_service import BaseService, ValidationError, NotFoundError


class MaterialService(BaseService):
    """Implementation of the material service interface."""

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
            return self._to_dict(material)
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
            return [self._to_dict(material) for material in materials]
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
                    'status': self._determine_inventory_status(material_data.get('initial_quantity', 0)),
                    'storage_location': material_data.get('storage_location', '')
                }
                self.inventory_repository.create(inventory_data)

                return self._to_dict(material)
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
                return self._to_dict(updated_material)
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
            if hasattr(material, 'components') and material.components:
                raise ValidationError(f"Cannot delete material {material_id} as it is used in components")

            # Delete material and related inventory
            with self.transaction():
                # Get inventory entries for this material
                inventory_entries = self.inventory_repository.get_by_item(
                    item_type='material',
                    item_id=material_id
                )

                # Delete inventory entries
                for entry in inventory_entries:
                    self.inventory_repository.delete(entry.id)

                # Delete material
                self.material_repository.delete(material_id)
                return True
        except Exception as e:
            self.logger.error(f"Error deleting material {material_id}: {str(e)}")
            raise

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for materials by name or other properties.

        Args:
            query: Search query string

        Returns:
            List of dicts representing matching materials
        """
        try:
            # Implement search functionality
            materials = self.material_repository.search(query)
            return [self._to_dict(material) for material in materials]
        except Exception as e:
            self.logger.error(f"Error searching materials: {str(e)}")
            raise

    def get_inventory_status(self, material_id: int) -> Dict[str, Any]:
        """Get inventory status for a material.

        Args:
            material_id: ID of the material

        Returns:
            Dict representing the inventory status

        Raises:
            NotFoundError: If material or inventory not found
        """
        try:
            # Check if material exists
            material = self.material_repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Get inventory entry
            inventory = self.inventory_repository.get_by_item(
                item_type='material',
                item_id=material_id
            )

            if not inventory:
                raise NotFoundError(f"Inventory entry for material {material_id} not found")

            # Return inventory status
            return self._to_dict(inventory)
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
            Dict representing the updated inventory

        Raises:
            NotFoundError: If material or inventory not found
            ValidationError: If validation fails
        """
        try:
            # Check if material exists
            material = self.material_repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Get inventory entry
            inventory = self.inventory_repository.get_by_item(
                item_type='material',
                item_id=material_id
            )

            if not inventory:
                raise NotFoundError(f"Inventory entry for material {material_id} not found")

            # Validate quantity
            if inventory.quantity + quantity < 0:
                raise ValidationError("Cannot reduce inventory below zero")

            # Update inventory
            with self.transaction():
                # Determine transaction type
                transaction_type = TransactionType.USAGE.value if quantity < 0 else TransactionType.RESTOCK.value

                # Update inventory quantity and status
                new_quantity = inventory.quantity + quantity
                inventory_data = {
                    'quantity': new_quantity,
                    'status': self._determine_inventory_status(new_quantity)
                }

                updated_inventory = self.inventory_repository.update(inventory.id, inventory_data)

                # Record transaction (if transaction repository is available)
                if hasattr(self, 'transaction_repository'):
                    transaction_data = {
                        'item_type': 'material',
                        'item_id': material_id,
                        'quantity': abs(quantity),
                        'type': transaction_type,
                        'notes': reason,
                        'created_at': datetime.now()
                    }
                    self.transaction_repository.create(transaction_data)

                return self._to_dict(updated_inventory)
        except Exception as e:
            self.logger.error(f"Error adjusting inventory for material {material_id}: {str(e)}")
            raise

    def get_by_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get materials by supplier ID.

        Args:
            supplier_id: ID of the supplier

        Returns:
            List of dicts representing materials from the supplier

        Raises:
            NotFoundError: If supplier not found
        """
        try:
            # Get materials by supplier
            materials = self.material_repository.get_by_supplier(supplier_id)
            return [self._to_dict(material) for material in materials]
        except Exception as e:
            self.logger.error(f"Error getting materials for supplier {supplier_id}: {str(e)}")
            raise

    def get_low_stock(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get materials with low stock levels.

        Args:
            threshold: Optional stock threshold (default uses system-defined threshold)

        Returns:
            List of dicts representing materials with low stock
        """
        try:
            # Get low stock materials
            if threshold is not None:
                # Custom threshold provided
                inventories = self.inventory_repository.get_by_quantity_below(threshold)
            else:
                # Use system-defined low stock status
                inventories = self.inventory_repository.get_by_status(InventoryStatus.LOW_STOCK.value)

            # Get material details for each inventory item
            result = []
            for inventory in inventories:
                if inventory.item_type == 'material':
                    material = self.material_repository.get_by_id(inventory.item_id)
                    if material:
                        material_dict = self._to_dict(material)
                        material_dict['inventory'] = self._to_dict(inventory)
                        result.append(material_dict)

            return result
        except Exception as e:
            self.logger.error(f"Error getting low stock materials: {str(e)}")
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
        # Only check required fields for new materials
        if not update:
            required_fields = ['name', 'material_type', 'unit']
            for field in required_fields:
                if field not in data:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate material_type if provided
        if 'material_type' in data:
            try:
                MaterialType(data['material_type'])
            except ValueError:
                raise ValidationError(f"Invalid material type: {data['material_type']}")

        # Validate supplier_id if provided
        if 'supplier_id' in data and data['supplier_id'] is not None:
            supplier_id = data['supplier_id']
            # This would require supplier repository, so we'll just validate the type for now
            if not isinstance(supplier_id, int) or supplier_id <= 0:
                raise ValidationError(f"Invalid supplier_id: {supplier_id}")

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


# services/implementations/leather_service.py
from typing import List, Optional, Dict, Any, Type, cast
from sqlalchemy.orm import Session

from database.repositories.leather_repository import LeatherRepository
from database.repositories.inventory_repository import InventoryRepository
from database.models.material import Leather
from database.models.enums import LeatherType, InventoryStatus
from services.implementations.material_service import MaterialService
from services.base_service import ValidationError, NotFoundError


class LeatherService(MaterialService):
    """Implementation of the leather service interface.

    Extends the material service with leather-specific functionality.
    """

    def __init__(self, session: Session, leather_repository: Optional[LeatherRepository] = None,
                 inventory_repository: Optional[InventoryRepository] = None):
        """Initialize the leather service.

        Args:
            session: SQLAlchemy database session
            leather_repository: Optional LeatherRepository instance
            inventory_repository: Optional InventoryRepository instance
        """
        super().__init__(session, leather_repository, inventory_repository)
        self.leather_repository = leather_repository or LeatherRepository(session)

    def create(self, leather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new leather material.

        Args:
            leather_data: Dict containing leather properties

        Returns:
            Dict representing the created leather

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Add default material_type if not provided
            if 'material_type' not in leather_data:
                leather_data['material_type'] = 'LEATHER'

            # Validate leather-specific data
            self._validate_leather_data(leather_data)

            # Use superclass to create the material
            return super().create(leather_data)
        except Exception as e:
            self.logger.error(f"Error creating leather: {str(e)}")
            raise

    def update(self, leather_id: int, leather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing leather material.

        Args:
            leather_id: ID of the leather to update
            leather_data: Dict containing updated leather properties

        Returns:
            Dict representing the updated leather

        Raises:
            NotFoundError: If leather not found
            ValidationError: If validation fails
        """
        try:
            # Ensure we're updating a leather material
            material = self.material_repository.get_by_id(leather_id)
            if not material or not isinstance(material, Leather):
                raise NotFoundError(f"Leather with ID {leather_id} not found")

            # Validate leather-specific data
            self._validate_leather_data(leather_data, update=True)

            # Use superclass to update the material
            return super().update(leather_id, leather_data)
        except Exception as e:
            self.logger.error(f"Error updating leather {leather_id}: {str(e)}")
            raise

    def get_by_type(self, leather_type: str) -> List[Dict[str, Any]]:
        """Get leathers by type.

        Args:
            leather_type: Leather type to filter by

        Returns:
            List of dicts representing leathers of the specified type
        """
        try:
            # Validate leather type
            try:
                LeatherType(leather_type)
            except ValueError:
                raise ValidationError(f"Invalid leather type: {leather_type}")

            # Get leathers by type
            leathers = self.leather_repository.get_by_leather_type(leather_type)
            return [self._to_dict(leather) for leather in leathers]
        except Exception as e:
            self.logger.error(f"Error getting leathers of type {leather_type}: {str(e)}")
            raise

    def get_by_thickness(self, min_thickness: float, max_thickness: float) -> List[Dict[str, Any]]:
        """Get leathers by thickness range.

        Args:
            min_thickness: Minimum thickness
            max_thickness: Maximum thickness

        Returns:
            List of dicts representing leathers in the thickness range
        """
        try:
            # Validate thickness range
            if min_thickness < 0 or max_thickness < min_thickness:
                raise ValidationError(f"Invalid thickness range: {min_thickness} to {max_thickness}")

            # Get leathers by thickness range
            leathers = self.leather_repository.get_by_thickness_range(min_thickness, max_thickness)
            return [self._to_dict(leather) for leather in leathers]
        except Exception as e:
            self.logger.error(f"Error getting leathers by thickness range: {str(e)}")
            raise

    def calculate_area_cost(self, leather_id: int, area: float) -> Dict[str, Any]:
        """Calculate cost for a specific area of leather.

        Args:
            leather_id: ID of the leather
            area: Area to calculate cost for

        Returns:
            Dict with cost information

        Raises:
            NotFoundError: If leather not found
            ValidationError: If validation fails
        """
        try:
            # Get leather
            leather = self.leather_repository.get_by_id(leather_id)
            if not leather:
                raise NotFoundError(f"Leather with ID {leather_id} not found")

            # Validate area
            if area <= 0:
                raise ValidationError(f"Area must be greater than zero")

            # Calculate cost
            if not hasattr(leather, 'price_per_unit') or leather.price_per_unit is None:
                raise ValidationError(f"Leather {leather_id} has no price information")

            cost = leather.price_per_unit * area

            # Return cost information
            return {
                'leather_id': leather_id,
                'leather_name': leather.name,
                'area': area,
                'price_per_unit': leather.price_per_unit,
                'total_cost': cost
            }
        except Exception as e:
            self.logger.error(f"Error calculating area cost for leather {leather_id}: {str(e)}")
            raise

    # Helper methods

    def _validate_leather_data(self, data: Dict[str, Any], update: bool = False) -> None:
        """Validate leather-specific data.

        Args:
            data: Leather data to validate
            update: Whether this is an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Call parent validation first
        super()._validate_material_data(data, update)

        # Only check required leather fields for new entries
        if not update:
            required_fields = ['leather_type']
            for field in required_fields:
                if field not in data:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate leather_type if provided
        if 'leather_type' in data:
            try:
                LeatherType(data['leather_type'])
            except ValueError:
                raise ValidationError(f"Invalid leather type: {data['leather_type']}")

        # Validate thickness if provided
        if 'thickness' in data:
            thickness = data['thickness']
            if not isinstance(thickness, (int, float)) or thickness <= 0:
                raise ValidationError(f"Invalid thickness: {thickness}")

        # Validate area if provided
        if 'area' in data:
            area = data['area']
            if not isinstance(area, (int, float)) or area <= 0:
                raise ValidationError(f"Invalid area: {area}")