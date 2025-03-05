# File: database/sqlalchemy/__init__.py
from .base import Base, CustomBase

# This can be used to create model classes
# Base = declarative_base()  # <---- REMOVE THIS LINE

__all__ = ["Base", "CustomBase"]