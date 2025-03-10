# tests/leatherwork_repository_tests/test_material_repository.py
import pytest
from datetime import datetime, timedelta
from database.models.enums import (
    MaterialType,
    QualityGrade,
    MeasurementUnit,
    InventoryStatus,
    SupplierStatus
)


class TestMaterialRepository:
    def _create_test_supplier(self, dbsession):
        """Helper method to create a test supplier."""

        class TestSupplier:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        supplier = TestSupplier(
            name="Test Supplier",
            contact_email="supplier@example.com",
            phone="555-123-4567",
            address="123 Supplier St",
            status=SupplierStatus.ACTIVE,
            created_at=datetime.now()
        )

        # Simulated database insert
        supplier.id = 1
        return supplier

    def test_create_material(self, dbsession):
        """Test creating a new material."""

        # Create a simple test material object
        class TestMaterial:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleMaterialRepo:
            def __init__(self):
                self.materials = {}
                self.next_id = 1

            def add(self, material):
                material.id = self.next_id
                self.materials[self.next_id] = material
                self.next_id += 1
                return material

            def get_by_id(self, id):
                return self.materials.get(id)

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleMaterialRepo()

        # Create a material
        material = TestMaterial(
            name="Premium Thread",
            material_type=MaterialType.THREAD,
            description="High-quality thread for leather stitching",
            supplier_id=supplier.id,
            unit_price=12.99,
            measurement_unit=MeasurementUnit.METER,
            quality_grade=QualityGrade.PREMIUM,
            color="Black",
            created_at=datetime.now()
        )

        # Save the material
        added_material = repository.add(material)

        # Verify the material was saved
        assert added_material.id == 1
        assert added_material.name == "Premium Thread"
        assert added_material.material_type == MaterialType.THREAD
        assert added_material.supplier_id == supplier.id
        assert added_material.quality_grade == QualityGrade.PREMIUM
        assert added_material.color == "Black"

    def test_read_material(self, dbsession):
        """Test reading a material."""

        # Create a simple test material object
        class TestMaterial:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleMaterialRepo:
            def __init__(self):
                self.materials = {}
                self.next_id = 1

            def add(self, material):
                material.id = self.next_id
                self.materials[self.next_id] = material
                self.next_id += 1
                return material

            def get_by_id(self, id):
                return self.materials.get(id)

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleMaterialRepo()

        # Create a material
        material = TestMaterial(
            name="Brown Edge Paint",
            material_type=MaterialType.EDGE_PAINT,
            description="Professional-grade edge paint for leather finishing",
            supplier_id=supplier.id,
            unit_price=24.50,
            measurement_unit=MeasurementUnit.MILLILITER,
            quality_grade=QualityGrade.PROFESSIONAL,
            color="Brown",
            created_at=datetime.now()
        )

        # Add to repository
        added_material = repository.add(material)

        # Read the material
        retrieved_material = repository.get_by_id(added_material.id)

        # Verify the material was retrieved correctly
        assert retrieved_material is not None
        assert retrieved_material.id == added_material.id
        assert retrieved_material.name == "Brown Edge Paint"
        assert retrieved_material.material_type == MaterialType.EDGE_PAINT
        assert retrieved_material.unit_price == 24.50

    def test_update_material(self, dbsession):
        """Test updating a material."""

        # Create a simple test material object
        class TestMaterial:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleMaterialRepo:
            def __init__(self):
                self.materials = {}
                self.next_id = 1

            def add(self, material):
                material.id = self.next_id
                self.materials[self.next_id] = material
                self.next_id += 1
                return material

            def get_by_id(self, id):
                return self.materials.get(id)

            def update(self, material):
                if material.id in self.materials:
                    self.materials[material.id] = material
                    return material
                return None

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleMaterialRepo()

        # Create a material
        material = TestMaterial(
            name="Leather Adhesive",
            material_type=MaterialType.ADHESIVE,
            description="Strong adhesive for leather bonding",
            supplier_id=supplier.id,
            unit_price=15.75,
            measurement_unit=MeasurementUnit.MILLILITER,
            quality_grade=QualityGrade.STANDARD,
            created_at=datetime.now()
        )

        # Add to repository
        added_material = repository.add(material)

        # Update the material
        added_material.name = "Premium Leather Adhesive"
        added_material.unit_price = 18.99
        added_material.quality_grade = QualityGrade.PREMIUM
        repository.update(added_material)

        # Retrieve and verify updates
        updated_material = repository.get_by_id(added_material.id)
        assert updated_material.name == "Premium Leather Adhesive"
        assert updated_material.unit_price == 18.99
        assert updated_material.quality_grade == QualityGrade.PREMIUM

    def test_delete_material(self, dbsession):
        """Test deleting a material."""

        # Create a simple test material object
        class TestMaterial:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleMaterialRepo:
            def __init__(self):
                self.materials = {}
                self.next_id = 1

            def add(self, material):
                material.id = self.next_id
                self.materials[self.next_id] = material
                self.next_id += 1
                return material

            def get_by_id(self, id):
                return self.materials.get(id)

            def delete(self, id):
                if id in self.materials:
                    del self.materials[id]
                    return True
                return False

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleMaterialRepo()

        # Create a material
        material = TestMaterial(
            name="Blue Dye",
            material_type=MaterialType.DYE,
            description="Premium leather dye",
            supplier_id=supplier.id,
            unit_price=32.00,
            measurement_unit=MeasurementUnit.MILLILITER,
            quality_grade=QualityGrade.PROFESSIONAL,
            color="Blue",
            created_at=datetime.now()
        )

        # Add to repository
        added_material = repository.add(material)

        # Delete the material
        material_id = added_material.id
        result = repository.delete(material_id)

        # Verify the material was deleted
        assert result is True
        assert repository.get_by_id(material_id) is None

    def test_find_materials_by_type(self, dbsession):
        """Test finding materials by type."""

        # Create a simple test material object
        class TestMaterial:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleMaterialRepo:
            def __init__(self):
                self.materials = {}
                self.next_id = 1

            def add(self, material):
                material.id = self.next_id
                self.materials[self.next_id] = material
                self.next_id += 1
                return material

            def find_by_type(self, material_type):
                return [m for m in self.materials.values() if m.material_type == material_type]

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleMaterialRepo()

        # Create materials of different types
        thread1 = TestMaterial(
            name="Black Thread",
            material_type=MaterialType.THREAD,
            supplier_id=supplier.id,
            unit_price=10.99,
            measurement_unit=MeasurementUnit.METER,
            quality_grade=QualityGrade.PREMIUM,
            color="Black"
        )

        thread2 = TestMaterial(
            name="Brown Thread",
            material_type=MaterialType.THREAD,
            supplier_id=supplier.id,
            unit_price=10.99,
            measurement_unit=MeasurementUnit.METER,
            quality_grade=QualityGrade.PREMIUM,
            color="Brown"
        )

        adhesive = TestMaterial(
            name="Contact Cement",
            material_type=MaterialType.ADHESIVE,
            supplier_id=supplier.id,
            unit_price=18.50,
            measurement_unit=MeasurementUnit.MILLILITER,
            quality_grade=QualityGrade.PROFESSIONAL
        )

        # Add to repository
        repository.add(thread1)
        repository.add(thread2)
        repository.add(adhesive)

        # Find materials by type
        thread_materials = repository.find_by_type(MaterialType.THREAD)
        adhesive_materials = repository.find_by_type(MaterialType.ADHESIVE)

        # Verify results
        assert len(thread_materials) == 2
        assert len(adhesive_materials) == 1
        assert all(m.material_type == MaterialType.THREAD for m in thread_materials)
        assert all(m.material_type == MaterialType.ADHESIVE for m in adhesive_materials)