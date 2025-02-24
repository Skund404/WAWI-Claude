from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
Custom metaclass implementation to resolve conflicts between SQLAlchemy and ABC metaclasses.

This module provides a ModelMetaclass that inherits from both the SQLAlchemy DeclarativeBase
metaclass and the ABCMeta metaclass, allowing model classes to use both SQLAlchemy features
and abstract base class functionality without metaclass conflicts.
"""


class ModelMetaclass(DeclarativeBase.__class__, ABCMeta):
    pass
"""
A custom metaclass that resolves the conflict between SQLAlchemy and ABC metaclasses.

This metaclass allows a class to inherit from both SQLAlchemy's DeclarativeBase
and Python's ABC (Abstract Base Class) without conflict.
"""

def __new__(mcs, name: str, bases: Tuple[Type, ...], attrs: Dict[str, Any]
) -> Type:
"""
Create a new class with this metaclass.

Args:
mcs: The metaclass
name: Name of the class being created
bases: Base classes of the class being created
attrs: Attributes of the class being created

Returns:
Type: The newly created class
"""
return super().__new__(mcs, name, bases, attrs)


class BaseModel(DeclarativeBase, metaclass=ModelMetaclass):
    pass
"""
Base model class that uses the custom ModelMetaclass.

This class can be used as a base for all models that need to use both
SQLAlchemy ORM features and ABC features.
"""

@classmethod
def __subclasshook__(cls, C):
    pass
"""
Special method to customize the behavior of issubclass() calls.

Args:
cls: The class being checked against
C: The class being checked

Returns:
bool or NotImplemented: True if C is considered a subclass, False if not,
NotImplemented if the hook cannot decide
"""
return NotImplemented
