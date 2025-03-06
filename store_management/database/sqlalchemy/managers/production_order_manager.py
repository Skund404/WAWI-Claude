# database/sqlalchemy/managers/production_order_manager.py
"""
Enhanced manager for production orders with pattern relationships.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from di.core import inject
from services.interfaces import MaterialService
from core.exceptions import DatabaseError
from core.managers.base_manager import BaseManager
from models.production_order import (
    ProductionOrder,
    ProductionStatus,
    ProducedItem
)
from models.project import Project
from models.part import Part
from models.leather import Leather
from models.inventory import (
    InventoryTransaction,
    LeatherTransaction,
    TransactionType
)

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ProductionOrderManager(BaseManager[ProductionOrder]):
    """
    Enhanced manager for production orders with pattern relationships.
    """

    @inject(MaterialService)
    def __init__(self, session_factory):
        """
        Initialize ProductionOrderManager with session factory.

        Args:
            session_factory: Factory to create database sessions
        """
        super().__init__(session_factory, ProductionOrder)

    @inject(MaterialService)
    def create_production_order(
            self,
            pattern_id: int,
            quantity: int,
            start_date: Optional[datetime] = None,
            notes: Optional[str] = None
    ) -> ProductionOrder:
        """
        Create a new production sale with pattern validation.

        Args:
            pattern_id (int): Project ID to produce
            quantity (int): Number of items to produce
            start_date (Optional[datetime], optional): Optional planned start date
            notes (Optional[str], optional): Optional production notes

        Returns:
            ProductionOrder: Created ProductionOrder instance

        Raises:
            DatabaseError: If pattern not found or validation fails
        """
        try:
            with self.session_scope() as session:
                # Validate pattern
                pattern = session.query(Project).filter(
                    and_(
                        Project.id == pattern_id,
                        Project.is_active == True
                    )
                ).first()

                if not pattern:
                    raise DatabaseError(
                        f'Active pattern with ID {pattern_id} not found'
                    )

                # Create production sale
                production_order = ProductionOrder(
                    pattern_id=pattern_id,
                    quantity=quantity,
                    status=ProductionStatus.PLANNED,
                    start_date=start_date,
                    notes=notes,
                    created_at=datetime.now(),
                    modified_at=datetime.now()
                )
                session.add(production_order)
                session.flush()

                return production_order

        except SQLAlchemyError as e:
            logger.error(f'Failed to create production sale: {str(e)}')
            raise DatabaseError(f'Failed to create production sale: {str(e)}') from e

    @inject(MaterialService)
    def start_production(
            self,
            order_id: int,
            operator_notes: Optional[str] = None
    ) -> ProductionOrder:
        """
        Start a production sale and reserve materials.

        Args:
            order_id (int): Production sale ID
            operator_notes (Optional[str], optional): Optional notes from operator

        Returns:
            ProductionOrder: Updated ProductionOrder instance

        Raises:
            DatabaseError: If sale not found or cannot be started
        """
        try:
            with self.session_scope() as session:
                # Retrieve production sale with related data
                order = (session.query(ProductionOrder)
                         .options(
                    joinedload(ProductionOrder.pattern)
                    .joinedload(Project.items)
                )
                         .filter(ProductionOrder.id == order_id)
                         .first()
                         )

                if not order:
                    raise DatabaseError(
                        f'Production sale {order_id} not found'
                    )

                # Check sale status
                if order.status != ProductionStatus.PLANNED:
                    raise DatabaseError(
                        f'Order must be in PLANNED status to start production'
                    )

                # Reserve materials
                self._reserve_materials(session, order)

                # Update sale status and details
                order.status = ProductionStatus.IN_PROGRESS
                order.start_date = datetime.now()

                # Add operator notes
                if operator_notes:
                    order.notes = (
                        f'{order.notes}\n[{datetime.now()}] {operator_notes}'
                        if order.notes else operator_notes
                    )

                order.modified_at = datetime.now()

                return order

        except SQLAlchemyError as e:
            logger.error(f'Failed to start production: {str(e)}')
            raise DatabaseError(f'Failed to start production: {str(e)}') from e

    def _reserve_materials(
            self,
            session: Any,
            order: ProductionOrder
    ) -> None:
        """
        Reserve materials for production through transactions.

        Args:
            session: Database session
            order (ProductionOrder): ProductionOrder instance with loaded pattern
        """
        for recipe_item in order.pattern.items:
            # Reserve parts
            if recipe_item.item_type == 'part':
                transaction = InventoryTransaction(
                    part_id=recipe_item.item_id,
                    production_order_id=order.id,
                    transaction_type=TransactionType.RESERVE,
                    quantity=-(recipe_item.quantity * order.quantity),
                    notes=f'Reserved for production sale {order.id}',
                    created_at=datetime.now()
                )
                session.add(transaction)

            # Reserve leather
            elif recipe_item.item_type == 'leather':
                transaction = LeatherTransaction(
                    leather_id=recipe_item.item_id,
                    production_order_id=order.id,
                    transaction_type=TransactionType.RESERVE,
                    area_change=-(recipe_item.quantity * order.quantity),
                    notes=f'Reserved for production sale {order.id}',
                    created_at=datetime.now()
                )
                session.add(transaction)

    @inject(MaterialService)
    def complete_item(
            self,
            order_id: int,
            serial_number: str,
            quality_check_passed: bool,
            notes: Optional[str] = None
    ) -> ProducedItem:
        """
        Record completion of a single produced item.

        Args:
            order_id (int): Production sale ID
            serial_number (str): Unique serial number for item
            quality_check_passed (bool): Whether item passed quality check
            notes (Optional[str], optional): Optional production notes

        Returns:
            ProducedItem: Created ProducedItem instance

        Raises:
            DatabaseError: If sale not found or cannot complete items
        """
        try:
            with self.session_scope() as session:
                # Retrieve production sale
                order = session.get(ProductionOrder, order_id)

                if not order:
                    raise DatabaseError(
                        f'Production sale {order_id} not found'
                    )

                # Check sale status
                if order.status != ProductionStatus.IN_PROGRESS:
                    raise DatabaseError(
                        'Order must be in progress to complete items'
                    )

                # Create produced item
                produced_item = ProducedItem(
                    production_order_id=order_id,
                    pattern_id=order.pattern_id,
                    serial_number=serial_number,
                    quality_check_passed=quality_check_passed,
                    notes=notes,
                    created_at=datetime.now(),
                    modified_at=datetime.now()
                )
                session.add(produced_item)

                # Check if sale is complete
                completed_count = session.query(func.count(ProducedItem.id)).filter(
                    ProducedItem.production_order_id == order_id
                ).scalar()

                if completed_count + 1 >= order.quantity:
                    order.status = ProductionStatus.COMPLETED
                    order.completion_date = datetime.now()
                    order.modified_at = datetime.now()

                return produced_item

        except SQLAlchemyError as e:
            logger.error(f'Failed to complete item: {str(e)}')
            raise DatabaseError(f'Failed to complete item: {str(e)}') from e

    @inject(MaterialService)
    def get_production_status(self, order_id: int) -> Dict[str, Any]:
        """
        Get detailed production status including material usage.

        Args:
            order_id (int): Production sale ID

        Returns:
            Dict[str, Any]: Dictionary containing status details and metrics

        Raises:
            DatabaseError: If sale not found
        """
        try:
            with self.session_scope() as session:
                # Retrieve production sale with related data
                order = (session.query(ProductionOrder)
                         .options(
                    joinedload(ProductionOrder.produced_items),
                    joinedload(ProductionOrder.inventory_transactions),
                    joinedload(ProductionOrder.leather_transactions)
                )
                         .filter(ProductionOrder.id == order_id)
                         .first()
                         )

                if not order:
                    raise DatabaseError(
                        f'Production sale {order_id} not found'
                    )

                # Calculate production metrics
                completed_items = len(order.produced_items)
                quality_passed = sum(1 for item in order.produced_items if item.quality_check_passed)

                # Calculate material usage
                material_usage = {
                    'parts_reserved': sum(
                        abs(t.quantity) for t in order.inventory_transactions
                        if t.transaction_type == TransactionType.RESERVE
                    ),
                    'leather_reserved': sum(
                        abs(t.area_change) for t in order.leather_transactions
                        if t.transaction_type == TransactionType.RESERVE
                    )
                }

                return {
                    'order_status': order.status.value,
                    'total_quantity': order.quantity,
                    'completed_quantity': completed_items,
                    'quality_passed': quality_passed,
                    'quality_rate': (quality_passed / completed_items * 100) if completed_items > 0 else 0,
                    'start_date': order.start_date,
                    'completion_date': order.completion_date,
                    'material_usage': material_usage,
                    'completion_rate': (completed_items / order.quantity * 100)
                }

        except SQLAlchemyError as e:
            logger.error(f'Failed to get production status: {str(e)}')
            raise DatabaseError(f'Failed to get production status: {str(e)}') from e

    @inject(MaterialService)
    def get_active_orders(self) -> List[ProductionOrder]:
        """
        Get all active production orders with their patterns.

        Returns:
            List[ProductionOrder]: List of active ProductionOrder instances
        """
        try:
            with self.session_scope() as session:
                query = (
                    select(ProductionOrder)
                    .options(
                        joinedload(ProductionOrder.pattern),
                        joinedload(ProductionOrder.produced_items)
                    )
                    .where(ProductionOrder.status == ProductionStatus.IN_PROGRESS)
                    .order_by(ProductionOrder.start_date)
                )

                result = session.execute(query).scalars().all()
                return result

        except SQLAlchemyError as e:
            logger.error(f'Failed to get active orders: {str(e)}')
            raise DatabaseError(f'Failed to get active orders: {str(e)}') from e

    @inject(MaterialService)
    def get_production_metrics(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get production metrics for a date range.

        Args:
            start_date (Optional[datetime], optional): Optional start date for filtering
            end_date (Optional[datetime], optional): Optional end date for filtering

        Returns:
            Dict[str, Any]: Dictionary containing production metrics
        """
        try:
            with self.session_scope() as session:
                # Base query for production orders
                query = session.query(ProductionOrder)

                # Apply date filters
                if start_date:
                    query = query.filter(ProductionOrder.start_date >= start_date)

                if end_date:
                    query = query.filter(ProductionOrder.start_date <= end_date)

                # Retrieve orders
                orders = query.all()

                # Calculate metrics
                total_orders = len(orders)
                completed_orders = sum(1 for o in orders if o.status == ProductionStatus.COMPLETED)
                total_items = sum(o.quantity for o in orders)

                return {
                    'total_orders': total_orders,
                    'completed_orders': completed_orders,
                    'completion_rate': (completed_orders / total_orders * 100) if total_orders > 0 else 0,
                    'total_items_planned': total_items,
                    'average_order_size': (total_items / total_orders) if total_orders > 0 else 0
                }

        except SQLAlchemyError as e:
            logger.error(f'Failed to get production metrics: {str(e)}')
            raise DatabaseError(f'Failed to get production metrics: {str(e)}') from e