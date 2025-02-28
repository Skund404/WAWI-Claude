"""
Interface for the Material Service.

This module defines the interface for the Material Service,
which is responsible for managing materials used in leatherworking projects.
"""

from abc import ABC, abstractmethod
import enum
from typing import Any, Dict, List, Optional, Union
from .base_service import IBaseService
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from services.base_service import BaseService
from services.interfaces.material_service import IMaterialService, MaterialType
from utils.circular_import_resolver import lazy_import, get_class


class MaterialService(BaseService, IMaterialService):
    """Implementation of material service for managing materials and transactions."""

    def __init__(self):
        """Initialize the Material Service."""
        super().__init__()
        self.logger.info("MaterialService initialized")
        self._materials = {}
        self._transactions = []

    def create(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new material.

        Args:
            material_data: Material data

        Returns:
            Created material data
        """
        material_id = material_data.get('id') or str(len(self._materials) + 1)
        material = {
            'id': material_id,
            'name': material_data.get('name', ''),
            'type': material_data.get('type', MaterialType.OTHER),
            'quantity': material_data.get('quantity', 0),
            'unit_price': material_data.get('unit_price', 0.0),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        self._materials[material_id] = material
        return material

    def get_by_id(self, material_id: str) -> Optional[Dict[str, Any]]:
        """Get material by ID.

        Args:
            material_id: Material ID

        Returns:
            Material data or None if not found
        """
        return self._materials.get(material_id)

    def update(self, material_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing material.

        Args:
            material_id: Material ID to update
            updates: Updates to apply

        Returns:
            Updated material data or None if not found
        """
        material = self._materials.get(material_id)
        if not material:
            return None

        material.update(updates)
        material['updated_at'] = datetime.now()
        return material

    def delete(self, material_id: str) -> bool:
        """Delete a material.

        Args:
            material_id: Material ID to delete

        Returns:
            True if deleted, False if not found
        """
        if material_id in self._materials:
            del self._materials[material_id]
            return True
        return False

    def get_materials(self, material_type: Optional[MaterialType] = None) -> List[Dict[str, Any]]:
        """Get all materials, optionally filtered by type.

        Args:
            material_type: Optional material type filter

        Returns:
            List of material data
        """
        if material_type:
            return [m for m in self._materials.values() if m.get('type') == material_type]
        return list(self._materials.values())

    def record_material_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record a material transaction.

        Args:
            transaction_data: Transaction data

        Returns:
            Created transaction data
        """
        transaction_id = len(self._transactions) + 1
        transaction = {
            'id': transaction_id,
            'material_id': transaction_data.get('material_id'),
            'quantity': transaction_data.get('quantity', 0),
            'type': transaction_data.get('type', 'use'),
            'timestamp': datetime.now(),
            'notes': transaction_data.get('notes', '')
        }

        self._transactions.append(transaction)

        # Update material quantity if applicable
        material_id = transaction.get('material_id')
        if material_id in self._materials:
            quantity_change = transaction.get('quantity', 0)
            transaction_type = transaction.get('type')

            if transaction_type == 'purchase':
                self._materials[material_id]['quantity'] += quantity_change
            elif transaction_type == 'use':
                self._materials[material_id]['quantity'] -= quantity_change

        return transaction

    def get_material_transactions(self,
                                  material_id: Optional[str] = None,
                                  transaction_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get material transactions with optional filtering.

        Args:
            material_id: Optional material ID filter
            transaction_type: Optional transaction type filter

        Returns:
            List of transaction data
        """
        result = self._transactions

        if material_id:
            result = [t for t in result if t.get('material_id') == material_id]

        if transaction_type:
            result = [t for t in result if t.get('type') == transaction_type]

        return result

    def calculate_material_cost(self, material_id: str, quantity: float) -> float:
        """Calculate cost for a given material quantity.

        Args:
            material_id: Material ID
            quantity: Quantity of material

        Returns:
            Calculated cost
        """
        material = self._materials.get(material_id)
        if not material:
            return 0.0

        unit_price = material.get('unit_price', 0.0)
        return unit_price * quantity

    def get_material_types(self) -> List[str]:
        """Get all available material types.

        Returns:
            List of material type names
        """
        return [t.name for t in MaterialType]

class MaterialType(enum.Enum):
    """Types of materials used in leatherworking."""
    LEATHER = "leather"
    HARDWARE = "hardware"
    THREAD = "thread"
    LINING = "lining"
    ADHESIVE = "adhesive"
    OTHER = "other"

