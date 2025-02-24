# Path: database/models/base.py
"""
Base model definitions for the application's database models.
"""

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer
from typing import Any, Dict

class Base(DeclarativeBase):
    """
    Base declarative class for SQLAlchemy models.
    Provides common functionality for all database models.
    """
    pass

class BaseModel:
    """
    Mixin class providing common model functionality.
    """
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    def to_dict(self, exclude_fields: list[str] = None) -> Dict[str, Any]:
        """
        Convert model instance to a dictionary.

        Args:
            exclude_fields (list[str], optional): Fields to exclude from the dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the model.
        """
        exclude_fields = exclude_fields or []
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if column.name not in exclude_fields
        }

    def __repr__(self) -> str:
        """
        Provide a string representation of the model.

        Returns:
            str: String representation including class name and primary key.
        """
        pk_value = getattr(self, 'id', None)
        return f"<{self.__class__.__name__}(id={pk_value})>"