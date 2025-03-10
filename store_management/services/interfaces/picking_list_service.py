# services/interfaces/picking_list_service.py
from typing import Dict, List, Any, Optional, Protocol


class IPickingListService(Protocol):
    """Interface for the PickingList Service.

    The PickingList Service manages material picking lists for projects,
    tracks picking progress, and validates inventory availability.
    """

    def get_by_id(self, picking_list_id: int) -> Dict[str, Any]:
        """Retrieve a picking list by its ID.

        Args:
            picking_list_id: The ID of the picking list to retrieve

        Returns:
            A dictionary representation of the picking list

        Raises:
            NotFoundError: If the picking list with the given ID does not exist
        """
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve all picking lists with optional filtering.

        Args:
            filters: Optional filters to apply to the picking list query

        Returns:
            List of dictionaries representing picking lists
        """
        ...

    def create_for_project(self, project_id: int, notes: Optional[str] = None) -> Dict[str, Any]:
        """Create a new picking list for a project.

        Args:
            project_id: ID of the project
            notes: Optional notes about the picking list

        Returns:
            Dictionary representation of the created picking list

        Raises:
            NotFoundError: If the project does not exist
            ValidationError: If the project has no components
            ServiceError: If a picking list already exists for the project
        """
        ...

    def update(self, picking_list_id: int, picking_list_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing picking list.

        Args:
            picking_list_id: ID of the picking list to update
            picking_list_data: Dictionary containing updated picking list data

        Returns:
            Dictionary representation of the updated picking list

        Raises:
            NotFoundError: If the picking list with the given ID does not exist
            ValidationError: If the updated data is invalid
        """
        ...

    def delete(self, picking_list_id: int) -> bool:
        """Delete a picking list by its ID.

        Args:
            picking_list_id: ID of the picking list to delete

        Returns:
            True if the picking list was successfully deleted

        Raises:
            NotFoundError: If the picking list with the given ID does not exist
            ServiceError: If the picking list cannot be deleted (e.g., in progress)
        """
        ...

    def get_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Get picking lists for a specific project.

        Args:
            project_id: ID of the project

        Returns:
            List of dictionaries representing picking lists for the project

        Raises:
            NotFoundError: If the project does not exist
        """
        ...

    def get_picking_list_items(self, picking_list_id: int) -> List[Dict[str, Any]]:
        """Get all items in a picking list.

        Args:
            picking_list_id: ID of the picking list

        Returns:
            List of dictionaries representing picking list items

        Raises:
            NotFoundError: If the picking list does not exist
        """
        ...

    def add_item(self, picking_list_id: int,
                 material_id: int,
                 component_id: Optional[int] = None,
                 quantity: float = 1.0) -> Dict[str, Any]:
        """Add an item to a picking list.

        Args:
            picking_list_id: ID of the picking list
            material_id: ID of the material
            component_id: Optional ID of the component using the material
            quantity: Quantity of the material needed

        Returns:
            Dictionary representing the added picking list item

        Raises:
            NotFoundError: If the picking list or material does not exist
            ValidationError: If the quantity is invalid
        """
        ...

    def remove_item(self, picking_list_id: int, item_id: int) -> bool:
        """Remove an item from a picking list.

        Args:
            picking_list_id: ID of the picking list
            item_id: ID of the picking list item

        Returns:
            True if the item was successfully removed

        Raises:
            NotFoundError: If the picking list or item does not exist
            ServiceError: If the item cannot be removed (e.g., already picked)
        """
        ...

    def update_item_quantity(self, picking_list_id: int,
                             item_id: int,
                             quantity: float) -> Dict[str, Any]:
        """Update the quantity of an item in a picking list.

        Args:
            picking_list_id: ID of the picking list
            item_id: ID of the picking list item
            quantity: New quantity of the material needed

        Returns:
            Dictionary representing the updated picking list item

        Raises:
            NotFoundError: If the picking list or item does not exist
            ValidationError: If the quantity is invalid
        """
        ...

    def record_picking(self, picking_list_id: int,
                       item_id: int,
                       quantity_picked: float,
                       notes: Optional[str] = None) -> Dict[str, Any]:
        """Record picking of an item.

        Args:
            picking_list_id: ID of the picking list
            item_id: ID of the picking list item
            quantity_picked: Quantity picked
            notes: Optional notes about the picking

        Returns:
            Dictionary representing the updated picking list item

        Raises:
            NotFoundError: If the picking list or item does not exist
            ValidationError: If the quantity is invalid
            ServiceError: If insufficient inventory is available
        """
        ...

    def complete_picking_list(self, picking_list_id: int,
                              notes: Optional[str] = None) -> Dict[str, Any]:
        """Mark a picking list as complete.

        Args:
            picking_list_id: ID of the picking list
            notes: Optional notes about the completion

        Returns:
            Dictionary representing the updated picking list

        Raises:
            NotFoundError: If the picking list does not exist
            ValidationError: If not all items have been picked
        """
        ...

    def cancel_picking_list(self, picking_list_id: int,
                            reason: str) -> Dict[str, Any]:
        """Cancel a picking list.

        Args:
            picking_list_id: ID of the picking list
            reason: Reason for cancellation

        Returns:
            Dictionary representing the updated picking list

        Raises:
            NotFoundError: If the picking list does not exist
            ServiceError: If the picking list cannot be cancelled
        """
        ...

    def validate_inventory(self, picking_list_id: int) -> Dict[str, Any]:
        """Validate that sufficient inventory exists for all items in a picking list.

        Args:
            picking_list_id: ID of the picking list

        Returns:
            Dictionary with validation results

        Raises:
            NotFoundError: If the picking list does not exist
        """
        ...