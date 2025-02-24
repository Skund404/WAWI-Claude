

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class SupplierManager(BaseManager[Supplier]):
    """
    Manager for handling supplier operations and relationships.
    Includes supplier performance tracking and order history management.
    """

    @inject(MaterialService)
        def __init__(self, session_factory):
        """Initialize SupplierManager with session factory."""
        super().__init__(session_factory, Supplier)

        @inject(MaterialService)
            def create_supplier(self, data: Dict[str, Any]) -> Supplier:
        """
        Create a new supplier with validation.

        Args:
            data: Supplier data including contact information

        Returns:
            Created Supplier instance

        Raises:
            DatabaseError: If validation fails
        """
        required_fields = ['name', 'contact_person', 'email', 'phone']
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            raise DatabaseError(
                f"Missing required fields: {', '.join(missing_fields)}")
        try:
            return self.create(data)
        except SQLAlchemyError as e:
            raise DatabaseError(f'Failed to create supplier: {str(e)}')

        @inject(MaterialService)
            def update_supplier(self, supplier_id: int, data: Dict[str, Any]
                            ) -> Optional[Supplier]:
        """
        Update supplier information.

        Args:
            supplier_id: Supplier ID
            data: Updated supplier data

        Returns:
            Updated Supplier instance or None if not found
        """
        try:
            supplier = self.update(supplier_id, data)
            if supplier:
                supplier.modified_at = datetime.utcnow()
            return supplier
        except SQLAlchemyError as e:
            raise DatabaseError(f'Failed to update supplier: {str(e)}')

        @inject(MaterialService)
            def get_supplier_with_orders(self, supplier_id: int) -> Optional[Supplier]:
        """
        Get supplier with their order history.

        Args:
            supplier_id: Supplier ID

        Returns:
            Supplier instance with orders loaded or None if not found
        """
        with self.session_scope() as session:
            query = select(Supplier).options(joinedload(Supplier.orders)
                                             ).filter(Supplier.id == supplier_id)
            return session.execute(query).scalar()

        @inject(MaterialService)
            def get_supplier_products(self, supplier_id: int) -> Dict[str, List]:
        """
        Get all products supplied by a supplier.

        Args:
            supplier_id: Supplier ID

        Returns:
            Dictionary containing parts and leather supplied
        """
        with self.session_scope() as session:
            supplier = session.get(Supplier, supplier_id)
            if not supplier:
                raise DatabaseError(f'Supplier {supplier_id} not found')
            parts = session.query(Part).filter(Part.supplier_id == supplier_id
                                               ).all()
            leather = session.query(Leather).filter(Leather.supplier_id ==
                                                    supplier_id).all()
            return {'parts': parts, 'leather': leather}

        @inject(MaterialService)
            def get_supplier_performance(self, supplier_id: int) -> Dict[str, Any]:
        """
        Calculate supplier performance metrics.

        Args:
            supplier_id: Supplier ID

        Returns:
            Dictionary containing performance metrics
        """
        with self.session_scope() as session:
            supplier = session.get(Supplier, supplier_id)
            if not supplier:
                raise DatabaseError(f'Supplier {supplier_id} not found')
            orders = session.query(Order).filter(Order.supplier_id ==
                                                 supplier_id).all()
            total_orders = len(orders)
            if total_orders == 0:
                return {'total_orders': 0, 'on_time_delivery_rate': 0,
                        'average_delay_days': 0, 'order_fulfillment_rate': 0,
                        'quality_rating': supplier.quality_rating or 0}
            on_time_deliveries = sum(1 for o in orders if o.delivery_date and
                                     o.delivery_date <= o.expected_delivery_date)
            delays = [(o.delivery_date - o.expected_delivery_date).days for
                      o in orders if o.delivery_date and o.delivery_date > o.
                      expected_delivery_date]
            fulfilled_orders = sum(1 for o in orders if o.status == 'completed'
                                   )
            return {'total_orders': total_orders, 'on_time_delivery_rate':
                    on_time_deliveries / total_orders * 100,
                    'average_delay_days': sum(delays) / len(delays) if delays else
                    0, 'order_fulfillment_rate': fulfilled_orders /
                    total_orders * 100, 'quality_rating': supplier.
                    quality_rating or 0}

        @inject(MaterialService)
            def update_supplier_rating(self, supplier_id: int, rating: float, notes:
                                   Optional[str] = None) -> Supplier:
        """
        Update supplier quality rating.

        Args:
            supplier_id: Supplier ID
            rating: New rating (0-5)
            notes: Optional notes about the rating

        Returns:
            Updated Supplier instance
        """
        if not 0 <= rating <= 5:
            raise DatabaseError('Rating must be between 0 and 5')
        with self.session_scope() as session:
            supplier = session.get(Supplier, supplier_id)
            if not supplier:
                raise DatabaseError(f'Supplier {supplier_id} not found')
            supplier.quality_rating = rating
            supplier.rating_notes = notes
            supplier.modified_at = datetime.utcnow()
            return supplier

        @inject(MaterialService)
            def get_supplier_order_history(self, supplier_id: int, start_date:
                                       Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[
                Order]:
        """
        Get supplier's order history with optional date range.

        Args:
            supplier_id: Supplier ID
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            List of Order instances
        """
        query = select(Order).filter(Order.supplier_id == supplier_id)
        if start_date:
            query = query.filter(Order.order_date >= start_date)
        if end_date:
            query = query.filter(Order.order_date <= end_date)
        query = query.order_by(Order.order_date.desc())
        with self.session_scope() as session:
            return list(session.execute(query).scalars())

        @inject(MaterialService)
            def get_top_suppliers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top suppliers based on order volume and performance.

        Args:
            limit: Number of suppliers to return

        Returns:
            List of supplier data with performance metrics
        """
        with self.session_scope() as session:
            suppliers = session.query(Supplier).options(joinedload(Supplier
                                                                   .orders)).all()
            supplier_metrics = []
            for supplier in suppliers:
                total_orders = len(supplier.orders)
                if total_orders == 0:
                    continue
                completed_orders = sum(1 for o in supplier.orders if o.
                                       status == 'completed')
                on_time_orders = sum(1 for o in supplier.orders if o.
                                     delivery_date and o.delivery_date <= o.
                                     expected_delivery_date)
                supplier_metrics.append({'id': supplier.id, 'name':
                                         supplier.name, 'total_orders': total_orders,
                                         'completed_orders': completed_orders,
                                         'on_time_delivery_rate': on_time_orders / total_orders *
                                         100, 'quality_rating': supplier.quality_rating or 0,
                                         'performance_score': (completed_orders / total_orders *
                                                               0.4 + on_time_orders / total_orders * 0.4 + (supplier.
                                                                                                            quality_rating or 0) / 5 * 0.2) * 100})
            return sorted(supplier_metrics, key=lambda x: x[
                'performance_score'], reverse=True)[:limit]

        @inject(MaterialService)
            def get_supplier_categories(self, supplier_id: int) -> List[str]:
        """
        Get categories of products supplied by a supplier.

        Args:
            supplier_id: Supplier ID

        Returns:
            List of unique product categories
        """
        with self.session_scope() as session:
            part_categories = session.query(Part.category).filter(Part.
                                                                  supplier_id == supplier_id).distinct().all()
            leather_types = session.query(Leather.type).filter(Leather.
                                                               supplier_id == supplier_id).distinct().all()
            categories = [cat[0] for cat in part_categories if cat[0]] + [type_
                                                                          [0] for type_ in leather_types if type_[0]]
            return sorted(set(categories))

        @inject(MaterialService)
            def search_suppliers(self, search_term: str) -> List[Supplier]:
        """
        Search suppliers across multiple fields.

        Args:
            search_term: Term to search for

        Returns:
            List of matching Supplier instances
        """
        query = select(Supplier).filter(or_(Supplier.name.ilike(
            f'%{search_term}%'), Supplier.contact_person.ilike(
            f'%{search_term}%'), Supplier.email.ilike(f'%{search_term}%'),
            Supplier.phone.ilike(f'%{search_term}%'), Supplier.notes.ilike(
            f'%{search_term}%')))
        with self.session_scope() as session:
            return list(session.execute(query).scalars())

        @inject(MaterialService)
            def get_supplier_statistics(self) -> Dict[str, Any]:
        """
        Get overall supplier statistics.

        Returns:
            Dictionary containing supplier statistics
        """
        with self.session_scope() as session:
            total_suppliers = session.query(func.count(Supplier.id)).scalar()
            active_suppliers = session.query(func.count(Supplier.id)).filter(
                Supplier.status == 'active').scalar()
            avg_rating = session.query(func.avg(Supplier.quality_rating)
                                       ).scalar() or 0
            total_orders = session.query(func.count(Order.id)).scalar()
            return {'total_suppliers': total_suppliers, 'active_suppliers':
                    active_suppliers, 'inactive_suppliers': total_suppliers -
                    active_suppliers, 'average_rating': round(avg_rating, 2),
                    'total_orders': total_orders, 'orders_per_supplier': round(
                        total_orders / total_suppliers, 2) if total_suppliers > 0 else
                    0}
