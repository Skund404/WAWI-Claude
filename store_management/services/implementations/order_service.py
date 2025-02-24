

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class OrderService(Service, IOrderService):
    """
    Implementation of the Order Service.

    Provides methods for managing order-related operations.
    """

    @inject(MaterialService)
        def __init__(self, session: Optional[Session] = None):
        """
        Initialize the Order Service.

        Args:
            session (Optional[Session]): SQLAlchemy database session
        """
        super().__init__(None)
        self._session = session or get_db()
        self._logger = logging.getLogger(__name__)

        @inject(MaterialService)
            def get_all_orders(self) -> List[Dict[str, Any]]:
        """
        Retrieve all orders.

        Returns:
            List[Dict[str, Any]]: List of order dictionaries
        """
        try:
            orders = self._session.query(Order).all()
            return [order.to_dict(include_items=True) for order in orders]
        except SQLAlchemyError as e:
            self._logger.error(f'Error retrieving orders: {e}')
            raise

        @inject(MaterialService)
            def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific order by ID.

        Args:
            order_id (int): Unique identifier for the order
                    returns:
                    Optional[Dict[str, Any]]: Order details or None if not found

                Raises:
                    ResourceNotFoundError: If order is not found
                """
        try:
            order = self._session.query(Order).get(order_id)
            if not order:
                raise ResourceNotFoundError('Order', str(order_id))
            return order.to_dict(include_items=True)
        except SQLAlchemyError as e:
            self._logger.error(f'Error retrieving order {order_id}: {e}')
            raise

        @inject(MaterialService)
            def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new order.

        Args:
            order_data (Dict[str, Any]): Data for creating a new order

        Returns:
            Dict[str, Any]: Created order details

        Raises:
            ValidationError: If order data is invalid
        """
        try:
            required_fields = ['supplier_id', 'order_number']
            for field in required_fields:
                if field not in order_data:
                    raise ValidationError(f'Missing required field: {field}')
            supplier = self._session.query(Supplier).get(order_data[
                'supplier_id'])
            if not supplier:
                raise ResourceNotFoundError('Supplier', str(order_data[
                    'supplier_id']))
            order = Order(order_number=order_data['order_number'],
                          supplier_id=order_data['supplier_id'],
                          expected_delivery_date=order_data.get(
                'expected_delivery_date'), status=order_data.get('status',
                                                                 OrderStatus.PENDING))
            if 'order_items' in order_data:
                for item_data in order_data['order_items']:
                    order_item = OrderItem(product_id=item_data[
                        'product_id'], quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'])
                    order.add_item(order_item)
            order.total_amount = order.calculate_total_amount()
            self._session.add(order)
            self._session.commit()
            return order.to_dict(include_items=True)
        except (SQLAlchemyError, ValidationError) as e:
            self._session.rollback()
            self._logger.error(f'Error creating order: {e}')
            raise

        @inject(MaterialService)
            def update_order(self, order_id: int, order_data: Dict[str, Any]) -> Dict[
                str, Any]:
        """
        Update an existing order.

        Args:
            order_id (int): Unique identifier for the order
            order_data (Dict[str, Any]): Updated order information

        Returns:
            Dict[str, Any]: Updated order details

        Raises:
            ResourceNotFoundError: If order is not found
        """
        try:
            order = self._session.query(Order).get(order_id)
            if not order:
                raise ResourceNotFoundError('Order', str(order_id))
            if 'status' in order_data:
                order.update_status(order_data['status'])
            if 'expected_delivery_date' in order_data:
                order.expected_delivery_date = order_data[
                    'expected_delivery_date']
            if 'order_items' in order_data:
                order.order_items.clear()
                for item_data in order_data['order_items']:
                    order_item = OrderItem(product_id=item_data[
                        'product_id'], quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'])
                    order.add_item(order_item)
            order.total_amount = order.calculate_total_amount()
            self._session.commit()
            return order.to_dict(include_items=True)
        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f'Error updating order {order_id}: {e}')
            raise

        @inject(MaterialService)
            def delete_order(self, order_id: int) -> bool:
        """
        Delete an order.

        Args:
            order_id (int): Unique identifier for the order

        Returns:
            bool: True if deletion was successful

        Raises:
            ResourceNotFoundError: If order is not found
        """
        try:
            order = self._session.query(Order).get(order_id)
            if not order:
                raise ResourceNotFoundError('Order', str(order_id))
            self._session.delete(order)
            self._session.commit()
            return True
        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f'Error deleting order {order_id}: {e}')
            raise

        @inject(MaterialService)
            def get_orders_by_status(self, status: OrderStatus) -> List[Dict[str, Any]]:
        """
        Retrieve orders by their status.

        Args:
            status (OrderStatus): Status to filter orders by

        Returns:
            List[Dict[str, Any]]: List of orders with the specified status
        """
        try:
            orders = self._session.query(Order).filter(Order.status == status
                                                       ).all()
            return [order.to_dict(include_items=True) for order in orders]
        except SQLAlchemyError as e:
            self._logger.error(
                f'Error retrieving orders with status {status}: {e}')
            raise

        @inject(MaterialService)
            def get_orders_by_date_range(self, start_date: datetime, end_date: datetime
                                     ) -> List[Dict[str, Any]]:
        """
        Retrieve orders within a specific date range.

        Args:
            start_date (datetime): Start of the date range
            end_date (datetime): End of the date range

        Returns:
            List[Dict[str, Any]]: List of orders within the date range
        """
        try:
            orders = self._session.query(Order).filter(Order.order_date.
                                                       between(start_date, end_date)).all()
            return [order.to_dict(include_items=True) for order in orders]
        except SQLAlchemyError as e:
            self._logger.error(f'Error retrieving orders by date range: {e}')
            raise

        @inject(MaterialService)
            def get_supplier_orders(self, supplier_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve all orders for a specific supplier.

        Args:
            supplier_id (int): Unique identifier for the supplier

        Returns:
            List[Dict[str, Any]]: List of orders for the specified supplier

        Raises:
            ResourceNotFoundError: If supplier is not found
        """
        try:
            supplier = self._session.query(Supplier).get(supplier_id)
            if not supplier:
                raise ResourceNotFoundError('Supplier', str(supplier_id))
            orders = self._session.query(Order).filter(Order.supplier_id ==
                                                       supplier_id).all()
            return [order.to_dict(include_items=True) for order in orders]
        except SQLAlchemyError as e:
            self._logger.error(
                f'Error retrieving orders for supplier {supplier_id}: {e}')
            raise

        @inject(MaterialService)
            def generate_order_report(self, start_date: datetime, end_date: datetime
                                  ) -> Dict[str, Any]:
        """
        Generate a comprehensive order report for a given period.

        Args:
            start_date (datetime): Start of the reporting period
            end_date (datetime): End of the reporting period

        Returns:
            Dict[str, Any]: Detailed order report
        """
        try:
            orders = self._session.query(Order).filter(Order.order_date.
                                                       between(start_date, end_date)).all()
            report = {'total_orders': len(orders), 'total_revenue': sum(
                order.total_amount for order in orders), 'orders_by_status':
                {}, 'top_suppliers': {}}
            for status in OrderStatus:
                report['orders_by_status'][status.value] = sum(1 for order in
                                                               orders if order.status == status)
            supplier_totals = {}
            for order in orders:
                supplier_totals[order.supplier_id] = supplier_totals.get(order
                                                                         .supplier_id, 0) + order.total_amount
            report['top_suppliers'] = dict(sorted(supplier_totals.items(),
                                                  key=lambda x: x[1], reverse=True)[:5])
            return report
        except SQLAlchemyError as e:
            self._logger.error(f'Error generating order report: {e}')
            raise
