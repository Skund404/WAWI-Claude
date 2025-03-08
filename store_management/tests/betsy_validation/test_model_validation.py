# tests/test_model_validation.py
"""
Tests focusing on model validation and error handling.
These tests ensure data integrity and validation rules are properly enforced.
"""

import pytest
import datetime
from typing import Dict, Any

from sqlalchemy.exc import IntegrityError

from database import ComponentMaterial, ProjectComponent
from database.models.base import ModelValidationError

from database.models import (
    Customer, Sales, Product, Material, Leather, Hardware,
    Tool, Pattern, Component, Project, Supplier
)
from database.models.enums import (
    CustomerStatus, CustomerTier, SaleStatus, PaymentStatus,
    MaterialType, LeatherType, HardwareType, ComponentType,
    ProjectType, ProjectStatus, SkillLevel, QualityGrade,
    MeasurementUnit
)


class TestRequiredFieldValidation:
    """Test validation of required fields."""

    def test_customer_required_fields(self, db_session):
        """Test that Customer model requires name and email."""
        # Missing name
        customer_no_name = Customer(
            email="test@example.com",
            status=CustomerStatus.ACTIVE
        )

        with pytest.raises(Exception) as excinfo:
            db_session.add(customer_no_name)
            db_session.flush()

        db_session.rollback()

        # Missing email
        customer_no_email = Customer(
            name="Test Customer",
            status=CustomerStatus.ACTIVE
        )

        with pytest.raises(Exception) as excinfo:
            db_session.add(customer_no_email)
            db_session.flush()

        db_session.rollback()

        # Valid customer
        valid_customer = Customer(
            name="Valid Customer",
            email="valid@example.com",
            status=CustomerStatus.ACTIVE
        )

        db_session.add(valid_customer)
        db_session.flush()

        # Verify valid customer was saved
        saved_customer = db_session.query(Customer).filter_by(email="valid@example.com").first()
        assert saved_customer is not None, "Valid customer should be saved"
        assert saved_customer.name == "Valid Customer", "Customer name should be saved correctly"

    def test_project_required_fields(self, db_session):
        """Test that Project model requires name and status."""
        # Missing name
        project_no_name = Project(
            description="Test description",
            type=ProjectType.WALLET,
            status=ProjectStatus.DESIGN_PHASE
        )

        with pytest.raises(Exception) as excinfo:
            db_session.add(project_no_name)
            db_session.flush()

        db_session.rollback()

        # Missing status
        project_no_status = Project(
            name="Test Project",
            description="Test description",
            type=ProjectType.WALLET
        )

        with pytest.raises(Exception) as excinfo:
            db_session.add(project_no_status)
            db_session.flush()

        db_session.rollback()

        # Valid project
        valid_project = Project(
            name="Valid Project",
            description="Test description",
            type=ProjectType.WALLET,
            status=ProjectStatus.DESIGN_PHASE
        )

        db_session.add(valid_project)
        db_session.flush()

        # Verify valid project was saved
        saved_project = db_session.query(Project).filter_by(name="Valid Project").first()
        assert saved_project is not None, "Valid project should be saved"
        assert saved_project.type == ProjectType.WALLET, "Project type should be saved correctly"


class TestDataTypeValidation:
    """Test validation of field data types."""

    def test_price_numeric_validation(self, db_session):
        """Test that price fields only accept numeric values."""
        # Product with invalid price
        invalid_product = Product(
            name="Invalid Price Product",
            price="not a number"  # This should fail
        )

        with pytest.raises(Exception) as excinfo:
            db_session.add(invalid_product)
            db_session.flush()

        db_session.rollback()

        # Product with valid price
        valid_product = Product(
            name="Valid Price Product",
            price=99.99
        )

        db_session.add(valid_product)
        db_session.flush()

        # Verify valid product was saved
        saved_product = db_session.query(Product).filter_by(name="Valid Price Product").first()
        assert saved_product is not None, "Valid product should be saved"
        assert saved_product.price == 99.99, "Product price should be saved correctly"

    def test_date_field_validation(self, db_session):
        """Test validation of date fields."""
        # Project with invalid date
        invalid_date_project = Project(
            name="Invalid Date Project",
            description="Test description",
            type=ProjectType.WALLET,
            status=ProjectStatus.DESIGN_PHASE,
            start_date="not a date"  # This should fail
        )

        with pytest.raises(Exception) as excinfo:
            db_session.add(invalid_date_project)
            db_session.flush()

        db_session.rollback()

        # Project with valid date
        now = datetime.datetime.utcnow()
        valid_date_project = Project(
            name="Valid Date Project",
            description="Test description",
            type=ProjectType.WALLET,
            status=ProjectStatus.DESIGN_PHASE,
            start_date=now
        )

        db_session.add(valid_date_project)
        db_session.flush()

        # Verify valid project was saved
        saved_project = db_session.query(Project).filter_by(name="Valid Date Project").first()
        assert saved_project is not None, "Valid project should be saved"
        assert saved_project.start_date is not None, "Project start date should be saved"


