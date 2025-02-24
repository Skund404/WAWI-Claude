# Path: database/models/model_metaclass.py
"""
Unified metaclass for handling complex model inheritance.
"""

from typing import Any, Dict, Type
from sqlalchemy.orm import DeclarativeBase
from abc import ABCMeta


class ModelMetaclass(DeclarativeBase.__class__, ABCMeta):
    """
    A unified metaclass that combines SQLAlchemy's DeclarativeBase
    with Python's abstract base class (ABC) metaclass.

    This metaclass resolves conflicts in multiple inheritance scenarios
    for database models with abstract interfaces.
    """

    def __new__(mcs, name: str, bases: tuple, attrs: Dict[str, Any]) -> Type:
        """
        Custom class creation method to handle complex inheritance.

        Args:
            name (str): Name of the class being created
            bases (tuple): Base classes
            attrs (Dict[str, Any]): Class attributes

        Returns:
            Type: Newly created class
        """
        # Remove potential duplicate base classes
        unique_bases = []
        for base in bases:
            if base not in unique_bases:
                unique_bases.append(base)

        # Merge attributes from all base classes
        for base in unique_bases:
            for key, value in getattr(base, '__dict__', {}).items():
                if key not in attrs:
                    attrs[key] = value

        # Create the class with unified metaclass
        return super().__new__(mcs, name, tuple(unique_bases), attrs)


class BaseModel(DeclarativeBase, metaclass=ModelMetaclass):
    """
    Base model class that uses the unified ModelMetaclass.
    Provides a foundation for all database models with robust inheritance.
    """

    @classmethod
    def __subclasshook__(cls, C: Type) -> bool:
        """
        Custom subclass hook to support interface-like behavior.

        Args:
            C (Type): Potential subclass to check

        Returns:
            bool: Whether C is considered a subclass
        """
        if cls is BaseModel:
            # Check for required methods or attributes
            if all(hasattr(C, attr) for attr in ['to_dict', 'validate']):
                return True
        return NotImplemented