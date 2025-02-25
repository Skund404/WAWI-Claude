# store_management/database/repositories/part_repository.py
"""
Repository for managing part-related database operations.

Provides specialized methods for retrieving and managing parts 
with advanced querying capabilities.
"""

from typing import List, Optional, Any
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
import logging

from di.core import inject
from services.interfaces import MaterialService
from models.part import Part, InventoryStatus
from models.supplier import Supplier

# Configure logging
logger = logging.getLogger(__name__)


class PartRepository:
    """
    Repository for Part model operations.

    Provides methods to interact with parts, including 
    retrieval, filtering, and advanced querying.
    """

    @inject(MaterialService)
    def __init__(self, session):
        """
        Initialize the PartRepository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def get_low_stock(self) -> List[Part]:
        """
        Retrieve parts with low stock levels.

        Returns:
            List[Part]: Parts with low or out of stock status
        """
        try:
            return (
                self.session.query(Part)
                .filter(Part.status.in_([
                    InventoryStatus.LOW_STOCK,
                    InventoryStatus.OUT_OF_STOCK
                ]))
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving low stock parts: {e}')
            raise

    def get_by_supplier(self, supplier_id: int) -> List[Part]:
        """
        Retrieve parts from a specific supplier.

        Args:
            supplier_id (int): Unique identifier of the supplier

        Returns:
            List[Part]: Parts from the specified supplier
        """
        try:
            return (
                self.session.query(Part)
                .filter(Part.supplier_id == supplier_id)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving parts for supplier {supplier_id}: {e}')
            raise

    def get_with_transactions(self, part_id: int) -> Optional[Part]:
        """
        Retrieve a part with its transaction history.

        Args:
            part_id (int): Unique identifier of the part

        Returns:
            Optional[Part]: Part with loaded transactions or None
        """
        try:
            return (
                self.session.query(Part)
                .options(joinedload(Part.transactions))
                .filter(Part.id == part_id)
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving part with transactions {part_id}: {e}')
            raise

    def search_parts(self, search_params: dict) -> List[Part]:
        """
        Search for parts based on multiple criteria.

        Args:
            search_params (dict): Search criteria including name, supplier, status, etc.

        Returns:
            List[Part]: List of parts matching the search criteria
        """
        try:
            query = self.session.query(Part)

            # Apply filters based on search parameters
            if 'name' in search_params:
                query = query.filter(Part.name.ilike(f"%{search_params['name']}%"))

            if 'supplier_id' in search_params:
                query = query.filter(Part.supplier_id == search_params['supplier_id'])

            if 'status' in search_params:
                query = query.filter(Part.status == search_params['status'])

            if 'min_stock' in search_params:
                query = query.filter(Part.stock_quantity >= search_params['min_stock'])

            if 'max_stock' in search_params:
                query = query.filter(Part.stock_quantity <= search_params['max_stock'])

            return query.all()
        except SQLAlchemyError as e:
            logger.error(f'Error searching parts: {e}')
            raise

    def update_stock(self, part_id: int, quantity_change: float) -> Part:
        """
        Update the stock quantity of a part.

        Args:
            part_id (int): Unique identifier of the part
            quantity_change (float): Amount to add or subtract from stock

        Returns:
            Part: Updated part instance

        Raises:
            ValueError: If stock update would result in negative stock
        """
        try:
            part = self.session.query(Part).get(part_id)

            if not part:
                raise ValueError(f"Part with ID {part_id} not found")

            # Calculate new stock
            new_stock = part.stock_quantity + quantity_change

            # Prevent negative stock
            if new_stock < 0:
                raise ValueError(
                    f"Insufficient stock. Cannot reduce below zero. Current: {part.stock_quantity}, Change: {quantity_change}")

            part.stock_quantity = new_stock

            # Update status based on stock level
            if new_stock == 0:
                part.status = InventoryStatus.OUT_OF_STOCK
            elif new_stock <= part.reorder_point:
                part.status = InventoryStatus.LOW_STOCK
            else:
                part.status = InventoryStatus.IN_STOCK

            self.session.commit()
            return part
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'Error updating part stock for part {part_id}: {e}')
            raise
        except ValueError as e:
            self.session.rollback()
            logger.error(f'Stock update validation error: {e}')
            raise

    def generate_inventory_report(self) -> dict:
        """
        Generate a comprehensive inventory report for parts.

        Returns:
            dict: Inventory report with key statistics
        """
        try:
            # Total parts
            total_parts = self.session.query(Part).count()

            # Low stock parts
            low_stock_parts = (
                self.session.query(Part)
                .filter(Part.status.in_([
                    InventoryStatus.LOW_STOCK,
                    InventoryStatus.OUT_OF_STOCK
                ]))
                .count()
            )

            # Parts by supplier
            supplier_parts = (
                self.session.query(Supplier.name, func.count(Part.id))
                .join(Part, Supplier.id == Part.supplier_id)
                .group_by(Supplier.name)
                .all()
            )

            return {
                'total_parts': total_parts,
                'low_stock_parts': low_stock_parts,
                'parts_by_supplier': dict(supplier_parts),
                'low_stock_percentage': (low_stock_parts / total_parts * 100) if total_parts > 0 else 0
            }
        except SQLAlchemyError as e:
            logger.error(f'Error generating inventory report: {e}')
            raise