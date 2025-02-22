# Path: database/sqlalchemy/base.py
from sqlalchemy.orm import declarative_base, DeclarativeMeta
from sqlalchemy.ext.declarative import declared_attr
import re


class CustomBase:
    """
    Custom base class for SQLAlchemy models with additional utility methods.

    Provides:
    - Automatic table name generation
    - Consistent repr method
    - Conversion to dictionary
    """

    @declared_attr
    def __tablename__(cls):
        """
        Automatically generate table name from class name.
        Converts from CamelCase to snake_case.

        Example:
        InventoryItem -> inventory_item
        """
        # Convert CamelCase to snake_case
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def __repr__(self):
        """
        Provide a string representation of the model.

        Returns:
            str: A string showing the class name and primary key value
        """
        # Try to find primary key column
        pk_cols = [col for col in self.__table__.columns if col.primary_key]

        if pk_cols:
            pk_values = [f"{col.name}={getattr(self, col.name)}" for col in pk_cols]
            return f"<{self.__class__.__name__} {', '.join(pk_values)}>"

        return f"<{self.__class__.__name__} at {hex(id(self))}>"

    def to_dict(self):
        """
        Convert model instance to a dictionary.

        Returns:
            dict: A dictionary representation of the model
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


# Create the declarative base with our custom base class
Base: DeclarativeMeta = declarative_base(cls=CustomBase)