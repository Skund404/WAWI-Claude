#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: fixed_standalone_model_test.py

"""
Completely standalone test suite for leatherworking database models.
This file contains both the test models and the test runner.
"""

import unittest
from datetime import datetime
import enum
import sys
import os

# Import SQLAlchemy components for SQLAlchemy 1.x
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Text, DateTime,
    Boolean, ForeignKey, Enum, Table, inspect, MetaData, JSON, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session

print("SQLAlchemy imported successfully")

# Create a base class for mock models
Base = declarative_base()
metadata = MetaData()

print("Base declarative base created")


# Define enumerations for mock models
class SaleStatus(enum.Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PaymentStatus(enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class PurchaseStatus(enum.Enum):
    DRAFT = "DRAFT"
    ORDERED = "ORDERED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"


class CustomerStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    POTENTIAL = "POTENTIAL"


class CustomerTier(enum.Enum):
    NEW = "NEW"
    STANDARD = "STANDARD"
    PREMIUM = "PREMIUM"
    VIP = "VIP"


class CustomerSource(enum.Enum):
    WEBSITE = "WEBSITE"
    REFERRAL = "REFERRAL"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    OTHER = "OTHER"


class InventoryStatus(enum.Enum):
    IN_STOCK = "IN_STOCK"
    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    ON_ORDER = "ON_ORDER"


class LeatherType(enum.Enum):
    VEGETABLE_TANNED = "VEGETABLE_TANNED"
    CHROME_TANNED = "CHROME_TANNED"
    FULL_GRAIN = "FULL_GRAIN"
    TOP_GRAIN = "TOP_GRAIN"


class HardwareType(enum.Enum):
    BUCKLE = "BUCKLE"
    SNAP = "SNAP"
    RIVET = "RIVET"
    MAGNETIC_CLOSURE = "MAGNETIC_CLOSURE"


class HardwareMaterial(enum.Enum):
    BRASS = "BRASS"
    STEEL = "STEEL"
    NICKEL = "NICKEL"


class HardwareFinish(enum.Enum):
    POLISHED = "POLISHED"
    BRUSHED = "BRUSHED"
    ANTIQUE = "ANTIQUE"


class ProjectType(enum.Enum):
    WALLET = "WALLET"
    BELT = "BELT"
    BAG = "BAG"
    CUSTOM = "CUSTOM"


class ProjectStatus(enum.Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class SkillLevel(enum.Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class ComponentType(enum.Enum):
    LEATHER = "LEATHER"
    HARDWARE = "HARDWARE"
    THREAD = "THREAD"
    LINING = "LINING"


class SupplierStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class MeasurementUnit(enum.Enum):
    PIECE = "PIECE"
    METER = "METER"
    SQUARE_METER = "SQUARE_METER"
    SQUARE_FOOT = "SQUARE_FOOT"


class QualityGrade(enum.Enum):
    PREMIUM = "PREMIUM"
    STANDARD = "STANDARD"
    ECONOMY = "ECONOMY"


class PickingListStatus(enum.Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class ToolListStatus(enum.Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"


print("Enums defined successfully")

# Define relationship tables for mock models
pattern_component_table = Table(
    'pattern_component',
    Base.metadata,
    Column('pattern_id', Integer, ForeignKey('patterns.id'), primary_key=True),
    Column('component_id', Integer, ForeignKey('components.id'), primary_key=True)
)

product_pattern_table = Table(
    'product_pattern',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True),
    Column('pattern_id', Integer, ForeignKey('patterns.id'), primary_key=True)
)

print("Relationship tables defined successfully")


# Define mixins for mock models
class TimestampMixin:
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)


class CostingMixin:
    cost_price = Column(Float, nullable=True)


print("Mixins defined successfully")


# Define mock models based on the ER diagram
class Customer(Base, TimestampMixin):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    status = Column(Enum(CustomerStatus), default=CustomerStatus.ACTIVE)
    tier = Column(Enum(CustomerTier), default=CustomerTier.STANDARD)
    source = Column(Enum(CustomerSource), nullable=True)
    notes = Column(Text, nullable=True)
    is_business = Column(Boolean, nullable=False, default=False)

    # Relationships
    sales = relationship("Sales", back_populates="customer")

    def validate(self):
        if not self.name:
            raise ValueError("Customer name is required")


class Supplier(Base, TimestampMixin):
    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    status = Column(Enum(SupplierStatus), default=SupplierStatus.ACTIVE)

    # Relationships
    materials = relationship("Material", back_populates="supplier")
    purchases = relationship("Purchase", back_populates="supplier")

    def validate(self):
        if not self.name:
            raise ValueError("Supplier name is required")


class Material(Base, TimestampMixin, CostingMixin):
    __tablename__ = 'materials'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    material_type = Column(String(50), nullable=False)
    description = Column(String(500), nullable=True)
    unit = Column(Enum(MeasurementUnit), nullable=True)
    quality = Column(Enum(QualityGrade), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="materials")
    component_materials = relationship("ComponentMaterial", back_populates="material")

    # Fixed relationship with explicit foreign_keys
    inventory = relationship(
        "Inventory",
        primaryjoin="and_(Material.id==Inventory.item_id, Inventory.item_type=='material')",
        foreign_keys="[Inventory.item_id]",
        uselist=False,
        viewonly=True  # Make this relationship read-only
    )

    __mapper_args__ = {
        'polymorphic_on': material_type,
        'polymorphic_identity': 'generic'
    }

    def validate(self):
        if not self.name:
            raise ValueError("Material name is required")


print("Basic models defined successfully")


class Leather(Material):
    leather_thickness = Column(Float, nullable=True)  # Renamed to avoid conflicts
    area = Column(Float, nullable=True)
    leather_color = Column(String(50), nullable=True)  # Renamed to avoid conflicts
    hide_size = Column(String(50), nullable=True)
    leather_type = Column(Enum(LeatherType), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'leather'
    }

    def validate(self):
        super().validate()
        # Add leather-specific validation here


class Hardware(Material):
    hardware_type = Column(Enum(HardwareType), nullable=True)
    hardware_material = Column(Enum(HardwareMaterial), nullable=True)
    finish = Column(Enum(HardwareFinish), nullable=True)
    dimensions = Column(String(100), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'hardware'
    }


class Thread(Material):
    thread_thickness = Column(Float, nullable=True)  # Renamed to avoid conflicts
    thread_color = Column(String(50), nullable=True)  # Renamed to avoid conflicts
    material_composition = Column(String(100), nullable=True)
    length = Column(Float, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'thread'
    }


print("Material subtypes defined successfully")


class Component(Base, TimestampMixin):
    __tablename__ = 'components'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    component_type = Column(Enum(ComponentType), nullable=False)
    attributes = Column(JSON, nullable=True)

    # Relationships
    component_materials = relationship("ComponentMaterial", back_populates="component")
    materials = relationship("Material", secondary="component_materials",
                             viewonly=True)
    patterns = relationship("Pattern", secondary=pattern_component_table,
                            back_populates="components")
    project_components = relationship("ProjectComponent", back_populates="component")

    def validate(self):
        if not self.name:
            raise ValueError("Component name is required")
        if not self.component_type:
            raise ValueError("Component type is required")


class ComponentMaterial(Base, TimestampMixin):
    __tablename__ = 'component_materials'

    id = Column(Integer, primary_key=True, autoincrement=True)
    component_id = Column(Integer, ForeignKey('components.id'), nullable=False)
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False)
    quantity = Column(Float, nullable=True)

    # Relationships
    component = relationship("Component", back_populates="component_materials")
    material = relationship("Material", back_populates="component_materials")

    def validate(self):
        if not self.component_id:
            raise ValueError("Component ID is required")
        if not self.material_id:
            raise ValueError("Material ID is required")


class Pattern(Base, TimestampMixin):
    __tablename__ = 'patterns'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    skill_level = Column(Enum(SkillLevel), nullable=False)
    instructions = Column(JSON, nullable=True)

    # Relationships
    components = relationship("Component", secondary=pattern_component_table,
                              back_populates="patterns")
    products = relationship("Product", secondary=product_pattern_table,
                            back_populates="patterns")

    def validate(self):
        if not self.name:
            raise ValueError("Pattern name is required")
        if not self.skill_level:
            raise ValueError("Skill level is required")


class Product(Base, TimestampMixin, CostingMixin):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    price = Column(Float, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    patterns = relationship("Pattern", secondary=product_pattern_table,
                            back_populates="products")
    sales_items = relationship("SalesItem", back_populates="product")
    # Fixed relationship with explicit foreign_keys
    inventory = relationship(
        "Inventory",
        primaryjoin="and_(Product.id==Inventory.item_id, Inventory.item_type=='product')",
        foreign_keys="[Inventory.item_id]",
        overlaps="inventory",  # This is exactly what the warning suggests
        uselist=False
    )
    def validate(self):
        if not self.name:
            raise ValueError("Product name is required")
        if not self.price:
            raise ValueError("Product price is required")
        if self.price <= 0:
            raise ValueError("Product price must be positive")


class Inventory(Base, TimestampMixin):
    __tablename__ = 'inventories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_type = Column(String(50), nullable=False)
    item_id = Column(Integer, nullable=False)
    quantity = Column(Float, nullable=False, default=0)
    status = Column(Enum(InventoryStatus), nullable=False)
    storage_location = Column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint('item_type', 'item_id', name='uix_inventory_item'),
    )

    def validate(self):
        if not self.item_type:
            raise ValueError("Item type is required")
        if not self.item_id:
            raise ValueError("Item ID is required")
        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative")

    def update_quantity(self, change):
        """Update inventory quantity and status."""
        self.quantity += change

        # Update status based on new quantity
        if self.quantity <= 0:
            self.status = InventoryStatus.OUT_OF_STOCK
        elif self.quantity <= 10:  # Arbitrary threshold
            self.status = InventoryStatus.LOW_STOCK
        else:
            self.status = InventoryStatus.IN_STOCK


class Sales(Base, TimestampMixin, CostingMixin):
    __tablename__ = 'sales'

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    total_amount = Column(Float, nullable=False, default=0.0)
    status = Column(Enum(SaleStatus), nullable=False, default=SaleStatus.DRAFT)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    notes = Column(Text, nullable=True)

    # Payment tracking
    amount_paid = Column(Float, nullable=False, default=0.0)
    payment_date = Column(DateTime, nullable=True)

    # Shipping information
    shipping_address = Column(String(500), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    shipped_date = Column(DateTime, nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="sales")
    items = relationship("SalesItem", back_populates="sale")
    projects = relationship("Project", back_populates="sale")
    picking_lists = relationship("PickingList", back_populates="sale")

    def validate(self):
        if self.total_amount < 0:
            raise ValueError("Total amount cannot be negative")

    def update_total_amount(self):
        """Recalculate the total amount based on the linked sales items."""
        if not hasattr(self, 'items') or not self.items:
            self.total_amount = 0.0
            return

        self.total_amount = sum(item.price * item.quantity for item in self.items)


class SalesItem(Base, TimestampMixin):
    __tablename__ = 'sales_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sales_id = Column(Integer, ForeignKey('sales.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    # Relationships
    sale = relationship("Sales", back_populates="items")
    product = relationship("Product", back_populates="sales_items")

    def validate(self):
        if not self.sales_id:
            raise ValueError("Sales ID is required")
        if not self.product_id:
            raise ValueError("Product ID is required")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.price < 0:
            raise ValueError("Price cannot be negative")


class Purchase(Base, TimestampMixin):
    __tablename__ = 'purchases'

    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    total_amount = Column(Float, nullable=False, default=0.0)
    status = Column(Enum(PurchaseStatus), default=PurchaseStatus.DRAFT)
    notes = Column(Text, nullable=True)

    # Order tracking
    order_date = Column(DateTime, nullable=True)
    expected_delivery = Column(DateTime, nullable=True)
    delivery_date = Column(DateTime, nullable=True)

    # Reference information
    purchase_order_number = Column(String(100), nullable=True)
    invoice_number = Column(String(100), nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="purchases")
    items = relationship("PurchaseItem", back_populates="purchase")

    def validate(self):
        if not self.supplier_id:
            raise ValueError("Supplier ID is required")
        if self.total_amount < 0:
            raise ValueError("Total amount cannot be negative")


class PurchaseItem(Base, TimestampMixin):
    __tablename__ = 'purchase_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_id = Column(Integer, ForeignKey('purchases.id'), nullable=False)
    item_type = Column(String(50), nullable=False)
    item_id = Column(Integer, nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    received_quantity = Column(Float, nullable=False, default=0.0)

    # Relationships
    purchase = relationship("Purchase", back_populates="items")
    # Add relationship with correct foreign_keys parameter
    material = relationship(
        "Material",
        primaryjoin="and_(PurchaseItem.item_id==Material.id, PurchaseItem.item_type=='material')",
        foreign_keys="[PurchaseItem.item_id]",
        viewonly=True
    )

    def validate(self):
        if not self.purchase_id:
            raise ValueError("Purchase ID is required")
        if not self.item_type:
            raise ValueError("Item type is required")
        if not self.item_id:
            raise ValueError("Item ID is required")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.price < 0:
            raise ValueError("Price cannot be negative")
        if self.received_quantity < 0:
            raise ValueError("Received quantity cannot be negative")
        if self.received_quantity > self.quantity:
            raise ValueError("Received quantity cannot exceed ordered quantity")

    def receive(self, quantity):
        """Record receipt of purchased items."""
        if quantity <= 0:
            raise ValueError("Received quantity must be positive")

        if self.received_quantity + quantity > self.quantity:
            raise ValueError("Received quantity cannot exceed ordered quantity")

        self.received_quantity += quantity


class Project(Base, TimestampMixin):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    type = Column(Enum(ProjectType), nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PLANNED)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    sales_id = Column(Integer, ForeignKey('sales.id'), nullable=True)

    # Relationships
    sale = relationship("Sales", back_populates="projects")
    project_components = relationship("ProjectComponent", back_populates="project")
    tool_lists = relationship("ToolList", back_populates="project")

    def validate(self):
        if not self.name:
            raise ValueError("Project name is required")
        if not self.type:
            raise ValueError("Project type is required")

    def update_status(self, new_status):
        """Update the project status and related dates."""
        old_status = self.status
        self.status = new_status

        # Update related dates based on status
        if (new_status == ProjectStatus.IN_PROGRESS and not self.start_date):
            self.start_date = datetime.now()
        elif (new_status == ProjectStatus.COMPLETED and not self.end_date):
            self.end_date = datetime.now()


class ProjectComponent(Base, TimestampMixin):
    __tablename__ = 'project_components'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    component_id = Column(Integer, ForeignKey('components.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    completed_quantity = Column(Integer, nullable=False, default=0)

    # Relationships
    project = relationship("Project", back_populates="project_components")
    component = relationship("Component", back_populates="project_components")

    def validate(self):
        if not self.project_id:
            raise ValueError("Project ID is required")
        if not self.component_id:
            raise ValueError("Component ID is required")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.completed_quantity < 0:
            raise ValueError("Completed quantity cannot be negative")
        if self.completed_quantity > self.quantity:
            raise ValueError("Completed quantity cannot exceed total quantity")

    def update_completion(self, amount):
        """Update completion status."""
        if amount <= 0:
            raise ValueError("Completion amount must be positive")

        if self.completed_quantity + amount > self.quantity:
            raise ValueError("Cannot complete more than the total quantity")

        self.completed_quantity += amount


class PickingList(Base, TimestampMixin):
    __tablename__ = 'picking_lists'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sales_id = Column(Integer, ForeignKey('sales.id'), nullable=True)
    status = Column(Enum(PickingListStatus), default=PickingListStatus.DRAFT)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    sale = relationship("Sales", back_populates="picking_lists")
    items = relationship("PickingListItem", back_populates="picking_list")

    def validate(self):
        pass  # No specific validations required

    def is_complete(self):
        """Check if all items have been picked."""
        if not self.items:
            return False

        return all(item.quantity_picked >= item.quantity_ordered for item in self.items)

    def update_status(self, new_status):
        """Update the status and related fields."""
        self.status = new_status

        if new_status == PickingListStatus.COMPLETED:
            self.completed_at = datetime.now()


class PickingListItem(Base, TimestampMixin):
    __tablename__ = 'picking_list_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    picking_list_id = Column(Integer, ForeignKey('picking_lists.id'), nullable=False)
    component_id = Column(Integer, ForeignKey('components.id'), nullable=True)
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=True)
    quantity_ordered = Column(Integer, nullable=False)
    quantity_picked = Column(Integer, nullable=False, default=0)

    # Relationships
    picking_list = relationship("PickingList", back_populates="items")
    component = relationship("Component", foreign_keys=[component_id])
    material = relationship("Material", foreign_keys=[material_id])

    def validate(self):
        if not self.picking_list_id:
            raise ValueError("Picking list ID is required")
        if not (self.component_id or self.material_id):
            raise ValueError("Either component ID or material ID is required")
        if self.quantity_ordered <= 0:
            raise ValueError("Quantity ordered must be positive")
        if self.quantity_picked < 0:
            raise ValueError("Quantity picked cannot be negative")

    def is_fully_picked(self):
        """Check if the item has been fully picked."""
        return self.quantity_picked >= self.quantity_ordered


class ToolList(Base, TimestampMixin):
    __tablename__ = 'tool_lists'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    status = Column(Enum(ToolListStatus), default=ToolListStatus.DRAFT)
    notes = Column(Text, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="tool_lists")
    items = relationship("ToolListItem", back_populates="tool_list")

    def validate(self):
        if not self.project_id:
            raise ValueError("Project ID is required")


class ToolListItem(Base, TimestampMixin):
    __tablename__ = 'tool_list_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_list_id = Column(Integer, ForeignKey('tool_lists.id'), nullable=False)
    tool_id = Column(Integer, nullable=False)  # No foreign key since we're not creating a Tool table for simplicity
    quantity = Column(Integer, nullable=False, default=1)

    # Relationships
    tool_list = relationship("ToolList", back_populates="items")

    def validate(self):
        if not self.tool_list_id:
            raise ValueError("Tool list ID is required")
        if not self.tool_id:
            raise ValueError("Tool ID is required")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")


print("All models defined successfully")


# Define test classes
class TestDBSetup(unittest.TestCase):
    """Test database setup and basic model operations."""

    @classmethod
    def setUpClass(cls):
        """Create an in-memory SQLite database for testing."""
        cls.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)
        cls.session = cls.Session()

    @classmethod
    def tearDownClass(cls):
        """Close the session and drop all tables."""
        cls.session.close()
        Base.metadata.drop_all(cls.engine)

    def test_base_tables_exist(self):
        """Test that all tables defined in the models exist in the database."""
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()

        expected_tables = [
            'customers', 'suppliers', 'materials', 'components',
            'component_materials', 'patterns', 'products', 'inventories',
            'sales', 'sales_items', 'purchases', 'purchase_items',
            'projects', 'project_components', 'picking_lists',
            'picking_list_items', 'tool_lists', 'tool_list_items'
        ]

        for table in expected_tables:
            self.assertIn(table, tables, f"Table {table} should exist in the database")

    def test_mixins(self):
        """Test that mixins add the expected columns."""
        inspector = inspect(self.engine)

        # Test TimestampMixin
        sales_columns = [col['name'] for col in inspector.get_columns('sales')]
        self.assertIn('created_at', sales_columns, "TimestampMixin should add created_at column")
        self.assertIn('updated_at', sales_columns, "TimestampMixin should add updated_at column")

        # Test CostingMixin
        material_columns = [col['name'] for col in inspector.get_columns('materials')]
        self.assertIn('cost_price', material_columns, "CostingMixin should add cost_price column")


class TestCustomerModel(unittest.TestCase):
    """Test the Customer model."""

    @classmethod
    def setUpClass(cls):
        """Create an in-memory SQLite database for testing."""
        cls.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)
        cls.session = cls.Session()

    @classmethod
    def tearDownClass(cls):
        """Close the session and drop all tables."""
        cls.session.close()
        Base.metadata.drop_all(cls.engine)

    def test_customer_create(self):
        """Test creating a customer with valid data."""
        customer = Customer(
            name="John Doe",
            email="john.doe@example.com",
            phone="123-456-7890",
            address="123 Main St, Anytown, USA",
            status=CustomerStatus.ACTIVE,
            tier=CustomerTier.STANDARD,
            source=CustomerSource.WEBSITE
        )

        self.session.add(customer)
        self.session.commit()

        saved_customer = self.session.query(Customer).filter_by(name="John Doe").first()
        self.assertIsNotNone(saved_customer)
        self.assertEqual(saved_customer.email, "john.doe@example.com")
        self.assertEqual(saved_customer.status, CustomerStatus.ACTIVE)

    def test_customer_validation(self):
        """Test customer validation."""
        # Missing required field 'name'
        with self.assertRaises(ValueError):
            customer = Customer(
                email="invalid@example.com",
                status=CustomerStatus.ACTIVE
            )
            customer.validate()

    def test_customer_relationships(self):
        """Test customer relationships."""
        customer = Customer(
            name="Jane Smith",
            email="jane.smith@example.com",
            status=CustomerStatus.ACTIVE
        )
        self.session.add(customer)
        self.session.commit()

        # Create a sale for this customer
        sale = Sales(
            customer_id=customer.id,
            total_amount=100.0,
            status=SaleStatus.CONFIRMED,
            payment_status=PaymentStatus.PENDING
        )
        self.session.add(sale)
        self.session.commit()

        # Test the relationship
        saved_customer = self.session.query(Customer).filter_by(name="Jane Smith").first()
        self.assertEqual(len(saved_customer.sales), 1)
        self.assertEqual(saved_customer.sales[0].total_amount, 100.0)


class TestMaterialModels(unittest.TestCase):
    """Test the Material models including subclasses."""

    @classmethod
    def setUpClass(cls):
        """Create an in-memory SQLite database for testing."""
        cls.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)
        cls.session = cls.Session()

        # Create a supplier for materials
        cls.supplier = Supplier(
            name="Materials R Us",
            contact_email="contact@materialsrus.com",
            status=SupplierStatus.ACTIVE
        )
        cls.session.add(cls.supplier)
        cls.session.commit()

    @classmethod
    def tearDownClass(cls):
        """Close the session and drop all tables."""
        cls.session.close()
        Base.metadata.drop_all(cls.engine)

    def test_leather_create(self):
        """Test creating a leather material."""
        leather = Leather(
            name="Premium Veg-Tan",
            leather_type=LeatherType.VEGETABLE_TANNED,
            leather_thickness=2.0,  # Using the renamed column
            area=12.5,
            quality=QualityGrade.PREMIUM,
            supplier_id=self.supplier.id,
            cost_price=120.0,
            leather_color="Natural",  # Using the renamed column
            hide_size="Large"
        )

        self.session.add(leather)
        self.session.commit()

        saved_leather = self.session.query(Leather).filter_by(name="Premium Veg-Tan").first()
        self.assertIsNotNone(saved_leather)
        self.assertEqual(saved_leather.leather_type, LeatherType.VEGETABLE_TANNED)
        self.assertEqual(saved_leather.leather_thickness, 2.0)
        self.assertEqual(saved_leather.material_type, "leather")  # Should be set by polymorphic identity

    def test_thread_create(self):
        """Test creating a thread material."""
        thread = Thread(
            name="Waxed Linen Thread",
            thread_thickness=1.0,  # Using the renamed column
            thread_color="Black",  # Using the renamed column
            material_composition="Linen",
            quality=QualityGrade.PREMIUM,
            supplier_id=self.supplier.id,
            cost_price=15.0,
            length=50.0
        )

        self.session.add(thread)
        self.session.commit()

        saved_thread = self.session.query(Thread).filter_by(name="Waxed Linen Thread").first()
        self.assertIsNotNone(saved_thread)
        self.assertEqual(saved_thread.thread_color, "Black")
        self.assertEqual(saved_thread.thread_thickness, 1.0)
        self.assertEqual(saved_thread.material_type, "thread")


# Only run a basic test for the standalone version to keep it simple and focused
if __name__ == '__main__':
    print("Running standalone model tests...")

    # Create a test suite with the basic tests
    test_suite = unittest.TestSuite()
    test_loader = unittest.TestLoader()  # Use TestLoader instead of deprecated makeSuite
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestDBSetup))
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestCustomerModel))
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestMaterialModels))

    # Create test runner
    test_runner = unittest.TextTestRunner(verbosity=2)

    # Run the tests
    result = test_runner.run(test_suite)

    # Set exit code based on test result
    sys.exit(not result.wasSuccessful())