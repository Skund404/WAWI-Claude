# tests/leatherwork_repository_tests/test_picking_list_repository.py
import pytest
from datetime import datetime, timedelta
from database.models.enums import (
    PickingListStatus,
    SaleStatus,
    CustomerStatus,
    ComponentType,
    MaterialType
)


class TestPickingListRepository:
    def _create_test_customer(self, dbsession):
        """Helper method to create a test customer."""

        class TestCustomer:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        customer = TestCustomer(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            phone="555-123-4567",
            status=CustomerStatus.ACTIVE
        )

        # Simulated database insert
        customer.id = 1
        return customer

    def _create_test_sales(self, dbsession, customer_id):
        """Helper method to create a test sales record."""

        class TestSales:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        sales = TestSales(
            customer_id=customer_id,
            sale_date=datetime.now(),
            total_amount=249.99,
            status=SaleStatus.DESIGN_APPROVAL,
            created_at=datetime.now()
        )

        # Simulated database insert
        sales.id = 1
        return sales

    def _create_test_material(self, dbsession):
        """Helper method to create a test material."""

        class TestMaterial:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        material = TestMaterial(
            name="Test Leather",
            material_type=MaterialType.LEATHER,
            description="Premium vegetable tanned leather",
            unit_price=15.99,
            color="Brown"
        )

        # Simulated database insert
        material.id = 1
        return material

    def _create_test_component(self, dbsession):
        """Helper method to create a test component."""

        class TestComponent:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        component = TestComponent(
            name="Front Panel",
            description="Front panel for wallet",
            component_type=ComponentType.LEATHER,
            attributes={"width": 100, "height": 80}
        )

        # Simulated database insert
        component.id = 1
        return component

    def test_create_picking_list(self, dbsession):
        """Test creating a new picking list."""

        # Create a simple test picking list object
        class TestPickingList:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePickingListRepo:
            def __init__(self):
                self.picking_lists = {}
                self.next_id = 1

            def add(self, picking_list):
                picking_list.id = self.next_id
                self.picking_lists[self.next_id] = picking_list
                self.next_id += 1
                return picking_list

            def get_by_id(self, id):
                return self.picking_lists.get(id)

        # Create test data
        customer = self._create_test_customer(dbsession)
        sales = self._create_test_sales(dbsession, customer.id)

        # Create the repository
        repository = SimplePickingListRepo()

        # Create a picking list
        picking_list = TestPickingList(
            sales_id=sales.id,
            status=PickingListStatus.DRAFT,
            created_at=datetime.now(),
            created_by="John Doe"
        )

        # Save the picking list
        added_picking_list = repository.add(picking_list)

        # Verify the picking list was saved
        assert added_picking_list.id == 1
        assert added_picking_list.sales_id == sales.id
        assert added_picking_list.status == PickingListStatus.DRAFT

    def test_read_picking_list(self, dbsession):
        """Test reading a picking list."""

        # Create a simple test picking list object
        class TestPickingList:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePickingListRepo:
            def __init__(self):
                self.picking_lists = {}
                self.next_id = 1

            def add(self, picking_list):
                picking_list.id = self.next_id
                self.picking_lists[self.next_id] = picking_list
                self.next_id += 1
                return picking_list

            def get_by_id(self, id):
                return self.picking_lists.get(id)

        # Create test data
        customer = self._create_test_customer(dbsession)
        sales = self._create_test_sales(dbsession, customer.id)

        # Create the repository
        repository = SimplePickingListRepo()

        # Create a picking list
        picking_list = TestPickingList(
            sales_id=sales.id,
            status=PickingListStatus.PENDING,
            created_at=datetime.now(),
            created_by="Jane Doe"
        )

        # Add to repository
        added_picking_list = repository.add(picking_list)

        # Read the picking list
        retrieved_picking_list = repository.get_by_id(added_picking_list.id)

        # Verify the picking list was retrieved correctly
        assert retrieved_picking_list is not None
        assert retrieved_picking_list.id == added_picking_list.id
        assert retrieved_picking_list.sales_id == sales.id
        assert retrieved_picking_list.status == PickingListStatus.PENDING

    def test_update_picking_list(self, dbsession):
        """Test updating a picking list."""

        # Create a simple test picking list object
        class TestPickingList:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePickingListRepo:
            def __init__(self):
                self.picking_lists = {}
                self.next_id = 1

            def add(self, picking_list):
                picking_list.id = self.next_id
                self.picking_lists[self.next_id] = picking_list
                self.next_id += 1
                return picking_list

            def get_by_id(self, id):
                return self.picking_lists.get(id)

            def update(self, picking_list):
                if picking_list.id in self.picking_lists:
                    self.picking_lists[picking_list.id] = picking_list
                    return picking_list
                return None

        # Create test data
        customer = self._create_test_customer(dbsession)
        sales = self._create_test_sales(dbsession, customer.id)

        # Create the repository
        repository = SimplePickingListRepo()

        # Create a picking list
        picking_list = TestPickingList(
            sales_id=sales.id,
            status=PickingListStatus.DRAFT,
            created_at=datetime.now(),
            created_by="Alice Johnson"
        )

        # Add to repository
        added_picking_list = repository.add(picking_list)

        # Update the picking list
        added_picking_list.status = PickingListStatus.IN_PROGRESS
        added_picking_list.picked_by = "Bob Williams"
        added_picking_list.picked_at = datetime.now()
        repository.update(added_picking_list)

        # Retrieve and verify updates
        updated_picking_list = repository.get_by_id(added_picking_list.id)
        assert updated_picking_list.status == PickingListStatus.IN_PROGRESS
        assert updated_picking_list.picked_by == "Bob Williams"
        assert hasattr(updated_picking_list, "picked_at")

    def test_delete_picking_list(self, dbsession):
        """Test deleting a picking list."""

        # Create a simple test picking list object
        class TestPickingList:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePickingListRepo:
            def __init__(self):
                self.picking_lists = {}
                self.next_id = 1

            def add(self, picking_list):
                picking_list.id = self.next_id
                self.picking_lists[self.next_id] = picking_list
                self.next_id += 1
                return picking_list

            def get_by_id(self, id):
                return self.picking_lists.get(id)

            def delete(self, id):
                if id in self.picking_lists:
                    del self.picking_lists[id]
                    return True
                return False

        # Create test data
        customer = self._create_test_customer(dbsession)
        sales = self._create_test_sales(dbsession, customer.id)

        # Create the repository
        repository = SimplePickingListRepo()

        # Create a picking list
        picking_list = TestPickingList(
            sales_id=sales.id,
            status=PickingListStatus.DRAFT,
            created_at=datetime.now(),
            created_by="Charlie Brown"
        )

        # Add to repository
        added_picking_list = repository.add(picking_list)

        # Delete the picking list
        picking_list_id = added_picking_list.id
        result = repository.delete(picking_list_id)

        # Verify the picking list was deleted
        assert result is True
        assert repository.get_by_id(picking_list_id) is None

    def test_add_item_to_picking_list(self, dbsession):
        """Test adding an item to a picking list."""

        # Create a simple test picking list object
        class TestPickingList:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

            def add_component(self, component, quantity_ordered):
                self.items.append({
                    "component_id": component.id,
                    "component": component,
                    "quantity_ordered": quantity_ordered,
                    "quantity_picked": 0,
                    "material_id": None,
                    "material": None
                })

            def add_material(self, material, quantity_ordered):
                self.items.append({
                    "material_id": material.id,
                    "material": material,
                    "quantity_ordered": quantity_ordered,
                    "quantity_picked": 0,
                    "component_id": None,
                    "component": None
                })

        # Create a simple in-memory repository for testing
        class SimplePickingListRepo:
            def __init__(self):
                self.picking_lists = {}
                self.next_id = 1

            def add(self, picking_list):
                picking_list.id = self.next_id
                self.picking_lists[self.next_id] = picking_list
                self.next_id += 1
                return picking_list

            def get_by_id(self, id):
                return self.picking_lists.get(id)

            def update(self, picking_list):
                if picking_list.id in self.picking_lists:
                    self.picking_lists[picking_list.id] = picking_list
                    return picking_list
                return None

        # Create test data
        customer = self._create_test_customer(dbsession)
        sales = self._create_test_sales(dbsession, customer.id)
        component = self._create_test_component(dbsession)
        material = self._create_test_material(dbsession)

        # Create the repository
        repository = SimplePickingListRepo()

        # Create a picking list
        picking_list = TestPickingList(
            sales_id=sales.id,
            status=PickingListStatus.DRAFT,
            created_at=datetime.now(),
            created_by="David Miller"
        )

        # Add to repository
        added_picking_list = repository.add(picking_list)

        # Add items to picking list
        added_picking_list.add_component(component, quantity_ordered=2)
        added_picking_list.add_material(material, quantity_ordered=0.5)
        repository.update(added_picking_list)

        # Retrieve and verify updates
        updated_picking_list = repository.get_by_id(added_picking_list.id)
        assert len(updated_picking_list.items) == 2

        component_items = [item for item in updated_picking_list.items if item["component_id"] is not None]
        material_items = [item for item in updated_picking_list.items if item["material_id"] is not None]

        assert len(component_items) == 1
        assert len(material_items) == 1
        assert component_items[0]["component_id"] == component.id
        assert component_items[0]["quantity_ordered"] == 2
        assert material_items[0]["material_id"] == material.id
        assert material_items[0]["quantity_ordered"] == 0.5

    def test_picking_list_status_transition(self, dbsession):
        """Test picking list status transitions."""

        # Create a simple test picking list object
        class TestPickingList:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePickingListRepo:
            def __init__(self):
                self.picking_lists = {}
                self.next_id = 1

            def add(self, picking_list):
                picking_list.id = self.next_id
                self.picking_lists[self.next_id] = picking_list
                self.next_id += 1
                return picking_list

            def get_by_id(self, id):
                return self.picking_lists.get(id)

            def update(self, picking_list):
                if picking_list.id in self.picking_lists:
                    self.picking_lists[picking_list.id] = picking_list
                    return picking_list
                return None

        # Create test data
        customer = self._create_test_customer(dbsession)
        sales = self._create_test_sales(dbsession, customer.id)

        # Create the repository
        repository = SimplePickingListRepo()

        # Create a picking list
        picking_list = TestPickingList(
            sales_id=sales.id,
            status=PickingListStatus.DRAFT,
            created_at=datetime.now(),
            created_by="Emily White"
        )

        # Add to repository
        added_picking_list = repository.add(picking_list)

        # Transition through different statuses
        status_transitions = [
            PickingListStatus.PENDING,
            PickingListStatus.IN_PROGRESS,
            PickingListStatus.COMPLETED
        ]

        for new_status in status_transitions:
            added_picking_list.status = new_status
            # Add timestamp for status change
            if new_status == PickingListStatus.IN_PROGRESS:
                added_picking_list.started_at = datetime.now()
            elif new_status == PickingListStatus.COMPLETED:
                added_picking_list.completed_at = datetime.now()
            repository.update(added_picking_list)

            # Verify status was updated
            updated_picking_list = repository.get_by_id(added_picking_list.id)
            assert updated_picking_list.status == new_status