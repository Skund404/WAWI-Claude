

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class MaterialType(enum.Enum):
    """
    Enum representing different types of materials.
    """
    LEATHER = 'Leather'
    THREAD = 'Thread'
    HARDWARE = 'Hardware'
    FABRIC = 'Fabric'
    OTHER = 'Other'


class MaterialQualityGrade(enum.Enum):
    """
    Enum representing material quality grades.
    """
    PREMIUM = 'Premium'
    HIGH = 'High'
    STANDARD = 'Standard'
    LOW = 'Low'


class Material(BaseModel):
    """
    Represents a material in the store management system.

    Attributes:
        name (str): Name of the material
        material_type (MaterialType): Type of material
        supplier_id (int): Foreign key to the Supplier
        quality_grade (MaterialQualityGrade): Quality grade of the material
        current_stock (float): Current stock quantity
        minimum_stock (float): Minimum stock threshold
        unit_price (float): Price per unit
        is_active (bool): Whether the material is currently active
    """
    __tablename__ = 'materials'
    name = Column(String(255), nullable=False, index=True)
    material_type = Column(Enum(MaterialType), nullable=False)
    supplier_id = Column(Integer, ForeignKey('supplier.id'), nullable=True)
    quality_grade = Column(Enum(MaterialQualityGrade),
                           default=MaterialQualityGrade.STANDARD)
    current_stock = Column(Float, default=0.0)
    minimum_stock = Column(Float, default=0.0)
    unit_price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    last_restocked_date = Column(DateTime(timezone=True))
    supplier = relationship('Supplier', back_populates='materials')
    transactions = relationship(
        'MaterialTransaction', back_populates='material')

    @inject(MaterialService)
        def __repr__(self) -> str:
        """
        String representation of the Material model.

        Returns:
            str: A string showing material name, type, and current stock
        """
        return (
            f"<Material(id={self.id}, name='{self.name}', type={self.material_type.value}, stock={self.current_stock})>"
        )

        @inject(MaterialService)
            def update_stock(self, quantity_change: float, transaction_type: str =
                         'ADJUSTMENT') -> None:
        """
        Update the current stock of the material.

        Args:
            quantity_change (float): Amount to change stock by (positive or negative)
            transaction_type (str): Type of stock transaction

        Raises:
            ValueError: If stock would become negative
        """
        new_stock = self.current_stock + quantity_change
        if new_stock < 0:
            raise ValueError(
                f'Stock cannot become negative. Current: {self.current_stock}, Change: {quantity_change}'
            )
        self.current_stock = new_stock
        self.last_restocked_date = func.now()
        transaction = MaterialTransaction(material_id=self.id,
                                          quantity_change=quantity_change, transaction_type=transaction_type)

        @inject(MaterialService)
            def is_low_stock(self) -> bool:
        """
        Check if material is below minimum stock threshold.

        Returns:
            bool: True if stock is low, False otherwise
        """
        return self.current_stock <= self.minimum_stock

        @inject(MaterialService)
            def deactivate(self) -> None:
        """
        Mark the material as inactive.
        """
        self.is_active = False

        @inject(MaterialService)
            def activate(self) -> None:
        """
        Mark the material as active.
        """
        self.is_active = True

        @inject(MaterialService)
            def to_dict(self, include_transactions: bool = False) -> dict:
        """
        Convert material to dictionary representation.

        Args:
            include_transactions (bool): Whether to include transaction history

        Returns:
            dict: Dictionary representation of the material
        """
        material_dict = super().to_dict()
        material_dict.update({'material_type': self.material_type.value,
                              'quality_grade': self.quality_grade.value, 'supplier_name':
                              self.supplier.name if self.supplier else None})
        if include_transactions:
            material_dict['transactions'] = [transaction.to_dict() for
                                             transaction in self.transactions]
        return material_dict


class MaterialTransaction(BaseModel):
    """
    Represents a transaction involving material stock.

    Attributes:
        material_id (int): Foreign key to the Material
        quantity_change (float): Amount of stock change
        transaction_type (str): Type of transaction (e.g., PURCHASE, USAGE, ADJUSTMENT)
        transaction_date (DateTime): Date of the transaction
    """
    __tablename__ = 'material_transactions'
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False)
    quantity_change = Column(Float, nullable=False)
    transaction_type = Column(String(50), nullable=False)
    transaction_date = Column(DateTime(timezone=True), server_default=func.
                              now())
    notes = Column(String(500))
    material = relationship('Material', back_populates='transactions')

    @inject(MaterialService)
        def __repr__(self) -> str:
        """
        String representation of the MaterialTransaction model.

        Returns:
            str: A string showing transaction details
        """
        return (
            f'<MaterialTransaction(material_id={self.material_id}, change={self.quantity_change}, type={self.transaction_type})>'
        )

        @inject(MaterialService)
            def to_dict(self) -> dict:
        """
        Convert material transaction to dictionary representation.

        Returns:
            dict: Dictionary representation of the material transaction
        """
        transaction_dict = super().to_dict()
        transaction_dict['material_name'
                         ] = self.material.name if self.material else None
        return transaction_dict
