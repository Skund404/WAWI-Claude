# database/repositories/purchase_item_repository.py
"""Repository for managing purchase item records."""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.models.purchase_item import PurchaseItem
from database.repositories.base_repository import BaseRepository
from database.exceptions import DatabaseError, ModelNotFoundError


class PurchaseItemRepository(BaseRepository[PurchaseItem]):
    """Repository for purchase item management operations."""

    def __init__(self, session: Session):
        """Initialize the PurchaseItem Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, PurchaseItem)
        self.logger = logging.getLogger(__name__)

    def get_by_purchase_id(self, purchase_id: int) -> List[PurchaseItem]:
        """Retrieve purchase items for a specific purchase.

        Args:
            purchase_id: ID of the purchase

        Returns:
            List of purchase items

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(PurchaseItem).filter(
                PurchaseItem.purchase_id == purchase_id
            )
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting purchase items by purchase_id: {str(e)}")
            raise DatabaseError(f"Database error retrieving purchase items: {str(e)}")

    def get_by_material_id(self, material_id: int) -> List[PurchaseItem]:
        """Retrieve purchase items for a specific material.

        Args:
            material_id: ID of the material

        Returns:
            List of purchase items

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(PurchaseItem).filter(
                PurchaseItem.material_id == material_id
            ).options(joinedload(PurchaseItem.purchase))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting purchase items by material_id: {str(e)}")
            raise DatabaseError(f"Database error retrieving purchase items: {str(e)}")

    def get_by_leather_id(self, leather_id: int) -> List[PurchaseItem]:
        """Retrieve purchase items for a specific leather.

        Args:
            leather_id: ID of the leather

        Returns:
            List of purchase items

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(PurchaseItem).filter(
                PurchaseItem.leather_id == leather_id
            ).options(joinedload(PurchaseItem.purchase))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting purchase items by leather_id: {str(e)}")
            raise DatabaseError(f"Database error retrieving purchase items: {str(e)}")

    def get_by_hardware_id(self, hardware_id: int) -> List[PurchaseItem]:
        """Retrieve purchase items for a specific hardware.

        Args:
            hardware_id: ID of the hardware

        Returns:
            List of purchase items

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(PurchaseItem).filter(
                PurchaseItem.hardware_id == hardware_id
            ).options(joinedload(PurchaseItem.purchase))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting purchase items by hardware_id: {str(e)}")
            raise DatabaseError(f"Database error retrieving purchase items: {str(e)}")

    def get_by_tool_id(self, tool_id: int) -> List[PurchaseItem]:
        """Retrieve purchase items for a specific tool.

        Args:
            tool_id: ID of the tool

        Returns:
            List of purchase items

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(PurchaseItem).filter(
                PurchaseItem.tool_id == tool_id
            ).options(joinedload(PurchaseItem.purchase))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting purchase items by tool_id: {str(e)}")
            raise DatabaseError(f"Database error retrieving purchase items: {str(e)}")

    def get_total_cost_by_purchase(self, purchase_id: int) -> float:
        """Calculate the total cost of all items in a purchase.

        Args:
            purchase_id: ID of the purchase

        Returns:
            Total cost of all items

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            result = self.session.query(
                func.sum(PurchaseItem.price * PurchaseItem.quantity)
            ).filter(
                PurchaseItem.purchase_id == purchase_id
            ).scalar()
            return float(result) if result is not None else 0.0
        except SQLAlchemyError as e:
            self.logger.error(f"Error calculating total purchase cost: {str(e)}")
            raise DatabaseError(f"Database error calculating total purchase cost: {str(e)}")

    def update_quantity(self, item_id: int, new_quantity: int) -> PurchaseItem:
        """Update the quantity of a purchase item.

        Args:
            item_id: ID of the purchase item
            new_quantity: New quantity value

        Returns:
            Updated purchase item

        Raises:
            ModelNotFoundError: If the purchase item is not found
            DatabaseError: If a database error occurs
        """
        try:
            purchase_item = self.get_by_id(item_id)
            if not purchase_item:
                raise ModelNotFoundError(f"Purchase item with ID {item_id} not found")

            purchase_item.quantity = new_quantity
            self.session.commit()
            return purchase_item
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating purchase item quantity: {str(e)}")
            raise DatabaseError(f"Database error updating purchase item quantity: {str(e)}")

    def update_price(self, item_id: int, new_price: float) -> PurchaseItem:
        """Update the price of a purchase item.

        Args:
            item_id: ID of the purchase item
            new_price: New price value

        Returns:
            Updated purchase item

        Raises:
            ModelNotFoundError: If the purchase item is not found
            DatabaseError: If a database error occurs
        """
        try:
            purchase_item = self.get_by_id(item_id)
            if not purchase_item:
                raise ModelNotFoundError(f"Purchase item with ID {item_id} not found")

            purchase_item.price = new_price
            self.session.commit()
            return purchase_item
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating purchase item price: {str(e)}")
            raise DatabaseError(f"Database error updating purchase item price: {str(e)}")

    def get_items_with_materials(self, purchase_id: int) -> List[PurchaseItem]:
        """Retrieve purchase items with material relationships loaded.

        Args:
            purchase_id: ID of the purchase

        Returns:
            List of purchase items with material relationships

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(PurchaseItem).filter(
                PurchaseItem.purchase_id == purchase_id,
                PurchaseItem.material_id.isnot(None)
            ).options(joinedload(PurchaseItem.material))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting purchase items with materials: {str(e)}")
            raise DatabaseError(f"Database error retrieving purchase items with materials: {str(e)}")

    def get_items_with_leathers(self, purchase_id: int) -> List[PurchaseItem]:
        """Retrieve purchase items with leather relationships loaded.

        Args:
            purchase_id: ID of the purchase

        Returns:
            List of purchase items with leather relationships

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(PurchaseItem).filter(
                PurchaseItem.purchase_id == purchase_id,
                PurchaseItem.leather_id.isnot(None)
            ).options(joinedload(PurchaseItem.leather))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting purchase items with leathers: {str(e)}")
            raise DatabaseError(f"Database error retrieving purchase items with leathers: {str(e)}")

    def get_items_with_hardware(self, purchase_id: int) -> List[PurchaseItem]:
        """Retrieve purchase items with hardware relationships loaded.

        Args:
            purchase_id: ID of the purchase

        Returns:
            List of purchase items with hardware relationships

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(PurchaseItem).filter(
                PurchaseItem.purchase_id == purchase_id,
                PurchaseItem.hardware_id.isnot(None)
            ).options(joinedload(PurchaseItem.hardware))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting purchase items with hardware: {str(e)}")
            raise DatabaseError(f"Database error retrieving purchase items with hardware: {str(e)}")

    def get_items_with_tools(self, purchase_id: int) -> List[PurchaseItem]:
        """Retrieve purchase items with tool relationships loaded.

        Args:
            purchase_id: ID of the purchase

        Returns:
            List of purchase items with tool relationships

        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            query = self.session.query(PurchaseItem).filter(
                PurchaseItem.purchase_id == purchase_id,
                PurchaseItem.tool_id.isnot(None)
            ).options(joinedload(PurchaseItem.tool))
            return query.all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting purchase items with tools: {str(e)}")
            raise DatabaseError(f"Database error retrieving purchase items with tools: {str(e)}")