class TestEnumValidation:
    """Test validation of enum fields."""

    def test_customer_status_validation(self, db_session):
        """Test validation of CustomerStatus enum."""
        # Customer with invalid status
        invalid_status_customer = Customer(
            name="Invalid Status Customer",
            email="invalid_status@example.com",
            status="NOT_A_REAL_STATUS"  # This should fail
        )

        with pytest.raises(Exception) as excinfo:
            db_session.add(invalid_status_customer)
            db_session.flush()

        db_session.rollback()

        # Customer with valid status
        valid_status_customer = Customer(
            name="Valid Status Customer",
            email="valid_status@example.com",
            status=CustomerStatus.ACTIVE
        )

        db_session.add(valid_status_customer)
        db_session.flush()

        # Verify valid customer was saved
        saved_customer = db_session.query(Customer).filter_by(email="valid_status@example.com").first()
        assert saved_customer is not None, "Valid customer should be saved"
        assert saved_customer.status == CustomerStatus.ACTIVE, "Customer status should be saved correctly"

    def test_project_type_validation(self, db_session):
        """Test validation of ProjectType enum."""
        # Project with invalid type
        invalid_type_project = Project(
            name="Invalid Type Project",
            description="Test description",
            type="NOT_A_REAL_TYPE",  # This should fail
            status=ProjectStatus.DESIGN_PHASE
        )

        with pytest.raises(Exception) as excinfo:
            db_session.add(invalid_type_project)
            db_session.flush()

        db_session.rollback()

        # Project with valid type
        valid_type_project = Project(
            name="Valid Type Project",
            description="Test description",
            type=ProjectType.WALLET,
            status=ProjectStatus.DESIGN_PHASE
        )

        db_session.add(valid_type_project)
        db_session.flush()

        # Verify valid project was saved
        saved_project = db_session.query(Project).filter_by(name="Valid Type Project").first()
        assert saved_project is not None, "Valid project should be saved"
        assert saved_project.type == ProjectType.WALLET, "Project type should be saved correctly"


class TestUniqueConstraintValidation:
    """Test validation of unique constraints."""

    def test_customer_email_uniqueness(self, db_session):
        """Test that customer email must be unique."""
        # Create a customer
        customer1 = Customer(
            name="First Customer",
            email="duplicate@example.com",
            status=CustomerStatus.ACTIVE
        )
        db_session.add(customer1)
        db_session.flush()

        # Try to create another customer with the same email
        customer2 = Customer(
            name="Second Customer",
            email="duplicate@example.com",  # Same email
            status=CustomerStatus.ACTIVE
        )

        with pytest.raises(Exception) as excinfo:
            db_session.add(customer2)
            db_session.flush()

        db_session.rollback()

        # Verify we still have only one customer with that email
        customers = db_session.query(Customer).filter_by(email="duplicate@example.com").all()
        assert len(customers) == 1, "Email should be unique across customers"

    def test_product_name_uniqueness(self, db_session):
        """Test that product names must be unique."""
        # Create a product
        product1 = Product(
            name="Duplicate Product Name",
            price=99.99
        )
        db_session.add(product1)
        db_session.flush()

        # Try to create another product with the same name
        product2 = Product(
            name="Duplicate Product Name",  # Same name
            price=149.99
        )

        with pytest.raises(Exception) as excinfo:
            db_session.add(product2)
            db_session.flush()

        db_session.rollback()

        # Verify we still have only one product with that name
        products = db_session.query(Product).filter_by(name="Duplicate Product Name").all()
        assert len(products) == 1, "Product name should be unique"


