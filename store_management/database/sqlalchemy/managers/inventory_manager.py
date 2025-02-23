from typing import List, Optional, Dict, Any, Union, Tuple
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.sqlalchemy.base_manager import BaseManager
from database.sqlalchemy.models_file import (
    Part, Leather, InventoryTransaction, LeatherTransaction,
    InventoryStatus, TransactionType
)
from utils.error_handler import DatabaseError
from utils.logger import logger


class InventoryManager:
    """
    Comprehensive inventory manager handling both Part and Leather inventory.
    Uses separate BaseManager instances for each model type.
    """

    def __init__(self, session_factory):
        """Initialize inventory managers with session factory."""
        self.session_factory = session_factory
        self.part_manager = BaseManager[Part](session_factory, Part)
        self.leather_manager = BaseManager[Leather](session_factory, Leather)

    def add_part(self, data: Dict[str, Any]) -> Part:
        """
        Add a new part to inventory.

        Args:
            data: Part data including initial stock levels

        Returns:
            Created Part instance
        """
        required_fields = ['name', 'current_stock', 'min_stock_level']
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            raise DatabaseError(f"Missing required fields: {', '.join(missing_fields)}")

        with self.session_factory() as session:
            try:
                # Create part
                part = Part(**data)
                session.add(part)
                session.flush()

                # Create initial transaction
                if part.current_stock > 0:
                    transaction = InventoryTransaction(
                        part_id=part.id,
                        transaction_type=TransactionType.INITIAL,
                        quantity=part.current_stock,
                        notes="Initial stock"
                    )
                    session.add(transaction)

                session.commit()
                return part
            except SQLAlchemyError as e:
                session.rollback()
                raise DatabaseError(f"Failed to add part: {str(e)}")

    def add_leather(self, data: Dict[str, Any]) -> Leather:
        """
        Add a new leather to inventory.

        Args:
            data: Leather data including initial area

        Returns:
            Created Leather instance
        """
        required_fields = ['type', 'color', 'thickness', 'available_area_sqft']
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            raise DatabaseError(f"Missing required fields: {', '.join(missing_fields)}")

        with self.session_factory() as session:
            try:
                # Create leather
                leather = Leather(**data)
                session.add(leather)
                session.flush()

                # Create initial transaction
                if leather.available_area_sqft > 0:
                    transaction = LeatherTransaction(
                        leather_id=leather.id,
                        transaction_type=TransactionType.INITIAL,
                        area_sqft=leather.available_area_sqft,
                        notes="Initial stock"
                    )
                    session.add(transaction)

                session.commit()
                return leather
            except SQLAlchemyError as e:
                session.rollback()
                raise DatabaseError(f"Failed to add leather: {str(e)}")

    def update_part_stock(self, part_id: int, quantity_change: int,
                          transaction_type: TransactionType,
                          notes: Optional[str] = None) -> Part:
        """
        Update part stock levels with transaction tracking.

        Args:
            part_id: Part ID
            quantity_change: Change in quantity (positive or negative)
            transaction_type: Type of transaction
            notes: Optional transaction notes

        Returns:
            Updated Part instance
        """
        with self.session_factory() as session:
            try:
                part = session.get(Part, part_id)
                if not part:
                    raise DatabaseError(f"Part {part_id} not found")

                new_stock = part.current_stock + quantity_change
                if new_stock < 0:
                    raise DatabaseError("Stock cannot be negative")

                # Update part stock
                part.current_stock = new_stock
                part.modified_at = datetime.utcnow()

                # Create transaction record
                transaction = InventoryTransaction(
                    part_id=part_id,
                    transaction_type=transaction_type,
                    quantity=abs(quantity_change),
                    notes=notes
                )
                session.add(transaction)

                # Update status
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
                raise DatabaseError(f"Failed to update part stock: {str(e)}")

    def update_leather_stock(self, leather_id: int, area_change: float,
                             transaction_type: TransactionType,
                             notes: Optional[str] = None) -> Leather:
        """
        Update leather stock levels with transaction tracking.

        Args:
            leather_id: Leather ID
            area_change: Change in area (positive or negative)
            transaction_type: Type of transaction
            notes: Optional transaction notes

        Returns:
            Updated Leather instance
        """
        with self.session_factory() as session:
            try:
                leather = session.get(Leather, leather_id)
                if not leather:
                    raise DatabaseError(f"Leather {leather_id} not found")

                new_area = leather.available_area_sqft + area_change
                if new_area < 0:
                    raise DatabaseError("Area cannot be negative")

                # Update leather stock
                leather.available_area_sqft = new_area
                leather.modified_at = datetime.utcnow()

                # Create transaction record
                transaction = LeatherTransaction(
                    leather_id=leather_id,
                    transaction_type=transaction_type,
                    area_sqft=abs(area_change),
                    notes=notes
                )
                session.add(transaction)

                # Update status
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
                raise DatabaseError(f"Failed to update leather stock: {str(e)}")

    def get_part_with_transactions(self, part_id: int) -> Optional[Part]:
        """
        Get part with its transaction history.

        Args:
            part_id: Part ID

        Returns:
            Part instance with transactions loaded or None if not found
        """
        with self.session_factory() as session:
            query = select(Part).options(
                joinedload(Part.transactions)
            ).filter(Part.id == part_id)
            return session.execute(query).scalar()

    def get_leather_with_transactions(self, leather_id: int) -> Optional[Leather]:
        """
        Get leather with its transaction history.

        Args:
            leather_id: Leather ID

        Returns:
            Leather instance with transactions loaded or None if not found
        """
        with self.session_factory() as session:
            query = select(Leather).options(
                joinedload(Leather.transactions)
            ).filter(Leather.id == leather_id)
            return session.execute(query).scalar()

    def get_low_stock_parts(self, include_out_of_stock: bool = True) -> List[Part]:
        """
        Get all parts with low stock levels.

        Args:
            include_out_of_stock: Whether to include out of stock items

        Returns:
            List of Part instances with low stock
        """
        with self.session_factory() as session:
            query = select(Part).filter(
                Part.current_stock <= Part.min_stock_level
            )
            if not include_out_of_stock:
                query = query.filter(Part.current_stock > 0)
            return list(session.execute(query).scalars())

    def get_low_stock_leather(self, include_out_of_stock: bool = True) -> List[Leather]:
        """
        Get all leather with low stock levels.

        Args:
            include_out_of_stock: Whether to include out of stock items

        Returns:
            List of Leather instances with low stock
        """
        with self.session_factory() as session:
            query = select(Leather).filter(
                Leather.available_area_sqft <= Leather.min_area_sqft
            )
            if not include_out_of_stock:
                query = query.filter(Leather.available_area_sqft > 0)
            return list(session.execute(query).scalars())

    def get_inventory_transactions(self, part_id: Optional[int] = None,
                                   leather_id: Optional[int] = None,
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> List[
        Union[InventoryTransaction, LeatherTransaction]]:
        """
        Get inventory transactions with optional filtering.

        Args:
            part_id: Optional Part ID to filter by
            leather_id: Optional Leather ID to filter by
            start_date: Optional start date for date range
            end_date: Optional end date for date range

        Returns:
            List of transaction instances
        """
        with self.session_factory() as session:
            transactions = []

            if part_id:
                query = select(InventoryTransaction).filter(
                    InventoryTransaction.part_id == part_id
                )
                if start_date:
                    query = query.filter(InventoryTransaction.timestamp >= start_date)
                if end_date:
                    query = query.filter(InventoryTransaction.timestamp <= end_date)
                transactions.extend(session.execute(query).scalars())

            if leather_id:
                query = select(LeatherTransaction).filter(
                    LeatherTransaction.leather_id == leather_id
                )
                if start_date:
                    query = query.filter(LeatherTransaction.timestamp >= start_date)
                if end_date:
                    query = query.filter(LeatherTransaction.timestamp <= end_date)
                transactions.extend(session.execute(query).scalars())

            return sorted(transactions, key=lambda x: x.timestamp, reverse=True)

    def get_inventory_value(self) -> Dict[str, float]:
        """
        Calculate total value of inventory.

        Returns:
            Dictionary with total values for parts and leather
        """
        with self.session_factory() as session:
            # Calculate parts value
            parts_value = session.query(
                func.sum(Part.current_stock * Part.price)
            ).scalar() or 0.0

            # Calculate leather value
            leather_value = session.query(
                func.sum(Leather.available_area_sqft * Leather.price_per_sqft)
            ).scalar() or 0.0

            return {
                'parts_value': parts_value,
                'leather_value': leather_value,
                'total_value': parts_value + leather_value
            }

    def search_inventory(self, search_term: str) -> Dict[str, List]:
        """
        Search both parts and leather inventory.

        Args:
            search_term: Term to search for

        Returns:
            Dictionary with matching parts and leather items
        """
        with self.session_factory() as session:
            # Search parts
            parts_query = select(Part).filter(
                or_(
                    Part.name.ilike(f"%{search_term}%"),
                    Part.color.ilike(f"%{search_term}%"),
                    Part.notes.ilike(f"%{search_term}%")
                )
            )
            parts = list(session.execute(parts_query).scalars())

            # Search leather
            leather_query = select(Leather).filter(
                or_(
                    Leather.type.ilike(f"%{search_term}%"),
                    Leather.color.ilike(f"%{search_term}%"),
                    Leather.notes.ilike(f"%{search_term}%")
                )
            )
            leather = list(session.execute(leather_query).scalars())

            return {
                'parts': parts,
                'leather': leather
            }

    def adjust_min_stock_levels(self, part_id: int, new_min_level: int) -> Part:
        """
        Adjust minimum stock level for a part.

        Args:
            part_id: Part ID
            new_min_level: New minimum stock level

        Returns:
            Updated Part instance
        """
        with self.session_factory() as session:
            part = session.get(Part, part_id)
            if not part:
                raise DatabaseError(f"Part {part_id} not found")

            part.min_stock_level = new_min_level
            # Update status based on new minimum
            if part.current_stock <= new_min_level:
                part.status = InventoryStatus.LOW_STOCK
            elif part.current_stock > new_min_level:
                part.status = InventoryStatus.IN_STOCK

            session.commit()
            return part

    def adjust_min_leather_area(self, leather_id: int, new_min_area: float) -> Leather:
        """
        Adjust minimum area for a leather type.

        Args:
            leather_id: Leather ID
            new_min_area: New minimum area in square feet

        Returns:
            Updated Leather instance
        """
        with self.session_factory() as session:
            leather = session.get(Leather, leather_id)
            if not leather:
                raise DatabaseError(f"Leather {leather_id} not found")

            leather.min_area_sqft = new_min_area
            # Update status based on new minimum
            if leather.available_area_sqft <= new_min_area:
                leather.status = InventoryStatus.LOW_STOCK
            elif leather.available_area_sqft > new_min_area:
                leather.status = InventoryStatus.IN_STOCK

            session.commit()
            return leather

    def get_inventory_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive inventory summary including counts and values.

        Returns:
            Dictionary containing inventory summary statistics
        """
        with self.session_factory() as session:
            # Get parts summary
            parts_summary = {
                'total_count': session.query(func.count(Part.id)).scalar(),
                'low_stock_count': session.query(func.count(Part.id)).filter(
                    Part.status == InventoryStatus.LOW_STOCK
                ).scalar(),
                'out_of_stock_count': session.query(func.count(Part.id)).filter(
                    Part.status == InventoryStatus.OUT_OF_STOCK
                ).scalar(),
                'total_value': session.query(
                    func.sum(Part.current_stock * Part.price)
                ).scalar() or 0.0
            }

            # Get leather summary
            leather_summary = {
                'total_count': session.query(func.count(Leather.id)).scalar(),
                'low_stock_count': session.query(func.count(Leather.id)).filter(
                    Leather.status == InventoryStatus.LOW_STOCK
                ).scalar(),
                'out_of_stock_count': session.query(func.count(Leather.id)).filter(
                    Leather.status == InventoryStatus.OUT_OF_STOCK
                ).scalar(),
                'total_area': session.query(
                    func.sum(Leather.available_area_sqft)
                ).scalar() or 0.0,
                'total_value': session.query(
                    func.sum(Leather.available_area_sqft * Leather.price_per_sqft)
                ).scalar() or 0.0
            }

            # Get transaction counts
            transaction_summary = {
                'part_transactions': session.query(
                    func.count(InventoryTransaction.id)
                ).scalar(),
                'leather_transactions': session.query(
                    func.count(LeatherTransaction.id)
                ).scalar()
            }

            return {
                'parts': parts_summary,
                'leather': leather_summary,
                'transactions': transaction_summary,
                'total_value': parts_summary['total_value'] + leather_summary['total_value']
            }

    def bulk_update_parts(self, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple parts in a single transaction.

        Args:
            updates: List of dictionaries containing part updates

        Returns:
            Number of parts updated
        """
        with self.session_factory() as session:
            try:
                count = 0
                for update_data in updates:
                    part_id = update_data.pop('id', None)
                    if not part_id:
                        continue

                    part = session.get(Part, part_id)
                    if part:
                        for key, value in update_data.items():
                            setattr(part, key, value)
                        count += 1

                session.commit()
                return count
            except SQLAlchemyError as e:
                session.rollback()
                raise DatabaseError(f"Failed to bulk update parts: {str(e)}")

    def bulk_update_leather(self, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple leather items in a single transaction.

        Args:
            updates: List of dictionaries containing leather updates

        Returns:
            Number of leather items updated
        """
        with self.session_factory() as session:
            try:
                count = 0
                for update_data in updates:
                    leather_id = update_data.pop('id', None)
                    if not leather_id:
                        continue

                    leather = session.get(Leather, leather_id)
                    if leather:
                        for key, value in update_data.items():
                            setattr(leather, key, value)
                        count += 1

                session.commit()
                return count
            except SQLAlchemyError as e:
                session.rollback()
                raise DatabaseError(f"Failed to bulk update leather: {str(e)}")

    def get_transaction_history(self, start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None,
                                transaction_type: Optional[TransactionType] = None) -> Dict[str, List]:
        """
        Get transaction history with optional filtering.

        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            transaction_type: Optional transaction type filter

        Returns:
            Dictionary containing part and leather transactions
        """
        with self.session_factory() as session:
            # Build part transactions query
            part_query = select(InventoryTransaction).options(
                joinedload(InventoryTransaction.part)
            )
            if start_date:
                part_query = part_query.filter(InventoryTransaction.timestamp >= start_date)
            if end_date:
                part_query = part_query.filter(InventoryTransaction.timestamp <= end_date)
            if transaction_type:
                part_query = part_query.filter(InventoryTransaction.transaction_type == transaction_type)

            # Build leather transactions query
            leather_query = select(LeatherTransaction).options(
                joinedload(LeatherTransaction.leather)
            )
            if start_date:
                leather_query = leather_query.filter(LeatherTransaction.timestamp >= start_date)
            if end_date:
                leather_query = leather_query.filter(LeatherTransaction.timestamp <= end_date)
            if transaction_type:
                leather_query = leather_query.filter(LeatherTransaction.transaction_type == transaction_type)

            return {
                'part_transactions': list(session.execute(part_query).scalars()),
                'leather_transactions': list(session.execute(leather_query).scalars())
            }

    def get_part_stock_history(self, part_id: int,
                               days: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get stock level history for a part.

        Args:
            part_id: Part ID
            days: Optional number of days to look back

        Returns:
            List of stock level changes with timestamps
        """
        with self.session_factory() as session:
            query = select(InventoryTransaction).filter(
                InventoryTransaction.part_id == part_id
            ).order_by(InventoryTransaction.timestamp)

            if days:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(InventoryTransaction.timestamp >= cutoff_date)

            transactions = session.execute(query).scalars()

            stock_history = []
            running_stock = 0
            for transaction in transactions:
                if transaction.transaction_type in [TransactionType.INITIAL, TransactionType.INCREASE]:
                    running_stock += transaction.quantity
                else:
                    running_stock -= transaction.quantity

                stock_history.append({
                    'timestamp': transaction.timestamp,
                    'stock_level': running_stock,
                    'change': transaction.quantity,
                    'transaction_type': transaction.transaction_type,
                    'notes': transaction.notes
                })

            return stock_history

    def get_leather_stock_history(self, leather_id: int,
                                  days: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get stock level history for a leather item.

        Args:
            leather_id: Leather ID
            days: Optional number of days to look back

        Returns:
            List of stock level changes with timestamps
        """
        with self.session_factory() as session:
            query = select(LeatherTransaction).filter(
                LeatherTransaction.leather_id == leather_id
            ).order_by(LeatherTransaction.timestamp)

            if days:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(LeatherTransaction.timestamp >= cutoff_date)

            transactions = session.execute(query).scalars()

            stock_history = []
            running_area = 0
            for transaction in transactions:
                if transaction.transaction_type in [TransactionType.INITIAL, TransactionType.INCREASE]:
                    running_area += transaction.area_sqft
                else:
                    running_area -= transaction.area_sqft

                stock_history.append({
                    'timestamp': transaction.timestamp,
                    'available_area': running_area,
                    'change': transaction.area_sqft,
                    'transaction_type': transaction.transaction_type,
                    'notes': transaction.notes
                })

            return stock_history

    def get_reorder_suggestions(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get suggestions for items that need reordering.

        Returns:
            Dictionary containing parts and leather that need reordering
        """
        with self.session_factory() as session:
            # Get parts that need reordering
            parts_query = select(Part).filter(
                Part.current_stock <= Part.min_stock_level
            ).order_by((Part.current_stock / Part.min_stock_level).asc())

            parts = []
            for part in session.execute(parts_query).scalars():
                parts.append({
                    'id': part.id,
                    'name': part.name,
                    'current_stock': part.current_stock,
                    'min_stock_level': part.min_stock_level,
                    'suggested_order': max(part.min_stock_level - part.current_stock, 0)
                })

            # Get leather that needs reordering
            leather_query = select(Leather).filter(
                Leather.available_area_sqft <= Leather.min_area_sqft
            ).order_by((Leather.available_area_sqft / Leather.min_area_sqft).asc())

            leather = []
            for item in session.execute(leather_query).scalars():
                leather.append({
                    'id': item.id,
                    'type': item.type,
                    'color': item.color,
                    'available_area': item.available_area_sqft,
                    'min_area': item.min_area_sqft,
                    'suggested_order': max(item.min_area_sqft - item.available_area_sqft, 0)
                })

            return {
                'parts': parts,
                'leather': leather
            }