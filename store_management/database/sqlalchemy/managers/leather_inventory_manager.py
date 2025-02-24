

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class LeatherInventoryManager(BaseManager[Leather]):
    """Specialized manager for leather inventory operations with area tracking."""

    @inject(MaterialService)
        def __init__(self, session_factory):
        """Initialize LeatherInventoryManager with session factory."""
        super().__init__(session_factory, Leather)

        @inject(MaterialService)
            def add_leather(self, data: Dict[str, Any]) -> Leather:
        """Add new leather to inventory with initial area tracking.

        Args:
            data: Leather data including initial area and supplier

        Returns:
            Created Leather instance

        Raises:
            DatabaseError: If validation fails or database operation fails
        """
        try:
            with self.session_scope() as session:
                leather = Leather(name=data['name'], type=data['type'],
                                  color=data.get('color'), thickness=data.get('thickness'
                                                                              ), supplier_id=data.get('supplier_id'), unit_price=data
                                  ['unit_price'], total_area=data['initial_area'],
                                  available_area=data['initial_area'], minimum_area=data.
                                  get('minimum_area', 0), status=InventoryStatus.IN_STOCK,
                                  location=data.get('location'), notes=data.get('notes'),
                                  created_at=datetime.now(), modified_at=datetime.now())
                session.add(leather)
                session.flush()
                transaction = LeatherTransaction(leather_id=leather.id,
                                                 transaction_type=TransactionType.INITIAL_STOCK,
                                                 area_change=data['initial_area'], remaining_area=data[
                                                     'initial_area'], unit_price=data['unit_price'], notes='Initial stock entry', created_at=datetime.now())
                session.add(transaction)
                return leather
        except SQLAlchemyError as e:
            logger.error(f'Failed to add leather: {str(e)}')
            raise DatabaseError(f'Failed to add leather: {str(e)}')

        @inject(MaterialService)
            def update_leather_area(self, leather_id: int, area_change: float,
                                transaction_type: TransactionType, notes: Optional[str] = None,
                                wastage: Optional[float] = None) -> Tuple[Leather, LeatherTransaction]:
        """Update leather area with transaction tracking and wastage calculation.

        Args:
            leather_id: Leather ID
            area_change: Change in area (negative for consumption)
            transaction_type: Type of transaction
            notes: Optional transaction notes
            wastage: Optional wastage area to track

        Returns:
            Tuple of (updated Leather instance, created Transaction)

        Raises:
            DatabaseError: If update fails or would result in negative area
        """
        try:
            with self.session_scope() as session:
                leather = session.get(Leather, leather_id)
                if not leather:
                    raise DatabaseError(f'Leather {leather_id} not found')
                new_area = leather.available_area + area_change
                if new_area < 0:
                    raise DatabaseError('Update would result in negative area')
                leather.available_area = new_area
                leather.modified_at = datetime.now()
                if new_area <= leather.minimum_area:
                    leather.status = InventoryStatus.LOW_STOCK
                elif new_area == 0:
                    leather.status = InventoryStatus.OUT_OF_STOCK
                else:
                    leather.status = InventoryStatus.IN_STOCK
                transaction = LeatherTransaction(leather_id=leather_id,
                                                 transaction_type=transaction_type, area_change=area_change, remaining_area=new_area, wastage=wastage,
                                                 notes=notes, created_at=datetime.now())
                session.add(transaction)
                return leather, transaction
        except SQLAlchemyError as e:
            logger.error(f'Failed to update leather area: {str(e)}')
            raise DatabaseError(f'Failed to update leather area: {str(e)}')

        @inject(MaterialService)
            def get_leather_with_transactions(self, leather_id: int,
                                          include_wastage: bool = False) -> Optional[Dict[str, Any]]:
        """Get leather details with transaction history and optional wastage analysis.

        Args:
            leather_id: Leather ID
            include_wastage: Whether to include wastage calculations

        Returns:
            Dictionary with leather details and transaction history
        """
        try:
            with self.session_scope() as session:
                leather = session.query(Leather).options(joinedload(Leather
                                                                    .transactions), joinedload(Leather.supplier)).filter(
                    Leather.id == leather_id).first()
                if not leather:
                    return None
                result = {'leather': leather, 'transactions': leather.
                          transactions, 'total_area': leather.total_area,
                          'available_area': leather.available_area, 'used_area':
                          leather.total_area - leather.available_area}
                if include_wastage:
                    total_wastage = sum(t.wastage for t in leather.
                                        transactions if t.wastage is not None)
                    result.update({'total_wastage': total_wastage,
                                   'wastage_percentage': total_wastage / leather.
                                   total_area * 100 if leather.total_area > 0 else 0})
                return result
        except SQLAlchemyError as e:
            logger.error(f'Failed to get leather details: {str(e)}')
            raise DatabaseError(f'Failed to get leather details: {str(e)}')

        @inject(MaterialService)
            def get_low_stock_leather(self, include_out_of_stock: bool = True,
                                  supplier_id: Optional[int] = None) -> List[Leather]:
        """Get leather items with low stock levels.

        Args:
            include_out_of_stock: Whether to include out of stock items
            supplier_id: Optional supplier ID to filter by

        Returns:
            List of Leather instances with low stock
        """
        try:
            with self.session_scope() as session:
                filters = [Leather.status == InventoryStatus.LOW_STOCK]
                if include_out_of_stock:
                    filters.append(Leather.status == InventoryStatus.
                                   OUT_OF_STOCK)
                if supplier_id:
                    filters.append(Leather.supplier_id == supplier_id)
                query = select(Leather).options(joinedload(Leather.supplier)
                                                ).where(or_(*filters)).order_by(Leather.available_area)
                result = session.execute(query).scalars().all()
                return result
        except SQLAlchemyError as e:
            logger.error(f'Failed to get low stock leather: {str(e)}')
            raise DatabaseError(f'Failed to get low stock leather: {str(e)}')

        @inject(MaterialService)
            def calculate_leather_efficiency(self, leather_id: int, date_range:
                                         Optional[Tuple[datetime, datetime]] = None) -> Dict[str, float]:
        """Calculate leather usage efficiency metrics.

        Args:
            leather_id: Leather ID
            date_range: Optional tuple of (start_date, end_date)

        Returns:
            Dictionary containing efficiency metrics
        """
        try:
            with self.session_scope() as session:
                query = session.query(LeatherTransaction).filter(
                    LeatherTransaction.leather_id == leather_id)
                if date_range:
                    start_date, end_date = date_range
                    query = query.filter(LeatherTransaction.created_at.
                                         between(start_date, end_date))
                transactions = query.all()
                total_used = sum(abs(t.area_change) for t in transactions if
                                 t.area_change < 0)
                total_wastage = sum(t.wastage for t in transactions if t.
                                    wastage is not None)
                return {'total_used_area': total_used, 'total_wastage':
                        total_wastage, 'efficiency_percentage': (total_used -
                                                                 total_wastage) / total_used * 100 if total_used > 0 else
                        100, 'wastage_percentage': total_wastage / total_used *
                        100 if total_used > 0 else 0}
        except SQLAlchemyError as e:
            logger.error(f'Failed to calculate leather efficiency: {str(e)}')
            raise DatabaseError(
                f'Failed to calculate leather efficiency: {str(e)}')

        @inject(MaterialService)
            def adjust_minimum_area(self, leather_id: int, new_minimum: float
                                ) -> Leather:
        """Adjust minimum area threshold for a leather type.

        Args:
            leather_id: Leather ID
            new_minimum: New minimum area threshold

        Returns:
            Updated Leather instance
        """
        try:
            with self.session_scope() as session:
                leather = session.get(Leather, leather_id)
                if not leather:
                    raise DatabaseError(f'Leather {leather_id} not found')
                leather.minimum_area = new_minimum
                leather.modified_at = datetime.now()
                if leather.available_area <= new_minimum:
                    leather.status = InventoryStatus.LOW_STOCK
                elif leather.available_area > new_minimum:
                    leather.status = InventoryStatus.IN_STOCK
                return leather
        except SQLAlchemyError as e:
            logger.error(f'Failed to adjust minimum area: {str(e)}')
            raise DatabaseError(f'Failed to adjust minimum area: {str(e)}')
