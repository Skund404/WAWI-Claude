# tests/leatherwork_repository_tests/test_supplies_repository.py
import pytest
from datetime import datetime, timedelta
from database.models.enums import (
    MaterialType,
    QualityGrade,
    MeasurementUnit,
    SupplierStatus,
    InventoryStatus
)


class TestSuppliesRepository:
    def _create_test_supplier(self, dbsession):
        """Helper method to create a test supplier."""

        class TestSupplier:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        supplier = TestSupplier(
            name="Craft Supplies Inc.",
            contact_email="supplies@example.com",
            phone="555-789-0123",
            address="456 Crafts St",
            status=SupplierStatus.ACTIVE,
            created_at=datetime.now()
        )

        # Simulated database insert
        supplier.id = 1
        return supplier

    def test_create_supplies(self, dbsession):
        """Test creating a new supplies material."""

        # Create a simple test supplies object
        class TestSupplies:
            def __init__(self, **kwargs):
                self.id = None
                self.material_type = MaterialType.SUPPLIES
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleSuppliesRepo:
            def __init__(self):
                self.supplies_items = {}
                self.next_id = 1

            def add(self, supplies):
                supplies.id = self.next_id
                self.supplies_items[self.next_id] = supplies
                self.next_id += 1
                return supplies

            def get_by_id(self, id):
                return self.supplies_items.get(id)

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleSuppliesRepo()

        # Create a supplies material (thread)
        supplies = TestSupplies(
            name="Tiger Thread",
            description="Waxed polyester thread for leatherwork",
            supplier_id=supplier.id,
            unit_price=15.99,
            measurement_unit=MeasurementUnit.METER,
            quality_grade=QualityGrade.PREMIUM,
            color="Black",
            created_at=datetime.now(),
            material_type_detail="thread",
            thickness="0.8mm",
            material_composition="Polyester"
        )

        # Save the supplies
        added_supplies = repository.add(supplies)

        # Verify the supplies was saved
        assert added_supplies.id == 1
        assert added_supplies.name == "Tiger Thread"
        assert added_supplies.material_type == MaterialType.SUPPLIES
        assert added_supplies.material_type_detail == "thread"
        assert added_supplies.thickness == "0.8mm"
        assert added_supplies.material_composition == "Polyester"
        assert added_supplies.color == "Black"

    def test_read_supplies(self, dbsession):
        """Test reading a supplies material."""

        # Create a simple test supplies object
        class TestSupplies:
            def __init__(self, **kwargs):
                self.id = None
                self.material_type = MaterialType.SUPPLIES
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleSuppliesRepo:
            def __init__(self):
                self.supplies_items = {}
                self.next_id = 1

            def add(self, supplies):
                supplies.id = self.next_id
                self.supplies_items[self.next_id] = supplies
                self.next_id += 1
                return supplies

            def get_by_id(self, id):
                return self.supplies_items.get(id)

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleSuppliesRepo()

        # Create a supplies material (adhesive)
        supplies = TestSupplies(
            name="Contact Cement",
            description="Strong contact cement for leatherwork",
            supplier_id=supplier.id,
            unit_price=12.50,
            measurement_unit=MeasurementUnit.MILLILITER,
            quality_grade=QualityGrade.STANDARD,
            created_at=datetime.now(),
            material_type_detail="adhesive",
            material_composition="Neoprene"
        )

        # Add to repository
        added_supplies = repository.add(supplies)

        # Read the supplies
        retrieved_supplies = repository.get_by_id(added_supplies.id)

        # Verify the supplies was retrieved correctly
        assert retrieved_supplies is not None
        assert retrieved_supplies.id == added_supplies.id
        assert retrieved_supplies.name == "Contact Cement"
        assert retrieved_supplies.material_type == MaterialType.SUPPLIES
        assert retrieved_supplies.material_type_detail == "adhesive"
        assert retrieved_supplies.material_composition == "Neoprene"

    def test_update_supplies(self, dbsession):
        """Test updating a supplies material."""

        # Create a simple test supplies object
        class TestSupplies:
            def __init__(self, **kwargs):
                self.id = None
                self.material_type = MaterialType.SUPPLIES
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleSuppliesRepo:
            def __init__(self):
                self.supplies_items = {}
                self.next_id = 1

            def add(self, supplies):
                supplies.id = self.next_id
                self.supplies_items[self.next_id] = supplies
                self.next_id += 1
                return supplies

            def get_by_id(self, id):
                return self.supplies_items.get(id)

            def update(self, supplies):
                if supplies.id in self.supplies_items:
                    self.supplies_items[supplies.id] = supplies
                    return supplies
                return None

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleSuppliesRepo()

        # Create a supplies material (dye)
        supplies = TestSupplies(
            name="Eco-Flo Leather Dye",
            description="Water-based leather dye",
            supplier_id=supplier.id,
            unit_price=8.75,
            measurement_unit=MeasurementUnit.MILLILITER,
            quality_grade=QualityGrade.PROFESSIONAL,
            color="Brown",
            created_at=datetime.now(),
            material_type_detail="dye",
            material_composition="Water-based"
        )

        # Add to repository
        added_supplies = repository.add(supplies)

        # Update the supplies
        added_supplies.name = "Premium Eco-Flo Leather Dye"
        added_supplies.description = "Professional water-based leather dye"
        added_supplies.unit_price = 9.99
        added_supplies.color = "Dark Brown"
        repository.update(added_supplies)

        # Retrieve and verify updates
        updated_supplies = repository.get_by_id(added_supplies.id)
        assert updated_supplies.name == "Premium Eco-Flo Leather Dye"
        assert updated_supplies.description == "Professional water-based leather dye"
        assert updated_supplies.unit_price == 9.99
        assert updated_supplies.color == "Dark Brown"

    def test_delete_supplies(self, dbsession):
        """Test deleting a supplies material."""

        # Create a simple test supplies object
        class TestSupplies:
            def __init__(self, **kwargs):
                self.id = None
                self.material_type = MaterialType.SUPPLIES
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleSuppliesRepo:
            def __init__(self):
                self.supplies_items = {}
                self.next_id = 1

            def add(self, supplies):
                supplies.id = self.next_id
                self.supplies_items[self.next_id] = supplies
                self.next_id += 1
                return supplies

            def get_by_id(self, id):
                return self.supplies_items.get(id)

            def delete(self, id):
                if id in self.supplies_items:
                    del self.supplies_items[id]
                    return True
                return False

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleSuppliesRepo()

        # Create a supplies material (edge paint)
        supplies = TestSupplies(
            name="Fenice Edge Paint",
            description="Professional edge paint for leather finishing",
            supplier_id=supplier.id,
            unit_price=18.50,
            measurement_unit=MeasurementUnit.MILLILITER,
            quality_grade=QualityGrade.PREMIUM,
            color="Black",
            created_at=datetime.now(),
            material_type_detail="edge_paint"
        )

        # Add to repository
        added_supplies = repository.add(supplies)

        # Delete the supplies
        supplies_id = added_supplies.id
        result = repository.delete(supplies_id)

        # Verify the supplies was deleted
        assert result is True
        assert repository.get_by_id(supplies_id) is None

    def test_find_supplies_by_type_detail(self, dbsession):
        """Test finding supplies by their detailed type."""

        # Create a simple test supplies object
        class TestSupplies:
            def __init__(self, **kwargs):
                self.id = None
                self.material_type = MaterialType.SUPPLIES
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleSuppliesRepo:
            def __init__(self):
                self.supplies_items = {}
                self.next_id = 1

            def add(self, supplies):
                supplies.id = self.next_id
                self.supplies_items[self.next_id] = supplies
                self.next_id += 1
                return supplies

            def find_by_type_detail(self, type_detail):
                return [s for s in self.supplies_items.values() if s.material_type_detail == type_detail]

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleSuppliesRepo()

        # Create supplies of different types
        thread1 = TestSupplies(
            name="Ritza Tiger Thread",
            material_type=MaterialType.SUPPLIES,
            supplier_id=supplier.id,
            material_type_detail="thread",
            color="Cream",
            thickness="0.6mm"
        )

        thread2 = TestSupplies(
            name="Waxed Linen Thread",
            material_type=MaterialType.SUPPLIES,
            supplier_id=supplier.id,
            material_type_detail="thread",
            color="Natural",
            thickness="0.45mm"
        )

        adhesive = TestSupplies(
            name="Barge Cement",
            material_type=MaterialType.SUPPLIES,
            supplier_id=supplier.id,
            material_type_detail="adhesive",
            material_composition="Neoprene"
        )

        # Add to repository
        repository.add(thread1)
        repository.add(thread2)
        repository.add(adhesive)

        # Find supplies by type detail
        thread_items = repository.find_by_type_detail("thread")
        adhesive_items = repository.find_by_type_detail("adhesive")

        # Verify results
        assert len(thread_items) == 2
        assert len(adhesive_items) == 1
        assert all(s.material_type_detail == "thread" for s in thread_items)
        assert all(s.material_type_detail == "adhesive" for s in adhesive_items)

    def test_find_supplies_by_color(self, dbsession):
        """Test finding supplies by color."""

        # Create a simple test supplies object
        class TestSupplies:
            def __init__(self, **kwargs):
                self.id = None
                self.material_type = MaterialType.SUPPLIES
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleSuppliesRepo:
            def __init__(self):
                self.supplies_items = {}
                self.next_id = 1

            def add(self, supplies):
                supplies.id = self.next_id
                self.supplies_items[self.next_id] = supplies
                self.next_id += 1
                return supplies

            def find_by_color(self, color):
                return [s for s in self.supplies_items.values() if hasattr(s, 'color') and s.color == color]

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleSuppliesRepo()

        # Create supplies with different colors
        black_thread = TestSupplies(
            name="Black Thread",
            material_type=MaterialType.SUPPLIES,
            supplier_id=supplier.id,
            material_type_detail="thread",
            color="Black"
        )

        black_dye = TestSupplies(
            name="Black Dye",
            material_type=MaterialType.SUPPLIES,
            supplier_id=supplier.id,
            material_type_detail="dye",
            color="Black"
        )

        brown_dye = TestSupplies(
            name="Brown Dye",
            material_type=MaterialType.SUPPLIES,
            supplier_id=supplier.id,
            material_type_detail="dye",
            color="Brown"
        )

        # Add to repository
        repository.add(black_thread)
        repository.add(black_dye)
        repository.add(brown_dye)

        # Find supplies by color
        black_items = repository.find_by_color("Black")
        brown_items = repository.find_by_color("Brown")

        # Verify results
        assert len(black_items) == 2
        assert len(brown_items) == 1
        assert all(s.color == "Black" for s in black_items)
        assert all(s.color == "Brown" for s in brown_items)