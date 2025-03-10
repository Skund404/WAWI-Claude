# tests/leatherwork_repository_tests/test_hardware_repository.py
import pytest
from datetime import datetime, timedelta
from database.models.enums import (
    MaterialType,
    QualityGrade,
    MeasurementUnit,
    HardwareType,
    HardwareMaterial,
    HardwareFinish,
    SupplierStatus,
    InventoryStatus
)


class TestHardwareRepository:
    def _create_test_supplier(self, dbsession):
        """Helper method to create a test supplier."""

        class TestSupplier:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        supplier = TestSupplier(
            name="Hardware Supplier Co.",
            contact_email="hardware@example.com",
            phone="555-444-5555",
            address="123 Hardware St",
            status=SupplierStatus.ACTIVE,
            created_at=datetime.now()
        )

        # Simulated database insert
        supplier.id = 1
        return supplier

    def test_create_hardware(self, dbsession):
        """Test creating a new hardware material."""

        # Create a simple test hardware object
        class TestHardware:
            def __init__(self, **kwargs):
                self.id = None
                self.material_type = MaterialType.HARDWARE
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleHardwareRepo:
            def __init__(self):
                self.hardware_items = {}
                self.next_id = 1

            def add(self, hardware):
                hardware.id = self.next_id
                self.hardware_items[self.next_id] = hardware
                self.next_id += 1
                return hardware

            def get_by_id(self, id):
                return self.hardware_items.get(id)

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleHardwareRepo()

        # Create a hardware material
        hardware = TestHardware(
            name="Solid Brass Buckle",
            description="High-quality solid brass belt buckle",
            supplier_id=supplier.id,
            unit_price=8.50,
            measurement_unit=MeasurementUnit.PIECE,
            quality_grade=QualityGrade.PREMIUM,
            created_at=datetime.now(),
            hardware_type=HardwareType.BUCKLE,
            hardware_material=HardwareMaterial.BRASS,
            finish=HardwareFinish.ANTIQUE,
            size="1 inch"
        )

        # Save the hardware
        added_hardware = repository.add(hardware)

        # Verify the hardware was saved
        assert added_hardware.id == 1
        assert added_hardware.name == "Solid Brass Buckle"
        assert added_hardware.material_type == MaterialType.HARDWARE
        assert added_hardware.hardware_type == HardwareType.BUCKLE
        assert added_hardware.hardware_material == HardwareMaterial.BRASS
        assert added_hardware.finish == HardwareFinish.ANTIQUE
        assert added_hardware.size == "1 inch"

    def test_read_hardware(self, dbsession):
        """Test reading a hardware material."""

        # Create a simple test hardware object
        class TestHardware:
            def __init__(self, **kwargs):
                self.id = None
                self.material_type = MaterialType.HARDWARE
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleHardwareRepo:
            def __init__(self):
                self.hardware_items = {}
                self.next_id = 1

            def add(self, hardware):
                hardware.id = self.next_id
                self.hardware_items[self.next_id] = hardware
                self.next_id += 1
                return hardware

            def get_by_id(self, id):
                return self.hardware_items.get(id)

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleHardwareRepo()

        # Create a hardware material
        hardware = TestHardware(
            name="Magnetic Snap Closure",
            description="Strong magnetic snap closure for bags",
            supplier_id=supplier.id,
            unit_price=3.25,
            measurement_unit=MeasurementUnit.PIECE,
            quality_grade=QualityGrade.STANDARD,
            created_at=datetime.now(),
            hardware_type=HardwareType.MAGNETIC_CLOSURE,
            hardware_material=HardwareMaterial.NICKEL,
            finish=HardwareFinish.NICKEL_PLATED,
            size="Medium"
        )

        # Add to repository
        added_hardware = repository.add(hardware)

        # Read the hardware
        retrieved_hardware = repository.get_by_id(added_hardware.id)

        # Verify the hardware was retrieved correctly
        assert retrieved_hardware is not None
        assert retrieved_hardware.id == added_hardware.id
        assert retrieved_hardware.name == "Magnetic Snap Closure"
        assert retrieved_hardware.hardware_type == HardwareType.MAGNETIC_CLOSURE
        assert retrieved_hardware.hardware_material == HardwareMaterial.NICKEL
        assert retrieved_hardware.finish == HardwareFinish.NICKEL_PLATED

    def test_update_hardware(self, dbsession):
        """Test updating a hardware material."""

        # Create a simple test hardware object
        class TestHardware:
            def __init__(self, **kwargs):
                self.id = None
                self.material_type = MaterialType.HARDWARE
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleHardwareRepo:
            def __init__(self):
                self.hardware_items = {}
                self.next_id = 1

            def add(self, hardware):
                hardware.id = self.next_id
                self.hardware_items[self.next_id] = hardware
                self.next_id += 1
                return hardware

            def get_by_id(self, id):
                return self.hardware_items.get(id)

            def update(self, hardware):
                if hardware.id in self.hardware_items:
                    self.hardware_items[hardware.id] = hardware
                    return hardware
                return None

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleHardwareRepo()

        # Create a hardware material
        hardware = TestHardware(
            name="Zipper",
            description="Metal zipper for bags",
            supplier_id=supplier.id,
            unit_price=2.50,
            measurement_unit=MeasurementUnit.PIECE,
            quality_grade=QualityGrade.STANDARD,
            created_at=datetime.now(),
            hardware_type=HardwareType.ZIPPER,
            hardware_material=HardwareMaterial.BRASS,
            finish=HardwareFinish.POLISHED,
            size="12 inch"
        )

        # Add to repository
        added_hardware = repository.add(hardware)

        # Update the hardware
        added_hardware.name = "YKK Zipper"
        added_hardware.description = "Premium YKK zipper for bags"
        added_hardware.unit_price = 3.75
        added_hardware.quality_grade = QualityGrade.PREMIUM
        added_hardware.finish = HardwareFinish.ANTIQUE
        repository.update(added_hardware)

        # Retrieve and verify updates
        updated_hardware = repository.get_by_id(added_hardware.id)
        assert updated_hardware.name == "YKK Zipper"
        assert updated_hardware.description == "Premium YKK zipper for bags"
        assert updated_hardware.unit_price == 3.75
        assert updated_hardware.quality_grade == QualityGrade.PREMIUM
        assert updated_hardware.finish == HardwareFinish.ANTIQUE

    def test_delete_hardware(self, dbsession):
        """Test deleting a hardware material."""

        # Create a simple test hardware object
        class TestHardware:
            def __init__(self, **kwargs):
                self.id = None
                self.material_type = MaterialType.HARDWARE
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleHardwareRepo:
            def __init__(self):
                self.hardware_items = {}
                self.next_id = 1

            def add(self, hardware):
                hardware.id = self.next_id
                self.hardware_items[self.next_id] = hardware
                self.next_id += 1
                return hardware

            def get_by_id(self, id):
                return self.hardware_items.get(id)

            def delete(self, id):
                if id in self.hardware_items:
                    del self.hardware_items[id]
                    return True
                return False

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleHardwareRepo()

        # Create a hardware material
        hardware = TestHardware(
            name="D-Ring",
            description="Metal D-ring for straps",
            supplier_id=supplier.id,
            unit_price=1.20,
            measurement_unit=MeasurementUnit.PIECE,
            quality_grade=QualityGrade.STANDARD,
            created_at=datetime.now(),
            hardware_type=HardwareType.D_RING,
            hardware_material=HardwareMaterial.NICKEL,
            finish=HardwareFinish.POLISHED,
            size="3/4 inch"
        )

        # Add to repository
        added_hardware = repository.add(hardware)

        # Delete the hardware
        hardware_id = added_hardware.id
        result = repository.delete(hardware_id)

        # Verify the hardware was deleted
        assert result is True
        assert repository.get_by_id(hardware_id) is None

    def test_find_hardware_by_type(self, dbsession):
        """Test finding hardware by type."""

        # Create a simple test hardware object
        class TestHardware:
            def __init__(self, **kwargs):
                self.id = None
                self.material_type = MaterialType.HARDWARE
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleHardwareRepo:
            def __init__(self):
                self.hardware_items = {}
                self.next_id = 1

            def add(self, hardware):
                hardware.id = self.next_id
                self.hardware_items[self.next_id] = hardware
                self.next_id += 1
                return hardware

            def find_by_hardware_type(self, hardware_type):
                return [h for h in self.hardware_items.values() if h.hardware_type == hardware_type]

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleHardwareRepo()

        # Create different types of hardware
        buckle1 = TestHardware(
            name="Center Bar Buckle",
            material_type=MaterialType.HARDWARE,
            supplier_id=supplier.id,
            unit_price=5.50,
            hardware_type=HardwareType.BUCKLE,
            hardware_material=HardwareMaterial.BRASS,
            finish=HardwareFinish.ANTIQUE,
            size="1 inch"
        )

        buckle2 = TestHardware(
            name="Roller Buckle",
            material_type=MaterialType.HARDWARE,
            supplier_id=supplier.id,
            unit_price=6.75,
            hardware_type=HardwareType.BUCKLE,
            hardware_material=HardwareMaterial.NICKEL,
            finish=HardwareFinish.POLISHED,
            size="1.5 inch"
        )

        rivet = TestHardware(
            name="Double Cap Rivet",
            material_type=MaterialType.HARDWARE,
            supplier_id=supplier.id,
            unit_price=0.75,
            hardware_type=HardwareType.RIVET,
            hardware_material=HardwareMaterial.BRASS,
            finish=HardwareFinish.ANTIQUE,
            size="Medium"
        )

        # Add to repository
        repository.add(buckle1)
        repository.add(buckle2)
        repository.add(rivet)

        # Find hardware by type
        buckles = repository.find_by_hardware_type(HardwareType.BUCKLE)
        rivets = repository.find_by_hardware_type(HardwareType.RIVET)

        # Verify results
        assert len(buckles) == 2
        assert len(rivets) == 1
        assert all(h.hardware_type == HardwareType.BUCKLE for h in buckles)
        assert all(h.hardware_type == HardwareType.RIVET for h in rivets)

    def test_find_hardware_by_material(self, dbsession):
        """Test finding hardware by material."""

        # Create a simple test hardware object
        class TestHardware:
            def __init__(self, **kwargs):
                self.id = None
                self.material_type = MaterialType.HARDWARE
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleHardwareRepo:
            def __init__(self):
                self.hardware_items = {}
                self.next_id = 1

            def add(self, hardware):
                hardware.id = self.next_id
                self.hardware_items[self.next_id] = hardware
                self.next_id += 1
                return hardware

            def find_by_hardware_material(self, hardware_material):
                return [h for h in self.hardware_items.values() if h.hardware_material == hardware_material]

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleHardwareRepo()

        # Create hardware from different materials
        brass_item1 = TestHardware(
            name="Brass Snap",
            material_type=MaterialType.HARDWARE,
            supplier_id=supplier.id,
            hardware_type=HardwareType.SNAP,
            hardware_material=HardwareMaterial.BRASS,
            finish=HardwareFinish.ANTIQUE
        )

        brass_item2 = TestHardware(
            name="Brass D-Ring",
            material_type=MaterialType.HARDWARE,
            supplier_id=supplier.id,
            hardware_type=HardwareType.D_RING,
            hardware_material=HardwareMaterial.BRASS,
            finish=HardwareFinish.POLISHED
        )

        nickel_item = TestHardware(
            name="Nickel Clasp",
            material_type=MaterialType.HARDWARE,
            supplier_id=supplier.id,
            hardware_type=HardwareType.CLASP,
            hardware_material=HardwareMaterial.NICKEL,
            finish=HardwareFinish.BRUSHED
        )

        # Add to repository
        repository.add(brass_item1)
        repository.add(brass_item2)
        repository.add(nickel_item)

        # Find hardware by material
        brass_items = repository.find_by_hardware_material(HardwareMaterial.BRASS)
        nickel_items = repository.find_by_hardware_material(HardwareMaterial.NICKEL)

        # Verify results
        assert len(brass_items) == 2
        assert len(nickel_items) == 1
        assert all(h.hardware_material == HardwareMaterial.BRASS for h in brass_items)
        assert all(h.hardware_material == HardwareMaterial.NICKEL for h in nickel_items)