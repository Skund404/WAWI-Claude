

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class BaseTransaction(BaseModel):
    pass
"""
Base class for all transaction models.

Provides common fields and functionality for tracking inventory changes.

Attributes:
id (int): Primary key
transaction_type (TransactionType): Type of transaction (purchase, use, etc.)
notes (str): Optional notes about the transaction
timestamp (datetime): When the transaction occurred
"""
__abstract__ = True
id = Column(Integer, primary_key=True)
transaction_type = Column(SQLEnum(TransactionType), nullable=False)
notes = Column(String(500))
timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

@inject(MaterialService)
def __init__(self, transaction_type: TransactionType, notes: Optional[
str] = None):
    pass
"""
Initialize a new transaction.

Args:
transaction_type: Type of inventory transaction
notes: Optional notes about the transaction
"""
self.transaction_type = transaction_type
self.notes = notes

@inject(MaterialService)
def __repr__(self) -> str:
"""Return string representation of the transaction."""
return (
f'<{self.__class__.__name__}(id={self.id}, type={self.transaction_type}, timestamp={self.timestamp})>'
)

@inject(MaterialService)
def to_dict(self) -> Dict[str, Any]:
"""
Convert transaction to dictionary representation.

Returns:
Dictionary containing transaction data
"""
return {'id': self.id, 'transaction_type': self.transaction_type.
name, 'notes': self.notes, 'timestamp': self.timestamp.
isoformat() if self.timestamp else None}
