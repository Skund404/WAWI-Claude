# store_management/services/interfaces/hardware_service.py
"""
Interface for Hardware Service in Leatherworking Store Management.

Defines the contract for hardware-related operations.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from di.core import inject
from utils.circular_import_resolver import CircularImportResolver

class HardwareType(Enum):
    """
    Enumeration of possible hardware types in leatherworking.
    """
    BUCKLE = "Buckle"
    SNAP = "Snap"
    RIVET = "Rivet"
    ZIPPER = "Zipper"
    CLASP = "Clasp"
    BUTTON = "Button"
    D_RING = "D-Ring"
    O_RING = "O-Ring"
    MAGNETIC_CLOSURE = "Magnetic Closure"
    OTHER = "Other"

class HardwareMaterial(Enum):
    """
    Enumeration of possible hardware materials.
    """
    BRASS = "Brass"
    STEEL = "Steel"
    STAINLESS_STEEL = "Stainless Steel"
    NICKEL = "Nickel"
    SILVER = "Silver"
    GOLD = "Gold"
    BRONZE = "Bronze"
    ALUMINUM = "Aluminum"
    PLASTIC = "Plastic"
    OTHER = "Other"

class IHardwareService(ABC):
    """
    Abstract base class defining the interface for hardware-related operations.
    """

    @abstractmethod
    @inject('IMaterialService')
    @inject('IInventoryService')
    def create_hardware(
        self,
        name: str,
        hardware_type: HardwareType,
        material: HardwareMaterial,
        quantity: float = 1.0,
        description: Optional[str] = None,
        material_service: Optional[Any] = None,
        inventory_service: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Create a new hardware item.

        Args:
            name (str): Name of the hardware item
            hardware_type (HardwareType): Type of hardware
            material (HardwareMaterial): Material of the hardware
            quantity (float, optional): Quantity of the hardware. Defaults to 1.0
            description (Optional[str], optional): Description of the hardware
            material_service (Optional[Any], optional): Material service for additional operations
            inventory_service (Optional[Any], optional): Inventory service for tracking

        Returns:
            Dict[str, Any]: Details of the created hardware item
        """
        pass

    @abstractmethod
    def update_hardware(
        self,
        hardware_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing hardware item.

        Args:
            hardware_id (str): Unique identifier of the hardware item
            updates (Dict[str, Any]): Dictionary of fields to update

        Returns:
            Dict[str, Any]: Updated hardware item details
        """
        pass

    @abstractmethod
    def get_hardware(
        self,
        hardware_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific hardware item by its ID.

        Args:
            hardware_id (str): Unique identifier of the hardware item

        Returns:
            Optional[Dict[str, Any]]: Hardware item details, or None if not found
        """
        pass

    @abstractmethod
    def list_hardware(
        self,
        hardware_type: Optional[HardwareType] = None,
        material: Optional[HardwareMaterial] = None
    ) -> List[Dict[str, Any]]:
        """
        List hardware items with optional filtering.

        Args:
            hardware_type (Optional[HardwareType], optional): Filter by hardware type
            material (Optional[HardwareMaterial], optional): Filter by material

        Returns:
            List[Dict[str, Any]]: List of hardware items matching the criteria
        """
        pass

    @abstractmethod
    def delete_hardware(
        self,
        hardware_id: str
    ) -> bool:
        """
        Delete a hardware item.

        Args:
            hardware_id (str): Unique identifier of the hardware item to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    @inject('IInventoryService')
    def check_hardware_availability(
        self,
        hardware_id: str,
        required_quantity: float,
        inventory_service: Optional[Any] = None
    ) -> bool:
        """
        Check if a specific quantity of hardware is available.

        Args:
            hardware_id (str): Unique identifier of the hardware item
            required_quantity (float): Quantity to check for availability
            inventory_service (Optional[Any], optional): Inventory service for checking

        Returns:
            bool: True if the required quantity is available, False otherwise
        """
        pass