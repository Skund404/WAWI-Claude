# Path: services/interfaces/hardware_service.py

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from database.models.hardware import Hardware
from database.base import BaseModel


class IHardwareService(ABC):
    """
    Interface for Hardware Service in the Leatherworking Management System.
    Defines the contract for hardware-related operations.
    """

    @abstractmethod
    def create_hardware(self, hardware_data: Dict[str, Any]) -> Hardware:
        """
        Create a new hardware item.

        Args:
            hardware_data (Dict[str, Any]): Hardware creation data

        Returns:
            Hardware: Created hardware instance
        """
        pass

    @abstractmethod
    def get_hardware(self, hardware_id: int) -> Optional[Hardware]:
        """
        Retrieve a hardware item by ID.

        Args:
            hardware_id (int): Hardware identifier

        Returns:
            Optional[Hardware]: Retrieved hardware
        """
        pass

    @abstractmethod
    def update_hardware(self, hardware_id: int, update_data: Dict[str, Any]) -> Optional[Hardware]:
        """
        Update an existing hardware item.

        Args:
            hardware_id (int): Hardware identifier
            update_data (Dict[str, Any]): Data to update

        Returns:
            Optional[Hardware]: Updated hardware
        """
        pass

    @abstractmethod
    def delete_hardware(self, hardware_id: int) -> bool:
        """
        Delete a hardware item.

        Args:
            hardware_id (int): Hardware identifier

        Returns:
            bool: Success of deletion
        """
        pass

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
    def generate_hardware_performance_report(self) -> List[Dict[str, Any]]:
        """
        Generate a performance report for hardware items.

        Returns:
            List[Dict[str, Any]]: Performance metrics for hardware
        """
        pass