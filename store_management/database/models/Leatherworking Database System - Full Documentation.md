# Leatherworking Database System - Comprehensive Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Base Models and Mixins](#base-models-and-mixins)
4. [Core Models](#core-models)
   - [Material and Subtypes](#material-and-subtypes)
   - [Component](#component)
   - [ComponentMaterial Relationship](#componentmaterial-relationship)
   - [Pattern](#pattern)
   - [Product](#product)
   - [Inventory](#inventory)
5. [Sales and Purchasing](#sales-and-purchasing)
   - [Customer](#customer)
   - [Sales and SalesItem](#sales-and-salesitem)
   - [Supplier](#supplier)
   - [Purchase and PurchaseItem](#purchase-and-purchaseitem)
6. [Project Management](#project-management)
   - [Project](#project)
   - [ProjectComponent](#projectcomponent)
   - [PickingList and PickingListItem](#pickinglist-and-pickinglistitem)
   - [ToolList and ToolListItem](#toollist-and-toollistitem)
7. [Tool Management](#tool-management)
   - [Tool](#tool)
   - [ToolMaintenance](#toolmaintenance)
   - [ToolCheckout](#toolcheckout)
8. [Relationship Tables](#relationship-tables)
9. [Enumerations](#enumerations)
10. [Validation and Error Handling](#validation-and-error-handling)
11. [Initialization and Registration](#initialization-and-registration)
12. [Common Troubleshooting](#common-troubleshooting)
13. [Database Schema Diagram](#database-schema-diagram)

## Introduction

The Leatherworking Database System is a comprehensive solution designed to manage all aspects of a custom leatherworking business. It provides functionality for inventory management, sales tracking, project planning, tool management, and more. The system is built using SQLAlchemy, a powerful Object-Relational Mapping (ORM) library for Python.

This documentation provides detailed information about each model, its attributes, relationships, validation logic, and implementation details. It is intended for developers who are maintaining or extending the system.

## System Architecture

The database system follows a modular design with clear separation of concerns:

- **Base Models and Mixins**: Provide common functionality and attributes that can be reused across multiple models
- **Core Models**: Represent the fundamental entities in the system (materials, components, patterns, products)
- **Sales and Purchasing**: Handle customer relationships, sales, suppliers, and purchasing
- **Project Management**: Track projects, components, picking lists, and tool lists
- **Tool Management**: Manage tools, maintenance, and checkouts

The system employs SQLAlchemy's ORM capabilities to abstract the underlying database operations and provide a clean, object-oriented interface.

## Base Models and Mixins

### Base

`Base` is the declarative base for all models, establishing the connection between the models and the database.

### ModelValidationError

Custom exception raised when model validation fails, providing clear error messages for debugging and user feedback.

### ValidationMixin

Provides common validation methods for models:
- `validate_length`: Validates string length against defined limits
- `validate_string_fields`: Validates string fields for length and format

### TimestampMixin

Adds timestamp columns to models:
- `created_at`: When the record was created
- `updated_at`: When the record was last updated

### CostingMixin

Adds cost-related columns to models:
- `unit_cost`: Cost per unit
- `unit_price`: Price per unit
- `markup_percentage`: Percentage markup for pricing calculations

### TrackingMixin

Adds user tracking columns:
- `created_by`: User who created the record
- `updated_by`: User who last updated the record

### ComplianceMixin

Adds compliance-related columns for record-keeping and regulatory requirements.

### AuditMixin

Adds auditing functionality to track changes to records over time.

### AbstractBase

Abstract base class that combines `Base` and `TimestampMixin`, used as the foundation for most models in the system.

## Core Models

### Material and Subtypes

The `Material` model represents raw materials used in leatherworking projects. It employs single table inheritance with `material_type` as the discriminator.

#### Material Base Class

```python
class Material(AbstractBase, ValidationMixin, CostingMixin):
    """
    Base class for all materials using single table inheritance.
    
    This is a polymorphic base class with material_type as the discriminator.
    """
    __tablename__ = 'materials'
    
    # Basic attributes
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    material_type: Mapped[MaterialType] = mapped_column(
        SQLEnum(MaterialType, native_enum=False),
        nullable=False
    )
    unit: Mapped[Optional[MeasurementUnit]] = mapped_column(Enum(MeasurementUnit))
    quality: Mapped[Optional[QualityGrade]] = mapped_column(Enum(QualityGrade))
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    supplier = relationship(...)
    components = relationship(...)  # Many-to-many with Component
    component_materials = relationship(...)  # Direct access to junction table
    inventory = relationship(...)  # One-to-one with Inventory
    picking_list_items = relationship(...)
    purchase_items = relationship(...)
```

#### Material Subtypes

Three specialized subtypes inherit from the base Material class:

1. **Leather**: Specialized for leather materials with properties like leather_type, thickness, and area
2. **Hardware**: For hardware items like buckles, rivets with properties like hardware_type, finish, and size
3. **Supplies**: For consumables like thread, adhesive, dye with properties like color and thread_thickness

#### Relationships

The `Material` model has a many-to-many relationship with `Component` through the `ComponentMaterial` junction table:

```python
# Relationship with components through junction table
components = relationship(
    "Component",
    secondary="component_materials",
    back_populates="materials",
    overlaps="material",  # Resolves overlap warnings
    viewonly=True  # Prevents circular dependency issues
)

# Direct access to the junction table
component_materials = relationship(
    "ComponentMaterial",
    back_populates="material",
    overlaps="components"
)
```

### Component

The `Component` model represents discrete parts used in leatherworking projects.

```python
class Component(AbstractBase, ValidationMixin):
    """
    Component used in patterns and projects.
    
    Attributes:
        name (str): Component name
        description (Optional[str]): Detailed description
        component_type (ComponentType): Type of component
        attributes (Optional[Dict[str, Any]]): Flexible attributes for the component
    """
    __tablename__ = 'components'
    
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    component_type: Mapped[ComponentType] = mapped_column(
        Enum(ComponentType),
        nullable=False,
        index=True
    )
    attributes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    component_materials = relationship(...)  # Direct access to junction table
    materials = relationship(...)  # Many-to-many with Material
    picking_list_items = relationship(...)
    # project_components and patterns relationships will be added later
```

### ComponentMaterial Relationship

The `ComponentMaterial` model serves as a junction table between `Component` and `Material`, allowing for many-to-many relationships with additional attributes.

```python
class ComponentMaterial(Base, ValidationMixin):
    """
    Junction table for the many-to-many relationship between Component and Material.
    
    Adds quantity information to the relationship.
    """
    __tablename__ = 'component_materials'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    component_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("components.id", ondelete="CASCADE"),
        nullable=False
    )
    material_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("materials.id", ondelete="CASCADE"),
        nullable=False
    )
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    
    # Relationships
    component = relationship("Component", back_populates="component_materials")
    material = relationship("Material", back_populates="component_materials")
```

#### Resolving Relationship Warnings

To resolve circular dependency warnings in the many-to-many relationship between `Component` and `Material`, the following configuration is used:

1. In the `Component` class:
```python
materials = relationship(
    "Material",
    secondary="component_materials",
    back_populates="components",
    overlaps="material",  # Exactly as specified in the warning
    viewonly=True  # Prevents circular dependency issues
)
```

2. In the `Material` class:
```python
components = relationship(
    "Component",
    secondary="component_materials",
    back_populates="materials",
    overlaps="component",  # Exactly as specified in the warning
    viewonly=True  # Prevents circular dependency issues
)
```

The `viewonly=True` parameter indicates that these relationships should only be used for reading data, not for modifying the junction table. To create or modify relationships, use the `ComponentMaterial` model directly:

```python
# Example: Creating a new relationship
new_relation = ComponentMaterial(component=component, material=material, quantity=5)
session.add(new_relation)
session.commit()
```

### Pattern

The `Pattern` model represents reusable designs or templates for leatherworking projects.

```python
class Pattern(AbstractBase, ValidationMixin):
    """
    Pattern used for leatherwork projects.
    
    Attributes:
        name (str): Pattern name
        description (Optional[str]): Detailed description
        instructions (Optional[str]): Step-by-step instructions
        size_parameters (Optional[Dict]): Size-related parameters
        material_requirements (Optional[Dict]): Required materials
        skill_level (SkillLevel): Required skill level
    """
    __tablename__ = 'patterns'
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    instructions: Mapped[Optional[str]] = mapped_column(String(5000))
    size_parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    material_requirements: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    skill_level: Mapped[Optional[SkillLevel]] = mapped_column(Enum(SkillLevel))
    
    # Relationships with Component through junction table
    components = relationship(
        "Component",
        secondary="pattern_components",
        back_populates="patterns"
    )
    
    # Relationship with Product
    products = relationship(
        "Product",
        secondary="product_patterns",
        back_populates="patterns"
    )
```

### Product

The `Product` model represents finished goods that can be sold to customers.

```python
class Product(AbstractBase, ValidationMixin, CostingMixin):
    """
    Product that can be sold.
    
    Attributes:
        name (str): Product name
        description (Optional[str]): Detailed description
        sku (str): Stock keeping unit
        unit_price (float): Price per unit
        markup_percentage (float): Percentage markup
        labor_cost (float): Labor cost
        overhead_cost (float): Overhead cost
        inventory_quantity (int): Quantity in inventory
        low_stock_threshold (int): Threshold for low stock alert
    """
    __tablename__ = 'products'
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    sku: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    unit_price: Mapped[Optional[float]] = mapped_column(Float)
    markup_percentage: Mapped[Optional[float]] = mapped_column(Float)
    labor_cost: Mapped[Optional[float]] = mapped_column(Float)
    overhead_cost: Mapped[Optional[float]] = mapped_column(Float)
    inventory_quantity: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    low_stock_threshold: Mapped[Optional[int]] = mapped_column(Integer, default=5)
    
    # Relationships
    patterns = relationship(
        "Pattern",
        secondary="product_patterns",
        back_populates="products"
    )
    
    sales_items = relationship("SalesItem", back_populates="product")
    
    inventory = relationship(
        "Inventory",
        primaryjoin="and_(Product.id==Inventory.item_id, Inventory.item_type=='product')",
        foreign_keys="[Inventory.item_id]",
        back_populates="product",
        uselist=False
    )
```

### Inventory

The `Inventory` model tracks the quantity and status of materials, products, and tools.

```python
class Inventory(AbstractBase, ValidationMixin, AuditMixin, TrackingMixin):
    """
    Inventory tracking for materials, products, and tools.
    
    Attributes:
        item_type (str): Type of item (material/product/tool)
        item_id (int): ID of the item
        quantity (float): Current quantity
        status (InventoryStatus): Status of the inventory item
        storage_location (str): Where the item is stored
        reorder_threshold (float): Threshold for reordering
        supplier_id (int): ID of the supplier
        cost (float): Cost of the inventory
    """
    __tablename__ = 'inventory'
    
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    status: Mapped[InventoryStatus] = mapped_column(
        Enum(InventoryStatus),
        nullable=False,
        default=InventoryStatus.IN_STOCK
    )
    storage_location: Mapped[Optional[str]] = mapped_column(String(100))
    reorder_threshold: Mapped[Optional[float]] = mapped_column(Float)
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True
    )
    cost: Mapped[Optional[float]] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Polymorphic relationships with different item types
    material = relationship(...)
    product = relationship(...)
    tool = relationship(...)
    supplier = relationship(...)
```

## Sales and Purchasing

### Customer

The `Customer` model represents clients who purchase products or commission projects.

```python
class Customer(AbstractBase, ValidationMixin):
    """
    Customer who purchases products or commissions projects.
    
    Attributes:
        first_name (str): First name
        last_name (str): Last name
        email (str): Email address
        phone (str): Phone number
        address (Dict): Address information
        status (CustomerStatus): Current status
        tier (CustomerTier): Customer tier
        source (CustomerSource): How the customer was acquired
    """
    __tablename__ = 'customers'
    
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    status: Mapped[CustomerStatus] = mapped_column(
        Enum(CustomerStatus),
        nullable=False,
        default=CustomerStatus.ACTIVE
    )
    tier: Mapped[Optional[CustomerTier]] = mapped_column(Enum(CustomerTier))
    source: Mapped[Optional[CustomerSource]] = mapped_column(Enum(CustomerSource))
    
    # Relationships
    sales = relationship("Sales", back_populates="customer")
    projects = relationship("Project", back_populates="customer")
```

### Sales and SalesItem

The `Sales` model tracks transactions with customers, while `SalesItem` represents individual line items within a sale.

```python
class Sales(AbstractBase, ValidationMixin, CostingMixin):
    """
    Sale transaction with a customer.
    
    Attributes:
        customer_id (int): ID of the customer
        sale_date (datetime): Date of the sale
        status (SaleStatus): Current status
        payment_status (PaymentStatus): Payment status
        shipping_cost (float): Cost of shipping
        tax (float): Tax amount
        total_amount (float): Total amount
    """
    __tablename__ = 'sales'
    
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True
    )
    sale_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[SaleStatus] = mapped_column(
        Enum(SaleStatus),
        nullable=False,
        default=SaleStatus.QUOTE_REQUEST
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.PENDING
    )
    shipping_cost: Mapped[Optional[float]] = mapped_column(Float, default=0)
    tax: Mapped[Optional[float]] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    customer = relationship("Customer", back_populates="sales")
    sales_items = relationship("SalesItem", back_populates="sale")
    projects = relationship("Project", back_populates="sale")
    picking_lists = relationship("PickingList", back_populates="sale")
```

```python
class SalesItem(AbstractBase, ValidationMixin):
    """
    Item in a sale.
    
    Attributes:
        sale_id (int): ID of the sale
        product_id (int): ID of the product
        quantity (int): Quantity sold
        unit_price (float): Price per unit
        total_price (float): Total price
    """
    __tablename__ = 'sales_items'
    
    sale_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sales.id", ondelete="CASCADE"),
        nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Relationships
    sale = relationship("Sales", back_populates="sales_items")
    product = relationship("Product", back_populates="sales_items")
```

### Supplier

The `Supplier` model represents vendors who provide materials or tools.

```python
class Supplier(AbstractBase, ValidationMixin):
    """
    Supplier of materials or tools.
    
    Attributes:
        name (str): Supplier name
        contact_name (str): Contact person's name
        email (str): Email address
        phone (str): Phone number
        address (str): Physical address
        status (SupplierStatus): Current status
    """
    __tablename__ = 'suppliers'
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_name: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(String(200))
    status: Mapped[SupplierStatus] = mapped_column(
        Enum(SupplierStatus),
        nullable=False,
        default=SupplierStatus.ACTIVE
    )
    
    # Relationships
    materials = relationship("Material", back_populates="supplier")
    tools = relationship("Tool", back_populates="supplier")
    purchases = relationship("Purchase", back_populates="supplier")
    inventory_items = relationship("Inventory", back_populates="supplier")
```

### Purchase and PurchaseItem

The `Purchase` model tracks orders placed with suppliers, while `PurchaseItem` represents individual line items within a purchase.

```python
class Purchase(AbstractBase, ValidationMixin):
    """
    Purchase from a supplier.
    
    Attributes:
        supplier_id (int): ID of the supplier
        purchase_date (datetime): Date of the purchase
        status (PurchaseStatus): Current status
        shipping_cost (float): Cost of shipping
        tax (float): Tax amount
        total_cost (float): Total cost
    """
    __tablename__ = 'purchases'
    
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True
    )
    purchase_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[PurchaseStatus] = mapped_column(
        Enum(PurchaseStatus),
        nullable=False,
        default=PurchaseStatus.DRAFT
    )
    shipping_cost: Mapped[Optional[float]] = mapped_column(Float, default=0)
    tax: Mapped[Optional[float]] = mapped_column(Float, default=0)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="purchases")
    purchase_items = relationship("PurchaseItem", back_populates="purchase")
```

```python
class PurchaseItem(AbstractBase, ValidationMixin):
    """
    Item in a purchase.
    
    Attributes:
        purchase_id (int): ID of the purchase
        item_type (str): Type of item (material/tool)
        item_id (int): ID of the item
        quantity (float): Quantity purchased
        unit_cost (float): Cost per unit
        total_cost (float): Total cost
    """
    __tablename__ = 'purchase_items'
    
    purchase_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("purchases.id", ondelete="CASCADE"),
        nullable=False
    )
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=1)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Polymorphic relationships with different item types
    material = relationship(...)
    tool = relationship(...)
    purchase = relationship("Purchase", back_populates="purchase_items")
```

## Project Management

### Project

The `Project` model represents leatherworking projects undertaken for customers.

```python
class Project(AbstractBase, ValidationMixin):
    """
    Leatherworking project.
    
    Attributes:
        name (str): Project name
        description (str): Detailed description
        customer_id (int): ID of the customer
        status (ProjectStatus): Current status
        start_date (datetime): Project start date
        end_date (datetime): Project end date
        estimated_hours (float): Estimated hours required
        actual_hours (float): Actual hours spent
        hourly_rate (float): Hourly rate for labor
        project_type (ProjectType): Type of project
    """
    __tablename__ = 'projects'
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True
    )
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus),
        nullable=False,
        default=ProjectStatus.INITIAL_CONSULTATION
    )
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float)
    actual_hours: Mapped[Optional[float]] = mapped_column(Float)
    hourly_rate: Mapped[Optional[float]] = mapped_column(Float)
    project_type: Mapped[Optional[ProjectType]] = mapped_column(Enum(ProjectType))
    
    # Relationships
    customer = relationship("Customer", back_populates="projects")
    project_components = relationship("ProjectComponent", back_populates="project")
    picking_lists = relationship("PickingList", back_populates="project")
    tool_lists = relationship("ToolList", back_populates="project")
    tool_checkouts = relationship("ToolCheckout", back_populates="project")
    sale = relationship("Sales", back_populates="projects")
```

### ProjectComponent

The `ProjectComponent` model links projects to the components they use.

```python
class ProjectComponent(AbstractBase, ValidationMixin):
    """
    Association between a project and its components.
    
    Attributes:
        project_id (int): ID of the project
        component_id (int): ID of the component
        quantity (int): Quantity of components
    """
    __tablename__ = 'project_components'
    
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    component_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("components.id", ondelete="CASCADE"),
        nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # Relationships
    project = relationship("Project", back_populates="project_components")
    component = relationship("Component", back_populates="project_components")
```

### PickingList and PickingListItem

The `PickingList` model represents a list of materials and components required for a project, while `PickingListItem` represents individual items on the list.

```python
class PickingList(AbstractBase, ValidationMixin):
    """
    List of materials and components required for a project.
    
    Attributes:
        project_id (int): ID of the project
        sales_id (int): ID of the sale
        status (PickingListStatus): Current status
        created_by (str): User who created the list
        notes (str): Additional notes
    """
    __tablename__ = 'picking_lists'
    
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True
    )
    sales_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("sales.id", ondelete="SET NULL"),
        nullable=True
    )
    status: Mapped[PickingListStatus] = mapped_column(
        Enum(PickingListStatus),
        nullable=False,
        default=PickingListStatus.DRAFT
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    project = relationship("Project", back_populates="picking_lists")
    sale = relationship("Sales", back_populates="picking_lists")
    picking_list_items = relationship("PickingListItem", back_populates="picking_list")
```

```python
class PickingListItem(AbstractBase, ValidationMixin):
    """
    Item in a picking list.
    
    Attributes:
        picking_list_id (int): ID of the picking list
        component_id (int): ID of the component
        material_id (int): ID of the material
        quantity_ordered (int): Quantity ordered
        quantity_picked (int): Quantity picked
    """
    __tablename__ = 'picking_list_items'
    
    picking_list_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("picking_lists.id", ondelete="CASCADE"),
        nullable=False
    )
    component_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("components.id", ondelete="SET NULL"),
        nullable=True
    )
    material_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("materials.id", ondelete="SET NULL"),
        nullable=True
    )
    quantity_ordered: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    quantity_picked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Relationships
    picking_list = relationship("PickingList", back_populates="picking_list_items")
    component = relationship("Component", back_populates="picking_list_items")
    material = relationship("Material", back_populates="picking_list_items")
```

### ToolList and ToolListItem

The `ToolList` model represents a list of tools required for a project, while `ToolListItem` represents individual tools on the list.

```python
class ToolList(AbstractBase, ValidationMixin):
    """
    List of tools required for a project.
    
    Attributes:
        project_id (int): ID of the project
        status (ToolListStatus): Current status
        created_by (str): User who created the list
        notes (str): Additional notes
    """
    __tablename__ = 'tool_lists'
    
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True
    )
    status: Mapped[ToolListStatus] = mapped_column(
        Enum(ToolListStatus),
        nullable=False,
        default=ToolListStatus.DRAFT
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    project = relationship("Project", back_populates="tool_lists")
    tool_list_items = relationship("ToolListItem", back_populates="tool_list")
```

```python
class ToolListItem(AbstractBase, ValidationMixin):
    """
    Item in a tool list.
    
    Attributes:
        tool_list_id (int): ID of the tool list
        tool_id (int): ID of the tool
        quantity (int): Quantity required
    """
    __tablename__ = 'tool_list_items'
    
    tool_list_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tool_lists.id", ondelete="CASCADE"),
        nullable=False
    )
    tool_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tools.id", ondelete="CASCADE"),
        nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # Relationships
    tool_list = relationship("ToolList", back_populates="tool_list_items")
    tool = relationship("Tool", back_populates="tool_list_items")
```

## Tool Management

### Tool

The `Tool` model represents tools used in leatherworking projects.

```python
class Tool(AbstractBase, ValidationMixin):
    """
    Tool used in leatherworking projects.
    
    Attributes:
        name (str): Tool name
        description (str): Detailed description
        category (ToolCategory): Tool category
        brand (str): Brand name
        supplier_id (int): ID of the supplier
        purchase_date (datetime): Date of purchase
        cost (float): Purchase cost
        status (str): Current status
    """
    __tablename__ = 'tools'
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    category: Mapped[Optional[ToolCategory]] = mapped_column(Enum(ToolCategory))
    brand: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(100))
    serial_number: Mapped[Optional[str]] = mapped_column(String(100))
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True
    )
    purchase_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    purchase_price: Mapped[Optional[float]] = mapped_column(Float)
    specifications: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="IN_STOCK"
    )
    last_maintenance_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    next_maintenance_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    maintenance_interval: Mapped[Optional[int]] = mapped_column(Integer) # Days
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="tools")
    inventory = relationship(...)
    purchase_items = relationship(...)
    tool_list_items = relationship("ToolListItem", back_populates="tool")
    tool_maintenances = relationship("ToolMaintenance", back_populates="tool")
    tool_checkouts = relationship("ToolCheckout", back_populates="tool")
```

### ToolMaintenance

The `ToolMaintenance` model tracks maintenance activities for tools.

```python
class ToolMaintenance(AbstractBase, ValidationMixin):
    """
    Maintenance record for a tool.
    
    Attributes:
        tool_id (int): ID of the tool
        maintenance_type (str): Type of maintenance
        maintenance_date (datetime): Date of maintenance
        performed_by (str): Person who performed the maintenance
        cost (float): Cost of maintenance
        status (str): Status of the maintenance
    """
    __tablename__ = 'tool_maintenances'
    
    tool_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tools.id", ondelete="CASCADE"),
        nullable=False
    )
    maintenance_type: Mapped[str] = mapped_column(String(100), nullable=False)
    maintenance_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    performed_by: Mapped[Optional[str]] = mapped_column(String(100))
    cost: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text)
    parts_used: Mapped[Optional[str]] = mapped_column(Text)
    maintenance_interval: Mapped[Optional[int]] = mapped_column(Integer) # Days
    next_maintenance_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    condition_before: Mapped[Optional[str]] = mapped_column(String(100))
    condition_after: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Relationships
    tool = relationship("Tool", back_populates="tool_maintenances")
```

### ToolCheckout

The `ToolCheckout` model tracks when tools are checked out for use.

```python
class ToolCheckout(AbstractBase, ValidationMixin):
    """
    Record of tool checkout.
    
    Attributes:
        tool_id (int): ID of the tool
        checked_out_by (str): Person who checked out the tool
        checked_out_date (datetime): Date of checkout
        due_date (datetime): Date the tool is due back
        returned_date (datetime): Date the tool was returned
        status (str): Current status
        project_id (int): ID of the associated project
    """
    __tablename__ = 'tool_checkouts'
    
    tool_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tools.id", ondelete="CASCADE"),
        nullable=False
    )
    checked_out_by: Mapped[str] = mapped_column(String(100), nullable=False)
    checked_out_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    returned_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="checked_out"
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True
    )
    condition_before: Mapped[Optional[str]] = mapped_column(String(100))
    condition_after: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Relationships
    tool = relationship("Tool", back_populates="tool_checkouts")
    project = relationship("Project", back_populates="tool_checkouts")
```

## Relationship Tables

The system includes several relationship tables to establish many-to-many relationships between models:

### pattern_component_table

Links patterns to components:

```python
pattern_component_table = Table(
    'pattern_components',
    Base.metadata,
    Column('pattern_id', Integer, ForeignKey('patterns.id', ondelete='CASCADE'), nullable=False),
    Column('component_id', Integer, ForeignKey('components.id', ondelete='CASCADE'), nullable=False),
    UniqueConstraint('pattern_id', 'component_id', name='uq_pattern_component')
)
```

### product_pattern_table

Links products to patterns:

```python
product_pattern_table = Table(
    'product_patterns',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
    Column('pattern_id', Integer, ForeignKey('patterns.id', ondelete='CASCADE'), nullable=False),
    UniqueConstraint('product_id', 'pattern_id', name='uq_product_pattern')
)
```

### component_material_table

Links components to materials (not to be confused with the ComponentMaterial model):

```python
component_material_table = Table(
    'component_materials',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('component_id', Integer, ForeignKey('components.id', ondelete='CASCADE'), nullable=False),
    Column('material_id', Integer, ForeignKey('materials.id', ondelete='CASCADE'), nullable=False),
    Column('quantity', Float, nullable=False, default=1.0),
    UniqueConstraint('component_id', 'material_id', name='uq_component_material')
)
```

## Enumerations

The system defines numerous enumerations (`enums.py`) to represent various statuses, types, and categories used across the models. These enums ensure data consistency and provide a clear set of choices for certain fields.

Some of the key enumerations include:

- **SaleStatus**: QUOTE_REQUEST, DESIGN_CONSULTATION, DESIGN_APPROVAL, etc.
- **PaymentStatus**: PENDING, PAID, PARTIALLY_PAID, REFUNDED, CANCELLED
- **PurchaseStatus**: DRAFT, ORDERED, PARTIALLY_RECEIVED, RECEIVED, CANCELLED
- **CustomerStatus**: ACTIVE, INACTIVE, SUSPENDED, ARCHIVED, POTENTIAL, BLOCKED, LEAD
- **CustomerTier**: STANDARD, PREMIUM, VIP
- **CustomerSource**: WEBSITE, RETAIL, REFERRAL, MARKETING, SOCIAL_MEDIA, etc.
- **InventoryStatus**: IN_STOCK, LOW_STOCK, OUT_OF_STOCK, DISCONTINUED, ON_ORDER, etc.
- **MaterialType**: LEATHER, HARDWARE, SUPPLIES, etc.
- **HardwareType**: BUCKLE, SNAP, RIVET, ZIPPER, CLASP, BUTTON, etc.
- **HardwareMaterial**: BRASS, STEEL, STAINLESS_STEEL, NICKEL, SILVER, GOLD, etc.
- **HardwareFinish**: POLISHED, BRUSHED, ANTIQUE, MATTE, CHROME, etc.
- **LeatherType**: VEGETABLE_TANNED, CHROME_TANNED, BRAIN_TANNED, OIL_TANNED, etc.
- **ProjectType**: WALLET, BRIEFCASE, MESSENGER_BAG, TOTE_BAG, BACKPACK, etc.
- **ProjectStatus**: INITIAL_CONSULTATION, DESIGN_PHASE, PATTERN_DEVELOPMENT, etc.
- **SkillLevel**: BEGINNER, INTERMEDIATE, ADVANCED, MASTER, EXPERT
- **ComponentType**: LEATHER, HARDWARE, LINING, THREAD, ADHESIVE, etc.
- **ToolCategory**: CUTTING, PUNCHING, STITCHING, MEASURING, FINISHING, etc.

## Validation and Error Handling

The system includes robust validation to ensure data integrity. Each model provides a `validate()` method that checks for:

- Required fields are present
- String fields don't exceed maximum lengths
- Numeric values are within reasonable ranges
- Foreign key references are valid

Validation errors raise a `ModelValidationError` with a descriptive message to aid in debugging.

Example validation from the `Component` class:

```python
def validate(self) -> None:
    """
    Validate component data.
    
    Raises:
        ModelValidationError: If validation fails
    """
    # Name validation
    if not self.name or not isinstance(self.name, str):
        raise ModelValidationError("Component name must be a non-empty string")
    
    if len(self.name) > 255:
        raise ModelValidationError("Component name cannot exceed 255 characters")
    
    # Description validation
    if self.description and len(self.description) > 500:
        raise ModelValidationError("Component description cannot exceed 500 characters")
    
    # Component type validation
    if not self.component_type:
        raise ModelValidationError("Component type must be specified")
    
    # Attributes validation
    if self.attributes is not None:
        if not isinstance(self.attributes, dict):
            raise ModelValidationError("Attributes must be a dictionary")
        
        # Optional: Additional attribute validation
        for key, value in self.attributes.items():
            if not isinstance(key, str):
                raise ModelValidationError("Attribute keys must be strings")
            
            if len(key) > 100:
                raise ModelValidationError("Attribute key cannot exceed 100 characters")
    
    return self
```

## Initialization and Registration

The system includes utilities for model initialization and registration:

### initialization_timer

A context manager to track model initialization performance:

```python
@contextmanager
def initialization_timer():
    """
    Context manager to track model initialization performance.
    
    Logs the time taken for model initialization.
    """
    start_time = time.time()
    try:
        yield
    finally:
        end_time = time.time()
        elapsed = end_time - start_time
        logging.debug(f"Model initialization took {elapsed:.4f} seconds")
```

### register_models

Registers all imported models in the `ModelRegistry`:

```python
def register_models():
    """
    Register all imported models in the ModelRegistry.
    
    Attempts to register each discovered model and logs any registration failures.
    """
    from sqlalchemy.ext.declarative import DeclarativeMeta
    
    # Find all classes derived from Base
    for name in dir():
        try:
            obj = globals()[name]
            if isinstance(obj, DeclarativeMeta) and obj != Base and obj.__name__ != 'AbstractBase':
                ModelRegistry.register(obj)
                logging.debug(f"Registered model: {obj.__name__}")
        except (KeyError, AttributeError) as e:
            logging.debug(f"Failed to register {name}: {str(e)}")
```

## Common Troubleshooting

### Relationship Circular Dependencies

When working with many-to-many relationships in SQLAlchemy, circular dependencies can occur when both sides of the relationship try to write to the same junction table columns. This can manifest as warnings like:

```
SAWarning: relationship 'Material.components' will copy column components.id to column component_materials.component_id, which conflicts with relationship(s): 'ComponentMaterial.component' (copies components.id to component_materials.component_id)...
```

To resolve these warnings, use the `overlaps` parameter and (if necessary) the `viewonly=True` parameter:

```python
# In Material class
components = relationship(
    "Component",
    secondary="component_materials",
    back_populates="materials",
    overlaps="component",  # Exact string from warning
    viewonly=True  # Make this relationship read-only
)

# In Component class
materials = relationship(
    "Material",
    secondary="component_materials",
    back_populates="components",
    overlaps="material",  # Exact string from warning
    viewonly=True  # Make this relationship read-only
)
```

With both relationships set to `viewonly=True`, you'll need to create or modify relationships directly through the `ComponentMaterial` model:

```python
# Creating a new relationship
new_relation = ComponentMaterial(component=component, material=material, quantity=5)
session.add(new_relation)
session.commit()
```

### Polymorphic Identity Issues

When working with single table inheritance, ensure the `polymorphic_identity` values in `__mapper_args__` match the actual string values stored in the discriminator column, not the enum values.

For example, in the `Material` subclasses:

```python
class Leather(Material):
    # ...
    __mapper_args__ = {
        'polymorphic_identity': 'leather'  # String value, not MaterialType.LEATHER
    }

class Hardware(Material):
    # ...
    __mapper_args__ = {
        'polymorphic_identity': 'hardware'  # String value, not MaterialType.HARDWARE
    }
```

### Accessing Related Objects Through Junction Tables

When using a many-to-many relationship with a junction model (not just a table), you have two ways to access related objects:

1. Through the direct many-to-many relationship (more convenient but read-only with `viewonly=True`):
```python
# Get all materials for a component
materials = component.materials

# Get all components for a material
components = material.components
```

2. Through the junction model (more control, required for modifications):
```python
# Get all ComponentMaterial records for a component
component_materials = component.component_materials

# Access the material and quantity for each record
for cm in component_materials:
    print(f"Material: {cm.material.name}, Quantity: {cm.quantity}")
```

## Database Schema Diagram

The ER diagram below illustrates the relationships between the main entities in the system:

```
erDiagram
    Customer ||--o{ Sales : places
    Sales ||--|{ SalesItem : contains
    Sales ||--o| PickingList : generates
    Sales ||--o| Project : requires

    SalesItem }|--|| Product : references
    
    Product }o--o{ Pattern : follows
    
    Pattern ||--|{ Component : composed_of
    
    Component ||--o{ ComponentMaterial : uses
    ComponentMaterial }|--|| Material : references
    
    Material ||--|| Inventory : tracked_in
    Product ||--|| Inventory : tracked_in
    Tool ||--|| Inventory : tracked_in
    
    Material |o--|| Supplier : supplied_by
    Tool |o--|| Supplier : supplied_by
    
    Material ||--o{ PickingListItem : listed_in
    Component ||--o{ PickingListItem : listed_in
    PickingList ||--|{ PickingListItem : contains
    
    Project ||--|{ ProjectComponent : contains
    ProjectComponent }|--|| Component : uses
    
    Project ||--o| ToolList : requires
    ToolList ||--|{ ToolListItem : contains
    ToolListItem }|--|| Tool : references
    
    Supplier ||--|{ Purchase : receives
    Purchase ||--|{ PurchaseItem : contains
    PurchaseItem }o--|| Material : orders
    PurchaseItem }o--|| Tool : orders
    
    Tool ||--o{ ToolMaintenance : has_maintenance
    Tool ||--o{ ToolCheckout : has_checkouts
    Project |o--o{ ToolCheckout : associated_with
```

This diagram shows the key relationships in the system, including:
- Customer sales and projects
- Product patterns and components
- Material and component relationships
- Inventory tracking
- Tool management and checkout
- Purchase and supply chain