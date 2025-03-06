# database/repositories/picking_list_repository.py
"""
Repository for managing PickingList entities.

This repository handles database operations for the PickingList and PickingListItem
models, including creation, retrieval, update, and deletion of picking lists.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Tuple

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.models.picking_list import PickingList, PickingListItem
from database.models.enums import PickingListStatus
from database.repositories.base_repository import BaseRepository
from database.exceptions import DatabaseError, ModelNotFoundError

# Setup logger
logger = logging.getLogger(__name__)

class PickingListRepository(BaseRepository[PickingList]):
    """Repository for managing PickingList entities."""
    
    def __init__(self, session: Session) -> None:
        """
        Initialize the PickingList Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, PickingList)
        logger.debug("PickingListRepository initialized")
    
    def get_by_sales_id(self, sales_id: int) -> Optional[PickingList]:
        """
        Get the picking list for a specific sale.

        Args:
            sales_id: The sale ID to query

        Returns:
            Optional[PickingList]: The picking list if found, None otherwise
        """
        try:
            query = self.session.query(PickingList).filter(
                PickingList.sales_id == sales_id
            )
            
            picking_list = query.first()
            if picking_list:
                logger.debug(f"Retrieved picking list for sale ID {sales_id}")
            else:
                logger.debug(f"No picking list found for sale ID {sales_id}")
                
            return picking_list
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving picking list for sale ID {sales_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def get_with_items(self, picking_list_id: int) -> Optional[PickingList]:
        """
        Get a picking list with its items eagerly loaded.

        Args:
            picking_list_id: The picking list ID to retrieve

        Returns:
            Optional[PickingList]: The picking list with items if found, None otherwise
        """
        try:
            query = self.session.query(PickingList).filter(
                PickingList.id == picking_list_id
            ).options(
                joinedload(PickingList.items)
            )
            
            picking_list = query.first()
            if not picking_list:
                logger.debug(f"No picking list found with ID {picking_list_id}")
                return None
            
            logger.debug(f"Retrieved picking list ID {picking_list_id} with {len(picking_list.items)} items")
            return picking_list
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving picking list ID {picking_list_id} with items: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def get_by_status(self, status: PickingListStatus) -> List[PickingList]:
        """
        Get all picking lists with a specific status.

        Args:
            status: The status to filter by

        Returns:
            List[PickingList]: List of picking lists matching the status
        """
        try:
            query = self.session.query(PickingList).filter(
                PickingList.status == status
            ).order_by(PickingList.created_at.desc())
            
            picking_lists = query.all()
            logger.debug(f"Retrieved {len(picking_lists)} picking lists with status {status.name}")
            return picking_lists
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving picking lists with status {status.name}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def create_for_sale(self, sales_id: int) -> PickingList:
        """
        Create a new picking list for a sale.

        Args:
            sales_id: The sale ID to create a picking list for

        Returns:
            PickingList: The created picking list

        Raises:
            DatabaseError: If there's an error creating the picking list
        """
        try:
            # Check if picking list already exists
            existing = self.get_by_sales_id(sales_id)
            if existing:
                logger.debug(f"Picking list already exists for sale ID {sales_id}")
                return existing
            
            # Create new picking list
            picking_list = PickingList(
                sales_id=sales_id,
                status=PickingListStatus.DRAFT,
                created_at=datetime.utcnow()
            )
            
            self.session.add(picking_list)
            self.session.commit()
            
            logger.debug(f"Created picking list for sale ID {sales_id}")
            return picking_list
        except Exception as e:
            self.session.rollback()
            error_msg = f"Error creating picking list for sale ID {sales_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def update_status(self, picking_list_id: int, status: PickingListStatus) -> PickingList:
        """
        Update the status of a picking list.

        Args:
            picking_list_id: The picking list ID
            status: The new status

        Returns:
            PickingList: The updated picking list

        Raises:
            ModelNotFoundError: If the picking list doesn't exist
            DatabaseError: For other database errors
        """
        try:
            # Get the picking list
            picking_list = self.get_by_id(picking_list_id)
            if not picking_list:
                error_msg = f"No picking list found with ID {picking_list_id}"
                logger.error(error_msg)
                raise ModelNotFoundError(error_msg)
            
            # Update the status
            picking_list.status = status
            
            # If marking as completed, set the completion date
            if status == PickingListStatus.COMPLETED and not picking_list.completed_at:
                picking_list.completed_at = datetime.utcnow()
            
            # If moving back from completed, clear the completion date
            if status != PickingListStatus.COMPLETED:
                picking_list.completed_at = None
            
            self.session.commit()
            
            logger.debug(f"Updated status of picking list ID {picking_list_id} to {status.name}")
            return picking_list
        except ModelNotFoundError:
            raise
        except Exception as e:
            self.session.rollback()
            error_msg = f"Error updating status of picking list ID {picking_list_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def add_item(self, 
                picking_list_id: int, 
                quantity_ordered: int,
                component_id: Optional[int] = None,
                material_id: Optional[int] = None,
                leather_id: Optional[int] = None,
                hardware_id: Optional[int] = None) -> PickingListItem:
        """
        Add an item to a picking list.

        Args:
            picking_list_id: The picking list ID
            quantity_ordered: The quantity to order
            component_id: Optional component ID
            material_id: Optional material ID
            leather_id: Optional leather ID
            hardware_id: Optional hardware ID

        Returns:
            PickingListItem: The created picking list item

        Raises:
            ModelNotFoundError: If the picking list doesn't exist
            ValueError: If no item reference is provided
            DatabaseError: For other database errors
        """
        try:
            # Get the picking list
            picking_list = self.get_by_id(picking_list_id)
            if not picking_list:
                error_msg = f"No picking list found with ID {picking_list_id}"
                logger.error(error_msg)
                raise ModelNotFoundError(error_msg)
            
            # Ensure at least one item reference is provided
            if not any([component_id, material_id, leather_id, hardware_id]):
                error_msg = "At least one of component_id, material_id, leather_id, or hardware_id must be provided"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Create the picking list item
            item = PickingListItem(
                picking_list_id=picking_list_id,
                component_id=component_id,
                material_id=material_id,
                leather_id=leather_id,
                hardware_id=hardware_id,
                quantity_ordered=quantity_ordered,
                quantity_picked=0,
                picked=False
            )
            
            self.session.add(item)
            self.session.commit()
            
            logger.debug(f"Added item to picking list ID {picking_list_id}")
            return item
        except ModelNotFoundError:
            raise
        except ValueError:
            raise
        except Exception as e:
            self.session.rollback()
            error_msg = f"Error adding item to picking list ID {picking_list_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def mark_item_as_picked(self, item_id: int, quantity: Optional[int] = None) -> PickingListItem:
        """
        Mark a picking list item as picked.

        Args:
            item_id: The item ID to mark
            quantity: Optional quantity picked (defaults to ordered quantity)

        Returns:
            PickingListItem: The updated picking list item

        Raises:
            ModelNotFoundError: If the item doesn't exist
            ValueError: If the quantity is invalid
            DatabaseError: For other database errors
        """
        try:
            # Get the item
            item = self.session.query(PickingListItem).filter(
                PickingListItem.id == item_id
            ).first()
            
            if not item:
                error_msg = f"No picking list item found with ID {item_id}"
                logger.error(error_msg)
                raise ModelNotFoundError(error_msg)
            
            # If quantity is specified, set it, otherwise pick all
            if quantity is not None:
                item.update_picked_quantity(quantity)
            else:
                item.mark_as_picked()
            
            self.session.commit()
            
            # Check if all items in the picking list are picked
            picking_list = self.get_with_items(item.picking_list_id)
            if picking_list and picking_list.is_complete():
                picking_list.mark_as_completed()
                self.session.commit()
                logger.debug(f"All items picked, marked picking list ID {item.picking_list_id} as completed")
            
            logger.debug(f"Marked picking list item ID {item_id} as picked")
            return item
        except ModelNotFoundError:
            raise
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"Validation error marking picking list item ID {item_id} as picked: {error_msg}")
            raise
        except Exception as e:
            self.session.rollback()
            error_msg = f"Error marking picking list item ID {item_id} as picked: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def reset_item_picking_status(self, item_id: int) -> PickingListItem:
        """
        Reset the picking status of an item.

        Args:
            item_id: The item ID to reset

        Returns:
            PickingListItem: The updated picking list item

        Raises:
            ModelNotFoundError: If the item doesn't exist
            DatabaseError: For other database errors
        """
        try:
            # Get the item
            item = self.session.query(PickingListItem).filter(
                PickingListItem.id == item_id
            ).first()
            
            if not item:
                error_msg = f"No picking list item found with ID {item_id}"
                logger.error(error_msg)
                raise ModelNotFoundError(error_msg)
            
            # Reset the picking status
            item.reset_picked_status()
            
            # If the picking list was completed, reset its status
            picking_list = self.get_by_id(item.picking_list_id)
            if picking_list and picking_list.status == PickingListStatus.COMPLETED:
                picking_list.reset_to_in_progress()
            
            self.session.commit()
            
            logger.debug(f"Reset picking status of picking list item ID {item_id}")
            return item
        except ModelNotFoundError:
            raise
        except Exception as e:
            self.session.rollback()
            error_msg = f"Error resetting picking status of picking list item ID {item_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)