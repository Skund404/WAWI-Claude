# tests/test_model_performance.py
"""
Tests focusing on model performance and edge cases.
These tests ensure the model system performs well under various conditions.
"""

import pytest
import time
import random
import string
import datetime
from typing import Dict, Any, List

from sqlalchemy import func, inspect
from sqlalchemy.orm import joinedload

from database.models import (
    Customer, Sales, SalesItem, Product, Supplier, Material,
    Project, Component, ProjectComponent
)
from database.models.enums import (
    CustomerStatus, SaleStatus, PaymentStatus, ProjectStatus,
    ProjectType, ComponentType, MaterialType
)


def random_string(length=10):
    """Generate a random string of fixed length."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


class TestBulkOperations:
    """Test bulk operations on models."""

    def test_bulk_insert(self, db_session):
        """Test bulk insertion of records."""
        # Create multiple customers at once
        num_customers = 50
        customers = []

        for i in range(num_customers):
            customers.append(Customer(
                name=f"Bulk Customer {i}",
                email=f"bulk{i}@example.com",
                status=CustomerStatus.ACTIVE
            ))

        start_time = time.time()
        db_session.add_all(customers)
        db_session.flush()
        end_time = time.time()

        # Log performance
        elapsed = end_time - start_time
        print(f"\nBulk inserted {num_customers} customers in {elapsed:.4f} seconds")

        # Verify all customers were saved
        count = db_session.query(Customer).filter(
            Customer.email.like('bulk%@example.com')
        ).count()

        assert count == num_customers, f"Should have inserted {num_customers} customers"

    def test_bulk_update(self, db_session):
        """Test bulk update of records."""
        # Create customers to update
        num_customers = 50
        customers = []

        for i in range(num_customers):
            customers.append(Customer(
                name=f"Update Customer {i}",
                email=f"update{i}@example.com",
                status=CustomerStatus.ACTIVE
            ))

        db_session.add_all(customers)
        db_session.flush()

        # Update all customers to a different status using a single query
        start_time = time.time()

        # Using SQLAlchemy update() for bulk operations
        from sqlalchemy import update
        stmt = update(Customer).where(
            Customer.email.like('update%@example.com')
        ).values(status=CustomerStatus.INACTIVE)

        db_session.execute(stmt)
        db_session.flush()

        end_time = time.time()

        # Log performance
        elapsed = end_time - start_time
        print(f"\nBulk updated {num_customers} customers in {elapsed:.4f} seconds")

        # Verify all customers were updated
        count = db_session.query(Customer).filter(
            Customer.email.like('update%@example.com'),
            Customer.status == CustomerStatus.INACTIVE
        ).count()

        assert count == num_customers, f"Should have updated {num_customers} customers"


class TestComplexQueries:
    """Test complex queries involving multiple models."""

    @pytest.fixture
    def complex_data(self, db_session):
        """Set up complex data for testing queries."""
        # Create suppliers
        supplier1 = Supplier(name="Supplier 1", contact_email="supplier1@example.com", status="ACTIVE")
        supplier2 = Supplier(name="Supplier 2", contact_email="supplier2@example.com", status="ACTIVE")
        db_session.add_all([supplier1, supplier2])
        db_session.flush()

        # Create materials
        materials = []
        for i in range(10):
            supplier_id = supplier1.id if i % 2 == 0 else supplier2.id
            material = Material(
                name=f"Material {i}",
                type=MaterialType.LEATHER if i % 3 == 0 else MaterialType.HARDWARE if i % 3 == 1 else MaterialType.THREAD,
                supplier_id=supplier_id
            )
            materials.append(material)

        db_session.add_all(materials)
        db_session.flush()

        # Create customers
        customers = [
            Customer(name="Complex Customer 1", email="complex1@example.com", status=CustomerStatus.ACTIVE),
            Customer(name="Complex Customer 2", email="complex2@example.com", status=CustomerStatus.ACTIVE)
        ]
        db_session.add_all(customers)
        db_session.flush()

        # Create products
        products = [
            Product(name="Complex Product 1", price=99.99),
            Product(name="Complex Product 2", price=149.99),
            Product(name="Complex Product 3", price=199.99)
        ]
        db_session.add_all(products)
        db_session.flush()

        # Create sales
        sales = []
        for i, customer in enumerate(customers):
            sale = Sales(
                customer_id=customer.id,
                total_amount=(i + 1) * 100.0,
                status=SaleStatus.COMPLETED if i % 2 == 0 else SaleStatus.IN_PRODUCTION,
                payment_status=PaymentStatus.PAID if i % 2 == 0 else PaymentStatus.PARTIALLY_PAID
            )
            sales.append(sale)

        db_session.add_all(sales)
        db_session.flush()

        # Create sales items
        sales_items = []
        for i, sale in enumerate(sales):
            for j, product in enumerate(products):
                sales_items.append(SalesItem(
                    sales_id=sale.id,
                    product_id=product.id,
                    quantity=j + 1,
                    price=product.price
                ))

        db_session.add_all(sales_items)
        db_session.flush()

        # Create projects
        projects = []
        for i, sale in enumerate(sales):
            project = Project(
                name=f"Complex Project {i}",
                description=f"Complex project {i} description",
                type=ProjectType.WALLET if i % 2 == 0 else ProjectType.BELT,
                status=ProjectStatus.DESIGN_PHASE if i % 3 == 0 else
                ProjectStatus.MATERIAL_SELECTION if i % 3 == 1 else
                ProjectStatus.IN_PRODUCTION,
                sales_id=sale.id
            )
            projects.append(project)

        db_session.add_all(projects)
        db_session.flush()

        # Create components
        components = []
        for i in range(5):
            component = Component(
                name=f"Complex Component {i}",
                type=ComponentType.LEATHER if i % 2 == 0 else ComponentType.HARDWARE
            )
            components.append(component)

        db_session.add_all(components)
        db_session.flush()

        # Create project components
        project_components = []
        for project in projects:
            for i, component in enumerate(components):
                if i % 2 == (projects.index(project) % 2):  # Only add some components to each project
                    project_components.append(ProjectComponent(
                        project_id=project.id,
                        component_id=component.id,
                        quantity=i + 1
                    ))

        db_session.add_all(project_components)
        db_session.commit()

        return {
            "suppliers": [supplier1, supplier2],
            "materials": materials,
            "customers": customers,
            "products": products,
            "sales": sales,
            "sales_items": sales_items,
            "projects": projects,
            "components": components,
            "project_components": project_components
        }

    def test_join_and_aggregate_query(self, db_session, complex_data):
        """Test a complex join and aggregate query."""
        # Query: Get total sales amount by customer with their project count
        start_time = time.time()

        results = db_session.query(
            Customer.name.label('customer_name'),
            func.sum(Sales.total_amount).label('total_sales'),
            func.count(Project.id).label('project_count')
        ).join(
            Sales, Sales.customer_id == Customer.id
        ).outerjoin(
            Project, Project.sales_id == Sales.id
        ).group_by(
            Customer.id
        ).order_by(
            func.sum(Sales.total_amount).desc()
        ).all()

        end_time = time.time()

        # Log performance
        elapsed = end_time - start_time
        print(f"\nComplex join and aggregate query executed in {elapsed:.4f} seconds")

        # Verify results
        assert len(results) > 0, "Should have at least one result"

        # Log results
        for result in results:
            print(f"Customer: {result.customer_name}, "
                  f"Total Sales: ${result.total_sales}, "
                  f"Project Count: {result.project_count}")

    def test_nested_subquery(self, db_session, complex_data):
        """Test a query with nested subqueries."""
        # Query: Find customers who have purchased products with components containing leather
        start_time = time.time()

        from sqlalchemy import select, distinct

        # Subquery to find projects with leather components
        leather_components = select(distinct(ProjectComponent.project_id)).where(
            ProjectComponent.component_id.in_(
                select(Component.id).where(Component.type == ComponentType.LEATHER)
            )
        ).scalar_subquery()

        # Subquery to find sales with leather projects
        sales_with_leather = select(distinct(Project.sales_id)).where(
            Project.id.in_(leather_components)
        ).scalar_subquery()

        # Main query to find customers
        customers = db_session.query(Customer).join(
            Sales, Sales.customer_id == Customer.id
        ).filter(
            Sales.id.in_(sales_with_leather)
        ).distinct().all()

        end_time = time.time()

        # Log performance
        elapsed = end_time - start_time
        print(f"\nNested subquery executed in {elapsed:.4f} seconds")

        # Verify results
        print(f"Found {len(customers)} customers who purchased products with leather components")
        for customer in customers:
            print(f"Customer: {customer.name}, Email: {customer.email}")

    def test_eager_loading(self, db_session, complex_data):
        """Test eager loading with joined and subquery loads."""
        # Query: Get all projects with their components using eager loading

        # First without eager loading (N+1 problem)
        start_time = time.time()

        projects = db_session.query(Project).all()

        # Force loading of relationships (would normally happen in view/controller)
        component_count = 0
        for project in projects:
            # This causes additional queries when accessed
            project_components = db_session.query(ProjectComponent).filter_by(project_id=project.id).all()
            component_count += len(project_components)

        end_time = time.time()

        # Log performance
        without_eager_time = end_time - start_time
        print(f"\nQuery without eager loading: {without_eager_time:.4f} seconds")

        # Now with eager loading
        start_time = time.time()

        eager_projects = db_session.query(Project).options(
            joinedload(Project.project_components)
        ).all()

        # Force loading of relationships (all data already loaded)
        eager_component_count = 0
        for project in eager_projects:
            # This doesn't cause additional queries due to eager loading
            if hasattr(project, 'project_components'):
                eager_component_count += len(project.project_components)

        end_time = time.time()

        # Log performance
        with_eager_time = end_time - start_time
        print(f"Query with eager loading: {with_eager_time:.4f} seconds")
        print(f"Performance improvement: {(without_eager_time - with_eager_time) / without_eager_time * 100:.2f}%")

        # Verify results are the same
        assert component_count == eager_component_count, "Both queries should return the same number of components"


class TestEdgeCases:
    """Test edge cases in model behavior."""

    def test_large_string_fields(self, db_session):
        """Test saving and retrieving large string fields."""
        # Create a large string
        large_string = "A" * 10000  # 10KB string

        # Create a project with a large description
        project = Project(
            name="Large String Project",
            description=large_string,  # Large description
            type=ProjectType.WALLET,
            status=ProjectStatus.DESIGN_PHASE
        )

        db_session.add(project)
        db_session.flush()

        # Retrieve project and verify large string is intact
        saved_project = db_session.query(Project).filter_by(name="Large String Project").first()
        assert len(saved_project.description) == 10000, "Large string should be saved and retrieved correctly"

    def test_handling_of_special_characters(self, db_session):
        """Test handling of special characters in string fields."""
        # Test with various special characters
        special_chars = "!@#$%^&*()_+{}|:\"<>?[];',./`~§±²³½¾¿€£¥©®™°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞß"

        # Create a customer with special characters
        customer = Customer(
            name=f"Special{special_chars}",
            email="special@example.com",
            status=CustomerStatus.ACTIVE,
            notes=f"Notes with special characters: {special_chars}"
        )

        db_session.add(customer)
        db_session.flush()

        # Retrieve customer and verify special characters are intact
        saved_customer = db_session.query(Customer).filter_by(email="special@example.com").first()
        assert special_chars in saved_customer.name, "Special characters in name should be preserved"
        assert special_chars in saved_customer.notes, "Special characters in notes should be preserved"

    def test_uuid_generation(self, db_session):
        """Test UUID generation for models."""
        # Create several models and check their UUIDs
        customer = Customer(
            name="UUID Test Customer",
            email="uuid@example.com",
            status=CustomerStatus.ACTIVE
        )

        product = Product(
            name="UUID Test Product",
            price=99.99
        )

        project = Project(
            name="UUID Test Project",
            description="Testing UUID generation",
            type=ProjectType.WALLET,
            status=ProjectStatus.DESIGN_PHASE
        )

        db_session.add_all([customer, product, project])
        db_session.flush()

        # Check that UUIDs were generated and are unique
        assert customer.uuid is not None, "Customer should have a UUID"
        assert product.uuid is not None, "Product should have a UUID"
        assert project.uuid is not None, "Project should have a UUID"

        assert customer.uuid != product.uuid, "UUIDs should be unique across models"
        assert product.uuid != project.uuid, "UUIDs should be unique across models"
        assert customer.uuid != project.uuid, "UUIDs should be unique across models"

        # Check UUID format (should be a valid UUID string)
        import uuid
        try:
            uuid.UUID(customer.uuid)
            uuid.UUID(product.uuid)
            uuid.UUID(project.uuid)
        except ValueError:
            assert False, "UUIDs should be in valid UUID format"


class TestCircularReferenceHandling:
    """Test handling of circular references between models."""

    def test_circular_reference_between_sales_and_project(self, db_session, sample_data):
        """Test handling of circular reference between Sales and Project."""
        # Create a customer
        customer = Customer(
            name="Circular Reference Customer",
            email="circular@example.com",
            status=CustomerStatus.ACTIVE
        )
        db_session.add(customer)
        db_session.flush()

        # Create a sale
        sale = Sales(
            customer_id=customer.id,
            total_amount=299.99,
            status=SaleStatus.DESIGN_CONSULTATION,
            payment_status=PaymentStatus.PENDING
        )
        db_session.add(sale)
        db_session.flush()

        # Create a project referencing the sale
        project = Project(
            name="Circular Reference Project",
            description="Testing circular references",
            type=ProjectType.WALLET,
            status=ProjectStatus.INITIAL_CONSULTATION,
            sales_id=sale.id  # Reference to sale
        )
        db_session.add(project)
        db_session.flush()

        # Update sale to reference the project
        # This creates a circular reference: Sale -> Project -> Sale
        sale.project_id = project.id
        db_session.flush()

        # Verify the circular reference works
        saved_sale = db_session.query(Sales).filter_by(id=sale.id).first()
        saved_project = db_session.query(Project).filter_by(id=project.id).first()

        # Check references in both directions
        assert saved_sale.project_id == project.id, "Sale should reference Project"
        assert saved_project.sales_id == sale.id, "Project should reference Sale"

        # Test navigating the relationship in both directions
        # From sale to project
        if hasattr(saved_sale, 'project'):
            assert saved_sale.project.id == project.id, "Sale.project should point to the correct Project"

        # From project to sale
        if hasattr(saved_project, 'sale') or hasattr(saved_project, 'sales'):
            sale_attr = 'sale' if hasattr(saved_project, 'sale') else 'sales'
            assert getattr(saved_project,
                           sale_attr).id == sale.id, f"Project.{sale_attr} should point to the correct Sale"