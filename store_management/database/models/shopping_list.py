

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
class ShoppingList(Base):
    """
    Model representing a shopping list.
    """
    __tablename__ = 'shopping_lists'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    status = Column(SQLAEnum(ShoppingListStatus), default=
        ShoppingListStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=
        datetime.utcnow)
    items = relationship('ShoppingListItem', back_populates='shopping_list',
        cascade='all, delete-orphan')

        @inject(MaterialService)
        def __init__(self, name: str, description: Optional[str]=None):
        """
        Initialize a shopping list.

        Args:
            name (str): Name of the shopping list
            description (Optional[str]): Description of the shopping list
        """
        self.name = name
        self.description = description

        @inject(MaterialService)
        def __repr__(self) ->str:
        """
        String representation of the shopping list.

        Returns:
            str: Shopping list representation
        """
        return (
            f"<ShoppingList(id={self.id}, name='{self.name}', status={self.status})>"
            )

        @inject(MaterialService)
        def to_dict(self) ->dict:
        """
        Convert shopping list to dictionary.

        Returns:
            dict: Dictionary representation of shopping list
        """
        return {'id': self.id, 'name': self.name, 'description': self.
            description, 'status': self.status.value, 'created_at': self.
            created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else
            None, 'items': [item.to_dict() for item in self.items]}

        @inject(MaterialService)
        def add_item(self, item) ->None:
        """
        Add an item to the shopping list.

        Args:
            item (ShoppingListItem): Item to add
        """
        self.items.append(item)
        self.updated_at = datetime.utcnow()

        @inject(MaterialService)
        def remove_item(self, item) ->None:
        """
        Remove an item from the shopping list.

        Args:
            item (ShoppingListItem): Item to remove
        """
        self.items.remove(item)
        self.updated_at = datetime.utcnow()

        @inject(MaterialService)
        def get_total_items(self) ->int:
        """
        Get total number of items in the list.

        Returns:
            int: Total number of items
        """
        return len(self.items)

        @inject(MaterialService)
        def get_pending_items(self) ->List['ShoppingListItem']:
        """
        Get items that haven't been purchased.

        Returns:
            List[ShoppingListItem]: List of pending items
        """
        return [item for item in self.items if not item.purchased]


class ShoppingListItem(Base):
    """
    Model representing an item in a shopping list.
    """
    __tablename__ = 'shopping_list_items'
    id = Column(Integer, primary_key=True)
    shopping_list_id = Column(Integer, ForeignKey('shopping_lists.id'),
        nullable=False)
    name = Column(String(100), nullable=False)
    quantity = Column(Float, default=1.0)
    unit = Column(String(20))
    priority = Column(Integer, default=0)
    notes = Column(String(500))
    purchased = Column(String(5), default=False)
    purchase_date = Column(DateTime)
    shopping_list = relationship('ShoppingList', back_populates='items')

        @inject(MaterialService)
        def __init__(self, name: str, quantity: float=1.0, unit: Optional[str]=
        None, priority: int=0, notes: Optional[str]=None):
        """
        Initialize a shopping list item.

        Args:
            name (str): Name of the item
            quantity (float): Quantity needed
            unit (Optional[str]): Unit of measurement
            priority (int): Priority level
            notes (Optional[str]): Additional notes
        """
        self.name = name
        self.quantity = quantity
        self.unit = unit
        self.priority = priority
        self.notes = notes

        @inject(MaterialService)
        def __repr__(self) ->str:
        """
        String representation of the shopping list item.

        Returns:
            str: Shopping list item representation
        """
        return (
            f"<ShoppingListItem(id={self.id}, name='{self.name}', quantity={self.quantity})>"
            )

        @inject(MaterialService)
        def to_dict(self) ->dict:
        """
        Convert shopping list item to dictionary.

        Returns:
            dict: Dictionary representation of shopping list item
        """
        return {'id': self.id, 'shopping_list_id': self.shopping_list_id,
            'name': self.name, 'quantity': self.quantity, 'unit': self.unit,
            'priority': self.priority, 'notes': self.notes, 'purchased':
            self.purchased, 'purchase_date': self.purchase_date.isoformat() if
            self.purchase_date else None}

        @inject(MaterialService)
        def mark_as_purchased(self) ->None:
        """
        Mark the item as purchased.
        """
        self.purchased = True
        self.purchase_date = datetime.utcnow()

        @inject(MaterialService)
        def update_quantity(self, new_quantity: float) ->None:
        """
        Update the quantity of the item.

        Args:
            new_quantity (float): New quantity value
        """
        self.quantity = new_quantity
