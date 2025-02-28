# services/implementations/inventory_service.py
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from services.base_service import BaseService
from services.interfaces.inventory_service import IInventoryService
from services.interfaces.material_service import MaterialType


class InventoryService(BaseService, IInventoryService):
    """Implementation of inventory service."""

    def __init__(self):
        """Initialize the Inventory Service with data structures for tracking."""
        super().__init__()
        self.logger.info("InventoryService initialized")
        # Initialize data structures for tracking inventory
        self._inventory = {}
        self._reservations = {}

    def check_material_availability(self, material_id: str, quantity: float) -> bool:
        """Check if a material is available in the specified quantity.

        Args:
            material_id: ID of the material to check
            quantity: Quantity required

        Returns:
            bool: True if available, False otherwise
        """
        self.logger.debug(f"Checking availability of material {material_id}, quantity {quantity}")
        # Simple implementation for now
        if material_id not in self._inventory:
            return False
        return self._inventory[material_id].get('quantity', 0) >= quantity

    def reserve_materials(self, materials: List[Dict[str, Any]], project_id: str) -> bool:
        """Reserve materials for a specific project.

        Args:
            materials: List of materials with quantities
            project_id: ID of the project to reserve for

        Returns:
            bool: True if reservation successful, False otherwise
        """
        self.logger.debug(f"Reserving materials for project {project_id}")

        # Check if all materials are available
        for material in materials:
            if not self.check_material_availability(material['id'], material['quantity']):
                return False

        # Reserve materials
        for material in materials:
            if material['id'] not in self._reservations:
                self._reservations[material['id']] = {}

            self._reservations[material['id']][project_id] = material['quantity']

            # Update available quantity
            current_quantity = self._inventory[material['id']].get('quantity', 0)
            self._inventory[material['id']]['quantity'] = current_quantity - material['quantity']

        return True

    def release_reserved_materials(self, project_id: str) -> bool:
        """Release materials reserved for a specific project.

        Args:
            project_id: ID of the project to release reservations for

        Returns:
            bool: True if release successful, False otherwise
        """
        self.logger.debug(f"Releasing reserved materials for project {project_id}")

        # Find all materials reserved for this project
        released_materials = {}

        for material_id, reservations in self._reservations.items():
            if project_id in reservations:
                released_quantity = reservations[project_id]
                released_materials[material_id] = released_quantity

                # Remove reservation
                del reservations[project_id]

                # Update available quantity
                current_quantity = self._inventory[material_id].get('quantity', 0)
                self._inventory[material_id]['quantity'] = current_quantity + released_quantity

        return len(released_materials) > 0

    def update_leather_area(self, leather_id: str, used_area: float) -> bool:
        """Update remaining area of leather after cutting.

        Args:
            leather_id: ID of the leather
            used_area: Area used in square units

        Returns:
            bool: True if update successful, False otherwise
        """
        self.logger.debug(f"Updating leather {leather_id} area, used {used_area} units")

        if leather_id not in self._inventory:
            return False

        leather = self._inventory[leather_id]
        if 'area' not in leather:
            return False

        current_area = leather['area']
        if current_area < used_area:
            return False

        leather['area'] = current_area - used_area
        return True

    def update_part_stock(self, part_id: str, quantity_change: int) -> bool:
        """Update stock level of a part.

        Args:
            part_id: ID of the part
            quantity_change: Amount to change (positive or negative)

        Returns:
            bool: True if update successful, False otherwise
        """
        self.logger.debug(f"Updating part {part_id} stock by {quantity_change}")

        if part_id not in self._inventory:
            return False

        part = self._inventory[part_id]
        current_quantity = part.get('quantity', 0)
        new_quantity = current_quantity + quantity_change

        if new_quantity < 0:
            return False

        part['quantity'] = new_quantity
        return True

    def get_low_stock_leather(self, threshold_area: float = 1.0) -> List[Dict[str, Any]]:
        """Get leather items below specified area threshold.

        Args:
            threshold_area: Area threshold in square units

        Returns:
            List of leather items below threshold
        """
        low_stock = []

        for item_id, item in self._inventory.items():
            if item.get('type') == 'leather' and item.get('area', 0) < threshold_area:
                low_stock.append({
                    'id': item_id,
                    'name': item.get('name', ''),
                    'area': item.get('area', 0),
                    'type': item.get('type', '')
                })

        return low_stock

    # Add to services/implementations/inventory_service.py

    def get_inventory_value(self) -> float:
        """Calculate total inventory value.

        Returns:
            float: Total value of all inventory items
        """
        total_value = 0.0

        for item in self._inventory.values():
            # Calculate based on item type
            if item.get('type') == 'leather':
                # Leather is valued by area
                area = item.get('area', 0)
                price_per_area = item.get('price_per_area', 0.0)
                total_value += area * price_per_area
            else:
                # Other items valued by quantity
                quantity = item.get('quantity', 0)
                unit_price = item.get('unit_price', 0.0)
                total_value += quantity * unit_price

        return total_value

    def get_low_stock_parts(self, threshold_quantity: int = 5) -> List[Dict[str, Any]]:
        """Get parts below specified quantity threshold.

        Args:
            threshold_quantity: Quantity threshold

        Returns:
            List of parts below threshold
        """
        low_stock = []

        for item_id, item in self._inventory.items():
            if item.get('type') != 'leather' and item.get('quantity', 0) < threshold_quantity:
                low_stock.append({
                    'id': item_id,
                    'name': item.get('name', ''),
                    'quantity': item.get('quantity', 0),
                    'type': item.get('type', '')
                })

        return low_stock

    def generate_inventory_report(self) -> Dict[str, Any]:
        """Generate a comprehensive inventory report.

        Returns:
            Dict containing inventory statistics and data
        """
        total_leather_area = 0
        total_parts = 0
        leather_count = 0
        part_types = {}

        for item in self._inventory.values():
            if item.get('type') == 'leather':
                total_leather_area += item.get('area', 0)
                leather_count += 1
            else:
                item_type = item.get('type', 'unknown')
                total_parts += item.get('quantity', 0)

                if item_type not in part_types:
                    part_types[item_type] = 0

                part_types[item_type] += item.get('quantity', 0)

        return {
            'total_leather_area': total_leather_area,
            'leather_count': leather_count,
            'total_parts': total_parts,
            'part_types': part_types,
            'low_stock_leather': self.get_low_stock_leather(),
            'low_stock_parts': self.get_low_stock_parts()
        }