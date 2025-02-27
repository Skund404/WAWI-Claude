# relative path: store_management/services/implementations/hardware_service.py
"""
Hardware Service Implementation for the Leatherworking Store Management application.

Provides comprehensive functionality for managing hardware inventory.
"""

from typing import Any, List, Dict, Optional, Union
import logging

from services.base_service import Service, ValidationError, NotFoundError
from services.interfaces.hardware_service import IHardwareService
from database.models.hardware import Hardware, HardwareType, HardwareMaterial, HardwareFinish
from database.repositories.hardware_repository import HardwareRepository
from database.sqlalchemy.session import get_db_session
from ..base_service import Service
from ..interfaces.material_service import IMaterialService, MaterialType


class MaterialService(Service, IMaterialService):
    """Implementation of the material service."""

    def __init__(self):
        """Initialize the Material Service."""
        super().__init__()
        self.logger.info("MaterialService initialized")
        self._materials = {}  # In-memory storage for development

    def get_all_materials(self, material_type: Optional[MaterialType] = None) -> List[Dict[str, Any]]:
        """Get all materials, optionally filtered by type.

        Args:
            material_type: Optional filter by material type

        Returns:
            List[Dict[str, Any]]: List of materials
        """
        materials = list(self._materials.values())
        if material_type:
            return [m for m in materials if m.get('type') == material_type.value]
        return materials

    def get_material_by_id(self, material_id: int) -> Optional[Dict[str, Any]]:
        """Get material by ID.

        Args:
            material_id: ID of the material to retrieve

        Returns:
            Optional[Dict[str, Any]]: Material data if found, None otherwise
        """
        return self._materials.get(material_id)

    def create_material(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new material.

        Args:
            material_data: Data for the new material

        Returns:
            Dict[str, Any]: Created material data
        """
        material_id = len(self._materials) + 1
        material = {**material_data, 'id': material_id}
        self._materials[material_id] = material
        return material

    def update_material(self, material_id: int, material_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing material.

        Args:
            material_id: ID of the material to update
            material_data: New material data

        Returns:
            Optional[Dict[str, Any]]: Updated material data if successful, None otherwise
        """
        if material_id not in self._materials:
            return None

        updated_material = {**self._materials[material_id], **material_data, 'id': material_id}
        self._materials[material_id] = updated_material
        return updated_material

    def delete_material(self, material_id: int) -> bool:
        """Delete a material.

        Args:
            material_id: ID of the material to delete

        Returns:
            bool: True if successful, False otherwise
        """
        if material_id not in self._materials:
            return False

        del self._materials[material_id]
        return True

    def search_materials(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for materials.

        Args:
            search_term: Term to search for

        Returns:
            List[Dict[str, Any]]: List of matching materials
        """
        search_term = search_term.lower()
        return [
            material for material in self._materials.values()
            if search_term in material.get('name', '').lower() or
               search_term in material.get('description', '').lower()
        ]

class HardwareService(Service[Hardware], IHardwareService):
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

        # Use provided repository or create a new one
        self._repository = hardware_repository or HardwareRepository(get_db_session())

    def get_by_id(self, id_value: int) -> Optional[Hardware]:
        """
        Retrieve a specific hardware item by its ID.

        Args:
            id_value (int): Unique identifier for the hardware item

        Returns:
            Optional[Hardware]: Hardware item or None if not found

        Raises:
            NotFoundError: If no hardware item with the given ID exists
        """
        try:
            hardware_item = self._repository.get_by_id(id_value)

            if not hardware_item:
                raise NotFoundError(
                    f"Hardware item with ID {id_value} not found",
                    {"id": id_value}
                )

            self.log_operation("Retrieved hardware item", {"id": id_value})
            return hardware_item
        except Exception as e:
            self.logger.error(f"Error retrieving hardware item: {e}")
            raise

    def get_all(
            self,
            filters: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> List[Hardware]:
        """
        Retrieve all hardware items with optional filtering and pagination.

        Args:
            filters (Optional[Dict[str, Any]], optional): Filtering criteria
            limit (Optional[int], optional): Maximum number of items to retrieve
            offset (Optional[int], optional): Number of items to skip

        Returns:
            List[Hardware]: List of hardware items
        """
        try:
            # Apply filtering, limit, and offset
            hardware_items = self._repository.get_all(
                filters=filters,
                limit=limit,
                offset=offset
            )

            self.log_operation("Retrieved hardware items", {
                "filter_count": len(hardware_items),
                "filters": filters or {},
                "limit": limit,
                "offset": offset
            })

            return hardware_items
        except Exception as e:
            self.logger.error(f"Error retrieving hardware items: {e}")
            return []

    def create(self, data: Dict[str, Any]) -> Hardware:
        """
        Create a new hardware item.

        Args:
            data (Dict[str, Any]): Hardware item details

        Returns:
            Hardware: Created hardware item

        Raises:
            ValidationError: If input data is invalid
        """
        try:
            # Validate input data
            self.validate_data(
                data,
                required_fields=[
                    'name',
                    'hardware_type',
                    'material',
                    'quantity',
                    'unit_price'
                ]
            )

            # Validate enum values
            try:
                hardware_type = HardwareType(data.get('hardware_type'))
                material = HardwareMaterial(data.get('material'))
                
                # Handle finish if provided
                finish = None
                if 'finish' in data and data['finish']:
                    finish = HardwareFinish(data['finish'])
            except ValueError as e:
                raise ValidationError(f"Invalid hardware type, material, or finish: {e}")

            # Prepare hardware data
            hardware_data = {
                'name': data['name'],
                'hardware_type': hardware_type,
                'material': material,
                'quantity': float(data['quantity']),
                'unit_price': float(data['unit_price']),
                'description': data.get('description', ''),
                'manufacturer': data.get('manufacturer', ''),
                'supplier_id': data.get('supplier_id')
            }
            
            # Add finish if it was provided
            if 'finish' in data and data['finish']:
                hardware_data['finish'] = finish

            # Create hardware item
            hardware_item = self._repository.create(hardware_data)

            self.log_operation("Created hardware item", {"id": hardware_item.id})
            return hardware_item

        except (ValidationError, ValueError) as ve:
            self.logger.error(f"Validation error creating hardware: {ve}")
            raise
        except Exception as e:
            self.logger.error(f"Error creating hardware item: {e}")
            raise

    def update(self, id_value: int, data: Dict[str, Any]) -> Hardware:
        """
        Update an existing hardware item.

        Args:
            id_value (int): Unique identifier of the hardware item to update
            data (Dict[str, Any]): Updated data

        Returns:
            Hardware: Updated hardware item

        Raises:
            ValidationError: If input data is invalid
            NotFoundError: If the hardware item doesn't exist
        """
        try:
            # Validate input data
            self.validate_data(data)

            # Prepare update data
            update_data = {}

            # Validate and add enum values if present
            if 'hardware_type' in data:
                try:
                    update_data['hardware_type'] = HardwareType(data['hardware_type'])
                except ValueError:
                    raise ValidationError(f"Invalid hardware type: {data['hardware_type']}")

            if 'material' in data:
                try:
                    update_data['material'] = HardwareMaterial(data['material'])
                except ValueError:
                    raise ValidationError(f"Invalid material: {data['material']}")
                    
            if 'finish' in data:
                try:
                    if data['finish']:
                        update_data['finish'] = HardwareFinish(data['finish'])
                    else:
                        update_data['finish'] = None
                except ValueError:
                    raise ValidationError(f"Invalid finish: {data['finish']}")

            # Add other updateable fields
            updateable_fields = [
                'name', 'quantity', 'unit_price',
                'description', 'manufacturer', 'supplier_id'
            ]

            for field in updateable_fields:
                if field in data:
                    update_data[field] = data[field]

            # Update hardware item
            hardware_item = self._repository.update(id_value, update_data)

            if not hardware_item:
                raise NotFoundError(
                    f"Hardware item with ID {id_value} not found",
                    {"id": id_value}
                )

            self.log_operation("Updated hardware item", {
                "id": id_value,
                "updated_fields": list(update_data.keys())
            })

            return hardware_item

        except (ValidationError, ValueError) as ve:
            self.logger.error(f"Validation error updating hardware: {ve}")
            raise
        except Exception as e:
            self.logger.error(f"Error updating hardware item: {e}")
            raise

    def delete(self, id_value: int) -> bool:
        """
        Delete a hardware item.

        Args:
            id_value (int): Unique identifier of the hardware item to delete

        Returns:
            bool: True if deletion was successful, False otherwise

        Raises:
            NotFoundError: If the hardware item doesn't exist
        """
        try:
            # Verify item exists before deletion
            existing_item = self.get_by_id(id_value)

            # Perform deletion
            deletion_result = self._repository.delete(id_value)

            if not deletion_result:
                raise NotFoundError(
                    f"Failed to delete hardware item with ID {id_value}",
                    {"id": id_value}
                )

            self.log_operation("Deleted hardware item", {"id": id_value})
            return True

        except NotFoundError:
            self.logger.error(f"Cannot delete non-existent hardware item: {id_value}")
            raise
        except Exception as e:
            self.logger.error(f"Error deleting hardware item: {e}")
            raise

    def search(
            self,
            query: str,
            filters: Optional[Dict[str, Any]] = None
    ) -> List[Hardware]:
        """
        Search for hardware items based on a query and optional filters.

        Args:
            query (str): Search query string
            filters (Optional[Dict[str, Any]], optional): Additional filtering criteria

        Returns:
            List[Hardware]: List of matching hardware items
        """
        try:
            # Prepare search filters
            search_filters = filters or {}
            search_filters['search_query'] = query

            # Perform search
            hardware_items = self._repository.search(search_filters)

            self.log_operation("Searched hardware items", {
                "query": query,
                "result_count": len(hardware_items),
                "filters": search_filters
            })

            return hardware_items
        except Exception as e:
            self.logger.error(f"Error searching hardware items: {e}")
            return []
            
    def get_by_finish(self, finish: HardwareFinish) -> List[Hardware]:
        """
        Get hardware items by finish type.
        
        Args:
            finish (HardwareFinish): The finish type to filter by
            
        Returns:
            List[Hardware]: List of hardware items with the specified finish
        """
        try:
            # Use repository to filter by finish
            if hasattr(self._repository, 'filter_by_finish'):
                hardware_items = self._repository.filter_by_finish(finish)
            else:
                # Fall back to generic filtering if specific method not available
                hardware_items = self._repository.get_all(filters={'finish': finish})
                
            self.log_operation("Retrieved hardware items by finish", {
                "finish": finish.value,
                "result_count": len(hardware_items)
            })
            
            return hardware_items
        except Exception as e:
            self.logger.error(f"Error retrieving hardware items by finish: {e}")
            return []

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