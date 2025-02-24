from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/database/models/storage.py

Storage model for the database.
"""


class Storage(Base, BaseModel):
    pass
"""
Storage entity representing physical storage locations for inventory.

This class defines the storage location data model and provides methods for storage management.
"""
__tablename__ = 'storage'
id = Column(Integer, primary_key=True)
name = Column(String(100), nullable=False, index=True)
location = Column(String(255), nullable=True)
capacity = Column(Float, default=0.0)
current_occupancy = Column(Float, default=0.0)
type = Column(String(50), nullable=True)
description = Column(Text, nullable=True)
status = Column(String(20), default='Active')
width = Column(Float, nullable=True)
height = Column(Float, nullable=True)
depth = Column(Float, nullable=True)
temperature_controlled = Column(Boolean, default=False)
humidity_controlled = Column(Boolean, default=False)
fire_resistant = Column(Boolean, default=False)
products = relationship('Product', back_populates='storage')

@inject(MaterialService)
def __init__(self, name: str, location: Optional[str] = None, capacity:
float = 0.0, current_occupancy: float = 0.0, type: Optional[str] = None,
description: Optional[str] = None, status: str = 'Active') -> None:
"""
Initialize a new Storage instance.

Args:
name: The name of the storage location.
location: The physical location description.
capacity: The total capacity of the storage.
current_occupancy: The current used capacity.
type: The type of storage (e.g., Warehouse, Workshop, etc.).
description: A detailed description of the storage.
status: The current status of the storage.
"""
self.name = name
self.location = location
self.capacity = capacity
self.current_occupancy = current_occupancy
self.type = type
self.description = description
self.status = status

@inject(MaterialService)
def __repr__(self) -> str:
"""
Get a string representation of the storage location.

Returns:
A string representation of the storage location.
"""
return (
f'<Storage id={self.id}, name={self.name}, status={self.status}>')

@inject(MaterialService)
def occupancy_percentage(self) -> float:
"""
Calculate the occupancy percentage of the storage.

Returns:
The occupancy percentage (0-100).
"""
if self.capacity == 0:
    pass
return 0.0
percentage = self.current_occupancy / self.capacity * 100
return round(percentage, 2)

@inject(MaterialService)
def is_full(self) -> bool:
"""
Check if the storage is full.

Returns:
True if the storage is full, False otherwise.
"""
return self.current_occupancy >= self.capacity

@inject(MaterialService)
def is_empty(self) -> bool:
"""
Check if the storage is empty.

Returns:
True if the storage is empty, False otherwise.
"""
return self.current_occupancy <= 0

@inject(MaterialService)
def available_capacity(self) -> float:
"""
Calculate the available capacity.

Returns:
The available capacity.
"""
return max(0, self.capacity - self.current_occupancy)

@inject(MaterialService)
def can_store(self, required_capacity: float) -> bool:
"""
Check if the storage can accommodate the required capacity.

Args:
required_capacity: The capacity required.

Returns:
True if the storage can accommodate the required capacity, False otherwise.
"""
return self.available_capacity() >= required_capacity
