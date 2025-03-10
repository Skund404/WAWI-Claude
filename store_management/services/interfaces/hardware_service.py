# services/interfaces/hardware_service.py
from typing import Dict, List, Any, Optional, Protocol


class IHardwareService(Protocol):
    """Interface for the Hardware Service.

    The Hardware Service handles specialized operations for hardware materials
    used in leatherworking projects, such as buckles, rivets, snaps, etc.
    """

    def get_by_id(self, hardware_id: int) -> Dict[str, Any]:
        """Retrieve a hardware item by its ID.

        Args:
            hardware_id: The ID of the hardware to retrieve

        Returns:
            A dictionary representation of the hardware

        Raises:
            NotFoundError: If the hardware with the given ID does not exist
        """
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve all hardware items with optional filtering.

        Args:
            filters: Optional filters to apply to the hardware query

        Returns:
            List of dictionaries representing hardware items
        """
        ...

    def create(self, hardware_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new hardware item.

        Args:
            hardware_data: Dictionary containing hardware data

        Returns:
            Dictionary representation of the created hardware

        Raises:
            ValidationError: If the hardware data is invalid
        """
        ...

    def update(self, hardware_id: int, hardware_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing hardware item.

        Args:
            hardware_id: ID of the hardware to update
            hardware_data: Dictionary containing updated hardware data

        Returns:
            Dictionary representation of the updated hardware

        Raises:
            NotFoundError: If the hardware with the given ID does not exist
            ValidationError: If the updated data is invalid
        """
        ...

    def delete(self, hardware_id: int) -> bool:
        """Delete a hardware item by its ID.

        Args:
            hardware_id: ID of the hardware to delete

        Returns:
            True if the hardware was successfully deleted

        Raises:
            NotFoundError: If the hardware with the given ID does not exist
            ServiceError: If the hardware cannot be deleted (e.g., in use)
        """
        ...

    def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Find hardware items by name (partial match).

        Args:
            name: Name or partial name to search for

        Returns:
            List of dictionaries representing matching hardware items
        """
        ...

    def find_by_type(self, hardware_type: str) -> List[Dict[str, Any]]:
        """Find hardware items by type.

        Args:
            hardware_type: Hardware type to filter by

        Returns:
            List of dictionaries representing hardware of the specified type
        """
        ...

    def find_by_material(self, material: str) -> List[Dict[str, Any]]:
        """Find hardware items by material.

        Args:
            material: Material type to filter by

        Returns:
            List of dictionaries representing hardware made of the specified material
        """
        ...

    def find_by_finish(self, finish: str) -> List[Dict[str, Any]]:
        """Find hardware items by finish.

        Args:
            finish: Finish type to filter by

        Returns:
            List of dictionaries representing hardware with the specified finish
        """
        ...

    def get_by_size(self, size: str) -> List[Dict[str, Any]]:
        """Find hardware items by size.

        Args:
            size: Size to filter by

        Returns:
            List of dictionaries representing hardware of the specified size
        """
        ...

    def get_inventory_status(self, hardware_id: int) -> Dict[str, Any]:
        """Get the current inventory status of a hardware item.

        Args:
            hardware_id: ID of the hardware

        Returns:
            Dictionary containing inventory information

        Raises:
            NotFoundError: If the hardware does not exist
        """
        ...

    def adjust_inventory(self, hardware_id: int,
                         quantity: int,
                         reason: str) -> Dict[str, Any]:
        """Adjust the inventory of a hardware item.

        Args:
            hardware_id: ID of the hardware
            quantity: Quantity to adjust (positive or negative)
            reason: Reason for the adjustment

        Returns:
            Dictionary containing updated inventory information

        Raises:
            NotFoundError: If the hardware does not exist
            ValidationError: If the adjustment would result in negative inventory
        """
        ...

    def get_components_using(self, hardware_id: int) -> List[Dict[str, Any]]:
        """Get components that use a specific hardware item.

        Args:
            hardware_id: ID of the hardware

        Returns:
            List of dictionaries representing components that use the hardware

        Raises:
            NotFoundError: If the hardware does not exist
        """
        ...

    def get_usage_history(self, hardware_id: int,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get the usage history for a hardware item.

        Args:
            hardware_id: ID of the hardware
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)

        Returns:
            List of dictionaries containing usage records

        Raises:
            NotFoundError: If the hardware does not exist
        """
        ...

    def get_compatible_hardware(self, hardware_id: int) -> List[Dict[str, Any]]:
        """Get hardware items that are compatible with the specified hardware.

        Args:
            hardware_id: ID of the hardware

        Returns:
            List of dictionaries representing compatible hardware items

        Raises:
            NotFoundError: If the hardware does not exist
        """
        ...

    def set_compatibility(self, hardware_id: int,
                          compatible_id: int,
                          is_compatible: bool = True) -> bool:
        """Set compatibility between two hardware items.

        Args:
            hardware_id: ID of the first hardware item
            compatible_id: ID of the second hardware item
            is_compatible: Whether the items are compatible

        Returns:
            True if the compatibility was successfully set

        Raises:
            NotFoundError: If either hardware item does not exist
        """
        ...