

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class HardwareType(Enum):
    """Enumeration of hardware types."""
    BUCKLE = 'buckle'
    SNAP = 'snap'
    ZIPPER = 'zipper'
    D_RING = 'd_ring'
    RIVET = 'rivet'
    MAGNETIC_CLASP = 'magnetic_clasp'
    BUTTON = 'button'
    OTHER = 'other'


class HardwareMaterial(Enum):
    """Enumeration of hardware materials."""
    BRASS = 'brass'
    STEEL = 'steel'
    NICKEL = 'nickel'
    ZINC = 'zinc'
    ALUMINUM = 'aluminum'
    COPPER = 'copper'
    BRONZE = 'bronze'
    OTHER = 'other'


class Hardware(BaseModel):
    """
    Hardware model representing metal fixtures and accessories used in leatherworking,
    including stock management and specifications.
    """
    __tablename__ = 'hardware'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    hardware_type = Column(SQLEnum(HardwareType), nullable=False)
    material = Column(SQLEnum(HardwareMaterial), nullable=False)
    finish = Column(String(50))
    size = Column(String(50))
    weight = Column(Float)
    load_capacity = Column(Float)
    quantity = Column(Integer, default=0)
    minimum_stock = Column(Integer)
    reorder_point = Column(Integer)
    unit_price = Column(Float)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    supplier_sku = Column(String(50))
    is_active = Column(Boolean, default=True)
    location = Column(String(50))
    notes = Column(String(500))
    supplier = relationship('Supplier', back_populates='hardware_items')
    project_components = relationship(
        'ProjectComponent', back_populates='hardware')

    @inject(MaterialService)
        def __repr__(self) -> str:
        """String representation of the Hardware item."""
        return (
            f"<Hardware(id={self.id}, name='{self.name}', type={self.hardware_type})>"
        )

        @inject(MaterialService)
            def is_low_stock(self) -> bool:
        """
        Check if the hardware item is at or below its reorder point.

        Returns:
            bool: True if stock is low, False otherwise
        """
        return self.quantity <= self.reorder_point

        @inject(MaterialService)
            def update_stock(self, quantity_change: int) -> None:
        """
        Update the hardware stock level.

        Args:
            quantity_change (int): Amount to change stock by (positive or negative)

        Raises:
            ValueError: If resulting quantity would be negative
        """
        new_quantity = self.quantity + quantity_change
        if new_quantity < 0:
            raise ValueError(
                f'Cannot reduce stock below zero. Current stock: {self.quantity}'
            )
        self.quantity = new_quantity
        if self.is_low_stock():
            pass

        @inject(MaterialService)
            def to_dict(self) -> Dict[str, Any]:
        """
        Convert the hardware item to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the hardware item
        """
        base_dict = super().to_dict()
        base_dict.update({'hardware_type': self.hardware_type.value,
                          'material': self.material.value})
        return base_dict
