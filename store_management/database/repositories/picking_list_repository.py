# database/repositories/picking_list_item_repository.py
"""
Repository for Picking List Item operations with advanced querying.
"""

from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from logging import getLogger

from database.repositories.base_repository import BaseRepository
from database.models.picking_list_item import PickingListItem
from database.exceptions import RepositoryError, ModelNotFoundError

class PickingListItemRepository(BaseRepository):
    """
    Repository for managing Picking List Item database operations.
    Supports advanced querying based on ER diagram relationships.
    """
    def __init__(self, session: Session):
        """
        Initialize the Picking List Item Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, PickingListItem)
        self.logger = getLogger(__name__)

    def get_by_picking_list(self, picking_list_id: int) -> List[PickingListItem]:
        """
        Retrieve all picking list items for a specific picking list.

        Args:
            picking_list_id (int): ID of the picking list

        Returns:
            List[PickingListItem]: List of picking list items
        """
        try:
            query = select(PickingListItem).where(
                PickingListItem.picking_list_id == picking_list_id
            )
            return list(self.session.execute(query).scalars().all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving picking list items: {str(e)}")
            raise RepositoryError(f"Failed to retrieve picking list items: {str(e)}")

    def get_by_component(self, component_id: int) -> List[PickingListItem]:
        """
        Retrieve all picking list items for a specific component.

        Args:
            component_id (int): ID of the component

        Returns:
            List[PickingListItem]: List of picking list items
        """
        try:
            query = select(PickingListItem).where(
                PickingListItem.component_id == component_id
            )
            return list(self.session.execute(query).scalars().all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving picking list items for component: {str(e)}")
            raise RepositoryError(f"Failed to retrieve picking list items for component: {str(e)}")

    def get_by_material(self, material_id: int) -> List[PickingListItem]:
        """
        Retrieve all picking list items for a specific material.

        Args:
            material_id (int): ID of the material

        Returns:
            List[PickingListItem]: List of picking list items
        """
        try:
            query = select(PickingListItem).where(
                PickingListItem.material_id == material_id
            )
            return list(self.session.execute(query).scalars().all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving picking list items for material: {str(e)}")
            raise RepositoryError(f"Failed to retrieve picking list items for material: {str(e)}")

    def get_partially_complete_items(self) -> List[PickingListItem]:
        """
        Retrieve picking list items where quantity picked is less than quantity ordered.

        Returns:
            List[PickingListItem]: List of partially complete picking list items
        """
        try:
            query = select(PickingListItem).where(
                PickingListItem.quantity_picked < PickingListItem.quantity_ordered
            )
            return list(self.session.execute(query).scalars().all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving partially complete picking list items: {str(e)}")
            raise RepositoryError(f"Failed to retrieve partially complete picking list items: {str(e)}")