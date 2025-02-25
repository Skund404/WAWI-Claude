# database/models/model_metaclass.py
"""
Metaclass and base model configuration for SQLAlchemy ORM models.

This module provides a custom metaclass and base model class that supports
both SQLAlchemy ORM functionality and abstract base class behaviors.
"""

from abc import ABCMeta
from typing import Any, Dict, Type

from sqlalchemy.orm import DeclarativeMeta, registry, declared_attr
from sqlalchemy.ext.declarative import declarative_base


class ModelMetaclass(DeclarativeMeta, ABCMeta):
    """
    A custom metaclass that combines DeclarativeMeta and ABCMeta.

    This allows for both SQLAlchemy ORM model creation and abstract base class
    functionality, enabling interface-like behavior for model classes.
    """

    def __subclasshook__(cls, C: Type) -> bool:
        """
        Custom subclass hook to determine if a class meets the requirements of an interface.

        Args:
            C (Type): The class to check for interface compliance.

        Returns:
            bool: True if the class implements all required methods,
                  False or NotImplemented otherwise.
        """
        if cls is BaseModel:
            # Add any specific method checks here if needed
            return NotImplemented
        return NotImplemented


# Create a registry for declarative base
_mapper_registry = registry()

class BaseModel:
    """
    Base model class using the ModelMetaclass.

    This class allows for both SQLAlchemy ORM functionality and
    abstract base class behaviors. It should be used as a base
    class for models that need to implement specific interfaces.

    Attributes:
        __tablename__ (str): Automatically generated table name from the class name.
    """

    # Use the registry for declarative base
    registry = _mapper_registry
    metadata = registry.metadata

    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate table name automatically from the class name.

        Returns:
            str: Lowercase class name as the table name.
        """
        return cls.__name__.lower()

    def __init__(self, *args: Any, **kwargs: Dict[str, Any]) -> None:
        """
        Initialize the model instance.

        Args:
            *args: Positional arguments to pass to parent classes.
            **kwargs: Keyword arguments for model attributes.
        """
        # Initialize with any provided keyword arguments
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        """
        Provide a string representation of the model instance.

        Returns:
            str: A string representation including class name and primary key.
        """
        # Attempt to get primary key for more informative representation
        pk_attrs = [
            f"{col}={getattr(self, col)}"
            for col in self.__table__.primary_key.columns.keys()
            if hasattr(self, col)
        ]
        pk_str = ', '.join(pk_attrs) if pk_attrs else 'no primary key'
        return f"{self.__class__.__name__}({pk_str})"

# Create the declarative base with our custom base and metaclass
Base = declarative_base(cls=BaseModel, metaclass=ModelMetaclass)