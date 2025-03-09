# Leatherworking Database System - Full Documentation

## System Overview

The Leatherworking Database System is a comprehensive SQLAlchemy-based data model designed to manage all aspects of a leatherworking business, including inventory, sales, production, and project management. This documentation provides a detailed reference for the database schema, model relationships, and business logic.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Framework](#core-framework)
   - [Base Classes](#base-classes)
   - [Entity Relationship Model](#entity-relationship-model)
3. [Model Documentation](#model-documentation)
   - [Material System](#material-system)
   - [Inventory System](#inventory-system)
   - [Component System](#component-system)
   - [Pattern and Product System](#pattern-and-product-system)
   - [Customer and Sales System](#customer-and-sales-system)
   - [Purchase System](#purchase-system)
   - [Project System](#project-system)
   - [Picking List System](#picking-list-system)
   - [Tool System](#tool-system)
4. [Business Workflows](#business-workflows)
5. [Implementation Considerations](#implementation-considerations)
6. [Code Examples](#code-examples)

## Architecture Overview

The database system is built on several key design principles:

1. **Single Table Inheritance (STI)** - Used for material types (Leather, Hardware, Thread) to simplify the data model while preserving type-specific attributes.

2. **Unified Inventory System** - A single inventory table tracks quantities for all item types (materials, products, tools) using a discriminator pattern.

3. **Clear Separation of Concerns** - Models are organized into logical groups with well-defined responsibilities.

4. **Comprehensive Validation** - Each model includes built-in validation to ensure data integrity.

5. **Circular Dependency Prevention** - The system uses string references and lazy loading to avoid circular import issues.

## Core Framework

### Base Classes

The system is built on a set of base classes and mixins that provide common functionality:

```python
class Base(DeclarativeBase):
    """Base class for all database models."""
    metadata = metadata

class AbstractBase(Base, TimestampMixin):
    """Abstract base class with ID and timestamps."""
    __abstract__ = True
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

class ValidationMixin:
    """Mixin for model validation."""
    def validate(self) -> None: pass

class TimestampMixin:
    """Mixin for tracking creation and update times."""
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.now)

class CostingMixin:
    """Mixin for cost tracking and margin calculation."""
    cost_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
```

### Entity Relationship Model

The database includes the following primary entities and their relationships:

- **Materials** (with subclasses Leather, Hardware, Thread)
- **Components** (parts used in patterns and projects)
- **Patterns** (design templates)
- **Products** (finished goods)
- **Customers** and **Sales** (order processing)
- **Suppliers** and **Purchases** (supply chain)
- **Projects** and **ProjectComponents** (production)
- **PickingLists** and **PickingListItems** (material collection)
- **Tools**, **ToolLists**, and **ToolListItems** (tool management)
- **Inventory** (unified inventory tracking)

## Model Documentation

### Material System

#### Material Model

The `Material` class serves as the base for all material types using Single Table Inheritance:

```python
class Material(AbstractBase, ValidationMixin, CostingMixin):
    __tablename__ = 'materials'
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    material_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    unit: Mapped[Optional[MeasurementUnit]] = mapped_column(Enum(MeasurementUnit), nullable=True)
    quality: Mapped[Optional[QualityGrade]] = mapped_column(Enum(QualityGrade), nullable=True)
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=True)
    
    __mapper_args__ = {
        'polymorphic_on': material_type,
        'polymorphic_identity': 'generic'
    }
```

**Subclasses**:

- **Leather**: With leather-specific attributes like `leather_type`, `thickness`, and `area`
- **Hardware**: With hardware-specific attributes like `hardware_type`, `hardware_material`, and `finish`
- **Thread**: With thread-specific attributes like `color`, `thickness`, and `material_composition`

**Relationships**:
- One supplier provides many materials
- Materials can be used in components via ComponentMaterial
- Materials appear in picking list items
- Materials are tracked in inventory

#### Supplier Model

The `Supplier` model represents vendors that provide materials and tools:

```python
class Supplier(AbstractBase, ValidationMixin):
    __tablename__ = 'suppliers'
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[SupplierStatus] = mapped_column(Enum(SupplierStatus), default=SupplierStatus.ACTIVE)
```

**Relationships**:
- Suppliers provide materials and tools
- Suppliers receive purchase orders

### Inventory System

#### Inventory Model

The `Inventory` model provides a unified inventory tracking system for all item types:

```python
class Inventory(AbstractBase, ValidationMixin):
    __tablename__ = 'inventory'
    
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    status: Mapped[InventoryStatus] = mapped_column(Enum(InventoryStatus), nullable=False)
    storage_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    __table_args__ = (
        UniqueConstraint('item_type', 'item_id', name='uix_inventory_item'),
    )
```

**Key Methods**:
```python
def update_quantity(self, change: float) -> None:
    """Update inventory quantity and status."""
    self.quantity += change
    
    # Update status based on new quantity
    if self.quantity <= 0:
        self.status = InventoryStatus.OUT_OF_STOCK
    elif self.quantity <= 10:  # Arbitrary threshold
        self.status = InventoryStatus.LOW_STOCK
    else:
        self.status = InventoryStatus.IN_STOCK
```

### Component System

#### Component Model

The `Component` model represents discrete parts used in patterns and projects:

```python
class Component(AbstractBase, ValidationMixin):
    __tablename__ = 'components'
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    component_type: Mapped[ComponentType] = mapped_column(Enum(ComponentType), nullable=False)
    attributes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
```

**Relationships**:
- Components can use multiple materials via ComponentMaterial
- Components appear in patterns
- Components are used in projects via ProjectComponent
- Components appear in picking list items

#### ComponentMaterial Model

The `ComponentMaterial` model represents the relationship between components and materials:

```python
class ComponentMaterial(AbstractBase, ValidationMixin):
    __tablename__ = 'component_materials'
    
    component_id: Mapped[int] = mapped_column(Integer, ForeignKey('components.id'), nullable=False)
    material_id: Mapped[int] = mapped_column(Integer, ForeignKey('materials.id'), nullable=False)
    quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
```

### Pattern and Product System

#### Pattern Model

The `Pattern` model represents design templates for products:

```python
class Pattern(AbstractBase, ValidationMixin):
    __tablename__ = 'patterns'
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    skill_level: Mapped[SkillLevel] = mapped_column(Enum(SkillLevel), nullable=False)
    instructions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
```

**Relationships**:
- Patterns can be associated with multiple products
- Patterns contain multiple components

#### Product Model

The `Product` model represents finished goods available for sale:

```python
class Product(AbstractBase, ValidationMixin, CostingMixin):
    __tablename__ = 'products'
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
```

**Key Methods**:
```python
def calculate_profit(self) -> Optional[float]:
    """Calculate profit amount per unit."""
    if not self.cost_price:
        return None
    return self.price - self.cost_price

def calculate_margin_percentage(self) -> Optional[float]:
    """Calculate margin percentage."""
    if not self.cost_price or self.price <= 0:
        return None
    return ((self.price - self.cost_price) / self.price) * 100
```

### Customer and Sales System

#### Customer Model

The `Customer` model represents a person or organization that purchases products:

```python
class Customer(AbstractBase, ValidationMixin):
    __tablename__ = 'customers'
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[CustomerStatus] = mapped_column(Enum(CustomerStatus), default=CustomerStatus.ACTIVE)
    tier: Mapped[CustomerTier] = mapped_column(Enum(CustomerTier), default=CustomerTier.STANDARD)
    source: Mapped[Optional[CustomerSource]] = mapped_column(Enum(CustomerSource), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_business: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
```

**Key Methods**:
```python
def upgrade_tier(self, new_tier: CustomerTier, reason: Optional[str] = None) -> None:
    """Upgrade customer to a higher tier."""
    # Ensure new tier is an upgrade
    tier_order = {
        CustomerTier.NEW: 0,
        CustomerTier.STANDARD: 1,
        CustomerTier.PREMIUM: 2,
        CustomerTier.VIP: 3
    }
    
    current_tier_value = tier_order.get(self.tier, 0)
    new_tier_value = tier_order.get(new_tier, 0)
    
    if new_tier_value <= current_tier_value:
        raise ValueError(f"New tier ({new_tier.name}) is not an upgrade")
    
    self.tier = new_tier
```

#### Sales Model

The `Sales` model represents a customer purchase:

```python
class Sales(AbstractBase, ValidationMixin, CostingMixin):
    __tablename__ = 'sales'
    
    customer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('customers.id'), nullable=True)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[SaleStatus] = mapped_column(Enum(SaleStatus), nullable=False, default=SaleStatus.DRAFT)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Payment tracking
    amount_paid: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payment_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Shipping information
    shipping_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shipped_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
```

**Key Methods**:
```python
def update_total_amount(self) -> None:
    """Recalculate the total amount based on the linked sales items."""
    if not hasattr(self, 'items') or not self.items:
        self.total_amount = 0.0
        return
        
    self.total_amount = sum(item.price * item.quantity for item in self.items)

def update_status(self, new_status: SaleStatus, notes: Optional[str] = None) -> None:
    """Update the sales status and add notes."""
    old_status = self.status
    self.status = new_status
    
    if notes:
        status_note = f"[STATUS CHANGE] {old_status.name} -> {new_status.name}: {notes}"
        if self.notes:
            self.notes += f"\n{status_note}"
        else:
            self.notes = status_note
```

#### SalesItem Model

The `SalesItem` model represents an individual product line in a sale:

```python
class SalesItem(AbstractBase, ValidationMixin):
    __tablename__ = 'sales_items'
    
    sales_id: Mapped[int] = mapped_column(Integer, ForeignKey('sales.id'), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
```

### Purchase System

#### Purchase Model

The `Purchase` model represents an order placed with a supplier:

```python
class Purchase(AbstractBase, ValidationMixin):
    __tablename__ = 'purchases'
    
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey('suppliers.id'), nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[PurchaseStatus] = mapped_column(Enum(PurchaseStatus), default=PurchaseStatus.DRAFT)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Order tracking
    order_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expected_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Reference information
    purchase_order_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    invoice_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
```

#### PurchaseItem Model

The `PurchaseItem` model represents an individual item line in a purchase order:

```python
class PurchaseItem(AbstractBase, ValidationMixin):
    __tablename__ = 'purchase_items'
    
    purchase_id: Mapped[int] = mapped_column(Integer, ForeignKey('purchases.id'), nullable=False)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    received_quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
```

**Key Methods**:
```python
def receive(self, quantity: float) -> None:
    """Record receipt of purchased items."""
    if quantity <= 0:
        raise ValueError("Received quantity must be positive")
    
    if self.received_quantity + quantity > self.quantity:
        raise ValueError("Received quantity cannot exceed ordered quantity")
    
    self.received_quantity += quantity
    
    # Update inventory for the received item
    if self.received_quantity > 0:
        item = None
        if self.item_type == 'material' and self.material:
            item = self.material
        elif self.item_type == 'tool' and self.tool:
            item = self.tool
            
        if item and hasattr(item, 'inventory') and item.inventory:
            item.inventory.update_quantity(quantity)
```

### Project System

#### Project Model

The `Project` model represents a production job, typically tied to a customer order:

```python
class Project(AbstractBase, ValidationMixin):
    __tablename__ = 'projects'
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    type: Mapped[ProjectType] = mapped_column(Enum(ProjectType), nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), default=ProjectStatus.PLANNED)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sales_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('sales.id'), nullable=True)
```

**Key Methods**:
```python
def update_status(self, new_status: ProjectStatus, notes: Optional[str] = None) -> None:
    """Update the project status and add notes."""
    old_status = self.status
    self.status = new_status
    
    # Update related dates based on status
    if (new_status == ProjectStatus.IN_PROGRESS and not self.start_date):
        self.start_date = datetime.now()
    elif (new_status == ProjectStatus.COMPLETED and not self.end_date):
        self.end_date = datetime.now()
```

#### ProjectComponent Model

The `ProjectComponent` model represents the relationship between a project and its required components:

```python
class ProjectComponent(AbstractBase, ValidationMixin):
    __tablename__ = 'project_components'
    
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey('projects.id'), nullable=False)
    component_id: Mapped[int] = mapped_column(Integer, ForeignKey('components.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    completed_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
```

**Key Methods**:
```python
def update_completion(self, amount: int) -> None:
    """Update completion status."""
    if amount <= 0:
        raise ValueError("Completion amount must be positive")
    
    if self.completed_quantity + amount > self.quantity:
        raise ValueError("Cannot complete more than the total quantity")
    
    self.completed_quantity += amount
```

### Picking List System

#### PickingList Model

The `PickingList` model represents a material picking list for production:

```python
class PickingList(AbstractBase, ValidationMixin):
    __tablename__ = 'picking_lists'
    
    sales_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('sales.id'), nullable=True)
    status: Mapped[PickingListStatus] = mapped_column(Enum(PickingListStatus), default=PickingListStatus.DRAFT)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
```

**Key Methods**:
```python
def is_complete(self) -> bool:
    """Check if all items have been picked."""
    if not self.items:
        return False
    
    return all(item.is_fully_picked() for item in self.items)
```

#### PickingListItem Model

The `PickingListItem` model represents an individual item in a picking list:

```python
class PickingListItem(AbstractBase, ValidationMixin):
    __tablename__ = 'picking_list_items'
    
    picking_list_id: Mapped[int] = mapped_column(Integer, ForeignKey('picking_lists.id'), nullable=False)
    component_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('components.id'), nullable=True)
    material_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('materials.id'), nullable=True)
    quantity_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_picked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
```

**Key Methods**:
```python
def is_fully_picked(self) -> bool:
    """Check if the item has been fully picked."""
    return self.quantity_picked >= self.quantity_ordered

def pick(self, quantity: int) -> None:
    """Record picked quantity."""
    if quantity <= 0:
        raise ValueError("Picked quantity must be positive")
    
    self.quantity_picked += quantity
    
    # Update inventory
    if self.material_id and hasattr(self, 'material') and self.material and hasattr(self.material, 'inventory'):
        self.material.inventory.update_quantity(-quantity)
```

### Tool System

#### Tool Model

The `Tool` model represents tools used in leatherworking production:

```python
class Tool(AbstractBase, ValidationMixin):
    __tablename__ = 'tools'
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tool_type: Mapped[ToolType] = mapped_column(Enum(ToolType), nullable=False)
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('suppliers.id'), nullable=True)
    needs_maintenance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    maintenance_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
```

**Key Methods**:
```python
def schedule_maintenance(self, notes: Optional[str] = None) -> None:
    """Mark the tool for maintenance."""
    self.needs_maintenance = True
    
    if notes:
        maintenance_note = f"[MAINTENANCE REQUIRED] {notes}"
        if self.maintenance_notes:
            self.maintenance_notes += f"\n{maintenance_note}"
        else:
            self.maintenance_notes = maintenance_note

def complete_maintenance(self, notes: Optional[str] = None) -> None:
    """Mark the tool maintenance as completed."""
    self.needs_maintenance = False
    
    if notes:
        maintenance_note = f"[MAINTENANCE COMPLETED] {notes}"
        if self.maintenance_notes:
            self.maintenance_notes += f"\n{maintenance_note}"
        else:
            self.maintenance_notes = maintenance_note
```

#### ToolList and ToolListItem Models

The `ToolList` model represents a list of tools needed for a project:

```python
class ToolList(AbstractBase, ValidationMixin):
    __tablename__ = 'tool_lists'
    
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey('projects.id'), nullable=False)
    status: Mapped[ToolListStatus] = mapped_column(Enum(ToolListStatus), default=ToolListStatus.DRAFT)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
```

The `ToolListItem` model represents an individual tool in a tool list:

```python
class ToolListItem(AbstractBase, ValidationMixin):
    __tablename__ = 'tool_list_items'
    
    tool_list_id: Mapped[int] = mapped_column(Integer, ForeignKey('tool_lists.id'), nullable=False)
    tool_id: Mapped[int] = mapped_column(Integer, ForeignKey('tools.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
```

## Business Workflows

### 1. Order Processing Workflow

1. **Order Creation**
   - Create a `Sales` record with `customer_id` and initial status
   - Add `SalesItem` records for each product ordered
   - Calculate total amount

2. **Material Collection**
   - Generate a `PickingList` from the sales order
   - Create `PickingListItem` records for required materials
   - Update inventory as materials are picked

3. **Production**
   - Create a `Project` linked to the sales order
   - Add `ProjectComponent` records for each component needed
   - Track progress through project status updates

4. **Order Completion**
   - Update project status to COMPLETED
   - Update sales status to COMPLETED or SHIPPED
   - Record payment information

### 2. Inventory Management Workflow

1. **Purchase Order Creation**
   - Create a `Purchase` record with supplier information
   - Add `PurchaseItem` records for materials or tools to order
   - Calculate total amount

2. **Receiving Orders**
   - Update purchase status to DELIVERED when received
   - Record received quantities for each purchase item
   - Update inventory records with new quantities

3. **Inventory Tracking**
   - Monitor inventory levels through the `Inventory` entity
   - Status updates based on quantity thresholds (IN_STOCK, LOW_STOCK, OUT_OF_STOCK)
   - Record storage locations for easy retrieval

### 3. Production Planning Workflow

1. **Pattern Development**
   - Create `Pattern` records with components and instructions
   - Link patterns to products for production reference

2. **Project Planning**
   - Create a `Project` with start and end dates
   - Add component requirements through `ProjectComponent` records
   - Generate `ToolList` for required tools

3. **Production Tracking**
   - Update project status throughout production stages
   - Track component completion
   - Record actual production hours

## Implementation Considerations

### Database Setup

1. **Initialization**

```python
# Create engine and tables
from sqlalchemy import create_engine
from database.models import Base

engine = create_engine('sqlite:///leatherworking.db')
Base.metadata.create_all(engine)
```

2. **Session Management**

```python
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)
session = Session()
```

### Preventing Circular Dependencies

The system uses several techniques to prevent circular dependencies:

1. **String References** - Using string names for relationship secondary tables
2. **Ordered Imports** - The `__init__.py` file uses a predefined import order
3. **Conditional Imports** - Some imports are done within functions to delay resolution

## Code Examples

### Creating a Material with Inventory Record

```python
# Create a new leather material
leather = Leather(
    name="Premium Veg-Tan Leather",
    leather_type=LeatherType.VEGETABLE_TANNED,
    thickness=2.0,
    area=12.5,
    quality=QualityGrade.PREMIUM,
    supplier_id=1,
    cost_price=120.0
)
session.add(leather)
session.flush()  # To get the ID

# Create inventory record for the leather
inventory = Inventory(
    item_type="material",
    item_id=leather.id,
    quantity=10.0,
    status=InventoryStatus.IN_STOCK,
    storage_location="Shelf A-3"
)
session.add(inventory)
session.commit()
```

### Processing a Customer Order

```python
# Create a sales order
sale = Sales(
    customer_id=1,
    status=SaleStatus.CONFIRMED,
    payment_status=PaymentStatus.PENDING
)
session.add(sale)
session.flush()

# Add sales items
item = SalesItem(
    sales_id=sale.id,
    product_id=1,
    quantity=2,
    price=89.99
)
session.add(item)
session.commit()

# Update the total amount
sale.update_total_amount()
session.commit()

# Create a picking list
picking_list = PickingList(
    sales_id=sale.id,
    status=PickingListStatus.DRAFT
)
session.add(picking_list)
session.flush()

# Add picking list items
picking_item = PickingListItem(
    picking_list_id=picking_list.id,
    material_id=1,
    quantity_ordered=4
)
session.add(picking_item)
session.commit()

# Record picking
picking_item.pick(4)
session.commit()

# Complete the picking list
picking_list.update_status(PickingListStatus.COMPLETED)
session.commit()
```

### Creating a Project

```python
# Create a project for a custom wallet
project = Project(
    name="Custom Bifold Wallet",
    description="Handmade bifold wallet with card slots",
    type=ProjectType.WALLET,
    status=ProjectStatus.PLANNED,
    sales_id=1
)
session.add(project)
session.flush()

# Add components to the project
project_component = ProjectComponent(
    project_id=project.id,
    component_id=1,  # Exterior leather component
    quantity=1
)
session.add(project_component)
session.commit()

# Create a tool list
tool_list = ToolList(
    project_id=project.id,
    status=ToolListStatus.DRAFT
)
session.add(tool_list)
session.flush()

# Add tools to the tool list
tool_item = ToolListItem(
    tool_list_id=tool_list.id,
    tool_id=1,  # Stitching tool
    quantity=1
)
session.add(tool_item)
session.commit()

# Start the project
project.update_status(ProjectStatus.IN_PROGRESS)
session.commit()
```

This completes the full documentation for the Leatherworking Database System. The system provides a comprehensive foundation for managing a leatherworking business, tracking inventory, processing orders, and managing production.