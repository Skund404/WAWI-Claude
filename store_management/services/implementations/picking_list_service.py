# services/implementations/picking_list_service.py
"""
Implementation of Picking List Service that manages picking lists for sales orders.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from database.models.picking_list import PickingList, PickingListItem
from database.models.picking_list import PickingListStatus
from database.repositories.picking_list_repository import PickingListRepository
from database.sqlalchemy.session import get_db_session

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.picking_list_service import IPickingListService


class PickingListService(BaseService, IPickingListService):
    """
    Implementation of the Picking List Service interface that handles picking list operations.
    """

    def __init__(self, picking_list_repository=None):
        """
        Initialize the Picking List Service with a repository.

        Args:
            picking_list_repository: Repository for picking list data access
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        if picking_list_repository:
            self.picking_list_repository = picking_list_repository
        else:
            session = get_db_session()
            self.picking_list_repository = PickingListRepository(session)
            self.session = session

    def get_picking_list(self, picking_list_id: int) -> PickingList:
        """
        Retrieve a picking list by its ID.

        Args:
            picking_list_id: ID of the picking list to retrieve

        Returns:
            PickingList: The retrieved picking list

        Raises:
            NotFoundError: If the picking list does not exist
        """
        try:
            picking_list = self.picking_list_repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")
            return picking_list
        except Exception as e:
            self.logger.error(f"Error retrieving picking list {picking_list_id}: {str(e)}")
            raise NotFoundError(f"Error retrieving picking list: {str(e)}")

    def get_picking_lists(self, **filters) -> List[PickingList]:
        """
        Retrieve picking lists based on optional filters.

        Args:
            **filters: Optional keyword arguments for filtering picking lists

        Returns:
            List[PickingList]: List of picking lists matching the filters
        """
        try:
            return self.picking_list_repository.find_all(**filters)
        except Exception as e:
            self.logger.error(f"Error retrieving picking lists: {str(e)}")
            return []

    def create_picking_list(self, sales_id: int, picking_list_data: Dict[str, Any] = None) -> PickingList:
        """
        Create a new picking list for a sales order with the provided data.

        Args:
            sales_id: ID of the sales order to create a picking list for
            picking_list_data: Additional data for creating the picking list

        Returns:
            PickingList: The created picking list

        Raises:
            ValidationError: If the picking list data is invalid
            NotFoundError: If the sales order does not exist
        """
        try:
            # Initialize picking list data if not provided
            if picking_list_data is None:
                picking_list_data = {}
            
            # Set required fields
            picking_list_data["sales_id"] = sales_id
            if "status" not in picking_list_data:
                picking_list_data["status"] = PickingListStatus.PENDING
            if "created_at" not in picking_list_data:
                picking_list_data["created_at"] = datetime.now()
            
            # Create picking list
            picking_list = PickingList(**picking_list_data)
            return self.picking_list_repository.add(picking_list)
        except Exception as e:
            self.logger.error(f"Error creating picking list for sales order {sales_id}: {str(e)}")
            raise ValidationError(f"Error creating picking list: {str(e)}")

    def update_picking_list(self, picking_list_id: int, picking_list_data: Dict[str, Any]) -> PickingList:
        """
        Update a picking list with the provided data.

        Args:
            picking_list_id: ID of the picking list to update
            picking_list_data: Data for updating the picking list

        Returns:
            PickingList: The updated picking list

        Raises:
            NotFoundError: If the picking list does not exist
            ValidationError: If the picking list data is invalid
        """
        try:
            # Get the picking list
            picking_list = self.get_picking_list(picking_list_id)
            
            # Update picking list fields
            for key, value in picking_list_data.items():
                if hasattr(picking_list, key):
                    setattr(picking_list, key, value)
            
            return self.picking_list_repository.update(picking_list)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating picking list {picking_list_id}: {str(e)}")
            raise ValidationError(f"Error updating picking list: {str(e)}")

    def delete_picking_list(self, picking_list_id: int) -> bool:
        """
        Delete a picking list by its ID.

        Args:
            picking_list_id: ID of the picking list to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            NotFoundError: If the picking list does not exist
        """
        try:
            # Get the picking list
            picking_list = self.get_picking_list(picking_list_id)
            
            # Delete picking list
            self.picking_list_repository.delete(picking_list)
            return True
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting picking list {picking_list_id}: {str(e)}")
            raise NotFoundError(f"Error deleting picking list: {str(e)}")

    def update_picking_list_status(self, picking_list_id: int, status: PickingListStatus) -> PickingList:
        """
        Update the status of a picking list.

        Args:
            picking_list_id: ID of the picking list to update
            status: New status for the picking list

        Returns:
            PickingList: The updated picking list

        Raises:
            NotFoundError: If the picking list does not exist
            ValidationError: If the status transition is invalid
        """
        try:
            # Get the picking list
            picking_list = self.get_picking_list(picking_list_id)
            
            # Validate status transition
            self._validate_status_transition(picking_list.status, status)
            
            # Update status
            picking_list.status = status
            
            # If status is COMPLETED, set the completed_at timestamp
            if status == PickingListStatus.COMPLETED and not picking_list.completed_at:
                picking_list.completed_at = datetime.now()
            
            return self.picking_list_repository.update(picking_list)
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating picking list {picking_list_id} status: {str(e)}")
            raise ValidationError(f"Error updating picking list status: {str(e)}")

    def _validate_status_transition(
        self, current_status: PickingListStatus, new_status: PickingListStatus
    ) -> None:
        """
        Validate if a status transition is allowed.

        Args:
            current_status: Current status of the picking list
            new_status: New status for the picking list

        Raises:
            ValidationError: If the status transition is invalid
        """
        # Define allowed status transitions
        allowed_transitions = {
            PickingListStatus.PENDING: [PickingListStatus.IN_PROGRESS, PickingListStatus.CANCELLED],
            PickingListStatus.IN_PROGRESS: [
                PickingListStatus.COMPLETED, 
                PickingListStatus.CANCELLED, 
                PickingListStatus.ON_HOLD
            ],
            PickingListStatus.ON_HOLD: [PickingListStatus.IN_PROGRESS, PickingListStatus.CANCELLED],
            PickingListStatus.COMPLETED: [PickingListStatus.IN_PROGRESS],  # Allow reopening if needed
            PickingListStatus.CANCELLED: [PickingListStatus.PENDING]  # Allow reactivating cancelled lists
        }
        
        if new_status not in allowed_transitions.get(current_status, []):
            raise ValidationError(
                f"Invalid status transition from {current_status.value} to {new_status.value}"
            )

    def mark_picking_list_completed(self, picking_list_id: int) -> PickingList:
        """
        Mark a picking list as completed.

        Args:
            picking_list_id: ID of the picking list to mark as completed

        Returns:
            PickingList: The updated picking list

        Raises:
            NotFoundError: If the picking list does not exist
            ValidationError: If the picking list cannot be marked as completed
        """
        try:
            # Get the picking list
            picking_list = self.get_picking_list(picking_list_id)
            
            # Check if all items have been picked
            for item in picking_list.items:
                if item.quantity_picked < item.quantity_ordered:
                    raise ValidationError(
                        "Cannot mark picking list as completed: "
                        "Not all items have been fully picked"
                    )
            
            # Update status to COMPLETED
            return self.update_picking_list_status(picking_list_id, PickingListStatus.COMPLETED)
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error marking picking list {picking_list_id} as completed: {str(e)}")
            raise ValidationError(f"Error marking picking list as completed: {str(e)}")

    def get_picking_list_items(self, picking_list_id: int) -> List[PickingListItem]:
        """
        Retrieve items in a picking list.

        Args:
            picking_list_id: ID of the picking list

        Returns:
            List[PickingListItem]: List of items in the picking list

        Raises:
            NotFoundError: If the picking list does not exist
        """
        try:
            # Get the picking list to ensure it exists
            picking_list = self.get_picking_list(picking_list_id)
            
            # Return its items
            return picking_list.items
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving items for picking list {picking_list_id}: {str(e)}")
            raise NotFoundError(f"Error retrieving picking list items: {str(e)}")

    def add_item_to_picking_list(
        self, picking_list_id: int, item_data: Dict[str, Any]
    ) -> PickingListItem:
        """
        Add an item to a picking list.

        Args:
            picking_list_id: ID of the picking list
            item_data: Data for the item to add (component_id, material_id, leather_id, hardware_id, etc.)

        Returns:
            PickingListItem: The created picking list item

        Raises:
            NotFoundError: If the picking list does not exist
            ValidationError: If the item data is invalid
        """
        try:
            # Get the picking list to ensure it exists
            picking_list = self.get_picking_list(picking_list_id)
            
            # Validate item data
            if "quantity_ordered" not in item_data or item_data["quantity_ordered"] <= 0:
                raise ValidationError("Quantity ordered must be greater than zero")
            
            # Set default values
            if "quantity_picked" not in item_data:
                item_data["quantity_picked"] = 0
            
            # Set picking list ID
            item_data["picking_list_id"] = picking_list_id
            
            # Create item
            item = PickingListItem(**item_data)
            self.session.add(item)
            self.session.commit()
            
            return item
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error adding item to picking list {picking_list_id}: {str(e)}")
            self.session.rollback()
            raise ValidationError(f"Error adding item to picking list: {str(e)}")

    def update_picking_list_item(
        self, picking_list_id: int, item_id: int, item_data: Dict[str, Any]
    ) -> PickingListItem:
        """
        Update a picking list item.

        Args:
            picking_list_id: ID of the picking list
            item_id: ID of the item to update
            item_data: Data for updating the item

        Returns:
            PickingListItem: The updated picking list item

        Raises:
            NotFoundError: If the picking list or item does not exist
            ValidationError: If the item data is invalid
        """
        try:
            # Get the picking list to ensure it exists
            picking_list = self.get_picking_list(picking_list_id)
            
            # Find the item
            item = None
            for list_item in picking_list.items:
                if list_item.id == item_id:
                    item = list_item
                    break
            
            if not item:
                raise NotFoundError(f"Picking list item with ID {item_id} not found")
            
            # Validate quantity_ordered if it's being updated
            if "quantity_ordered" in item_data and item_data["quantity_ordered"] <= 0:
                raise ValidationError("Quantity ordered must be greater than zero")
            
            # Validate quantity_picked if it's being updated
            if "quantity_picked" in item_data:
                if item_data["quantity_picked"] < 0:
                    raise ValidationError("Quantity picked cannot be negative")
                
                # Get the current or updated quantity_ordered value
                quantity_ordered = (
                    item_data.get("quantity_ordered", item.quantity_ordered)
                )
                
                if item_data["quantity_picked"] > quantity_ordered:
                    raise ValidationError(
                        "Quantity picked cannot exceed quantity ordered"
                    )
            
            # Update item fields
            for key, value in item_data.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            
            # Commit changes
            self.session.commit()
            
            return item
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating picking list item {item_id}: {str(e)}")
            self.session.rollback()
            raise ValidationError(f"Error updating picking list item: {str(e)}")

    def remove_item_from_picking_list(self, picking_list_id: int, item_id: int) -> bool:
        """
        Remove an item from a picking list.

        Args:
            picking_list_id: ID of the picking list
            item_id: ID of the item to remove

        Returns:
            bool: True if the item was removed successfully

        Raises:
            NotFoundError: If the picking list or item does not exist
        """
        try:
            # Get the picking list to ensure it exists
            picking_list = self.get_picking_list(picking_list_id)
            
            # Find the item
            item = None
            for list_item in picking_list.items:
                if list_item.id == item_id:
                    item = list_item
                    break
            
            if not item:
                raise NotFoundError(f"Picking list item with ID {item_id} not found")
            
            # Remove the item
            self.session.delete(item)
            self.session.commit()
            
            return True
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error removing item from picking list {picking_list_id}: {str(e)}")
            self.session.rollback()
            raise NotFoundError(f"Error removing item from picking list: {str(e)}")

    def update_item_quantities(
        self, picking_list_id: int, item_id: int, quantity_picked: int
    ) -> PickingListItem:
        """
        Update the quantities of a picking list item.

        Args:
            picking_list_id: ID of the picking list
            item_id: ID of the item to update
            quantity_picked: The quantity that has been picked

        Returns:
            PickingListItem: The updated picking list item

        Raises:
            NotFoundError: If the picking list or item does not exist
            ValidationError: If the quantity is invalid
        """
        try:
            # Get the picking list to ensure it exists
            picking_list = self.get_picking_list(picking_list_id)
            
            # Find the item
            item = None
            for list_item in picking_list.items:
                if list_item.id == item_id:
                    item = list_item
                    break
            
            if not item:
                raise NotFoundError(f"Picking list item with ID {item_id} not found")
            
            # Validate quantity
            if quantity_picked < 0:
                raise ValidationError("Quantity picked cannot be negative")
            
            if quantity_picked > item.quantity_ordered:
                raise ValidationError("Quantity picked cannot exceed quantity ordered")
            
            # Update quantity
            item.quantity_picked = quantity_picked
            self.session.commit()
            
            return item
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating item quantities in picking list {picking_list_id}: {str(e)}")
            self.session.rollback()
            raise ValidationError(f"Error updating item quantities: {str(e)}")

    def get_picking_lists_by_sales_order(self, sales_id: int) -> List[PickingList]:
        """
        Retrieve picking lists for a specific sales order.

        Args:
            sales_id: ID of the sales order

        Returns:
            List[PickingList]: List of picking lists for the sales order
        """
        try:
            return self.picking_list_repository.find_all(sales_id=sales_id)
        except Exception as e:
            self.logger.error(f"Error retrieving picking lists for sales order {sales_id}: {str(e)}")
            return []