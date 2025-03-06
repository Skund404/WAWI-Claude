"""
database/repositories/picking_list_repository.py - Repository for picking list data access
"""
import logging
from datetime import datetime
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from typing import Any, Dict, List, Optional, Tuple

from database.models.picking_list import PickingList, PickingListItem, PickingListStatus
from database.repositories.base_repository import BaseRepository

class PickingListRepository(BaseRepository):
    """Repository for handling picking list data access operations."""

    def __init__(self, session: Session):
        """Initialize the PickingList Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, PickingList)
        self.logger = logging.getLogger(__name__)

    def get_all(self) -> List[PickingList]:
        """
        Get all picking lists.

        Returns:
            List[PickingList]: List of all picking lists
        """
        try:
            return self.session.query(PickingList).order_by(PickingList.creation_date.desc()).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving all picking lists: {e}")
            raise

    def get_by_id(self, list_id: int) -> Optional[PickingList]:
        """
        Get a picking list by ID.

        Args:
            list_id: ID of the picking list to retrieve

        Returns:
            Optional[PickingList]: The picking list if found, otherwise None
        """
        try:
            return self.session.query(PickingList).filter(PickingList.id == list_id).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving picking list by ID {list_id}: {e}")
            raise

    def create(self, list_data: Dict[str, Any]) -> PickingList:
        """
        Create a new picking list.

        Args:
            list_data: Dictionary containing picking list data

        Returns:
            PickingList: The created picking list
        """
        try:
            picking_list = PickingList(
                name=list_data['name'],
                description=list_data.get('description'),
                status=list_data.get('status', PickingListStatus.DRAFT)
            )

            self.session.add(picking_list)
            self.session.flush()

            return picking_list
        except SQLAlchemyError as e:
            self.logger.error(f"Error creating picking list: {e}")
            self.session.rollback()
            raise

    def update(self, list_id: int, list_data: Dict[str, Any]) -> Optional[PickingList]:
        """
        Update an existing picking list.

        Args:
            list_id: ID of the picking list to update
            list_data: Dictionary containing updated picking list data

        Returns:
            Optional[PickingList]: The updated picking list if found, otherwise None
        """
        try:
            picking_list = self.get_by_id(list_id)
            if not picking_list:
                return None

            if 'name' in list_data:
                picking_list.name = list_data['name']
            if 'description' in list_data:
                picking_list.description = list_data['description']
            if 'status' in list_data:
                picking_list.status = list_data['status']

            picking_list.last_updated = datetime.now()
            self.session.flush()

            return picking_list
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating picking list {list_id}: {e}")
            self.session.rollback()
            raise

    def delete(self, list_id: int) -> bool:
        """
        Delete a picking list.

        Args:
            list_id: ID of the picking list to delete

        Returns:
            bool: True if successfully deleted, False if not found
        """
        try:
            picking_list = self.get_by_id(list_id)
            if not picking_list:
                return False

            self.session.delete(picking_list)
            self.session.flush()

            return True
        except SQLAlchemyError as e:
            self.logger.error(f"Error deleting picking list {list_id}: {e}")
            self.session.rollback()
            raise

    def get_items(self, list_id: int) -> List[PickingListItem]:
        """
        Get all items for a specific picking list.

        Args:
            list_id: ID of the picking list

        Returns:
            List[PickingListItem]: List of items in the picking list
        """
        try:
            return self.session.query(PickingListItem).filter(
                PickingListItem.list_id == list_id
            ).order_by(PickingListItem.id).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving items for picking list {list_id}: {e}")
            raise

    def get_item_by_id(self, item_id: int) -> Optional[PickingListItem]:
        """
        Get a picking list item by ID.

        Args:
            item_id: ID of the item to retrieve

        Returns:
            Optional[PickingListItem]: The item if found, otherwise None
        """
        try:
            return self.session.query(PickingListItem).filter(
                PickingListItem.id == item_id
            ).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving picking list item {item_id}: {e}")
            raise

    def add_item(self, item_data: Dict[str, Any]) -> PickingListItem:
        """
        Add an item to a picking list.

        Args:
            item_data: Dictionary containing item data

        Returns:
            PickingListItem: The created item
        """
        try:
            item = PickingListItem(
                list_id=item_data['list_id'],
                material_id=item_data['material_id'],
                required_quantity=item_data['required_quantity'],
                picked_quantity=item_data.get('picked_quantity', 0.0),
                unit=item_data.get('unit', 'pcs'),
                storage_location=item_data.get('storage_location'),
                notes=item_data.get('notes'),
                is_picked=item_data.get('is_picked', False)
            )

            self.session.add(item)
            self.session.flush()

            return item
        except SQLAlchemyError as e:
            self.logger.error(f"Error adding item to picking list: {e}")
            self.session.rollback()
            raise

    def update_item(self, item_id: int, item_data: Dict[str, Any]) -> Optional[PickingListItem]:
        """
        Update a picking list item.

        Args:
            item_id: ID of the item to update
            item_data: Dictionary containing updated item data

        Returns:
            Optional[PickingListItem]: The updated item if found, otherwise None
        """
        try:
            item = self.get_item_by_id(item_id)
            if not item:
                return None

            # Update properties if provided
            for key, value in item_data.items():
                if hasattr(item, key):
                    setattr(item, key, value)

            self.session.flush()

            return item
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating picking list item {item_id}: {e}")
            self.session.rollback()
            raise

    def remove_item(self, item_id: int) -> bool:
        """
        Remove an item from a picking list.

        Args:
            item_id: ID of the item to remove

        Returns:
            bool: True if successfully removed, False if not found
        """
        try:
            item = self.get_item_by_id(item_id)
            if not item:
                return False

            self.session.delete(item)
            self.session.flush()

            return True
        except SQLAlchemyError as e:
            self.logger.error(f"Error removing picking list item {item_id}: {e}")
            self.session.rollback()
            raise

    def filter_by_status(self, status: PickingListStatus) -> List[PickingList]:
        """
        Filter picking lists by status.

        Args:
            status: Status to filter by

        Returns:
            List[PickingList]: Filtered picking lists
        """
        try:
            return self.session.query(PickingList).filter(
                PickingList.status == status
            ).order_by(PickingList.creation_date.desc()).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error filtering picking lists by status {status}: {e}")
            raise

    def search(self, search_term: str) -> List[PickingList]:
        """
        Search picking lists by name or description.

        Args:
            search_term: Term to search for

        Returns:
            List[PickingList]: Matching picking lists
        """
        try:
            search_pattern = f"%{search_term}%"
            return self.session.query(PickingList).filter(
                or_(
                    PickingList.name.ilike(search_pattern),
                    PickingList.description.ilike(search_pattern)
                )
            ).order_by(PickingList.creation_date.desc()).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error searching picking lists with term '{search_term}': {e}")
            raise

    def get_picking_lists_with_items(self) -> List[PickingList]:
        """
        Get all picking lists with their items loaded.

        Returns:
            List[PickingList]: List of picking lists with items eager loaded
        """
        try:
            return self.session.query(PickingList).options(
                joinedload(PickingList.items)
            ).order_by(PickingList.creation_date.desc()).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving picking lists with items: {e}")
            raise