# database/sqlalchemy/managers/inventory_manager.py
"""
Comprehensive inventory manager for handling Part and Leather inventory.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union

from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from di.core import inject
from services.interfaces import MaterialService
from core.exceptions import DatabaseError
from core.managers.base_manager import BaseManager
from models.part import Part
from models.leather import Leather
from models.inventory import (
    InventoryTransaction,
    LeatherTransaction,
    TransactionType,
    InventoryStatus
)

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class InventoryManager:
    """
    Comprehensive inventory manager handling both Part and Leather inventory.
    Uses separate BaseManager instances for each model type.
    """

    @inject(MaterialService)
    def __init__(self, session_factory):
        """
        Initialize inventory managers with session factory.

        Args:
            session_factory: Factory to create database sessions
        """
        self.session_factory = session_factory
        self.part_manager = BaseManager[Part](session_factory, Part)
        self.leather_manager = BaseManager[Leather](session_factory, Leather)

    @inject(MaterialService)
    def add_part(self, data: Dict[str, Any]) -> Part:
        """
        Add a new part to inventory.

        Args:
            data (Dict[str, Any]): Part data including initial stock levels

        Returns:
            Part: Created Part instance

        Raises:
            DatabaseError: If validation or creation fails
        """
        # Validate required fields
        required_fields = ['name', 'current_stock', 'min_stock_level']
        missing_fields = [f for f in required_fields if f not in data]

        if missing_fields:
            raise DatabaseError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

        try:
            with self.session_factory() as session:
                # Create part
                part = Part(**data)
                session.add(part)
                session.flush()

                # Add initial stock transaction if stock is positive
                if part.current_stock > 0:
                    transaction = InventoryTransaction(
                        part_id=part.id,
                        transaction_type=TransactionType.INITIAL,
                        quantity=part.current_stock,
                        notes='Initial stock'
                    )
                    session.add(transaction)

                session.commit()
                return part

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f'Failed to add part: {str(e)}')
            raise DatabaseError(f'Failed to add part: {str(e)}') from e

    @inject(MaterialService)
    def add_leather(self, data: Dict[str, Any]) -> Leather:
        """
        Add a new leather to inventory.

        Args:
            data (Dict[str, Any]): Leather data including initial area

        Returns:
            Leather: Created Leather instance

        Raises:
            DatabaseError: If validation or creation fails
        """
        # Validate required fields
        required_fields = ['type', 'color', 'thickness', 'available_area_sqft']
        missing_fields = [f for f in required_fields if f not in data]

        if missing_fields:
            raise DatabaseError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

        try:
            with self.session_factory() as session:
                # Create leather
                leather = Leather(**data)
                session.add(leather)
                session.flush()

                # Add initial stock transaction if area is positive
                if leather.available_area_sqft > 0:
                    transaction = LeatherTransaction(
                        leather_id=leather.id,
                        transaction_type=TransactionType.INITIAL,
                        area_change=leather.available_area_sqft,
                        notes='Initial stock'
                    )
                    session.add(transaction)

                session.commit()
                return leather

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f'Failed to add leather: {str(e)}')
            raise DatabaseError(f'Failed to add leather: {str(e)}') from e

    @inject(MaterialService)
    def update_part_stock(
            self,
            part_id: int,
            quantity_change: int,
            transaction_type: TransactionType,
            notes: Optional[str] = None
    ) -> Part:
        """
        Update part stock levels with transaction tracking.

        Args:
            part_id (int): Part ID
            quantity_change (int): Change in quantity (positive or negative)
            transaction_type (TransactionType): Type of transaction
            notes (Optional[str], optional): Transaction notes

        Returns:
            Part: Updated Part instance

        Raises:
            DatabaseError: If update fails or stock would become negative
        """
        with self.session_factory() as session:
            try:
                # Retrieve part
                part = session.get(Part, part_id)

                if not part:
                    raise DatabaseError(f'Part {part_id} not found')

                # Calculate new stock
                new_stock = part.current_stock + quantity_change

                # Check for negative stock
                if new_stock < 0:
                    raise DatabaseError('Stock cannot be negative')

                # Update stock and modification time
                part.current_stock = new_stock
                part.modified_at = datetime.utcnow()

                # Create transaction
                transaction = InventoryTransaction(
                    part_id=part_id,
                    transaction_type=transaction_type,
                    quantity=abs(quantity_change),
                    notes=notes
                )
                session.add(transaction)

                # Update inventory status
                if new_stock <= part.min_stock_level:
                    part.status = InventoryStatus.LOW_STOCK
                elif new_stock == 0:
                    part.status = InventoryStatus.OUT_OF_STOCK
                else:
                    part.status = InventoryStatus.IN_STOCK

                session.commit()
                return part

            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f'Failed to update part stock: {str(e)}')
                raise DatabaseError(f'Failed to update part stock: {str(e)}') from e

    @inject(MaterialService)
    def update_leather_stock(
            self,
            leather_id: int,
            area_change: float,
            transaction_type: TransactionType,
            notes: Optional[str] = None
    ) -> Leather:
        """
        Update leather stock levels with transaction tracking.

        Args:
            leather_id (int): Leather ID
            area_change (float): Change in area (positive or negative)
            transaction_type (TransactionType): Type of transaction
            notes (Optional[str], optional): Transaction notes

        Returns:
            Leather: Updated Leather instance

        Raises:
            DatabaseError: If update fails or area would become negative
        """
        with self.session_factory() as session:
            try:
                # Retrieve leather
                leather = session.get(Leather, leather_id)

                if not leather:
                    raise DatabaseError(f'Leather {leather_id} not found')

                # Calculate new area
                new_area = leather.available_area_sqft + area_change

                # Check for negative area
                if new_area < 0:
                    raise DatabaseError('Area cannot be negative')

                # Update area and modification time
                leather.available_area_sqft = new_area
                leather.modified_at = datetime.utcnow()

                # Create transaction
                transaction = LeatherTransaction(
                    leather_id=leather_id,
                    transaction_type=transaction_type,
                    area_change=abs(area_change),
                    notes=notes
                )
                session.add(transaction)

                # Update inventory status
                if new_area <= leather.min_area_sqft:
                    leather.status = InventoryStatus.LOW_STOCK
                elif new_area == 0:
                    leather.status = InventoryStatus.OUT_OF_STOCK
                else:
                    leather.status = InventoryStatus.IN_STOCK

                session.commit()
                return leather

            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f'Failed to update leather stock: {str(e)}')
                raise DatabaseError(f'Failed to update leather stock: {str(e)}') from e

    @inject(MaterialService)
    def get_part_with_transactions(self, part_id: int) -> Optional[Part]:
        """
        Get part with its transaction history.

        Args:
            part_id (int): Part ID

        Returns:
            Optional[Part]: Part instance with transactions loaded or None if not found
        """
        with self.session_factory() as session:
            query = select(Part).options(joinedload(Part.transactions)).filter(Part.id == part_id)
            return session.execute(query).scalar()

    @inject(MaterialService)
    def get_leather_with_transactions(self, leather_id: int) -> Optional[Leather]:
        """
        Get leather with its transaction history.

        Args:
            leather_id (int): Leather ID

        Returns:
            Optional[Leather]: Leather instance with transactions loaded or None if not found
        """
        with self.session_factory() as session:
            query = select(Leather).options(joinedload(Leather.transactions)).filter(Leather.id == leather_id)
            return session.execute(query).scalar()

    @inject(MaterialService)
    def get_low_stock_parts(self, include_out_of_stock: bool = True) -> List[Part]:
        """
        Get all parts with low stock levels.

        Args:
            include_out_of_stock (bool, optional): Whether to include out of stock items. Defaults to True.

        Returns:
            List[Part]: List of Part instances with low stock
        """
        with self.session_factory() as session:
            query = select(Part).filter(Part.current_stock <= Part.min_stock_level)

            if not include_out_of_stock:
                query = query.filter(Part.current_stock > 0)

            return list(session.execute(query).scalars())

    @inject(MaterialService)
    def get_low_stock_leather(self, include_out_of_stock: bool = True) -> List[Leather]:
        """
        Get all leather with low stock levels.

        Args:
            include_out_of_stock (bool, optional): Whether to include out of stock items. Defaults to True.

        Returns:
            List[Leather]: List of Leather instances with low stock
        """
        with self.session_factory() as session:
            query = select(Leather).filter(Leather.available_area_sqft <= Leather.min_area_sqft)

            if not include_out_of_stock:
                query = query.filter(Leather.available_area_sqft > 0)

            return list(session.execute(query).scalars())

    @inject(MaterialService)
    def get_inventory_transactions(
            self,
            part_id: Optional[int] = None,
            leather_id: Optional[int] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Union[InventoryTransaction, LeatherTransaction]]:
        """
        Get inventory transactions with optional filtering.

        Args:
            part_id (Optional[int], optional): Part ID to filter by
            leather_id (Optional[int], optional): Leather ID to filter by
            start_date (Optional[datetime], optional): Start date for date range
            end_date (Optional[datetime], optional): End date for date range

        Returns:
            List[Union[InventoryTransaction, LeatherTransaction]]: List of transaction instances
        """
        with self.session_factory() as session:
            transactions = []

            # Retrieve part transactions if part_id is provided
            if part_id:
                query = select(InventoryTransaction).filter(InventoryTransaction.part_id == part_id)

                if start_date:
                    query = query.filter(InventoryTransaction.timestamp >= start_date)

                if end_date:
                    query = query.filter(InventoryTransaction.timestamp <= end_date)

                transactions.extend(session.execute(query).scalars())

            # Retrieve leather transactions if leather_id is provided
            if leather_id:
                query = select(LeatherTransaction).filter(LeatherTransaction.leather_id == leather_id)

                if start_date:
                    query = query.filter(LeatherTransaction.timestamp >= start_date)

                if end_date:
                    query = query.filter(LeatherTransaction.timestamp <= end_date)

                transactions.extend(session.execute(query).scalars())

            # Sort transactions by timestamp in descending sale
            return sorted(transactions, key=lambda x: x.timestamp, reverse=True)

    @inject(MaterialService)
    def get_inventory_value(self) -> Dict[str, float]:
        """
        Calculate total value of inventory.

        Returns:
            Dict[str, float]: Dictionary with total values for parts and leather
        """
        with self.session_factory() as session:
            parts_value = session.query(func.sum(Part.current_stock * Part.price)).scalar() or 0.0
            leather_value = session.query(
                func.sum(Leather.available_area_sqft * Leather.price_per_sqft)).scalar() or 0.0

            return {
                'parts_value': parts_value,
                'leather_value': leather_value,
                'total_value': parts_value + leather_value
            }

    @inject(MaterialService)
    def search_inventory(self, search_term: str) -> Dict[str, List]:
        """
        Search both parts and leather inventory.

        Args:
            search_term (str): Term to search for

        Returns:
            Dict[str, List]: Dictionary with matching parts and leather items
        """
        with self.session_factory() as session:
            # Search parts
            parts_query = select(Part).filter(
                or_(
                    Part.name.ilike(f'%{search_term}%'),
                    Part.color.ilike(f'%{search_term}%'),
                    Part.notes.ilike(f'%{search_term}%')
                )
            )
            parts = list(session.execute(parts_query).scalars())

            # Search leather
            leather_query = select(Leather).filter(
                or_(
                    Leather.type.ilike(f'%{search_term}%'),
                    Leather.color.ilike(f'%{search_term}%'),
                    Leather.notes.ilike(f'%{search_term}%')
                )
            )
            leather = list(session.execute(leather_query).scalars())

            return {'parts': parts, 'leather': leather}

    # Additional methods can be added as needed...