class TestForeignKeyValidation:
    """Test validation of foreign key constraints."""

    def test_sales_customer_fk_validation(self, db_session):
        """Test that Sales requires a valid customer_id."""
        # Try to create a sale with non-existent customer_id
        invalid_sale = Sales(
            customer_id=9999,  # Non-existent ID
            total_amount=199.99,
            status=SaleStatus.COMPLETED,
            payment_status=PaymentStatus.PAID
        )

        with pytest.raises(Exception) as excinfo:
            db_session.add(invalid_sale)
            db_session.flush()

        db_session.rollback()

        # Create a valid customer first
        customer = Customer(
            name="FK Test Customer",
            email="fk_test@example.com",
            status=CustomerStatus.ACTIVE
        )
        db_session.add(customer)
        db_session.flush()

        # Now create a sale with valid customer_id
        valid_sale = Sales(
            customer_id=customer.id,
            total_amount=199.99,
            status=SaleStatus.COMPLETED,
            payment_status=PaymentStatus.PAID
        )

        db_session.add(valid_sale)
        db_session.flush()

        # Verify sale was saved
        saved_sale = db_session.query(Sales).filter_by(customer_id=customer.id).first()
        assert saved_sale is not None, "Sale with valid customer_id should be saved"
        assert saved_sale.total_amount == 199.99, "Sale amount should be saved correctly"

    def test_project_component_fk_validation(self, db_session):
        """Test that ProjectComponent requires valid project_id and component_id."""
        # Try to create a project component with non-existent IDs
        invalid_project_component = ProjectComponent(
            project_id=9999,  # Non-existent ID
            component_id=9999,  # Non-existent ID
            quantity=1
        )

        with pytest.raises(Exception) as excinfo:
            db_session.add(invalid_project_component)
            db_session.flush()

        db_session.rollback()

        # Create valid project and component first
        project = Project(
            name="FK Test Project",
            description="Testing foreign keys",
            type=ProjectType.WALLET,
            status=ProjectStatus.DESIGN_PHASE
        )

        component = Component(
            name="FK Test Component",
            type=ComponentType.LEATHER
        )

        db_session.add_all([project, component])
        db_session.flush()

        # Now create a valid project component
        valid_project_component = ProjectComponent(
            project_id=project.id,
            component_id=component.id,
            quantity=1
        )

        db_session.add(valid_project_component)
        db_session.flush()

        # Verify project component was saved
        saved_pc = db_session.query(ProjectComponent).filter_by(
            project_id=project.id,
            component_id=component.id
        ).first()

        assert saved_pc is not None, "ProjectComponent with valid IDs should be saved"
        assert saved_pc.quantity == 1, "ProjectComponent quantity should be saved correctly"


class TestQuantityValidation:
    """Test validation of quantity fields."""

    def test_non_negative_quantity(self, db_session, sample_data):
        """Test that quantity fields must be non-negative."""
        component_id = sample_data['component']['id']
        material_id = sample_data['material']['id']

        # Try to create a component material with negative quantity
        invalid_component_material = ComponentMaterial(
            component_id=component_id,
            material_id=material_id,
            quantity=-5  # Negative quantity
        )

        with pytest.raises(Exception) as excinfo:
            db_session.add(invalid_component_material)
            db_session.flush()

        db_session.rollback()

        # Create with valid (non-negative) quantity
        valid_component_material = ComponentMaterial(
            component_id=component_id,
            material_id=material_id,
            quantity=5  # Valid quantity
        )

        db_session.add(valid_component_material)
        db_session.flush()

        # Verify component material was saved
        saved_cm = db_session.query(ComponentMaterial).filter_by(
            component_id=component_id,
            material_id=material_id
        ).first()

        assert saved_cm is not None, "ComponentMaterial with valid quantity should be saved"
        assert saved_cm.quantity == 5, "ComponentMaterial quantity should be saved correctly"


