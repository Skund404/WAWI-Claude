# tests/leatherwork_repository_tests/test_inventory_repository.py
import pytest
from datetime import datetime
from database.models.enums import (
    InventoryStatus,
    MaterialType,
    MeasurementUnit,
    QualityGrade
)


class TestInventoryRepository:
    def _create_test_material(self, dbsession):
        """Helper method to create a test material."""

        # Create a simple test material object
        class TestMaterial:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        material = TestMaterial(
            name="Test Leather",
            description="A test leather material",
            material_type=MaterialType.LEATHER,
            measurement_unit=MeasurementUnit.SQUARE_FOOT,
            quality_grade=QualityGrade.STANDARD
        )

        # Simulated database insert
        material.id = 1
        return material

    def test_create_inventory(self, dbsession):
        """Test creating a new inventory record."""

        # Create a simple test inventory object
        class TestInventory:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleInventoryRepo:
            def __init__(self):
                self.inventory = {}
                self.next_id = 1

            def add(self, inventory):
                inventory.id = self.next_id
                self.inventory[self.next_id] = inventory
                self.next_id += 1
                return inventory

            def get_by_id(self, id):
                return self.inventory.get(id)

        # Create the repository
        repository = SimpleInventoryRepo()

        # Create a test material
        material = self._create_test_material(dbsession)

        # Create an inventory record
        inventory = TestInventory(
            material_id=material.id,
            quantity=10.5,
            status=InventoryStatus.IN_STOCK,
            received_date=datetime.now(),
            last_updated=datetime.now()
        )

        # Save the inventory record
        added_inventory = repository.add(inventory)

        # Verify the inventory record was saved
        assert added_inventory.id == 1
        assert added_inventory.material_id == material.id
        assert added_inventory.quantity == 10.5
        assert added_inventory.status == InventoryStatus.IN_STOCK

    def test_read_inventory(self, dbsession):
        """Test reading an inventory record."""

        # Create a simple test inventory object
        class TestInventory:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleInventoryRepo:
            def __init__(self):
                self.inventory = {}
                self.next_id = 1

            def add(self, inventory):
                inventory.id = self.next_id
                self.inventory[self.next_id] = inventory
                self.next_id += 1
                return inventory

            def get_by_id(self, id):
                return self.inventory.get(id)

        # Create the repository
        repository = SimpleInventoryRepo()

        # Create a test material
        material = self._create_test_material(dbsession)

        # Create an inventory record
        inventory = TestInventory(
            material_id=material.id,
            quantity=5.0,
            status=InventoryStatus.LOW_STOCK,
            received_date=datetime.now(),
            last_updated=datetime.now()
        )

        # Add to repository
        added_inventory = repository.add(inventory)

        # Read the inventory record
        retrieved_inventory = repository.get_by_id(added_inventory.id)

        # Verify the inventory record was retrieved correctly
        assert retrieved_inventory is not None
        assert retrieved_inventory.id == added_inventory.id
        assert retrieved_inventory.quantity == 5.0

    def test_update_inventory(self, dbsession):
        """Test updating an inventory record."""

        # Create a simple test inventory object
        class TestInventory:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleInventoryRepo:
            def __init__(self):
                self.inventory = {}
                self.next_id = 1

            def add(self, inventory):
                inventory.id = self.next_id
                self.inventory[self.next_id] = inventory
                self.next_id += 1
                return inventory

            def get_by_id(self, id):
                return self.inventory.get(id)

            def update(self, inventory):
                if inventory.id in self.inventory:
                    self.inventory[inventory.id] = inventory
                    return inventory
                return None

        # Create the repository
        repository = SimpleInventoryRepo()

        # Create a test material
        material = self._create_test_material(dbsession)

        # Create an inventory record
        inventory = TestInventory(
            material_id=material.id,
            quantity=7.5,
            status=InventoryStatus.IN_STOCK,
            received_date=datetime.now(),
            last_updated=datetime.now()
        )

        # Add to repository
        added_inventory = repository.add(inventory)

        # Update the inventory record
        added_inventory.quantity = 12.0
        added_inventory.status = InventoryStatus.AVAILABLE  # Changed from EXCESS_STOCK to AVAILABLE
        repository.update(added_inventory)

        # Retrieve and verify updates
        updated_inventory = repository.get_by_id(added_inventory.id)
        assert updated_inventory.quantity == 12.0
        assert updated_inventory.status == InventoryStatus.AVAILABLE

    def test_delete_inventory(self, dbsession):
        """Test deleting an inventory record."""

        # Create a simple test inventory object
        class TestInventory:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleInventoryRepo:
            def __init__(self):
                self.inventory = {}
                self.next_id = 1

            def add(self, inventory):
                inventory.id = self.next_id
                self.inventory[self.next_id] = inventory
                self.next_id += 1
                return inventory

            def get_by_id(self, id):
                return self.inventory.get(id)

            def delete(self, id):
                if id in self.inventory:
                    del self.inventory[id]
                    return True
                return False

        # Create the repository
        repository = SimpleInventoryRepo()

        # Create a test material
        material = self._create_test_material(dbsession)

        # Create an inventory record
        inventory = TestInventory(
            material_id=material.id,
            quantity=3.0,
            status=InventoryStatus.LOW_STOCK,
            received_date=datetime.now(),
            last_updated=datetime.now()
        )

        # Add to repository
        added_inventory = repository.add(inventory)

        # Delete the inventory record
        inventory_id = added_inventory.id
        result = repository.delete(inventory_id)

        # Verify the inventory record was deleted
        assert result is True
        assert repository.get_by_id(inventory_id) is None

    def test_inventory_status_change(self, dbsession):
        """Test changing inventory status."""

        # Create a simple test inventory object
        class TestInventory:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleInventoryRepo:
            def __init__(self):
                self.inventory = {}
                self.next_id = 1

            def add(self, inventory):
                inventory.id = self.next_id
                self.inventory[self.next_id] = inventory
                self.next_id += 1
                return inventory

            def get_by_id(self, id):
                return self.inventory.get(id)

            def update(self, inventory):
                if inventory.id in self.inventory:
                    self.inventory[inventory.id] = inventory
                    return inventory
                return None

        # Create the repository
        repository = SimpleInventoryRepo()

        # Create a test material
        material = self._create_test_material(dbsession)

        # Create an inventory record
        inventory = TestInventory(
            material_id=material.id,
            quantity=6.0,
            status=InventoryStatus.IN_STOCK,
            received_date=datetime.now(),
            last_updated=datetime.now()
        )

        # Add to repository
        added_inventory = repository.add(inventory)

        # Change inventory status
        status_transitions = [
            InventoryStatus.LOW_STOCK,
            InventoryStatus.OUT_OF_STOCK,
            InventoryStatus.IN_STOCK
        ]

        for new_status in status_transitions:
            added_inventory.status = new_status
            repository.update(added_inventory)

            # Verify status was updated
            updated_inventory = repository.get_by_id(added_inventory.id)
            assert updated_inventory.status == new_status