# Relative path: store_management/database/sqlalchemy/base.py

"""
Custom base module for SQLAlchemy models with common methods and representations.
"""

from typing import Dict, Any
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeMeta
from di.core import inject



Base: DeclarativeMeta = declarative_base()

class CustomBase:
    """
    Custom base mixin to add common methods to SQLAlchemy models.

    Provides a consistent __repr__ and to_dict method for all models.
    """


    def __repr__(self) -> str:
        """
        Generate a string representation of the model.

        Returns:
            str: A string representation of the model instance.
        """
        # Filter out private and callable attributes
        attrs = ', '.join(
            f'{k}={repr(v)}' 
            for k, v in self.__dict__.items() 
            if not k.startswith('_') and not callable(v)
        )
        return f'{self.__class__.__name__}({attrs})'


    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model instance to a dictionary.

        Returns:
            dict: A dictionary representation of the model instance.
        """
        # Use SQLAlchemy table columns to ensure consistent dictionary conversion
        return {
            column.name: getattr(self, column.name) 
            for column in self.__table__.columns
        }