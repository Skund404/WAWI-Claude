# File: database/sqlalchemy/base.py
from sqlalchemy.ext.declarative import declarative_base

# Create a declarative base for SQLAlchemy models
Base = declarative_base()


class CustomBase:
    """
    Custom base mixin to add common methods to SQLAlchemy models.

    Provides a consistent __repr__ and to_dict method for all models.
    """

    def __repr__(self):
        """
        Generate a string representation of the model.

        Returns:
            str: A string representation of the model instance.
        """
        # Exclude SQLAlchemy internal attributes
        attrs = ', '.join(f"{k}={repr(v)}" for k, v in self.__dict__.items()
                          if not k.startswith('_') and not callable(v))
        return f"{self.__class__.__name__}({attrs})"

    def to_dict(self):
        """
        Convert the model instance to a dictionary.

        Returns:
            dict: A dictionary representation of the model instance.
        """
        return {column.name: getattr(self, column.name)
                for column in self.__table__.columns}