# database/database.py
"""
Database utilities and centralized model imports.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# Create the base class for declarative models
Base = declarative_base()

# Base and common models
from database.models.base import AbstractBase, ValidationMixin, CostingMixin, TimestampMixin, TrackingMixin

# Enums
from database.models.enums import (
    CustomerStatus, SalesStatus, PaymentStatus, SupplierStatus, InventoryStatus,
    ProjectType, ProjectStatus, SkillLevel, MaterialType, LeatherType,
    HardwareType, ToolType, MeasurementUnit, QualityGrade, PurchaseStatus,
    PickingListStatus, ToolListStatus
)

# Import all models to register them with the Base class
# Previously implemented models
from database.models.storage import Storage
from database.models.customer import Customer
from database.models.supplier import Supplier
from database.models.sales import Sales
from database.models.sales_item import SalesItem
from database.models.project import Project
from database.models.product import Product
from database.models.tool import Tool
from database.models.tool_list import ToolList
from database.models.tool_list_item import ToolListItem

# Newly implemented models
from database.models.material import Material, Leather, Hardware, Supplies
from database.models.inventory import MaterialInventory, LeatherInventory, HardwareInventory, ProductInventory
from database.models.component import (
    Component, ComponentMaterial, ComponentLeather,
    ComponentHardware, ComponentTool, PatternComponent, ProjectComponent
)
# Pattern and related models
from database.models.pattern import Pattern, ProductPattern

# Picking list and related models
from database.models.picking_list import PickingList, PickingListItem

# Purchase and related models
from database.models.purchase import Purchase, PurchaseItem


def create_db_engine(url, echo=False):
    """
    Create and return a SQLAlchemy engine.

    Args:
        url (str): Database connection URL
        echo (bool): Whether to log SQL queries

    Returns:
        Engine: SQLAlchemy engine
    """
    return create_engine(url, echo=echo)


def create_session_factory(engine):
    """
    Create and return a SQLAlchemy session factory.

    Args:
        engine (Engine): SQLAlchemy engine

    Returns:
        Session: SQLAlchemy session factory
    """
    return scoped_session(sessionmaker(bind=engine))


def create_tables(engine):
    """
    Create all tables in the database.

    Args:
        engine (Engine): SQLAlchemy engine
    """
    Base.metadata.create_all(engine)


def drop_tables(engine):
    """
    Drop all tables from the database.

    Args:
        engine (Engine): SQLAlchemy engine
    """
    Base.metadata.drop_all(engine)


def get_in_memory_db():
    """
    Create an in-memory SQLite database for testing.

    Returns:
        tuple: (engine, session_factory)
    """
    engine = create_engine('sqlite:///:memory:', echo=False)
    session_factory = create_session_factory(engine)
    create_tables(engine)
    return engine, session_factory