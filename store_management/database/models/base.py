# database/base.py

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeMeta
from typing import Dict, Any

# Create the declarative base
Base = declarative_base()


class BaseModel(Base):
    """
    Base model class that all model classes should inherit from.
    Provides common functionality for all models.
    """
    __abstract__ = True

    def __repr__(self) -> str:
        """Return a string representation of the model."""
        return f"<{self.__class__.__name__}(id={getattr(self, 'id', None)})>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model instance to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {column.name: getattr(self, column.name)
                for column in self.__table__.columns}