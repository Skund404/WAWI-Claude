# database/models/order_item.py
from typing import Optional
from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from database.models.base import Base, ModelValidationError

# Forward declarations for circular imports
Order = None
Product = None

class OrderItem(Base):
    """Represents an individual item within an order."""
    __tablename__ = 'order_items'

    # Foreign key relationships
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'), nullable=False)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey('products.id'), nullable=True)

    # Item details
    item_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    discount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Product relationship
    product: Mapped[Optional['Product']] = relationship(
        'Product',
        lazy='selectin'
    )

    def __init__(self, **kwargs):
        """Initialize the OrderItem instance."""
        # Handle subtotal/line_total/total_price naming variations
        if 'subtotal' in kwargs and 'total_price' not in kwargs:
            kwargs['total_price'] = kwargs.pop('subtotal')
        elif 'line_total' in kwargs and 'total_price' not in kwargs:
            kwargs['total_price'] = kwargs.pop('line_total')

        # Calculate total_price if not provided
        if 'total_price' not in kwargs and 'quantity' in kwargs and 'unit_price' in kwargs:
            kwargs['total_price'] = kwargs['quantity'] * kwargs['unit_price'] - kwargs.get('discount', 0)

        # If product_id is provided but item_name isn't, we should try to lookup the product name
        # But for now just use a placeholder
        if 'product_id' in kwargs and 'item_name' not in kwargs:
            kwargs['item_name'] = f"Product #{kwargs['product_id']}"

        super().__init__(**kwargs)

    @property
    def subtotal(self) -> float:
        """Calculate the subtotal for this order item."""
        return self.total_price + self.discount

    @property
    def line_total(self) -> float:
        """Alias for total_price for compatibility."""
        return self.total_price


# Set up relationship later to avoid circular imports
def setup_relationships():
    global Order, Product

    # Set up Order relationship
    if Order is None:
        try:
            from database.models.order import Order as O
            Order = O

            # Set up relationship if not already set
            if not hasattr(OrderItem, 'order'):
                OrderItem.order = relationship(
                    'Order',
                    back_populates='items',
                    lazy='selectin'
                )
        except ImportError:
            logger.warning("Could not import Order")

    # Set up Product relationship
    if Product is None:
        try:
            from database.models.product import Product as P
            Product = P
            # Relationship is already defined in class attribute
        except ImportError:
            logger.warning("Could not import Product")

# Try to setup relationships immediately
setup_relationships()
