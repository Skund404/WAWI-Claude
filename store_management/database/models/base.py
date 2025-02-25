# database/models/base.py
"""
Base model classes for SQLAlchemy ORM models.

This module defines the Base class that all SQLAlchemy models should inherit from,
as well as common functionality through the BaseModel class.
"""

from typing import Any, Dict, Optional
from sqlalchemy.orm import declarative_base, DeclarativeMeta
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy import create_engine, MetaData
from sqlalchemy.sql import func

# Define naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Create metadata with naming convention
metadata = MetaData(naming_convention=convention)

# Create base class for declarative models
Base = declarative_base(metadata=metadata)


class BaseModel:
    """
    Base model providing common functionality for all SQLAlchemy models.

    Attributes:
        id (int): Primary key for the model.
        created_at (DateTime): Timestamp of model creation.
        updated_at (DateTime): Timestamp of last model update.
    """
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        """
        Default string representation of the model.

        Returns:
            str: String representation including class name and ID.
        """
        return f"<{self.__class__.__name__} id={self.id}>"

    def to_dict(self, exclude: list = None) -> Dict[str, Any]:
        """
        Convert model instance to a dictionary.

        Args:
            exclude (list, optional): List of attributes to exclude from dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the model.
        """
        if exclude is None:
            exclude = []

        result = {}
        for key in self.__mapper__.c.keys():
            if key not in exclude:
                result[key] = getattr(self, key)
        return result

    def update(self, **kwargs) -> 'BaseModel':
        """
        Update model attributes.

        Args:
            **kwargs: Keyword arguments representing attributes to update.

        Returns:
            BaseModel: Updated instance.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self