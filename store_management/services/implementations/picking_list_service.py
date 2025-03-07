"""
services/implementations/picking_list_service.py
Implementation of the picking list service for the leatherworking application.
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from database.models.picking_list import PickingList, PickingListItem
from database.models.picking_list import PickingListStatus
from database.repositories.picking_list_repository import PickingListRepository
from database.sqlalchemy.session import get_db_session

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.picking_list_service import IPickingListService


class PickingListService(BaseService, IPickingListService):
    """Service implementation for managing picking lists."""

    def __init__(self, picking_list_repository=None):
        """
        Initialize the Picking List Service with a repository.

        Args:
            picking_list_repository: Repository for picking list data access
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # Initialize repository, creating a new one if not provided
        if picking_list_repository is None:
            session = get_db_session()
            self.repository = PickingListRepository(session)
        else:
            self.repository = picking_list_repository

    def create_picking_list(self, sales_id: int, **kwargs) -> Dict[str, Any]:
        """
        Create a new picking list for a sales order.

        Args:
            sales_id: ID of the associated sales record
            **kwargs: Additional picking list attributes

        Returns:
            Dict containing the created picking list data

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Set defaults for new picking list
            data = {
                "sales_id": sales_id,
                "status": PickingListStatus.DRAFT,
                "created_at": datetime.now(),
                **kwargs
            }

            self.logger.info(f"Creating picking list for sales_id={sales_id}")

            # Create the picking list through the repository
            picking_list = self.repository.create(data)

            # Return the serialized picking list
            return self._serialize_picking_list(picking_list)
        except Exception as e:
            self.logger.error(f"Error creating picking list: {str(e)}")
            raise ValidationError(f"Failed to create picking list: {str(e)}")

    def get_picking_list(self, picking_list_id: int) -> Dict[str, Any]:
        """
        Get a picking list by ID.

        Args:
            picking_list_id: ID of the picking list to retrieve

        Returns:
            Dict containing the picking list data

        Raises:
            NotFoundError: If the picking list doesn't exist
        """
        try:
            picking_list = self.repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            return self._serialize_picking_list(picking_list)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving picking list {picking_list_id}: {str(e)}")
            raise ServiceError(f"Failed to retrieve picking list: {str(e)}")

    def get_picking_lists(self,
                         status: Optional[PickingListStatus] = None,
                         sales_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get picking lists with optional filtering.

        Args:
            status: Filter by picking list status
            sales_id: Filter by associated sales ID

        Returns:
            List of picking list dictionaries
        """
        try:
            filters = {}
            if status:
                filters["status"] = status
            if sales_id:
                filters["sales_id"] = sales_id

            picking_lists = self.repository.get_all_by_filter(**filters)
            return [self._serialize_picking_list(pl) for pl in picking_lists]
        except Exception as e:
            self.logger.error(f"Error retrieving picking lists: {str(e)}")
            return []

    def update_picking_list(self,
                           picking_list_id: int,
                           **kwargs) -> Dict[str, Any]:
        """
        Update a picking list's attributes.

        Args:
            picking_list_id: ID of the picking list to update
            **kwargs: Attributes to update

        Returns:
            Dict containing the updated picking list

        Raises:
            NotFoundError: If the picking list doesn't exist
            ValidationError: If update validation fails
        """
        try:
            picking_list = self.repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Remove any attributes that shouldn't be directly updated
            for key in ["id", "created_at"]:
                if key in kwargs:
                    del kwargs[key]

            self.logger.info(f"Updating picking list {picking_list_id} with {kwargs}")
            updated_picking_list = self.repository.update(picking_list_id, kwargs)
            return self._serialize_picking_list(updated_picking_list)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating picking list {picking_list_id}: {str(e)}")
            raise ValidationError(f"Failed to update picking list: {str(e)}")

    def update_status(self,
                     picking_list_id: int,
                     status: PickingListStatus) -> Dict[str, Any]:
        """
        Update the status of a picking list.

        Args:
            picking_list_id: ID of the picking list
            status: New status value

        Returns:
            Dict containing the updated picking list

        Raises:
            NotFoundError: If the picking list doesn't exist
            ValidationError: If status transition is invalid
        """
        try:
            picking_list = self.repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Validate status transition
            self._validate_status_transition(picking_list.status, status)

            update_data = {"status": status}

            # If completing the picking list, set the completed_at timestamp
            if status == PickingListStatus.COMPLETED:
                update_data["completed_at"] = datetime.now()

            self.logger.info(f"Updating picking list {picking_list_id} status to {status}")
            updated_picking_list = self.repository.update(picking_list_id, update_data)
            return self._serialize_picking_list(updated_picking_list)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating picking list status: {str(e)}")
            raise ValidationError(f"Failed to update picking list status: {str(e)}")

    def add_item(self,
                picking_list_id: int,
                component_id: Optional[int] = None,
                material_id: Optional[int] = None,
                leather_id: Optional[int] = None,
                hardware_id: Optional[int] = None,
                quantity_ordered: int = 1) -> Dict[str, Any]:
        """
        Add an item to a picking list.

        Args:
            picking_list_id: ID of the picking list
            component_id: ID of the component (optional)
            material_id: ID of the material (optional)
            leather_id: ID of the leather (optional)
            hardware_id: ID of the hardware (optional)
            quantity_ordered: Quantity of the item ordered

        Returns:
            Dict containing the created picking list item

        Raises:
            NotFoundError: If the picking list doesn't exist
            ValidationError: If item validation fails
        """
        try:
            # Verify picking list exists
            picking_list = self.repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Validate at least one item type is specified
            if not any([component_id, material_id, leather_id, hardware_id]):
                raise ValidationError("At least one item type must be specified")

            # Validate quantity
            if quantity_ordered <= 0:
                raise ValidationError("Quantity ordered must be greater than zero")

            # Create item data
            item_data = {
                "picking_list_id": picking_list_id,
                "quantity_ordered": quantity_ordered,
                "quantity_picked": 0  # Initialize to zero
            }

            # Add optional IDs if provided
            if component_id:
                item_data["component_id"] = component_id
            if material_id:
                item_data["material_id"] = material_id
            if leather_id:
                item_data["leather_id"] = leather_id
            if hardware_id:
                item_data["hardware_id"] = hardware_id

            self.logger.info(f"Adding item to picking list {picking_list_id}")
            item = self.repository.add_item(item_data)
            return self._serialize_picking_list_item(item)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error adding item to picking list: {str(e)}")
            raise ValidationError(f"Failed to add item to picking list: {str(e)}")

    def update_item(self,
                   item_id: int,
                   quantity_picked: Optional[int] = None,
                   **kwargs) -> Dict[str, Any]:
        """
        Update a picking list item.

        Args:
            item_id: ID of the picking list item
            quantity_picked: Quantity actually picked
            **kwargs: Additional attributes to update

        Returns:
            Dict containing the updated picking list item

        Raises:
            NotFoundError: If the item doesn't exist
            ValidationError: If update validation fails
        """
        try:
            # Verify item exists
            item = self.repository.get_item_by_id(item_id)
            if not item:
                raise NotFoundError(f"Picking list item with ID {item_id} not found")

            # Update data
            update_data = kwargs
            if quantity_picked is not None:
                if quantity_picked < 0:
                    raise ValidationError("Quantity picked cannot be negative")
                update_data["quantity_picked"] = quantity_picked

            # Remove any attributes that shouldn't be directly updated
            for key in ["id", "picking_list_id"]:
                if key in update_data:
                    del update_data[key]

            self.logger.info(f"Updating picking list item {item_id}")
            updated_item = self.repository.update_item(item_id, update_data)
            return self._serialize_picking_list_item(updated_item)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating picking list item: {str(e)}")
            raise ValidationError(f"Failed to update picking list item: {str(e)}")

    def remove_item(self, item_id: int) -> None:
        """
        Remove an item from a picking list.

        Args:
            item_id: ID of the picking list item to remove

        Raises:
            NotFoundError: If the item doesn't exist
        """
        try:
            # Verify item exists
            item = self.repository.get_item_by_id(item_id)
            if not item:
                raise NotFoundError(f"Picking list item with ID {item_id} not found")

            self.logger.info(f"Removing picking list item {item_id}")
            self.repository.delete_item(item_id)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error removing picking list item: {str(e)}")
            raise ValidationError(f"Failed to remove picking list item: {str(e)}")

    def process_picking_list(self, picking_list_id: int) -> Dict[str, Any]:
        """
        Process a picking list, updating inventory and related records.

        Args:
            picking_list_id: ID of the picking list to process

        Returns:
            Dict containing the processed picking list data

        Raises:
            NotFoundError: If the picking list doesn't exist
            ValidationError: If the picking list cannot be processed
        """
        try:
            # Verify picking list exists
            picking_list = self.repository.get_by_id(picking_list_id)
            if not picking_list:
                raise NotFoundError(f"Picking list with ID {picking_list_id} not found")

            # Validate picking list status
            if picking_list.status not in [PickingListStatus.IN_PROGRESS, PickingListStatus.DRAFT]:
                raise ValidationError(f"Cannot process picking list with status {picking_list.status}")

            # Validate all items have been picked
            for item in picking_list.items:
                if item.quantity_picked < item.quantity_ordered:
                    raise ValidationError(f"Item {item.id} has not been fully picked")

            # Process the picking list - this would typically update inventory
            # and possibly create related records, but we'll just update the status
            # for this implementation

            self.logger.info(f"Processing picking list {picking_list_id}")
            updated_picking_list = self.repository.update(
                picking_list_id,
                {
                    "status": PickingListStatus.COMPLETED,
                    "completed_at": datetime.now()
                }
            )

            # Update project components or other related records as needed
            # This would be implemented based on the specific business requirements

            return self._serialize_picking_list(updated_picking_list)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error processing picking list: {str(e)}")
            raise ValidationError(f"Failed to process picking list: {str(e)}")

    def _validate_status_transition(self, current_status: PickingListStatus,
                                   new_status: PickingListStatus) -> None:
        """
        Validate if a status transition is allowed.

        Args:
            current_status: Current picking list status
            new_status: New picking list status

        Raises:
            ValidationError: If the status transition is not allowed
        """
        # Define allowed status transitions
        allowed_transitions = {
            PickingListStatus.DRAFT: [PickingListStatus.IN_PROGRESS, PickingListStatus.CANCELLED],
            PickingListStatus.IN_PROGRESS: [PickingListStatus.COMPLETED, PickingListStatus.CANCELLED],
            PickingListStatus.COMPLETED: [PickingListStatus.CANCELLED],
            PickingListStatus.CANCELLED: []  # No transitions allowed from cancelled
        }

        if new_status not in allowed_transitions.get(current_status, []):
            raise ValidationError(
                f"Cannot transition from {current_status} to {new_status}"
            )

    def _serialize_picking_list(self, picking_list: PickingList) -> Dict[str, Any]:
        """
        Serialize a picking list to a dictionary.

        Args:
            picking_list: PickingList instance to serialize

        Returns:
            Dictionary representation of the picking list
        """
        result = {
            "id": picking_list.id,
            "sales_id": picking_list.sales_id,
            "status": picking_list.status.name,
            "created_at": picking_list.created_at.isoformat() if picking_list.created_at else None,
            "completed_at": picking_list.completed_at.isoformat() if picking_list.completed_at else None
        }

        # Include items if they are loaded
        if hasattr(picking_list, 'items') and picking_list.items is not None:
            result["items"] = [self._serialize_picking_list_item(item) for item in picking_list.items]

        return result

    def _serialize_picking_list_item(self, item: PickingListItem) -> Dict[str, Any]:
        """
        Serialize a picking list item to a dictionary.

        Args:
            item: PickingListItem instance to serialize

        Returns:
            Dictionary representation of the picking list item
        """
        return {
            "id": item.id,
            "picking_list_id": item.picking_list_id,
            "component_id": item.component_id if hasattr(item, 'component_id') else None,
            "material_id": item.material_id if hasattr(item, 'material_id') else None,
            "leather_id": item.leather_id if hasattr(item, 'leather_id') else None,
            "hardware_id": item.hardware_id if hasattr(item, 'hardware_id') else None,
            "quantity_ordered": item.quantity_ordered,
            "quantity_picked": item.quantity_picked
        }