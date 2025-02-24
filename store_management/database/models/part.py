from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
logger = logging.getLogger(__name__)


class Part(BaseModel):
    """
    Model for parts/components inventory.
    """
    __tablename__ = 'parts'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    quantity = Column(Float, default=0)
    unit = Column(String(20), nullable=False)
    minimum_stock = Column(Float, default=0)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    transactions = relationship('InventoryTransaction', back_populates=
        'part', cascade='all, delete-orphan')
    supplier = relationship('Supplier', back_populates='parts')
