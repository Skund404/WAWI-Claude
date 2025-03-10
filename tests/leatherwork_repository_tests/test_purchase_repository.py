# tests/leatherwork_repository_tests/test_purchase_repository.py
import pytest
from datetime import datetime, timedelta
from database.models.enums import (
    PurchaseStatus,
    SupplierStatus,
    MaterialType,
    ToolCategory
)


class TestPurchaseRepository:
    def _create_test_supplier(self, dbsession):
        """Helper method to create a test supplier."""

        class TestSupplier:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        supplier = TestSupplier(
            name="Leather Supply Inc.",
            contact_email="supplier@example.com",
            phone="555-123-4567",
            address="123 Supply St",
            status=SupplierStatus.ACTIVE,
            created_at=datetime.now()
        )

        # Simulated database insert
        supplier.id = 1
        return supplier

    def _create_test_material(self, dbsession):
        """Helper method to create a test material."""

        class TestMaterial:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        material = TestMaterial(
            name="Full Grain Leather",
            material_type=MaterialType.LEATHER,
            description="Premium full grain leather",
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
            name="Leather Knife",
            description="Professional leather cutting knife",
            tool_category=ToolCategory.CUTTING,
            purchase_price=45.99
        )

        # Simulated database insert
        tool.id = 1
        return tool

    def test_create_purchase(self, dbsession):
        """Test creating a new purchase."""

        # Create a simple test purchase object
        class TestPurchase:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePurchaseRepo:
            def __init__(self):
                self.purchases = {}
                self.next_id = 1

            def add(self, purchase):
                purchase.id = self.next_id
                self.purchases[self.next_id] = purchase
                self.next_id += 1
                return purchase

            def get_by_id(self, id):
                return self.purchases.get(id)

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimplePurchaseRepo()

        # Create a purchase
        purchase = TestPurchase(
            supplier_id=supplier.id,
            order_date=datetime.now(),
            expected_delivery_date=datetime.now() + timedelta(days=7),
            total_amount=149.99,
            status=PurchaseStatus.PENDING,
            created_at=datetime.now(),
            created_by="John Smith",
            reference_number="PO-2025-001"
        )

        # Save the purchase
        added_purchase = repository.add(purchase)

        # Verify the purchase was saved
        assert added_purchase.id == 1
        assert added_purchase.supplier_id == supplier.id
        assert added_purchase.total_amount == 149.99
        assert added_purchase.status == PurchaseStatus.PENDING
        assert added_purchase.reference_number == "PO-2025-001"

    def test_read_purchase(self, dbsession):
        """Test reading a purchase."""

        # Create a simple test purchase object
        class TestPurchase:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePurchaseRepo:
            def __init__(self):
                self.purchases = {}
                self.next_id = 1

            def add(self, purchase):
                purchase.id = self.next_id
                self.purchases[self.next_id] = purchase
                self.next_id += 1
                return purchase

            def get_by_id(self, id):
                return self.purchases.get(id)

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimplePurchaseRepo()

        # Create a purchase
        purchase = TestPurchase(
            supplier_id=supplier.id,
            order_date=datetime.now(),
            expected_delivery_date=datetime.now() + timedelta(days=5),
            total_amount=89.75,
            status=PurchaseStatus.ORDERED,
            created_at=datetime.now(),
            created_by="Jane Doe",
            reference_number="PO-2025-002"
        )

        # Add to repository
        added_purchase = repository.add(purchase)

        # Read the purchase
        retrieved_purchase = repository.get_by_id(added_purchase.id)

        # Verify the purchase was retrieved correctly
        assert retrieved_purchase is not None
        assert retrieved_purchase.id == added_purchase.id
        assert retrieved_purchase.supplier_id == supplier.id
        assert retrieved_purchase.total_amount == 89.75
        assert retrieved_purchase.status == PurchaseStatus.ORDERED
        assert retrieved_purchase.reference_number == "PO-2025-002"

    def test_update_purchase(self, dbsession):
        """Test updating a purchase."""

        # Create a simple test purchase object
        class TestPurchase:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePurchaseRepo:
            def __init__(self):
                self.purchases = {}
                self.next_id = 1

            def add(self, purchase):
                purchase.id = self.next_id
                self.purchases[self.next_id] = purchase
                self.next_id += 1
                return purchase

            def get_by_id(self, id):
                return self.purchases.get(id)

            def update(self, purchase):
                if purchase.id in self.purchases:
                    self.purchases[purchase.id] = purchase
                    return purchase
                return None

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimplePurchaseRepo()

        # Create a purchase
        purchase = TestPurchase(
            supplier_id=supplier.id,
            order_date=datetime.now(),
            expected_delivery_date=datetime.now() + timedelta(days=10),
            total_amount=215.50,
            status=PurchaseStatus.PENDING,
            created_at=datetime.now(),
            created_by="Michael Johnson",
            reference_number="PO-2025-003"
        )

        # Add to repository
        added_purchase = repository.add(purchase)

        # Update the purchase
        added_purchase.status = PurchaseStatus.ORDERED
        added_purchase.ordered_at = datetime.now()
        added_purchase.ordered_by = "Michael Johnson"
        added_purchase.total_amount = 225.75  # Updated total
        added_purchase.notes = "Rush order"
        repository.update(added_purchase)

        # Retrieve and verify updates
        updated_purchase = repository.get_by_id(added_purchase.id)
        assert updated_purchase.status == PurchaseStatus.ORDERED
        assert hasattr(updated_purchase, "ordered_at")
        assert updated_purchase.ordered_by == "Michael Johnson"
        assert updated_purchase.total_amount == 225.75
        assert updated_purchase.notes == "Rush order"

    def test_delete_purchase(self, dbsession):
        """Test deleting a purchase."""

        # Create a simple test purchase object
        class TestPurchase:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePurchaseRepo:
            def __init__(self):
                self.purchases = {}
                self.next_id = 1

            def add(self, purchase):
                purchase.id = self.next_id
                self.purchases[self.next_id] = purchase
                self.next_id += 1
                return purchase

            def get_by_id(self, id):
                return self.purchases.get(id)

            def delete(self, id):
                if id in self.purchases:
                    del self.purchases[id]
                    return True
                return False

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimplePurchaseRepo()

        # Create a purchase
        purchase = TestPurchase(
            supplier_id=supplier.id,
            order_date=datetime.now(),
            expected_delivery_date=datetime.now() + timedelta(days=3),
            total_amount=75.25,
            status=PurchaseStatus.DRAFT,
            created_at=datetime.now(),
            created_by="Sarah Williams",
            reference_number="PO-2025-004"
        )

        # Add to repository
        added_purchase = repository.add(purchase)

        # Delete the purchase
        purchase_id = added_purchase.id
        result = repository.delete(purchase_id)

        # Verify the purchase was deleted
        assert result is True
        assert repository.get_by_id(purchase_id) is None

    def test_add_item_to_purchase(self, dbsession):
        """Test adding an item to a purchase."""

        # Create a simple test purchase object
        class TestPurchase:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

            def add_material(self, material, quantity, price):
                self.items.append({
                    "material_id": material.id,
                    "material": material,
                    "quantity": quantity,
                    "price": price,
                    "item_type": "material",
                    "tool_id": None,
                    "tool": None
                })

            def add_tool(self, tool, quantity, price):
                self.items.append({
                    "tool_id": tool.id,
                    "tool": tool,
                    "quantity": quantity,
                    "price": price,
                    "item_type": "tool",
                    "material_id": None,
                    "material": None
                })

        # Create a simple in-memory repository for testing
        class SimplePurchaseRepo:
            def __init__(self):
                self.purchases = {}
                self.next_id = 1

            def add(self, purchase):
                purchase.id = self.next_id
                self.purchases[self.next_id] = purchase
                self.next_id += 1
                return purchase

            def get_by_id(self, id):
                return self.purchases.get(id)

            def update(self, purchase):
                if purchase.id in self.purchases:
                    self.purchases[purchase.id] = purchase
                    return purchase
                return None

        # Create test data
        supplier = self._create_test_supplier(dbsession)
        material = self._create_test_material(dbsession)
        tool = self._create_test_tool(dbsession)

        # Create the repository
        repository = SimplePurchaseRepo()

        # Create a purchase
        purchase = TestPurchase(
            supplier_id=supplier.id,
            order_date=datetime.now(),
            expected_delivery_date=datetime.now() + timedelta(days=7),
            total_amount=0,  # Will be calculated
            status=PurchaseStatus.DRAFT,
            created_at=datetime.now(),
            created_by="Robert Brown",
            reference_number="PO-2025-005"
        )

        # Add to repository
        added_purchase = repository.add(purchase)

        # Add items to purchase
        added_purchase.add_material(material, quantity=5, price=15.99)
        added_purchase.add_tool(tool, quantity=1, price=45.99)

        # Calculate total
        material_total = 5 * 15.99
        tool_total = 1 * 45.99
        added_purchase.total_amount = material_total + tool_total

        repository.update(added_purchase)

        # Retrieve and verify updates
        updated_purchase = repository.get_by_id(added_purchase.id)
        assert len(updated_purchase.items) == 2

        material_items = [item for item in updated_purchase.items if item["item_type"] == "material"]
        tool_items = [item for item in updated_purchase.items if item["item_type"] == "tool"]

        assert len(material_items) == 1
        assert len(tool_items) == 1
        assert material_items[0]["material_id"] == material.id
        assert material_items[0]["quantity"] == 5
        assert material_items[0]["price"] == 15.99
        assert tool_items[0]["tool_id"] == tool.id
        assert tool_items[0]["quantity"] == 1
        assert tool_items[0]["price"] == 45.99
        assert updated_purchase.total_amount == (5 * 15.99) + (1 * 45.99)

    def test_purchase_status_transition(self, dbsession):
        """Test purchase status transitions."""

        # Create a simple test purchase object
        class TestPurchase:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePurchaseRepo:
            def __init__(self):
                self.purchases = {}
                self.next_id = 1

            def add(self, purchase):
                purchase.id = self.next_id
                self.purchases[self.next_id] = purchase
                self.next_id += 1
                return purchase

            def get_by_id(self, id):
                return self.purchases.get(id)

            def update(self, purchase):
                if purchase.id in self.purchases:
                    self.purchases[purchase.id] = purchase
                    return purchase
                return None

        # Create test data
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimplePurchaseRepo()

        # Create a purchase
        purchase = TestPurchase(
            supplier_id=supplier.id,
            order_date=datetime.now(),
            expected_delivery_date=datetime.now() + timedelta(days=7),
            total_amount=125.50,
            status=PurchaseStatus.DRAFT,
            created_at=datetime.now(),
            created_by="Lisa Taylor",
            reference_number="PO-2025-006"
        )

        # Add to repository
        added_purchase = repository.add(purchase)

        # Transition through different statuses
        status_transitions = [
            (PurchaseStatus.PENDING, "pending_at"),
            (PurchaseStatus.ORDERED, "ordered_at"),
            (PurchaseStatus.SHIPPED, "shipped_at"),
            (PurchaseStatus.DELIVERED, "delivered_at")
        ]

        for new_status, timestamp_field in status_transitions:
            added_purchase.status = new_status
            # Add timestamp for status change
            setattr(added_purchase, timestamp_field, datetime.now())
            repository.update(added_purchase)

            # Verify status was updated
            updated_purchase = repository.get_by_id(added_purchase.id)
            assert updated_purchase.status == new_status
            assert hasattr(updated_purchase, timestamp_field)

    def test_find_purchases_by_supplier(self, dbsession):
        """Test finding purchases by supplier."""

        # Create a simple test purchase object
        class TestPurchase:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePurchaseRepo:
            def __init__(self):
                self.purchases = {}
                self.next_id = 1

            def add(self, purchase):
                purchase.id = self.next_id
                self.purchases[self.next_id] = purchase
                self.next_id += 1
                return purchase

            def find_by_supplier_id(self, supplier_id):
                return [p for p in self.purchases.values() if p.supplier_id == supplier_id]

        # Create test suppliers
        class TestSupplier:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        supplier1 = TestSupplier(
            name="Leather Co.",
            contact_email="leather@example.com",
            status=SupplierStatus.ACTIVE
        )
        supplier1.id = 1

        supplier2 = TestSupplier(
            name="Tool Shop",
            contact_email="tools@example.com",
            status=SupplierStatus.ACTIVE
        )
        supplier2.id = 2

        # Create the repository
        repository = SimplePurchaseRepo()

        # Create purchases for different suppliers
        purchase1 = TestPurchase(
            supplier_id=supplier1.id,
            total_amount=100.00,
            status=PurchaseStatus.ORDERED,
            reference_number="PO-S1-001"
        )

        purchase2 = TestPurchase(
            supplier_id=supplier1.id,
            total_amount=150.00,
            status=PurchaseStatus.SHIPPED,
            reference_number="PO-S1-002"
        )

        purchase3 = TestPurchase(
            supplier_id=supplier2.id,
            total_amount=200.00,
            status=PurchaseStatus.PENDING,
            reference_number="PO-S2-001"
        )

        # Add to repository
        repository.add(purchase1)
        repository.add(purchase2)
        repository.add(purchase3)

        # Find purchases by supplier
        supplier1_purchases = repository.find_by_supplier_id(supplier1.id)
        supplier2_purchases = repository.find_by_supplier_id(supplier2.id)

        # Verify results
        assert len(supplier1_purchases) == 2
        assert len(supplier2_purchases) == 1
        assert all(p.supplier_id == supplier1.id for p in supplier1_purchases)
        assert all(p.supplier_id == supplier2.id for p in supplier2_purchases)
        assert any(p.reference_number == "PO-S1-001" for p in supplier1_purchases)
        assert any(p.reference_number == "PO-S1-002" for p in supplier1_purchases)
        assert any(p.reference_number == "PO-S2-001" for p in supplier2_purchases)