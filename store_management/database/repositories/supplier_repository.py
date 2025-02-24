from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/database/repositories/supplier_repository.py

Supplier repository for database access.
"""
logger = logging.getLogger(__name__)


class SupplierRepository(BaseRepository):
    """
    Repository for Supplier model database access.

    This class provides specialized operations for the Supplier model.
    """

        @inject(MaterialService)
        def __init__(self, session: Session):
        """
        Initialize a new SupplierRepository instance.

        Args:
            session: SQLAlchemy session.
        """
        super().__init__(session, Supplier)

        @inject(MaterialService)
        def search(self, search_term: str, fields: List[str], limit: Optional[
        int]=None) ->List[Supplier]:
        """
        Search for suppliers by a search term in specified fields.

        Args:
            search_term: The search term.
            fields: List of field names to search in.
            limit: Maximum number of results to return.

        Returns:
            List of suppliers that match the search criteria.
        """
        try:
            from sqlalchemy import or_
            if not search_term or not fields:
                return []
            conditions = []
            for field in fields:
                if hasattr(Supplier, field):
                    attr = getattr(Supplier, field)
                    conditions.append(attr.ilike(f'%{search_term}%'))
            if not conditions:
                return []
            query = self.session.query(Supplier).filter(or_(*conditions))
            if limit:
                query = query.limit(limit)
            return query.all()
        except SQLAlchemyError as e:
            logger.error(
                f"Error searching suppliers for '{search_term}' in {fields}: {str(e)}"
                )
            return []

        @inject(MaterialService)
        def get_supplier_orders(self, supplier_id: int, start_date: Optional[
        datetime]=None, end_date: Optional[datetime]=None) ->List[Any]:
        """
        Get orders for a supplier.

        Args:
            supplier_id: The ID of the supplier.
            start_date: Optional start date for filtering orders.
            end_date: Optional end date for filtering orders.

        Returns:
            List of orders for the supplier.
        """
        try:
            supplier = self.get_by_id(supplier_id)
            if not supplier or not hasattr(supplier, 'orders'):
                return []
            if supplier.orders is None:
                return []
            if start_date or end_date:
                from sqlalchemy import and_
                conditions = []
                if start_date:
                    conditions.append(Order.created_at >= start_date)
                if end_date:
                    conditions.append(Order.created_at <= end_date)
                return self.session.query(Order).filter(and_(Order.
                    supplier_id == supplier_id, *conditions)).all()
            return supplier.orders
        except (SQLAlchemyError, NameError) as e:
            logger.error(
                f'Error getting orders for supplier ID {supplier_id}: {str(e)}'
                )
            return []

        @inject(MaterialService)
        def get_top_suppliers(self, limit: int=10, performance_metric: str='rating'
        ) ->List[Supplier]:
        """
        Get top suppliers based on a performance metric.

        Args:
            limit: Maximum number of suppliers to return.
            performance_metric: Metric to sort by (rating, reliability_score, etc.).

        Returns:
            List of top suppliers.
        """
        try:
            if not hasattr(Supplier, performance_metric):
                logger.warning(
                    f'Invalid performance metric: {performance_metric}')
                performance_metric = 'rating'
            metric_attr = getattr(Supplier, performance_metric)
            return self.session.query(Supplier).filter(Supplier.is_active ==
                True).order_by(desc(metric_attr)).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(
                f'Error getting top suppliers by {performance_metric}: {str(e)}'
                )
            return []

        @inject(MaterialService)
        def create(self, data: Dict[str, Any]) ->Optional[Supplier]:
        """
        Create a new supplier.

        Args:
            data: Dictionary of supplier data.

        Returns:
            The created supplier, or None if creation failed.
        """
        try:
            if 'name' not in data or not data['name']:
                raise ValueError('Supplier name is required')
            supplier = Supplier(**data)
            self.session.add(supplier)
            self.session.flush()
            logger.info(f'Created supplier: {supplier.name}')
            return supplier
        except Exception as e:
            logger.error(f'Error creating supplier: {str(e)}')
            self.session.rollback()
            return None

        @inject(MaterialService)
        def update(self, supplier_id: int, data: Dict[str, Any]) ->Optional[
        Supplier]:
        """
        Update a supplier.

        Args:
            supplier_id: The ID of the supplier to update.
            data: Dictionary of supplier data to update.

        Returns:
            The updated supplier, or None if update failed.
        """
        try:
            supplier = self.get_by_id(supplier_id)
            if not supplier:
                logger.warning(
                    f'Supplier with ID {supplier_id} not found for update')
                return None
            for key, value in data.items():
                if hasattr(supplier, key):
                    setattr(supplier, key, value)
            self.session.flush()
            logger.info(f'Updated supplier: {supplier.name}')
            return supplier
        except Exception as e:
            logger.error(
                f'Error updating supplier with ID {supplier_id}: {str(e)}')
            self.session.rollback()
            return None

        @inject(MaterialService)
        def delete(self, supplier_id: int) ->bool:
        """
        Delete a supplier.

        Args:
            supplier_id: The ID of the supplier to delete.

        Returns:
            True if deletion was successful, False otherwise.
        """
        try:
            supplier = self.get_by_id(supplier_id)
            if not supplier:
                logger.warning(
                    f'Supplier with ID {supplier_id} not found for deletion')
                return False
            supplier.is_active = False
            self.session.flush()
            logger.info(f'Marked supplier as inactive: {supplier.name}')
            return True
        except Exception as e:
            logger.error(
                f'Error deactivating supplier with ID {supplier_id}: {str(e)}')
            self.session.rollback()
            return False
