# tests/test_integration.py
import pytest
from sqlalchemy.orm import Session
from typing import Generator

from main import create_app
from database.session import get_db_session
from database.models.base import Base
from database.models import (
    material,
    MaterialTransaction,
    Project,
    ProjectComponent,
    Sale,
    SaleItem,
    Product,
    Storage,
    Supplier
)


@pytest.fixture(scope="session")
def db() -> Generator[Session, None, None]:
    """Fixture to create a test database session."""
    engine = get_db_session(test_mode=True)
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        session = Session(bind=conn)
        yield session
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def app(db: Session):
    """Fixture to create the application instance for testing."""
    app = create_app(test_mode=True, db=db)
    yield app


def test_create_material(app, db: Session):
    """Test creating a new material."""
    material_data = {
        "name": "Test Leather",
        "description": "Integration test material",
        "type": "LEATHER",
        "supplier_id": 1,
        "unit_cost": 10.0,
        # Add more material fields...
    }
    response = app.test_client().post("/materials", json=material_data)
    assert response.status_code == 201
    material_id = response.json["id"]

    material = db.query(Material).filter(Material.id == material_id).first()
    assert material is not None
    assert material.name == "Test Leather"
    # Assert other material properties...


def test_create_project(app, db: Session):
    """Test creating a new project."""
    project_data = {
        "name": "Test Project",
        "description": "Integration test project",
        "type": "BAG",
        "status": "IN_PROGRESS",
        # Add more project fields...
    }
    response = app.test_client().post("/projects", json=project_data)
    assert response.status_code == 201
    project_id = response.json["id"]

    project = db.query(Project).filter(Project.id == project_id).first()
    assert project is not None
    assert project.name == "Test Project"
    # Assert other project properties...


def test_create_order(app, db: Session):
    """Test creating a new sale."""
    order_data = {
        "customer_name": "John Doe",
        "status": "PENDING",
        "items": [
            {"product_id": 1, "quantity": 2},
            {"product_id": 2, "quantity": 1},
        ],
        # Add more sale fields...
    }
    response = app.test_client().post("/orders", json=order_data)
    assert response.status_code == 201
    order_id = response.json["id"]

    order = db.query(Sale).filter(Sale.id == order_id).first()
    assert order is not None
    assert order.customer_name == "John Doe"
    # Assert other sale properties and relationships...


def test_material_transaction(app, db: Session):
    """Test creating a material transaction."""
    transaction_data = {
        "material_id": 1,
        "quantity": 5,
        "transaction_type": "PURCHASE",
        # Add more transaction fields...
    }
    response = app.test_client().post("/material-transactions", json=transaction_data)
    assert response.status_code == 201
    transaction_id = response.json["id"]

    transaction = db.query(MaterialTransaction).filter(MaterialTransaction.id == transaction_id).first()
    assert transaction is not None
    assert transaction.quantity == 5
    # Assert other transaction properties and relationships...


def test_assign_product_to_storage(app, db: Session):
    """Test assigning a product to storage."""
    assignment_data = {
        "product_id": 1,
        "storage_id": 1,
        "quantity": 10,
        # Add more assignment fields...
    }
    response = app.test_client().post("/product-storage", json=assignment_data)
    assert response.status_code == 201

    product = db.query(Product).filter(Product.id == 1).first()
    storage = db.query(Storage).filter(Storage.id == 1).first()
    assert product in storage.products
    # Assert other assignment properties...

def test_update_project_status(app, db: Session):
    """Test updating a project's status."""
    project = db.query(Project).first()
    assert project is not None

    update_data = {
        "status": "COMPLETED"
    }
    response = app.test_client().put(f"/projects/{project.id}", json=update_data)
    assert response.status_code == 200

    updated_project = db.query(Project).filter(Project.id == project.id).first()
    assert updated_project.status == "COMPLETED"

def test_add_project_component(app, db: Session):
    """Test adding a component to a project."""
    project = db.query(Project).first()
    assert project is not None

    component_data = {
        "project_id": project.id,
        "name": "Test Component",
        "description": "Integration test component",
        "quantity": 2,
        "material_id": 1,
        # Add more component fields...
    }
    response = app.test_client().post("/project-components", json=component_data)
    assert response.status_code == 201
    component_id = response.json["id"]

    component = db.query(ProjectComponent).filter(ProjectComponent.id == component_id).first()
    assert component is not None
    assert component.project_id == project.id
    assert component.name == "Test Component"
    # Assert other component properties...

def test_update_order_status(app, db: Session):
    """Test updating an sale's status."""
    order = db.query(Sale).first()
    assert order is not None

    update_data = {
        "status": "PROCESSING"
    }
    response = app.test_client().put(f"/orders/{order.id}", json=update_data)
    assert response.status_code == 200

    updated_order = db.query(Sale).filter(Sale.id == order.id).first()
    assert updated_order.status == "PROCESSING"

