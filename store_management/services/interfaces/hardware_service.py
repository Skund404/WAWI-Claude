# relative path: store_management/services/interfaces/hardware_service.py
"""
Hardware Service Interface for the Leatherworking Store Management application.

Defines the contract for hardware-related service operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from database.models.hardware import Hardware, HardwareType, HardwareMaterial, HardwareFinish

class IHardwareService(ABC):
    """
    Interface defining hardware service operations.
    """

    @abstractmethod
    def get_low_stock_hardware(self, include_zero_stock: bool = False) -> List[Hardware]:
        """
        Retrieve hardware items with low stock.

        Args:
            include_zero_stock (bool): Whether to include hardware with zero stock

        Returns:
            List[Hardware]: Hardware items below minimum stock level
        """
        pass

    @abstractmethod
    def get_hardware_by_supplier(self, supplier_id: int) -> List[Hardware]:
        """
        Retrieve hardware items from a specific supplier.

        Args:
            supplier_id (int): Supplier identifier

        Returns:
            List[Hardware]: Hardware items from the specified supplier
        """
        pass

    @abstractmethod
    def generate_hardware_performance_report(self) -> List[Dict[str, Any]]:
        """
        Generate a performance report for hardware items.

        Returns:
            List[Dict[str, Any]]: Performance metrics for hardware
        """
        pass

    @abstractmethod
    def search_hardware(
        self,
        hardware_type: Optional[HardwareType] = None,
        material: Optional[HardwareMaterial] = None,
        finish: Optional[HardwareFinish] = None,
        min_stock: Optional[int] = None,
        max_stock: Optional[int] = None,
        min_load_capacity: Optional[float] = None,
        max_load_capacity: Optional[float] = None
    ) -> List[Hardware]:
        """
        Advanced search for hardware with multiple filtering options.

        Args:
            hardware_type (Optional[HardwareType]): Filter by hardware type
            material (Optional[HardwareMaterial]): Filter by material
            finish (Optional[HardwareFinish]): Filter by finish
            min_stock (Optional[int]): Minimum current stock
            max_stock (Optional[int]): Maximum current stock
            min_load_capacity (Optional[float]): Minimum load capacity
            max_load_capacity (Optional[float]): Maximum load capacity

        Returns:
            List[Hardware]: Matching hardware items
        """
        pass