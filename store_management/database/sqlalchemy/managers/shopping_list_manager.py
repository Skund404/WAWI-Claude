# Path: database/sqlalchemy/managers/shopping_list_manager.py

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from sqlalchemy import select, or_, and_, case, func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from di.core import inject
from services.interfaces import MaterialService
from models import ShoppingList, ShoppingListItem, Supplier, Part, Leather, Order
from core.exceptions import DatabaseError


class ShoppingListManager:
    """
    Manager for handling shopping list operations and related functionality.

    Provides comprehensive methods for creating, updating, and managing 
    shopping lists and their items across the inventory system.
    """

    def __init__(self, session_factory):
        """
        Initialize ShoppingListManager with session factory.

        Args:
            session_factory (Callable): Factory function to create database sessions
        """
        self.session_factory = session_factory
        self.logger = logging.getLogger(self.__class__.__name__)

    def session_scope(self):
        """
        Provide a transactional scope around a series of operations.

        Yields:
            Session: Database session
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_shopping_list(self, data: Dict[str, Any], items: List[Dict[str, Any]] = None) -> ShoppingList:
        """
        Create a new shopping list with optional items.

        Args:
            data (Dict[str, Any]): Shopping list data (name, description, etc.)
            items (List[Dict[str, Any]], optional): Optional list of shopping list items

        Returns:
            ShoppingList: Created shopping list instance

        Raises:
            DatabaseError: If validation fails or database operation fails
        """
        try:
            with self.session_scope() as session:
                # Validate required fields
                if not data.get('name'):
                    raise ValueError("Shopping list name is required")

                # Create shopping list
                shopping_list = ShoppingList(
                    name=data['name'],
                    description=data.get('description', ''),
                    priority=data.get('priority', 'normal'),
                    due_date=data.get('due_date'),
                    status='active',
                    created_at=datetime.now(),
                    modified_at=datetime.now()
                )
                session.add(shopping_list)
                session.flush()  # Ensure ID is generated

                # Add items if provided
                if items:
                    for item_data in items:
                        item = ShoppingListItem(
                            shopping_list_id=shopping_list.id,
                            supplier_id=item_data.get('supplier_id'),
                            part_id=item_data.get('part_id'),
                            leather_id=item_data.get('leather_id'),
                            quantity=item_data['quantity'],
                            notes=item_data.get('notes', ''),
                            purchased=False,
                            created_at=datetime.now(),
                            modified_at=datetime.now()
                        )
                        session.add(item)

                return shopping_list

        except (SQLAlchemyError, ValueError) as e:
            self.logger.error(f'Failed to create shopping list: {str(e)}')
            raise DatabaseError(f'Failed to create shopping list: {str(e)}')

    def get_shopping_list_with_items(self, list_id: int) -> Optional[ShoppingList]:
        """
        Retrieve a shopping list with all its items, including related data.

        Args:
            list_id (int): Shopping list ID

        Returns:
            Optional[ShoppingList]: Shopping list with loaded items and relationships
        """
        try:
            with self.session_scope() as session:
                query = (
                    select(ShoppingList)
                    .options(
                        joinedload(ShoppingList.items)
                        .joinedload(ShoppingListItem.supplier),
                        joinedload(ShoppingList.items)
                        .joinedload(ShoppingListItem.part),
                        joinedload(ShoppingList.items)
                        .joinedload(ShoppingListItem.leather)
                    )
                    .where(ShoppingList.id == list_id)
                )
                result = session.execute(query).scalar_one_or_none()
                return result

        except SQLAlchemyError as e:
            self.logger.error(f'Failed to get shopping list: {str(e)}')
            raise DatabaseError(f'Failed to get shopping list: {str(e)}')

    def add_shopping_list_item(self, list_id: int, item_data: Dict[str, Any]) -> ShoppingListItem:
        """
        Add an item to an existing shopping list.

        Args:
            list_id (int): Shopping list ID
            item_data (Dict[str, Any]): Item data to add

        Returns:
            ShoppingListItem: Created shopping list item

        Raises:
            DatabaseError: If shopping list not found or item creation fails
        """
        try:
            with self.session_scope() as session:
                # Validate shopping list exists
                shopping_list = session.get(ShoppingList, list_id)
                if not shopping_list:
                    raise DatabaseError(f'Shopping list {list_id} not found')

                # Validate required fields
                if 'quantity' not in item_data:
                    raise ValueError("Quantity is required for shopping list item")

                # Create and add item
                item = ShoppingListItem(
                    shopping_list_id=list_id,
                    supplier_id=item_data.get('supplier_id'),
                    part_id=item_data.get('part_id'),
                    leather_id=item_data.get('leather_id'),
                    quantity=item_data['quantity'],
                    notes=item_data.get('notes', ''),
                    purchased=False,
                    created_at=datetime.now(),
                    modified_at=datetime.now()
                )
                session.add(item)
                return item

        except (SQLAlchemyError, ValueError) as e:
            self.logger.error(f'Failed to add shopping list item: {str(e)}')
            raise DatabaseError(f'Failed to add shopping list item: {str(e)}')

    def update_shopping_list_status(self, list_id: int, status: str) -> Optional[ShoppingList]:
        """
        Update the status of a shopping list.

        Args:
            list_id (int): Shopping list ID
            status (str): New status to set

        Returns:
            Optional[ShoppingList]: Updated shopping list or None if not found
        """
        try:
            with self.session_scope() as session:
                shopping_list = session.get(ShoppingList, list_id)
                if shopping_list:
                    shopping_list.status = status
                    shopping_list.modified_at = datetime.now()
                    return shopping_list
                return None

        except SQLAlchemyError as e:
            self.logger.error(f'Failed to update shopping list status: {str(e)}')
            raise DatabaseError(f'Failed to update shopping list status: {str(e)}')

    def mark_item_purchased(self, list_id: int, item_id: int, purchase_data: Dict[str, Any]) -> Optional[
        ShoppingListItem]:
        """
        Mark a specific shopping list item as purchased.

        Args:
            list_id (int): Shopping list ID
            item_id (int): Shopping list item ID
            purchase_data (Dict[str, Any]): Purchase details

        Returns:
            Optional[ShoppingListItem]: Updated shopping list item
        """
        try:
            with self.session_scope() as session:
                item = (
                    session.query(ShoppingListItem)
                    .filter(
                        ShoppingListItem.id == item_id,
                        ShoppingListItem.shopping_list_id == list_id
                    )
                    .first()
                )

                if item:
                    item.purchased = True
                    item.purchase_date = purchase_data.get('purchase_date', datetime.now())
                    item.purchase_price = purchase_data.get('purchase_price')
                    item.modified_at = datetime.now()
                    return item
                return None

        except SQLAlchemyError as e:
            self.logger.error(f'Failed to mark item as purchased: {str(e)}')
            raise DatabaseError(f'Failed to mark item as purchased: {str(e)}')

    def get_pending_items(self) -> List[ShoppingListItem]:
        """
        Retrieve all pending (unpurchased) items across all shopping lists.

        Returns:
            List[ShoppingListItem]: List of unpurchased items
        """
        try:
            with self.session_scope() as session:
                query = (
                    select(ShoppingListItem)
                    .options(
                        joinedload(ShoppingListItem.shopping_list),
                        joinedload(ShoppingListItem.supplier)
                    )
                    .where(ShoppingListItem.purchased == False)
                    .order_by(ShoppingListItem.created_at)
                )
                result = session.execute(query).scalars().all()
                return list(result)

        except SQLAlchemyError as e:
            self.logger.error(f'Failed to get pending items: {str(e)}')
            raise DatabaseError(f'Failed to get pending items: {str(e)}')

    def get_items_by_supplier(self, supplier_id: int) -> List[ShoppingListItem]:
        """
        Retrieve all shopping list items for a specific supplier.

        Args:
            supplier_id (int): Supplier ID

        Returns:
            List[ShoppingListItem]: List of items from the specified supplier
        """
        try:
            with self.session_scope() as session:
                query = (
                    select(ShoppingListItem)
                    .options(joinedload(ShoppingListItem.shopping_list))
                    .where(ShoppingListItem.supplier_id == supplier_id)
                    .order_by(ShoppingListItem.created_at)
                )
                result = session.execute(query).scalars().all()
                return list(result)

        except SQLAlchemyError as e:
            self.logger.error(f'Failed to get supplier items: {str(e)}')
            raise DatabaseError(f'Failed to get supplier items: {str(e)}')

    def get_shopping_list_summary(self, list_id: int) -> Dict[str, Any]:
        """
        Generate summary statistics for a specific shopping list.

        Args:
            list_id (int): Shopping list ID

        Returns:
            Dict[str, Any]: Summary statistics for the shopping list
        """
        try:
            with self.session_scope() as session:
                # Aggregate query to get summary statistics
                stats = (
                    session.query(
                        func.count(ShoppingListItem.id).label('total_items'),
                        func.sum(case((ShoppingListItem.purchased == True, 1), else_=0)).label('purchased_items'),
                        func.sum(ShoppingListItem.purchase_price).label('total_spent')
                    )
                    .filter(ShoppingListItem.shopping_list_id == list_id)
                    .first()
                )

                # Calculate summary metrics
                total_items = stats.total_items or 0
                purchased_items = stats.purchased_items or 0
                total_spent = float(stats.total_spent or 0)

                return {
                    'total_items': total_items,
                    'purchased_items': purchased_items,
                    'pending_items': total_items - purchased_items,
                    'total_spent': total_spent,
                    'completion_percentage': (purchased_items / total_items * 100) if total_items > 0 else 0
                }

        except SQLAlchemyError as e:
            self.logger.error(f'Failed to get shopping list summary: {str(e)}')
            raise DatabaseError(f'Failed to get shopping list summary: {str(e)}')

    def search_shopping_lists(self, search_term: str) -> List[ShoppingList]:
        """
        Search shopping lists by name or description.

        Args:
            search_term (str): Term to search for

        Returns:
            List[ShoppingList]: Matching shopping lists
        """
        try:
            with self.session_scope() as session:
                query = (
                    select(ShoppingList)
                    .where(
                        or_(
                            ShoppingList.name.ilike(f'%{search_term}%'),
                            ShoppingList.description.ilike(f'%{search_term}%')
                        )
                    )
                    .order_by(ShoppingList.created_at.desc())
                )
                result = session.execute(query).scalars().all()
                return list(result)

        except SQLAlchemyError as e:
            self.logger.error(f'Failed to search shopping lists: {str(e)}')
            raise DatabaseError(f'Failed to search shopping lists: {str(e)}')

    def filter_shopping_lists(
            self,
            status: Optional[str] = None,
            priority: Optional[str] = None,
            date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[ShoppingList]:
        """
        Filter shopping lists based on various criteria.

        Args:
            status (Optional[str]): Filter by list status
            priority (Optional[str]): Filter by list priority
            date_range (Optional[Tuple[datetime, datetime]]): Filter by date range

        Returns:
            List[ShoppingList]: Filtered shopping lists
        """
        try:
            with self.session_scope() as session:
                # Build dynamic filters
                filters = []

                if status:
                    filters.append(ShoppingList.status == status)

                if priority:
                    filters.append(ShoppingList.priority == priority)

                if date_range:
                    start_date, end_date = date_range
                    filters.append(ShoppingList.created_at.between(start_date, end_date))

                # Construct and execute query
                query = (
                    select(ShoppingList)
                    .where(and_(*filters) if filters else True)
                    .order_by(ShoppingList.created_at.desc())
                )

                result = session.execute(query).scalars().all()
                return list(result)

        except SQLAlchemyError as e:
            self.logger.error(f'Failed to filter shopping lists: {str(e)}')
            raise DatabaseError(f'Failed to filter shopping lists: {str(e)}')

        def bulk_update_items(self, updates: List[Dict[str, Any]], list_id: Optional[int] = None) -> int:
            """
            Perform bulk updates on shopping list items.

            Args:
                updates (List[Dict[str, Any]]): List of item updates
                list_id (Optional[int]): Optional shopping list ID to restrict updates

            Returns:
                int: Number of items updated
            """
            try:
                with self.session_scope() as session:
                    updated_count = 0

                    for update_data in updates:
                        # Extract item ID from update data
                        item_id = update_data.pop('id')

                        # Build query to find item
                        query = session.query(ShoppingListItem).filter(ShoppingListItem.id == item_id)

                        # Optional list_id filtering
                        if list_id:
                            query = query.filter(ShoppingListItem.shopping_list_id == list_id)

                        # Find and update item
                        item = query.first()
                        if item:
                            # Update item attributes
                            for key, value in update_data.items():
                                setattr(item, key, value)

                            # Update modification timestamp
                            item.modified_at = datetime.now()
                            updated_count += 1

                    return updated_count

            except SQLAlchemyError as e:
                self.logger.error(f'Failed to bulk update items: {str(e)}')
                raise DatabaseError(f'Failed to bulk update items: {str(e)}')

        def merge_shopping_lists(self, source_ids: List[int], target_id: int) -> ShoppingList:
            """
            Merge multiple shopping lists into a target list.

            Args:
                source_ids (List[int]): List of source shopping list IDs
                target_id (int): Target shopping list ID

            Returns:
                ShoppingList: Updated target shopping list

            Raises:
                DatabaseError: If any list is not found or merge fails
            """
            try:
                with self.session_scope() as session:
                    # Validate target list exists
                    target_list = session.get(ShoppingList, target_id)
                    if not target_list:
                        raise DatabaseError(f'Target shopping list {target_id} not found')

                    # Process each source list
                    for source_id in source_ids:
                        # Validate source list exists
                        source_list = session.get(ShoppingList, source_id)
                        if not source_list:
                            raise DatabaseError(f'Source shopping list {source_id} not found')

                        # Transfer items to target list
                        for item in source_list.items:
                            item.shopping_list_id = target_id
                            item.modified_at = datetime.now()

                        # Mark source list as merged
                        source_list.status = 'merged'
                        source_list.modified_at = datetime.now()

                    # Update target list
                    target_list.modified_at = datetime.now()
                    target_list.description += f"\nMerged with lists: {', '.join(map(str, source_ids))}"

                    return target_list

            except SQLAlchemyError as e:
                self.logger.error(f'Failed to merge shopping lists: {str(e)}')
                raise DatabaseError(f'Failed to merge shopping lists: {str(e)}')

        def get_overdue_items(self) -> List[ShoppingListItem]:
            """
            Retrieve all overdue items from active shopping lists.

            Returns:
                List[ShoppingListItem]: List of overdue items
            """
            try:
                with self.session_scope() as session:
                    current_date = datetime.now()
                    query = (
                        select(ShoppingListItem)
                        .join(ShoppingList)
                        .options(
                            joinedload(ShoppingListItem.shopping_list),
                            joinedload(ShoppingListItem.supplier)
                        )
                        .where(
                            and_(
                                ShoppingList.status == 'active',
                                ShoppingList.due_date < current_date,
                                ShoppingListItem.purchased == False
                            )
                        )
                        .order_by(ShoppingList.due_date)
                    )
                    result = session.execute(query).scalars().all()
                    return list(result)

            except SQLAlchemyError as e:
                self.logger.error(f'Failed to get overdue items: {str(e)}')
                raise DatabaseError(f'Failed to get overdue items: {str(e)}')

    # Logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='shopping_lists.log'
    )

    # Additional imports for completeness
    import logging
    from datetime import datetime
    from typing import Dict, Any, Optional, List, Tuple, Callable

    from sqlalchemy import select, or_, and_, case, func
    from sqlalchemy.orm import joinedload
    from sqlalchemy.exc import SQLAlchemyError

    # Import custom exceptions and models
    from core.exceptions import DatabaseError
    from models import (
        ShoppingList,
        ShoppingListItem,
        Supplier,
        Part,
        Leather
    )