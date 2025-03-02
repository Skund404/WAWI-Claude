# services/interfaces/hardware_service.py
"""
Interface for hardware-related operations.
Defines the contract for hardware management in the leatherworking application.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from database.models.hardware_enums import HardwareType, HardwareMaterial, HardwareFinish
from database.models.enums import InventoryStatus, TransactionType


class IHardwareService(ABC):
    """
    Interface for hardware management service.
    Defines methods for creating, updating, retrieving, and managing hardware items.
    """

    @abstractmethod
    def get_all_hardware(self, include_inactive: bool = False,
                         include_deleted: bool = False) -> List[Dict[str, Any]]:
        """
        Get all hardware items in the inventory.

        Args:
            include_inactive (bool): Whether to include inactive hardware
            include_deleted (bool): Whether to include soft-deleted hardware

        Returns:
            List[Dict[str, Any]]: List of hardware items as dictionaries
        """
        pass

    @abstractmethod
    def get_hardware_by_id(self, hardware_id: str) -> Dict[str, Any]:
        """
        Get a hardware item by its ID.

        Args:
            hardware_id (str): ID of the hardware to retrieve

        Returns:
            Dict[str, Any]: Hardware item as a dictionary

        Raises:
            NotFoundError: If hardware with the specified ID does not exist
        """
        pass

    @abstractmethod
    def create_hardware(self, hardware_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new hardware item.

        Args:
            hardware_data (Dict[str, Any]): Hardware data to create

        Returns:
            Dict[str, Any]: Created hardware item as a dictionary

        Raises:
            ValidationError: If validation fails
        """
        pass

    @abstractmethod
    def update_hardware(self, hardware_id: str, hardware_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing hardware item.

        Args:
            hardware_id (str): ID of the hardware to update
            hardware_data (Dict[str, Any]): Updated hardware data

        Returns:
            Dict[str, Any]: Updated hardware item as a dictionary

        Raises:
            NotFoundError: If hardware with the specified ID does not exist
            ValidationError: If validation fails
        """
        pass

    @abstractmethod
    def delete_hardware(self, hardware_id: str, permanent: bool = False) -> Dict[str, Any]:
        """
        Delete a hardware item (soft delete by default).

        Args:
            hardware_id (str): ID of the hardware to delete
            permanent (bool): Whether to permanently delete the hardware

        Returns:
            Dict[str, Any]: Deleted hardware info or success message

        Raises:
            NotFoundError: If hardware with the specified ID does not exist
        """
        pass

    @abstractmethod
    def restore_hardware(self, hardware_id: str) -> Dict[str, Any]:
        """
        Restore a soft-deleted hardware item.

        Args:
            hardware_id (str): ID of the hardware to restore

        Returns:
            Dict[str, Any]: Restored hardware item as a dictionary

        Raises:
            NotFoundError: If hardware with the specified ID does not exist
        """
        pass

    @abstractmethod
    def adjust_hardware_quantity(self, hardware_id: str, quantity_change: int,
                                 transaction_type: TransactionType, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Adjust the quantity of a hardware item.

        Args:
            hardware_id (str): ID of the hardware to adjust
            quantity_change (int): Amount to change (positive or negative)
            transaction_type (TransactionType): Type of transaction causing the adjustment
            notes (Optional[str]): Optional notes about the adjustment

        Returns:
            Dict[str, Any]: Updated hardware item as a dictionary

        Raises:
            NotFoundError: If hardware with the specified ID does not exist
            ValidationError: If resulting quantity would be negative
        """
        pass

    @abstractmethod
    def search_hardware(self, search_terms: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for hardware items based on criteria.

        Args:
            search_terms (Dict[str, Any]): Search criteria

        Returns:
            List[Dict[str, Any]]: List of matching hardware items as dictionaries
        """
        pass

    @abstractmethod
    def get_hardware_by_type(self, hardware_type: Union[HardwareType, str]) -> List[Dict[str, Any]]:
        """
        Get hardware items of a specific type.

        Args:
            hardware_type (Union[HardwareType, str]): Type of hardware to retrieve

        Returns:
            List[Dict[str, Any]]: List of hardware items as dictionaries
        """
        pass

    @abstractmethod
    def get_hardware_by_material(self, material: Union[HardwareMaterial, str]) -> List[Dict[str, Any]]:
        """
        Get hardware items made of a specific material.

        Args:
            material (Union[HardwareMaterial, str]): Material to filter by

        Returns:
            List[Dict[str, Any]]: List of hardware items as dictionaries
        """
        pass

    @abstractmethod
    def get_low_stock_hardware(self) -> List[Dict[str, Any]]:
        """
        Get hardware items with quantity below reorder threshold.

        Returns:
            List[Dict[str, Any]]: List of low stock hardware items as dictionaries
        """
        pass

    @abstractmethod
    def get_hardware_by_supplier(self, supplier_id: str) -> List[Dict[str, Any]]:
        """
        Get hardware items from a specific supplier.

        Args:
            supplier_id (str): ID of the supplier

        Returns:
            List[Dict[str, Any]]: List of hardware items as dictionaries
        """
        pass

    @abstractmethod
    def get_hardware_by_status(self, status: Union[InventoryStatus, str]) -> List[Dict[str, Any]]:
        """
        Get hardware items with a specific inventory status.

        Args:
            status (Union[InventoryStatus, str]): Inventory status to filter by

        Returns:
            List[Dict[str, Any]]: List of hardware items as dictionaries
        """
        pass

    @abstractmethod
    def get_hardware_stats(self) -> Dict[str, Any]:
        """
        Get statistics about hardware inventory.

        Returns:
            Dict[str, Any]: Dictionary with hardware inventory statistics
        """
        pass