

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
class SupplierService(Service, ISupplierService):
    """
    Implementation of the Supplier Service.

    Provides methods for managing supplier-related operations.
    """

        @inject(MaterialService)
        def __init__(self, session: Optional[Session]=None):
        """
        Initialize the Supplier Service.

        Args:
            session (Optional[Session]): SQLAlchemy database session
        """
        super().__init__(None)
        self._session = session or get_db()
        self._logger = logging.getLogger(__name__)

        @inject(MaterialService)
        def get_all_suppliers(self) ->List[Dict[str, Any]]:
        """
        Retrieve all suppliers.

        Returns:
            List[Dict[str, Any]]: List of supplier dictionaries
        """
        try:
            suppliers = self._session.query(Supplier).all()
            return [supplier.to_dict() for supplier in suppliers]
        except SQLAlchemyError as e:
            self._logger.error(f'Error retrieving suppliers: {e}')
            raise

        @inject(MaterialService)
        def get_supplier_by_id(self, supplier_id: int) ->Optional[Dict[str, Any]]:
        """
        Retrieve a specific supplier by ID.

        Args:
            supplier_id (int): Unique identifier for the supplier

        Returns:
            Optional[Dict[str, Any]]: Supplier details or None if not found
        """
        try:
            supplier = self._session.query(Supplier).get(supplier_id)
            return supplier.to_dict(include_orders=True) if supplier else None
        except SQLAlchemyError as e:
            self._logger.error(f'Error retrieving supplier {supplier_id}: {e}')
            raise

        @inject(MaterialService)
        def create_supplier(self, supplier_data: Dict[str, Any]) ->Dict[str, Any]:
        """
        Create a new supplier.

        Args:
            supplier_data (Dict[str, Any]): Data for creating a new supplier

        Returns:
            Dict[str, Any]: Created supplier details
        """
        try:
            required_fields = ['name', 'email']
            for field in required_fields:
                if field not in supplier_data:
                    raise ValueError(f'Missing required field: {field}')
            new_supplier = Supplier(**supplier_data)
            self._session.add(new_supplier)
            self._session.commit()
            return new_supplier.to_dict()
        except (SQLAlchemyError, ValueError) as e:
            self._session.rollback()
            self._logger.error(f'Error creating supplier: {e}')
            raise

        @inject(MaterialService)
        def update_supplier(self, supplier_id: int, supplier_data: Dict[str, Any]
        ) ->Dict[str, Any]:
        """
        Update an existing supplier.

        Args:
            supplier_id (int): Unique identifier for the supplier
            supplier_data (Dict[str, Any]): Updated supplier information

        Returns:
            Dict[str, Any]: Updated supplier details
        """
        try:
            supplier = self._session.query(Supplier).get(supplier_id)
            if not supplier:
                raise ValueError(f'Supplier with ID {supplier_id} not found')
            for key, value in supplier_data.items():
                if hasattr(supplier, key):
                    setattr(supplier, key, value)
            self._session.commit()
            return supplier.to_dict()
        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f'Error updating supplier {supplier_id}: {e}')
            raise

        @inject(MaterialService)
        def delete_supplier(self, supplier_id: int) ->bool:
        """
        Delete a supplier.

        Args:
            supplier_id (int): Unique identifier for the supplier

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            supplier = self._session.query(Supplier).get(supplier_id)
            if not supplier:
                raise ValueError(f'Supplier with ID {supplier_id} not found')
            self._session.delete(supplier)
            self._session.commit()
            return True
        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f'Error deleting supplier {supplier_id}: {e}')
            raise

        @inject(MaterialService)
        def get_supplier_performance(self, supplier_id: int, start_date:
        datetime, end_date: datetime) ->Dict[str, Any]:
        """
        Get performance metrics for a specific supplier.

        Args:
            supplier_id (int): Unique identifier for the supplier
            start_date (datetime): Start of the performance period
            end_date (datetime): End of the performance period

        Returns:
            Dict[str, Any]: Supplier performance metrics
        """
        try:
            supplier = self._session.query(Supplier).get(supplier_id)
            if not supplier:
                raise ValueError(f'Supplier with ID {supplier_id} not found')
            orders = supplier.orders.filter(Order.created_at.between(
                start_date, end_date)).all()
            performance = {'total_orders': len(orders), 'total_value': sum(
                order.total_amount for order in orders),
                'on_time_delivery_rate': self._calculate_on_time_delivery(
                orders), 'supplier_rating': supplier.rating}
            return performance
        except SQLAlchemyError as e:
            self._logger.error(f'Error calculating supplier performance: {e}')
            raise

        @inject(MaterialService)
        def generate_supplier_report(self) ->List[Dict[str, Any]]:
        """
        Generate a comprehensive report of all suppliers.

        Returns:
            List[Dict[str, Any]]: Detailed supplier report
        """
        try:
            suppliers = self._session.query(Supplier).all()
            report = []
            for supplier in suppliers:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                performance = self.get_supplier_performance(supplier.id,
                    start_date, end_date)
                supplier_report = supplier.to_dict()
                supplier_report.update(performance)
                report.append(supplier_report)
            return report
        except SQLAlchemyError as e:
            self._logger.error(f'Error generating supplier report: {e}')
            raise

        @inject(MaterialService)
        def _calculate_on_time_delivery(self, orders: List['Order']) ->float:
        """
        Calculate on-time delivery rate for a set of orders.

        Args:
            orders (List[Order]): List of orders to analyze

        Returns:
            float: Percentage of on-time deliveries
        """
        if not orders:
            return 0.0
        on_time_deliveries = sum(1 for order in orders if order.
            delivery_date <= order.expected_delivery_date)
        return on_time_deliveries / len(orders) * 100