class TestToDict:
    """Test the to_dict functionality."""

    def test_to_dict_includes_all_fields(self, db_session):
        """Test that to_dict includes all model fields."""
        # Create a customer with all fields filled
        customer = Customer(
            name="Dict Test Customer",
            email="dict_test@example.com",
            status=CustomerStatus.ACTIVE,
            tier=CustomerTier.PREMIUM,
            notes="Test notes"
        )

        db_session.add(customer)
        db_session.flush()

        # Get dictionary representation
        customer_dict = customer.to_dict()

        # Check that all fields are included
        assert 'id' in customer_dict, "Dictionary should include id"
        assert 'name' in customer_dict, "Dictionary should include name"
        assert 'email' in customer_dict, "Dictionary should include email"
        assert 'status' in customer_dict, "Dictionary should include status"
        assert 'tier' in customer_dict, "Dictionary should include tier"
        assert 'notes' in customer_dict, "Dictionary should include notes"
        assert 'uuid' in customer_dict, "Dictionary should include uuid"
        assert 'is_deleted' in customer_dict, "Dictionary should include is_deleted"

        # Check values
        assert customer_dict['name'] == "Dict Test Customer"
        assert customer_dict['email'] == "dict_test@example.com"
        assert customer_dict['status'] == CustomerStatus.ACTIVE
        assert customer_dict['tier'] == CustomerTier.PREMIUM
        assert customer_dict['notes'] == "Test notes"

    def test_to_dict_excludes_specified_fields(self, db_session):
        """Test that to_dict excludes specified fields."""
        # Create a customer
        customer = Customer(
            name="Exclude Test Customer",
            email="exclude_test@example.com",
            status=CustomerStatus.ACTIVE,
            tier=CustomerTier.STANDARD,
            notes="Test notes for exclusion"
        )

        db_session.add(customer)
        db_session.flush()

        # Get dictionary representation with exclusions
        exclude_fields = ['notes', 'created_at', 'updated_at', 'uuid']
        customer_dict = customer.to_dict(exclude_fields=exclude_fields)

        # Check that specified fields are excluded
        for field in exclude_fields:
            assert field not in customer_dict, f"Dictionary should not include {field}"

        # Check that other fields are included
        assert 'id' in customer_dict, "Dictionary should include id"
        assert 'name' in customer_dict, "Dictionary should include name"
        assert 'email' in customer_dict, "Dictionary should include email"
        assert 'status' in customer_dict, "Dictionary should include status"
        assert 'tier' in customer_dict, "Dictionary should include tier"


class TestSoftDelete:
    """Test soft delete functionality."""

    def test_soft_delete_and_restore(self, db_session):
        """Test soft delete and restore functionality."""
        # Create a customer
        customer = Customer(
            name="Soft Delete Test Customer",
            email="soft_delete@example.com",
            status=CustomerStatus.ACTIVE
        )
        db_session.add(customer)
        db_session.flush()

        # Soft delete the customer
        customer.soft_delete()
        db_session.flush()

        # Check that customer is marked as deleted
        deleted_customer = db_session.query(Customer).filter_by(id=customer.id).first()
        assert deleted_customer.is_deleted, "Customer should be marked as deleted"
        assert deleted_customer.deleted_at is not None, "deleted_at should be set"

        # Restore the customer
        deleted_customer.restore()
        db_session.flush()

        # Check that customer is restored
        restored_customer = db_session.query(Customer).filter_by(id=customer.id).first()
        assert not restored_customer.is_deleted, "Customer should be marked as not deleted"
        assert restored_customer.deleted_at is None, "deleted_at should be None"

    def test_query_excludes_soft_deleted_by_default(self, db_session):
        """Test that queries exclude soft-deleted records by default if implemented."""
        # Create customers
        customer1 = Customer(
            name="Customer 1",
            email="customer1@example.com",
            status=CustomerStatus.ACTIVE
        )

        customer2 = Customer(
            name="Customer 2",
            email="customer2@example.com",
            status=CustomerStatus.ACTIVE
        )

        db_session.add_all([customer1, customer2])
        db_session.flush()

        # Soft delete one customer
        customer1.soft_delete()
        db_session.flush()

        # Create a query that filters deleted records if the model supports it
        query = db_session.query(Customer)
        if hasattr(Customer, 'get_active_only_query'):
            query = Customer.get_active_only_query(query)
        else:
            query = query.filter(Customer.is_deleted == False)

        # Check that only non-deleted customers are returned
        active_customers = query.all()
        active_emails = [c.email for c in active_customers]

        assert "customer2@example.com" in active_emails, "Non-deleted customer should be included"
        assert "customer1@example.com" not in active_emails, "Deleted customer should be excluded"