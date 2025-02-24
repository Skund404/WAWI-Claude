from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
database/sqlalchemy/core/specialized/supplier_manager.py
Specialized manager for Supplier models with additional capabilities.
"""


class SupplierManager(BaseManager[Supplier]):
    """
    Specialized manager for Supplier model operations.

    Extends BaseManager with supplier-specific operations.
    """

        @inject(MaterialService)
        def get_supplier_with_orders(self, supplier_id: int) ->Optional[Supplier]:
        """
        Get supplier with their order history.

        Args:
            supplier_id: Supplier ID

        Returns:
            Supplier with orders loaded or None if not found

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = select(Supplier).options(joinedload(Supplier.orders)
                    ).where(Supplier.id == supplier_id)
                result = session.execute(query)
                return result.scalars().first()
        except Exception as e:
            raise DatabaseError(f'Failed to retrieve supplier with orders',
                str(e))

        @inject(MaterialService)
        def get_supplier_products(self, supplier_id: int) ->Dict[str, List]:
        """
        Get all products supplied by a supplier.

        Args:
            supplier_id: Supplier ID

        Returns:
            Dictionary containing parts and leather supplied

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                parts_query = select(Part).where(Part.supplier_id ==
                    supplier_id)
                parts_result = session.execute(parts_query)
                parts = list(parts_result.scalars().all())
                leather_query = select(Leather).where(Leather.supplier_id ==
                    supplier_id)
                leather_result = session.execute(leather_query)
                leather = list(leather_result.scalars().all())
                return {'parts': parts, 'leather': leather}
        except Exception as e:
            raise DatabaseError(f'Failed to get supplier products', str(e))

        @inject(MaterialService)
        def get_supplier_order_history(self, supplier_id: int, start_date:
        Optional[datetime]=None, end_date: Optional[datetime]=None) ->List[
        Order]:
        """
        Get supplier's order history with optional date range.

        Args:
            supplier_id: Supplier ID
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            List of Order instances

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            with self.session_scope() as session:
                query = select(Order).where(Order.supplier_id == supplier_id)
                if start_date:
                    query = query.where(Order.order_date >= start_date)
                if end_date:
                    query = query.where(Order.order_date <= end_date)
                query = query.order_by(Order.order_date.desc())
                result = session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            raise DatabaseError(f'Failed to get supplier order history', str(e)
                )

        @inject(MaterialService)
        def update_supplier_rating(self, supplier_id: int, rating: float, notes:
        Optional[str]=None) ->Optional[Supplier]:
        """
        Update supplier quality rating.

        Args:
            supplier_id: Supplier ID
            rating: New rating (0-5)
            notes: Optional notes about the rating

        Returns:
            Updated Supplier instance

        Raises:
            DatabaseError: If update fails
        """
        if rating < 0 or rating > 5:
            raise ValueError('Rating must be between 0 and 5')
        data = {'rating': rating}
        if notes:
            data['rating_notes'] = notes
        return self.update(supplier_id, data)

        @inject(MaterialService)
        def search_suppliers(self, term: str) ->List[Supplier]:
        """
        Search suppliers across multiple fields.

        Args:
            term: Term to search for

        Returns:
            List of matching Supplier instances

        Raises:
            DatabaseError: If search fails
        """
        return self.search(term, fields=['name', 'contact_name',
            'contact_email', 'contact_phone'])
