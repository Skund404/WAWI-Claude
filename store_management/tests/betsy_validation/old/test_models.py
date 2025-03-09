# tests/test_models.py
"""
Comprehensive test suite for validating database models against the ER diagram,
testing relationships, and identifying potential bugs in the model system.
"""

import unittest
import datetime
import uuid
import logging
from typing import Dict, List, Type, Any, Set

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

# Import the base model and model registry
from database.models.base import Base, initialize_all_model_relationships

# Import all models to ensure they're registered
from database.models import (
    Customer, Sales, SalesItem, Product, ProductPattern, Purchase, PurchaseItem,
    Supplier, ProductInventory, MaterialInventory, LeatherInventory, HardwareInventory,
    ToolInventory, Project, Pattern, Component, material, Leather, Hardware, Tool,
    ComponentMaterial, ComponentLeather, ComponentHardware, ComponentTool,
    ProjectComponent, PickingList, PickingListItem, ToolList, ToolListItem
)
from database.models.enums import (
    SaleStatus, PaymentStatus, PurchaseStatus, CustomerStatus, CustomerTier,
    InventoryStatus, MaterialType, LeatherType, HardwareType, ProjectType, ProjectStatus,
    SkillLevel, ComponentType, MeasurementUnit, QualityGrade
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelTestCase(unittest.TestCase):
    """Base test case for model testing with common setup."""

    @classmethod
    def setUpClass(cls):
        """Set up in-memory database and session factory."""
        # Create in-memory SQLite database
        cls.engine = create_engine('sqlite:///:memory:', echo=False)
        cls.SessionFactory = sessionmaker(bind=cls.engine)

        # Create all tables
        Base.metadata.create_all(cls.engine)

        # Initialize relationships
        initialize_all_model_relationships()

        # Log registered models
        logger.info(f"Registered models: {', '.join(Base.list_models())}")

    def setUp(self):
        """Create a new session for each test."""
        self.session = self.SessionFactory()

    def tearDown(self):
        """Close session after each test."""
        self.session.close()


class ERDiagramValidationTest(ModelTestCase):
    """Tests to validate models against the ER diagram structure."""

    def test_all_entities_exist(self):
        """Verify that all entities from ER diagram exist as models."""
        expected_entities = {
            'Customer', 'Sales', 'SalesItem', 'Product', 'ProductPattern',
            'Purchase', 'PurchaseItem', 'Supplier', 'ProductInventory',
            'MaterialInventory', 'LeatherInventory', 'HardwareInventory',
            'ToolInventory', 'Project', 'Pattern', 'Component', 'Material',
            'Leather', 'Hardware', 'Tool', 'ComponentMaterial',
            'ComponentLeather', 'ComponentHardware', 'ComponentTool',
            'ProjectComponent', 'PickingList', 'PickingListItem',
            'ToolList', 'ToolListItem'
        }

        # Get actual models registered
        actual_models = set(Base.list_models())

        # Check for missing entities
        missing_entities = expected_entities - actual_models
        unexpected_entities = actual_models - expected_entities - {'Base'}

        self.assertEqual(missing_entities, set(), f"Missing entities: {missing_entities}")
        self.assertEqual(unexpected_entities, set(), f"Unexpected entities: {unexpected_entities}")

    def test_entity_primary_keys(self):
        """Verify that all entities have primary keys as per ER diagram."""
        for model_name in Base.list_models():
            model_class = Base.get_model(model_name)
            if model_class:
                # Get primary key columns
                pk_columns = [key.name for key in inspect(model_class).primary_key]

                # Every model should have at least one primary key
                self.assertGreaterEqual(len(pk_columns), 1,
                                        f"{model_name} should have at least one primary key")

                # For junction tables, check for composite keys
                if model_name in ['ComponentMaterial', 'ComponentLeather',
                                  'ComponentHardware', 'ComponentTool']:
                    self.assertGreaterEqual(len(pk_columns), 2,
                                            f"Junction table {model_name} should have a composite primary key")

    def _get_foreign_keys(self, model_class):
        """Helper method to get foreign keys for a model."""
        inspector = inspect(self.engine)
        fks = []

        if hasattr(model_class, '__tablename__'):
            for fk in inspector.get_foreign_keys(model_class.__tablename__):
                fks.append({
                    'constrained_columns': fk['constrained_columns'],
                    'referred_table': fk['referred_table'],
                    'referred_columns': fk['referred_columns']
                })

        return fks

    def test_entity_relationships(self):
        """Test that entity relationships match the ER diagram."""
        # Define expected relationships based on ER diagram
        expected_relationships = {
            'Sales': ['Customer', 'PickingList', 'Project'],
            'SalesItem': ['Sales', 'Product'],
            'Product': ['ProductPattern', 'ProductInventory', 'SalesItem'],
            'ProjectComponent': ['Project', 'Component', 'PickingListItem'],
            'PickingList': ['Sales', 'PickingListItem'],
            'Project': ['Sales', 'ProjectComponent', 'ToolList']
            # Add more expected relationships as needed
        }

        for model_name, related_models in expected_relationships.items():
            model_class = Base.get_model(model_name)
            if not model_class:
                self.fail(f"Model {model_name} not found")
                continue

            # Get foreign keys
            fks = self._get_foreign_keys(model_class)

            # Get relationship attribute names
            relationships = inspect(model_class).relationships.keys()

            # Check for each expected relationship
            for related_model in related_models:
                # Check if there's a relationship with this name or a foreign key to this table
                related_table = Base.get_model(related_model).__tablename__ if Base.get_model(related_model) else None

                relationship_exists = False

                # Check in relationships
                for rel_name in relationships:
                    if rel_name.lower() == related_model.lower() or rel_name.endswith('_' + related_model.lower()):
                        relationship_exists = True
                        break

                # Check in foreign keys
                for fk in fks:
                    if fk['referred_table'] == related_table:
                        relationship_exists = True
                        break

                self.assertTrue(relationship_exists,
                                f"{model_name} should have a relationship with {related_model}")


class ModelCreationTest(ModelTestCase):
    """Tests to ensure models can be instantiated and saved to the database."""

    def test_create_customer(self):
        """Test creating and saving a Customer model."""
        customer = Customer(
            name="Test Customer",
            email="test@example.com",
            status=CustomerStatus.ACTIVE,
            tier=CustomerTier.STANDARD
        )

        self.session.add(customer)
        self.session.commit()

        # Verify the customer was saved
        saved_customer = self.session.query(Customer).filter_by(email="test@example.com").first()
        self.assertIsNotNone(saved_customer)
        self.assertEqual(saved_customer.name, "Test Customer")

    def test_create_sales_with_items(self):
        """Test creating Sales with SalesItems."""
        # Create a customer first
        customer = Customer(
            name="Sales Test Customer",
            email="sales@example.com",
            status=CustomerStatus.ACTIVE
        )
        self.session.add(customer)
        self.session.flush()

        # Create a product
        product = Product(
            name="Test Product",
            price=99.99
        )
        self.session.add(product)
        self.session.flush()

        # Create a sale
        sale = Sales(
            customer_id=customer.id,
            total_amount=99.99,
            status=SaleStatus.COMPLETED,
            payment_status=PaymentStatus.PAID
        )
        self.session.add(sale)
        self.session.flush()

        # Create a sales item
        sales_item = SalesItem(
            sales_id=sale.id,
            product_id=product.id,
            quantity=1,
            price=99.99
        )
        self.session.add(sales_item)
        self.session.commit()

        # Verify the sales and items were created
        saved_sale = self.session.query(Sales).filter_by(customer_id=customer.id).first()
        self.assertIsNotNone(saved_sale)

        saved_items = self.session.query(SalesItem).filter_by(sales_id=saved_sale.id).all()
        self.assertEqual(len(saved_items), 1)
        self.assertEqual(saved_items[0].price, 99.99)

    def test_create_project_with_components(self):
        """Test creating a Project with Components."""
        # Create a pattern
        pattern = Pattern(
            name="Test Pattern",
            description="A test pattern",
            skill_level=SkillLevel.INTERMEDIATE
        )
        self.session.add(pattern)
        self.session.flush()

        # Create a component
        component = Component(
            name="Test Component",
            type=ComponentType.LEATHER
        )
        self.session.add(component)
        self.session.flush()

        # Create a project
        project = Project(
            name="Test Project",
            description="A test project",
            type=ProjectType.WALLET,
            status=ProjectStatus.DESIGN_PHASE,
            start_date=datetime.datetime.utcnow()
        )
        self.session.add(project)
        self.session.flush()

        # Connect project and component
        project_component = ProjectComponent(
            project_id=project.id,
            component_id=component.id,
            quantity=1
        )
        self.session.add(project_component)
        self.session.commit()

        # Verify the project and components were created
        saved_project = self.session.query(Project).filter_by(name="Test Project").first()
        self.assertIsNotNone(saved_project)

        saved_components = self.session.query(ProjectComponent).filter_by(project_id=saved_project.id).all()
        self.assertEqual(len(saved_components), 1)
        self.assertEqual(saved_components[0].component_id, component.id)


class ModelRelationshipTest(ModelTestCase):
    """Tests to verify relationships between models work as expected."""

    def test_customer_sales_relationship(self):
        """Test the relationship between Customer and Sales."""
        # Create a customer
        customer = Customer(
            name="Relationship Test Customer",
            email="relationship@example.com",
            status=CustomerStatus.ACTIVE
        )
        self.session.add(customer)
        self.session.flush()

        # Create multiple sales for the customer
        sale1 = Sales(
            customer_id=customer.id,
            total_amount=199.99,
            status=SaleStatus.COMPLETED,
            payment_status=PaymentStatus.PAID
        )
        sale2 = Sales(
            customer_id=customer.id,
            total_amount=299.99,
            status=SaleStatus.IN_PRODUCTION,
            payment_status=PaymentStatus.PARTIALLY_PAID
        )

        self.session.add_all([sale1, sale2])
        self.session.commit()

        # Query customer and check sales relationship
        saved_customer = self.session.query(Customer).filter_by(email="relationship@example.com").first()

        # Check if the relationship attribute exists
        self.assertTrue(hasattr(saved_customer, 'sales_records') or hasattr(saved_customer, 'sales'),
                        "Customer should have a relationship to Sales")

        # If it's 'sales_records'
        if hasattr(saved_customer, 'sales_records'):
            sales = saved_customer.sales_records
            self.assertEqual(len(sales), 2, "Customer should have 2 sales")
        # If it's 'sales'
        elif hasattr(saved_customer, 'sales'):
            sales = saved_customer.sales
            self.assertEqual(len(sales), 2, "Customer should have 2 sales")

        # Query sales and check customer relationship
        saved_sale = self.session.query(Sales).filter_by(id=sale1.id).first()

        # Check if the relationship attribute exists
        self.assertTrue(hasattr(saved_sale, 'customer'),
                        "Sales should have a relationship to Customer")

        if hasattr(saved_sale, 'customer'):
            self.assertEqual(saved_sale.customer.id, customer.id,
                             "Sales should be linked to the correct customer")

    def test_picking_list_items_relationship(self):
        """Test the relationship between PickingList and PickingListItems."""
        # Create a picking list
        picking_list = PickingList(
            status="pending"
        )
        self.session.add(picking_list)
        self.session.flush()

        # Create a material for the picking list item
        material = Material(
            name="Test Material",
            type=MaterialType.LEATHER
        )
        self.session.add(material)
        self.session.flush()

        # Create picking list items
        item1 = PickingListItem(
            picking_list_id=picking_list.id,
            material_id=material.id,
            quantity_ordered=5,
            quantity_picked=0
        )
        item2 = PickingListItem(
            picking_list_id=picking_list.id,
            material_id=material.id,
            quantity_ordered=3,
            quantity_picked=2
        )

        self.session.add_all([item1, item2])
        self.session.commit()

        # Query picking list and check items relationship
        saved_picking_list = self.session.query(PickingList).filter_by(id=picking_list.id).first()

        # Check if the relationship attribute exists
        self.assertTrue(hasattr(saved_picking_list, 'items') or hasattr(saved_picking_list, 'picking_list_items'),
                        "PickingList should have a relationship to PickingListItem")

        # Check items count
        items_attr = 'items' if hasattr(saved_picking_list, 'items') else 'picking_list_items' if hasattr(
            saved_picking_list, 'picking_list_items') else None
        if items_attr:
            items = getattr(saved_picking_list, items_attr)
            self.assertEqual(len(items), 2, "PickingList should have 2 items")

        # Query item and check picking list relationship
        saved_item = self.session.query(PickingListItem).filter_by(id=item1.id).first()

        # Check if the relationship attribute exists
        self.assertTrue(hasattr(saved_item, 'picking_list'),
                        "PickingListItem should have a relationship to PickingList")

        if hasattr(saved_item, 'picking_list'):
            self.assertEqual(saved_item.picking_list.id, picking_list.id,
                             "PickingListItem should be linked to the correct PickingList")


class PolymorphicRelationshipTest(ModelTestCase):
    """Tests for polymorphic relationships and complex inheritance structures."""

    def test_component_material_relationships(self):
        """Test relationships between components and materials."""
        # Create materials
        leather = Leather(
            name="Test Leather",
            type=LeatherType.FULL_GRAIN,
            quality=QualityGrade.PREMIUM
        )

        hardware = Hardware(
            name="Test Hardware",
            type=HardwareType.BUCKLE
        )

        # Create a component
        component = Component(
            name="Mixed Component",
            type=ComponentType.LEATHER
        )

        self.session.add_all([leather, hardware, component])
        self.session.flush()

        # Create relationships
        comp_leather = ComponentLeather(
            component_id=component.id,
            leather_id=leather.id,
            quantity=1.5
        )

        comp_hardware = ComponentHardware(
            component_id=component.id,
            hardware_id=hardware.id,
            quantity=4
        )

        self.session.add_all([comp_leather, comp_hardware])
        self.session.commit()

        # Verify relationships
        # Check if component has leathers
        saved_component = self.session.query(Component).filter_by(id=component.id).first()

        # Check leather relationship
        leather_relationship = self.session.query(ComponentLeather).filter_by(component_id=component.id).all()
        self.assertEqual(len(leather_relationship), 1, "Component should have 1 leather")
        self.assertEqual(leather_relationship[0].leather_id, leather.id)

        # Check hardware relationship
        hardware_relationship = self.session.query(ComponentHardware).filter_by(component_id=component.id).all()
        self.assertEqual(len(hardware_relationship), 1, "Component should have 1 hardware")
        self.assertEqual(hardware_relationship[0].hardware_id, hardware.id)


class ValidationMixinTest(ModelTestCase):
    """Tests for the ValidationMixin functionality."""

    def test_model_validation(self):
        """Test validation methods on models."""
        # Test with invalid email format
        with self.assertRaises(Exception):
            customer = Customer(
                name="Invalid Email Customer",
                email="not-an-email",  # Invalid email format
                status=CustomerStatus.ACTIVE
            )
            self.session.add(customer)
            self.session.commit()

        # Rollback after the error
        self.session.rollback()

        # Test with valid data
        customer = Customer(
            name="Valid Customer",
            email="valid@example.com",
            status=CustomerStatus.ACTIVE
        )
        self.session.add(customer)
        self.session.commit()

        saved_customer = self.session.query(Customer).filter_by(email="valid@example.com").first()
        self.assertIsNotNone(saved_customer)


class SoftDeleteTest(ModelTestCase):
    """Tests for soft delete functionality."""

    def test_soft_delete(self):
        """Test soft delete and restore functionality."""
        # Create a customer
        customer = Customer(
            name="Delete Test Customer",
            email="delete@example.com",
            status=CustomerStatus.ACTIVE
        )
        self.session.add(customer)
        self.session.commit()

        # Verify customer exists
        saved_customer = self.session.query(Customer).filter_by(email="delete@example.com").first()
        self.assertIsNotNone(saved_customer)
        self.assertFalse(saved_customer.is_deleted)

        # Soft delete the customer
        saved_customer.soft_delete()
        self.session.commit()

        # Verify customer is marked as deleted
        deleted_customer = self.session.query(Customer).filter_by(email="delete@example.com").first()
        self.assertTrue(deleted_customer.is_deleted)
        self.assertIsNotNone(deleted_customer.deleted_at)

        # Restore the customer
        deleted_customer.restore()
        self.session.commit()

        # Verify customer is restored
        restored_customer = self.session.query(Customer).filter_by(email="delete@example.com").first()
        self.assertFalse(restored_customer.is_deleted)
        self.assertIsNone(restored_customer.deleted_at)


class CircularImportTest(ModelTestCase):
    """Tests for circular import resolution."""

    def test_circular_import_resolution(self):
        """Test that circular imports are resolved correctly."""
        # Create a sales record
        customer = Customer(
            name="Circular Import Test",
            email="circular@example.com",
            status=CustomerStatus.ACTIVE
        )
        self.session.add(customer)
        self.session.flush()

        sale = Sales(
            customer_id=customer.id,
            total_amount=399.99,
            status=SaleStatus.COMPLETED,
            payment_status=PaymentStatus.PAID
        )
        self.session.add(sale)
        self.session.flush()

        # Create a project that references the sale
        project = Project(
            name="Circular Project",
            description="Testing circular imports",
            type=ProjectType.WALLET,
            status=ProjectStatus.DESIGN_PHASE,
            start_date=datetime.datetime.utcnow(),
            sales_id=sale.id
        )
        self.session.add(project)
        self.session.commit()

        # Test circular reference from sale to project
        saved_sale = self.session.query(Sales).filter_by(id=sale.id).first()

        # Check if the relationship attribute exists (may be 'project' or 'projects')
        has_project_attr = hasattr(saved_sale, 'project') or hasattr(saved_sale, 'projects')
        self.assertTrue(has_project_attr, "Sales should have a relationship to Project")

        # Check reference from project to sale
        saved_project = self.session.query(Project).filter_by(id=project.id).first()
        self.assertTrue(hasattr(saved_project, 'sale') or hasattr(saved_project, 'sales'),
                        "Project should have a relationship to Sales")

        if hasattr(saved_project, 'sale'):
            self.assertEqual(saved_project.sale.id, sale.id)
        elif hasattr(saved_project, 'sales'):
            self.assertEqual(saved_project.sales.id, sale.id)


class DictConversionTest(ModelTestCase):
    """Tests for to_dict functionality."""

    def test_to_dict(self):
        """Test converting models to dictionaries."""
        # Create a customer
        now = datetime.datetime.utcnow()
        customer = Customer(
            name="Dict Test Customer",
            email="dict@example.com",
            status=CustomerStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        self.session.add(customer)
        self.session.commit()

        # Convert to dict
        customer_dict = customer.to_dict()

        # Verify dict content
        self.assertEqual(customer_dict['name'], "Dict Test Customer")
        self.assertEqual(customer_dict['email'], "dict@example.com")
        self.assertEqual(customer_dict['status'], CustomerStatus.ACTIVE)

        # Test excluding fields
        customer_dict_excluded = customer.to_dict(exclude_fields=['created_at', 'updated_at'])
        self.assertNotIn('created_at', customer_dict_excluded)
        self.assertNotIn('updated_at', customer_dict_excluded)


if __name__ == '__main__':
    unittest.main()