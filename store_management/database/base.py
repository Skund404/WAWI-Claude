# database/base.py
"""
Base model and declarative base for SQLAlchemy models.

Provides a foundational model class with common functionality
for all database models in the application.
"""

from typing import Dict, Any
import sqlalchemy as sa
from sqlalchemy.orm import registry, DeclarativeBase, mapped_column
from sqlalchemy.orm.decl_api import DeclarativeMeta


class BaseModel:
    """
    Base model class that all SQLAlchemy models should inherit from.

    Provides common methods and attributes for database models:
    - Automatic string representation
    - Dictionary conversion
    - Basic validation helpers
    """

    def __repr__(self) -> str:
        """
        Generate a string representation of the model instance.

        Returns:
            str: Readable representation of the model
        """
        # Get primary key value if exists
        pk = self.get_primary_key_value()

        # Use class name and primary key in representation
        pk_repr = f" {pk}" if pk is not None else ""
        return f"<{self.__class__.__name__}{pk_repr}>"

    def get_primary_key_value(self) -> Any:
        """
        Retrieve the primary key value of the model instance.

        Returns:
            Any: Value of the primary key, or None if not found
        """
        # Attempt to find the primary key column
        for column in self.__table__.columns:  # type: ignore
            if column.primary_key:
                return getattr(self, column.name, None)
        return None

    def to_dict(self, exclude_fields: list = None) -> Dict[str, Any]:
        """
        Convert the model instance to a dictionary representation.

        Args:
            exclude_fields (list, optional): List of fields to exclude from the dictionary

        Returns:
            Dict[str, Any]: Dictionary representation of the model instance
        """
        exclude_fields = exclude_fields or []

        # Convert all columns to a dictionary, excluding specified fields
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns  # type: ignore
            if column.name not in exclude_fields and
               hasattr(self, column.name)
        }

    def update(self, **kwargs):
        """
        Update model instance attributes.

        Args:
            **kwargs: Keyword arguments to update model attributes
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @classmethod
    def create(cls, **kwargs):
        """
        Class method to create a new instance with given attributes.

        Args:
            **kwargs: Keyword arguments to initialize the model

        Returns:
            BaseModel: Newly created model instance
        """
        return cls(**kwargs)


# Create a registry for declarative base
mapper_registry = registry()


# Create the declarative base using the registry
class Base(DeclarativeBase):
    """
    Declarative base for SQLAlchemy models using the registry.
    """
    registry = mapper_registry


# Export both Base and BaseModel for use in other modules
__all__ = ['Base', 'BaseModel', 'mapper_registry']