from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/database/models/supplier.py

Supplier model for the database.
"""


class Supplier(Base, BaseModel):
    """
    Supplier entity representing vendors who provide materials or products.

    This class defines the supplier data model and provides methods for supplier management.
    """
    __tablename__ = 'suppliers'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    contact_name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    tax_id = Column(String(50), nullable=True, unique=True)
    website = Column(String(255), nullable=True)
    notes = Column(String(500), nullable=True)
    rating = Column(Float, default=0.0)
    reliability_score = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    price_score = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    is_preferred = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow)
    products = relationship('Product', back_populates='supplier')

        @inject(MaterialService)
        def __init__(self, name: str, contact_name: Optional[str]=None, email:
        Optional[str]=None, phone: Optional[str]=None, address: Optional[
        str]=None, tax_id: Optional[str]=None) ->None:
        """
        Initialize a new Supplier instance.

        Args:
            name: The name of the supplier.
            contact_name: The name of the contact person at the supplier.
            email: The email address of the supplier.
            phone: The phone number of the supplier.
            address: The physical address of the supplier.
            tax_id: The tax identification number of the supplier.
        """
        self.name = name
        self.contact_name = contact_name
        self.email = email
        self.phone = phone
        self.address = address
        self.tax_id = tax_id
        self.is_active = True
        self.is_preferred = False
        self.rating = 0.0
        self.reliability_score = 0.0
        self.quality_score = 0.0
        self.price_score = 0.0

        @inject(MaterialService)
        def validate(self) ->bool:
        """
        Validate the supplier data.

        Returns:
            True if all validation checks pass, False otherwise.

        Raises:
            ValueError: If any validation check fails.
        """
        if not self.name:
            raise ValueError('Supplier name is required')
        if self.email and not self._validate_email(self.email):
            raise ValueError(f'Invalid email format: {self.email}')
        if self.phone and not self._validate_phone(self.phone):
            raise ValueError(f'Invalid phone format: {self.phone}')
        return True

        @inject(MaterialService)
        def _validate_email(self, email: str) ->bool:
        """Validate email format."""
        import re
        pattern = '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$'
        return bool(re.match(pattern, email))

        @inject(MaterialService)
        def _validate_phone(self, phone: str) ->bool:
        """Validate phone format."""
        import re
        pattern = '^[0-9+\\-() ]+$'
        return bool(re.match(pattern, phone))

        @inject(MaterialService)
        def update_rating(self, new_rating: float) ->None:
        """
        Update the supplier's rating.

        Args:
            new_rating: The new rating value (0.0 to 5.0).

        Raises:
            ValueError: If the rating is not within the valid range.
        """
        if not 0 <= new_rating <= 5:
            raise ValueError('Rating must be between 0 and 5')
        self.rating = new_rating
        self.updated_at = datetime.datetime.utcnow()

        @inject(MaterialService)
        def activate(self) ->None:
        """Activate this supplier."""
        self.is_active = True
        self.updated_at = datetime.datetime.utcnow()

        @inject(MaterialService)
        def deactivate(self) ->None:
        """Deactivate this supplier."""
        self.is_active = False
        self.updated_at = datetime.datetime.utcnow()

        @inject(MaterialService)
        def to_dict(self, exclude_fields: Optional[List[str]]=None,
        include_relationships: bool=False) ->Dict[str, Any]:
        """
        Convert the supplier instance to a dictionary.

        Args:
            exclude_fields: List of field names to exclude from the dictionary.
            include_relationships: Whether to include related entities.

        Returns:
            A dictionary representation of the supplier.
        """
        if exclude_fields is None:
            exclude_fields = []
        supplier_dict = {'id': self.id, 'name': self.name, 'contact_name':
            self.contact_name, 'email': self.email, 'phone': self.phone,
            'address': self.address, 'tax_id': self.tax_id, 'website': self
            .website, 'notes': self.notes, 'rating': self.rating,
            'reliability_score': self.reliability_score, 'quality_score':
            self.quality_score, 'price_score': self.price_score,
            'is_active': self.is_active, 'is_preferred': self.is_preferred,
            'created_at': self.created_at.isoformat() if self.created_at else
            None, 'updated_at': self.updated_at.isoformat() if self.
            updated_at else None}
        for field in exclude_fields:
            if field in supplier_dict:
                del supplier_dict[field]
        if include_relationships:
            if hasattr(self, 'products') and self.products is not None:
                supplier_dict['products'] = [product.to_dict(exclude_fields
                    =['supplier']) for product in self.products]
            if hasattr(self, 'orders') and self.orders is not None:
                supplier_dict['orders'] = [order.to_dict(exclude_fields=[
                    'supplier']) for order in self.orders]
        return supplier_dict