def test_get_material_transactions(app, db: Session):
    """Test retrieving material transactions."""
    response = app.test_client().get("/material-transactions")
    assert response.status_code == 200

    transactions = response.json
    assert isinstance(transactions, list)
    # Assert the expected number of transactions
    # Assert the presence of specific transactions

def test_get_project_by_id(app, db: Session):
    """Test retrieving a project by its ID."""
    project = db.query(Project).first()
    assert project is not None

    response = app.test_client().get(f"/projects/{project.id}")
    assert response.status_code == 200

    project_data = response.json
    assert project_data["id"] == project.id
    assert project_data["name"] == project.name
    # Assert other project properties...

def test_delete_order(app, db: Session):
    """Test deleting an sale."""
    order = db.query(Sale).first()
    assert order is not None

    response = app.test_client().delete(f"/orders/{order.id}")
    assert response.status_code == 204

    deleted_order = db.query(Sale).filter(Sale.id == order.id).first()
    assert deleted_order is None

def test_get_storage_locations(app, db: Session):
    """Test retrieving storage locations."""
    response = app.test_client().get("/storage-locations")
    assert response.status_code == 200

    storage_locations = response.json
    assert isinstance(storage_locations, list)
    # Assert the expected number of storage locations
    # Assert the presence of specific storage locations

def test_create_supplier(app, db: Session):
    """Test creating a new supplier."""
    supplier_data = {
        "name": "Test Supplier",
        "contact_person": "John Doe",
        "email": "john@example.com",
        "phone": "1234567890",
        # Add more supplier fields...
    }
    response = app.test_client().post("/suppliers", json=supplier_data)
    assert response.status_code == 201
    supplier_id = response.json["id"]

    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    assert supplier is not None
    assert supplier.name == "Test Supplier"

# tests/test_integration.py
# ... (Previous code remains the same)

def test_update_material_quantity(app, db: Session):
    """Test updating a material's quantity."""
    material = db.query(Material).first()
    assert material is not None

    update_data = {
        "quantity": material.quantity + 10
    }
    response = app.test_client().put(f"/materials/{material.id}", json=update_data)
    assert response.status_code == 200

    updated_material = db.query(Material).filter(Material.id == material.id).first()
    assert updated_material.quantity == material.quantity + 10

def test_get_orders_by_status(app, db: Session):
    """Test retrieving orders by status."""
    status = "PENDING"
    response = app.test_client().get(f"/orders?status={status}")
    assert response.status_code == 200

    orders = response.json
    assert isinstance(orders, list)
    for order in orders:
        assert order["status"] == status

def test_create_product(app, db: Session):
    """Test creating a new product."""
    product_data = {
        "name": "Test Product",
        "description": "Integration test product",
        "price": 99.99,
        "category": "ACCESSORY",
        # Add more product fields...
    }
    response = app.test_client().post("/products", json=product_data)
    assert response.status_code == 201
    product_id = response.json["id"]

    product = db.query(Product).filter(Product.id == product_id).first()
    assert product is not None
    assert product.name == "Test Product"
    # Assert other product properties...

def test_update_supplier_details(app, db: Session):
    """Test updating a supplier's details."""
    supplier = db.query(Supplier).first()
    assert supplier is not None

    update_data = {
        "contact_person": "Updated Contact",
        "email": "updated@example.com"
    }
    response = app.test_client().put(f"/suppliers/{supplier.id}", json=update_data)
    assert response.status_code == 200

    updated_supplier = db.query(Supplier).filter(Supplier.id == supplier.id).first()
    assert updated_supplier.contact_person == "Updated Contact"
    assert updated_supplier.email == "updated@example.com"

def test_get_project_components(app, db: Session):
    """Test retrieving project components."""
    project = db.query(Project).first()
    assert project is not None

    response = app.test_client().get(f"/projects/{project.id}/components")
    assert response.status_code == 200

    components = response.json
    assert isinstance(components, list)
    # Assert the expected number of components
    # Assert the presence of specific components

def test_delete_material(app, db: Session):
    """Test deleting a material."""
    material = db.query(Material).first()
    assert material is not None

    response = app.test_client().delete(f"/materials/{material.id}")
    assert response.status_code == 204

    deleted_material = db.query(Material).filter(Material.id == material.id).first()
    assert deleted_material is None

def test_get_products_by_category(app, db: Session):
    """Test retrieving products by category."""
    category = "ACCESSORY"
    response = app.test_client().get(f"/products?category={category}")
    assert response.status_code == 200

    products = response.json
    assert isinstance(products, list)
    for product in products:
        assert product["category"] == category

def test_update_storage_details(app, db: Session):
    """Test updating a storage's details."""
    storage = db.query(Storage).first()
    assert storage is not None

    update_data = {
        "name": "Updated Storage",
        "location": "New Location"
    }
    response = app.test_client().put(f"/storage/{storage.id}", json=update_data)
    assert response.status_code == 200

    updated_storage = db.query(Storage).filter(Storage.id == storage.id).first()
    assert updated_storage.name == "Updated Storage"
    assert updated_storage.location == "New Location"

# Add more integration test cases for different functionalities...