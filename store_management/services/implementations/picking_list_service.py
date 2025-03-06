"""
services/implementations/picking_list_service.py - Implementation of the Picking List Service
"""
import logging
from datetime import datetime

from database.repositories.picking_list_repository import PickingListRepository
from database.sqlalchemy.session import get_db_session
from database.models.picking_list import PickingList, PickingListItem, PickingListStatus
from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.picking_list_service import IPickingListService

from typing import Any, Dict, List, Optional

class PickingListService(BaseService, IPickingListService):
    """Service for managing picking lists and items."""

    def __init__(self, picking_list_repository=None):
        """
        Initialize the Picking List Service with a repository.

        Args:
            picking_list_repository: Repository for picking list data access
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)

        if picking_list_repository is None:
            # Create repository with a new session
            session = get_db_session()
            self.picking_list_repository = PickingListRepository(session)
            self._owns_session = True
        else:
            self.picking_list_repository = picking_list_repository
            self._owns_session = False

        self.logger.info("Initialized PickingListService with repository")

    def _convert_picking_list_to_dict(self, picking_list: PickingList) -> Dict[str, Any]:
        """
        Convert a PickingList model instance to a dictionary.

        Args:
            picking_list: PickingList model instance

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            'id': picking_list.id,
            'name': picking_list.name,
            'description': picking_list.description,
            'status': picking_list.status.name if isinstance(picking_list.status, PickingListStatus) else picking_list.status,
            'created_at': picking_list.created_at,
            'updated_at': picking_list.updated_at
        }

    def _convert_item_to_dict(self, item: PickingListItem) -> Dict[str, Any]:
        """
        Convert a PickingListItem model instance to a dictionary.

        Args:
            item: PickingListItem model instance

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        material_name = f"Material {item.material_id}"
        if hasattr(item, 'material') and item.material:
            material_name = item.material.name

        return {
            'id': item.id,
            'list_id': item.list_id,
            'material_id': item.material_id,
            'material_name': material_name,
            'required_quantity': item.required_quantity,
            'picked_quantity': item.picked_quantity,
            'unit': item.unit,
            'storage_location': item.storage_location,
            'notes': item.notes,
            'is_picked': item.is_picked
        }

    def get_all_lists(self) -> List[Dict[str, Any]]:
        """
        Get all picking lists.

        Returns:
            List[Dict[str, Any]]: List of picking lists data
        """
        try:
            picking_lists = self.picking_list_repository.get_all()
            return [self._convert_picking_list_to_dict(pl) for pl in picking_lists]
        except Exception as e:
            self.logger.error(f"Error retrieving all picking lists: {e}")
            return []

    # Alias for get_all_lists to match view calls
    def get_all(self) -> List[Dict[str, Any]]:
        """Alias for get_all_lists for backward compatibility."""
        return self.get_all_lists()

    def get_list_by_id(self, list_id: int) -> Dict[str, Any]:
        """
        Get a picking list by ID.

        Args:
            list_id: ID of the picking list to retrieve

        Returns:
            Dict[str, Any]: Picking list data

        Raises:
            NotFoundError: If picking list not found
        """
        picking_list = self.picking_list_repository.get_by_id(list_id)
        if not picking_list:
            raise NotFoundError(f"Picking list with ID {list_id} not found")

        result = self._convert_picking_list_to_dict(picking_list)

        # Add items to the result
        items = self.picking_list_repository.get_items(list_id)
        result['items'] = [self._convert_item_to_dict(item) for item in items]

        return result

    # Alias for get_list_by_id to match view calls
    def get_picking_list(self, list_id: int) -> Dict[str, Any]:
        """Alias for get_list_by_id for backward compatibility."""
        return self.get_list_by_id(list_id)

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a picking list by name.

        Args:
            name: Name of the picking list to retrieve

        Returns:
            Optional[Dict[str, Any]]: Picking list data or None if not found
        """
        try:
            picking_lists = self.picking_list_repository.search(name)
            for pl in picking_lists:
                if pl.name.lower() == name.lower():
                    result = self._convert_picking_list_to_dict(pl)

                    # Add items to the result
                    items = self.picking_list_repository.get_items(pl.id)
                    result['items'] = [self._convert_item_to_dict(item) for item in items]

                    return result
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving picking list by name '{name}': {e}")
            return None

    def create_list(self, list_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new picking list.

        Args:
            list_data: Picking list data

        Returns:
            Dict[str, Any]: Created picking list

        Raises:
            ValidationError: If data is invalid
        """
        # Validate required fields
        if 'name' not in list_data or not list_data['name']:
            raise ValidationError("Picking list name is required")

        try:
            # Create the picking list
            picking_list = self.picking_list_repository.create(list_data)

            # Commit changes
            if self._owns_session:
                self.picking_list_repository.session.commit()

            self.logger.info(f"Created new picking list: {picking_list.name}")
            return self._convert_picking_list_to_dict(picking_list)

        except Exception as e:
            if self._owns_session:
                self.picking_list_repository.session.rollback()
            self.logger.error(f"Error creating picking list: {e}")
            raise

    def update_list(self, list_id: int, list_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing picking list.

        Args:
            list_id: ID of the picking list to update
            list_data: Picking list data to update

        Returns:
            Dict[str, Any]: Updated picking list

        Raises:
            NotFoundError: If picking list not found
            ValidationError: If data is invalid
        """
        # Validate name if provided
        if 'name' in list_data and not list_data['name']:
            raise ValidationError("Picking list name cannot be empty")

        try:
            # Update the picking list
            picking_list = self.picking_list_repository.update(list_id, list_data)

            if not picking_list:
                raise NotFoundError(f"Picking list with ID {list_id} not found")

            # Commit changes
            if self._owns_session:
                self.picking_list_repository.session.commit()

            self.logger.info(f"Updated picking list: {picking_list.name}")
            return self._convert_picking_list_to_dict(picking_list)

        except (NotFoundError, ValidationError):
            # Pass through our custom exceptions
            raise
        except Exception as e:
            if self._owns_session:
                self.picking_list_repository.session.rollback()
            self.logger.error(f"Error updating picking list {list_id}: {e}")
            raise

    def delete_list(self, list_id: int) -> bool:
        """
        Delete a picking list.

        Args:
            list_id: ID of the picking list to delete

        Returns:
            bool: True if successfully deleted

        Raises:
            NotFoundError: If picking list not found
        """
        try:
            # Delete the picking list
            result = self.picking_list_repository.delete(list_id)

            if not result:
                raise NotFoundError(f"Picking list with ID {list_id} not found")

            # Commit changes
            if self._owns_session:
                self.picking_list_repository.session.commit()

            self.logger.info(f"Deleted picking list with ID: {list_id}")
            return True

        except NotFoundError:
            # Pass through our custom exception
            raise
        except Exception as e:
            if self._owns_session:
                self.picking_list_repository.session.rollback()
            self.logger.error(f"Error deleting picking list {list_id}: {e}")
            raise

    def get_list_items(self, list_id: int) -> List[Dict[str, Any]]:
        """
        Get all items for a picking list.

        Args:
            list_id: ID of the picking list

        Returns:
            List[Dict[str, Any]]: List of picking list items

        Raises:
            NotFoundError: If picking list not found
        """
        # Verify picking list exists
        self.get_list_by_id(list_id)

        try:
            # Get items
            items = self.picking_list_repository.get_items(list_id)
            return [self._convert_item_to_dict(item) for item in items]

        except Exception as e:
            self.logger.error(f"Error retrieving items for picking list {list_id}: {e}")
            raise

    def add_item(self, list_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add an item to a picking list.

        Args:
            list_id: ID of the picking list
            item_data: Item data to add

        Returns:
            Dict[str, Any]: Added item

        Raises:
            NotFoundError: If picking list not found
            ValidationError: If data is invalid
        """
        # Verify picking list exists
        self.get_list_by_id(list_id)

        # Validate required fields
        if 'material_id' not in item_data:
            raise ValidationError("Material ID is required for picking list items")

        if 'required_quantity' not in item_data or item_data['required_quantity'] <= 0:
            raise ValidationError("Required quantity must be positive")

        try:
            # Add list_id to item data
            item_data['list_id'] = list_id

            # Create the item
            item = self.picking_list_repository.add_item(item_data)

            # Commit changes
            if self._owns_session:
                self.picking_list_repository.session.commit()

            self.logger.info(f"Added item to picking list {list_id}: Material ID {item.material_id}")
            return self._convert_item_to_dict(item)

        except Exception as e:
            if self._owns_session:
                self.picking_list_repository.session.rollback()
            self.logger.error(f"Error adding item to picking list {list_id}: {e}")
            raise

    def add_items(self, list_name: str, items_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add multiple items to a picking list.

        Args:
            list_name: Name of the picking list
            items_data: List of item data to add

        Returns:
            Dict[str, Any]: Updated picking list

        Raises:
            NotFoundError: If picking list not found
            ValidationError: If data is invalid
        """
        # Get the picking list by name
        picking_list = self.get_by_name(list_name)
        if not picking_list:
            raise NotFoundError(f"Picking list with name '{list_name}' not found")

        list_id = picking_list['id']

        # Add each item
        for item_data in items_data:
            # Add material_id if it's missing (for backward compatibility)
            if 'material_id' not in item_data and 'name' in item_data:
                # This is a simplified implementation - in a real app, you'd
                # need to look up the material ID by name
                item_data['material_id'] = 1

            # Convert quantity to required_quantity if needed
            if 'quantity' in item_data and 'required_quantity' not in item_data:
                item_data['required_quantity'] = item_data.pop('quantity')

            self.add_item(list_id, item_data)

        # Return the updated picking list
        return self.get_list_by_id(list_id)

    def update_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a picking list item.

        Args:
            item_data: Item data including ID

        Returns:
            Dict[str, Any]: Updated item

        Raises:
            NotFoundError: If item not found
            ValidationError: If data is invalid
        """
        if 'id' not in item_data:
            raise ValidationError("Item ID is required for updates")

        item_id = item_data['id']

        # Validate quantity if provided
        if 'required_quantity' in item_data and item_data['required_quantity'] <= 0:
            raise ValidationError("Required quantity must be positive")

        try:
            # Update the item
            item = self.picking_list_repository.update_item(item_id, item_data)

            if not item:
                raise NotFoundError(f"Picking list item with ID {item_id} not found")

            # Commit changes
            if self._owns_session:
                self.picking_list_repository.session.commit()

            self.logger.info(f"Updated picking list item: {item_id}")
            return self._convert_item_to_dict(item)

        except (NotFoundError, ValidationError):
            # Pass through our custom exceptions
            raise
        except Exception as e:
            if self._owns_session:
                self.picking_list_repository.session.rollback()
            self.logger.error(f"Error updating picking list item {item_id}: {e}")
            raise

    # Compatibility method for updating items from the view
    def update_picking_list_item(self, item_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compatibility method for updating picking list items."""
        item_data['id'] = item_id
        return self.update_item(item_data)

    def remove_item(self, item_id: int) -> bool:
        """
        Remove an item from a picking list.

        Args:
            item_id: ID of the item to remove

        Returns:
            bool: True if successfully removed

        Raises:
            NotFoundError: If item not found
        """
        try:
            # Remove the item
            result = self.picking_list_repository.remove_item(item_id)

            if not result:
                raise NotFoundError(f"Picking list item with ID {item_id} not found")

            # Commit changes
            if self._owns_session:
                self.picking_list_repository.session.commit()

            self.logger.info(f"Removed picking list item with ID: {item_id}")
            return True

        except NotFoundError:
            # Pass through our custom exception
            raise
        except Exception as e:
            if self._owns_session:
                self.picking_list_repository.session.rollback()
            self.logger.error(f"Error removing picking list item {item_id}: {e}")
            raise

    def mark_item_picked(self, item_id: int, quantity: float) -> Dict[str, Any]:
        """
        Mark a picking list item as picked with the specified quantity.

        Args:
            item_id: ID of the item to mark
            quantity: Quantity picked

        Returns:
            Dict[str, Any]: Updated item

        Raises:
            NotFoundError: If item not found
            ValidationError: If quantity is invalid
        """
        if quantity < 0:
            raise ValidationError("Picked quantity cannot be negative")

        try:
            # Get the item
            item = self.picking_list_repository.get_item_by_id(item_id)

            if not item:
                raise NotFoundError(f"Picking list item with ID {item_id} not found")

            # Update picked quantity and status
            item_data = {
                'picked_quantity': quantity,
                'is_picked': quantity >= item.required_quantity
            }

            # Update the item
            item = self.picking_list_repository.update_item(item_id, item_data)

            # Commit changes
            if self._owns_session:
                self.picking_list_repository.session.commit()

            self.logger.info(f"Marked item {item_id} as picked: {quantity} {item.unit}")
            return self._convert_item_to_dict(item)

        except (NotFoundError, ValidationError):
            # Pass through our custom exceptions
            raise
        except Exception as e:
            if self._owns_session:
                self.picking_list_repository.session.rollback()
            self.logger.error(f"Error marking item {item_id} as picked: {e}")
            raise

    def filter_lists_by_status(self, status: PickingListStatus) -> List[Dict[str, Any]]:
        """
        Filter picking lists by status.

        Args:
            status: Status to filter by

        Returns:
            List[Dict[str, Any]]: Filtered picking lists
        """
        try:
            picking_lists = self.picking_list_repository.filter_by_status(status)
            return [self._convert_picking_list_to_dict(pl) for pl in picking_lists]
        except Exception as e:
            self.logger.error(f"Error filtering picking lists by status {status}: {e}")
            return []

    def search_lists(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search picking lists by name or description.

        Args:
            search_term: Term to search for

        Returns:
            List[Dict[str, Any]]: Matching picking lists
        """
        try:
            picking_lists = self.picking_list_repository.search(search_term)
            return [self._convert_picking_list_to_dict(pl) for pl in picking_lists]
        except Exception as e:
            self.logger.error(f"Error searching picking lists with term '{search_term}': {e}")
            return []

    # Add additional methods to support the view
    def generate_picking_list_from_project(self, project_id: int) -> Dict[str, Any]:
        """
        Generate a picking list from a project.

        Args:
            project_id: ID of the project to generate from

        Returns:
            Dict[str, Any]: Created picking list

        Raises:
            NotFoundError: If project not found
        """
        # This is a placeholder implementation
        # In a real app, you would:
        # 1. Get the project details
        # 2. Extract materials needed
        # 3. Create a picking list with those materials

        try:
            # Create a picking list
            list_data = {
                'name': f"Project {project_id} Picking List",
                'description': f"Generated from Project {project_id}",
                'status': PickingListStatus.DRAFT.name
            }

            picking_list = self.create_list(list_data)

            # Dummy item data - in a real app, this would come from the project
            item_data = {
                'material_id': 1,
                'required_quantity': 10,
                'unit': 'pcs'
            }

            self.add_item(picking_list['id'], item_data)

            return self.get_list_by_id(picking_list['id'])

        except Exception as e:
            self.logger.error(f"Error generating picking list from project {project_id}: {e}")
            raise

    def generate_picking_list_from_order(self, order_id: int) -> Dict[str, Any]:
        """
        Generate a picking list from an sale.

        Args:
            order_id: ID of the sale to generate from

        Returns:
            Dict[str, Any]: Created picking list

        Raises:
            NotFoundError: If sale not found
        """
        # This is a placeholder implementation
        # In a real app, you would:
        # 1. Get the sale details
        # 2. Extract materials needed
        # 3. Create a picking list with those materials

        try:
            # Create a picking list
            list_data = {
                'name': f"Order {order_id} Picking List",
                'description': f"Generated from Order {order_id}",
                'status': PickingListStatus.DRAFT.name
            }

            picking_list = self.create_list(list_data)

            # Dummy item data - in a real app, this would come from the sale
            item_data = {
                'material_id': 1,
                'required_quantity': 5,
                'unit': 'pcs'
            }

            self.add_item(picking_list['id'], item_data)

            return self.get_list_by_id(picking_list['id'])

        except Exception as e:
            self.logger.error(f"Error generating picking list from sale {order_id}: {e}")
            raise