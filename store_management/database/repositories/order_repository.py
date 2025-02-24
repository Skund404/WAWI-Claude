

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class OrderRepository(BaseRepository):
    """
    Repository for managing order-related database operations.

    Provides specialized methods for retrieving, creating, and managing
    orders with advanced querying capabilities.
    """

    @inject(MaterialService)
        def __init__(self, session: Session):
        """
        Initialize the OrderRepository with a database session.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Order)

        @inject(MaterialService)
            def get_with_items(self, order_id: int) -> Optional[Order]:
        """
        Retrieve an order with its associated items in a single query.

        Args:
            order_id (int): Unique identifier of the order

        Returns:
            Order instance with populated order items, or None if not found
        """
        try:
            return self.session.query(Order).options(joinedload(Order.
                                                                order_items)).options(joinedload(Order.supplier)).filter(
                Order.id == order_id).first()
        except Exception as e:
            raise DatabaseError(f'Error retrieving order with items: {str(e)}')

        @inject(MaterialService)
            def get_by_status(self, status: OrderStatus) -> List[Order]:
        """
        Retrieve orders filtered by their current status.

        Args:
            status (OrderStatus): Status to filter orders by

        Returns:
            List of Order instances matching the specified status
        """
        try:
            return self.session.query(Order).options(joinedload(Order.
                                                                order_items)).options(joinedload(Order.supplier)).filter(
                Order.status == status).all()
        except Exception as e:
            raise DatabaseError(f'Error retrieving orders by status: {str(e)}')

        @inject(MaterialService)
            def get_by_supplier(self, supplier_id: int) -> List[Order]:
        """
        Retrieve all orders for a specific supplier.

        Args:
            supplier_id (int): Unique identifier of the supplier

        Returns:
            List of Order instances for the specified supplier
        """
        try:
            return self.session.query(Order).options(joinedload(Order.
                                                                order_items)).options(joinedload(Order.supplier)).filter(
                Order.supplier_id == supplier_id).all()
        except Exception as e:
            raise DatabaseError(
                f'Error retrieving orders for supplier: {str(e)}')

        @inject(MaterialService)
            def get_by_date_range(self, start_date: datetime, end_date: datetime
                              ) -> List[Order]:
        """
        Retrieve orders within a specific date range.

        Args:
            start_date (datetime): Start of the date range
            end_date (datetime): End of the date range

        Returns:
            List of Order instances within the specified date range
        """
        try:
            return self.session.query(Order).options(joinedload(Order.
                                                                order_items)).options(joinedload(Order.supplier)).filter(Order
                                                                                                                         .order_date.between(start_date, end_date)).all()
        except Exception as e:
            raise DatabaseError(
                f'Error retrieving orders by date range: {str(e)}')

        @inject(MaterialService)
            def search(self, search_term: str, fields: List[str] = None, limit: int = 10
                   ) -> List[Order]:
        """
        Search for orders using a flexible search across multiple fields.

        Args:
            search_term (str): Term to search for
            fields (Optional[List[str]]): Specific fields to search
            limit (int, optional): Maximum number of results. Defaults to 10.

        Returns:
            List of Order instances matching the search criteria
        """
        try:
            if not fields:
                fields = ['order_number', 'notes']
            search_conditions = []
            normalized_term = f'%{search_term.lower().strip()}%'
            for field in fields:
                if field == 'order_number':
                    search_conditions.append(func.lower(Order.order_number)
                                             .like(normalized_term))
                elif field == 'notes':
                    search_conditions.append(func.lower(Order.notes).like(
                        normalized_term))
            supplier_subquery = self.session.query(Supplier).filter(func.
                                                                    lower(Supplier.name).like(normalized_term)).subquery()
            query = self.session.query(Order).options(joinedload(Order.
                                                                 order_items)).options(joinedload(Order.supplier)).filter(or_
                                                                                                                          (*search_conditions)).limit(limit)
            return query.all()
        except Exception as e:
            raise DatabaseError(f'Error searching orders: {str(e)}')

        @inject(MaterialService)
            def create(self, order: Order) -> Order:
        """
        Create a new order with associated items.

        Args:
            order (Order): Order instance to create

        Returns:
            Created Order instance

        Raises:
            ValidationError: If order creation fails validation
            DatabaseError: For database-related errors
        """
        try:
            if not order.order_items:
                raise ValidationError('Order must have at least one item')
            order.calculate_total_amount()
            self.session.add(order)
            for item in order.order_items:
                self.session.add(item)
            self.session.commit()
            return order
        except (ValidationError, DatabaseError):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(f'Error creating order: {str(e)}')

        @inject(MaterialService)
            def update(self, order_id: int, order: Order) -> Order:
        """
        Update an existing order with new information.

        Args:
            order_id (int): ID of the order to update
            order (Order): Updated Order instance

        Returns:
            Updated Order instance

        Raises:
            ValidationError: If order update fails validation
            DatabaseError: For database-related errors
        """
        try:
            existing_order = self.get(order_id)
            if not existing_order:
                raise ValidationError(f'Order with ID {order_id} not found')
            if not order.order_items:
                raise ValidationError('Order must have at least one item')
            order.calculate_total_amount()
            for key, value in order.__dict__.items():
                if not key.startswith('_') and key != 'id':
                    setattr(existing_order, key, value)
            existing_order.order_items.clear()
            for item in order.order_items:
                item.order_id = existing_order.id
                self.session.add(item)
            self.session.commit()
            return existing_order
        except (ValidationError, DatabaseError):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(f'Error updating order: {str(e)}')

        @inject(MaterialService)
            def delete(self, order_id: int) -> bool:
        """
        Delete an order and its associated items.

        Args:
            order_id (int): ID of the order to delete

        Returns:
            Boolean indicating successful deletion

        Raises:
            ValidationError: If order cannot be deleted
            DatabaseError: For database-related errors
        """
        try:
            order = self.get(order_id)
            if not order:
                raise ValidationError(f'Order with ID {order_id} not found')
            for item in order.order_items:
                self.session.delete(item)
            self.session.delete(order)
            self.session.commit()
            return True
        except (ValidationError, DatabaseError):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            raise DatabaseError(f'Error deleting order: {str(e)}')
