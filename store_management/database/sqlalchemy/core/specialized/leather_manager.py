from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
Specialized manager for Leather-related database operations.
"""


class LeatherManager(BaseManager):
    """
    Specialized manager for handling Leather-related database operations.

    Provides methods for managing leather inventory, transactions,
    and stock-related queries.
    """

        @inject(MaterialService)
        def get_leather_with_transactions(self, leather_id: int) ->Optional[Leather
        ]:
        """
        Retrieve a leather item with its associated transactions.

        Args:
            leather_id (int): The unique identifier of the leather item.

        Returns:
            Optional[Leather]: The leather item with its transactions, or None if not found.
        """
        try:
            with self.session_scope() as session:
                leather = session.query(Leather).filter(Leather.id ==
                    leather_id).first()
                if leather:
                    leather.transactions
                return leather
        except Exception as e:
            self._logger.error(
                f'Error retrieving leather with transactions: {e}')
            return None

        @inject(MaterialService)
        def update_leather_area(self, leather_id: int, area_change: float,
        transaction_type: TransactionType, notes: Optional[str]=None,
        wastage: Optional[float]=None) ->bool:
        """
        Update leather area and create a corresponding transaction.

        Args:
            leather_id (int): The unique identifier of the leather.
            area_change (float): The amount to change in area (can be positive or negative).
            transaction_type (TransactionType): The type of stock transaction.
            notes (Optional[str], optional): Additional notes about the transaction. Defaults to None.
            wastage (Optional[float], optional): Wastage amount during the transaction. Defaults to None.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            with self.session_scope() as session:
                leather = session.query(Leather).filter(Leather.id ==
                    leather_id).first()
                if not leather:
                    self._logger.warning(
                        f'Leather with ID {leather_id} not found.')
                    return False
                leather.current_area += area_change
                transaction = LeatherTransaction(leather_id=leather_id,
                    area_change=area_change, transaction_type=
                    transaction_type, notes=notes, wastage=wastage)
                session.add(transaction)
                return True
        except Exception as e:
            self._logger.error(f'Error updating leather area: {e}')
            return False

        @inject(MaterialService)
        def get_low_stock_leather(self, include_out_of_stock: bool=False,
        supplier_id: Optional[int]=None) ->List[Leather]:
        """
        Retrieve leather items with low stock.

        Args:
            include_out_of_stock (bool, optional): Whether to include leather with zero area.
                                                   Defaults to False.
            supplier_id (Optional[int], optional): Filter by specific supplier. Defaults to None.

        Returns:
            List[Leather]: List of leather items with low stock.
        """
        try:
            with self.session_scope() as session:
                query = session.query(Leather)
                if include_out_of_stock:
                    query = query.filter(Leather.current_area <= Leather.
                        min_area)
                else:
                    query = query.filter((Leather.current_area <= Leather.
                        min_area) & (Leather.current_area > 0))
                if supplier_id is not None:
                    query = query.filter(Leather.supplier_id == supplier_id)
                return query.all()
        except Exception as e:
            self._logger.error(f'Error retrieving low stock leather: {e}')
            return []

        @inject(MaterialService)
        def get_by_supplier(self, supplier_id: int) ->List[Leather]:
        """
        Retrieve leather items associated with a specific supplier.

        Args:
            supplier_id (int): The unique identifier of the supplier.

        Returns:
            List[Leather]: List of leather items from the specified supplier.
        """
        try:
            with self.session_scope() as session:
                return session.query(Leather).filter(Leather.supplier_id ==
                    supplier_id).all()
        except Exception as e:
            self._logger.error(f'Error retrieving leather by supplier: {e}')
            return []
