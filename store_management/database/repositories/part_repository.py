

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
class PartRepository(BaseRepository[Part]):
    """Repository for Part model operations"""

        @inject(MaterialService)
        def __init__(self, session: Session):
        super().__init__(session, Part)

        @inject(MaterialService)
        def get_low_stock(self) ->List[Part]:
        """
        Get parts with low stock levels.

        Returns:
            List of parts with low stock
        """
        return self.session.query(Part).filter(Part.status.in_([
            InventoryStatus.LOW_STOCK, InventoryStatus.OUT_OF_STOCK])).all()

        @inject(MaterialService)
        def get_by_supplier(self, supplier_id: int) ->List[Part]:
        """
        Get parts by supplier.

        Args:
            supplier_id: Supplier ID

        Returns:
            List of parts from the specified supplier
        """
        return self.session.query(Part).filter(Part.supplier_id == supplier_id
            ).all()

        @inject(MaterialService)
        def get_with_transactions(self, part_id: int) ->Optional[Part]:
        """
        Get part with transaction history.

        Args:
            part_id: Part ID

        Returns:
            Part with loaded transactions or None
        """
        return self.session.query(Part).options(joinedload(Part.transactions)
            ).filter(Part.id == part_id).first()
