from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService

"""
Circular Import Resolver for Supplier Model.

Provides a mechanism to lazily load and resolve model relationships
to prevent circular import issues.
"""
if TYPE_CHECKING:
    from .product import Product
    from .sale import Sale


class SupplierModelResolver:
    """
    A resolver class to handle lazy loading of supplier-related models.

    This class provides a centralized way to manage supplier model
    relationships and prevent circular import issues.
    """
    _product_model: Optional[Any] = None
    _order_model: Optional[Any] = None

    @classmethod
    def set_product_model(cls, product_model: Any) -> None:
        """
        Set the Product model class for lazy loading.

        Args:
            product_model (Any): Product model class.
        """
        cls._product_model = product_model

    @classmethod
    def set_order_model(cls, order_model: Any) -> None:
        """
        Set the Order model class for lazy loading.

        Args:
            order_model (Any): Order model class.
        """
        cls._order_model = order_model

    @classmethod
    def get_products_relationship(cls):
        """
        Get the products relationship with lazy loading.

        Returns:
            Mapped[List[Any]]: Relationship to Product models.
        """
        if cls._product_model is None:
            from .product import Product
            cls._product_model = Product
        return relationship(cls._product_model, back_populates='supplier',
                            lazy='subquery')

    @classmethod
    def get_orders_relationship(cls):
        """
        Get the orders relationship with lazy loading.

        Returns:
            Mapped[List[Any]]: Relationship to Order models.
        """
        if cls._order_model is None:
            from .sale import Sale
            cls._order_model = Sale
        return relationship(cls._order_model, back_populates='supplier',
                            lazy='subquery')


def create_supplier_model(base_classes):
    """
    Dynamically create the Supplier model with resolved relationships.

    Args:
        base_classes (tuple): Base classes for the model.

    Returns:
        type: Dynamically created Supplier model class.
    """

    class Supplier(*base_classes):
        """
        Represents a supplier in the system with comprehensive tracking.
        """
        __tablename__ = 'suppliers'
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        name: Mapped[str] = mapped_column(String(100), nullable=False)
        contact_name: Mapped[Optional[str]] = mapped_column(String(100))
        email: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
        phone: Mapped[Optional[str]] = mapped_column(String(20))
        address: Mapped[Optional[str]] = mapped_column(String(255))
        tax_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
        rating: Mapped[float] = mapped_column(Float, default=0.0)
        is_active: Mapped[bool] = mapped_column(Boolean, default=True)
        payment_terms: Mapped[Optional[str]] = mapped_column(String(100))
        credit_limit: Mapped[Optional[float]] = mapped_column(Float)
        last_order_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
        products = SupplierModelResolver.get_products_relationship()
        orders = SupplierModelResolver.get_orders_relationship()

        @inject(MaterialService)
        def __init__(self, name: str, contact_name: Optional[str] = None,
                     email: Optional[str] = None, phone: Optional[str] = None, address:
                     Optional[str] = None, tax_id: Optional[str] = None):
            """
            Initialize a Supplier instance.

            Args:
                name (str): Name of the supplier.
                contact_name (Optional[str], optional): Primary contact person.
                email (Optional[str], optional): Supplier's contact email.
                phone (Optional[str], optional): Supplier's contact phone.
                address (Optional[str], optional): Supplier's physical address.
                tax_id (Optional[str], optional): Tax identification number.
            """
            self.name = name
            self.contact_name = contact_name
            self.email = email
            self.phone = phone
            self.address = address
            self.tax_id = tax_id
            self.rating = 0.0
            self.is_active = True
            self.credit_limit = 0.0

        @inject(MaterialService)
        def validate(self) -> bool:
            """
            Validate supplier data.

            Returns:
                bool: True if data is valid, False otherwise.
            """
            if not self.name:
                return False
            if self.email and '@' not in self.email:
                return False
            if self.phone and not self.phone.replace(' ', '').isdigit():
                return False
            return True

        @inject(MaterialService)
        def update_rating(self, new_rating: float) -> None:
            """
            Update supplier rating.

            Args:
                new_rating (float): New rating value.

            Raises:
                ValueError: If rating is out of valid range.
            """
            if not 0 <= new_rating <= 5:
                raise ValueError('Rating must be between 0 and 5')
            self.rating = new_rating

        @inject(MaterialService)
        def activate(self) -> None:
            """
            Activate the supplier.
            """
            self.is_active = True

        @inject(MaterialService)
        def deactivate(self) -> None:
            """
            Deactivate the supplier.
            """
            self.is_active = False

        @inject(MaterialService)
        def to_dict(self, exclude_fields: Optional[List[str]] = None,
                    include_relationships: bool = False) -> Dict[str, Any]:
            """
            Convert Supplier to dictionary representation.

            Args:
                exclude_fields (Optional[List[str]], optional): Fields to exclude.
                include_relationships (bool, optional): Whether to include related entities.

            Returns:
                Dict[str, Any]: Dictionary of supplier attributes.
            """
            exclude_fields = exclude_fields or []
            supplier_dict = {'id': self.id, 'name': self.name,
                             'contact_name': self.contact_name, 'email': self.email,
                             'phone': self.phone, 'address': self.address, 'tax_id':
                                 self.tax_id, 'rating': self.rating, 'is_active': self.
                    is_active, 'payment_terms': self.payment_terms,
                             'credit_limit': self.credit_limit, 'last_order_date': self.
                    last_order_date.isoformat() if self.last_order_date else None}
            for field in exclude_fields:
                supplier_dict.pop(field, None)
            if include_relationships:
                supplier_dict['products'] = [product.to_dict() for product in
                                             self.products]
                supplier_dict['orders'] = [order.to_dict() for order in
                                           self.orders]
            return supplier_dict

    return Supplier


Supplier = create_supplier_model((BaseModel, TimestampMixin, ValidationMixin))