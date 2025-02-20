# store_management/database/sqlalchemy/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean, func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from typing import List
from .base import Base

class InventoryStatus(enum.Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"

class ProductionStatus(enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TransactionType(enum.Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    PRODUCTION = "production"

class OrderStatus(enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    ORDERED = "ordered"
    RECEIVED = "received"
    CANCELLED = "cancelled"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"

class Storage(Base):
    """Storage locations for inventory items"""
    __tablename__ = 'storage'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    capacity = Column(Float, nullable=False)
    current_utilization = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    products = relationship("Product", back_populates="storage")

    def __repr__(self):
        return f"<Storage(name='{self.name}', location='{self.location}')>"

class Product(Base):
    """Products stored in inventory"""
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    sku = Column(String(50), unique=True)
    quantity = Column(Integer, default=0)
    min_quantity = Column(Integer, default=0)
    unit_price = Column(Float)
    storage_id = Column(Integer, ForeignKey('storage.id'))
    status = Column(Enum(InventoryStatus), default=InventoryStatus.IN_STOCK)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    storage = relationship("Storage", back_populates="products")
    recipe = relationship("Recipe", back_populates="product", uselist=False)

    def __repr__(self):
        return f"<Product(name='{self.name}', sku='{self.sku}')>"

class Recipe(Base):
    """Production recipes for products"""
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    product_id = Column(Integer, ForeignKey('products.id'))
    production_time = Column(Float)  # In hours
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    product = relationship("Product", back_populates="recipe")
    items = relationship("RecipeItem", back_populates="recipe")

    def __repr__(self):
        return f"<Recipe(name='{self.name}')>"

class RecipeItem(Base):
    """Items required for a recipe"""
    __tablename__ = 'recipe_items'

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recipes.id'))
    component_type = Column(String(50))  # 'product', 'part', or 'leather'
    component_id = Column(Integer)
    quantity = Column(Float)
    unit = Column(String(20))
    notes = Column(String(200))

    # Relationships
    recipe = relationship("Recipe", back_populates="items")

    def __repr__(self):
        return f"<RecipeItem(recipe_id={self.recipe_id}, component_type='{self.component_type}')>"

class Supplier(Base):
    """Suppliers of parts and materials"""
    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    contact_person = Column(String(100))
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(String(200))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    parts = relationship("Part", back_populates="supplier")
    leather = relationship("Leather", back_populates="supplier")
    orders = relationship("Order", back_populates="supplier")
    shopping_list_items = relationship("ShoppingListItem", back_populates="supplier")

    def __repr__(self):
        return f"<Supplier(name='{self.name}')>"

class Part(Base):
    """Parts used in production"""
    __tablename__ = 'parts'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    quantity = Column(Integer, default=0)
    min_quantity = Column(Integer, default=0)
    unit_price = Column(Float)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    supplier = relationship("Supplier", back_populates="parts")

    def __repr__(self):
        return f"<Part(name='{self.name}')>"

class Leather(Base):
    """Leather materials"""
    __tablename__ = 'leather'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50))
    color = Column(String(50))
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    area = Column(Float, default=0.0)  # In square feet/meters
    min_area = Column(Float, default=0.0)
    price_per_unit = Column(Float)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    supplier = relationship("Supplier", back_populates="leather")

    def __repr__(self):
        return f"<Leather(name='{self.name}', type='{self.type}')>"

class ShoppingList(Base):
    """Shopping lists for ordering supplies"""
    __tablename__ = 'shopping_lists'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    status = Column(Enum(OrderStatus), default=OrderStatus.DRAFT)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    items = relationship("ShoppingListItem", back_populates="shopping_list", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ShoppingList(name='{self.name}', status='{self.status}')>"

class ShoppingListItem(Base):
    """Items in a shopping list"""
    __tablename__ = 'shopping_list_items'

    id = Column(Integer, primary_key=True)
    shopping_list_id = Column(Integer, ForeignKey('shopping_lists.id'))
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    item_type = Column(String(50))  # 'part' or 'leather'
    item_id = Column(Integer)
    quantity = Column(Float)
    unit = Column(String(20))
    estimated_price = Column(Float)
    notes = Column(String(200))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    shopping_list = relationship("ShoppingList", back_populates="items")
    supplier = relationship("Supplier", back_populates="shopping_list_items")

    def __repr__(self):
        return f"<ShoppingListItem(list_id={self.shopping_list_id}, type='{self.item_type}')>"

class Order(Base):
    """Purchase orders"""
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    order_date = Column(DateTime, default=func.now())
    expected_delivery = Column(DateTime)
    status = Column(Enum(OrderStatus), default=OrderStatus.DRAFT)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    total_amount = Column(Float, default=0.0)
    notes = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    supplier = relationship("Supplier", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order(number='{self.order_number}', status='{self.status}')>"

class OrderItem(Base):
    """Items in a purchase order"""
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    item_type = Column(String(50))  # 'part' or 'leather'
    item_id = Column(Integer)
    quantity = Column(Float)
    unit = Column(String(20))
    unit_price = Column(Float)
    total_price = Column(Float)
    received_quantity = Column(Float, default=0)
    notes = Column(String(200))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    order = relationship("Order", back_populates="items")

    def __repr__(self):
        return f"<OrderItem(order_id={self.order_id}, type='{self.item_type}')>"