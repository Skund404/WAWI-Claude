# services/implementations/shopping_list_service.py
from database.models.shopping_list import ShoppingList, ShoppingListItem
from database.models.enums import ShoppingListStatus, Priority
from database.repositories.shopping_list_repository import ShoppingListRepository
from database.sqlalchemy.session import get_db_session
from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.shopping_list_service import IShoppingListService

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime


class ShoppingListService(BaseService, IShoppingListService):
    """
    Service implementation for managing Shopping List entities.

    Responsibilities:
    - Create, read, update, and delete shopping list records
    - Validate shopping list data
    - Handle database interactions
    - Provide business logic for shopping list management
    """

    def __init__(self,
                 session: Optional[Session] = None,
                 shopping_list_repository: Optional[ShoppingListRepository] = None):
        """
        Initialize the Shopping List Service.

        Args:
            session (Optional[Session]): SQLAlchemy database session
            shopping_list_repository (Optional[ShoppingListRepository]): Shopping list data access repository
        """
        self.session = session or get_db_session()
        self.repository = shopping_list_repository or ShoppingListRepository(self.session)
        self.logger = logging.getLogger(self.__class__.__name__)

    def list_shopping_lists(self,
                            status: Optional[ShoppingListStatus] = None,
                            priority: Optional[Priority] = None,
                            is_completed: Optional[bool] = None) -> List[ShoppingList]:
        """
        List shopping lists with optional filtering.

        Args:
            status (Optional[ShoppingListStatus]): Filter by shopping list status
            priority (Optional[Priority]): Filter by priority
            is_completed (Optional[bool]): Filter by completion status

        Returns:
            List[ShoppingList]: List of shopping lists matching the criteria
        """
        try:
            # Construct query
            query = self.session.query(ShoppingList)

            # Apply filters
            if status:
                query = query.filter(ShoppingList.status == status)

            if priority:
                query = query.filter(ShoppingList.priority == priority)

            if is_completed is not None:
                query = query.filter(ShoppingList.is_completed == is_completed)

            # Execute query
            shopping_lists = query.all()

            self.logger.info("Shopping lists retrieved", extra={
                "total_lists": len(shopping_lists),
                "status": status,
                "priority": priority,
                "is_completed": is_completed
            })

            return shopping_lists

        except SQLAlchemyError as e:
            self.logger.error(f"Error listing shopping lists: {str(e)}", extra={
                "error": str(e),
                "status": status,
                "priority": priority,
                "is_completed": is_completed
            })
            raise ValidationError(f"Error retrieving shopping lists: {str(e)}")

    def add_item_to_shopping_list(self,
                                  shopping_list_id: int,
                                  item_data: Dict[str, Any]) -> ShoppingListItem:
        """
        Add an item to an existing shopping list.

        Args:
            shopping_list_id (int): ID of the shopping list
            item_data (Dict[str, Any]): Data for the new shopping list item

        Returns:
            ShoppingListItem: The newly created item

        Raises:
            NotFoundError: If shopping list doesn't exist
            ValidationError: If item data is invalid
        """
        try:
            # Retrieve existing shopping list
            shopping_list = self.get_shopping_list_by_id(shopping_list_id)

            # Add item to shopping list (method includes validation)
            item = shopping_list.add_item(item_data)

            # Commit changes
            self.session.commit()

            self.logger.info(f"Item added to shopping list", extra={
                "shopping_list_id": shopping_list_id,
                "item_id": item.id,
                "item_name": item.name
            })

            return item

        except (ValueError, TypeError) as e:
            self.session.rollback()
            self.logger.error(f"Adding item to shopping list failed: {str(e)}", extra={
                "shopping_list_id": shopping_list_id,
                "item_data": item_data,
                "error": str(e)
            })
            raise ValidationError(f"Invalid item data: {str(e)}")

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Database error adding item to shopping list: {str(e)}", extra={
                "shopping_list_id": shopping_list_id,
                "item_data": item_data,
                "error": str(e)
            })
            raise ValidationError(f"Database error: {str(e)}")

    def update_shopping_list_item(self,
                                  item_id: int,
                                  update_data: Dict[str, Any]) -> ShoppingListItem:
        """
        Update an existing shopping list item.

        Args:
            item_id (int): ID of the shopping list item to update
            update_data (Dict[str, Any]): Data to update

        Returns:
            ShoppingListItem: Updated shopping list item

        Raises:
            NotFoundError: If shopping list item doesn't exist
            ValidationError: If update data is invalid
        """
        try:
            # Retrieve existing item
            item = self.session.query(ShoppingListItem).get(item_id)

            if not item:
                raise NotFoundError(f"Shopping list item with ID {item_id} not found")

            # Update item (method includes validation)
            item.update(**update_data)

            # Commit changes
            self.session.commit()

            self.logger.info(f"Shopping list item updated successfully", extra={
                "item_id": item.id,
                "shopping_list_id": item.shopping_list_id,
                "updates": list(update_data.keys())
            })

            return item

        except (ValueError, TypeError) as e:
            self.session.rollback()
            self.logger.error(f"Shopping list item update failed: {str(e)}", extra={
                "item_id": item_id,
                "update_data": update_data,
                "error": str(e)
            })
            raise ValidationError(f"Invalid update data: {str(e)}")

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Database error during shopping list item update: {str(e)}", extra={
                "item_id": item_id,
                "update_data": update_data,
                "error": str(e)
            })
            raise ValidationError(f"Database error: {str(e)}")

    def remove_item_from_shopping_list(self, item_id: int) -> None:
        """
        Remove an item from a shopping list.

        Args:
            item_id (int): ID of the shopping list item to remove

        Raises:
            NotFoundError: If shopping list item doesn't exist
        """
        try:
            # Retrieve existing item
            item = self.session.query(ShoppingListItem).get(item_id)

            if not item:
                raise NotFoundError(f"Shopping list item with ID {item_id} not found")

            # Get the associated shopping list
            shopping_list = item.shopping_list

            # Remove item from shopping list
            shopping_list.remove_item(item_id)

            # Commit changes
            self.session.commit()

            self.logger.info(f"Item removed from shopping list", extra={
                "item_id": item_id,
                "shopping_list_id": shopping_list.id
            })

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error removing item from shopping list: {str(e)}", extra={
                "item_id": item_id,
                "error": str(e)
            })
            raise NotFoundError(f"Error removing item from shopping list: {str(e)}")

    def mark_shopping_list_completed(self, shopping_list_id: int) -> ShoppingList:
        """
        Mark a shopping list as completed.

        Args:
            shopping_list_id (int): ID of the shopping list to mark as completed

        Returns:
            ShoppingList: Updated shopping list instance

        Raises:
            NotFoundError: If shopping list doesn't exist
        """
        try:
            # Retrieve existing shopping list
            shopping_list = self.get_shopping_list_by_id(shopping_list_id)

            # Mark as completed
            shopping_list.mark_completed()

            # Commit changes
            self.session.commit()

            self.logger.info(f"Shopping list marked as completed", extra={
                "shopping_list_id": shopping_list_id
            })

            return shopping_list

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error marking shopping list as completed: {str(e)}", extra={
                "shopping_list_id": shopping_list_id,
                "error": str(e)
            })
            raise NotFoundError(f"Error marking shopping list as completed: {str(e)}")

    def reset_shopping_list(self, shopping_list_id: int) -> ShoppingList:
        """
        Reset a shopping list to draft status and unmark all items.

        Args:
            shopping_list_id (int): ID of the shopping list to reset

        Returns:
            ShoppingList: Reset shopping list instance

        Raises:
            NotFoundError: If shopping list doesn't exist
        """
        try:
            # Retrieve existing shopping list
            shopping_list = self.get_shopping_list_by_id(shopping_list_id)

            # Reset shopping list
            shopping_list.reset()

            # Reset all items
            for item in shopping_list.items:
                item.reset_purchase_status()

            # Commit changes
            self.session.commit()

            self.logger.info(f"Shopping list reset to draft", extra={
                "shopping_list_id": shopping_list_id
            })

            return shopping_list

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error resetting shopping list: {str(e)}", extra={
                "shopping_list_id": shopping_list_id,
                "error": str(e)
            })
            raise NotFoundError(f"Error resetting shopping list: {str(e)}")

    def calculate_shopping_list_total(self, shopping_list_id: int) -> Dict[str, Any]:
        """
        Calculate the total estimated cost of a shopping list.

        Args:
            shopping_list_id (int): ID of the shopping list

        Returns:
            Dict[str, Any]: Dictionary containing total cost and item details

        Raises:
            NotFoundError: If shopping list doesn't exist
        """
        try:
            # Retrieve existing shopping list
            shopping_list = self.get_shopping_list_by_id(shopping_list_id)

            # Calculate total
            total_estimated_cost = 0
            item_details = []

            for item in shopping_list.items:
                # Calculate item total
                item_total = (item.quantity or 0) * (item.estimated_price or 0)
                total_estimated_cost += item_total

                # Collect item details
                item_details.append({
                    'id': item.id,
                    'name': item.name,
                    'quantity': item.quantity,
                    'estimated_price': item.estimated_price,
                    'item_total': item_total,
                    'is_purchased': item.is_purchased
                })

            # Prepare results
            result = {
                'shopping_list_id': shopping_list.id,
                'shopping_list_name': shopping_list.name,
                'total_estimated_cost': total_estimated_cost,
                'item_count': len(shopping_list.items),
                'purchased_items_count': sum(1 for item in shopping_list.items if item.is_purchased),
                'items': item_details
            }

            self.logger.info(f"Shopping list total calculated", extra={
                "shopping_list_id": shopping_list_id,
                "total_estimated_cost": total_estimated_cost
            })

            return result

        except SQLAlchemyError as e:
            self.logger.error(f"Error calculating shopping list total: {str(e)}", extra={
                "shopping_list_id": shopping_list_id,
                "error": str(e)
            })
            raise NotFoundError(f"Error calculating shopping list total: {str(e)}")

    def create_shopping_list(self, data: Dict[str, Any]) -> ShoppingList:
        """
        Create a new shopping list.

        Args:
            data (Dict[str, Any]): Shopping list data including name, status, etc.

        Returns:
            ShoppingList: The created shopping list
        """
        try:
            # Validate required fields
            if 'name' not in data or not data['name']:
                raise ValidationError("Shopping list name is required")

            # Create new shopping list instance
            shopping_list = ShoppingList(
                name=data['name'],
                description=data.get('description', ''),
                status=data.get('status', ShoppingListStatus.PENDING),
                priority=data.get('priority', Priority.MEDIUM),
                due_date=data.get('due_date'),
                created_by=data.get('created_by', 'system')
            )

            # Add to session and commit
            self.session.add(shopping_list)
            self.session.commit()

            self.logger.info(f"Shopping list created successfully", extra={
                "shopping_list_id": shopping_list.id,
                "name": shopping_list.name
            })

            return shopping_list

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error creating shopping list: {str(e)}", extra={
                "data": data,
                "error": str(e)
            })
            raise ValidationError(f"Failed to create shopping list: {str(e)}")

    def get_shopping_list_by_id(self, list_id: int) -> ShoppingList:
        """
        Get a shopping list by ID.

        Args:
            list_id (int): ID of the shopping list

        Returns:
            ShoppingList: Shopping list object

        Raises:
            NotFoundError: If shopping list doesn't exist
        """
        try:
            shopping_list = self.session.query(ShoppingList).get(list_id)

            if not shopping_list:
                raise NotFoundError(f"Shopping list with ID {list_id} not found")

            return shopping_list

        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving shopping list: {str(e)}", extra={
                "list_id": list_id,
                "error": str(e)
            })
            raise NotFoundError(f"Error retrieving shopping list: {str(e)}")

    def update_shopping_list(self, list_id: int, data: Dict[str, Any]) -> ShoppingList:
        """
        Update an existing shopping list.

        Args:
            list_id (int): ID of the shopping list to update
            data (Dict[str, Any]): Shopping list data to update

        Returns:
            ShoppingList: Updated shopping list

        Raises:
            NotFoundError: If shopping list doesn't exist
            ValidationError: If update data is invalid
        """
        try:
            # Retrieve existing shopping list
            shopping_list = self.get_shopping_list_by_id(list_id)

            # Update fields if provided
            if 'name' in data:
                shopping_list.name = data['name']

            if 'description' in data:
                shopping_list.description = data['description']

            if 'status' in data:
                shopping_list.status = data['status']

            if 'priority' in data:
                shopping_list.priority = data['priority']

            if 'due_date' in data:
                shopping_list.due_date = data['due_date']

            # Commit changes
            self.session.commit()

            self.logger.info(f"Shopping list updated successfully", extra={
                "shopping_list_id": shopping_list.id,
                "updates": list(data.keys())
            })

            return shopping_list

        except (ValueError, TypeError) as e:
            self.session.rollback()
            self.logger.error(f"Shopping list update failed: {str(e)}", extra={
                "list_id": list_id,
                "data": data,
                "error": str(e)
            })
            raise ValidationError(f"Invalid update data: {str(e)}")

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Database error during shopping list update: {str(e)}", extra={
                "list_id": list_id,
                "data": data,
                "error": str(e)
            })
            raise ValidationError(f"Database error: {str(e)}")

    def delete_shopping_list(self, list_id: int) -> bool:
        """
        Delete a shopping list.

        Args:
            list_id (int): ID of the shopping list to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            NotFoundError: If shopping list doesn't exist
        """
        try:
            # Retrieve existing shopping list
            shopping_list = self.get_shopping_list_by_id(list_id)

            # Delete the shopping list
            self.session.delete(shopping_list)
            self.session.commit()

            self.logger.info(f"Shopping list deleted successfully", extra={
                "shopping_list_id": list_id
            })

            return True

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error deleting shopping list: {str(e)}", extra={
                "list_id": list_id,
                "error": str(e)
            })
            raise NotFoundError(f"Error deleting shopping list: {str(e)}")