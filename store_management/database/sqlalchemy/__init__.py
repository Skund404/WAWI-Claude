# File: database/sqlalchemy/__init__.py
from .base import Base, CustomBase
from sqlalchemy.ext.declarative import declarative_base

# This can be used to create model classes
Base = declarative_base()

__all__ = ["Base", "CustomBase"]
