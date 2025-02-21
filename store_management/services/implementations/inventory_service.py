# store_management/services/implementations/inventory_service.py
from typing import List, Optional, Dict, Any, Tuple, Type, cast
from datetime import datetime

from store_management.di.service import Service
from store_management.di.container import DependencyContainer
from store_management.services.interfaces.inventory_service import IInventoryService
from store_management.database.sqlalchemy.base_manager import BaseManager
from store_management.database.sqlalchemy.models.part import Part
from store_management.database.sqlalchemy.models.leather import Leather
from store_management.database.sqlalchemy.models.enums import InventoryStatus, TransactionType


class InventoryService(Service, IInventoryService):
    """Service for inventory management operations."""

    def __init__(self, container: DependencyContainer):
        """Initialize service with appropriate managers."""
        super().__init__(container)
        self._part_manager = self.get_dependency(BaseManager[Part])
        self._leather_manager = self.get_dependency(BaseManager[Leather])

    def update_part_stock(self, part_id: int, quantity_change: int,
                          transaction_type: str, notes: Optional[str] = None) -> Tuple[bool, str]:
        """
        Update part stock with transaction tracking.

        Args:
            part_id: Part ID
            quantity_change: Change in quantity (positive or negative)
            transaction_type: Type of transaction
            notes: Optional notes

        Returns:
            Tuple of (success, message)
        """
        try:
            # Get the part
            part = self._part_manager.get(part_id)
            if not part:
                return False, f"Part with ID {part_id} not found"

            # Check if quantity would go negative
            if part.quantity + quantity_change < 0:
                return False, "Cannot reduce stock below zero"

            # Update the part quantity
            part.quantity += quantity_change

            # Update status based on new quantity
            if part.quantity <= 0:
                part.status = InventoryStatus.OUT_OF_STOCK
            elif part.quantity <= part.minimum_stock:
                part.status = InventoryStatus.LOW_STOCK
            else:
                part.status = InventoryStatus.IN_STOCK

            # Create transaction record
            transaction_data = {
                "part_id": part_id,
                "quantity_change": quantity_change,
                "type": transaction_type,
                "notes": notes or "",
                "timestamp": datetime.now()
            }

            # In a real implementation, we'd have a transaction manager
            # For now, we'll just update the part
            self._part_manager.update(part_id, {
                "quantity": part.quantity,
                "status": part.status
            })

            return True, f"Updated part stock, new quantity: {part.quantity}"

        except Exception as e:
            return False, f"Error updating part stock: {str(e)}"

    def update_leather_area(self, leather_id: int, area_change: float,
                            transaction_type: str, notes: Optional[str] = None,
                            wastage: Optional[float] = None) -> Tuple[bool, str]:
        """
        Update leather area with transaction tracking.

        Args:
            leather_id: Leather ID
            area_change: Change in area (positive or negative)
            transaction_type: Type of transaction
            notes: Optional notes
            wastage: Optional wastage area

        Returns:
            Tuple of (success, message)
        """
        try:
            # Get the leather
            leather = self._leather_manager.get(leather_id)
            if not leather:
                return False, f"Leather with ID {leather_id} not found"

            # Check if area would go negative
            if leather.area + area_change < 0:
                return False, "Cannot reduce area below zero"

            # Update the leather area
            leather.area += area_change

            # Update status based on new area
            if leather.area <= 0:
                leather.status = InventoryStatus.OUT_OF_STOCK
            elif leather.area <= leather.minimum_area:
                leather.status = InventoryStatus.LOW_STOCK
            else:
                leather.status = InventoryStatus.IN_STOCK

            # Create transaction record
            transaction_data = {
                "leather_id": leather_id,
                "area_change": area_change,
                "type": transaction_type,
                "notes": notes or "",
                "wastage": wastage or 0.0,
                "timestamp": datetime.now()
            }

            # In a real implementation, we'd have a transaction manager
            # For now, we'll just update the leather
            self._leather_manager.update(leather_id, {
                "area": leather.area,
                "status": leather.status
            })

            return True, f"Updated leather area, new area: {leather.area}"

        except Exception as e:
            return False, f"Error updating leather area: {str(e)}"

    def get_low_stock_parts(self, include_out_of_stock: bool = True) -> List[Dict[str, Any]]:
        """
        Get parts with low stock levels.

        Args:
            include_out_of_stock: Whether to include out of stock items

        Returns:
            List of parts with low stock
        """
        try:
            # In a real implementation, we'd use a specialized query
            # For simplicity, we'll filter all parts
            all_parts = self._part_manager.get_all()
            low_stock_parts = []

            for part in all_parts:
                if part.status == InventoryStatus.LOW_STOCK or \
                        (include_out_of_stock and part.status == InventoryStatus.OUT_OF_STOCK):
                    low_stock_parts.append(self._part_to_dict(part))

            return low_stock_parts

        except Exception as e:
            # Log the error
            print(f"Error getting low stock parts: {str(e)}")
            return []

    def get_low_stock_leather(self, include_out_of_stock: bool = True) -> List[Dict[str, Any]]:
        """
        Get leather with low stock levels.

        Args:
            include_out_of_stock: Whether to include out of stock items

        Returns:
            List of leather with low stock
        """
        try:
            # In a real implementation, we'd use a specialized query
            # For simplicity, we'll filter all leather
            all_leather = self._leather_manager.get_all()
            low_stock_leather = []

            for leather in all_leather:
                if leather.status == InventoryStatus.LOW_STOCK or \
                        (include_out_of_stock and leather.status == InventoryStatus.OUT_OF_STOCK):
                    low_stock_leather.append(self._leather_to_dict(leather))

            return low_stock_leather

        except Exception as e:
            # Log the error
            print(f"Error getting low stock leather: {str(e)}")
            return []

    def _part_to_dict(self, part: Part) -> Dict[str, Any]:
        """Convert Part model to dictionary."""
        return {
            "id": part.id,
            "name": part.name,
            "description": part.description,
            "quantity": part.quantity,
            "minimum_stock": part.minimum_stock,
            "status": part.status.name if hasattr(part.status, 'name') else str(part.status),
            "supplier_id": part.supplier_id,
            "unit_price": part.unit_price
        }

    def _leather_to_dict(self, leather: Leather) -> Dict[str, Any]:
        """Convert Leather model to dictionary."""
        return {
            "id": leather.id,
            "name": leather.name,
            "description": leather.description,
            "area": leather.area,
            "minimum_area": leather.minimum_area,
            "status": leather.status.name if hasattr(leather.status, 'name') else str(leather.status),
            "supplier_id": leather.supplier_id,
            "unit_price": leather.unit_price,
            "color": leather.color,
            "thickness": leather.thickness
        }