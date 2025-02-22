# Path: database/sqlalchemy/base.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

# Create the declarative base for all models
Base = declarative_base()

class CustomBase:
    """
    Custom base class for SQLAlchemy models with additional utility methods.
    """
    id = Column(Integer, primary_key=True, autoincrement=True)

    def __repr__(self):
        """
        Provides a string representation of the model instance.

        Returns:
            str: String representation showing the class name and ID
        """
        return f"<{self.__class__.__name__}(id={self.id})>"

    def to_dict(self):
        """
        Convert model instance to a dictionary.

        Returns:
            dict: Dictionary representation of the model instance
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# Create the declarative base
Base = declarative_base(cls=CustomBase)