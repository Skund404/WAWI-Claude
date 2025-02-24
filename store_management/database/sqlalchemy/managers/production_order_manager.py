# database/sqlalchemy/managers/production_order_manager.py

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.sqlalchemy.base_manager import BaseManager
from database.sqlalchemy.models_file import (
    ProductionOrder,
    Project,
    ProducedItem,
    InventoryTransaction,
    LeatherTransaction,
    ProductionStatus,
    TransactionType
)
from utils.error_handler import DatabaseError
from utils.logger import logger


class ProductionOrderManager(BaseManager[ProductionOrder]):
    """Enhanced manager for production orders with pattern relationships."""

    def __init__(self, session_factory):
        """Initialize ProductionOrderManager with session factory."""
        super().__init__(session_factory, ProductionOrder)

    def create_production_order(
            self,
            recipe_id: int,
            quantity: int,
            start_date: Optional[datetime] = None,
            notes: Optional[str] = None
    ) -> ProductionOrder:
        """Create a new production order with pattern validation.

        Args:
            recipe_id: Project ID to produce
            quantity: Number of items to produce
            start_date: Optional planned start date
            notes: Optional production notes

        Returns:
            Created ProductionOrder instance

        Raises:
            DatabaseError: If pattern not found or validation fails
        """
        try:
            with self.session_scope() as session:
                # Verify pattern exists and is active
                pattern = session.query(Project).filter(
                    and_(Project.id == recipe_id, Project.is_active == True)
                ).first()

                if not pattern:
                    raise DatabaseError(
                        f"Active pattern with ID {recipe_id} not found"
                    )

                # Create production order
                production_order = ProductionOrder(
                    recipe_id=recipe_id,
                    quantity=quantity,
                    status=ProductionStatus.PLANNED,
                    start_date=start_date,
                    notes=notes,
                    created_at=datetime.now(),
                    modified_at=datetime.now()
                )
                session.add(production_order)
                session.flush()  # Get ID for the production order

                return production_order

        except SQLAlchemyError as e:
            logger.error(f"Failed to create production order: {str(e)}")
            raise DatabaseError(f"Failed to create production order: {str(e)}")

    def start_production(
            self,
            order_id: int,
            operator_notes: Optional[str] = None
    ) -> ProductionOrder:
        """Start a production order and reserve materials.

        Args:
            order_id: Production order ID
            operator_notes: Optional notes from operator

        Returns:
            Updated ProductionOrder instance
        """
        try:
            with self.session_scope() as session:
                order = (
                    session.query(ProductionOrder)
                    .options(
                        joinedload(ProductionOrder.pattern)
                        .joinedload(Project.items)
                    )
                    .filter(ProductionOrder.id == order_id)
                    .first()
                )

                if not order:
                    raise DatabaseError(f"Production order {order_id} not found")

                if order.status != ProductionStatus.PLANNED:
                    raise DatabaseError(
                        f"Order must be in PLANNED status to start production"
                    )

                # Reserve materials through inventory transactions
                self._reserve_materials(session, order)

                # Update order status
                order.status = ProductionStatus.IN_PROGRESS
                order.start_date = datetime.now()
                if operator_notes:
                    order.notes = (
                        f"{order.notes}\n[{datetime.now()}] {operator_notes}"
                        if order.notes
                        else operator_notes
                    )
                order.modified_at = datetime.now()

                return order

        except SQLAlchemyError as e:
            logger.error(f"Failed to start production: {str(e)}")
            raise DatabaseError(f"Failed to start production: {str(e)}")

    def _reserve_materials(
            self,
            session: Any,
            order: ProductionOrder
    ) -> None:
        """Reserve materials for production through transactions.

        Args:
            session: Database session
            order: ProductionOrder instance with loaded pattern
        """
        for recipe_item in order.pattern.items:
            if recipe_item.part_id:
                transaction = InventoryTransaction(
                    part_id=recipe_item.part_id,
                    production_order_id=order.id,
                    transaction_type=TransactionType.RESERVE,
                    quantity=-(recipe_item.quantity * order.quantity),
                    notes=f"Reserved for production order {order.id}",
                    created_at=datetime.now()
                )
                session.add(transaction)

            if recipe_item.leather_id:
                transaction = LeatherTransaction(
                    leather_id=recipe_item.leather_id,
                    production_order_id=order.id,
                    transaction_type=TransactionType.RESERVE,
                    area_change=-(recipe_item.area * order.quantity),
                    notes=f"Reserved for production order {order.id}",
                    created_at=datetime.now()
                )
                session.add(transaction)

    def complete_item(
            self,
            order_id: int,
            serial_number: str,
            quality_check_passed: bool,
            notes: Optional[str] = None
    ) -> ProducedItem:
        """Record completion of a single produced item.

        Args:
            order_id: Production order ID
            serial_number: Unique serial number for item
            quality_check_passed: Whether item passed quality check
            notes: Optional production notes

        Returns:
            Created ProducedItem instance
        """
        try:
            with self.session_scope() as session:
                order = session.get(ProductionOrder, order_id)
                if not order:
                    raise DatabaseError(f"Production order {order_id} not found")

                if order.status != ProductionStatus.IN_PROGRESS:
                    raise DatabaseError("Order must be in progress to complete items")

                # Create produced item record
                produced_item = ProducedItem(
                    production_order_id=order_id,
                    recipe_id=order.recipe_id,
                    serial_number=serial_number,
                    quality_check_passed=quality_check_passed,
                    notes=notes,
                    created_at=datetime.now(),
                    modified_at=datetime.now()
                )
                session.add(produced_item)

                # Check if all items are completed
                completed_count = (
                    session.query(func.count(ProducedItem.id))
                    .filter(ProducedItem.production_order_id == order_id)
                    .scalar()
                )

                if completed_count + 1 >= order.quantity:
                    order.status = ProductionStatus.COMPLETED
                    order.completion_date = datetime.now()
                    order.modified_at = datetime.now()

                return produced_item

        except SQLAlchemyError as e:
            logger.error(f"Failed to complete item: {str(e)}")
            raise DatabaseError(f"Failed to complete item: {str(e)}")

    def get_production_status(self, order_id: int) -> Dict[str, Any]:
        """Get detailed production status including material usage.

        Args:
            order_id: Production order ID

        Returns:
            Dictionary containing status details and metrics
        """
        try:
            with self.session_scope() as session:
                order = (
                    session.query(ProductionOrder)
                    .options(
                        joinedload(ProductionOrder.produced_items),
                        joinedload(ProductionOrder.inventory_transactions),
                        joinedload(ProductionOrder.leather_transactions)
                    )
                    .filter(ProductionOrder.id == order_id)
                    .first()
                )

                if not order:
                    raise DatabaseError(f"Production order {order_id} not found")

                completed_items = len(order.produced_items)
                quality_passed = sum(
                    1 for item in order.produced_items
                    if item.quality_check_passed
                )

                # Calculate material usage
                material_usage = {
                    "parts_reserved": sum(
                        abs(t.quantity)
                        for t in order.inventory_transactions
                        if t.transaction_type == TransactionType.RESERVE
                    ),
                    "leather_reserved": sum(
                        abs(t.area_change)
                        for t in order.leather_transactions
                        if t.transaction_type == TransactionType.RESERVE
                    )
                }

                return {
                    "order_status": order.status.value,
                    "total_quantity": order.quantity,
                    "completed_quantity": completed_items,
                    "quality_passed": quality_passed,
                    "quality_rate": (
                        (quality_passed / completed_items * 100)
                        if completed_items > 0 else 0
                    ),
                    "start_date": order.start_date,
                    "completion_date": order.completion_date,
                    "material_usage": material_usage,
                    "completion_rate": (
                            completed_items / order.quantity * 100
                    )
                }

        except SQLAlchemyError as e:
            logger.error(f"Failed to get production status: {str(e)}")
            raise DatabaseError(f"Failed to get production status: {str(e)}")

    def get_active_orders(self) -> List[ProductionOrder]:
        """Get all active production orders with their patterns.

        Returns:
            List of ProductionOrder instances with loaded relationships
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
            logger.error(f"Failed to get active orders: {str(e)}")
            raise DatabaseError(f"Failed to get active orders: {str(e)}")

    def get_production_metrics(
            self,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get production metrics for a date range.

        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            Dictionary containing production metrics
        """
        try:
            with self.session_scope() as session:
                query = session.query(ProductionOrder)

                if start_date:
                    query = query.filter(ProductionOrder.start_date >= start_date)
                if end_date:
                    query = query.filter(ProductionOrder.start_date <= end_date)

                orders = query.all()

                total_orders = len(orders)
                completed_orders = sum(
                    1 for o in orders
                    if o.status == ProductionStatus.COMPLETED
                )
                total_items = sum(o.quantity for o in orders)

                return {
                    "total_orders": total_orders,
                    "completed_orders": completed_orders,
                    "completion_rate": (
                        (completed_orders / total_orders * 100)
                        if total_orders > 0 else 0
                    ),
                    "total_items_planned": total_items,
                    "average_order_size": (
                        total_items / total_orders if total_orders > 0 else 0
                    )
                }

        except SQLAlchemyError as e:
            logger.error(f"Failed to get production metrics: {str(e)}")
            raise DatabaseError(f"Failed to get production metrics: {str(e)}")