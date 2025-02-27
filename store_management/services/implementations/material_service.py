"""
Material Service Implementation.

This module provides a concrete implementation of the Material Service interface
for managing materials used in leatherworking projects.
"""

import logging
from typing import Any, Dict, List, Optional

# Try to import the interface
try:
    from services.interfaces.material_service import IMaterialService, MaterialType
except ImportError:
    # Create placeholder classes if imports fail
    import enum

    class MaterialType(enum.Enum):
        """Types of materials used in leatherworking."""
        LEATHER = "leather"
        HARDWARE = "hardware"
        THREAD = "thread"
        LINING = "lining"
        ADHESIVE = "adhesive"
        OTHER = "other"

    class IMaterialService:
        """Placeholder for IMaterialService interface."""
        pass


class MaterialService(IMaterialService):
    """
    Implementation of the Material Service interface.

    This service manages materials used in leatherworking projects,
    including inventory tracking, cost calculations, and material transactions.
    """

    def __init__(self):
        """Initialize the Material Service."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("MaterialService initialized")

        # For demonstration purposes, we'll use an in-memory dictionary
        self._materials = {}
        self._material_types = {}
        self._next_id = 1

    def get_material(self, material_id: int) -> Dict[str, Any]:
        """
        Retrieve a material by its ID.

        Args:
            material_id: Unique identifier of the material

        Returns:
            Dictionary containing material details

        Raises:
            ValueError: If material with given ID doesn't exist
        """
        self.logger.debug(f"Getting material with ID: {material_id}")

        if material_id not in self._materials:
            raise ValueError(f"Material with ID {material_id} not found")

        return self._materials[material_id]

    def get_materials(self,
                     material_type: Optional[MaterialType] = None,
                     limit: int = 100,
                     offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get a list of materials, optionally filtered by type.

        Args:
            material_type: Optional filter by material type
            limit: Maximum number of records to return
            offset: Number of records to skip for pagination

        Returns:
            List of dictionaries containing material details
        """
        self.logger.debug(f"Getting materials with type: {material_type}, limit: {limit}, offset: {offset}")

        # Start with all materials
        materials = list(self._materials.values())

        # Filter by type if specified
        if material_type:
            materials = [m for m in materials if m.get('material_type') == material_type]

        # Apply pagination
        paginated = materials[offset:offset + limit]

        return paginated

    def search_materials(self,
                        search_term: str,
                        material_type: Optional[MaterialType] = None) -> List[Dict[str, Any]]:
        """
        Search materials by name, description, or other attributes.

        Args:
            search_term: Term to search for
            material_type: Optional filter by material type

        Returns:
            List of dictionaries containing matching material details
        """
        self.logger.debug(f"Searching materials with term: {search_term}, type: {material_type}")

        search_term = search_term.lower()
        results = []

        for material in self._materials.values():
            # Check if search term matches name or description
            name_match = search_term in material.get('name', '').lower()
            desc_match = search_term in material.get('description', '').lower()

            # Filter by type if specified
            type_match = True
            if material_type:
                type_match = material.get('material_type') == material_type

            if (name_match or desc_match) and type_match:
                results.append(material)

        return results

    def create_material(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new material.

        Args:
            material_data: Dictionary containing material details

        Returns:
            Dictionary containing the created material details

        Raises:
            ValueError: If material data is invalid
        """
        self.logger.debug(f"Creating material with data: {material_data}")

        # Validate required fields
        required_fields = ['name', 'material_type']
        for field in required_fields:
            if field not in material_data:
                raise ValueError(f"Missing required field: {field}")

        # Create new material
        material_id = self._next_id
        self._next_id += 1

        material = {
            'id': material_id,
            **material_data
        }

        # Store in dictionary
        self._materials[material_id] = material

        self.logger.info(f"Created material with ID: {material_id}")
        return material

    def update_material(self,
                       material_id: int,
                       material_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing material.

        Args:
            material_id: Unique identifier of the material to update
            material_data: Dictionary containing updated material details

        Returns:
            Dictionary containing the updated material details

        Raises:
            ValueError: If material with given ID doesn't exist
        """
        self.logger.debug(f"Updating material {material_id} with data: {material_data}")

        # Check if material exists
        if material_id not in self._materials:
            raise ValueError(f"Material with ID {material_id} not found")

        # Update the material
        self._materials[material_id].update(material_data)

        self.logger.info(f"Updated material with ID: {material_id}")
        return self._materials[material_id]

    def delete_material(self, material_id: int) -> bool:
        """
        Delete a material.

        Args:
            material_id: Unique identifier of the material to delete

        Returns:
            True if deletion was successful, False otherwise

        Raises:
            ValueError: If material with given ID doesn't exist
        """
        self.logger.debug(f"Deleting material with ID: {material_id}")

        # Check if material exists
        if material_id not in self._materials:
            raise ValueError(f"Material with ID {material_id} not found")

        # Delete the material
        del self._materials[material_id]

        self.logger.info(f"Deleted material with ID: {material_id}")
        return True

    def get_material_types(self) -> List[Dict[str, Any]]:
        """
        Get a list of all material types.

        Returns:
            List of dictionaries containing material type details
        """
        self.logger.debug("Getting all material types")

        return [
            {"id": material_type.name, "name": material_type.value}
            for material_type in MaterialType
        ]

    def record_material_transaction(self,
                                   material_id: int,
                                   quantity: float,
                                   transaction_type: str,
                                   notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Record a material transaction (purchase, usage, etc.).

        Args:
            material_id: Unique identifier of the material
            quantity: Quantity of material in the transaction
            transaction_type: Type of transaction (purchase, usage, adjustment, etc.)
            notes: Optional notes about the transaction

        Returns:
            Dictionary containing the transaction details

        Raises:
            ValueError: If material with given ID doesn't exist
        """
        self.logger.debug(f"Recording transaction for material ID {material_id}")

        # Check if material exists
        if material_id not in self._materials:
            raise ValueError(f"Material with ID {material_id} not found")

        # Create transaction record
        transaction = {
            'material_id': material_id,
            'quantity': quantity,
            'transaction_type': transaction_type,
            'notes': notes
        }

        # Update material quantity
        material = self._materials[material_id]
        current_quantity = material.get('quantity', 0)
        material['quantity'] = current_quantity + quantity

        self.logger.info(f"Recorded transaction for material ID {material_id}")
        return transaction

    def get_material_transactions(self,
                                 material_id: int,
                                 start_date: Optional[str] = None,
                                 end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a list of transactions for a specific material.

        Args:
            material_id: Unique identifier of the material
            start_date: Optional start date for filtering transactions
            end_date: Optional end date for filtering transactions

        Returns:
            List of dictionaries containing transaction details

        Raises:
            ValueError: If material with given ID doesn't exist
        """
        self.logger.debug(f"Getting transactions for material ID {material_id}")

        # Check if material exists
        if material_id not in self._materials:
            raise ValueError(f"Material with ID {material_id} not found")

        # In this simple implementation, we don't store transactions
        # In a real implementation, this would query a database
        return []

    def calculate_material_cost(self,
                               material_id: int,
                               quantity: float) -> float:
        """
        Calculate the cost of a specified quantity of material.

        Args:
            material_id: Unique identifier of the material
            quantity: Quantity of material to calculate cost for

        Returns:
            Calculated cost

        Raises:
            ValueError: If material with given ID doesn't exist
        """
        self.logger.debug(f"Calculating cost for {quantity} units of material ID {material_id}")

        # Check if material exists
        if material_id not in self._materials:
            raise ValueError(f"Material with ID {material_id} not found")

        # Get material and calculate cost
        material = self._materials[material_id]
        unit_price = material.get('unit_price', 0)

        return unit_price * quantity