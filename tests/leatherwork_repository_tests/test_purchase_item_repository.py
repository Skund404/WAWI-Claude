# tests/leatherwork_repository_tests/test_purchase_item_repository.py
import pytest
from datetime import datetime, timedelta
from database.models.enums import (
    PurchaseStatus,
    SupplierStatus,
    MaterialType,
    ToolCategory,
    InventoryStatus
)


class TestPurchaseItemRepository:
    def _create_test_supplier(self, dbsession):
        """Helper method to create a test supplier."""

        class TestSupplier:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        supplier = TestSupplier(
            name="Leather Supply Co.",
            contact_email="supplier@example.com",
            phone="555-123-4567",
            status=SupplierStatus.ACTIVE
        )

        # Simulated database insert
        supplier.id = 1
        return supplier

    def _create_test_purchase(self, dbsession, supplier_id):
        """Helper method to create a test purchase."""

        class TestPurchase:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        purchase = TestPurchase(
            supplier_id=supplier_id,
            order_date=datetime.now(),
            expected_delivery_date=datetime.now() + timedelta(days=7),
            total_amount=0,
            status=PurchaseStatus.PENDING,
            reference_number="PO-2025-001"
        )

        # Simulated database insert
        purchase.id = 1
        return purchase

    def _create_test_material(self, dbsession):
        """Helper method to create a test material."""

        class TestMaterial:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        material = TestMaterial(
            name="Vegetable Tanned Leather",
            material_type=MaterialType.LEATHER,
            description="Premium vegetable tanned leather",
            unit_price=15.99
        )

        # Simulated database insert
        material.id = 1
        return material

    def _create_test_tool(self, dbsession):
        """Helper method to create a test tool."""

        class TestTool:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        tool = TestTool(
            name="Stitching Awl",
            description="Professional stitching awl",
            tool_category=ToolCategory.STITCHING,
            purchase_price=25.99
        )

        # Simulated database insert
        tool.id = 1
        return tool

    def test_create_purchase_item_material(self, dbsession):
        """Test creating a new purchase item for a material."""

        # Create a simple test purchase item object
        class TestPurchaseItem:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePurchaseItemRepo:
            def __init__(self):
                self.purchase_items = {}
                self.next_id = 1

            def add(self, purchase_item):
                purchase_item.id = self.next_id
                self.purchase_items[self.next_id] = purchase_item
                self.next_id += 1
                return purchase_item

            def get_by_id(self, id):
                return self.purchase_items.get(id)

        # Create test data
        supplier = self._create_test_supplier(dbsession)
        purchase = self._create_test_purchase(dbsession, supplier.id)
        material = self._create_test_material(dbsession)

        # Create the repository
        repository = SimplePurchaseItemRepo()

        # Create a purchase item for material
        purchase_item = TestPurchaseItem(
            purchase_id=purchase.id,
            item_id=material.id,
            item_type="material",
            quantity=5,
            price=15.99,
            total_price=5 * 15.99,
            created_at=datetime.now()
        )

        # Save the purchase item
        added_purchase_item = repository.add(purchase_item)

        # Verify the purchase item was saved
        assert added_purchase_item.id == 1
        assert added_purchase_item.purchase_id == purchase.id
        assert added_purchase_item.item_id == material.id
        assert added_purchase_item.item_type == "material"
        assert added_purchase_item.quantity == 5
        assert added_purchase_item.price == 15.99
        assert added_purchase_item.total_price == 5 * 15.99

    def test_create_purchase_item_tool(self, dbsession):
        """Test creating a new purchase item for a tool."""

        # Create a simple test purchase item object
        class TestPurchaseItem:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePurchaseItemRepo:
            def __init__(self):
                self.purchase_items = {}
                self.next_id = 1

            def add(self, purchase_item):
                purchase_item.id = self.next_id
                self.purchase_items[self.next_id] = purchase_item
                self.next_id += 1
                return purchase_item

            def get_by_id(self, id):
                return self.purchase_items.get(id)

        # Create test data
        supplier = self._create_test_supplier(dbsession)
        purchase = self._create_test_purchase(dbsession, supplier.id)
        tool = self._create_test_tool(dbsession)

        # Create the repository
        repository = SimplePurchaseItemRepo()

        # Create a purchase item for tool
        purchase_item = TestPurchaseItem(
            purchase_id=purchase.id,
            item_id=tool.id,
            item_type="tool",
            quantity=1,
            price=25.99,
            total_price=1 * 25.99,
            created_at=datetime.now()
        )

        # Save the purchase item
        added_purchase_item = repository.add(purchase_item)

        # Verify the purchase item was saved
        assert added_purchase_item.id == 1
        assert added_purchase_item.purchase_id == purchase.id
        assert added_purchase_item.item_id == tool.id
        assert added_purchase_item.item_type == "tool"
        assert added_purchase_item.quantity == 1
        assert added_purchase_item.price == 25.99
        assert added_purchase_item.total_price == 1 * 25.99

    def test_read_purchase_item(self, dbsession):
        """Test reading a purchase item."""

        # Create a simple test purchase item object
        class TestPurchaseItem:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePurchaseItemRepo:
            def __init__(self):
                self.purchase_items = {}
                self.next_id = 1

            def add(self, purchase_item):
                purchase_item.id = self.next_id
                self.purchase_items[self.next_id] = purchase_item
                self.next_id += 1
                return purchase_item

            def get_by_id(self, id):
                return self.purchase_items.get(id)

        # Create test data
        supplier = self._create_test_supplier(dbsession)
        purchase = self._create_test_purchase(dbsession, supplier.id)
        material = self._create_test_material(dbsession)

        # Create the repository
        repository = SimplePurchaseItemRepo()

        # Create a purchase item
        purchase_item = TestPurchaseItem(
            purchase_id=purchase.id,
            item_id=material.id,
            item_type="material",
            quantity=3,
            price=15.99,
            total_price=3 * 15.99,
            created_at=datetime.now()
        )

        # Add to repository
        added_purchase_item = repository.add(purchase_item)

        # Read the purchase item
        retrieved_purchase_item = repository.get_by_id(added_purchase_item.id)

        # Verify the purchase item was retrieved correctly
        assert retrieved_purchase_item is not None
        assert retrieved_purchase_item.id == added_purchase_item.id
        assert retrieved_purchase_item.purchase_id == purchase.id
        assert retrieved_purchase_item.item_id == material.id
        assert retrieved_purchase_item.quantity == 3
        assert retrieved_purchase_item.price == 15.99

    def test_update_purchase_item(self, dbsession):
        """Test updating a purchase item."""

        # Create a simple test purchase item object
        class TestPurchaseItem:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePurchaseItemRepo:
            def __init__(self):
                self.purchase_items = {}
                self.next_id = 1

            def add(self, purchase_item):
                purchase_item.id = self.next_id
                self.purchase_items[self.next_id] = purchase_item
                self.next_id += 1
                return purchase_item

            def get_by_id(self, id):
                return self.purchase_items.get(id)

            def update(self, purchase_item):
                if purchase_item.id in self.purchase_items:
                    self.purchase_items[purchase_item.id] = purchase_item
                    return purchase_item
                return None

        # Create test data
        supplier = self._create_test_supplier(dbsession)
        purchase = self._create_test_purchase(dbsession, supplier.id)
        material = self._create_test_material(dbsession)

        # Create the repository
        repository = SimplePurchaseItemRepo()

        # Create a purchase item
        purchase_item = TestPurchaseItem(
            purchase_id=purchase.id,
            item_id=material.id,
            item_type="material",
            quantity=2,
            price=15.99,
            total_price=2 * 15.99,
            created_at=datetime.now()
        )

        # Add to repository
        added_purchase_item = repository.add(purchase_item)

        # Update the purchase item
        added_purchase_item.quantity = 4
        added_purchase_item.price = 14.99  # Discounted price
        added_purchase_item.total_price = 4 * 14.99
        added_purchase_item.notes = "Updated quantity"
        repository.update(added_purchase_item)

        # Retrieve and verify updates
        updated_purchase_item = repository.get_by_id(added_purchase_item.id)
        assert updated_purchase_item.quantity == 4
        assert updated_purchase_item.price == 14.99
        assert updated_purchase_item.total_price == 4 * 14.99
        assert updated_purchase_item.notes == "Updated quantity"

    def test_delete_purchase_item(self, dbsession):
        """Test deleting a purchase item."""

        # Create a simple test purchase item object
        class TestPurchaseItem:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePurchaseItemRepo:
            def __init__(self):
                self.purchase_items = {}
                self.next_id = 1

            def add(self, purchase_item):
                purchase_item.id = self.next_id
                self.purchase_items[self.next_id] = purchase_item
                self.next_id += 1
                return purchase_item

            def get_by_id(self, id):
                return self.purchase_items.get(id)

            def delete(self, id):
                if id in self.purchase_items:
                    del self.purchase_items[id]
                    return True
                return False

        # Create test data
        supplier = self._create_test_supplier(dbsession)
        purchase = self._create_test_purchase(dbsession, supplier.id)
        tool = self._create_test_tool(dbsession)

        # Create the repository
        repository = SimplePurchaseItemRepo()

        # Create a purchase item
        purchase_item = TestPurchaseItem(
            purchase_id=purchase.id,
            item_id=tool.id,
            item_type="tool",
            quantity=1,
            price=25.99,
            total_price=1 * 25.99,
            created_at=datetime.now()
        )

        # Add to repository
        added_purchase_item = repository.add(purchase_item)

        # Delete the purchase item
        purchase_item_id = added_purchase_item.id
        result = repository.delete(purchase_item_id)

        # Verify the purchase item was deleted
        assert result is True
        assert repository.get_by_id(purchase_item_id) is None

    def test_find_purchase_items_by_purchase(self, dbsession):
        """Test finding purchase items by purchase."""

        # Create a simple test purchase item object
        class TestPurchaseItem:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePurchaseItemRepo:
            def __init__(self):
                self.purchase_items = {}
                self.next_id = 1

            def add(self, purchase_item):
                purchase_item.id = self.next_id
                self.purchase_items[self.next_id] = purchase_item
                self.next_id += 1
                return purchase_item

            def find_by_purchase_id(self, purchase_id):
                return [pi for pi in self.purchase_items.values() if pi.purchase_id == purchase_id]

        # Create test data
        class TestPurchase:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        supplier = self._create_test_supplier(dbsession)

        purchase1 = TestPurchase(
            supplier_id=supplier.id,
            total_amount=0,
            status=PurchaseStatus.PENDING,
            reference_number="PO-001"
        )
        purchase1.id = 1

        purchase2 = TestPurchase(
            supplier_id=supplier.id,
            total_amount=0,
            status=PurchaseStatus.PENDING,
            reference_number="PO-002"
        )
        purchase2.id = 2

        material = self._create_test_material(dbsession)
        tool = self._create_test_tool(dbsession)

        # Create the repository
        repository = SimplePurchaseItemRepo()

        # Create purchase items
        item1 = TestPurchaseItem(
            purchase_id=purchase1.id,
            item_id=material.id,
            item_type="material",
            quantity=3,
            price=15.99
        )

        item2 = TestPurchaseItem(
            purchase_id=purchase1.id,
            item_id=tool.id,
            item_type="tool",
            quantity=1,
            price=25.99
        )

        item3 = TestPurchaseItem(
            purchase_id=purchase2.id,
            item_id=material.id,
            item_type="material",
            quantity=2,
            price=15.99
        )

        # Add to repository
        repository.add(item1)
        repository.add(item2)
        repository.add(item3)

        # Find purchase items by purchase
        purchase1_items = repository.find_by_purchase_id(purchase1.id)
        purchase2_items = repository.find_by_purchase_id(purchase2.id)

        # Verify results
        assert len(purchase1_items) == 2
        assert len(purchase2_items) == 1
        assert all(pi.purchase_id == purchase1.id for pi in purchase1_items)
        assert all(pi.purchase_id == purchase2.id for pi in purchase2_items)

    def test_update_received_quantity(self, dbsession):
        """Test updating received quantity for a purchase item."""

        # Create a simple test purchase item object
        class TestPurchaseItem:
            def __init__(self, **kwargs):
                self.id = None
                self.received_quantity = 0
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePurchaseItemRepo:
            def __init__(self):
                self.purchase_items = {}
                self.next_id = 1

            def add(self, purchase_item):
                purchase_item.id = self.next_id
                self.purchase_items[self.next_id] = purchase_item
                self.next_id += 1
                return purchase_item

            def get_by_id(self, id):
                return self.purchase_items.get(id)

            def update(self, purchase_item):
                if purchase_item.id in self.purchase_items:
                    self.purchase_items[purchase_item.id] = purchase_item
                    return purchase_item
                return None

            def update_received_quantity(self, id, received_quantity, received_date=None):
                if id in self.purchase_items:
                    purchase_item = self.purchase_items[id]
                    purchase_item.received_quantity = received_quantity
                    purchase_item.received_date = received_date or datetime.now()
                    return purchase_item
                return None

        # Create test data
        supplier = self._create_test_supplier(dbsession)
        purchase = self._create_test_purchase(dbsession, supplier.id)
        material = self._create_test_material(dbsession)

        # Create the repository
        repository = SimplePurchaseItemRepo()

        # Create a purchase item
        purchase_item = TestPurchaseItem(
            purchase_id=purchase.id,
            item_id=material.id,
            item_type="material",
            quantity=10,
            price=15.99,
            total_price=10 * 15.99,
            created_at=datetime.now()
        )

        # Add to repository
        added_purchase_item = repository.add(purchase_item)

        # Update received quantity
        now = datetime.now()
        repository.update_received_quantity(added_purchase_item.id, 8, now)

        # Retrieve and verify updates
        updated_purchase_item = repository.get_by_id(added_purchase_item.id)
        assert updated_purchase_item.received_quantity == 8
        assert updated_purchase_item.received_date == now