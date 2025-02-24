from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/database/models/product.py

Product model for the database.
"""


class Product(Base, BaseModel):
    """
    Product entity representing items that can be sold or used in projects.

    This class defines the product data model and provides methods for product management.
    """
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    sku = Column(String(50), unique=True, nullable=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    cost_price = Column(Float, nullable=False, default=0.0)
    stock_quantity = Column(Integer, default=0)
    minimum_stock = Column(Integer, default=0)
    reorder_point = Column(Integer, default=5)
    material_type = Column(String(50), nullable=True)
    weight = Column(Float, nullable=True)
    dimensions = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True)
    storage_id = Column(Integer, ForeignKey('storage.id'), nullable=True)
    supplier = relationship('Supplier', back_populates='products')
    storage = relationship('Storage', back_populates='products')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow)

        @inject(MaterialService)
        def __init__(self, name: str, price: float, cost_price: float,
        description: Optional[str]=None, sku: Optional[str]=None,
        material_type: Optional[str]=None) ->None:
        """
        Initialize a new Product instance.

        Args:
            name: The name of the product.
            price: The selling price of the product.
            cost_price: The cost price of the product.
            description: A description of the product.
            sku: The stock keeping unit code.
            material_type: The type of material used in the product.
        """
        self.name = name
        self.price = price
        self.cost_price = cost_price
        self.description = description
        self.sku = sku
        self.material_type = material_type
        self.stock_quantity = 0
        self.is_active = True
        self.is_featured = False

        @inject(MaterialService)
        def __repr__(self) ->str:
        """
        Get a string representation of the product.

        Returns:
            A string representation of the product.
        """
        return (
            f'<Product id={self.id}, name={self.name}, sku={self.sku}, stock={self.stock_quantity}>'
            )

        @inject(MaterialService)
        def update_stock(self, quantity_change: int, transaction_type: str=
        'manual', notes: Optional[str]=None) ->None:
        """
        Update the product stock quantity.

        Args:
            quantity_change: The amount to change the stock by (positive or negative).
            transaction_type: The type of transaction causing the stock change.
            notes: Optional notes about the transaction.

        Raises:
            ValueError: If the resulting stock would be negative.
        """
        new_quantity = self.stock_quantity + quantity_change
        if new_quantity < 0:
            raise ValueError(
                f'Cannot reduce stock below 0. Current stock: {self.stock_quantity}, Requested change: {quantity_change}'
                )
        self.stock_quantity = new_quantity
        self.updated_at = datetime.datetime.utcnow()

        @inject(MaterialService)
        def is_low_stock(self) ->bool:
        """
        Check if the product stock is below the reorder point.

        Returns:
            True if the stock is below the reorder point, False otherwise.
        """
        return self.stock_quantity <= self.reorder_point

        @inject(MaterialService)
        def calculate_profit_margin(self) ->float:
        """
        Calculate the profit margin percentage for this product.

        Returns:
            The profit margin as a percentage.
        """
        if self.price == 0:
            return 0
        profit = self.price - self.cost_price
        margin = profit / self.price * 100
        return round(margin, 2)

        @inject(MaterialService)
        def activate(self) ->None:
        """Activate this product."""
        self.is_active = True
        self.updated_at = datetime.datetime.utcnow()

        @inject(MaterialService)
        def deactivate(self) ->None:
        """Deactivate this product."""
        self.is_active = False
        self.updated_at = datetime.datetime.utcnow()

        @inject(MaterialService)
        def to_dict(self, include_details: bool=False) ->Dict[str, Any]:
        """
        Convert the product instance to a dictionary.

        Args:
            include_details: Whether to include related entities and detailed information.

        Returns:
            A dictionary representation of the product.
        """
        product_dict = {'id': self.id, 'name': self.name, 'sku': self.sku,
            'description': self.description, 'price': self.price,
            'cost_price': self.cost_price, 'stock_quantity': self.
            stock_quantity, 'minimum_stock': self.minimum_stock,
            'reorder_point': self.reorder_point, 'material_type': self.
            material_type, 'weight': self.weight, 'dimensions': self.
            dimensions, 'is_active': self.is_active, 'is_featured': self.
            is_featured, 'profit_margin': self.calculate_profit_margin(),
            'created_at': self.created_at.isoformat() if self.created_at else
            None, 'updated_at': self.updated_at.isoformat() if self.
            updated_at else None}
        if include_details:
            if self.supplier:
                product_dict['supplier'] = {'id': self.supplier.id, 'name':
                    self.supplier.name}
            if self.storage:
                product_dict['storage'] = {'id': self.storage.id, 'name':
                    self.storage.name, 'location': self.storage.location}
        return product_dict
