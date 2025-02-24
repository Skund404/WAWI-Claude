# Relative path: store_management/database/models/part.py

"""
Part Model Module

Defines the Part model for storing material/inventory information.
"""

from sqlalchemy import Column, String, Float, Boolean
from sqlalchemy.orm import relationship

from .base import BaseModel
from database.sqlalchemy.core import Base


class Part(BaseModel):
    pass
"""
Represents a part or material in the inventory system.

Attributes:
name (str): Name of the part.
description (str): Detailed description of the part.
quantity (float): Current quantity in inventory.
unit (str): Unit of measurement.
is_active (bool): Whether the part is currently active in inventory.
"""
__tablename__ = 'parts'

# Specific columns for Part model
name = Column(String(255), nullable=False, unique=True, index=True)
description = Column(String(500), nullable=True)
quantity = Column(Float, default=0.0)
unit = Column(String(50), nullable=False, default='unit')
is_active = Column(Boolean, default=True)

# Optional: Relationships with other models
# Example: storage_locations = relationship("StorageLocation", back_populates="parts")

def __repr__(self):
    pass
"""
String representation of the Part model.

Returns:
str: Descriptive string of the Part instance.
"""
return (
f"<Part(id={self.id}, "
f"name='{self.name}', "
f"quantity={self.quantity} {self.unit}, "
f"active={self.is_active})>"
)

@classmethod
def create_part(
cls,
name: str,
description: str = None,
quantity: float = 0.0,
unit: str = 'unit',
is_active: bool = True,
**kwargs
) -> 'Part':
"""
Class method to create a new Part instance with validation.

Args:
name (str): Name of the part.
description (str, optional): Description of the part.
quantity (float, optional): Initial quantity. Defaults to 0.0.
unit (str, optional): Unit of measurement. Defaults to 'unit'.
is_active (bool, optional): Active status. Defaults to True.
**kwargs: Additional attributes to set.

Returns:
Part: Newly created Part instance
"""
part_data = {
'name': name,
'description': description,
'quantity': quantity,
'unit': unit,
'is_active': is_active,
**kwargs
}

return cls.create(**part_data)

def adjust_quantity(self, amount: float) -> float:
"""
Adjust the quantity of the part.

Args:
amount (float): Amount to add or subtract from current quantity.

Returns:
float: New quantity after adjustment.

Raises:
ValueError: If adjustment would result in negative quantity.
"""
new_quantity = self.quantity + amount

if new_quantity < 0:
    pass
raise ValueError(
f"Quantity adjustment would result in negative value for {self.name}")

self.quantity = new_quantity
return self.quantity

def deactivate(self) -> None:
"""
Deactivate the part.
"""
self.is_active = False

def activate(self) -> None:
"""
Activate the part.
"""
self.is_active = True
